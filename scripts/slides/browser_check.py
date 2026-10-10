"""Inspect rendered Reveal decks in installed Chrome with Playwright.

No browser download is attempted. Screenshots and a JSON review record are build
artifacts, not publication assets. Bounds checks supplement a human review of
the screenshots and do not constitute native PowerPoint or screen-reader QA.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import threading
from urllib.parse import quote, urlsplit


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


@contextmanager
def serve(directory: Path):
    """Serve only rendered output, on an ephemeral loopback port."""
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietHandler, directory=str(directory.resolve()))
    )
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def installed_chrome(explicit: Path | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    else:
        for command in ("google-chrome", "google-chrome-stable", "chrome", "chromium"):
            found = shutil.which(command)
            if found:
                candidates.append(Path(found))
        for directory in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                          os.environ.get("LOCALAPPDATA")):
            if directory:
                candidates.append(Path(directory) / "Google/Chrome/Application/chrome.exe")
        candidates.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise RuntimeError("Installed Chrome not found. Supply --chrome PATH; no browser download was attempted.")


def contact_sheet(screenshots: Path) -> str | None:
    """Combine unaltered screenshot thumbnails for a private visual overview."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    paths = sorted(screenshots.glob("desktop-*.png"))
    if not paths:
        return None
    columns, width, height, gutter, label = 4, 400, 225, 12, 28
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * (width + gutter) + gutter,
                              rows * (height + label + gutter) + gutter), "#e3e8eb")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(paths):
        with Image.open(path) as source:
            thumb = source.convert("RGB")
            thumb.thumbnail((width, height))
            x = gutter + (index % columns) * (width + gutter)
            y = gutter + (index // columns) * (height + label + gutter)
            sheet.paste(thumb, (x, y))
            draw.text((x, y + height + 6), path.stem, fill="black")
    path = screenshots / "desktop-contact-sheet.jpg"
    sheet.save(path, quality=90)
    return str(path)


SLIDE_INVENTORY = """() => Reveal.getSlides().map((slide, ordinal) => ({
  ordinal,
  id: slide.id,
  title: (slide.querySelector('h1,h2,h3')?.innerText || '').trim(),
  indices: Reveal.getIndices(slide),
  notes: (slide.querySelector('aside.notes')?.textContent || '').trim(),
  teaching: slide.classList.contains('level2'),
  invalidDate: slide.id === 'title-slide' && /\\bInvalid Date\\b/i.test(slide.textContent),
  unresolvedShortcode: /\\{\\{[<%]\\s*(?:var|meta|include)\\b/.test(slide.textContent)
}))"""


SLIDE_METRICS = """() => {
  const slide = Reveal.getCurrentSlide();
  const viewport = {width: innerWidth, height: innerHeight};
  const issues = [];
  const images = [];
  const fonts = [];
  const epsilon = 2;
  const visible = el => {
    if (el.closest('aside.notes,script,style,[hidden],.speaker-notes')) return false;
    for (let p = el; p && p !== slide.parentElement; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false;
    }
    return !!el.getClientRects().length;
  };
  const rounded = r => ({x: +r.x.toFixed(2), y: +r.y.toFixed(2),
    width: +r.width.toFixed(2), height: +r.height.toFixed(2)});
  const check = (rect, kind, content) => {
    if (rect.width <= 0 || rect.height <= 0) return;
    if (rect.left < -epsilon || rect.top < -epsilon ||
        rect.right > viewport.width + epsilon || rect.bottom > viewport.height + epsilon) {
      issues.push({kind, content: content.slice(0,160), bounds: rounded(rect)});
    }
  };
  // Text ranges catch glyphs that extend beyond a table cell or paragraph box.
  const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!node.textContent.trim() || !visible(node.parentElement)) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    for (const rect of range.getClientRects()) check(rect, 'text-outside-viewport', node.textContent.trim());
    const style = getComputedStyle(node.parentElement);
    fonts.push(parseFloat(style.fontSize) * Reveal.getScale());
  }
  for (const el of slide.querySelectorAll('img,table,pre,svg,video')) {
    if (!visible(el)) continue;
    check(el.getBoundingClientRect(), 'element-outside-viewport', el.tagName + ' ' + (el.alt || el.textContent.trim()));
  }
  for (const el of slide.querySelectorAll('img')) {
    if (!visible(el)) continue;
    images.push({src: el.currentSrc || el.src, alt: el.alt,
      complete: el.complete, naturalWidth: el.naturalWidth, bounds: rounded(el.getBoundingClientRect())});
    if (!el.complete || el.naturalWidth === 0) issues.push({kind:'image-not-loaded', content:el.src});
    if (!el.alt.trim()) issues.push({kind:'image-missing-alt', content:el.src});
  }
  const unexpected = Reveal.getSlides().filter(s => s !== slide && visible(s)).filter(s => {
      const r = s.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 &&
        r.left < viewport.width && r.top < viewport.height;
    }).map(s => s.id);
  if (unexpected.length) issues.push({kind:'other-slide-visible', content:unexpected.join(', ')});
  return {viewport, scale: Reveal.getScale(), images, issues,
    minimumTextSizeOnScreen: fonts.length ? +Math.min(...fonts).toFixed(2) : null,
    scrollSize: {width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight}};
}"""


def move_to(page, indices: dict) -> None:
    page.evaluate("""p => {
      if (Reveal.isScrollView?.()) {
        // Small viewports use Reveal's native scroll view. A direct slide()
        // call can stop on the preceding scroll-snap point in Chrome.
        const target = Reveal.getSlides().find(slide => {
          const index = Reveal.getIndices(slide);
          return index.h === p.h && (index.v || 0) === (p.v || 0);
        });
        target.closest('.scroll-page').scrollIntoView({block: 'start', behavior: 'instant'});
      } else {
        Reveal.slide(p.h, p.v || 0, -1);
      }
    }""", indices)
    try:
        page.wait_for_function(
            "p => { const q = Reveal.getIndices(); return q.h === p.h && (q.v || 0) === (p.v || 0); }",
            arg=indices, timeout=5000,
        )
    except Exception as exc:
        current = page.evaluate("() => ({indices: Reveal.getIndices(), id: Reveal.getCurrentSlide().id})")
        raise RuntimeError(f"Reveal did not navigate to {indices}; current state: {current}") from exc
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    page.wait_for_function(
        "() => Array.from(Reveal.getCurrentSlide().querySelectorAll('img')).every(i => i.complete)",
        timeout=10000,
    )


def inspect_steps(page, slide: dict, screenshots: Path) -> dict:
    """Exercise real advance/back keys and check that hidden content keeps its space."""
    state_script = """() => Array.from(Reveal.getCurrentSlide().querySelectorAll('.fragment')).map(el => {
      const r = el.getBoundingClientRect();
      return {index: +el.dataset.fragmentIndex, visible: el.classList.contains('visible'),
        x: r.x, y: r.y, width: r.width, height: r.height};
    })"""
    before = page.evaluate(state_script)
    if not before:
        return {"count": 0, "passed": True}
    groups = sorted({item["index"] for item in before})
    errors = []
    if any(item["visible"] for item in before):
        errors.append("A later point is visible before the first advance")
    page.screenshot(path=str(screenshots / f"steps-{slide['ordinal'] + 1:02d}-start.png"))
    for index in groups:
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(30)
        after = page.evaluate(state_script)
        if page.evaluate("() => Reveal.getCurrentSlide().id") != slide["id"]:
            errors.append("Advance left the slide before revealing all points")
            break
        for old, new in zip(before, after):
            if new["visible"] != (new["index"] <= index):
                errors.append(f"Fragment {new['index']} has incorrect visibility at step {index}")
            if any(abs(new[key] - old[key]) > 1 for key in ("x", "y", "width", "height")):
                errors.append("Content moved when the next point appeared")
        if page.evaluate(SLIDE_METRICS)["issues"]:
            errors.append(f"Content bounds failed at step {index}")
        page.screenshot(path=str(screenshots / f"steps-{slide['ordinal'] + 1:02d}-{index:02d}.png"))
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(30)
    if page.evaluate("() => Reveal.getCurrentSlide().id") != slide["id"]:
        errors.append("Back left the slide instead of hiding its final point")
    elif any(item["visible"] for item in page.evaluate(state_script) if item["index"] == groups[-1]):
        errors.append("Back did not hide the final point")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(30)
    return {"count": len(groups), "passed": not errors, "errors": errors}


def inspect_deck(context, url: str, chapter: str, screenshots: Path) -> dict:
    page = context.new_page()
    runtime_errors: list[str] = []
    failed_requests: list[dict] = []
    remote_requests: list[str] = []
    origin = urlsplit(url).netloc
    page.on("pageerror", lambda error: runtime_errors.append(str(error)))

    def response_received(response) -> None:
        if response.status >= 400 and not response.url.endswith("favicon.ico"):
            failed_requests.append({"url": response.url, "status": response.status})

    def request_failed(request) -> None:
        if not request.url.endswith("favicon.ico"):
            failed_requests.append({"url": request.url, "failure": request.failure})

    def route_request(route) -> None:
        parsed = urlsplit(route.request.url)
        if parsed.scheme in {"http", "https"} and parsed.netloc != origin:
            remote_requests.append(route.request.url)
            route.abort()
        else:
            route.continue_()

    page.on("response", response_received)
    page.on("requestfailed", request_failed)
    page.route("**/*", route_request)
    page.set_viewport_size({"width": 1600, "height": 900})
    page.goto(url, wait_until="networkidle")
    page.wait_for_function("() => typeof Reveal !== 'undefined' && Reveal.isReady()")
    page.evaluate("() => document.fonts.ready")
    inventory = page.evaluate(SLIDE_INVENTORY)
    screenshots.mkdir(parents=True, exist_ok=True)
    # Remove obsolete states owned by this checker after a fragment revision.
    for old in screenshots.glob('steps-*.png'):
        if old.is_file() and not old.is_symlink():
            old.unlink()
    result = {"chapter": chapter, "url": url, "slideCount": len(inventory),
              "teachingSlideCount": sum(slide["teaching"] for slide in inventory),
              "slides": [], "checks": {}, "errors": []}
    if not inventory:
        raise RuntimeError(f"{chapter}: Reveal initialized without any slides")

    for slide in inventory:
        entry = {key: slide[key] for key in ("ordinal", "id", "title", "indices", "teaching")}
        entry["notesPresent"] = bool(slide["notes"])
        if slide["invalidDate"]:
            result["errors"].append(f"Opening slide {slide['id']} contains Invalid Date")
        if slide["unresolvedShortcode"]:
            result["errors"].append(f"Slide {slide['id']} contains an unresolved variable/include shortcode")
        if slide["teaching"] and not slide["notes"]:
            result["errors"].append(f"Teaching slide {slide['id']} has no notes")
        move_to(page, slide["indices"])
        entry["steps"] = inspect_steps(page, slide, screenshots)
        result["errors"].extend(f"{slide['id']}: {error}" for error in entry["steps"].get("errors", []))
        entry["desktop"] = page.evaluate(SLIDE_METRICS)
        screenshot = screenshots / f"desktop-{slide['ordinal'] + 1:02d}.png"
        page.screenshot(path=str(screenshot), full_page=False)
        entry["desktop"]["screenshot"] = str(screenshot)
        result["slides"].append(entry)

    # Reveal scales a fixed presentation canvas on narrow screens. Record the
    # effective type size rather than claiming that a phone view is classroom-readable.
    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate("() => Reveal.layout()")
    for slide, entry in zip(inventory, result["slides"]):
        move_to(page, slide["indices"])
        # Geometry review covers the complete content, even when scroll-view
        # navigation stops before the final fragment's reveal position.
        page.evaluate("() => Reveal.getCurrentSlide().querySelectorAll('.fragment').forEach(el => el.classList.add('visible'))")
        entry["narrow"] = page.evaluate(SLIDE_METRICS)
        screenshot = screenshots / f"narrow-{slide['ordinal'] + 1:02d}.png"
        page.screenshot(path=str(screenshot), full_page=False)
        entry["narrow"]["screenshot"] = str(screenshot)

    page.set_viewport_size({"width": 1600, "height": 900})
    page.evaluate("() => Reveal.layout()")
    move_to(page, inventory[0]["indices"])
    previous = page.evaluate("() => Reveal.getCurrentSlide().id")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(200)
    following = page.evaluate("() => Reveal.getCurrentSlide().id")
    result["checks"]["keyboardNavigation"] = {"passed": following != previous,
                                               "from": previous, "to": following}

    note_slide = next((item for item in inventory if item["teaching"] and item["notes"]), None)
    if note_slide:
        move_to(page, note_slide["indices"])
        try:
            with context.expect_page(timeout=10000) as popup_info:
                page.keyboard.press("s")
            popup = popup_info.value
            popup.wait_for_load_state("domcontentloaded")
            # The speaker view shows the current slide's notes; look for their opening words.
            opening = " ".join(note_slide["notes"].split()[:6])
            popup.wait_for_function(r"(text) => document.body.innerText.replace(/\s+/g, ' ').includes(text)",
                                    arg=opening, timeout=10000)
            popup.screenshot(path=str(screenshots / "speaker-view.png"))
            result["checks"]["speakerView"] = {"passed": True, "url": popup.url, "notesVisible": True}
            popup.close()
        except Exception as exc:
            result["checks"]["speakerView"] = {"passed": False, "error": str(exc)}
    else:
        result["checks"]["speakerView"] = {"passed": False, "error": "No teaching slide notes found"}

    result["checks"]["runtimeErrors"] = runtime_errors
    result["checks"]["failedResources"] = failed_requests
    result["checks"]["externalRuntimeDependencies"] = sorted(set(remote_requests))
    for entry in result["slides"]:
        for view in ("desktop", "narrow"):
            for issue in entry[view]["issues"]:
                result["errors"].append(f"{entry['id']} {view}: {issue['kind']}: {issue['content']}")
    if runtime_errors or failed_requests or remote_requests:
        result["errors"].append("Browser runtime or resource checks failed; inspect checks for details")
    if not result["checks"]["keyboardNavigation"]["passed"]:
        result["errors"].append("ArrowRight did not navigate from the opening slide")
    if not result["checks"]["speakerView"]["passed"]:
        result["errors"].append("Speaker-view popup did not display public teaching notes")
    result["status"] = "passed" if not result["errors"] else "failed"
    result["contactSheet"] = contact_sheet(screenshots)
    page.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--chapter", action="append",
                        help="chapter-NN or case-part-N, repeatable; defaults to all rendered decks")
    parser.add_argument("--chrome", type=Path, help="Path to installed Chrome")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "slides/_build/revealjs"
    report_path = args.report or root / "outputs/build/browser-review.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot_root = report_path.parent / "browser-review"
    report = {
        "schemaVersion": 1,
        "reviewedAt": datetime.now(timezone.utc).isoformat(),
        "status": "unverified",
        "browser": {},
        "nativePowerPoint": "unverified: this script does not open or inspect PowerPoint",
        "humanVisualReview": "required: inspect all generated screenshots for visual quality",
        "screenReaderReview": "unverified: DOM bounds and alt text do not test reading order or screen readers",
        "narrowScreenNote": "Reveal scales the canvas; effective type sizes are recorded without a readability claim",
        "decks": [],
        "errors": [],
    }
    try:
        from playwright.sync_api import sync_playwright

        chrome = installed_chrome(args.chrome)
        decks = ([output / name / "index.html" for name in args.chapter] if args.chapter else
                 sorted(path for pattern in ("chapter-*", "case-part-*") for path in output.glob(f"{pattern}/index.html")))
        if not decks or any(not path.is_file() for path in decks):
            raise RuntimeError("Rendered decks are missing. Render slides before running browser review.")
        with serve(output) as base_url, sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=str(chrome), headless=True)
            report["browser"] = {"executable": str(chrome), "version": browser.version, "headless": True}
            context = browser.new_context(device_scale_factor=1, reduced_motion="reduce")
            try:
                for path in decks:
                    chapter = path.parent.name
                    url = base_url + "/" + quote(path.relative_to(output).as_posix())
                    try:
                        deck = inspect_deck(context, url, chapter, screenshot_root / chapter)
                        deck["renderedHtmlSha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                        report["decks"].append(deck)
                    except Exception as exc:
                        report["decks"].append({"chapter": chapter, "status": "failed", "errors": [str(exc)]})
                report["status"] = "passed" if all(deck["status"] == "passed" for deck in report["decks"]) else "failed"
            finally:
                context.close()
                browser.close()
    except Exception as exc:
        report["errors"].append(str(exc))
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Browser review {report['status']}: {report_path}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    for deck in report["decks"]:
        for error in deck.get("errors", []):
            print(f"ERROR: {deck['chapter']}: {error}")
    return 0 if report["status"] == "passed" else (2 if report["status"] == "unverified" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
