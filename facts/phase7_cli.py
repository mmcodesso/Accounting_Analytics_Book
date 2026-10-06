"""The Phase 7 commands: the registry of the literals a roll rewrites, and the lint that guards them.

    python facts/phase7_cli.py visible [--db PATH] --out facts/visible-2026.json
    python facts/phase7_cli.py lint    [--db PATH | --snapshot FILE] [--root DIR] [--report FILE] [FILES]
    python facts/phase7_cli.py report  [--snapshot FILE] [--out FILE]      # counts by kind, class and file

`visible` writes the snapshot of a dataset (facts/visible.py snapshot_file): the window, the SHA-256, every key
(fy.* years, id.* documents, date.* dates, val.* values) and the selection rules that found nothing.

`lint` fails on any year in the window's range, document ID or code, date, clock time, or exact value in a file in
scope that no rule, key or allow-list entry (facts/literals/) covers, and on any key whose value on the dataset is not
the literal the text shows. With --snapshot (default facts/visible-2026.json) it needs no dataset. The rewriter
(facts/roll_text.py) refuses to run while the lint fails.

(These commands would be `scripts/facts.py visible|lint` with a three-line dispatch; see the Phase 7 report.)
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "scripts"))

DEFAULT_SNAPSHOT = HERE / "visible-2026.json"


def cmd_visible(a) -> int:
    from db import Data
    import visible
    d = Data(a.db)
    snap = visible.snapshot_file(d)
    out = Path(a.out)
    out.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    kinds = collections.Counter(k.split(".", 1)[0] for k in snap["keys"])
    print(f"wrote {out}: fiscal {d.F}-{d.C}, {len(snap['keys'])} keys ({dict(kinds)})")
    for name, why in snap["missing"].items():
        print(f"  missing: {name}: {why}")
    return 1 if snap["missing"] else 0


def snapshot_for(a) -> dict:
    if getattr(a, "db", None):
        from db import Data
        import visible
        return visible.snapshot_file(Data(a.db))
    return json.loads(Path(a.snapshot).read_text(encoding="utf-8"))


ALT_RX = None


def zone_of(rel: str, text: str, spans, pos: int) -> str:
    """Where a literal sits: python, slides, multiple choice, alt text, a code block, or prose."""
    name = rel.rsplit("/", 1)[-1]
    if rel.endswith(".py"):
        return "python"
    if rel.startswith("facts/notes/templates/"):
        return "template"
    if rel.startswith("slides/"):
        return "slides"
    if name == "_multiple-choice.qmd":
        return "multiple choice"
    for kind, a, b in spans:
        if a <= pos < b:
            return kind
    return "prose"


def zone_spans(text: str) -> list[tuple[str, int, int]]:
    import re
    import textscan as ts
    out = [("alt text", m.start(), m.end()) for m in re.finditer(r"fig-alt=(?:\"[^\"]*\"|'[^']*')", text)]
    out += [("code block", m.start(), m.end()) for m in ts.FENCE_RX.finditer(text)]
    return out


def lint_all(snap: dict, root: Path, files: list[Path] | None = None, zones: collections.Counter | None = None):
    """(problems, counts, per-file counts): every literal in scope classified against the snapshot."""
    import textscan as ts
    import visible_values as vv
    import os
    keys = snap["keys"]
    if snap.get("accounts"):         # the chart of accounts, so the value scanner needs no dataset
        vv.ACCOUNTS = set(snap["accounts"])
    F, N = int(keys["fy.F"]), int(keys["fy.N"])
    problems: list[str] = []
    counts: collections.Counter = collections.Counter()
    per_file: dict[str, collections.Counter] = {}
    cwd = os.getcwd()
    os.chdir(root)
    try:
        for p in files or ts.scope_files(root):
            rel = ts.rel_of(p, root)
            text = ts.read_text(p)
            c = per_file.setdefault(rel, collections.Counter())
            spans = zone_spans(text) if zones is not None and not rel.endswith(".py") else []
            for lit in ts.classify(rel, text, F, N, ids=keys, root=root):
                if zones is not None and lit.kind == "year":
                    zones[(zone_of(rel, text, spans, lit.start), lit.cls or "unclassified")] += 1
                counts[(lit.kind, lit.cls or "unclassified")] += 1
                c[(lit.kind, lit.cls or "unclassified")] += 1
                if lit.problem:
                    problems.append(f"{lit.where()}: {lit.text!r}: {lit.problem}")
            for o in (vv.classify(rel, text) if ts.values_scanned(rel) else []):
                key = ("value", o.cls.split(":")[0] if o.cls else "unclassified")
                counts[key] += 1
                c[key] += 1
                if not o.cls:
                    problems.append(f"{o.file}:{o.line}: {o.literal!r}: value with no class in values.yml | {o.context[:90]}")
                elif o.cls == "key":
                    if o.key not in keys:
                        problems.append(f"{o.file}:{o.line}: {o.literal!r}: {o.key} is not in the registry")
                    else:
                        shown = vv.display(keys[o.key], o.fmt) if o.fmt else str(keys[o.key])
                        if shown != o.literal:
                            problems.append(f"{o.file}:{o.line}: {o.literal!r}: {o.key} = {keys[o.key]!r} shows {shown!r}")
    finally:
        os.chdir(cwd)
    return problems, counts, per_file


def cmd_lint(a) -> int:
    root = Path(a.root).resolve()
    snap = snapshot_for(a)
    files = [root / f for f in a.files] if a.files else None
    problems, counts, _ = lint_all(snap, root, files)
    for p in problems:
        print(p)
    total = sum(counts.values())
    print(f"{total} literals classified in scope, {len(problems)} problem(s)")
    if a.report:
        Path(a.report).write_text(render_report(snap, counts, problems), encoding="utf-8")
    return 1 if problems else 0


def render_report(snap: dict, counts, problems, per_file=None, zones=None) -> str:
    L = ["# Literals of the text by kind and class", "",
         f"Registry: window {snap.get('window')}, {len(snap['keys'])} keys. Problems: {len(problems)}.", "",
         "| Kind | Class | Literals |", "|---|---|---:|"]
    for (k, c), n in sorted(counts.items()):
        L.append(f"| {k} | {c} | {n} |")
    if zones:
        L += ["", "## Year literals by where they sit", "", "| Where | Class | Years |", "|---|---|---:|"]
        for (z, c), n in sorted(zones.items()):
            L.append(f"| {z} | {c} | {n} |")
    if per_file:
        L += ["", "## By file", "", "| File | Literals | Years | IDs and codes | Dates and times | Values |", "|---|---:|---:|---:|---:|---:|"]
        for f in sorted(per_file):
            c = per_file[f]
            def n(*kinds):
                return sum(v for (k, _), v in c.items() if k in kinds)
            L.append(f"| {f} | {sum(c.values())} | {n('year')} | {n('id', 'code')} | {n('date', 'time')} | {n('value')} |")
    if problems:
        L += ["", "## Problems", ""] + [f"- {p}" for p in problems]
    return "\n".join(L) + "\n"


def cmd_report(a) -> int:
    root = Path(a.root).resolve()
    snap = snapshot_for(a)
    zones: collections.Counter = collections.Counter()
    problems, counts, per_file = lint_all(snap, root, zones=zones)
    text = render_report(snap, counts, problems, per_file, zones)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    from paths import DB
    p = sub.add_parser("visible")
    p.add_argument("--db", type=Path, default=DB)
    p.add_argument("--out", required=True)
    for name in ("lint", "report"):
        p = sub.add_parser(name)
        p.add_argument("--db", type=Path, default=None, help="compute the registry from this dataset")
        p.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
        p.add_argument("--root", type=Path, default=REPO)
        if name == "lint":
            p.add_argument("--report", type=Path)
            p.add_argument("files", nargs="*")
        else:
            p.add_argument("--out")
    a = ap.parse_args(argv)
    return dict(visible=cmd_visible, lint=cmd_lint, report=cmd_report)[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
