#!/usr/bin/env python3
"""Check the EPUB and the DOCX the book builds, and compare them with an earlier build.

    python scripts/ebook_validate.py --epub outputs/build/downloads/book-latest.epub \\
                                     --docx outputs/build/downloads/book-latest.docx
    python scripts/ebook_validate.py --epub NEW.epub --baseline-epub OLD.epub --report outputs/build/ebook-report.json

An EPUB is read as a ZIP and as XML: the first entry is the stored mimetype, container.xml names the package, every
manifest item exists and has the right media type, the spine and the cover refer to manifest items, every XHTML page
parses, every image and internal link in it resolves, and no SVG diagram remains (unless --allow-svg). A DOCX is read
the same way: every part parses and has a content type, every picture's relationship resolves to a part that is
there, and each picture keeps its aspect ratio, fits the text column and prints at a usable resolution.

With a baseline (an earlier build) the check also proves that nothing but the diagrams changed: the text of every page,
the styles, the caption and alternative text of every figure and the order of the figures are the same, and each
figure is as large on the page as it was. EPUBCheck runs too when it is installed (it needs Java). The exit status is 1
when anything is wrong.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import posixpath
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urldefrag, urlparse

NS = {
    "c": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "x": "http://www.w3.org/1999/xhtml",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "asvg": "http://schemas.microsoft.com/office/drawing/2016/SVG/main",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
}
EMU_PER_INCH = 914400
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
               ".svg": "image/svg+xml", ".webp": "image/webp"}
MAX_LISTED = 12
ALT_ELEMENTS = {"img", "area", "input"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def q(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


@dataclass
class Report:
    kind: str
    path: str
    size: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def as_dict(self) -> dict:
        return {"kind": self.kind, "path": self.path, "bytes": self.size, "ok": self.ok, "errors": self.errors,
                "warnings": self.warnings, **self.info}


def listed(items: Iterable[str]) -> str:
    items = list(items)
    shown = "; ".join(items[:MAX_LISTED])
    return shown + (f"; and {len(items) - MAX_LISTED} more" if len(items) > MAX_LISTED else "")


def parse_xml(data: bytes, what: str, report: Report) -> ET.Element | None:
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        report.error(f"{what} is not well-formed XML: {exc}")
        return None


def open_zip(path: Path, report: Report) -> zipfile.ZipFile | None:
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        report.error(f"{path.name} is not a readable ZIP archive: {exc}")
        return None
    bad = archive.testzip()
    if bad:
        report.error(f"{path.name}: the entry {bad} fails its CRC check")
        return None
    return archive


def png_info(data: bytes, what: str, report: Report):
    """(width, height, mode, dpi_x) of an image, or None when it does not decode."""
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            dpi = image.info.get("dpi", (None, None))[0]
            return image.size[0], image.size[1], image.mode, dpi
    except Exception as exc:
        report.error(f"{what} is not a readable image: {exc}")
        return None


# --- EPUB -----------------------------------------------------------------------------------------------------

def resolve(base: str, href: str) -> str:
    """The archive path an href in the file `base` points to (no fragment, percent-decoding applied)."""
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), unquote(href)))


def is_local(href: str) -> bool:
    parsed = urlparse(href)
    return not parsed.scheme and not parsed.netloc and href != ""


def validate_epub(path: Path, *, allow_svg: bool = False, expect_figures: int | None = None) -> Report:
    report = Report("epub", str(path), path.stat().st_size if path.exists() else 0)
    archive = open_zip(path, report)
    if archive is None:
        return report
    names = [info.filename for info in archive.infolist()]
    first = archive.infolist()[0] if names else None
    if first is None or first.filename != "mimetype":
        report.error("The first ZIP entry is not 'mimetype'.")
    else:
        if first.compress_type != zipfile.ZIP_STORED:
            report.error("The 'mimetype' entry is compressed; it must be stored.")
        if first.extra:
            report.error("The 'mimetype' entry has an extra field; it must have none.")
        if archive.read("mimetype") != b"application/epub+zip":
            report.error("The 'mimetype' entry does not read 'application/epub+zip'.")
    if len(set(names)) != len(names):
        report.error("The archive has duplicate entry names.")

    if "META-INF/container.xml" not in names:
        report.error("META-INF/container.xml is missing.")
        return report
    container = parse_xml(archive.read("META-INF/container.xml"), "META-INF/container.xml", report)
    rootfile = container.find(".//c:rootfile", NS) if container is not None else None
    if rootfile is None or not rootfile.get("full-path"):
        report.error("container.xml names no package document (rootfile).")
        return report
    opf_path = rootfile.get("full-path")
    if opf_path not in names:
        report.error(f"The package document {opf_path} is missing.")
        return report
    package = parse_xml(archive.read(opf_path), opf_path, report)
    if package is None:
        return report

    manifest: dict[str, dict] = {}
    by_path: dict[str, dict] = {}
    for item in package.findall("opf:manifest/opf:item", NS):
        entry = {"id": item.get("id"), "href": item.get("href"), "type": item.get("media-type"),
                 "properties": (item.get("properties") or "").split()}
        if not entry["id"] or not entry["href"]:
            report.error("A manifest item has no id or no href.")
            continue
        if entry["id"] in manifest:
            report.error(f"The manifest id {entry['id']} is used twice.")
        entry["path"] = resolve(opf_path, entry["href"])
        manifest[entry["id"]] = entry
        by_path[entry["path"]] = entry
        if entry["path"] not in names:
            report.error(f"The manifest lists {entry['href']}, which is not in the archive.")
        expected = IMAGE_TYPES.get(posixpath.splitext(entry["path"])[1].lower())
        if expected and entry["type"] != expected:
            report.error(f"{entry['href']} is declared as {entry['type']}, not {expected}.")
    spine = package.findall("opf:spine/opf:itemref", NS)
    if not spine:
        report.error("The spine is empty.")
    for itemref in spine:
        if itemref.get("idref") not in manifest:
            report.error(f"The spine refers to {itemref.get('idref')}, which is not in the manifest.")
    cover_ids = [m.get("content") for m in package.findall("opf:metadata/opf:meta[@name='cover']", NS)]
    cover_paths = {e["path"] for e in manifest.values() if "cover-image" in e["properties"]}
    for cover_id in cover_ids:
        if cover_id not in manifest:
            report.error(f"The cover meta refers to {cover_id}, which is not in the manifest.")
        else:
            cover_paths.add(manifest[cover_id]["path"])
    if not cover_paths:
        report.warn("The package declares no cover image.")
    listed_paths = set(by_path) | {"mimetype", opf_path}
    orphans = [n for n in names if not n.endswith("/") and n not in listed_paths and not n.startswith("META-INF/")]
    if orphans:
        report.warn(f"Archive entries that are not in the manifest: {listed(orphans)}")

    documents = [e for e in manifest.values() if e["type"] == "application/xhtml+xml" and e["path"] in names]
    ids: dict[str, set[str]] = {}
    trees: dict[str, ET.Element] = {}
    for entry in documents:
        tree = parse_xml(archive.read(entry["path"]), entry["path"], report)
        if tree is None:
            continue
        trees[entry["path"]] = tree
        ids[entry["path"]] = {el.get("id") for el in tree.iter() if el.get("id")}
        ids[entry["path"]] |= {el.get("name") for el in tree.iter() if el.get("name")}

    images: dict[str, int] = {}
    figures = missing_alt = 0
    broken_images: list[str] = []
    broken_links: list[str] = []
    svg_uses: list[str] = []
    misplaced_alt: list[str] = []
    for path_, tree in trees.items():
        for img in tree.iter(q("x", "img")):
            src = img.get("src") or ""
            if not is_local(src):
                continue
            target = resolve(path_, urldefrag(src)[0])
            entry = by_path.get(target)
            if entry is None or target not in names:
                broken_images.append(f"{path_}: {src}")
                continue
            if not (entry["type"] or "").startswith("image/"):
                broken_images.append(f"{path_}: {src} is declared as {entry['type']}")
                continue
            images[target] = images.get(target, 0) + 1
            if entry["type"] == "image/svg+xml":
                svg_uses.append(f"{path_}: {src}")
            if target not in cover_paths and posixpath.basename(path_) != "cover.xhtml":
                figures += 1
                if not (img.get("alt") or "").strip():
                    missing_alt += 1
        for element in tree.iter():
            tag = local_name(element.tag)
            if element.get("alt") is not None and tag not in ALT_ELEMENTS:
                misplaced_alt.append(f"{path_}: <{tag}>")
        for link in tree.iter(q("x", "a")):
            href = link.get("href") or ""
            if not is_local(href):
                continue
            base, fragment = urldefrag(href)
            target = resolve(path_, base) if base else path_
            if target not in by_path and target not in trees:
                broken_links.append(f"{path_}: {href}")
            elif fragment and target in ids and unquote(fragment) not in ids[target]:
                broken_links.append(f"{path_}: {href}")
    if broken_images:
        report.error(f"{len(broken_images)} image reference(s) do not resolve: {listed(broken_images)}")
    if broken_links:
        report.error(f"{len(broken_links)} internal link(s) do not resolve: {listed(broken_links)}")
    if misplaced_alt:
        report.error(f"{len(misplaced_alt)} element(s) carry an alt attribute that XHTML 5 allows only on img, area "
                     f"and input (EPUBCheck RSC-005): {listed(misplaced_alt)}")
    if svg_uses and not allow_svg:
        report.error(f"{len(svg_uses)} SVG diagram(s) remain in the pages: {listed(svg_uses)}")
    if missing_alt:
        report.warn(f"{missing_alt} figure image(s) have no alt text.")
    for entry in manifest.values():
        if entry["type"] == "image/svg+xml" and not allow_svg:
            report.error(f"The manifest still lists the SVG {entry['href']}.")
            break

    # The navigation documents and the NCX.
    ncx = [e for e in manifest.values() if e["type"] == "application/x-dtbncx+xml" and e["path"] in names]
    for entry in ncx:
        tree = parse_xml(archive.read(entry["path"]), entry["path"], report)
        if tree is None:
            continue
        for point in tree.iter(q("ncx", "content")):
            src = point.get("src") or ""
            base, fragment = urldefrag(src)
            target = resolve(entry["path"], base)
            if target not in by_path:
                report.error(f"{entry['path']}: {src} does not resolve")
            elif fragment and target in ids and fragment not in ids[target]:
                report.error(f"{entry['path']}: {src} names a missing anchor")
    if not any("nav" in e["properties"] for e in manifest.values()):
        report.warn("The package has no navigation document (properties='nav').")

    # Image files: they decode, and what they are.
    modes: dict[str, int] = {}
    image_bytes = 0
    diagrams = 0
    sizes: list[tuple[int, int]] = []
    for target in images:
        data = archive.read(target)
        image_bytes += len(data)
        if target in cover_paths:
            continue
        if target.endswith(".png") or target.endswith(".jpg"):
            decoded = png_info(data, target, report)
            if decoded:
                modes[decoded[2]] = modes.get(decoded[2], 0) + 1
                sizes.append(decoded[:2])
                diagrams += 1
    total_image_bytes = sum(archive.getinfo(n).file_size for n in names if posixpath.splitext(n)[1].lower() in IMAGE_TYPES)
    report.info.update({
        "xhtml_pages": len(trees), "images": len(images), "figure_images": figures, "diagram_files": diagrams,
        "svg_files": sum(1 for e in manifest.values() if e["type"] == "image/svg+xml"),
        "png_files": sum(1 for e in manifest.values() if e["type"] == "image/png"),
        "image_modes": modes, "image_bytes": total_image_bytes,
        "widest_png": max((w for w, _ in sizes), default=0), "narrowest_png": min((w for w, _ in sizes), default=0),
    })
    if expect_figures is not None and figures != expect_figures:
        report.error(f"{figures} figure image(s) found; {expect_figures} expected.")
    return report


# Where scripts/install_epubcheck.py puts EPUBCheck and a Java runtime (untracked).
TOOLS = Path(__file__).resolve().parents[1] / "outputs" / "tools"


def find_java() -> str | None:
    """Java from the path, JAVA_HOME or outputs/tools/jre (scripts/install_epubcheck.py)."""
    import os
    found = shutil.which("java")
    if found:
        return found
    homes = [Path(os.environ["JAVA_HOME"])] if os.environ.get("JAVA_HOME") else []
    homes += sorted((TOOLS / "jre").glob("*"))
    for home in homes:
        for name in ("java.exe", "java"):
            if (home / "bin" / name).is_file():
                return str(home / "bin" / name)
    return None


def find_epubcheck_jar() -> Path | None:
    """EPUBCHECK_JAR, else outputs/tools/epubcheck (scripts/install_epubcheck.py)."""
    import os
    explicit = os.environ.get("EPUBCHECK_JAR")
    if explicit and Path(explicit).is_file():
        return Path(explicit)
    return next(iter(sorted((TOOLS / "epubcheck").rglob("epubcheck.jar"))), None)


def run_epubcheck(path: Path, report: Report) -> None:
    """Run EPUBCheck and report what it finds.

    It is the check distributors such as Draft2Digital run on an uploaded EPUB. It is the `epubcheck` command when that
    exists, else the jar (EPUBCHECK_JAR or outputs/tools) with Java. When either is missing the report says so, and
    the checks above do not replace it: python scripts/install_epubcheck.py installs both under outputs/tools."""
    command = shutil.which("epubcheck")
    if command is not None:
        command_list = [command, str(path)]
    else:
        jar, java = find_epubcheck_jar(), find_java()
        if not (jar and java):
            report.info["epubcheck"] = "not run (python scripts/install_epubcheck.py installs EPUBCheck and Java)"
            return
        command_list = [java, "-jar", str(jar), str(path)]
    result = subprocess.run(command_list, capture_output=True, text=True)
    summary = next((line for line in result.stdout.splitlines() if line.startswith("Messages:")), "")
    report.info["epubcheck"] = (summary or "completed") if result.returncode == 0 else "failed"
    if result.returncode != 0:
        errors = [line for line in (result.stdout + result.stderr).splitlines() if line.startswith(("ERROR", "FATAL"))]
        report.error(f"EPUBCheck reported {len(errors)} problem(s): " + listed(line[:300] for line in errors[:4]))


# --- DOCX -----------------------------------------------------------------------------------------------------

def content_type_of(part: str, defaults: dict[str, str], overrides: dict[str, str]) -> str | None:
    extension = "rels" if part.endswith(".rels") else posixpath.splitext(part)[1].lstrip(".").lower()
    return overrides.get("/" + part) or defaults.get(extension)


# Word's own page when a section sets none: US Letter with one-inch margins.
DEFAULT_TEXT_WIDTH_TWIPS = 12240 - 2 * 1440


def text_width_emu(body: ET.Element) -> tuple[int, bool]:
    """The width of the text column of the last section, in EMU, and whether the document sets it.

    A section without a page size (Pandoc's output, whose styles come from the reference document) is laid out by
    Word on its default page: Letter with one-inch margins."""
    section = body.find("w:sectPr", NS)
    size = section.find("w:pgSz", NS) if section is not None else None
    margins = section.find("w:pgMar", NS) if section is not None else None
    if size is None or margins is None:
        return DEFAULT_TEXT_WIDTH_TWIPS * EMU_PER_INCH // 1440, False
    twips = int(size.get(q("w", "w"))) - int(margins.get(q("w", "left"), 0)) - int(margins.get(q("w", "right"), 0))
    return twips * EMU_PER_INCH // 1440, True


def validate_docx(path: Path, *, allow_svg: bool = False, min_ppi: float = 200, max_ppi: float = 400,
                  expect_figures: int | None = None, aspect_tolerance: float = 0.01) -> Report:
    report = Report("docx", str(path), path.stat().st_size if path.exists() else 0)
    archive = open_zip(path, report)
    if archive is None:
        return report
    names = [i.filename for i in archive.infolist()]
    if len(set(names)) != len(names):
        report.error("The archive has duplicate entry names.")
    for required in ("[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/_rels/document.xml.rels"):
        if required not in names:
            report.error(f"The required part {required} is missing.")
    if not report.ok:
        return report

    types = parse_xml(archive.read("[Content_Types].xml"), "[Content_Types].xml", report)
    defaults = {d.get("Extension").lower(): d.get("ContentType") for d in types.findall("ct:Default", NS)} if types is not None else {}
    overrides = {o.get("PartName"): o.get("ContentType") for o in types.findall("ct:Override", NS)} if types is not None else {}
    parts = [n for n in names if not n.endswith("/") and n != "[Content_Types].xml"]
    for part in parts:
        if content_type_of(part, defaults, overrides) is None:
            report.error(f"The part {part} has no content type.")
        if part.endswith((".xml", ".rels")):
            parse_xml(archive.read(part), part, report)
    for partname in overrides:
        if partname.lstrip("/") not in names:
            report.error(f"[Content_Types].xml has an override for {partname}, which is not in the archive.")

    rels_tree = parse_xml(archive.read("word/_rels/document.xml.rels"), "word/_rels/document.xml.rels", report)
    rels: dict[str, dict] = {}
    if rels_tree is not None:
        for rel in rels_tree.findall("rel:Relationship", NS):
            external = rel.get("TargetMode") == "External"
            target = rel.get("Target") or ""
            rels[rel.get("Id")] = {"target": target, "external": external,
                                   "path": None if external else posixpath.normpath(posixpath.join("word", target)) if not target.startswith("/") else target.lstrip("/"),
                                   "type": (rel.get("Type") or "").rsplit("/", 1)[-1]}
            if not external and rels[rel.get("Id")]["path"] not in names:
                report.error(f"The relationship {rel.get('Id')} points to {target}, which is not in the archive.")
    document = parse_xml(archive.read("word/document.xml"), "word/document.xml", report)
    if document is None:
        return report
    body = document.find("w:body", NS)
    text_width, width_is_set = text_width_emu(body) if body is not None else (None, False)

    pictures: list[dict] = []
    problems_blip: list[str] = []
    svg_blips = 0
    for index, drawing in enumerate(document.iter(q("w", "drawing")), 1):
        container = drawing.find("wp:inline", NS)
        if container is None:
            container = drawing.find("wp:anchor", NS)
        if container is None:
            continue
        extent = container.find("wp:extent", NS)
        properties = container.find("wp:docPr", NS)
        blip = container.find(".//a:blip", NS)
        svg_blip = container.find(".//asvg:svgBlip", NS)
        if svg_blip is not None:
            svg_blips += 1
        if blip is None or extent is None:
            problems_blip.append(f"drawing {index} has no picture")
            continue
        rid = blip.get(q("r", "embed"))
        rel = rels.get(rid)
        if rel is None or rel["path"] not in names:
            problems_blip.append(f"drawing {index}: {rid} does not resolve")
            continue
        if rel["type"] != "image":
            problems_blip.append(f"drawing {index}: {rid} is a {rel['type']}, not an image")
            continue
        pictures.append({"index": index, "rid": rid, "part": rel["path"], "cx": int(extent.get("cx")),
                         "cy": int(extent.get("cy")), "id": properties.get("id") if properties is not None else None,
                         "descr": (properties.get("descr") if properties is not None else "") or ""})
    if problems_blip:
        report.error(f"{len(problems_blip)} picture(s) do not resolve: {listed(problems_blip)}")
    if svg_blips and not allow_svg:
        report.error(f"{svg_blips} picture(s) still carry an SVG (svgBlip).")
    for part in names:
        if part.lower().endswith(".svg") and not allow_svg:
            report.error(f"The archive still contains the SVG {part}.")
            break

    identifiers = [p["id"] for p in pictures]
    if len(set(identifiers)) != len(identifiers):
        report.warn("Some pictures share a drawing id (docPr).")
    media_bytes = sum(archive.getinfo(n).file_size for n in names if n.startswith("word/media/"))
    resolutions: list[float] = []
    modes: dict[str, int] = {}
    too_wide: list[str] = []
    skewed: list[str] = []
    poor: list[str] = []
    seen_parts: dict[str, tuple] = {}
    for picture in pictures:
        part = picture["part"]
        if part not in seen_parts:
            seen_parts[part] = png_info(archive.read(part), part, report) or (0, 0, "?", None)
        width, height, mode, _dpi = seen_parts[part]
        if not width:
            continue
        modes[mode] = modes.get(mode, 0) + 1
        inches = picture["cx"] / EMU_PER_INCH
        ppi = width / inches
        resolutions.append(ppi)
        drift = abs((width / height) / (picture["cx"] / picture["cy"]) - 1)
        if drift > aspect_tolerance:
            skewed.append(f"drawing {picture['index']} ({drift:.1%})")
        if text_width and picture["cx"] > text_width * 1.005:
            too_wide.append(f"drawing {picture['index']}")
        if ppi < min_ppi:
            poor.append(f"drawing {picture['index']} ({ppi:.0f} ppi)")
    if skewed:
        report.error(f"{len(skewed)} picture(s) are stretched (aspect ratio off by more than "
                     f"{aspect_tolerance:.0%}): {listed(skewed)}")
    if too_wide:
        report.error(f"{len(too_wide)} picture(s) are wider than the text column: {listed(too_wide)}")
    if poor:
        report.warn(f"{len(poor)} picture(s) print below {min_ppi:.0f} ppi: {listed(poor)}")
    if resolutions and max(resolutions) > max_ppi:
        report.warn(f"The highest resolution is {max(resolutions):.0f} ppi (above {max_ppi:.0f}).")
    captions = []
    for paragraph in document.iter(q("w", "p")):
        style = paragraph.find("w:pPr/w:pStyle", NS)
        if style is not None and style.get(q("w", "val")) == "ImageCaption":
            if "".join(t.text or "" for t in paragraph.iter(q("w", "t"))).startswith("Figure"):
                captions.append(paragraph)
    described = sum(1 for p in pictures if p["descr"].strip())
    report.info.update({
        "pictures": len(pictures), "media_files": len({n for n in names if n.startswith("word/media/")}),
        "svg_pictures": svg_blips, "image_modes": modes, "media_bytes": media_bytes,
        "captions": len(captions), "pictures_with_description": described,
        "text_width_inches": round(text_width / EMU_PER_INCH, 3) if text_width else None,
        "text_width_from": "the document's page setup" if width_is_set else "Word's default page (Letter, 1-inch margins)",
        "min_ppi": round(min(resolutions), 1) if resolutions else None,
        "max_ppi": round(max(resolutions), 1) if resolutions else None})
    if captions and len(captions) != len(pictures):
        report.warn(f"{len(captions)} figure caption paragraph(s) for {len(pictures)} picture(s).")
    if expect_figures is not None and len(pictures) != expect_figures:
        report.error(f"{len(pictures)} picture(s) found; {expect_figures} expected.")
    return report


# --- Comparison with an earlier build -------------------------------------------------------------------------

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_epub_part(name: str, data: bytes) -> bytes:
    text = data.decode("utf-8", "replace")
    text = re.sub(r"media/(file\d+)\.(?:svg|png)", r"media/\1.IMG", text)
    text = re.sub(r"\b(file\d+)_(?:svg|png)\b", r"\1_IMG", text)       # Pandoc's manifest ids end in the extension
    text = re.sub(r'(<div\b[^>]*?) alt="[^"]*"', r"\1", text)           # filters/epub-markup.lua drops it from the wrapper
    text = re.sub(r'media-type="image/(?:svg\+xml|png)"', 'media-type="image/IMG"', text)
    text = re.sub(r'<meta property="dcterms:modified">[^<]*</meta>', "", text)
    text = re.sub(r"<dcterms:modified[^>]*>[^<]*</dcterms:modified>", "", text)
    return text.encode("utf-8")


def compare_epub(old: Path, new: Path) -> Report:
    """Nothing but the diagram files differs between two EPUBs: the pages, the styles, the package and the cover."""
    report = Report("epub-compare", f"{old.name} -> {new.name}", new.stat().st_size)
    with zipfile.ZipFile(old) as before, zipfile.ZipFile(new) as after:
        old_names, new_names = set(before.namelist()), set(after.namelist())
        stripped = lambda names: {re.sub(r"\.(svg|png)$", ".IMG", n) if n.startswith("EPUB/media/file") else n for n in names}
        if stripped(old_names) != stripped(new_names):
            report.error("The two EPUBs do not hold the same files (apart from the diagrams): "
                         + listed(sorted((stripped(old_names) ^ stripped(new_names)))))
        changed = []
        for name in sorted(old_names & new_names):
            if name.startswith("EPUB/media/"):
                continue
            a, b = before.read(name), after.read(name)
            if name.endswith((".xhtml", ".opf", ".ncx", ".xml", ".html")):
                a, b = normalize_epub_part(name, a), normalize_epub_part(name, b)
            if a != b:
                changed.append(name)
        if changed:
            report.error(f"{len(changed)} page(s) differ from the earlier EPUB beyond the diagrams: {listed(changed)}")
        old_cover = [n for n in old_names if n.endswith(".png") and "cover" in n.lower()]
        for name in old_cover:
            if name in new_names and before.read(name) != after.read(name):
                report.error(f"The cover image {name} changed.")
        report.info.update({"compared_pages": len(old_names & new_names) - len(changed), "differing_pages": len(changed)})
    return report


def drawing_summaries(document: ET.Element) -> list[dict]:
    result = []
    for drawing in document.iter(q("w", "drawing")):
        container = drawing.find("wp:inline", NS) if drawing.find("wp:inline", NS) is not None else drawing.find("wp:anchor", NS)
        extent = container.find("wp:extent", NS)
        properties = container.find("wp:docPr", NS)
        result.append({"cx": int(extent.get("cx")), "cy": int(extent.get("cy")),
                       "descr": properties.get("descr") or "", "name": properties.get("name") or ""})
    return result


def normalize_docx_document(data: bytes) -> bytes:
    """document.xml without the pictures and without the numbers that count them: the relationship ids (the SVG and
    its PNG took two each) and the bookmark ids, which Pandoc numbers from the same counter."""
    text = data.decode("utf-8", "replace")
    text = re.sub(r"<w:drawing>.*?</w:drawing>", "<w:drawing/>", text, flags=re.S)
    text = re.sub(r'w:id="\d+"', 'w:id="N"', text)
    return re.sub(r"rId\d+", "rIdN", text).encode("utf-8")


def relationship_targets(data: bytes, *, images: bool) -> list[tuple]:
    """The (type, target, mode) of each relationship in a .rels part, in order, leaving out image relationships."""
    tree = ET.fromstring(data)
    rows = []
    for rel in tree.findall("rel:Relationship", NS):
        kind = (rel.get("Type") or "").rsplit("/", 1)[-1]
        if (kind == "image") != images:
            continue
        rows.append((kind, rel.get("Target"), rel.get("TargetMode")))
    return rows


def compare_docx(old: Path, new: Path, *, size_tolerance: float = 0.01) -> Report:
    """Nothing but the pictures differs between two DOCX files; each picture keeps its size on the page."""
    report = Report("docx-compare", f"{old.name} -> {new.name}", new.stat().st_size)
    with zipfile.ZipFile(old) as before, zipfile.ZipFile(new) as after:
        old_names, new_names = set(before.namelist()), set(after.namelist())
        special = {"word/document.xml", "[Content_Types].xml", "docProps/core.xml"}
        ignore = lambda n: n.startswith("word/media/") or n in special
        changed = []
        for name in sorted(old_names & new_names):
            if ignore(name):
                continue
            a, b = before.read(name), after.read(name)
            if name.endswith(".rels"):
                if relationship_targets(a, images=False) != relationship_targets(b, images=False):
                    changed.append(name)
                continue
            if name == "word/footnotes.xml":
                a, b = (re.sub(rb"rId\d+", b"rIdN", x) for x in (a, b))
            if a != b:
                changed.append(name)
        only = sorted(n for n in (old_names ^ new_names) if not n.startswith("word/media/"))
        if only:
            report.error(f"The two files do not hold the same parts: {listed(only)}")
        core = lambda raw: re.sub(rb"<dcterms:(created|modified)[^>]*>[^<]*</dcterms:\1>", b"", raw)
        if core(before.read("docProps/core.xml")) != core(after.read("docProps/core.xml")):
            changed.append("docProps/core.xml")
        if changed:
            report.error(f"{len(changed)} part(s) differ beyond the pictures: {listed(changed)}")
        old_doc, new_doc = before.read("word/document.xml"), after.read("word/document.xml")
        if normalize_docx_document(old_doc) != normalize_docx_document(new_doc):
            report.error("word/document.xml differs beyond the pictures (text, styles, captions or structure).")
        old_pics = drawing_summaries(ET.fromstring(old_doc))
        new_pics = drawing_summaries(ET.fromstring(new_doc))
        if len(old_pics) != len(new_pics):
            report.error(f"{len(old_pics)} picture(s) before, {len(new_pics)} after.")
        worst = 0.0
        resized = []
        for index, (a, b) in enumerate(zip(old_pics, new_pics), 1):
            drift = max(abs(b["cx"] / a["cx"] - 1), abs(b["cy"] / a["cy"] - 1))
            worst = max(worst, drift)
            if drift > size_tolerance:
                resized.append(f"picture {index} ({drift:.1%})")
        if resized:
            report.error(f"{len(resized)} picture(s) changed size on the page: {listed(resized)}")
        report.info.update({"pictures_compared": min(len(old_pics), len(new_pics)),
                            "largest_size_change": round(worst, 5), "differing_parts": len(changed)})
    return report


# --- The report -----------------------------------------------------------------------------------------------

def megabytes(value: int | float) -> str:
    return f"{value / 1e6:.2f} MB"


def baseline_line(report: Report, baseline: Path | None) -> str:
    if baseline is None or not baseline.is_file():
        return ""
    before = baseline.stat().st_size
    return f" (was {megabytes(before)}: {1 - report.size / before:.0%} smaller)"


def print_report(reports: list[Report], baselines: dict[str, Path | None]) -> None:
    for report in reports:
        status = "OK" if report.ok else "FAILED"
        line = f"{report.kind}: {status}"
        if not report.kind.endswith("compare"):
            line += f"  {megabytes(report.size)}{baseline_line(report, baselines.get(report.kind))}"
        print(line)
        for key, value in report.info.items():
            print(f"    {key}: {value}")
        for warning in report.warnings:
            print(f"    warning: {warning}")
        for error in report.errors:
            print(f"    ERROR: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the EPUB and DOCX of the book.")
    parser.add_argument("--epub", type=Path)
    parser.add_argument("--docx", type=Path)
    parser.add_argument("--baseline-epub", type=Path, help="An earlier EPUB: report the size change and prove nothing else changed.")
    parser.add_argument("--baseline-docx", type=Path)
    parser.add_argument("--allow-svg", action="store_true", help="Do not treat SVG diagrams as an error.")
    parser.add_argument("--expect-figures", type=int, help="The number of diagrams each format must carry.")
    parser.add_argument("--min-ppi", type=float, default=200.0, help="Warn below this resolution in the DOCX.")
    parser.add_argument("--report", type=Path, help="Write the reports as JSON.")
    args = parser.parse_args(argv)
    if not (args.epub or args.docx):
        parser.error("Give --epub and/or --docx.")
    reports: list[Report] = []
    baselines: dict[str, Path | None] = {"epub": args.baseline_epub, "docx": args.baseline_docx}
    if args.epub:
        reports.append(validate_epub(args.epub, allow_svg=args.allow_svg, expect_figures=args.expect_figures))
        run_epubcheck(args.epub, reports[-1])
        if args.baseline_epub:
            reports.append(compare_epub(args.baseline_epub, args.epub))
    if args.docx:
        reports.append(validate_docx(args.docx, allow_svg=args.allow_svg, expect_figures=args.expect_figures,
                                     min_ppi=args.min_ppi))
        if args.baseline_docx:
            reports.append(compare_docx(args.baseline_docx, args.docx))
    print_report(reports, baselines)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps([r.as_dict() for r in reports], indent=2) + "\n", encoding="utf-8")
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
