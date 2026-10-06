"""The instructor notes document: Instructor-Notes.zip.

    python facts/instructor/package.py [--out DIR] [--no-docx] [--skip-verify]

Builds outputs/companion/solutions/Instructor-Notes.zip: a README and, for every chapter, case and
appendix in book order, one Markdown file (and a .docx of each, through Quarto's bundled pandoc, when it is
available) that reads as a teaching companion.  Per tutorial, exercise, case requirement and milestone it gives the
heading and the instructor note; per chapter, the multiple-choice answer key with its rationale for every question.

Where each text comes from:
  * headings and their order: the public .qmd files as they are now (the includes of each chapter.qmd are expanded);
  * generated notes: the templates rendered through the registry on the dataset (facts/instructor/source.py);
  * the notes that never had a template (Exercise A.1, Requirement 1 of the Part I case, the notes of Guided
    Tutorial A.2) and eleven answer keys: the literal comments archived from commit 4feb03f (baseline-4feb03f.json).
Nothing else is written: after building, the script checks that every number in every file occurs in the notes used,
in a heading of the book, or in the stamp (the dataset release and the SHA-256 values of _variables.yml).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for p in (REPO / "scripts", REPO / "facts", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import source  # noqa: E402  (facts/instructor/source.py)

OUT = REPO / "outputs" / "companion" / "solutions"
ZIP_NAME = "Instructor-Notes.zip"
INCLUDE = re.compile(r"^\{\{< include (\S+) >\}\}\s*$")
EXERCISE = re.compile(r"^\*\*Exercise (\d+|[A-Z])\.(\d+):? (.+?)\*\*")
REQUIREMENT = re.compile(r"^\*\*Requirement (\d+): (.+?)\*\*")
MILESTONE = re.compile(r"^(\d+)\. \*\*(.+?)\*\*")
TUTORIAL = re.compile(r"^## Guided Tutorial (\w+\.\d+): (.+?)\s*(\{.*\})?$")
HEADING = re.compile(r"^(#{1,4}) (.+?)\s*(\{[^}]*\})?\s*$")


# --- the book's structure ---------------------------------------------------------------------------------------------

@dataclass
class Unit:
    kind: str                 # chapter, case, appendix
    path: str                 # repository-relative path of the main file
    number: str               # "4", "A", "Part 2"
    title: str
    slug: str
    lines: list[tuple[str, str]] = field(default_factory=list)      # (origin file, line) after expanding includes


def book_units() -> list[Unit]:
    cfg = yaml.safe_load((REPO / "_quarto.yml").read_text(encoding="utf-8"))["book"]
    paths: list[str] = []
    for entry in cfg["chapters"]:
        if isinstance(entry, dict):
            paths += [c for c in entry["chapters"]]
    paths += cfg.get("appendices", [])
    units = []
    for path in paths:
        text = (REPO / path).read_text(encoding="utf-8")
        if path.startswith("chapters/"):
            n = int(re.match(r"chapters/(\d+)-", path).group(1))
            title = re.search(r'^title:\s*"(.+)"\s*$', text, flags=re.M).group(1)
            units.append(Unit("chapter", path, str(n), title, f"chapter-{n:02d}"))
        elif path.startswith("cases/"):
            n = re.match(r"cases/part-(\d+)-case", path).group(1)
            title = re.search(r"^# Comprehensive Case: (.+?)\s*\{", text, flags=re.M).group(1)
            units.append(Unit("case", path, f"Part {n}", title, f"part-{n}-case"))
        else:
            letter = re.match(r"appendices/([a-z])-", path).group(1).upper()
            title = re.search(r"^# (.+?)\s*\{", text, flags=re.M).group(1)
            units.append(Unit("appendix", path, letter, title, f"appendix-{letter.lower()}"))
    for i, u in enumerate(units, 1):
        u.slug = f"{i:02d}-{u.slug}"
        u.lines = expand(u.path)
    return units


def expand(path: str, seen: tuple = ()) -> list[tuple[str, str]]:
    """The lines of a .qmd with its includes replaced by the included files, each line with its origin file."""
    out = []
    folder = (REPO / path).parent
    for line in (REPO / path).read_text(encoding="utf-8").split("\n"):
        m = INCLUDE.match(line.rstrip("\r"))
        if m:
            ref = m.group(1)
            target = ((REPO / ref.lstrip("/")) if ref.startswith("/") else (folder / ref)).resolve().relative_to(REPO).as_posix()
            if target in seen:
                raise ValueError(f"include loop at {target}")
            out += expand(target, seen + (path,))
        else:
            out.append((path, line.rstrip("\r")))
    return out


# --- notes ------------------------------------------------------------------------------------------------------------

def inner(comment: str) -> str:
    """A comment's text without its markers, on one line."""
    return re.sub(r"\s+", " ", re.sub(r"^<!--|-->$", "", comment.strip())).strip()


def note_for(origin: str, name: str, pattern: str) -> str | None:
    """The note's comment: rendered through the registry, else the archived literal, else None."""
    try:
        return source.note_comment(origin, name, pattern)
    except KeyError:
        return None


CODE_SPAN = re.compile(r"(`+)(.+?)\1", re.S)
SPECIAL = re.compile(r"([\\<>*_\[\]#|~$])")


def escape(text: str) -> str:
    """Markdown-escape the text outside its code spans (a note holds <id>, $A5, [@Quantity], * and _ as plain text)."""
    out, pos = [], 0
    plain = lambda t: SPECIAL.sub(r"\\\1", t)
    for m in CODE_SPAN.finditer(text):
        out += [plain(text[pos:m.start()]), m.group(0)]
        pos = m.end()
    out.append(plain(text[pos:]))
    return "".join(out)


def paragraph(comment: str) -> str:
    """A note as Markdown: its label (up to the first colon outside parentheses) in bold, then its text as one
    paragraph."""
    text = inner(comment)
    depth = 0
    for i, ch in enumerate(text[:400]):
        depth += (ch == "(") - (ch == ")")
        if ch == ":" and depth == 0 and i >= 3 and text[i + 1:i + 2] == " ":
            return f"**{escape(text[:i])}:** {escape(text[i + 1:].strip())}"
    return escape(text)


KEY_ENTRY = re.compile(r"^\s+(\d+) ([A-D]): (.*)$")


def answer_key(comment: str) -> tuple[list[str], list[tuple[int, str, str]]]:
    """The key line of an answer-key comment ('1 D, 2 A, ...') as letters, and its (question, letter, rationale)."""
    lines = comment.strip().split("\n")
    key_line = lines[1].strip().rstrip(".")
    letters = re.findall(r"\d+ ([A-D])", key_line)
    entries: list[list] = []
    for line in lines[2:]:
        line = re.sub(r"\s*-->$", "", line)
        m = KEY_ENTRY.match(line)
        if m:
            entries.append([int(m.group(1)), m.group(2), m.group(3).strip()])
        elif entries and line.strip():
            entries[-1][2] += " " + line.strip()
    return letters, [tuple(e) for e in entries]


def claude_keys() -> dict[str, str]:
    """The keys CLAUDE.md lists as 'Multiple-choice keys used so far' (chapter number or 'A' -> letters)."""
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    line = next(l for l in text.split("\n") if "Multiple-choice keys used so far" in l)
    keys = {m.group(1): m.group(2) for m in re.finditer(r"\bch(\d+) ([A-D]+)", line)}
    keys["A"] = re.search(r"appendix A ([A-D]+)", line).group(1)
    return keys


# --- one unit's document ----------------------------------------------------------------------------------------------

@dataclass
class Result:
    md: str
    notes: int = 0                    # items that carry a note
    items: int = 0
    missing: list[str] = field(default_factory=list)     # items the book holds no note for
    keys: dict = field(default_factory=dict)
    used: list[str] = field(default_factory=list)        # the texts the body was assembled from
    headings: list[str] = field(default_factory=list)


def stamp_lines(v: dict) -> list[str]:
    d = v["dataset"]
    return [f"Accounting Analytics: An Integrated Approach, {v['edition']} edition. Dataset release {d['version']} "
            f"({d['window']}).", "Public, like the rest of the book: try an exercise first, then compare your work."]


def render_unit(u: Unit, v: dict, keys_expected: dict[str, str]) -> Result:
    r = Result(md="")
    body: list[str] = []
    h1 = (f"Chapter {u.number}: {u.title}" if u.kind == "chapter"
          else f"Comprehensive Case, {u.number}: {u.title}" if u.kind == "case"
          else f"Appendix: {u.title}")
    r.headings.append(h1)
    head = [f"# {h1}", "", *stamp_lines(v), ""]

    emitted: dict[int, str] = {}              # the headings above the current item, by level, already written
    context: dict[int, str] = {}              # the source's current headings, by level
    in_fence = False

    def emit_context(upto: int) -> int:
        """Write the pending context headings (levels 2..upto) and return the deepest level written."""
        deepest = 1
        for lvl in range(2, upto + 1):
            if lvl in context and emitted.get(lvl) != context[lvl]:
                body.extend([f"{'#' * lvl} {context[lvl]}", ""])
                r.headings.append(context[lvl])
                emitted[lvl] = context[lvl]
                for deeper in [k for k in emitted if k > lvl]:
                    del emitted[deeper]
            if lvl in context:
                deepest = lvl
        return deepest

    def add_note(level: int, heading: str, comment: str | None, kind: str, label: str):
        body.extend([f"{'#' * level} {heading}", ""])
        r.headings.append(heading)
        r.items += 1
        if comment is None:
            body.extend(["No separate instructor note: the book holds none for this " + kind + ".", ""])
            r.missing.append(label)
        else:
            text = paragraph(comment)
            body.extend([text, ""])
            r.used.append(inner(comment))
            r.notes += 1

    for origin, line in u.lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        hm = HEADING.match(line)
        if hm:
            level, text = len(hm.group(1)), hm.group(2).strip()
            text = re.sub(r"\s*\{.*\}$", "", text)
            if level >= 2:
                context[level] = text
                for deeper in [k for k in context if k > level]:
                    del context[deeper]
        tm = TUTORIAL.match(line)
        if tm:
            tid, title = tm.group(1), re.sub(r"\s*\{.*\}$", "", tm.group(2))
            name = f"t{tid.split('.')[1]}"
            pat = rf"<!--\s*(?:Guided )?Tutorial {re.escape(tid)}\b"
            comment = note_for(origin, name, pat)
            emitted.clear()
            add_note(2, f"Guided Tutorial {tid}: {title}", comment, "tutorial", f"Tutorial {tid}")
            continue
        if origin.endswith("_multiple-choice.qmd") and hm and len(hm.group(1)) == 2:
            number = u.number if u.kind == "chapter" else "A"
            pat = rf"<!--\s*Answer key, (?:Chapter|Appendix) {number}\b"
            comment = note_for(origin, "mcq", pat)
            emitted.clear()
            body.extend(["## Multiple-Choice Answer Key", ""])
            r.headings.append("Multiple-Choice Answer Key")
            if comment is None:
                body.extend(["No answer key is archived for this chapter.", ""])
                r.missing.append("answer key")
            else:
                letters, entries = answer_key(comment)
                if [e[1] for e in entries] != letters or [e[0] for e in entries] != list(range(1, len(letters) + 1)):
                    raise ValueError(f"{origin}: the answer key's list and its rationales disagree")
                r.keys[number] = "".join(letters)
                body.extend(["Key: " + ", ".join(f"{i} {c}" for i, c in enumerate(letters, 1)) + ".", "",
                             "| Question | Answer | Rationale |", "|---:|:---:|---|"])
                body.extend(f"| {q} | {a} | {escape(why)} |" for q, a, why in entries)
                body.append("")
                r.used.append(inner(comment))
                r.items += 1
                r.notes += 1
            continue
        em = EXERCISE.match(line)
        if em and origin.endswith("_exercises.qmd"):
            ch, n, title = em.group(1), em.group(2), em.group(3).rstrip(".")
            pat = rf"<!--\s*Instructor notes, Exercise {re.escape(ch)}\.{n}\b"
            comment = note_for(origin, f"ex{n}", pat)
            deepest = emit_context(3)
            add_note(deepest + 1, f"Exercise {ch}.{n}: {title}", comment, "exercise", f"Exercise {ch}.{n}")
            continue
        rm = REQUIREMENT.match(line)
        if rm:
            n, title = rm.group(1), rm.group(2).rstrip(".").strip()
            pat = rf"<!--\s*Instructor notes, Requirement {n}\b"
            comment = note_for(origin, f"r{n}", pat)
            deepest = emit_context(3)
            add_note(deepest + 1, f"Requirement {n}: {title}", comment, "requirement", f"Requirement {n}")
            continue
        mm = MILESTONE.match(line)
        if mm and context.get(2) == "Getting Started":
            n, title = mm.group(1), mm.group(2).rstrip(".").strip()
            pat = rf"<!--\s*Instructor notes, Milestone {n}\b"
            comment = note_for(origin, f"m{n}", pat)
            if comment is None:
                continue                       # a numbered list item of Getting Started that is not a milestone
            deepest = emit_context(2)
            add_note(deepest + 1, f"Milestone {n}: {title}", comment, "milestone", f"Milestone {n}")
    for k, letters in r.keys.items():
        want = keys_expected.get(k)
        if want is not None and want != letters:
            r.missing.append(f"KEY MISMATCH {k}: archive {letters}, CLAUDE.md {want}")
    r.md = "\n".join(head + body).rstrip("\n") + "\n"
    return r


# --- README, verification, packaging ----------------------------------------------------------------------------------

def readme(units: list[Unit], results: list[Result], v: dict, docx: bool) -> str:
    d = v["dataset"]
    rows = [f"| {u.slug}.md | {('Chapter ' + u.number) if u.kind == 'chapter' else ('Part ' + u.number.split()[1] + ' case') if u.kind == 'case' else 'Appendix'}: "
            f"{u.title} | {res.notes} of {res.items} |" for u, res in zip(units, results)]
    return "\n".join([
        f"# Instructor Notes, {v['edition']} edition", "",
        f"*Accounting Analytics: An Integrated Approach*, {v['edition']} edition, built on the Charles River dataset "
        f"release {d['version']} ({d['window']}).", "",
        "These files are public, like the rest of the book. Try an exercise first, then compare your work with the solution.", "",
        "## What these files hold", "",
        "One file per chapter, comprehensive case and appendix, in the order of the book" +
        (" (each also as a Word document)" if docx else "") + ". Each gives, for every guided tutorial, exercise, case "
        "requirement and milestone, the book's heading and the instructor note: the values to expect on this dataset "
        "release, the conditions the exercise depends on, and what a strong answer says. A chapter that has "
        "multiple-choice questions also gives the answer key with a rationale for every question.", "",
        "The values were computed from the dataset release named above. On a different release or build of the "
        "dataset, expect different values; the instructor notes of that release replace these.", "",
        "## Dataset release", "",
        f"- Edition: {v['edition']}", f"- Dataset release: {d['version']} ({d['window']})",
        f"- CharlesRiver.sqlite SHA-256: {d['sha256']['sqlite']}",
        f"- CharlesRiver.xlsx SHA-256: {d['sha256']['xlsx']}",
        f"- CharlesRiver_csv (zip) SHA-256: {d['sha256']['csv']}", "",
        "## Files", "", "| File | Contents | Items with a note |", "|---|---|---|", *rows, "",
        "Items without a note are listed in the file with a line that says so: the book holds no instructor note for "
        "them.", ""])


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d[\d,.]*\d|\d", text))


def unescape(text: str) -> str:
    return re.sub(r"\\([\\<>*_\[\]#|~$])", r"\1", text)


def verify(units: list[Unit], results: list[Result], readme_text: str, v: dict) -> list[str]:
    """What the files hold is only what the notes hold: every paragraph is exactly one note (its label in bold, the
    escapes undone), every answer and rationale is in the archived key, and every number is in a note, a heading or
    the stamp."""
    problems = []
    stamp = numbers(" ".join(stamp_lines(v)))
    for u, res in zip(units, results):
        used = set(res.used)
        allowed = stamp | numbers(" ".join(res.used)) | numbers(" ".join(res.headings)) | numbers(u.slug)
        body = [l for l in res.md.split("\n") if l.strip() and not l.startswith("#")]
        for tok in numbers("\n".join(body)):
            if tok not in allowed:
                problems.append(f"{u.slug}: the number {tok} is not in a note, a heading or the stamp")
        key_text = " ".join(t for t in res.used if t.startswith("Answer key"))
        for line in body:
            if line.startswith("|"):
                cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
                if cells[0].isdigit() and f"{cells[0]} {cells[1]}: {unescape(cells[2])}" not in key_text:
                    problems.append(f"{u.slug}: row {cells[0]} of the key is not in the archived key")
                continue
            if line in stamp_lines(v) or line.startswith("Key: ") or line.startswith("No separate instructor note"):
                continue
            plain = re.sub(r"^\*\*(.+?):\*\* ", r"\1: ", unescape(line))
            if plain not in used:
                problems.append(f"{u.slug}: a paragraph is not a note: {plain[:70]}")
    return problems


def pandoc_command() -> list[str] | None:
    """Quarto's bundled pandoc (its tools folder), run directly: `quarto pandoc` on Windows drops the start of a long
    output line, so the converted text is checked and written with the bundled executable itself."""
    q = shutil.which("quarto")
    if not q:
        return None
    tools = Path(q).resolve().parent / "tools"
    for name in ("pandoc.exe", "pandoc"):
        if (tools / name).is_file():
            return [str(tools / name)]
    return [q, "pandoc"]


READER = "commonmark+pipe_tables"


def pandoc_docx(md: Path, docx: Path) -> bool:
    pandoc = pandoc_command()
    ref = REPO / "styles" / "reference.docx"
    cmd = [*pandoc, str(md), "-f", READER, "-o", str(docx)]
    if ref.is_file():
        cmd += ["--reference-doc", str(ref)]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"no .docx for {md.name}: {exc}", file=sys.stderr)
        return False


def plain_text(path: Path, reader: str | None = None) -> str:
    cmd = [*pandoc_command(), str(path), "-t", "plain", "--wrap=none"] + (["-f", reader] if reader else [])
    return subprocess.run(cmd, check=True, capture_output=True, encoding="utf-8").stdout


def check_docx(md: Path, docx: Path) -> bool:
    """The .docx says what the Markdown says: both read back as the same words."""
    words = lambda t: [w for w in re.sub(r"[‘’]", "'", re.sub(r"[“”]", '"', t)).split() if set(w) != {"-"}]
    return words(plain_text(md, READER)) == words(plain_text(docx))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--no-docx", action="store_true")
    ap.add_argument("--skip-verify", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    v = yaml.safe_load((REPO / "_variables.yml").read_text(encoding="utf-8"))
    units = book_units()
    expected = claude_keys()
    results = [render_unit(u, v, expected) for u in units]
    docx_ok = not args.no_docx and pandoc_command() is not None
    readme_text = readme(units, results, v, docx_ok)
    problems = [] if args.skip_verify else verify(units, results, readme_text, v)
    folder = out / "Instructor-Notes"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    (folder / "README.md").write_text(readme_text, encoding="utf-8", newline="\n")
    made_docx = 0
    for u, res in zip(units, results):
        md = folder / f"{u.slug}.md"
        md.write_text(res.md, encoding="utf-8", newline="\n")
        if docx_ok:
            made_docx += pandoc_docx(md, md.with_suffix(".docx"))
            if not check_docx(md, md.with_suffix(".docx")):
                problems.append(f"{u.slug}: the .docx does not read back as the Markdown")
    if docx_ok:
        pandoc_docx(folder / "README.md", folder / "README.docx")
    zpath = out / ZIP_NAME
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.iterdir()):
            z.write(f, f"Instructor-Notes/{f.name}")
    keys = {k: s for res in results for k, s in res.keys.items()}
    mismatches = [m for res in results for m in res.missing if m.startswith("KEY MISMATCH")]
    missing = [(u.slug, m) for u, res in zip(units, results) for m in res.missing if not m.startswith("KEY MISMATCH")]
    print(f"{len(units)} files, {sum(r.items for r in results)} items, {sum(r.notes for r in results)} with a note; "
          f"{len(keys)} answer keys, {len(mismatches)} mismatch(es) with CLAUDE.md; {made_docx} .docx; zip {zpath}")
    for m in mismatches:
        print("  ", m)
    for u, m in missing:
        print(f"   no note: {u} {m}")
    for p in problems:
        print("VERIFY", p)
    return 1 if problems or mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
