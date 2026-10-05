#!/usr/bin/env python3
"""Exercise all seven Pandoc PowerPoint layout choices using an isolated fixture.

Selection rules: https://pandoc.org/MANUAL.html#powerpoint-layout-choice
The existing prepared reference is copied; canonical deck/template inputs are
never modified. Outputs and the actual slide-to-layout map go to outputs/build.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import posixpath
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.slides.prepare import LAYOUTS, find_quarto

FIXTURE = """---
title: "Layout smoke test"
author: "Internal validation fixture"
slide-level: 2
format:
  pptx:
    reference-doc: reference.pptx
    output-file: layouts.pptx
---

# Section Header

## Title and Content

One text paragraph uses the ordinary content layout.

## Two Content

:::: {.columns}
::: {.column}
Left text only.
:::
::: {.column}
Right text only.
:::
::::

## Comparison

:::: {.columns}
::: {.column}
Left caption precedes its table.

| Item | Value |
|:--|--:|
| Example | 10 |
:::
::: {.column}
Right caption precedes its table.

| Item | Value |
|:--|--:|
| Example | 20 |
:::
::::

## Content with Caption

A text paragraph precedes a table outside columns.

| Item | Value |
|:--|--:|
| Example | 30 |

---

::: {.notes}
This slide contains notes only and should use the Blank layout.
:::
"""

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def relationship_map(data: bytes) -> dict[str, ET.Element]:
    return {element.get("Id"): element for element in ET.fromstring(data)}


def slide_layouts(pptx: Path) -> list[dict]:
    result = []
    with zipfile.ZipFile(pptx) as archive:
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        relationships = relationship_map(archive.read("ppt/_rels/presentation.xml.rels"))
        for index, slide_id in enumerate(presentation.findall("p:sldIdLst/p:sldId", NS), 1):
            rel = relationships[slide_id.get(f'{{{NS["r"]}}}id')]
            slide_path = posixpath.normpath(posixpath.join("ppt", rel.get("Target")))
            slide = ET.fromstring(archive.read(slide_path))
            rel_path = posixpath.join(posixpath.dirname(slide_path), "_rels", posixpath.basename(slide_path) + ".rels")
            slide_rels = relationship_map(archive.read(rel_path))
            layout_rel = next(item for item in slide_rels.values() if item.get("Type").endswith("/slideLayout"))
            layout_path = posixpath.normpath(posixpath.join(posixpath.dirname(slide_path), layout_rel.get("Target")))
            layout = ET.fromstring(archive.read(layout_path))
            result.append({"slide": index, "layout": layout.find("p:cSld", NS).get("name"),
                           "visible_text": " | ".join(node.text or "" for node in slide.findall(".//a:t", NS)),
                           "layout_part": layout_path})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--quarto")
    args = parser.parse_args()
    root = args.root.resolve()
    quarto = args.quarto or find_quarto()
    parent = root / "outputs/build/layout-smoke"
    if parent.is_symlink() or not parent.resolve().is_relative_to(root / "outputs/build"):
        raise ValueError("Unsafe layout smoke output directory")
    output = parent / datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%S-%fZ")
    output.mkdir(parents=True)
    shutil.copy2(root / "slides/_shared/theme/reference.pptx", output / "reference.pptx")
    (output / "_quarto.yml").write_text("project:\n  type: default\n  render: [layouts.qmd]\n", encoding="utf-8")
    (output / "layouts.qmd").write_text(FIXTURE, encoding="utf-8")
    with (output / "render.log").open("w", encoding="utf-8") as log:
        subprocess.run([quarto, "render", "layouts.qmd", "--to", "pptx"], cwd=output,
                       env=dict(os.environ, PYTHONUTF8="1"), stdout=log, stderr=subprocess.STDOUT, check=True)
    mapped = slide_layouts(output / "layouts.pptx")
    missing = sorted(LAYOUTS - {item["layout"] for item in mapped})
    report = {"status": "passed" if not missing and len(mapped) == 7 else "failed",
              "quarto_version": subprocess.check_output([quarto, "--version"], text=True).strip(),
              "reference": "slides/_shared/theme/reference.pptx (copied)",
              "missing_layouts": missing, "slides": mapped,
              "selection_rules_source": "https://pandoc.org/MANUAL.html#powerpoint-layout-choice"}
    path = output / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Report: {path}")
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
