"""Compare a published chapter deck with its local render and check resources.

Writes a disposable report. It never changes approval records or deploys files.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit, urlencode
from urllib.request import Request, urlopen
import zipfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.build_all import source_checks
from scripts.slides.verify import (active_chapters, css_resources, load_manifest,
                                  safe_path, verify_outputs)


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Accounting Analytics publication verification",
                                    "Cache-Control": "no-cache"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise ValueError(f"Resource returned HTTP {response.status}: {url}")
        return response.read()


class Resources(HTMLParser):
    def __init__(self, base: str):
        super().__init__()
        self.base = base
        self.urls: set[str] = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        ref = (values.get("src") if tag in {"img", "script"}
               else values.get("href") if tag == "link" else None)
        if ref and not urlsplit(ref).scheme and not ref.startswith("//"):
            self.urls.add(urljoin(self.base, ref))


def powerpoint_parts(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()
                if name.startswith(("ppt/slides/", "ppt/notesSlides/", "ppt/media/"))}


def verify_published(root: Path, chapter_id: str, *, base_url: str | None = None,
                     release: str | None = None) -> dict:
    root = root.resolve()
    manifest = load_manifest(root / "slides/manifest.yml")
    chapter = next((item for item in active_chapters(manifest, public_only=True)
                    if item["id"] == chapter_id), None)
    if chapter is None:
        raise ValueError(f"Expected an approved chapter: {chapter_id}")
    errors = source_checks(root, manifest, chapter_id)
    errors += verify_outputs(root, {**manifest, "chapters": [chapter]})
    if errors:
        raise ValueError("Local render validation failed:\n" + "\n".join(errors))
    base_url = (base_url or manifest["book_url"]).rstrip("/") + "/"
    if urlsplit(base_url).scheme not in {"http", "https"}:
        raise ValueError("Published site URL must use HTTP or HTTPS.")
    base = urljoin(base_url, f"slides/{chapter_id}/")
    query = "?" + urlencode({"release": release or datetime.now(timezone.utc).isoformat()})
    document = fetch(base + "index.html" + query)
    local = safe_path(root, f"slides/_build/revealjs/{chapter_id}/index.html")
    if document != local.read_bytes():
        raise ValueError(f"Published Reveal HTML differs from the local render: {chapter_id}")
    resources = Resources(base + "index.html")
    resources.feed(document.decode("utf-8"))
    speaker_view = urljoin(base, "index_files/libs/revealjs/plugin/notes/speaker-view.html")
    resources.urls.add(speaker_view)
    # Validate CSS dependencies as well as the script/image/style URLs in HTML.
    checked: set[str] = set()
    pending = set(resources.urls)
    while pending:
        urls = sorted(pending - checked)
        if not urls:
            break
        with ThreadPoolExecutor(max_workers=6) as pool:
            contents = list(pool.map(fetch, urls))
        checked.update(urls)
        pending = set()
        for url, content in zip(urls, contents):
            if urlsplit(url).path.endswith(".css"):
                for ref in css_resources(content.decode("utf-8-sig")):
                    if not urlsplit(ref).scheme and not ref.startswith("//"):
                        pending.add(urljoin(url, ref))
    published = fetch(base + chapter_id + ".pptx" + query)
    local = safe_path(root, f"slides/_build/pptx/{chapter_id}/{chapter_id}.pptx")
    parts = powerpoint_parts(published)
    if parts != powerpoint_parts(local.read_bytes()):
        raise ValueError(f"Published PowerPoint slides, notes, or images differ: {chapter_id}")
    count = sum(bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", name)) for name in parts)
    book_source = next(path for path in chapter["book_sources"] if path.endswith("/chapter.qmd"))
    book = fetch(urljoin(base_url, book_source.replace(".qmd", ".html")) + query).decode("utf-8")
    for target in (f"slides/{chapter_id}/index.html", f"slides/{chapter_id}/{chapter_id}.pptx"):
        if target not in book:
            raise ValueError(f"Published book chapter is missing its slide link: {target}")
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "chapter": chapter_id,
              "status": "passed", "reveal_url": base + "index.html",
              "pptx_url": base + chapter_id + ".pptx", "slides": count,
              "html_matches_local_render": True, "powerpoint_slide_note_media_parts_match": True,
              "local_resources_checked": len(checked), "speaker_view_resource": "passed",
              "book_links": "passed"}
    path = safe_path(root, f"outputs/build/{chapter_id}/live-site-verification.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--chapter", default="chapter-01")
    parser.add_argument("--base-url", help="Published book root; defaults to the manifest's book_url")
    parser.add_argument("--release", help="Optional revision for cache-busting requests")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_published(args.root, args.chapter,
                                        base_url=args.base_url, release=args.release), indent=2))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
