#!/usr/bin/env python3
"""Build the EPUB and the DOCX with optimized diagrams, check them, and report what the optimization saved.

    python scripts/build_ebooks.py                  # both formats
    python scripts/build_ebooks.py --epub           # one format (or --docx)
    python scripts/build_ebooks.py --force-figures  # render every diagram again
    python scripts/build_ebooks.py --baseline       # also build the same text with SVG diagrams, to compare

The EPUB and the DOCX carry a PNG of each diagram in place of its SVG (filters/raster-figures.lua, scripts/figure_raster.py).
This script makes the PNGs first, with progress (a render of --to epub or --to docx would make any that are missing
itself, but quietly), renders each format with Quarto into _book/, copies it to outputs/build/downloads/book-latest.<ext>
(the files scripts/build_all.py and scripts/release.py use), and checks it (scripts/ebook_validate.py). The report is
written to outputs/build/ebook-report.json. The exit status is 1 when a check fails.

The website and the PDF are not touched: `quarto render --to html` and `--to pdf` run exactly as before.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import ebook_validate, figure_raster  # noqa: E402

DOWNLOADS = "outputs/build/downloads"
BASELINES = "outputs/ebook-baseline"
REPORT = "outputs/build/ebook-report.json"
PRODUCT = "_book/Accounting-Analytics.{ext}"


def find_quarto() -> str:
    from scripts.slides.prepare import find_quarto as find
    return find()


def render(root: Path, quarto: str, fmt: str, destination: Path, *, svg: bool = False) -> Path:
    """Render one format with Quarto and copy the product to `destination`."""
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["AA_PYTHON"] = sys.executable
    if svg:
        env["AA_EBOOK_FIGURES"] = "svg"
    else:
        env.pop("AA_EBOOK_FIGURES", None)
    print(f"+ quarto render --to {fmt}{' (SVG diagrams, for the comparison)' if svg else ''}", flush=True)
    subprocess.run([quarto, "render", "--to", fmt], cwd=root, env=env, check=True)
    product = root / PRODUCT.format(ext=fmt)
    if not product.is_file():
        raise RuntimeError(f"Quarto did not create {product}.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(product, destination)
    return destination


def build(root: Path, formats: list[str], *, force_figures: bool = False, baseline: bool = False,
          compare_with: Path | None = None, validate: bool = True, quarto: str | None = None) -> int:
    quarto = quarto or find_quarto()
    downloads = root / DOWNLOADS
    baselines = compare_with or root / BASELINES

    print("Making the optimized diagrams (cached: only new or changed ones are rendered).", flush=True)
    results = figure_raster.ensure(root, None, force=force_figures, log=lambda m: print(m, flush=True))
    summary = figure_raster.summarize(results)
    print(f"{summary['figures']} diagrams: {summary['rendered']} rendered, {summary['reduced']} reduced again, "
          f"{summary['cached']} cached; {summary['png_bytes'] / 1e6:.1f} MB of PNG against "
          f"{summary['svg_bytes'] / 1e6:.1f} MB of SVG.", flush=True)

    built: dict[str, Path] = {}
    for fmt in formats:
        if baseline:
            render(root, quarto, fmt, baselines / f"book-latest.{fmt}", svg=True)
        built[fmt] = render(root, quarto, fmt, downloads / f"book-latest.{fmt}")

    if not validate:
        return 0
    reports: list[ebook_validate.Report] = []
    compared: dict[str, Path | None] = {}
    for fmt, path in built.items():
        old = baselines / f"book-latest.{fmt}"
        compared[fmt] = old if old.is_file() else None
        if fmt == "epub":
            report = ebook_validate.validate_epub(path, expect_figures=summary["figures"])
            ebook_validate.run_epubcheck(path, report)
            reports.append(report)
            if compared[fmt]:
                reports.append(ebook_validate.compare_epub(old, path))
        else:
            reports.append(ebook_validate.validate_docx(path, expect_figures=summary["figures"]))
            if compared[fmt]:
                reports.append(ebook_validate.compare_docx(old, path))
    ebook_validate.print_report(reports, compared)
    report_path = root / REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"figures": summary, "reports": [r.as_dict() for r in reports]}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"Report: {report_path.relative_to(root)}")
    return 0 if all(r.ok for r in reports) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--epub", action="store_true", help="Build the EPUB.")
    parser.add_argument("--docx", action="store_true", help="Build the DOCX.")
    parser.add_argument("--force-figures", action="store_true", help="Render every diagram again.")
    parser.add_argument("--baseline", action="store_true",
                        help=f"Also build each format with SVG diagrams into {BASELINES}/ and compare with it.")
    parser.add_argument("--compare-with", type=Path, metavar="DIR",
                        help="Compare with book-latest.<ext> files already in this folder (built from the same text).")
    parser.add_argument("--no-validate", action="store_true", help="Build only.")
    parser.add_argument("--quarto", help="Explicit Quarto executable, or set QUARTO_BIN.")
    args = parser.parse_args(argv)
    formats = [fmt for fmt in ("epub", "docx") if getattr(args, fmt)] or ["epub", "docx"]
    try:
        return build(ROOT, formats, force_figures=args.force_figures, baseline=args.baseline,
                     compare_with=args.compare_with, validate=not args.no_validate, quarto=args.quarto)
    except (figure_raster.RasterError, RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
