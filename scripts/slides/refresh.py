#!/usr/bin/env python3
"""Refresh approved public slide facts and figures from the pinned read-only dataset.

Normal publication calls check_fresh() and uses the committed results. Only the
authoring refresh reads datasets/. Requires PyYAML and rsvg-convert on PATH (or
RSVG_CONVERT pointing to it) to create the high-resolution PowerPoint PNGs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from shared.calculations.chapter01 import WORKFLOW_STAGES, salesorder_sample, source_trace
from shared.calculations.invoice_margin import quarterly_margin

GENERATORS = (
    "shared/calculations/chapter01.py",
    "shared/calculations/invoice_margin.py",
    "scripts/slides/refresh.py",
)
OUTPUT = Path("shared/generated/chapter-01")
ASSET_NAMES = ("workflow", "source-trace", "furniture-margin", "salesorder-focus")
INK, BLUE, TEAL, AMBER = "#2C3E50", "#1A5276", "#117A65", "#8A5D00"
GRAY, RULE, TINT, WHITE = "#5D6D7E", "#CAD3DA", "#EAF2F8", "#FFFFFF"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _content_hash(path: Path) -> str:
    """Normalize text newlines so Windows checkouts and Linux CI agree."""
    if path.suffix in {".py", ".qmd", ".svg", ".csv"}:
        return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    return sha256(path)


def _pin(root: Path) -> dict:
    import yaml

    values = yaml.safe_load((root / "_variables.yml").read_text(encoding="utf-8"))
    return {"edition": str(values["edition"]), "version": values["dataset"]["version"],
            "sha256": values["dataset"]["sha256"]["sqlite"]}


def _source_hashes(root: Path) -> dict:
    return {name: _content_hash(root / name) for name in GENERATORS}


def check_fresh(root: Path) -> list[str]:
    """Dataset-free verification of source freshness and every committed artifact."""
    root = root.resolve()
    target = root / OUTPUT
    path = target / "facts.json"
    if not path.is_file():
        return ["Missing shared/generated/chapter-01/facts.json; run --refresh-shared."]
    try:
        facts = json.loads(path.read_text(encoding="utf-8"))
        errors = []
        if facts.get("schema_version") != 1:
            errors.append("Unsupported public slide facts schema.")
        if facts.get("dataset") != _pin(root):
            errors.append("The pinned dataset or edition changed; run --refresh-shared.")
        if facts.get("generator_sha256") != _source_hashes(root):
            errors.append("Public slide calculation/figure source changed; run --refresh-shared.")
        expected = {f"{name}.{ext}" for name in ASSET_NAMES for ext in ("svg", "png")}
        expected.update(("furniture-margin.csv", "_furniture-table.qmd"))
        artifacts = facts.get("artifact_sha256", {})
        if set(artifacts) != expected:
            errors.append("The public slide artifact inventory is incomplete or unexpected.")
        for name in sorted(expected):
            artifact = target / name
            if not artifact.is_file() or artifacts.get(name) != _content_hash(artifact):
                errors.append(f"Missing or modified public slide artifact: {name}")
        return errors
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"Cannot validate public slide facts: {exc}"]


def _text(x: float, y: float, value: str, size: int = 28, color: str = INK,
          weight: str = "normal", anchor: str = "start") -> str:
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{html.escape(value)}</text>')


def _rect(x: float, y: float, w: float, h: float, fill: str = WHITE,
          stroke: str = RULE, radius: int = 10, width: int = 2) -> str:
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')


def _line(x1: float, y1: float, x2: float, y2: float, color: str = GRAY,
          arrow: bool = False, dashed: bool = False) -> str:
    return (f'<path d="M{x1:g},{y1:g} L{x2:g},{y2:g}" fill="none" stroke="{color}" '
            f'stroke-width="3"' + (' marker-end="url(#arrow)"' if arrow else "")
            + (' stroke-dasharray="9 6"' if dashed else "") + '/>')


def _svg(title: str, description: str, content: list[str], width: int = 1280,
         height: int = 600) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{html.escape(title)}</title>\n'
            f'<desc id="desc">{html.escape(description)}</desc>\n'
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" '
            'refY="5" orient="auto"><path d="M0,0 L9,5 L0,10" fill="none" '
            f'stroke="{GRAY}" stroke-width="1.5"/></marker></defs>\n'
            f'<rect width="100%" height="100%" fill="{WHITE}"/>\n'
            '<g font-family="Arial, Liberation Sans, sans-serif">\n' + "\n".join(content)
            + "\n</g>\n</svg>\n")


def workflow_svg() -> str:
    content = []
    spots = [(30, 26), (460, 26), (890, 26), (890, 330), (460, 330), (30, 330)]
    # Presentation profile: focused phrases at ~20 pt when shown 12 inches wide.
    # These summarize the canonical stages; the book keeps their full descriptions.
    focused = ("Frame a specific\nbusiness question.", "Choose relevant\ntables and columns.",
               "Fix missing values,\nduplicates, formats.", "Summarize, compare,\nmodel, find anomalies.",
               "Make evidence clear\nfor stakeholders.", "Explain findings to\ndecision makers.")
    for index, ((title, body), (x, y)) in enumerate(zip(WORKFLOW_STAGES, spots)):
        color = BLUE if index < 3 else TEAL
        content.append(_rect(x, y, 360, 220, TINT if index < 3 else "#E8F6F3", color))
        short_title = " ".join(title.split()[:2])
        content.append(_text(x + 20, y + 44, short_title, 34, color, "bold"))
        for line, words in enumerate(focused[index].splitlines()):
            content.append(_text(x + 20, y + 103 + line * 44, words, 32))
    for x1, y1, x2, y2 in ((394, 136, 446, 136), (824, 136, 876, 136),
                           (1070, 252, 1070, 310), (884, 440, 832, 440), (454, 440, 402, 440)):
        content.append(_line(x1, y1, x2, y2, arrow=True))
    return _svg("The accounting analytics workflow",
                "Six stages read clockwise: define the question, access the data, prepare and clean, "
                "analyze, visualize and present, and communicate findings. Each stage feeds the next.",
                content, height=580)


def trace_svg(trace: dict) -> str:
    content = []
    cards = [
        (30, f'GLEntry {trace["gl_entry_id"]}',
         [f'Credit: ${trace["credit"]:,.2f}', f'Account: {trace["account_number"]}',
          "Revenue posting", trace["posting_date"]]),
        (460, f'SalesInvoice {trace["invoice_id"]}',
         [trace["invoice_number"], trace["invoice_date"], "Source document", "for this posting"]),
        (890, f'Line {trace["invoice_line_id"]}',
         [f'Quantity: {trace["quantity"]:g}', f'Unit price: ${trace["unit_price"]:,.2f}',
          f'Line total: ${trace["line_total"]:,.2f}', trace["item_code"]]),
    ]
    for x, title, lines in cards:
        content.append(_rect(x, 90, 360, 280, TINT, BLUE))
        content.append(_text(x + 20, 137, title, 32, BLUE, "bold"))
        for index, line in enumerate(lines):
            content.append(_text(x + 20, 195 + index * 44, str(line), 32))
    content.append(_text(210, 52, "Posting", 34, BLUE, "bold", "middle"))
    content.append(_text(640, 52, "Document", 34, BLUE, "bold", "middle"))
    content.append(_text(1070, 52, "Document line", 34, BLUE, "bold", "middle"))
    content.append(_line(396, 230, 444, 230, arrow=True, dashed=True))
    content.append(_line(826, 230, 874, 230, arrow=True, dashed=True))
    content.append(_text(640, 426, 'SourceDocumentType + SourceDocumentID + SourceLineID', 32,
                         AMBER, "bold", "middle"))
    content.append(_text(640, 482, "One revenue posting; not a complete journal entry.", 32,
                         INK, anchor="middle"))
    return _svg("Trace one revenue posting to its source",
                f'GLEntry {trace["gl_entry_id"]} is a revenue credit of ${trace["credit"]:,.2f}. '
                f'The source fields identify SalesInvoice {trace["invoice_id"]} and '
                f'line {trace["invoice_line_id"]}, with quantity {trace["quantity"]:g} '
                f'at ${trace["unit_price"]:,.2f} each. This is one posting, not the complete journal entry.',
                content, height=520)


def margin_svg(quarters: list[dict], year: int) -> str:
    content = []
    left, right, top, bottom = 140, 1220, 100, 460
    content.append(_text(left, 43, "Invoice-based margin at standard cost", 34, BLUE, "bold"))
    content.append(_text(left, 81, f"Furniture | fiscal {year}", 32, GRAY))
    # A zero baseline preserves scale; the labels provide precise comparison.
    maximum = max(0.6, max(q["margin_rate"] or 0 for q in quarters) * 1.15)
    minimum = min(0, min(q["margin_rate"] or 0 for q in quarters) * 1.15)
    scale = lambda rate: bottom - (rate - minimum) / (maximum - minimum) * (bottom - top)
    for rate in (0.0, 0.2, 0.4, 0.6):
        y = scale(rate)
        content.append(_line(left, y, right, y, color=RULE))
        content.append(_text(left - 18, y + 10, f"{rate:.0%}", 32, GRAY, anchor="end"))
    previous = None
    for index, quarter in enumerate(quarters):
        x = left + 115 + index * 280
        rate = quarter["margin_rate"]
        content.append(_text(x, bottom + 49, quarter["period"].split("-")[1], 34,
                             INK, "bold", "middle"))
        if rate is None:
            content.append(_text(x, top + 140, "No revenue", 32, GRAY, anchor="middle"))
            previous = None
            continue
        y = scale(rate)
        if previous:
            content.append(_line(*previous, x, y, BLUE))
        content.append(f'<circle cx="{x}" cy="{y:g}" r="8" fill="{BLUE}"/>')
        content.append(_text(x, y - 24, f"{rate:.2%}", 34, BLUE, "bold", "middle"))
        previous = (x, y)
    content.append(_text(left, 561, "Margin rate = (revenue − extended standard cost) ÷ revenue",
                         32, GRAY))
    labels = "; ".join(f'{q["period"]}: {q["margin_rate"]:.2%}' if q["margin_rate"] is not None
                       else f'{q["period"]}: undefined because revenue is zero' for q in quarters)
    return _svg(f"Furniture margin rates in {year}",
                labels + ". The vertical axis starts at zero. These are invoice-based rates at standard cost.",
                content, height=600)


def salesorder_svg(rows: list[dict]) -> str:
    content = [_text(32, 46, "SalesOrder — first three data rows", 34, BLUE, "bold")]
    xs, widths = [32, 264, 662, 960], [232, 398, 298, 288]
    headers = ["SalesOrderID", "OrderNumber", "OrderDate", "CustomerID"]
    keys = ["sales_order_id", "order_number", "order_date", "customer_id"]
    for column, (x, width, header) in enumerate(zip(xs, widths, headers)):
        for row_index in range(4):
            y = 79 + row_index * 64
            fill = "#FEF5E7" if column == 3 else TINT if row_index == 0 else WHITE
            content.append(_rect(x, y, width, 64, fill, RULE, radius=0))
            value = header if row_index == 0 else str(rows[row_index - 1][keys[column]])
            content.append(_text(x + 15, y + 42, value, 32, INK,
                                 "bold" if row_index == 0 or column == 3 else "normal"))
    content.append(_rect(xs[3], 79, widths[3], 256, "none", AMBER, radius=0, width=4))
    content.append(_line(1104, 345, 1104, 406, AMBER, arrow=True))
    first = rows[0]
    content.append(_rect(32, 422, 1216, 100, "#E8F6F3", TEAL))
    content.append(_text(56, 462, "Customer lookup: order 1", 32, TEAL, "bold"))
    content.append(_text(56, 501, f'CustomerID {first["customer_id"]} → {first["customer_name"]}', 32))
    content.append(_text(530, 481, "Look up the key; row positions can differ.", 32, TEAL))
    return _svg("A focused mock of the SalesOrder worksheet",
                "First three SalesOrder rows with SalesOrderID, OrderNumber, OrderDate, and CustomerID. "
                f'CustomerID is outlined. The first order has CustomerID {first["customer_id"]}, '
                f'which identifies {first["customer_name"]} in the Customer table. '
                "This is a mock of actual dataset rows, not a live Excel screenshot.",
                content, height=555)


def _write_table(path: Path, quarters: list[dict], year: int) -> None:
    a, b = quarters[2:]
    money = lambda value: f"${value:,.2f}"
    percent = lambda value: f"{value:.2%}" if value is not None else "Undefined"
    lines = [f"Furniture · fiscal {year} · invoice-based margin at standard cost", "",
             "| Measure | Q3 | Q4 |", "|:--|--:|--:|"]
    for label, key, display in (("Invoiced revenue", "revenue", money),
                                 ("Extended standard cost", "standard_cost", money),
                                 ("Margin", "margin", money), ("Margin rate", "margin_rate", percent)):
        lines.append(f"| {label} | {display(a[key])} | {display(b[key])} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def refresh(root: Path) -> None:
    root = root.resolve()
    pin = _pin(root)
    database = (Path(os.environ.get("CHARLESRIVER_DATA", root / "datasets"))
                / "CharlesRiver.sqlite").resolve()
    before = sha256(database)
    if before != pin["sha256"]:
        raise ValueError("Dataset SHA-256 differs from _variables.yml; public facts were not changed.")
    renderer = os.environ.get("RSVG_CONVERT") or shutil.which("rsvg-convert")
    if not renderer:
        raise RuntimeError("rsvg-convert is required for --refresh-shared; public builds use committed PNGs.")
    year = int(pin["edition"])
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    try:
        quarters = quarterly_margin(connection, year, "Furniture")
        trace = source_trace(connection)
        sample = salesorder_sample(connection)
    finally:
        connection.close()
    if sha256(database) != before:
        raise RuntimeError("The dataset changed during the read-only refresh; retry after investigating.")
    target = root / OUTPUT
    target.mkdir(parents=True, exist_ok=True)
    figures = {"workflow": workflow_svg(), "source-trace": trace_svg(trace),
               "furniture-margin": margin_svg(quarters, year), "salesorder-focus": salesorder_svg(sample)}
    for name, document in figures.items():
        ET.fromstring(document)  # refuse malformed SVG before exporting
        svg_path = target / f"{name}.svg"
        svg_path.write_text(document, encoding="utf-8")
        subprocess.run([renderer, "--format", "png", "--width", "2560", "--output",
                        str(target / f"{name}.png"), str(svg_path)], check=True)
    with (target / "furniture-margin.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(quarters[0]))
        writer.writeheader()
        writer.writerows(quarters)
    _write_table(target / "_furniture-table.qmd", quarters, year)
    artifact_names = [f"{name}.{ext}" for name in ASSET_NAMES for ext in ("svg", "png")]
    artifact_names += ["furniture-margin.csv", "_furniture-table.qmd"]
    facts = {"schema_version": 1, "dataset": pin, "generator_sha256": _source_hashes(root),
             "artifact_sha256": {name: _content_hash(target / name) for name in sorted(artifact_names)},
             "text_hash_policy": "UTF-8 with normalized LF newlines; binary assets and dataset use raw bytes",
             "measure": "Invoice-based margin at standard cost", "furniture_quarters": quarters,
             "source_trace": trace, "salesorder_rows": sample}
    (target / "facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Refreshed public Chapter 1 facts and figures; dataset SHA-256 unchanged ({before}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Check committed results without reading datasets/.")
    args = parser.parse_args()
    if args.check:
        errors = check_fresh(REPO_ROOT)
        for error in errors:
            print(error, file=sys.stderr)
        return int(bool(errors))
    refresh(REPO_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
