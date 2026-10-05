#!/usr/bin/env python3
"""Render isolated propagation experiments without changing authoritative inputs.

Creates four source-only checkouts beneath outputs/build/propagation-check, using
ordinary mkdir so Windows ACLs are inherited. The actual dataset is read through
CHARLESRIVER_DATA and is never copied. Changed calculations and labels are test
perturbations only: none of these decks are publication candidates.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.slides.prepare import find_quarto

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise ValueError(f"Propagation fixture no longer matches {path}: {old}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def run(checkout: Path, command: list[str], name: str, env: dict) -> None:
    log = checkout / f"{name}.log"
    print(f"{checkout.name}: {name}", flush=True)
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=checkout, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        raise RuntimeError(f"{name} failed ({result.returncode}):\n" +
                           "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]))


def copy_sources(root: Path, target: Path) -> None:
    target.mkdir(parents=True)
    ignore = shutil.ignore_patterns("_build", "_shared", ".quarto", "__pycache__")
    for directory in ("slides", "shared", "scripts/slides"):
        shutil.copytree(root / directory, target / directory, ignore=ignore)
    for rel in ("_variables.yml", "filters/strip-comments.lua",
                "scripts/figures/ch01.py", "scripts/figures/ch06.py", "scripts/figures/data.py",
                "scripts/figures/drawio.py", "scripts/figures/excel.py"):
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, destination)
    # The helper copied this script as source, never a recursively copied output.
    if (target / "datasets").exists():
        raise AssertionError("The isolated checkout must not contain a dataset copy")


def change_geometry(path: Path) -> None:
    with zipfile.ZipFile(path) as source:
        members = {name: source.read(name) for name in source.namelist()}
    changed = 0
    for name, data in list(members.items()):
        if not name.startswith("ppt/slideLayouts/") or not name.endswith(".xml"):
            continue
        document = ET.fromstring(data)
        common = document.find("p:cSld", NS)
        if common is None or common.get("name") != "Title and Content":
            continue
        for shape in document.findall(".//p:sp", NS):
            placeholder = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
            if placeholder is not None and placeholder.get("type") == "title":
                offset = shape.find("p:spPr/a:xfrm/a:off", NS)
                offset.set("y", str(int(offset.get("y")) + 91440))
                changed += 1
        members[name] = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    if changed != 1:
        raise ValueError(f"Expected one Title and Content title placeholder; found {changed}")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
        for name, data in members.items():
            output.writestr(name, data)


def snapshot(checkout: Path) -> dict:
    html_root = checkout / "slides/_build/revealjs"
    html = (html_root / "chapter-01/index.html").read_text(encoding="utf-8")
    css = "\n".join(path.read_text(encoding="utf-8") for path in sorted(html_root.rglob("*.css")))
    pptx = checkout / "slides/_build/pptx/chapter-01/chapter-01.pptx"
    with zipfile.ZipFile(pptx) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    text = "\n".join(" ".join(ET.fromstring(data).itertext()) for name, data in members.items()
                     if re.match(r"ppt/slides/slide\d+\.xml$", name))
    theme_xml = "\n".join(data.decode("utf-8") for name, data in members.items()
                          if name.startswith("ppt/theme/") and name.endswith(".xml"))
    layout_y = None
    for name, data in members.items():
        if not name.startswith("ppt/slideLayouts/") or not name.endswith(".xml"):
            continue
        document = ET.fromstring(data)
        common = document.find("p:cSld", NS)
        if common is None or common.get("name") != "Title and Content":
            continue
        for shape in document.findall(".//p:sp", NS):
            ph = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
            if ph is not None and ph.get("type") == "title":
                layout_y = int(shape.find("p:spPr/a:xfrm/a:off", NS).get("y"))
    return {"html": html, "css": css, "pptx_text": text, "theme_xml": theme_xml,
            "layout_y": layout_y,
            "package_content": {name: hashlib.sha256(data).hexdigest() for name, data in members.items()
                                if name != "docProps/core.xml"},
            "media_hashes": {hashlib.sha256(data).hexdigest() for name, data in members.items()
                             if name.startswith("ppt/media/")},
            "facts": json.loads((checkout / "shared/generated/chapter-01/facts.json").read_text(encoding="utf-8"))}


def render(checkout: Path, quarto: str, env: dict, *, refresh: bool = False) -> None:
    if refresh:
        run(checkout, [sys.executable, "scripts/slides/refresh.py"], "refresh", env)
    run(checkout, [sys.executable, "-c",
        "from pathlib import Path; from scripts.slides.prepare import prepare; "
        "from scripts.slides.verify import load_manifest; "
        "prepare(Path('.').resolve(),load_manifest(Path('slides/manifest.yml')))"], "prepare", env)
    for fmt in ("revealjs", "pptx"):
        run(checkout, [quarto, "render", "slides", "--to", fmt, "--output-dir", f"_build/{fmt}"], fmt, env)


def book_evidence(checkout: Path, env: dict) -> dict:
    code = (
        "import json,sys; from pathlib import Path; sys.path.insert(0,'scripts/figures'); "
        "import ch01,ch06; p=Path('book-workflow.drawio'); d=ch01.fig_01_02(); d.save(p); "
        "before=p.stat().st_mtime_ns; d.save(p); "
        "assert p.stat().st_mtime_ns==before, 'unchanged Diagram.save changed mtime'; "
        "Path('book-measure.json').write_text(json.dumps({'q3':ch06.margin_pct(grp='Furniture',per='2026-Q3'),"
        "'no_op_save_preserved_mtime':True}))"
    )
    run(checkout, [sys.executable, "-c", code], "book-evidence", env)
    return json.loads((checkout / "book-measure.json").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--quarto")
    parser.add_argument("--dataset-dir", type=Path, help="Defaults to CHARLESRIVER_DATA or root/datasets")
    args = parser.parse_args()
    root = args.root.resolve()
    quarto = args.quarto or find_quarto()
    folder = root / "outputs/build/propagation-check"
    if folder.is_symlink() or not folder.resolve().is_relative_to(root / "outputs/build"):
        raise ValueError("Unsafe propagation output directory")
    stamp = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%S-%fZ")
    output = folder / stamp
    output.mkdir(parents=True)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    dataset = (args.dataset_dir or Path(env.get("CHARLESRIVER_DATA", root / "datasets"))).resolve()
    env["CHARLESRIVER_DATA"] = str(dataset)
    before = digest(dataset / "CharlesRiver.sqlite")
    report = {"status": "running", "output": str(output), "dataset_sha256_before": before,
              "dataset_copied": False, "native_visual_review": "not part of this automated propagation check",
              "experiments": {}}
    report_path = output / "report.json"
    try:
        cases = {name: output / name for name in ("baseline", "changed-shared", "css-only", "geometry-only")}
        for target in cases.values():
            copy_sources(root, target)
        baseline, changed, css_only, geometry = cases.values()
        render(baseline, quarto, env)
        original = snapshot(baseline)
        original_book = book_evidence(baseline, env)
        # Shared sources, not the generated slide assets, receive each perturbation.
        replace(changed / "slides/theme/tokens.yml", "font: Arial", "font: Georgia")
        replace(changed / "slides/theme/tokens.yml", "blue: '1A5276'", "blue: '7030A0'")
        replace(changed / "_variables.yml", 'window: "fiscal 2024–2026"', 'window: "PROPAGATION WINDOW CHECK"')
        fragment = changed / "shared/fragments/_accounting-analytics.qmd"
        fragment.write_text(fragment.read_text(encoding="utf-8") + "\nPropagation fragment marker.\n", encoding="utf-8")
        replace(changed / "shared/calculations/chapter01.py", "1. Define the question", "1. Frame the question")
        replace(changed / "shared/calculations/invoice_margin.py", "C=r[1] * r[9]", "C=r[1] * r[9] * 1.01")
        run(changed, [sys.executable, "-c", "from pathlib import Path; from scripts.slides.refresh import check_fresh; "
                     "errors=check_fresh(Path('.')); assert any('source changed' in e for e in errors); print(errors)"],
            "stale-input-rejected", env)
        render(changed, quarto, env, refresh=True)
        updated = snapshot(changed)
        updated_book = book_evidence(changed, env)
        assert "#7030a0" in updated["css"].lower() and "Georgia" in updated["css"]
        assert 'val="7030A0"' in updated["theme_xml"] and 'typeface="Georgia"' in updated["theme_xml"]
        for marker in ("PROPAGATION WINDOW CHECK", "Propagation fragment marker."):
            assert marker in updated["html"] and marker in updated["pptx_text"], marker
        workflow = changed / "shared/generated/chapter-01/workflow"
        svg = workflow.with_suffix(".svg").read_text(encoding="utf-8")
        assert "1. Frame" in svg
        assert "1. Frame the question" in (changed / "book-workflow.drawio").read_text(encoding="utf-8")
        assert digest(workflow.with_suffix(".png")) in updated["media_hashes"]
        assert digest(workflow.with_suffix(".png")) not in original["media_hashes"]
        rendered_svg = next((changed / "slides/_build/revealjs").rglob("workflow.svg"))
        assert "1. Frame" in rendered_svg.read_text(encoding="utf-8")
        q3 = updated["facts"]["furniture_quarters"][2]
        assert q3["margin_rate"] != original["facts"]["furniture_quarters"][2]["margin_rate"]
        assert abs(q3["margin_rate"] - updated_book["q3"]) < 1e-12
        amount = f'${q3["standard_cost"]:,.2f}'
        assert amount in updated["html"] and amount in updated["pptx_text"]
        report["experiments"]["shared_sources"] = {"status": "passed", "theme_color": "7030A0",
            "theme_font": "Georgia", "root_variable_and_fragment_in_both_formats": True,
            "diagram_in_book_reveal_and_pptx": True, "calculation_in_book_and_both_formats": True,
            "stale_calculation_rejected_before_refresh": True, "baseline_q3_rate": original_book["q3"],
            "perturbed_q3_rate": updated_book["q3"], "no_op_save_preserved_mtime": True}
        css_path = css_only / "slides/theme/reveal.scss"
        css_path.write_text(css_path.read_text(encoding="utf-8") +
                           "\n.reveal .slides h2 { letter-spacing: 0.017em; }\n", encoding="utf-8")
        render(css_only, quarto, env)
        css_result = snapshot(css_only)
        assert re.search(r"letter-spacing:\s*0?\.017em", css_result["css"])
        assert original["package_content"] == css_result["package_content"]
        report["experiments"]["reveal_css_only"] = {"status": "passed", "rendered_css_changed": True,
                                                      "pptx_package_members_unchanged_except_core_metadata": True}
        change_geometry(geometry / "slides/theme/reference-base.pptx")
        render(geometry, quarto, env)
        geometry_result = snapshot(geometry)
        assert geometry_result["layout_y"] == original["layout_y"] + 91440
        assert geometry_result["html"] == original["html"] and geometry_result["css"] == original["css"]
        report["experiments"]["pptx_geometry_only"] = {"status": "passed", "title_y_delta_emu": 91440,
                                                         "reveal_html_and_css_unchanged": True}
        after = digest(dataset / "CharlesRiver.sqlite")
        assert before == after
        report.update(status="passed", dataset_sha256_after=after,
                      dataset_unchanged=True, render_count=8,
                      quarto_version=subprocess.check_output([quarto, "--version"], text=True).strip())
    except Exception as exc:
        report.update(status="failed", error=str(exc))
        raise
    finally:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Propagation report: {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
