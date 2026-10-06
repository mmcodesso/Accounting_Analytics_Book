"""Rewrite the text of the book for a new edition: every classified literal from the old values to the new ones.

Phase 7 of the companion-files and yearly-roll program keeps readable 2026-edition literals in the source
(fiscal 2026, SI-2025-007947, 2026-12-11, $29,756,420.08). A roll computes the registry of the new dataset
(`python facts/phase7_cli.py visible --db NEW.sqlite --out new.json`) and runs

    python facts/roll_text.py --from facts/visible-2026.json --to new.json [--apply] [--root DIR] [--report FILE]

which rewrites, in every file in scope, each literal that facts/literals/ classifies, from its old value to its
new one, and writes the report: the diff of a rolled checkout is the impact report.

- years by role, simultaneously (2024 -> 2025 and 2025 -> 2026 in one pass, computed on the original text);
- document IDs, dates and clock times through their registry keys (facts/visible.py), in the literal's own shape
  (2026-12-11, 11 December 2026, December 11, 2026, 11 December);
- the first and last day of a month, and the dates tied to the window, with their year moved by role;
- exact values through the keys of facts/literals/values.yml, in the literal's own display format
  (facts/visible_values.py): $29,756,420.08, 29.8M, 47.49%, 27,933.

It leaves alone the real-world years (citations, standards, software releases, Learn dates), the constants
(teaching thresholds, worked examples), the generated directories (shared/generated, slides/_shared,
slides/_variables.yml, slides/_build), and the generated note regions if any reappear (`facts.py sync` rewrites
those). A literal whose key has no value in the new registry (a selection rule found no document) is not
rewritten and is listed under "Unresolved"; so are literals the new dataset cannot support in the same words
("two desks"). Without --apply it writes the report only. It refuses to run when a file in scope has an
unclassified literal (see `python facts/phase7_cli.py lint`), and applying the rewrite to the same registry
twice (--from X --to X) changes no file.
"""

from __future__ import annotations

import argparse
import calendar
import collections
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import textscan as ts  # noqa: E402

REPO = HERE.parent
YEAR_KEYS = ["fy.Fm1", "fy.F", "fy.P", "fy.C", "fy.N", "fy.N1", "fy.N2", "fy.edition"]


@dataclass
class Edit:
    file: str
    line: int
    start: int            # offsets in the normalized (LF) text
    end: int
    old: str
    new: str
    kind: str             # year | id | code | date | time | value
    cls: str
    key: str | None = None


@dataclass
class Plan:
    edits: list[Edit] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    ambiguous: list[str] = field(default_factory=list)
    counts: collections.Counter = field(default_factory=collections.Counter)    # (kind, class) -> literals seen
    files: dict[str, int] = field(default_factory=dict)                           # file -> literals classified


def load_snapshot(path: str | Path) -> dict:
    snap = json.loads(Path(path).read_text(encoding="utf-8"))
    if "keys" not in snap:
        snap = {"keys": snap, "window": None, "missing": {}}
    return snap


def year_map(old: dict, new: dict) -> dict[int, int]:
    """Each year of the old window's range -> the same role's year in the new one."""
    out: dict[int, int] = {}
    for k in YEAR_KEYS:
        if k in old and k in new:
            a, b = int(old[k]), int(new[k])
            if out.get(a, b) != b:
                raise SystemExit(f"{k}: year {a} is both {out[a]} and {b} in the new registry")
            out[a] = b
    return out


# --- reading a file as the scanners see it ---------------------------------------------------------

def read(path: Path) -> tuple[str, list[int]]:
    """The file's text with LF line ends, and for each offset of that text the offset in the raw text."""
    raw = path.read_bytes().decode("utf-8")
    if "\r" not in raw:
        return raw, []
    out, idx = [], []
    i, n = 0, len(raw)
    while i < n:
        if raw[i] == "\r" and i + 1 < n and raw[i + 1] == "\n":
            i += 1
            continue
        out.append(raw[i])
        idx.append(i)
        i += 1
    idx.append(n)
    return "".join(out), idx


def apply(path: Path, edits: list[Edit], text: str, idx: list[int]) -> None:
    raw = path.read_bytes().decode("utf-8")
    for e in sorted(edits, key=lambda e: -e.start):
        a, b = (idx[e.start], idx[e.end - 1] + 1) if idx else (e.start, e.end)
        assert raw[a:b].replace("\r\n", "\n") == e.old, (path, e)
        raw = raw[:a] + e.new + raw[b:]
    path.write_bytes(raw.encode("utf-8"))


# --- the plan -----------------------------------------------------------------------------------------

def shift_date(lit: ts.Lit, ymap: dict[int, int], structural: bool) -> str | None:
    """A date with its year moved by role; a month-end stays a month-end. None if the new date does not exist."""
    y, mon, day = ts.date_parts(lit)
    if y is None or y not in ymap:
        return None
    ny = ymap[y]
    if structural and ts.is_month_end(y, mon, day):
        day = calendar.monthrange(ny, mon)[1]
    try:
        import datetime as dt
        dt.date(ny, mon, day)
    except ValueError:
        return None
    return ts.render_date(f"{ny:04d}-{mon:02d}-{day:02d}", lit.shape, lit.text)


def plan_file(rel: str, text: str, old: dict, new: dict, ymap: dict[int, int], F: int, N: int,
              root: Path, plan: Plan, vv) -> None:
    lits = ts.classify(rel, text, F, N, ids=old, root=root)
    plan.files[rel] = plan.files.get(rel, 0) + len(lits)
    for lit in lits:
        plan.counts[(lit.kind, lit.cls or "unclassified")] += 1
        if lit.problem:
            plan.problems.append(f"{lit.where()}: {lit.text!r}: {lit.problem}")
            continue
        where = f"{lit.where()}: {lit.text!r}"

        def put(newtext: str | None, kind=lit.kind, cls=lit.cls, key=lit.key):
            if newtext is None:
                plan.unresolved.append(f"{where}: no value for {key or 'the new year'} in the new registry")
            elif newtext != lit.text:
                plan.edits.append(Edit(rel, lit.line, lit.start, lit.end, lit.text, newtext, kind, cls, key))

        if lit.cls in ("role", "edition") and lit.kind == "year":
            put(str(ymap[lit.year]) if lit.year in ymap else None)
        elif lit.cls == "key" and lit.kind in ("id", "code", "name"):
            v = new.get(lit.key)
            put(None if v is None else str(v))
        elif lit.cls == "key" and lit.kind == "time":
            v = new.get(lit.key)
            put(None if v is None else str(v))
        elif lit.cls == "key" and lit.kind == "date":
            v = new.get(lit.key)
            put(None if v is None else ts.render_date(str(v), lit.shape, lit.text))
        elif lit.kind == "date" and lit.cls in ("structural", "shift"):
            put(shift_date(lit, ymap, lit.cls == "structural"))
    # exact values (agent B)
    for o in (vv.classify(rel, text) if ts.values_scanned(rel) else []):
        plan.counts[("value", o.cls.split(":")[0] if o.cls else "unclassified")] += 1
        if not o.cls:
            plan.problems.append(f"{o.file}:{o.line}: {o.literal!r}: value with no class in values.yml")
            continue
        if o.cls != "key":
            continue
        ov, nv = old.get(o.key), new.get(o.key)
        where = f"{o.file}:{o.line}: {o.literal!r} ({o.key})"
        if ov is None:
            plan.stale.append(f"{where}: no such key in the old registry")
            continue
        shown = vv.display(ov, o.fmt) if o.fmt else str(ov)
        if shown != o.literal:
            plan.stale.append(f"{where}: the old registry shows {shown!r}; the text is stale, not rewritten")
            continue
        if nv is None:
            plan.unresolved.append(f"{where}: no value in the new registry")
            continue
        if nv == ov:
            continue
        newtext = render_value(vv, nv, o.fmt, o.literal, rel.endswith(".qmd")) if o.fmt else str(nv)
        if newtext != o.literal:
            plan.edits.append(Edit(o.file, o.line, o.start, o.end, o.literal, newtext, "value", "key", o.key))


# --- the classification files roll with the text -----------------------------------------------------------
#
# facts/literals/ids.yml, dates.yml and values.yml map a literal as the text writes it to its registry key, so
# they hold 2026-edition literals too. A roll rewrites the literals in these files by the same keys, or the lint
# would fail on the rolled text.

def _scalar_edit(rel: str, text: str, node, newlit: str) -> Edit:
    a, b = node.start_mark.index, node.end_mark.index
    old = text[a:b]
    q = old[0] if old[:1] in "'\"" else ""
    if q:
        new = q + newlit + q
    elif re.search(r"(?:^[\s\-?:,\[\]{}#&*!|>'\"%@`]|: | #|:$)", newlit) and not re.match(r"^[-+]?[$\d.]", newlit):
        new = '"' + newlit + '"'
    else:
        new = newlit
    line = text.count(chr(10), 0, a) + 1
    return Edit(rel, line, a, b, old, new, "classification", "key")


def render_value(vv, nv, fmt, old_literal: str, prose: bool) -> str:
    """The new value in the literal's display format. A prose amount that had no thousands separator because it was
    below 1,000 gets one when the new edition's value reaches 1,000 ($688.42 -> $3,346.80)."""
    text = vv.display(nv, fmt)
    if prose and isinstance(nv, (int, float)) and not isinstance(nv, bool):
        f = vv.parse_format(fmt) if isinstance(fmt, str) else fmt
        head = lambda t: re.sub(r"[^\d.]", "", t).split(".")[0]      # noqa: E731
        if not f.sep and f.unit in ("", "x") and len(head(old_literal)) <= 3 and len(head(text)) >= 4:
            import dataclasses
            text = vv.display(nv, dataclasses.replace(f, sep=","))
    return text


def _new_literal(lit: str, key: str, fmt: str | None, old: dict, new: dict, vv, rel: str, prose: bool = False) -> str | None:
    """The literal the text will carry for this key in the new edition, or None if it stays."""
    ov, nv = old.get(key), new.get(key)
    if ov is None or nv is None or ov == nv:
        return None
    f = fmt or (vv.infer_format(lit) if vv.parse_literal(lit) else None)
    if f is None:
        if str(ov) != lit:
            return None
        newlit = str(nv)
    else:
        if vv.display(ov, f) != lit:
            return None
        newlit = render_value(vv, nv, f, lit, prose)
    return None if newlit == lit else newlit


def _quote(newlit: str, was_quoted: str = "") -> str:
    """A YAML key for the literal: quoted when it was, or when plain text would read as a number, date or flag."""
    import yaml
    if was_quoted:
        return was_quoted + newlit + was_quoted
    try:
        plain_is_text = isinstance(yaml.safe_load("{" + newlit + ": x}"), dict) and             all(isinstance(k, str) for k in yaml.safe_load("{" + newlit + ": x}"))
    except yaml.YAMLError:
        plain_is_text = False
    return newlit if plain_is_text else '"' + newlit.replace("\\", "\\\\").replace('"', '\\"') + '"'


def literal_file_edits(rel: str, text: str, old: dict, new: dict, vv) -> tuple[list[Edit], list[str]]:
    """Edits that roll the literal -> key tables of facts/literals/ (ids.yml, dates.yml, values.yml).

    A key text is replaced in place. In values.yml an entry may list several specs (a key with a context each) for one
    literal; when the specs now read differently the entry is split, and when two entries now read alike they are
    merged, so the table still tells every occurrence apart. A context that spells the old literal ("(2, 7)") follows."""
    import yaml
    edits: list[Edit] = []
    notes: list[str] = []
    collisions: list[str] = []
    root = yaml.compose(text)
    if root is None:
        return edits, notes
    top = {k.value: v for k, v in root.value}
    line = lambda pos: text.count(chr(10), 0, pos) + 1   # noqa: E731

    def key_edit(knode, newlit):
        a, b = knode.start_mark.index, knode.end_mark.index
        q = text[a] if text[a] in "'\"" else ""
        edits.append(Edit(rel, line(a), a, b, text[a:b], _quote(newlit, q), "classification", "key"))

    def spec_nodes(v):
        return [v] if v.id in ("scalar", "mapping") else [x for y in v.value for x in spec_nodes(y)]

    def spec_info(sn):
        """(key or None, format or None, context node or None)"""
        if sn.id == "scalar":
            return (sn.value if sn.value not in ("constant", "computed") else None), None, None
        m = {k.value: v for k, v in sn.value}
        return (m["key"].value if "key" in m else None), (m["format"].value if "format" in m else None), m.get("context")

    name = rel.rsplit("/", 1)[-1]
    if name in ("ids.yml", "dates.yml"):
        for section in ("ids", "names", "dates", "times"):
            node = top.get(section)
            if node is not None and node.id == "mapping":
                for k, v in node.value:
                    nl = _new_literal(k.value, v.value, None, old, new, vv, rel)
                    if nl is not None:
                        key_edit(k, nl)
        return edits, notes
    if name != "values.yml":
        return edits, notes

    def mapping(node, fmt, where, prose=None):
        """prose: True for a file of prose, False for code; None (everywhere, rules) writes both forms when they differ."""
        if node is None or node.id != "mapping":
            return
        entries = []       # (knode, vnode, literal, [(spec node, [new literals] or [], context node)])
        for k, v in node.value:
            if k.value in ("constants", "computed", "review"):
                continue
            specs = []
            for sn in spec_nodes(v):
                key, f, ctx = spec_info(sn)
                nls: list[str] = []
                if key:
                    for pr in ((prose,) if prose is not None else (False, True)):
                        nl = _new_literal(k.value, key, f or fmt, old, new, vv, rel, pr)
                        if nl is not None and nl not in nls:
                            nls.append(nl)
                specs.append((sn, nls, ctx))
            entries.append((k, v, k.value, specs))
        targets: dict[str, list[int]] = {}
        for i, (k, v, lit, specs) in enumerate(entries):
            for tg in {t for _, nls, _ in specs for t in (nls or [lit])}:
                targets.setdefault(tg, []).append(i)
        involved = []
        for i, (k, v, lit, specs) in enumerate(entries):
            tgs = {t for _, nls, _ in specs for t in (nls or [lit])}
            if len(tgs) == 1 and all(len(targets[n]) == 1 for n in tgs):
                tg = next(iter(tgs))
                if tg != lit:
                    key_edit(k, tg)
            else:
                involved.append(i)
        if not involved:
            return
        merged: dict[str, list[str]] = {}
        order: list[str] = []
        for i in involved:
            k, v, lit, specs = entries[i]
            for sn, nls, ctx in specs:
                a, b = sn.start_mark.index, sn.end_mark.index
                for tg in (nls or [lit]):
                    st = text[a:b]
                    if tg != lit and ctx is not None:      # the context follows an old literal it spells
                        ca, cb = ctx.start_mark.index - a, ctx.end_mark.index - a
                        ctxt = re.sub(r"(?<![\d.,])" + re.escape(lit) + r"(?![\d])", tg, st[ca:cb])
                        st = st[:ca] + ctxt + st[cb:]
                    if tg not in merged:
                        merged[tg] = []
                        order.append(tg)
                    merged[tg].append(st)
        # one line per entry in the source: replace the first involved entry, drop the others
        first = involved[0]
        for i in involved:
            k, v, lit, specs = entries[i]
            a, b = k.start_mark.index, v.end_mark.index
            ls = text.rfind(chr(10), 0, a) + 1
            if i == first:
                indent = text[ls:a]
                lines = []
                for tg in order:
                    body = merged[tg][0] if len(merged[tg]) == 1 else "[" + ", ".join(merged[tg]) + "]"
                    lines.append(f"{indent}{_quote(tg)}: {body}")
                edits.append(Edit(rel, line(a), ls, b, text[ls:b], chr(10).join(lines), "classification", "key"))
            else:
                end = text.find(chr(10), b)
                end = len(text) if end < 0 else end + 1
                edits.append(Edit(rel, line(a), ls, end, text[ls:end], "", "classification", "key"))
        notes.append(f"{where}: {len(involved)} entries split, merged or written in two forms ({', '.join(order[:6])}{'...' if len(order) > 6 else ''})")
        for tg, sts in merged.items():
            bare = [st for st in sts if "context" not in st]
            if len(set(bare)) > 1:
                collisions.append(f"{where}: after the roll the literal {tg} stands for {len(set(bare))} different keys "
                                  f"({'; '.join(sorted(set(b[:60] for b in bare)))}) with no context to tell them apart: add a context in values.yml")

    for fk, fv in (top["files"].value if "files" in top else []):
        mapping(fv, None, f"{rel}:files:{fk.value}", prose=fk.value.endswith(".qmd"))
    mapping(top.get("everywhere"), None, f"{rel}:everywhere")
    for r in (top["rules"].value if "rules" in top else []):
        m = {k.value: v for k, v in r.value}
        if "map" in m:
            mapping(m["map"], m["format"].value if "format" in m else None, f"{rel}:rules")
    return edits, notes + ["AMBIGUOUS " + c for c in collisions]


def plan_literal_files(root: Path, old: dict, new: dict, plan: Plan, texts: dict, vv) -> None:
    for name in ("ids.yml", "dates.yml", "values.yml"):
        p = root / "facts" / "literals" / name
        if not p.is_file():
            continue
        rel = ts.rel_of(p, root)
        text, idx = read(p)
        texts[rel] = (p, text, idx)
        es, notes = literal_file_edits(rel, text, old, new, vv)
        plan.edits += es
        plan.info += [n for n in notes if not n.startswith("AMBIGUOUS ")]
        plan.ambiguous += [n[len("AMBIGUOUS "):] for n in notes if n.startswith("AMBIGUOUS ")]
        plan.unresolved += [n for n in notes if "no value in the new registry" in n]
        plan.counts[("classification", "key")] += len(es)


def dedupe(edits: list[Edit]) -> list[Edit]:
    """One edit per span: both scanners may claim a document code; they must then agree on the new text."""
    seen: dict[tuple, Edit] = {}
    out = []
    for e in edits:
        k = (e.file, e.start, e.end)
        if k in seen:
            if seen[k].new != e.new:
                out.append(e)       # kept, so check_overlaps reports the disagreement
            continue
        seen[k] = e
        out.append(e)
    return out


def check_overlaps(edits: list[Edit]) -> list[str]:
    out = []
    by = collections.defaultdict(list)
    for e in edits:
        by[e.file].append(e)
    for f, es in by.items():
        es.sort(key=lambda e: e.start)
        for a, b in zip(es, es[1:]):
            if b.start < a.end:
                out.append(f"{f}:{a.line}: edits overlap: {a.old!r} and {b.old!r}")
    return out


def make_plan(root: Path, old: dict, new: dict, files: list[Path] | None = None) -> tuple[Plan, dict]:
    import visible_values as vv
    ok, nk = old["keys"], new["keys"]
    if old.get("accounts"):          # the chart of accounts, so the value scanner needs no dataset
        vv.ACCOUNTS = set(old["accounts"])
    ymap = year_map(ok, nk)
    F, N = int(ok["fy.F"]), int(ok["fy.N"])
    plan = Plan()
    texts: dict[str, tuple[Path, str, list[int]]] = {}
    cwd = os.getcwd()
    os.chdir(root)      # visible_values reads per-file entries by the path relative to the checkout
    try:
        for p in files or ts.scope_files(root):
            rel = ts.rel_of(p, root)
            text, idx = read(p)
            texts[rel] = (p, text, idx)
            plan_file(rel, text, ok, nk, ymap, F, N, root, plan, vv)
    finally:
        os.chdir(cwd)
    plan_literal_files(root, ok, nk, plan, texts, vv)
    plan.edits = dedupe(plan.edits)
    plan.problems += check_overlaps(plan.edits)
    return plan, texts


# --- the report ---------------------------------------------------------------------------------------

def warnings_of(new: dict) -> list[str]:
    out = []
    nk = new["keys"]
    if nk.get("id.trace.exact") is False:
        out.append(f"The traced sale of Chapters 1 and 3 is {nk.get('id.trace.invoice')} ({nk.get('id.trace.quantity')} units of "
                   f"{nk.get('id.trace.item_code')}), the nearest to the one the text tells (two desks): review the wording.")
    lo, hi = int(nk["fy.Fm1"]), int(nk["fy.N2"])
    for k, v in sorted(nk.items()):
        if not k.startswith("fy.") and isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi:
            out.append(f"{k} is {v} on the new dataset, which reads like a year: classify its occurrences in "
                       f"facts/literals/years.yml (files:) or the lint will take them for years.")
    for name, why in (new.get("missing") or {}).items():
        out.append(f"Selection rule {name} found nothing on the new dataset: {why}.")
    return out


def report(plan: Plan, old: dict, new: dict, applied: bool) -> str:
    L = ["# What the new edition changes in the text", ""]
    L.append(f"- Old registry: window {old.get('window')}, {old.get('db', '?')}")
    L.append(f"- New registry: window {new.get('window')}, {new.get('db', '?')}")
    L.append(f"- {'Applied' if applied else 'Dry run (nothing written)'}: {len(plan.edits)} literals rewritten in "
             f"{len({e.file for e in plan.edits})} files; {len(plan.unresolved)} unresolved; {len(plan.stale)} stale; "
             f"{len(plan.problems)} unclassified or inconsistent.")
    L += ["", "## Warnings for the author", ""] + [f"- {w}" for w in warnings_of(new)] if warnings_of(new) else []
    L += ["", "## Literals classified, by kind and class", "", "| Kind | Class | Literals |", "|---|---|---:|"]
    for (k, c), n in sorted(plan.counts.items()):
        L.append(f"| {k} | {c} | {n} |")
    L += ["", "## Rewritten, by kind and class", "", "| Kind | Class | Rewritten |", "|---|---|---:|"]
    cnt = collections.Counter((e.kind, e.cls) for e in plan.edits)
    for (k, c), n in sorted(cnt.items()):
        L.append(f"| {k} | {c} | {n} |")
    L += ["", "## Rewritten, by file", "", "| File | Literals classified | Rewritten |", "|---|---:|---:|"]
    per = collections.Counter(e.file for e in plan.edits)
    for f in sorted(plan.files):
        L.append(f"| {f} | {plan.files[f]} | {per.get(f, 0)} |")
    for title, items in (("Unresolved (no value in the new registry; not rewritten)", plan.unresolved),
                         ("Classification entries split or merged by the roll", plan.info),
                         ("Ambiguous after the roll: one literal, several keys, no context (fix in values.yml before the next roll)", plan.ambiguous),
                         ("Stale literals (the text differs from the old registry; not rewritten)", plan.stale),
                         ("Unclassified or inconsistent", plan.problems)):
        if items:
            L += ["", f"## {title}", ""] + [f"- {i}" for i in items]
    L += ["", "## Changes", ""]
    last = None
    for e in sorted(plan.edits, key=lambda e: (e.file, e.start)):
        if e.file != last:
            L += ["", f"### {e.file}", ""]
            last = e.file
        L.append(f"- line {e.line}: `{e.old}` -> `{e.new}` ({e.kind}, {e.cls}{', ' + e.key if e.key else ''})")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="old", required=True, help="the old edition's registry (facts/visible-2026.json)")
    ap.add_argument("--to", dest="new", required=True, help="the new edition's registry")
    ap.add_argument("--apply", action="store_true", help="write the files (default: only the report)")
    ap.add_argument("--root", type=Path, default=REPO, help="the checkout to rewrite (default: this repository)")
    ap.add_argument("--report", type=Path, help="write the impact report here (default: print the summary)")
    ap.add_argument("--allow-unclassified", action="store_true",
                    help="rewrite what is classified even if the lint finds literals no rule covers")
    a = ap.parse_args(argv)
    old, new = load_snapshot(a.old), load_snapshot(a.new)
    plan, texts = make_plan(a.root.resolve(), old, new)
    if plan.problems and not a.allow_unclassified:
        print(f"Refusing to run: {len(plan.problems)} literal(s) are unclassified or inconsistent with the old registry "
              f"(python facts/phase7_cli.py lint):")
        for p in plan.problems[:40]:
            print("  " + p)
        if a.report:
            a.report.write_text(report(plan, old, new, False), encoding="utf-8")
        return 2
    if a.apply:
        by = collections.defaultdict(list)
        for e in plan.edits:
            by[e.file].append(e)
        for rel, es in by.items():
            p, text, idx = texts[rel]
            apply(p, es, text, idx)
    rep = report(plan, old, new, a.apply)
    if a.report:
        a.report.write_text(rep, encoding="utf-8")
        print(f"wrote {a.report}")
    print(f"{'applied' if a.apply else 'planned'}: {len(plan.edits)} rewrites in {len({e.file for e in plan.edits})} files; "
          f"{len(plan.unresolved)} unresolved, {len(plan.stale)} stale, {len(plan.problems)} unclassified")
    return 1 if (plan.unresolved or plan.stale or plan.problems or plan.ambiguous) else 0


if __name__ == "__main__":
    raise SystemExit(main())
