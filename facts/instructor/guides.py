"""Instructor guides: one folder per chapter, case and exercise-bearing appendix.

    python facts/instructor/guides.py list [--unit U]            # the units, their items and file names
    python facts/instructor/guides.py scaffold --unit U [--force] # create the unit's template files
    python facts/instructor/guides.py sources --unit U --out FILE # everything an author reads for the unit
    python facts/instructor/guides.py context KEY                 # the keys a template may use, with values
    python facts/instructor/guides.py render [--unit U | --all]   # templates -> instructor-notes/<unit>/
    python facts/instructor/guides.py check [--unit U | --all]    # the rules in facts/instructor/STANDARD.md
    python facts/instructor/guides.py figures                     # instructor-notes/figures.yml
    python facts/instructor/guides.py pdf [--unit U | --all]      # instructor-notes/ -> outputs/instructor/pdf/ (vector figures)
    python facts/instructor/guides.py package                     # outputs/companion/solutions/Instructor-Notes.zip (PDF files only)

A unit U is a chapter number (1..19), a comprehensive case (case1..case4) or an appendix (appB, appC).

The source of every file is a Markdown template, facts/instructor/guides/<unit folder>/<file>.md, with a YAML front
matter and a Jinja body (the same engine, filters and context functions as the generated notes of facts/notes).
`render` writes the filled-in Markdown to instructor-notes/<unit folder>/, which is what ships.  See STANDARD.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sqlite3
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for _p in (REPO / "scripts", REPO / "facts", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

GUIDES = HERE / "guides"
OUT = REPO / "instructor-notes"
FIGURE_SOURCES = HERE / "figures"
SOLUTIONS = REPO / "outputs" / "companion" / "solutions"
ZIP_OUT = SOLUTIONS
PDF_DIR = REPO / "outputs" / "instructor" / "pdf"
FIGURE_PDF_DIR = OUT / "figures"          # the figures of the notes, as vector PDFs (tracked)
PDF_ASSETS = HERE / "pdf"
ZIP_NAME = "Instructor-Notes.zip"

TOOLS = ("conceptual", "excel", "sql", "powerbi", "mixed")
FIGURE_KINDS = ("excel-mock", "sql-mock", "pbi-mock", "diagram", "chart")
PERSPECTIVES = ("financial", "managerial", "auditing", "general")
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}

NOTE_HEADINGS_CHAPTER = ["At a glance", "What students should be able to do afterward", "Preparing to teach", "Teaching approaches",
                         "Tutorial guide", "Difficult ideas and misconceptions", "Discussion prompts", "Using the exercises",
                         "Multiple-choice questions", "Connections"]
NOTE_HEADINGS_CASE = ["At a glance", "What students should be able to do afterward", "Preparing to teach", "Teaching approaches",
                      "Difficult ideas and misconceptions", "Discussion prompts", "Using the requirements", "Assessment rubric",
                      "Connections"]
ITEM_HEADINGS = ["Purpose and learning outcomes", "Before you assign", "How to run it", "Step-by-step solution", "Expected results",
                 "What a strong answer says", "Common mistakes and how to respond", "Grading guide",
                 "Extensions and discussion questions"]
LIMITS = {"item": (450, 2700), "note": (1000, 4600)}        # words of the rendered file
MAX_FIGURES = {"item": 3, "note": 4}


# --- the units and their items ----------------------------------------------------------------------------------------

@dataclass
class Item:
    kind: str                      # exercise, requirement
    number: str                    # "6.1", "3"
    title: str
    origin: str
    perspective: str = "general"
    text: str = ""                 # the item's text in the book
    parts: list[str] = field(default_factory=list)      # (1) ... (n) of an exercise, the bullets of a requirement
    note_key: str | None = None

    @property
    def item_no(self) -> str:
        return self.number.split(".")[-1]

    @property
    def filename(self) -> str:
        prefix = "ex" if self.kind == "exercise" else "req"
        return f"{prefix}-{self.number}-{slugify(self.title)}.md"


@dataclass
class GUnit:
    uid: str                       # 6, case2, appB
    fig: str                       # 06, C2, AB
    folder: str
    base: object                   # package.Unit
    items: list[Item] = field(default_factory=list)
    tutorials: list[tuple[str, str]] = field(default_factory=list)
    milestones: list[tuple[str, str]] = field(default_factory=list)
    has_mcq: bool = False

    @property
    def is_case(self) -> bool:
        return any(i.kind == "requirement" for i in self.items)

    @property
    def note_file(self) -> str:
        return "00-case-notes.md" if self.is_case else "00-chapter-notes.md"

    @property
    def files(self) -> list[str]:
        return [self.note_file] + [i.filename for i in self.items]

    @property
    def text(self) -> str:
        return "\n".join(line for _, line in self.base.lines)


def slugify(title: str) -> str:
    title = re.sub(r"\s*\((?:Chapters?|Auditing|Part)[^)]*\)\s*$", "", title)
    words = re.findall(r"[a-z0-9]+", title.lower())
    out: list[str] = []
    for w in words:
        if len("-".join(out + [w])) > 48 and out:
            break
        out.append(w)
    return "-".join(out)


def clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\\", "")).strip().rstrip(".").strip()


def build_units() -> list[GUnit]:
    import package
    import source
    units = []
    for u in package.book_units():
        folder = Path(u.path).parent.name if u.kind != "case" else None
        if u.kind == "chapter":
            n = int(u.number)
            g = GUnit(str(n), f"{n:02d}", f"chapter-{folder}", u)
        elif u.kind == "case":
            n = int(u.number.split()[1])
            g = GUnit(f"case{n}", f"C{n}", f"case-part-{n}", u)
        else:
            g = GUnit(f"app{u.number}", f"A{u.number}", f"appendix-{folder}", u)
        _parse(g, package, source)
        units.append(g)
    return units


def _parse(g: GUnit, package, source) -> None:
    in_fence = False
    ctx: dict[int, str] = {}
    current: Item | None = None
    lines = g.base.lines
    for idx, (origin, line) in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            hm = package.HEADING.match(line)
            if hm:
                level = len(hm.group(1))
                if level >= 2:
                    ctx[level] = re.sub(r"\s*\{.*\}$", "", hm.group(2).strip())
                    for deeper in [k for k in ctx if k > level]:
                        del ctx[deeper]
                if current is not None and (level <= 3 if current.kind == "exercise" else level <= 2):
                    current = None
            tm = package.TUTORIAL.match(line)
            if tm and not in_fence:
                g.tutorials.append((tm.group(1), re.sub(r"\s*\{.*\}$", "", tm.group(2))))
            if origin.endswith("_multiple-choice.qmd") and hm and len(hm.group(1)) == 2:
                g.has_mcq = True
            em = package.EXERCISE.match(line)
            if em and origin.endswith("_exercises.qmd"):
                ch, n, title = em.group(1), em.group(2), clean_title(em.group(3))
                persp = ("financial" if "Financial" in ctx.get(3, "") else "managerial" if "Managerial" in ctx.get(3, "")
                         else "auditing" if "Auditing" in ctx.get(3, "") else "general")
                current = Item("exercise", f"{ch}.{n}", title, origin, persp, note_key=source.key_for(origin, f"ex{n}"))
                current.text = line + "\n"
                g.items.append(current)
                continue
            rm = package.REQUIREMENT.match(line)
            if rm:
                n, title = rm.group(1), clean_title(rm.group(2))
                current = Item("requirement", n, title, origin, note_key=source.key_for(origin, f"r{n}"))
                current.text = line + "\n"
                g.items.append(current)
                continue
            mm = package.MILESTONE.match(line)
            if mm and ctx.get(2) == "Getting Started":
                n, title = mm.group(1), clean_title(mm.group(2))
                if source.key_for(origin, f"m{n}") or source.archived_comment(origin, rf"<!--\s*Instructor notes, Milestone {n}\b"):
                    g.milestones.append((n, title))
        if current is not None:
            current.text += line + "\n"
            pm = re.match(r"^\((\d+)\)\s+(.*)", line) if current.kind == "exercise" else re.match(r"^- (.*)", line)
            if pm:
                current.parts.append(clean_title(pm.group(2) if current.kind == "exercise" else pm.group(1)))


def find_unit(units: list[GUnit], uid: str) -> GUnit:
    uid = uid.strip()
    for g in units:
        if uid.lower() in (g.uid.lower(), g.fig.lower(), g.folder.lower()):
            return g
    raise SystemExit(f"no unit {uid!r}; units: " + ", ".join(g.uid for g in units))


# --- templates ---------------------------------------------------------------------------------------------------------

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def split_front(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        raise ValueError("no YAML front matter")
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def protect_fences(body: str) -> tuple[str, dict[str, str]]:
    """Replace each fenced code block with a token, so Jinja never sees DAX or M braces.  A fence whose info string
    ends in the word jinja is left in place (its `jinja` word is dropped) so values can be placed inside it."""
    out, blocks = [], {}
    buf: list[str] = []
    fence = ""
    live = False
    for line in body.split("\n"):
        m = FENCE.match(line)
        if not fence:
            if m:
                fence, buf = m.group(2), [line]
                live = m.group(3).strip().endswith("jinja")
                if live:
                    buf = [line.replace("jinja", "", 1).rstrip()]
            else:
                out.append(line)
            continue
        if m and m.group(2).startswith(fence[0]) and len(m.group(2)) >= len(fence) and not m.group(3).strip():
            buf.append(line)
            if live:
                out.extend(buf)
            else:
                token = f"@@FENCE{len(blocks)}@@"
                blocks[token] = "\n".join(buf)
                out.append(token)
            fence, buf, live = "", [], False
        else:
            buf.append(line)
    if fence:
        raise ValueError("an unclosed code fence")
    return "\n".join(out), blocks


def restore_fences(text: str, blocks: dict[str, str]) -> str:
    for token, block in blocks.items():
        text = text.replace(token, block)
    return text


def fenced_blocks(body: str) -> list[tuple[str, str]]:
    """(info string, content) of every fenced block of a body."""
    blocks, buf, info, fence = [], [], "", ""
    for line in body.split("\n"):
        m = FENCE.match(line)
        if not fence:
            if m:
                fence, info, buf = m.group(2), m.group(3).strip(), []
        elif m and m.group(2).startswith(fence[0]) and len(m.group(2)) >= len(fence) and not m.group(3).strip():
            blocks.append((info, "\n".join(buf)))
            fence = ""
        else:
            buf.append(line)
    return blocks


def competency(label_candidates: list[str]) -> str:
    path = REPO / "drafts" / "competency-map-by-item.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    for cand in label_candidates:
        m = re.search(rf"^## {re.escape(cand)}:.*?(?=^## |\Z)", text, re.S | re.M)
        if m:
            return m.group(0).strip()
    return ""


def competency_labels(g: GUnit, item: Item) -> list[str]:
    if item.kind == "exercise":
        return [item.number]
    if g.uid.startswith("case"):
        return [f"Part {ROMAN[int(g.uid[4:])]} R{item.number}"]
    return [f"Ch. {g.uid} R{item.number}", f"Chapter {g.uid} R{item.number}"]


def scaffold_note(g: GUnit) -> str:
    title = g.base.title
    h1 = (f"Chapter {g.base.number}: {title}" if g.base.kind == "chapter" else
          f"Comprehensive Case, {g.base.number}: {title}" if g.base.kind == "case" else f"Appendix {g.base.number}: {title}")
    meta = {"title": h1, "kind": "case-notes" if g.is_case else "chapter-notes", "unit": g.uid, "minutes": 0,
            "tool": "conceptual", "figures": []}
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip()
    heads = NOTE_HEADINGS_CASE if g.is_case else NOTE_HEADINGS_CHAPTER
    body = [f"---\n{front}\n---", f"# {h1}", "", "{{ header() }}", ""]
    for h in heads:
        body += [f"## {h}", "", "TODO", ""]
        if h == "Tutorial guide":
            body = body[:-2]
            for tid, ttitle in g.tutorials:
                body += [f"### Guided Tutorial {tid}: {ttitle}", "", "TODO", ""]
        if h == "Multiple-choice questions" and g.has_mcq:
            body = body[:-2] + ["{{ mcq_key() }}", "", "TODO", ""]
    if g.milestones:
        i = body.index("## Difficult ideas and misconceptions")
        ms = ["## Milestone guide", ""]
        for n, mt in g.milestones:
            ms += [f"### Milestone {n}: {mt}", "", "TODO", ""]
        body[i:i] = ms
    return "\n".join(body).rstrip() + "\n"


def scaffold_item(g: GUnit, item: Item) -> str:
    label = f"Exercise {item.number}" if item.kind == "exercise" else f"Requirement {item.number}"
    h1 = f"{label}: {item.title}"
    meta = {"title": item.title, "kind": item.kind, "number": item.number, "unit": g.uid,
            "perspective": item.perspective, "tool": "conceptual", "minutes": 0, "solution": "", "figures": []}
    if item.note_key:
        meta = {"note": item.note_key, **meta}
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip()
    body = [f"---\n{front}\n---", f"# {h1}", "", "{{ header() }}", ""]
    for h in ITEM_HEADINGS:
        body += [f"## {h}", ""]
        if h == "Step-by-step solution":
            if item.parts:
                for i, p in enumerate(item.parts, 1):
                    lead = f"Requirement ({i})" if item.kind == "exercise" else f"Part {i}"
                    body += [f"### {lead}: {p[:70].rstrip()}{'...' if len(p) > 70 else ''}", "", "TODO", ""]
            else:
                body += ["TODO", ""]
        elif h == "Expected results":
            body += ["TODO", "", "{{ expected() }}", ""] if item.note_key else ["TODO", ""]
        else:
            body += ["TODO", ""]
    return "\n".join(body).rstrip() + "\n"


def cmd_scaffold(units: list[GUnit], uid: str, force: bool) -> int:
    g = find_unit(units, uid)
    folder = GUIDES / g.folder
    folder.mkdir(parents=True, exist_ok=True)
    made = 0
    jobs = [(g.note_file, scaffold_note(g))] + [(i.filename, scaffold_item(g, i)) for i in g.items]
    for name, text in jobs:
        path = folder / name
        if path.exists() and not force:
            print(f"kept    {path.relative_to(REPO)}")
            continue
        path.write_text(text, encoding="utf-8", newline="\n")
        made += 1
        print(f"created {path.relative_to(REPO)}")
    print(f"{made} file(s) created in {folder.relative_to(REPO)}")
    return 0


# --- contexts and rendering ---------------------------------------------------------------------------------------------

def get_context(key: str, d, claims) -> dict:
    import guide_contexts
    guide_contexts.load()
    if key in guide_contexts.CONTEXTS:
        return guide_contexts.CONTEXTS[key](d, claims)
    import notes
    notes.load()
    if key in notes.NOTES:
        return notes.NOTES[key].context(d, claims)
    raise KeyError(f"no context {key!r}: not a guide context and not a registered note")


class Env:
    """The Jinja environment and the data a render needs, built once per run."""

    def __init__(self):
        import jinja2
        import notes
        from db import Data
        self.notes = notes
        self.d = Data()
        self.jenv = jinja2.Environment(undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                                       keep_trailing_newline=True, autoescape=False)
        self.jenv.filters.update(notes.ENV.filters)


def stamp_row() -> str:
    v = yaml.safe_load((REPO / "_variables.yml").read_text(encoding="utf-8"))
    return f"{v['book']['edition'].capitalize()} edition, dataset release {v['dataset']['version']} ({v['dataset']['window']})"


def header_table(g: GUnit, meta: dict) -> str:
    rows = [("Unit", f"{g.base.kind.capitalize()} {g.base.number}: {g.base.title}")]
    if meta.get("kind") in ("exercise", "requirement"):
        rows.append(("Item", f"{meta['kind'].capitalize()} {meta['number']}"))
        if meta.get("perspective") not in (None, "general"):
            rows.append(("Perspective", {"financial": "Financial accounting", "managerial": "Managerial accounting",
                                         "auditing": "Auditing"}[meta["perspective"]]))
    rows.append(("Tools", meta.get("tool_label") or {"conceptual": "Workbook browsing and written work", "excel": "Excel",
                                                       "sql": "SQL (DB Browser for SQLite)", "powerbi": "Power BI Desktop",
                                                       "mixed": "More than one tool"}.get(meta.get("tool"), "")))
    if meta.get("minutes"):
        rows.append(("Time", f"About {meta['minutes']} minutes" if meta.get("kind") != "chapter-notes" and meta.get("kind") != "case-notes"
                     else f"About {meta['minutes']} minutes of class time"))
    if meta.get("solution"):
        rows.append(("Solution file", str(meta["solution"])))
    rows.append(("Release", stamp_row()))
    return "| | |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows)


def alt_text(figure: dict) -> str:
    """The alt text of a built figure: its purpose, and for a mock of an interface, "A mock of ..." (the book's rule)."""
    purpose = figure["purpose"].strip().replace("[", "(").replace("]", ")")
    if str(figure.get("kind", "")).endswith("-mock"):
        first = purpose.split(" ", 1)[0]
        return "A mock of " + (purpose[0].lower() + purpose[1:] if first in ("The", "A", "An") else purpose)
    return purpose


def render_template(env: Env, g: GUnit, path: Path) -> tuple[str, dict, list[str], str]:
    """(rendered Markdown, front matter, failed claims, the body with fences protected for scans)."""
    meta, body = split_front(path.read_text(encoding="utf-8"))
    protected, blocks = protect_fences(body)
    claims = env.notes.Claims()
    values: dict = {}
    if meta.get("note"):
        values.update(get_context(meta["note"], env.d, claims))
    for key in meta.get("uses") or []:
        values[key.replace(".", "_")] = get_context(key, env.d, claims)
    figs = {f["id"]: f for f in meta.get("figures") or []}
    used: list[str] = []

    def figure(fid: str) -> str:
        if fid not in figs:
            raise KeyError(f"figure {fid} is used but not declared in the front matter")
        used.append(fid)
        f = figs[fid]
        image = OUT / "figures" / g.folder / f"{fid}.pdf"
        if image.is_file():
            return f"![{alt_text(f)}](../figures/{g.folder}/{fid}.pdf)"
        return (f"> **[Figure placeholder {fid}]** {f['purpose']}\n"
                f"> Kind: {f['kind']} · Shows: {f.get('shows', '')} · Data: {f.get('data', 'none')} · Status: planned")

    def expected() -> str:
        import package
        import source
        if not meta.get("note"):
            return ""
        return "> " + package.paragraph(source.rendered(meta["note"])).replace("\n", "\n> ")

    def mcq_key() -> str:
        import package
        import source
        base = g.base
        pat = rf"<!--\s*Answer key, (?:Chapter|Appendix) {re.escape(base.number)}\b"
        origin = next(o for o, _ in base.lines if o.endswith("_multiple-choice.qmd"))
        comment = source.note_comment(origin, "mcq", pat)
        letters, entries = package.answer_key(comment)
        rows = ["Key: " + ", ".join(f"{i} {c}" for i, c in enumerate(letters, 1)) + ".", "",
                "| Question | Answer | Rationale |", "|---:|:---:|---|"]
        rows += [f"| {q} | {a} | {package.escape(why)} |" for q, a, why in entries]
        return "\n".join(rows)

    tmpl = env.jenv.from_string(protected, globals={
        **values, "d": env.d, "meta": meta, "unit": g, "figure": figure, "expected": expected, "mcq_key": mcq_key,
        "header": lambda: header_table(g, meta)})
    text = restore_fences(tmpl.render(), blocks)
    text = "\n".join(l.rstrip() for l in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    unused = [f for f in figs if f not in used]
    return text, meta, claims.failed + [f"figure {f} is declared but never used" for f in unused], protected


def cmd_render(units: list[GUnit], targets: list[GUnit], env: Env) -> int:
    problems = 0
    for g in targets:
        folder = GUIDES / g.folder
        out = OUT / g.folder
        if not folder.is_dir():
            if len(targets) == 1:
                print(f"{g.uid}: no templates in {folder.relative_to(REPO)}; run scaffold first")
                return 1
            continue
        out.mkdir(parents=True, exist_ok=True)
        wanted = set()
        for path in sorted(folder.glob("*.md")):
            try:
                text, meta, failed, _ = render_template(env, g, path)
            except Exception as exc:                       # noqa: BLE001 - report which template failed
                print(f"FAIL {path.relative_to(REPO)}: {type(exc).__name__}: {exc}")
                problems += 1
                continue
            for f in failed:
                print(f"CLAIM {path.name}: {f}")
                problems += 1
            (out / path.name).write_text(text, encoding="utf-8", newline="\n")
            wanted.add(path.name)
        for stale in out.glob("*.md"):
            if stale.name not in wanted:
                stale.unlink()
        print(f"{g.uid}: {len(wanted)} file(s) rendered to {out.relative_to(REPO)}")
    write_readme(units)
    return 1 if problems else 0


def write_readme(units: list[GUnit]) -> None:
    OUT.mkdir(exist_ok=True)
    rows = []
    for g in units:
        folder = OUT / g.folder
        n = len(list(folder.glob("*.md"))) if folder.is_dir() else 0
        label = (f"Chapter {g.base.number}" if g.base.kind == "chapter" else f"Part {g.base.number.split()[1]} case"
                 if g.base.kind == "case" else f"Appendix {g.base.number}")
        rows.append(f"| [{g.folder}]({g.folder}/{g.note_file}) | {label}: {g.base.title} | {n} of {len(g.files)} |")
    text = "\n".join([
        "# Instructor Notes", "",
        f"*Accounting Analytics: An Integrated Approach*, {stamp_row()}.", "",
        "One folder per chapter, comprehensive case and appendix that has exercises. Each folder holds a chapter (or case) note, "
        "with the teaching approaches, the tutorial guide and the multiple-choice key, and one file per exercise or requirement, "
        "with its purpose, a step-by-step solution, the expected values, common mistakes and a grading guide.", "",
        "These files are public, like the rest of the book. Try an exercise first, then compare your work. The values were "
        "computed from the dataset release named above; on another release or build, expect different values.", "",
        "| Folder | Unit | Files written |", "|---|---|---|", *rows, "",
        "The figures are drawn from the dataset: mocks of Excel, DB Browser for SQLite and Power BI Desktop (labeled \"A mock of\"), diagrams and charts. A mock shows the layout and values a correct answer produces, not a screenshot of the application.", ""])
    (OUT / "README.md").write_text(text, encoding="utf-8", newline="\n")


# --- checks ------------------------------------------------------------------------------------------------------------

NUMBER = re.compile(
    r"(?<![\w.@/-])(?:\d{4}-\d{2}-\d{2}|[A-Z]{1,4}-\d{4}-\d{3,}|\$\d[\d,]*(?:\.\d+)?|\d{1,3}(?:,\d{3})+(?:\.\d+)?"
    r"|\d+(?:\.\d+)?%|\d+\.\d{2,}|\d{4,})(?![\w-])")
EXPR = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)
INLINE_CODE = re.compile(r"(`+).+?\1", re.S)
LINK_TARGET = re.compile(r"\]\([^)]*\)")
PRONOUN = re.compile(r"\b(he|she|him|his|hers)\b", re.I)


def authored_prose(protected_body: str) -> str:
    text = re.sub(r"@@FENCE\d+@@", " ", protected_body)
    text = EXPR.sub(" ", text)
    text = INLINE_CODE.sub(" ", text)
    text = LINK_TARGET.sub("]", text)
    return re.sub(r"<!--.*?-->", " ", text, flags=re.S)


def stray_numbers(protected_body: str, allowed_text: str) -> list[str]:
    allowed = allowed_text.replace("\\", "")
    out = []
    for m in NUMBER.finditer(authored_prose(protected_body)):
        tok = m.group(0)
        if tok.lstrip("$") in allowed:
            continue
        out.append(tok)
    return sorted(set(out))


def figure_manifest() -> dict:
    """The figures recorded in instructor-notes/figures/manifest.json (id -> entry), empty when there is none."""
    path = OUT / "figures" / "manifest.json"
    if not path.is_file():
        return {}
    import json
    return json.loads(path.read_text(encoding="utf-8")).get("figures", {})


def solution_corpus() -> str:
    if not SOLUTIONS.is_dir():
        return ""
    chunks = []
    for p in SOLUTIONS.rglob("*.sql"):
        chunks.append(re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="replace")))
    return "\n".join(chunks)


def check_sql(blocks: list[tuple[str, str]], corpus: str, db) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for info, content in blocks:
        if info.split()[:1] != ["sql"]:
            continue
        norm = re.sub(r"\s+", " ", content.strip().rstrip(";").strip())
        if corpus and norm in corpus:
            continue
        code = "\n".join(l for l in content.split("\n") if not l.strip().startswith("--")).strip()
        if not code or re.match(r"(?is)^\s*(CREATE|DROP|INSERT|UPDATE|DELETE|ALTER)", code):
            continue
        try:
            db.execute("EXPLAIN " + code.rstrip(";"))
            warnings.append(f"SQL block not found verbatim in a solution script (it parses): {norm[:60]}...")
        except sqlite3.Error as exc:
            errors.append(f"SQL block does not run: {exc}: {norm[:60]}...")
    return errors, warnings


def check_unit(env: Env, g: GUnit, corpus: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    folder = GUIDES / g.folder
    if not folder.is_dir():
        return [f"{g.uid}: no folder {folder.relative_to(REPO)}"], warns
    have = {p.name for p in folder.glob("*.md")}
    want = set(g.files)
    for name in sorted(want - have):
        errors.append(f"{g.uid}: missing file {name}")
    for name in sorted(have - want):
        errors.append(f"{g.uid}: extra file {name} (no matching exercise, requirement or notes)")
    unit_text = g.text
    figure_ids: set[str] = set()
    db = sqlite3.connect(f"{env.d.path.resolve().as_uri()}?mode=ro", uri=True)
    for item_file in sorted(want & have):
        path = folder / item_file
        tag = f"{g.uid}/{item_file}"
        is_note = item_file.startswith("00-")
        item = next((i for i in g.items if i.filename == item_file), None)
        try:
            text, meta, failed, protected = render_template(env, g, path)
        except Exception as exc:                           # noqa: BLE001
            errors.append(f"{tag}: cannot render: {type(exc).__name__}: {exc}")
            continue
        for f in failed:
            errors.append(f"{tag}: {f}")
        if meta.get("tool") not in TOOLS:
            errors.append(f"{tag}: tool must be one of {TOOLS}")
        if not is_note:
            if meta.get("perspective") not in PERSPECTIVES:
                errors.append(f"{tag}: perspective must be one of {PERSPECTIVES}")
            if not isinstance(meta.get("minutes"), int) or meta["minutes"] <= 0:
                errors.append(f"{tag}: minutes must be a positive integer")
            if meta.get("tool") != "conceptual" and not meta.get("solution"):
                errors.append(f"{tag}: solution (the file, sheet or script that holds the model answer) is empty")
        heads = (ITEM_HEADINGS if not is_note else NOTE_HEADINGS_CASE if g.is_case else NOTE_HEADINGS_CHAPTER)
        if is_note and g.is_case and g.milestones:
            heads = heads[:4] + ["Milestone guide"] + heads[4:]
        if is_note and not g.is_case and not g.tutorials:
            heads = [h for h in heads if h != "Tutorial guide"]
        if is_note and not g.has_mcq:
            heads = [h for h in heads if h != "Multiple-choice questions"]
        found = [m.group(1).strip() for m in re.finditer(r"^## (.+?)\s*$", text, re.M)]
        if found != heads:
            errors.append(f"{tag}: the ## headings must be exactly {heads}; found {found}")
        if is_note:
            for tid, _ in g.tutorials:
                if f"### Guided Tutorial {tid}:" not in text:
                    errors.append(f"{tag}: the tutorial guide lacks Guided Tutorial {tid}")
            for n, _ in g.milestones:
                if f"### Milestone {n}:" not in text:
                    errors.append(f"{tag}: the milestone guide lacks Milestone {n}")
        elif item and item.kind == "exercise":
            for i in range(1, len(item.parts) + 1):
                if f"### Requirement ({i})" not in text:
                    errors.append(f"{tag}: the step-by-step solution lacks '### Requirement ({i})'")
        if re.search(r"\bTODO\b", text):
            errors.append(f"{tag}: contains TODO")
        leak = re.search(r"built-in method|<bound method|<function |object at 0x|\$-\d|(?<!\w)nan(?!\w)", text)
        if leak:
            errors.append(f"{tag}: a context value leaked into the text ({leak.group(0)!r}); do not name a context key like a dict method")
        if re.search(r"\{\{|\{%|@@FENCE", re.sub(r"```.*?```", " ", text, flags=re.S)):      # M and DAX in a fence may hold {{
            errors.append(f"{tag}: an unresolved template expression remains")
        words = len(re.findall(r"\w+", text))
        lo, hi = LIMITS["note" if is_note else "item"]
        if not lo <= words <= hi:
            errors.append(f"{tag}: {words} words (allowed {lo}-{hi})")
        allowed = unit_text if is_note else (item.text if item else "") + "\n" + "\n".join(
            line for _, line in g.base.lines if line.startswith("#"))
        stray = stray_numbers(protected, allowed)
        if stray:
            errors.append(f"{tag}: literal data values in the prose (use a context value): {', '.join(stray[:12])}")
        figs = meta.get("figures") or []
        manifest = figure_manifest()
        for f in figs:
            pdf = OUT / "figures" / g.folder / f"{f.get('id')}.pdf"
            if pdf.is_file():
                if f.get("id") not in manifest:
                    errors.append(f"{tag}: figure {f.get('id')} has a PDF but no entry in figures/manifest.json")
                if not (FIGURE_SOURCES / g.folder / f"{f.get('id')}.drawio").is_file():
                    errors.append(f"{tag}: figure {f.get('id')} has a PDF but no Draw.io source")
        limit = MAX_FIGURES["note" if is_note else "item"]
        if len(figs) > limit:
            errors.append(f"{tag}: {len(figs)} figures declared (at most {limit})")
        item_no = "0" if is_note else item.item_no
        for f in figs:
            fid = f.get("id", "")
            if not re.fullmatch(rf"IF-{re.escape(g.fig)}-{item_no}-[A-Z]", fid):
                errors.append(f"{tag}: figure id {fid!r} must be IF-{g.fig}-{item_no}-<letter>")
            if fid in figure_ids:
                errors.append(f"{tag}: figure id {fid} is used twice in the unit")
            figure_ids.add(fid)
            if f.get("kind") not in FIGURE_KINDS:
                errors.append(f"{tag}: figure {fid} kind must be one of {FIGURE_KINDS}")
            for k in ("purpose", "shows"):
                if not f.get(k):
                    errors.append(f"{tag}: figure {fid} lacks {k}")
        sq_err, sq_warn = check_sql(fenced_blocks(text), corpus, db)
        errors += [f"{tag}: {e}" for e in sq_err]
        warns += [f"{tag}: {w}" for w in sq_warn]
        if re.search(r"\bnamely\b", text, re.I):
            errors.append(f"{tag}: 'namely' (the book's style: use a colon)")
        pn = sorted(set(p.lower() for p in PRONOUN.findall(re.sub(r"```.*?```", " ", text, flags=re.S))))
        if pn:
            warns.append(f"{tag}: gendered pronouns {pn} (use the role or they/them)")
    return errors, warns


def cmd_check(units: list[GUnit], targets: list[GUnit], env: Env) -> int:
    corpus = solution_corpus()
    total_err = 0
    for g in targets:
        errors, warns = check_unit(env, g, corpus)
        for w in warns:
            print("warn ", w)
        for e in errors:
            print("ERROR", e)
        total_err += len(errors)
        print(f"{g.uid}: {len(g.files)} expected file(s), {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if total_err else 0


# --- figures, sources, context --------------------------------------------------------------------------------------------

def collect_figures(units: list[GUnit]) -> list[dict]:
    rows = []
    for g in units:
        folder = GUIDES / g.folder
        for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            meta, _ = split_front(path.read_text(encoding="utf-8"))
            for f in meta.get("figures") or []:
                built = (OUT / "figures" / g.folder / f"{f['id']}.pdf").is_file()
                rows.append({"id": f["id"], "unit": g.folder, "file": path.name, "kind": f.get("kind"),
                             "purpose": f.get("purpose"), "shows": f.get("shows"), "data": f.get("data"),
                             "status": "built" if built else "planned"})
    return rows


def cmd_figures(units: list[GUnit], uid: str | None = None) -> int:
    rows = collect_figures(units)
    if uid:
        code = find_unit(units, uid).fig
        for r in rows:
            if r["id"].startswith(f"IF-{code}-"):
                print(f"{r['id']}  [{r['kind']}]  {r['status']}  ({r['file']})")
                for key in ("purpose", "shows", "data"):
                    print(f"    {key}: {r[key]}")
                print()
        return 0
    OUT.mkdir(exist_ok=True)
    (OUT / "figures.yml").write_text(yaml.safe_dump(rows, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"{len(rows)} figure placeholder(s): {kinds}")
    return 0


def cmd_context(key: str) -> int:
    import notes
    env = Env()
    claims = notes.Claims()
    values = get_context(key, env.d, claims)
    for k, v in values.items():
        s = repr(notes.plain(v))
        print(f"{k} = {s[:160]}{'...' if len(s) > 160 else ''}")
    for c in claims.failed:
        print("CLAIM FAILS:", c)
    return 0


def solution_artifacts(g: GUnit) -> list[str]:
    found = []
    pats = []
    if g.uid.isdigit():
        n = int(g.uid)
        pats = [f"Chapter{n:02d}-*"]
    elif g.uid.startswith("case"):
        pats = [f"Part{ROMAN[int(g.uid[4:])]}-case*"]
    else:
        pats = [f"Appendix{g.uid[3:]}-*"]
    for pat in pats:
        found += [p.relative_to(REPO).as_posix() for p in sorted(SOLUTIONS.glob(pat)) if p.is_dir()]
    return found


def builder_modules(g: GUnit) -> list[str]:
    base = REPO / "scripts" / "companion"
    names = []
    if g.uid.isdigit():
        n = int(g.uid)
        names = [f"ex{n:02d}.py", f"cap{n}.py", f"cap{n}_monitoring.py"]
    elif g.uid.startswith("case"):
        names = [f"case{g.uid[4:]}.py"]
    else:
        names = [f"ex{g.uid[3:].lower()}.py"]
    return [p.relative_to(REPO).as_posix() for sub in ("xlbuild", "sqlbuild", "pbibuild") for nm in names
            for p in [base / sub / nm] if p.is_file()]


def cmd_sources(units: list[GUnit], g: GUnit, out: Path) -> int:
    import notes
    env = Env()
    lines = [f"# Sources for {g.folder} (unit {g.uid})", "",
             f"Templates go in facts/instructor/guides/{g.folder}/ ; rendered output goes to instructor-notes/{g.folder}/", "",
             "## Where to look", ""]
    slide = REPO / "slides" / (f"chapter-{int(g.uid):02d}" if g.uid.isdigit() else f"case-part-{g.uid[4:]}" if g.uid.startswith("case") else "none") / "index.qmd"
    lines += [f"- data facts: facts/baseline-2026.md (search the unit's number)",
              f"- chapter text: {g.base.path} and its _*.qmd includes (expanded below)",
              f"- slide deck with talk-track notes: {slide.relative_to(REPO).as_posix() if slide.is_file() else '(none)'}",
              f"- built solution files: {', '.join(solution_artifacts(g)) or '(none)'}",
              f"- builder modules (the exact steps): {', '.join(builder_modules(g)) or '(none)'}",
              f"- competency map by item: drafts/competency-map-by-item.md",
              f"- existing flat note: outputs/companion/solutions/Instructor-Notes/ (the previous package)", "",
              "## Items and file names", ""]
    lines += [f"- {g.note_file}  (chapter/case note)"]
    for i in g.items:
        lines += [f"- {i.filename}  [{i.kind} {i.number}, {i.perspective}, note key: {i.note_key or 'none'}]"]
    lines += ["", f"Tutorials: {g.tutorials}", f"Milestones: {g.milestones}", f"Has multiple-choice questions: {g.has_mcq}", ""]
    lines += ["## Existing generated instructor notes and their context keys", ""]
    for i in g.items:
        lines += [f"### {i.kind} {i.number}: {i.title}", ""]
        if i.note_key:
            claims = notes.Claims()
            text, values, failed = notes.render(notes.NOTES[i.note_key], env.d)
            lines += [f"note key: {i.note_key}", "", text, "", "context keys: " + ", ".join(values.keys()), ""]
            if failed:
                lines += ["CLAIMS THAT FAIL: " + "; ".join(failed), ""]
        else:
            archived = None
            try:
                import source
                pat = (rf"<!--\s*Instructor notes, Exercise {re.escape(i.number)}\b" if i.kind == "exercise"
                       else rf"<!--\s*Instructor notes, Requirement {i.number}\b")
                archived = source.archived_comment(i.origin, pat)
            except Exception:                                  # noqa: BLE001
                archived = None
            lines += [("archived literal note:\n\n" + archived) if archived else "no generated or archived note", ""]
        comp = competency(competency_labels(g, i))
        if comp:
            lines += [comp, ""]
    extra = []
    import source
    for tid, ttitle in g.tutorials:
        k = int(tid.split(".")[1])
        origin = (Path(g.base.path).parent / f"_tutorial-{k:02d}.qmd").as_posix()
        key = source.key_for(origin, f"t{k}")
        if key:
            text = f"note key: {key}\n\n" + notes.render(notes.NOTES[key], env.d)[0]
        else:
            text = source.archived_comment(origin, rf"<!--\s*(?:Guided )?Tutorial {re.escape(tid)}\b")
        extra += [f"### Tutorial {tid}: {ttitle}", "", text or "no generated or archived note", ""]
    for n, mt in g.milestones:
        key = source.key_for(g.base.path, f"m{n}")
        if key:
            text = f"note key: {key}\n\n" + notes.render(notes.NOTES[key], env.d)[0]
        else:
            text = source.archived_comment(g.base.path, rf"<!--\s*Instructor notes, Milestone {n}\b")
        extra += [f"### Milestone {n}: {mt}", "", text or "no generated or archived note", ""]
    if extra:
        lines += ["## Existing notes for the tutorials and milestones", "", *extra]
    lines += ["## The unit's expanded text", "", g.text]
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote {out} ({sum(len(l) for l in lines) // 1000} KB)")
    return 0


def cmd_list(units: list[GUnit], uid: str | None) -> int:
    for g in units if uid is None else [find_unit(units, uid)]:
        print(f"{g.uid:6s} fig={g.fig:3s} {g.folder}  items={len(g.items)} tutorials={len(g.tutorials)} "
              f"milestones={len(g.milestones)} mcq={g.has_mcq}")
        if uid is not None:
            print("   ", g.note_file)
            for i in g.items:
                print("   ", i.filename, f"[{i.note_key or '-'}]")
    return 0


# --- PDF files and the package ----------------------------------------------------------------------------------------------
#
# The instructor notes ship as PDF files only.  Each rendered file of instructor-notes/ becomes a PDF through pandoc
# and LuaLaTeX (facts/instructor/pdf/instructor.tex and instructor.lua: the book's fonts and colors, code on the book's
# gray, tables sized from their content), and each figure is its Draw.io vector PDF, exported the way the book exports
# its figures (build_instructor.py), so a figure's text stays text at any zoom.

PDF_FIGURE = re.compile(r"figures/([^/\s)]+)/(IF-[A-Za-z0-9-]+)\.pdf")
PDF_SETTINGS = [
    ("-V", "documentclass=scrartcl"), ("-V", "classoption=parskip=half"), ("-V", "fontsize=10pt"),
    ("-V", "papersize=letter"), ("-V", "geometry=margin=0.85in"), ("-V", "lang=en-US"),
    ("-V", "mainfont=TeX Gyre Pagella"), ("-V", "sansfont=TeX Gyre Heros"), ("-V", "monofont=Latin Modern Mono"),
    ("-V", "monofontoptions=Scale=0.9")]


def pandoc_version(pk) -> str:
    out = subprocess.run([*pk.pandoc_command(), "--version"], capture_output=True, text=True, encoding="utf-8")
    return out.stdout.split("\n", 1)[0].strip()


def pdf_key(md: Path, version: str) -> str:
    """What a PDF is built from: the Markdown, the vector PDFs of the figures it shows, the template and filter, pandoc."""
    h = hashlib.sha256()
    data = md.read_bytes().replace(b"\r\n", b"\n")
    h.update(data)
    for folder, fid in sorted(set(PDF_FIGURE.findall(data.decode("utf-8")))):
        pdf = FIGURE_PDF_DIR / folder / f"{fid}.pdf"
        h.update(pdf.read_bytes() if pdf.is_file() else b"-")
    for name in ("instructor.tex", "instructor.lua"):
        h.update((PDF_ASSETS / name).read_bytes().replace(b"\r\n", b"\n"))
    h.update(version.encode())
    return h.hexdigest()


def pandoc_pdf(pk, md: Path, out: Path) -> tuple[bool, str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [*pk.pandoc_command(), str(md), "-f", "commonmark+pipe_tables+smart+fancy_lists", "-o", str(out),
           "--pdf-engine=lualatex", "--shift-heading-level-by=-1", "--syntax-highlighting=tango"]
    for flag, value in PDF_SETTINGS:
        cmd += [flag, value]
    cmd += ["-H", str(PDF_ASSETS / "instructor.tex"), "--lua-filter", str(PDF_ASSETS / "instructor.lua"),
            "-M", f"figure-dir={FIGURE_PDF_DIR.as_posix()}",
            "--resource-path", str(md.parent)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = result.returncode == 0 and out.is_file()
    return ok, (result.stderr or "")[-1500:]


def missing_figure_pdfs(targets: list[GUnit]) -> list[str]:
    """The figures the rendered notes link whose PDF is not in instructor-notes/figures/ (build them with
    scripts/figures/instructor/build_instructor.py, which needs Draw.io and the dataset)."""
    missing = []
    for g in targets:
        for md in sorted((OUT / g.folder).glob("*.md")):
            for folder, fid in sorted(set(PDF_FIGURE.findall(md.read_text(encoding="utf-8")))):
                if not (FIGURE_PDF_DIR / folder / f"{fid}.pdf").is_file():
                    missing.append(f"{md.name}: {folder}/{fid}.pdf")
    return missing


def readme_pdf_source(units: list[GUnit]) -> Path:
    """The README of the PDF package as Markdown (the index of instructor-notes/README.md, without its links)."""
    text = (OUT / "README.md").read_text(encoding="utf-8")
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("Each folder holds a chapter (or case) note,", "Each folder holds PDF files: a chapter (or case) note,")
    path = PDF_DIR / "README.md"
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def cmd_pdf(units: list[GUnit], targets: list[GUnit], force: bool = False, jobs: int = 4) -> int:
    import package as pk
    if shutil.which("lualatex") is None:
        raise SystemExit("lualatex not found: the PDF files need a TeX distribution (MiKTeX or TeX Live) on PATH")
    if not OUT.is_dir():
        raise SystemExit("nothing rendered: run render --all first")
    missing = missing_figure_pdfs(targets)
    for line in missing:
        print(f"MISSING figure PDF {line}")
    problems = len(missing)
    version = pandoc_version(pk)
    manifest_path = PDF_DIR / "manifest.json"
    done = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    work: list[tuple[str, Path, Path, str]] = []
    for g in targets:
        for md in sorted((OUT / g.folder).glob("*.md")):
            rel = f"{g.folder}/{md.stem}"
            out = PDF_DIR / g.folder / f"{md.stem}.pdf"
            key = pdf_key(md, version)
            if force or not out.is_file() or done.get(rel) != key:
                work.append((rel, md, out, key))
    if len(targets) == len(units):
        readme = readme_pdf_source(units)
        key = pdf_key(readme, version)
        if force or not (PDF_DIR / "README.pdf").is_file() or done.get("README") != key:
            work.append(("README", readme, PDF_DIR / "README.pdf", key))
    print(f"{len(work)} PDF file(s) to build")
    results: list[tuple[str, bool, str, str]] = []
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for (rel, md, out, key), (ok, log) in zip(work, pool.map(lambda w: pandoc_pdf(pk, w[1], w[2]), work)):
            results.append((rel, ok, log, key))
            if ok:
                done[rel] = key
            else:
                problems += 1
                print(f"FAILED  {rel}\n{log}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(dict(sorted(done.items())), indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{sum(1 for r in results if r[1])} built, {sum(1 for r in results if not r[1])} failed "
          f"(PDF files in {PDF_DIR.relative_to(REPO)})")
    return 1 if problems else 0


def cmd_package(units: list[GUnit], force: bool = False, jobs: int = 4) -> int:
    """Instructor-Notes.zip: the PDF files only, one folder per unit, and a README.pdf."""
    rc = cmd_pdf(units, units, force, jobs)
    if rc:
        print("package stopped: some PDF files did not build", file=sys.stderr)
        return rc
    zpath = ZIP_OUT / ZIP_NAME
    ZIP_OUT.mkdir(parents=True, exist_ok=True)
    stale = ZIP_OUT / "Instructor-Notes"
    if stale.is_dir():
        shutil.rmtree(stale)                 # the folder the flat legacy package left beside the zip
    count = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(PDF_DIR / "README.pdf", "Instructor-Notes/README.pdf")
        count += 1
        for g in units:
            for md in sorted((OUT / g.folder).glob("*.md")):
                z.write(PDF_DIR / g.folder / f"{md.stem}.pdf", f"Instructor-Notes/{g.folder}/{md.stem}.pdf")
                count += 1
    print(f"wrote {zpath} ({count} PDF files, {zpath.stat().st_size / 1048576:.1f} MB)")
    return 0


# --- main ----------------------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("list", "scaffold", "sources", "render", "check"):
        p = sub.add_parser(name)
        p.add_argument("--unit")
        if name in ("render", "check"):
            p.add_argument("--all", action="store_true")
        if name == "scaffold":
            p.add_argument("--force", action="store_true")
        if name == "sources":
            p.add_argument("--out", required=True)
    fg = sub.add_parser("figures")
    fg.add_argument("--unit")
    c = sub.add_parser("context")
    c.add_argument("key")
    pf = sub.add_parser("pdf")
    pf.add_argument("--unit")
    pf.add_argument("--all", action="store_true")
    pf.add_argument("--force", action="store_true")
    pf.add_argument("--jobs", type=int, default=4)
    pk = sub.add_parser("package")
    pk.add_argument("--force", action="store_true")
    pk.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args(argv)
    if args.cmd == "context":
        return cmd_context(args.key)
    units = build_units()
    if args.cmd == "list":
        return cmd_list(units, args.unit)
    if args.cmd == "scaffold":
        if not args.unit:
            raise SystemExit("scaffold needs --unit")
        return cmd_scaffold(units, args.unit, args.force)
    if args.cmd == "figures":
        return cmd_figures(units, args.unit)
    if args.cmd == "package":
        return cmd_package(units, args.force, args.jobs)
    if args.cmd == "pdf":
        if not args.all and not args.unit:
            raise SystemExit("pdf needs --unit or --all")
        return cmd_pdf(units, units if args.all else [find_unit(units, args.unit)], args.force, args.jobs)
    if args.cmd == "sources":
        return cmd_sources(units, find_unit(units, args.unit), Path(args.out))
    if not args.all and not args.unit:
        raise SystemExit(f"{args.cmd} needs --unit or --all")
    targets = units if args.all else [find_unit(units, args.unit)]
    env = Env()
    return cmd_render(units, targets, env) if args.cmd == "render" else cmd_check(units, targets, env)


if __name__ == "__main__":
    sys.exit(main())
