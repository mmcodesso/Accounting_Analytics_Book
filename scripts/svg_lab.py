#!/usr/bin/env python3
"""A lab for smaller Draw.io SVGs: audit the exports, build variants, compare them with what is committed.

    python scripts/svg_lab.py baseline [--rev COMMIT]     # v0: the SVGs with a PNG of every label (the files of an earlier commit)
    python scripts/svg_lab.py audit
    python scripts/svg_lab.py build   --variants v1 v2 v3 --set representative      # or --set all, or figure names
    python scripts/svg_lab.py compare --set representative --engines edge chrome firefox
    python scripts/svg_lab.py determinism --set representative

Variants (everything goes to outputs/svg-lab/, which is untracked; visuals/svg and visuals/src are never written):

    v0  the baseline: the SVGs as they were with a PNG of every label (outputs/svg-lab/v0 from `baseline`; the
        committed files if there is none)
    v1  v0 with the markup no viewer needs removed, PNG fallbacks kept          (scripts/svg_native.strip_svg_metadata)
    v2  Draw.io's export with --embed-svg-fonts false: labels stay HTML, the fallback is Draw.io's plain-text <text>,
        no PNGs; then the same stripping
    v3  v2, but every label that fits on one line is exported as native <text> (Draw.io's "Convert labels to SVG",
        switched on for those cells in a temporary copy of the source); labels that wrap stay HTML

Draw.io's conversion does not wrap text and does not read <br>, which is why v3 converts only labels measured to fit.
compare writes outputs/svg-lab/report.json and report.md.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import export_drawio_svgs as exporter  # noqa: E402
from scripts import svg_native  # noqa: E402

LAB = ROOT / "outputs" / "svg-lab"
SRC_DIR = ROOT / "visuals" / "src"
SVG_DIR = ROOT / "visuals" / "svg"
PDF_DIR = ROOT / "visuals" / "pdf"
SCALE = 2          # screenshots draw the SVG at twice its size
BROWSERS = {
    "edge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"],
    "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "firefox": [r"C:\Program Files\Mozilla Firefox\firefox.exe", r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"],
}
# What an adoption has to meet (the report applies these).
GATES = {"text_integrity": 1.0, "geometry_share": 0.995, "median_pixel_pct": 0.3, "worst_pixel_pct": 2.0, "size_reduction": 0.90}


class LabError(RuntimeError):
    pass


# ------------------------------------------------------------------------------------------------------- files


def stems() -> list[str]:
    return sorted(path.stem for path in SVG_DIR.glob("*.svg"))


def variant_path(variant: str, stem: str, raw: bool = False) -> Path:
    if variant == "v0":
        # the baseline: outputs/svg-lab/v0 when `baseline` made it, else the committed files
        return (LAB / "v0" if (LAB / "v0").is_dir() else SVG_DIR) / f"{stem}.svg"
    return LAB / ("raw" if raw else "") / variant / f"{stem}.svg"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def gzip_size(data: bytes) -> int:
    return len(gzip.compress(data, 9, mtime=0))


def chapter_of(stem: str) -> str:
    match = re.match(r"fig-(\d\d)-", stem) or re.match(r"fig-([a-z])-", stem)
    return match.group(1) if match else "other"


def choose(selection: list[str]) -> list[str]:
    everything = stems()
    if selection in ([], ["representative"]):
        audit = LAB / "audit.json"
        if not audit.is_file():
            raise LabError("Run `svg_lab.py audit` first: it chooses the representative figures.")
        return json.loads(read(audit))["representative"]["figures"]
    if selection == ["all"]:
        return everything
    chosen = [name for name in everything if any(name == s or name.startswith(s) for s in selection)]
    missing = [s for s in selection if not any(name == s or name.startswith(s) for name in everything)]
    if missing:
        raise LabError(f"No figure matches {', '.join(missing)}")
    return chosen


# ------------------------------------------------------------------------------------------------------- audit


def figure_features(stem: str) -> dict:
    """Counts that decide whether a diagram is a good test of text rendering."""
    svg = read(variant_path("v0", stem))
    source = read(SRC_DIR / f"{stem}.drawio")
    found = [label for label in svg_native.labels(svg) if label.kind == "html"]
    lines = [max(1, round((label.image_box[3] - 2.6) / (label.size * 1.2)))
             for label in found if label.image_box and label.size]
    special = Counter(ch for label in found for ch in label.text if ord(ch) > 127 and ch != "\xa0")
    cells = re.findall(r"<mxCell\b[^>]*>", source)
    return {
        "bytes": len(svg.encode()), "labels": len(found), "multi_line": sum(1 for n in lines if n > 1),
        "br": sum(label.has_br for label in found), "nowrap": sum(label.nowrap for label in found),
        "bold_runs": sum(any(run.bold for run in label.runs if run.text.strip()) for label in found),
        "colored_runs": sum(len({run.color for run in label.runs if run.text.strip()}) > 1 for label in found),
        "nbsp": sum("\xa0" in label.text for label in found), "special": sum(special.values()),
        "min_font": min((label.size for label in found if label.size), default=0),
        "edge_labels": sum(1 for cell in cells if 'edge="1"' in cell and re.search(r'\svalue="[^"]+"', cell)),
        "rotated": source.count("horizontal=0"),
        "whole_bold": sum(1 for cell in cells if "fontStyle=1" in cell),
    }


def pick_representative(features: dict[str, dict]) -> dict:
    """A few diagrams that between them cover every kind of label the book has."""
    def best(key, pool=None):
        pool = pool if pool is not None else list(features)
        ranked = sorted((s for s in pool if features[s][key] > 0), key=lambda s: (-features[s][key], s))
        return ranked[0] if ranked else None

    def in_chapters(low: int, high: int) -> list[str]:
        return [s for s in features if re.match(r"fig-(\d\d)-", s) and low <= int(s[4:6]) <= high]

    picks = {
        "largest file (small labels, many of them)": max(features, key=lambda s: features[s]["bytes"]),
        "median file": sorted(features, key=lambda s: features[s]["bytes"])[len(features) // 2],
        "connectors with edge labels": best("edge_labels"),
        "formatted text (bold, colour, <br>)": max(features, key=lambda s: (features[s]["colored_runs"] + features[s]["br"], s)),
        "wrapping labels": best("multi_line"),
        "special characters": best("special"),
        "no-break spaces (code mocks)": best("nbsp"),
        "nowrap labels": best("nowrap"),
        "bold-style cells": best("whole_bold"),
        "rotated label": best("rotated"),
        "Excel mock": best("labels", in_chapters(4, 8)),
        "DB Browser mock": best("labels", in_chapters(9, 12)),
        "Power BI mock": best("labels", in_chapters(13, 16)),
    }
    figures = sorted({s for s in picks.values() if s})
    return {"figures": figures, "why": {k: v for k, v in picks.items() if v}}


def audit() -> dict:
    LAB.mkdir(parents=True, exist_ok=True)
    totals = Counter()
    features: dict[str, dict] = {}
    for stem in stems():
        data = variant_path("v0", stem).read_bytes()
        text = data.decode("utf-8")
        totals["files"] += 1
        totals["bytes"] += len(data)
        totals["gzip_bytes"] += gzip_size(data)
        pngs = re.findall(rb'data:image/png;base64,([A-Za-z0-9+/=]+)', data)
        totals["png_uris"] += len(pngs)
        totals["png_base64_bytes"] += sum(len(p) for p in pngs)
        totals["switch"] += text.count("<switch")
        totals["foreignObject"] += text.count("<foreignObject")
        totals["image_elements"] += text.count("<image")
        totals["style_or_fontface"] += text.count("<style") + text.count("@font-face")
        nonfallback = re.sub(r"<image [^>]*?/>", "", text)
        totals["gzip_without_png"] += gzip_size(nonfallback.encode())
        totals["foreignObject_bytes"] += sum(len(m.group(0).encode()) for m in re.finditer(r"<foreignObject.*?</foreignObject>", nonfallback, re.S))
        totals["pointer_events_bytes"] += sum(len(m.group(0).encode()) for m in re.finditer(r' pointer-events="[^"]*"', nonfallback))
        totals["cell_id_bytes"] += sum(len(m.group(0).encode()) for m in re.finditer(r' data-cell-id="[^"]*"', nonfallback))
        totals["style_duplicate_bytes"] += sum(len(m.group(0).encode()) for m in re.finditer(r' style="(?:fill|stroke)[^"]*"', nonfallback))
        totals["pdf_exists"] += (PDF_DIR / f"{stem}.pdf").is_file()
        features[stem] = figure_features(stem)
    meter = svg_native.TextMeter()
    confusion = Counter()
    for stem in features:
        for label in svg_native.labels(read(variant_path("v0", stem))):
            if label.kind != "html" or not label.image_box or not label.size:
                continue
            truth_single = round((label.image_box[3] - 2.6) / (label.size * 1.2)) <= 1
            predicted = svg_native.fits_on_one_line(label, meter)
            confusion[f"predicted {'1 line' if predicted else 'wraps'} / truth {'1 line' if truth_single else 'wraps'}"] += 1
    label_classes = Counter()
    for f in features.values():
        label_classes["labels"] += f["labels"]
        for key in ("multi_line", "br", "nowrap", "bold_runs", "colored_runs", "nbsp", "special", "edge_labels", "rotated", "whole_bold"):
            label_classes[key] += f[key]
    result = {
        "totals": dict(totals), "label_classes": dict(label_classes), "classifier_vs_png_heights": dict(confusion),
        "font": meter.description, "representative": pick_representative(features), "features": features,
        "drawio": drawio_version(),
    }
    (LAB / "audit.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    total = totals["bytes"]
    print(f"{totals['files']} SVGs, {total / 1e6:.2f} MB ({totals['gzip_bytes'] / 1e6:.2f} MB gzipped)")
    print(f"  PNG fallbacks   {totals['png_uris']:>6} = {totals['png_base64_bytes'] / 1e6:.2f} MB ({totals['png_base64_bytes'] / total:.1%}); "
          f"<switch> {totals['switch']}, foreignObject {totals['foreignObject']}, <image> {totals['image_elements']}")
    print(f"  without PNGs    {(total - totals['png_base64_bytes']) / 1e6:.2f} MB, gzip {totals['gzip_without_png'] / 1e6:.2f} MB; "
          f"foreignObject HTML {totals['foreignObject_bytes'] / 1e6:.2f} MB, style duplicates {totals['style_duplicate_bytes'] / 1e6:.2f} MB, "
          f"pointer-events {totals['pointer_events_bytes'] / 1e6:.2f} MB, data-cell-id {totals['cell_id_bytes'] / 1e6:.2f} MB")
    print(f"  <style>/@font-face {totals['style_or_fontface']}; every SVG has a PDF: {totals['pdf_exists'] == totals['files']}")
    print("  labels:", dict(label_classes))
    print("  classifier against the PNG heights:", dict(confusion))
    print("  representative:", ", ".join(result["representative"]["figures"]))
    return result


def drawio_version() -> str:
    try:
        exe = exporter.find_drawio_executable(None)
        return f"{exe.parent.name} (see Help > About); resources/app.asar says " + (
            re.search(rb'"name":\s*"draw\.io",\s*"version":\s*"([\d.]+)"', (exe.parent / "resources" / "app.asar").read_bytes()).group(1).decode())
    except Exception as exc:  # noqa: BLE001 - informational only
        return f"unknown ({exc})"


# ---------------------------------------------------------------------------------------------------- baseline


def baseline(selection: list[str], revision: str | None) -> None:
    """Make v0, the baseline the variants are compared with: visuals/svg as it was when every label carried a PNG
    (the files of an earlier commit, --rev), or a new Draw.io export with the PNGs (--svg-labels png-fallback)."""
    target = LAB / "v0"
    names = choose(selection) if selection else stems()
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    if revision:
        archive = subprocess.run(["git", "archive", revision, "visuals/svg"], cwd=ROOT, capture_output=True, check=True).stdout
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(["tar", "-x", "-C", temp], input=archive, check=True)
            for path in (Path(temp) / "visuals" / "svg").glob("*.svg"):
                shutil.copy2(path, target / path.name)
        print(f"v0: {len(list(target.glob('*.svg')))} files of visuals/svg at {revision}")
        return
    exe = exporter.find_drawio_executable(None)
    for number, stem in enumerate(names, 1):
        exporter.export_svg(exe, SRC_DIR / f"{stem}.drawio", target / f"{stem}.svg", exporter.DEFAULT_PADDING, "png-fallback")
        print(f"[{number}/{len(names)}] {stem}", flush=True)


# ------------------------------------------------------------------------------------------------------- build


def post_process(path: Path) -> None:
    """The exporter's own steps after Draw.io, so that only the label handling differs from the committed files."""
    exporter.add_svg_padding(path, exporter.DEFAULT_PADDING)
    exporter.remove_drawio_text_warning(path)
    exporter.force_light_colors(path)
    exporter.add_white_background(path)


def drawio_export(exe: Path, source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.stem}.tmp.svg")
    temporary.unlink(missing_ok=True)
    exporter.run_drawio([str(exe), "-x", "-f", "svg", "--svg-theme", "light", *svg_native.DRAWIO_NO_RASTER_FALLBACK,
                         "-o", str(temporary), str(source)], source, temporary, "SVG")
    post_process(temporary)
    temporary.replace(target)


def build_figure(exe: Path | None, stem: str, variants: list[str], meter: svg_native.TextMeter | None) -> dict:
    info: dict = {}
    source = SRC_DIR / f"{stem}.drawio"
    if "v1" in variants:
        path = variant_path("v1", stem)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg_native.strip_svg_metadata(read(variant_path("v0", stem))), encoding="utf-8")
    if "v2" in variants or "v3" in variants:
        raw2 = variant_path("v2", stem, raw=True)
        if "v2" in variants or not raw2.is_file():
            started = time.time()
            drawio_export(exe, source, raw2)
            info["v2_seconds"] = round(time.time() - started, 1)
        v2 = variant_path("v2", stem)
        v2.parent.mkdir(parents=True, exist_ok=True)
        v2.write_text(svg_native.strip_svg_metadata(read(raw2)), encoding="utf-8")
    if "v3" in variants:
        cells = svg_native.single_line_cells(read(variant_path("v2", stem, raw=True)), meter)
        raw3 = variant_path("v3", stem, raw=True)
        info["v3_cells_converted"] = len(cells)
        if cells:
            temporary = LAB / "src" / f"{stem}.drawio"
            temporary.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(svg_native.native_labels_copy(read(source), cells), encoding="utf-8")
            started = time.time()
            drawio_export(exe, temporary, raw3)
            info["v3_seconds"] = round(time.time() - started, 1)
        else:
            raw3.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(variant_path("v2", stem, raw=True), raw3)
        v3 = variant_path("v3", stem)
        v3.parent.mkdir(parents=True, exist_ok=True)
        v3.write_text(svg_native.strip_svg_metadata(read(raw3)), encoding="utf-8")
    return info


def build(variants: list[str], selection: list[str]) -> None:
    names = choose(selection)
    exe = exporter.find_drawio_executable(None) if ({"v2", "v3"} & set(variants)) else None
    meter = svg_native.TextMeter() if "v3" in variants else None
    log = {}
    started = time.time()
    for number, stem in enumerate(names, 1):
        log[stem] = build_figure(exe, stem, variants, meter)
        print(f"[{number}/{len(names)}] {stem} {log[stem]}", flush=True)
    previous = json.loads(read(LAB / "build.json")) if (LAB / "build.json").is_file() else {}
    previous.update(log)
    (LAB / "build.json").write_text(json.dumps(previous, indent=1), encoding="utf-8")
    print(f"Built {len(names)} figures in {time.time() - started:.0f} s -> {LAB.relative_to(ROOT)}")


# ----------------------------------------------------------------------------------------------------- render


def find_browser(engine: str) -> str:
    for candidate in BROWSERS[engine]:
        if Path(candidate).is_file():
            return candidate
    raise LabError(f"{engine} was not found.")


def root_size(text: str) -> tuple[float, float, tuple[float, float, float, float]]:
    tag = re.search(r"<svg\b[^>]*>", text).group(0)
    width = float(re.search(r'\swidth="([\d.]+)px"', tag).group(1))
    height = float(re.search(r'\sheight="([\d.]+)px"', tag).group(1))
    box = tuple(float(v) for v in re.search(r'\sviewBox="([^"]+)"', tag).group(1).replace(",", " ").split())
    return width, height, box  # type: ignore[return-value]


def screenshot(engine: str, svg: Path, png: Path, workdir: Path, scale: int = SCALE) -> None:
    """The SVG as an <img> (how the book uses it), drawn at `scale` times its size on white."""
    width, height, _ = root_size(read(svg))
    w, h = int(round(width * scale)), int(round(height * scale))
    png.parent.mkdir(parents=True, exist_ok=True)
    png.unlink(missing_ok=True)
    page = workdir / f"{png.stem}.html"
    page.write_text(f'<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff">'
                    f'<img src="{svg.resolve().as_uri()}" style="display:block;width:{w}px;height:{h}px"></body>', encoding="utf-8")
    exe = find_browser(engine)
    if engine == "firefox":
        # Firefox takes the picture's path as a separate argument; a profile folder of its own keeps runs apart
        profile = workdir / "firefox-profile"
        profile.mkdir(exist_ok=True)
        command = [exe, "-no-remote", "-profile", str(profile), "--headless", "--screenshot", str(png), f"--window-size={w},{h}", page.as_uri()]
    else:
        profile = workdir / f"{engine}-profile"
        command = [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                   f"--window-size={w},{h}", f"--screenshot={png}", page.as_uri()]
    subprocess.run(command, check=True, capture_output=True, timeout=180)
    page.unlink(missing_ok=True)
    if not png.is_file():
        raise LabError(f"{engine} made no screenshot of {svg.name}")


def render_many(engine: str, jobs: list[tuple[Path, Path]], workers: int = 4) -> None:
    """Screenshots in parallel, each worker with its own browser profile; skips pictures newer than their SVG."""
    todo = [(svg, png) for svg, png in jobs if not png.is_file() or png.stat().st_mtime < svg.stat().st_mtime]
    if not todo:
        return
    folders = [Path(tempfile.mkdtemp(prefix=f"svg-lab-{engine}-")) for _ in range(workers)]
    try:
        def run(index: int) -> None:
            for position in range(index, len(todo), workers):
                svg, png = todo[position]
                screenshot(engine, svg, png, folders[index])
        with ThreadPoolExecutor(workers) as pool:
            for future in [pool.submit(run, i) for i in range(workers)]:
                future.result()
    finally:
        for folder in folders:
            shutil.rmtree(folder, ignore_errors=True)


def gray(png: Path):
    import numpy as np
    from PIL import Image
    with Image.open(png) as image:
        return np.asarray(image.convert("L"), dtype=np.int16)


def tolerant_mismatch(a, b, radius: int = 2, threshold: int = 60):
    """Mask of the pixels of a that no pixel of b within `radius` matches to within `threshold` gray levels. A text
    edge a pixel or two off, or anti-aliased differently, does not count; a missing or moved word does."""
    import numpy as np
    height, width = a.shape
    best = np.full(a.shape, 255, dtype=np.int16)
    padded = np.pad(b, radius, mode="edge")
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            best = np.minimum(best, np.abs(a - padded[radius + dy:radius + dy + height, radius + dx:radius + dx + width]))
    return best > threshold


def pixel_metrics(base, other) -> dict:
    import numpy as np
    if base.shape != other.shape:
        return {"same_size": False, "base": list(base.shape), "other": list(other.shape)}
    bad = tolerant_mismatch(base, other) | tolerant_mismatch(other, base)
    ink = int(((base < 200) | (other < 200)).sum()) or 1
    block = 40
    h, w = (bad.shape[0] // block) * block, (bad.shape[1] // block) * block
    blocks = bad[:h, :w].reshape(h // block, block, w // block, block).mean(axis=(1, 3)) if h and w else np.zeros((1, 1))
    return {"same_size": True, "mismatch_pct": round(float(bad.sum()) / ink * 100, 4),
            "raw_diff_pct": round(float((np.abs(base - other) > 60).sum()) / ink * 100, 4),
            "worst_block_pct": round(float(blocks.max()) * 100, 1), "_mask": bad}


# --------------------------------------------------------------------------------------------------- compare


TEXT_ONLY_CSS = ("<style>rect,path,ellipse,circle,polygon,polyline,line{display:none}"
                 "svg{background:#808080 !important}</style>")


def text_only(svg_text: str) -> str:
    """The same SVG with every shape hidden on a mid-gray page, so only label ink is left (dark and white text both show)."""
    tag = re.search(r"<svg\b[^>]*>", svg_text)
    return svg_text[:tag.end()] + TEXT_ONLY_CSS + svg_text[tag.end():]


def native_label_geometry(v0: str, v3_raw: str, base_gray, other_gray, vb) -> dict:
    """Where the ink of each label that v3 draws natively is, against the baseline's HTML label, in renders that
    hold the text alone: centre of the ink (to a fraction of a pixel) and amount of ink inside the label's own box
    (the baseline's PNG fallback is the box Draw.io computed), and ink anywhere outside every label box."""
    import numpy as np
    labels0 = [label for label in svg_native.labels(v0) if label.kind == "html" and label.image_box]
    originals = {label.cell: label for label in labels0}
    height, width = base_gray.shape
    pad = 3.0

    def window(box):
        x, y, w, h = box
        x0, x1 = int((x - pad - vb[0]) * SCALE), int((x + w + pad - vb[0]) * SCALE)
        y0, y1 = int((y - pad - vb[1]) * SCALE), int((y + h + pad - vb[1]) * SCALE)
        return max(0, x0), max(0, y0), min(width, x1), min(height, y1)

    def ink(region):
        return np.where(np.abs(region - 128) > 40, np.abs(region - 128), 0).astype(np.float64)

    checked = within = within_loose = 0
    shifts, ratios, outside, offsets = [], [], [], []
    for label in svg_native.labels(v3_raw):
        original = originals.get(label.cell)
        if label.kind != "native" or original is None or original.text != label.text:
            continue
        x0, y0, x1, y1 = window(original.image_box)
        if x1 <= x0 or y1 <= y0:
            continue
        a, b = ink(base_gray[y0:y1, x0:x1]), ink(other_gray[y0:y1, x0:x1])
        if a.sum() < 200 or b.sum() < 1:
            continue
        checked += 1
        grid_y, grid_x = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        centre = lambda m: (float((m * grid_x).sum() / m.sum()), float((m * grid_y).sum() / m.sum()))
        (ax, ay), (bx, by) = centre(a), centre(b)
        dx, dy = (bx - ax) / SCALE, (by - ay) / SCALE          # signed, in the SVG's own pixels: + is right and down
        shift = float(np.hypot(dx, dy))
        ratio = float(b.sum() / a.sum())
        shifts.append(shift)
        ratios.append(ratio)
        offsets.append((label.size, dx, dy))
        inks_alike = 0.85 <= ratio <= 1.15
        within += shift <= 0.75 and inks_alike
        within_loose += shift <= 1.5 and inks_alike
        if not (shift <= 0.75 and inks_alike):
            outside.append((label.cell, f"shift {shift:.2f} px, ink x{ratio:.2f}", label.text[:30]))
    covered = np.zeros(base_gray.shape, dtype=bool)
    for label in labels0:
        x0, y0, x1, y1 = window(label.image_box)
        covered[y0:y1, x0:x1] = True
    stray = lambda g: int(((np.abs(g - 128) > 40) & ~covered).sum())
    return {"checked": checked, "within": within, "within_1_5": within_loose,
            "max_shift": round(max(shifts, default=0.0), 2),
            "median_shift": round(statistics.median(shifts), 3) if shifts else 0.0,
            "offsets": [(round(size, 1), round(dx, 3), round(dy, 3)) for size, dx, dy in offsets],
            "ink_ratio_range": [round(min(ratios, default=1.0), 2), round(max(ratios, default=1.0), 2)],
            "outside": outside[:8], "stray_ink_px": {"v0": stray(base_gray), "v3": stray(other_gray)}}


def offsets_by_size(report: dict) -> dict:
    """Signed offset of native text against the HTML text (SVG pixels, + is down), per font size, over all figures."""
    grouped: dict[float, list] = {}
    for entry in report["figures"].values():
        for size, dx, dy in entry.get("geometry", {}).get("offsets", []):
            grouped.setdefault(size, []).append((dx, dy))
    return {str(size): {"labels": len(v), "median_dx": round(statistics.median(a for a, _ in v), 2),
                        "median_dy": round(statistics.median(b for _, b in v), 2),
                        "dy_range": [round(min(b for _, b in v), 2), round(max(b for _, b in v), 2)]}
            for size, v in sorted(grouped.items())}


def text_integrity(v0: str, other: str) -> dict:
    """Every Draw.io cell shows the same characters in the same weight, slant and colour as in the baseline."""
    base = {}
    for label in svg_native.labels(v0):
        base.setdefault(label.cell, []).append(label)
    seen = {}
    for label in svg_native.labels(other):
        seen.setdefault(label.cell, []).append(label)
    mismatches = []
    for cell in sorted(set(base) | set(seen)):
        a = [l.signature() for l in base.get(cell, [])]
        b = [l.signature() for l in seen.get(cell, [])]
        if a != b:
            mismatches.append((cell, "".join(c[0] for l in a for c in l)[:40], "".join(c[0] for l in b for c in l)[:40]))
    total = len(set(base) | set(seen))
    return {"cells": total, "mismatched": len(mismatches), "examples": mismatches[:5]}


def export_rules(text: str, v0_text: str) -> list[str]:
    """What scripts/figures/check_figures.py --exports requires, and that the drawing is the same size."""
    problems = []
    if "light-dark(" in text:
        problems.append("light-dark() colors")
    if "color-scheme: light;" not in text:
        problems.append("not forced to the light color scheme")
    if "background-color: #FFFFFF;" not in text[:3000]:
        problems.append("no white background")
    if root_size(text) != root_size(v0_text):
        problems.append(f"drawing size {root_size(text)[:2]} instead of {root_size(v0_text)[:2]}")
    if "<style" in text or "@font-face" in text:
        problems.append("embedded CSS or fonts")
    return problems


def xmllint(paths: list[Path]) -> int:
    tool = shutil.which("xmllint")
    if not tool:
        return -1
    failures = 0
    for start in range(0, len(paths), 40):
        result = subprocess.run([tool, "--noout", *map(str, paths[start:start + 40])], capture_output=True, text=True)
        failures += result.stderr.count("parser error")
    return failures


def compare(selection: list[str], engines: list[str], variants: list[str], pixels: bool) -> dict:
    import numpy as np
    names = choose(selection)
    audit_data = json.loads(read(LAB / "audit.json")) if (LAB / "audit.json").is_file() else {}
    representative = set(audit_data.get("representative", {}).get("figures", []))
    report: dict = {"figures": {}, "set": selection or ["representative"], "variants": variants, "engines": engines,
                    "drawio": audit_data.get("drawio"), "font": audit_data.get("font"),
                    "when": time.strftime("%Y-%m-%d %H:%M")}
    for variant in variants:
        missing = [s for s in names if not variant_path(variant, s).is_file()]
        if missing:
            raise LabError(f"{variant} has not been built for {len(missing)} figures (first: {missing[0]}). Run build first.")
    # sizes, validity, text
    sizes = {v: Counter() for v in ["v0", *variants]}
    for stem in names:
        v0 = read(variant_path("v0", stem))
        entry = {"chapter": chapter_of(stem), "sizes": {}, "problems": {}, "text": {}}
        for variant in ["v0", *variants]:
            data = variant_path(variant, stem).read_bytes()
            entry["sizes"][variant] = {"bytes": len(data), "gzip": gzip_size(data)}
            sizes[variant]["bytes"] += len(data)
            sizes[variant]["gzip"] += entry["sizes"][variant]["gzip"]
            raw_file = variant_path(variant, stem, raw=True)
            if variant != "v0" and raw_file.is_file():
                entry["sizes"][variant]["unstripped"] = raw_file.stat().st_size
                sizes[variant]["unstripped"] += raw_file.stat().st_size
            if variant != "v0":
                entry["problems"][variant] = export_rules(read(variant_path(variant, stem)), v0)
                if variant in ("v2", "v3") and "<image" in read(variant_path(variant, stem)):
                    entry["problems"][variant].append("a raster <image> is left")
                raw = variant_path(variant, stem, raw=True)
                text = read(raw if raw.is_file() else variant_path(variant, stem))
                entry["text"][variant] = text_integrity(v0, text)
                if variant in ("v2", "v3"):
                    counts = Counter(label.kind for label in svg_native.labels(text))
                    entry.setdefault("labels", {})[variant] = dict(counts)
        report["figures"][stem] = entry
    report["totals"] = {v: dict(c) for v, c in sizes.items()}
    report["xmllint_failures"] = {v: xmllint([variant_path(v, s) for s in names]) for v in variants}
    by_chapter: dict[str, Counter] = {}
    for stem, entry in report["figures"].items():
        bucket = by_chapter.setdefault(entry["chapter"], Counter())
        for variant, size in entry["sizes"].items():
            bucket[f"{variant}_bytes"] += size["bytes"]
            bucket[f"{variant}_gzip"] += size["gzip"]
    report["by_chapter"] = {k: dict(v) for k, v in sorted(by_chapter.items())}
    # pixels, per engine
    sheet_candidates = []
    if pixels:
        for engine in engines:
            subset = names if engine == "edge" else [s for s in names if s in representative]
            jobs = [(variant_path(v, s), LAB / "shots" / engine / v / f"{s}.png") for s in subset for v in ["v0", *variants]]
            started = time.time()
            render_many(engine, jobs, workers=4 if engine != "firefox" else 1)
            print(f"{engine}: {len(jobs)} screenshots in {time.time() - started:.0f} s", flush=True)
            for stem in subset:
                base = gray(LAB / "shots" / engine / "v0" / f"{stem}.png")
                for variant in variants:
                    other = gray(LAB / "shots" / engine / variant / f"{stem}.png")
                    metrics = pixel_metrics(base, other)
                    mask = metrics.pop("_mask", None)
                    report["figures"][stem].setdefault("pixels", {}).setdefault(engine, {})[variant] = metrics
                    if engine == "edge" and variant in ("v3", "v2") and mask is not None:
                        sheet_candidates.append((metrics["mismatch_pct"], stem, variant, mask))
                        sheet_candidates.sort(key=lambda item: -item[0])
                        del sheet_candidates[6:]  # keep only the masks of the worst few
        write_sheets_later = sorted(sheet_candidates, key=lambda item: -item[0])[:6]
        if "v3" in variants and "edge" in engines:
            report_geometry(report, names)
        write_sheets(write_sheets_later)
    report["fallback_renderers"] = fallback_renderers(sorted(representative & set(names)), variants) if pixels else {}
    report["crop"] = crop_check(sorted(representative & set(names)), variants) if pixels else {}
    report["native_offsets"] = offsets_by_size(report)
    if "v3" in variants:
        report["why_html"] = why_html(names)
    report["decks"] = decks_effect(report, variants)
    report["page_load"] = page_load(report, variants) if pixels else {}
    report["gates"] = gates(report, variants)
    report["pdf"] = pdf_static()
    (LAB / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    write_report(report)
    return report


def report_geometry(report: dict, names: list[str]) -> None:
    """Text-only renders of v0 and v3 in Edge, then the per-label ink comparison."""
    jobs, todo = [], []
    for stem in names:
        raw = variant_path("v3", stem, raw=True)
        if not raw.is_file() or not any(label.kind == "native" for label in svg_native.labels(read(raw))):
            continue
        for variant, path in (("v0", variant_path("v0", stem)), ("v3", variant_path("v3", stem))):
            target = LAB / "textonly" / variant / f"{stem}.svg"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.is_file() or read(target) != text_only(read(path)):
                target.write_text(text_only(read(path)), encoding="utf-8")
            jobs.append((target, LAB / "shots" / "edge-text" / variant / f"{stem}.png"))
        todo.append(stem)
    render_many("edge", jobs, workers=4)
    for stem in todo:
        v0 = read(variant_path("v0", stem))
        if gray(LAB / "shots" / "edge-text" / "v0" / f"{stem}.png").shape != gray(LAB / "shots" / "edge-text" / "v3" / f"{stem}.png").shape:
            report["figures"][stem]["geometry"] = {"checked": 0, "within": 0, "within_1_5": 0, "offsets": [], "outside": [],
                                                   "stray_ink_px": {"v0": 0, "v3": 0}, "size_differs": True}
            continue
        report["figures"][stem]["geometry"] = native_label_geometry(
            v0, read(variant_path("v3", stem, raw=True)), gray(LAB / "shots" / "edge-text" / "v0" / f"{stem}.png"),
            gray(LAB / "shots" / "edge-text" / "v3" / f"{stem}.png"), root_size(v0)[2])


def write_sheets(candidates: list) -> None:
    """Side by side: the baseline, the variant, and where they differ (red), for the figures that differ most."""
    from PIL import Image
    folder = LAB / "sheets"
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    for percent, stem, variant, mask in candidates:
        with Image.open(LAB / "shots" / "edge" / "v0" / f"{stem}.png") as base, Image.open(LAB / "shots" / "edge" / variant / f"{stem}.png") as other:
            base, other = base.convert("RGB"), other.convert("RGB")
            if base.size != other.size:
                continue
            overlay = base.convert("L").convert("RGB")
            pixels = overlay.load()
            ys, xs = mask.nonzero()
            for y, x in zip(ys.tolist(), xs.tolist()):
                pixels[x, y] = (230, 20, 20)
            sheet = Image.new("RGB", (base.width, base.height * 3 + 20), "white")
            for index, picture in enumerate((base, other, overlay)):
                sheet.paste(picture, (0, index * (base.height + 10)))
            sheet.save(folder / f"{percent:07.3f}-{stem}-{variant}.png")


def fallback_renderers(names: list[str], variants: list[str]) -> dict:
    """Viewers without foreignObject: rsvg-convert and MuPDF. Share of label boxes (the baseline's PNG boxes) with ink."""
    import numpy as np
    from PIL import Image
    result: dict = {}
    rsvg = shutil.which("rsvg-convert") or (r"C:\tools\rsvg-convert.exe" if Path(r"C:\tools\rsvg-convert.exe").is_file() else None)
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            pymupdf = None
    folder = LAB / "shots" / "fallback"
    folder.mkdir(parents=True, exist_ok=True)
    for stem in names:
        v0 = read(variant_path("v0", stem))
        boxes = [label.image_box for label in svg_native.labels(v0) if label.kind == "html" and label.image_box and label.text]
        vb = root_size(v0)[2]
        width = int(root_size(v0)[0] * SCALE)
        for variant in ["v0", *variants]:
            svg = variant_path(variant, stem)
            for tool in (["rsvg"] if rsvg else []) + (["mupdf"] if pymupdf else []):
                png = folder / f"{stem}.{variant}.{tool}.png"
                try:
                    if tool == "rsvg":
                        subprocess.run([rsvg, "-f", "png", "-w", str(width), "-b", "white", "-o", str(png), str(svg)],
                                       check=True, capture_output=True, timeout=120)
                    else:
                        document = pymupdf.open(str(svg))
                        document[0].get_pixmap(matrix=pymupdf.Matrix(SCALE, SCALE)).save(str(png))
                    image = np.asarray(Image.open(png).convert("L"), dtype=np.int16)
                except Exception as exc:  # noqa: BLE001
                    result.setdefault(stem, {}).setdefault(tool, {})[variant] = f"failed: {str(exc)[:80]}"
                    continue
                scale_x = image.shape[1] / root_size(v0)[0]
                with_ink = 0
                for x, y, w, h in boxes:
                    x0, y0 = int((x - vb[0]) * scale_x), int((y - vb[1]) * scale_x)
                    region = image[max(0, y0):int((y + h - vb[1]) * scale_x) + 1, max(0, x0):int((x + w - vb[0]) * scale_x) + 1]
                    if region.size:
                        background = int(np.bincount(region.ravel().astype(np.int64).clip(0, 255)).argmax())
                        with_ink += bool((np.abs(region - background) > 48).sum() >= 4)
                result.setdefault(stem, {}).setdefault(tool, {})[variant] = {"label_boxes": len(boxes), "with_ink": with_ink}
    return result


def crop_check(names: list[str], variants: list[str]) -> dict:
    """The Reveal decks show a detail of a figure: crop the baseline and v2/v3 alike and compare what Edge draws."""
    from scripts.slides.prepare import crop_svg
    result = {}
    folder = LAB / "crop"
    folder.mkdir(parents=True, exist_ok=True)
    for stem in names[:6]:
        crop = (0.0, 0.0, 1.0, 0.55)
        shots = {}
        for variant in ["v0", *variants]:
            target = folder / f"{stem}.{variant}.svg"
            crop_svg(variant_path(variant, stem), target, crop)
            shots[variant] = folder / f"{stem}.{variant}.png"
        render_many("edge", [(folder / f"{stem}.{v}.svg", shots[v]) for v in shots], workers=3)
        base = gray(shots["v0"])
        result[stem] = {v: {k: m[k] for k in m if k != "_mask"} for v in variants
                        for m in [pixel_metrics(base, gray(shots[v]))]}
    return result


def gates(report: dict, variants: list[str]) -> dict:
    names = list(report["figures"])
    totals = report["totals"]
    verdict = {}
    for variant in variants:
        mismatched = sum(report["figures"][s]["text"][variant]["mismatched"] for s in names)
        cells = sum(report["figures"][s]["text"][variant]["cells"] for s in names)
        pixels = [report["figures"][s]["pixels"]["edge"][variant] for s in names if "pixels" in report["figures"][s]
                  and variant in report["figures"][s]["pixels"].get("edge", {})]
        sized = [p for p in pixels if p.get("same_size")]
        percents = [p["mismatch_pct"] for p in sized]
        geometry = [report["figures"][s]["geometry"] for s in names if "geometry" in report["figures"][s]] if variant == "v3" else []
        checked = sum(g["checked"] for g in geometry)
        within = sum(g["within"] for g in geometry)
        loose = sum(g["within_1_5"] for g in geometry)
        stray = sum(max(0, g["stray_ink_px"]["v3"] - g["stray_ink_px"]["v0"]) for g in geometry)
        reduction = 1 - totals[variant]["bytes"] / totals["v0"]["bytes"]
        verdict[variant] = {
            "text_integrity": {"value": 1 - mismatched / max(1, cells), "pass": mismatched == 0},
            "geometry_share": {"value": within / checked if checked else None, "checked": checked,
                               "pass": (within / checked >= GATES["geometry_share"]) if checked else True},
            "geometry_loose": {"value": loose / checked if checked else None, "checked": checked,
                               "pass": (loose / checked >= GATES["geometry_share"]) if checked else True},
            "stray_text_ink": {"value": stray, "pass": stray <= 50},
            "median_pixel_pct": {"value": statistics.median(percents) if percents else None,
                                 "pass": (statistics.median(percents) <= GATES["median_pixel_pct"]) if percents else False},
            "worst_pixel_pct": {"value": max(percents) if percents else None,
                                "pass": (max(percents) <= GATES["worst_pixel_pct"]) if percents else False},
            "all_same_size": {"value": len(sized) == len(pixels), "pass": len(sized) == len(pixels)},
            "size_reduction": {"value": reduction, "pass": reduction >= GATES["size_reduction"]},
            "export_rule_problems": {"value": sum(len(report["figures"][s]["problems"][variant]) for s in names),
                                     "pass": all(not report["figures"][s]["problems"][variant] for s in names)},
            "xmllint": {"value": report["xmllint_failures"].get(variant), "pass": report["xmllint_failures"].get(variant) == 0},
        }
    return verdict


def why_html(names: list[str]) -> dict:
    """Over every label of v2 (all HTML): how many v3 turns into native text, and why each other one stays HTML."""
    meter = svg_native.TextMeter()
    counts: Counter = Counter()
    for stem in names:
        for label in svg_native.labels(read(variant_path("v2", stem, raw=True))):
            counts[svg_native.stays_html_because(label, meter) or "native"] += 1
    return dict(counts)


def decks_effect(report: dict, variants: list[str]) -> dict:
    """What the figures staged for the Reveal decks (slides/_shared/visuals, untracked) would weigh with each variant:
    a crop is a copy of its figure with a narrower viewBox, so it shrinks by its figure's ratio."""
    folder = ROOT / "slides" / "_shared" / "visuals"
    if not folder.is_dir() or len(report["figures"]) < len(stems()):
        return {}
    current = Counter()
    projected = {v: 0.0 for v in variants}
    for path in folder.glob("*.svg"):
        stem = path.name.split(".crop-")[0].removesuffix(".svg")
        entry = report["figures"].get(stem)
        if entry is None:
            continue
        size = path.stat().st_size
        current["bytes"] += size
        current["files"] += 1
        for variant in variants:
            projected[variant] += size * entry["sizes"][variant]["bytes"] / entry["sizes"]["v0"]["bytes"]
    return {"files": current["files"], "bytes": current["bytes"], **{v: round(b) for v, b in projected.items()}}


def page_load(report: dict, variants: list[str], chapters: int = 3, runs: int = 3) -> dict:
    """Edge loads every figure of a chapter as <img> from local files (milliseconds until the page load event: fetch and parse): median per variant,
    for the chapters with the most SVG bytes. A guide to the client's work, not a network measurement."""
    if len(report["figures"]) < len(stems()):
        return {}
    biggest = sorted(report["by_chapter"], key=lambda c: -report["by_chapter"][c]["v0_bytes"])[:chapters]
    exe = find_browser("edge")
    result: dict = {}
    folder = Path(tempfile.mkdtemp(prefix="svg-lab-load-"))
    try:
        for chapter in biggest:
            names = [s for s, e in report["figures"].items() if e["chapter"] == chapter]
            for variant in ["v0", *variants]:
                images = "".join(f'<img src="{variant_path(variant, s).resolve().as_uri()}?run=RUN" width="860">' for s in names)
                times = []
                for run in range(runs):
                    page = folder / f"{chapter}-{variant}-{run}.html"
                    page.write_text("<!doctype html><meta charset='utf-8'><body><script>const t0=performance.now();</script>"
                                    + images.replace("RUN", str(run)) + "<script>window.addEventListener('load', () => {"
                                    "document.body.textContent = 'MS=' + Math.round(performance.now() - t0); });</script></body>", encoding="utf-8")
                    out = subprocess.run([exe, "--headless=new", "--disable-gpu", f"--user-data-dir={folder / 'profile'}", "--dump-dom",
                                          page.as_uri()], capture_output=True, text=True, timeout=300)
                    found = re.search(r"MS=(\d+)", out.stdout)
                    if found:
                        times.append(int(found.group(1)))
                result.setdefault(chapter, {"figures": len(names)})[variant] = statistics.median(times) if times else None
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    return result


def pdf_static() -> dict:
    """The PDF build never draws an SVG: filters/pdf-figures.lua swaps every one for its PDF."""
    lua = read(ROOT / "filters" / "pdf-figures.lua")
    missing = [s for s in stems() if not (PDF_DIR / f"{s}.pdf").is_file()]
    return {"figures_without_pdf": missing, "lua_swaps_svg_for_pdf": "visuals/svg" in lua and ".pdf" in lua,
            "pdf_dir_bytes": sum(p.stat().st_size for p in PDF_DIR.glob("*.pdf"))}


def mb(value: float) -> str:
    return f"{value / 1e6:.2f} MB"


def write_report(report: dict) -> None:
    variants = report["variants"]
    totals = report["totals"]
    base = totals["v0"]
    lines = [f"# SVG lab report ({report['when']})", "",
             f"Figures compared: {len(report['figures'])} ({', '.join(report['set'])}). Draw.io: {report['drawio']}. "
             f"Text measured with: {report['font']}.", "", "## Size", "",
             "| variant | raw | vs v0 | before stripping | gzip (what a visitor downloads) | vs v0 |", "|---|---|---|---|---|---|"]
    for variant in ["v0", *variants]:
        t = totals[variant]
        before = mb(t["unstripped"]) if t.get("unstripped") else "-"
        lines.append(f"| {variant} | {mb(t['bytes'])} | {t['bytes'] / base['bytes'] - 1:+.1%} | {before} | {mb(t['gzip'])} | {t['gzip'] / base['gzip'] - 1:+.1%} |")
    lines += ["", "## Gates", ""]
    names = {"text_integrity": "Text integrity (every cell: same characters, weight, slant, colour)",
             "geometry_share": "Native labels with ink centre within 0.75 px of the HTML label (ink amount 0.85-1.15x)",
             "geometry_loose": "Native labels with ink centre within 1.5 px",
             "stray_text_ink": "Text ink outside every label box, beyond the baseline's (pixels)", "median_pixel_pct": "Median figure pixel difference (%, after 2 px tolerance)",
             "worst_pixel_pct": "Worst figure pixel difference (%)", "all_same_size": "Every drawing keeps its size",
             "size_reduction": "Size reduction (raw)", "export_rule_problems": "check_figures --exports rules (problems)", "xmllint": "xmllint failures"}
    lines += ["| gate | " + " | ".join(variants) + " |", "|---|" + "---|" * len(variants)]
    for key, label in names.items():
        cells = []
        for variant in variants:
            gate = report["gates"][variant][key]
            value = gate["value"]
            shown = "n/a" if value is None else (f"{value:.4f}" if isinstance(value, float) else str(value))
            cells.append(f"{'PASS' if gate['pass'] else 'FAIL'} ({shown})")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines += ["", "## By chapter (SVGs a chapter shows, raw MB)", "",
              "| chapter | " + " | ".join(["v0", *variants]) + " |", "|---|" + "---|" * (len(variants) + 1)]
    for chapter, row in report["by_chapter"].items():
        lines.append(f"| {chapter} | " + " | ".join(f"{row.get(f'{v}_bytes', 0) / 1e6:.2f}" for v in ["v0", *variants]) + " |")
    if report.get("why_html"):
        lines += ["", "## What v3 does with the labels", "",
                  "| outcome | labels |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(report["why_html"].items(), key=lambda kv: -kv[1])]
    if report.get("decks"):
        d = report["decks"]
        lines += ["", "## Figures staged for the Reveal decks (slides/_shared/visuals)", "",
                  f"{d['files']} files, {mb(d['bytes'])} now; with " + ", ".join(f"{v} about {mb(d[v])}" for v in variants) + "."]
    if report.get("page_load"):
        lines += ["", "## Load in Edge (ms until the load event, median of 3, every figure of the chapter as <img> from local files)", "",
                  "| chapter | figures | " + " | ".join(["v0", *variants]) + " |", "|---|---|" + "---|" * (len(variants) + 1)]
        for chapter, row in report["page_load"].items():
            lines.append(f"| {chapter} | {row['figures']} | " + " | ".join(str(row.get(v)) for v in ["v0", *variants]) + " |")
    lines += ["", "## Labels", ""]
    kinds = {v: Counter() for v in variants if v in ("v2", "v3")}
    for entry in report["figures"].values():
        for variant, counts in entry.get("labels", {}).items():
            kinds[variant].update(counts)
    for variant, counts in kinds.items():
        lines.append(f"- {variant}: {dict(counts)}")
    if report.get("native_offsets"):
        lines += ["", "## Where native text sits against HTML text (v3, SVG pixels, + is down)", "",
                  "| font size | labels | median dx | median dy | dy range |", "|---|---|---|---|---|"]
        for size, row in report["native_offsets"].items():
            lines.append(f"| {size} px | {row['labels']} | {row['median_dx']} | {row['median_dy']} | {row['dy_range'][0]} to {row['dy_range'][1]} |")
    lines += ["", "## Per figure (Edge, 2x)", "", "| figure | " + " | ".join(f"{v} size" for v in variants) + " | " +
              " | ".join(f"{v} pixels %" for v in variants) + " |", "|---|" + "---|" * (2 * len(variants))]
    for stem, entry in sorted(report["figures"].items(), key=lambda kv: -kv[1]["sizes"]["v0"]["bytes"])[:40]:
        edge = entry.get("pixels", {}).get("edge", {})
        lines.append(f"| {stem} | " + " | ".join(f"{entry['sizes'][v]['bytes'] / 1e3:.0f} KB" for v in variants) + " | " +
                     " | ".join(str(edge.get(v, {}).get("mismatch_pct", "-")) for v in variants) + " |")
    lines += ["", "## Other engines (representative set)", ""]
    for stem, entry in report["figures"].items():
        for engine, per in entry.get("pixels", {}).items():
            if engine != "edge":
                lines.append(f"- {stem} {engine}: " + ", ".join(f"{v} {m.get('mismatch_pct', m)}%" for v, m in per.items()))
    lines += ["", "## Viewers without foreignObject (label boxes that show ink)", ""]
    for stem, per_tool in report.get("fallback_renderers", {}).items():
        for tool, per_variant in per_tool.items():
            lines.append(f"- {stem} {tool}: " + ", ".join(f"{v} {d['with_ink']}/{d['label_boxes']}" if isinstance(d, dict) else f"{v} {d}"
                                                          for v, d in per_variant.items()))
    lines += ["", "## Crop (as the Reveal decks cut figures)", ""]
    for stem, per in report.get("crop", {}).items():
        lines.append(f"- {stem}: " + ", ".join(f"{v} {m.get('mismatch_pct', m)}%" for v, m in per.items()))
    pdf = report["pdf"]
    lines += ["", "## PDF", "", f"- figures without a vector PDF: {len(pdf['figures_without_pdf'])}; the Lua filter swaps SVG for PDF: "
              f"{pdf['lua_swaps_svg_for_pdf']}; visuals/pdf is {mb(pdf['pdf_dir_bytes'])} and does not depend on the SVGs."]
    (LAB / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {(LAB / 'report.md').relative_to(ROOT)}")
    print("\n".join(lines[:40]))


# ------------------------------------------------------------------------------------------------ determinism


def determinism(selection: list[str], variants: list[str]) -> dict:
    """Export the same figure twice per variant: are the bytes identical?"""
    names = choose(selection)[:8]
    exe = exporter.find_drawio_executable(None)
    meter = svg_native.TextMeter()
    result = {}
    folder = LAB / "determinism"
    for stem in names:
        source = SRC_DIR / f"{stem}.drawio"
        outputs = {}
        for run in (1, 2):
            first = folder / f"{stem}.v2.{run}.svg"
            drawio_export(exe, source, first)
            outputs[f"v2_{run}"] = first.read_bytes()
            if "v3" in variants:
                cells = svg_native.single_line_cells(read(first), meter)
                temporary = folder / f"{stem}.src.{run}.drawio"
                temporary.write_text(svg_native.native_labels_copy(read(source), cells), encoding="utf-8")
                target = folder / f"{stem}.v3.{run}.svg"
                drawio_export(exe, temporary, target)
                outputs[f"v3_{run}"] = target.read_bytes()
        result[stem] = {"v2_identical": outputs["v2_1"] == outputs["v2_2"],
                        **({"v3_identical": outputs["v3_1"] == outputs["v3_2"]} if "v3" in variants else {})}
        print(stem, result[stem], flush=True)
    (LAB / "determinism.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit")
    base = sub.add_parser("baseline")
    base.add_argument("--rev", help="A git revision whose visuals/svg is the baseline (a commit before the plain-text fallback).")
    base.add_argument("--set", nargs="*", default=[], dest="selection", help="Figure names (default: all).")
    for name in ("build", "compare", "determinism"):
        command = sub.add_parser(name)
        command.add_argument("--set", nargs="*", default=["representative"], dest="selection",
                             help="'representative', 'all', or figure names / prefixes.")
        command.add_argument("--variants", nargs="+", default=["v1", "v2", "v3"], choices=["v1", "v2", "v3"])
        if name == "compare":
            command.add_argument("--engines", nargs="+", default=["edge"], choices=list(BROWSERS))
            command.add_argument("--no-pixels", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "audit":
            audit()
        elif args.command == "baseline":
            baseline(args.selection, args.rev)
        elif args.command == "build":
            build(args.variants, args.selection)
        elif args.command == "compare":
            compare(args.selection, args.engines, args.variants, not args.no_pixels)
        else:
            determinism(args.selection, args.variants)
    except (LabError, exporter.ExportError, svg_native.FontMissing, subprocess.CalledProcessError, OSError, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
