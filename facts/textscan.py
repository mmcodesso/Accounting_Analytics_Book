"""Find and classify the years, document IDs, and dates in the text a yearly roll rewrites.

Phase 7 of the companion-files and yearly-roll program keeps readable literals written for the edition
(fiscal 2026, SI-2025-007947, 2026-12-11) in the source. At each roll, scripts/roll_text.py rewrites
every classified literal from the old edition's value to the new one, and `python scripts/facts.py lint`
fails on any literal no rule covers. This module is the engine both use. The classification lives in
facts/literals/:

- years.yml: the rules that classify a year by its context: a role year of the window (fiscal 2026,
  December 2026, 2024-2026, FiscalYear = 2026), the edition, or a real-world date that a roll keeps (a
  citation, a software release, a standard's effective date), with per-file decisions;
- ids.yml: document IDs (SI-2025-007947) and their keys in facts/visible.py, which selects the document
  with the same role in any build;
- dates.yml: dates; a structural date (the first or last day of a month) moves with its year, a data
  date is a key, a hypothetical date tied to the window shifts with its year, and real-world dates stay.

Exact values (29,756,420.08, 47.49%) belong to facts/visible_values.py and facts/literals/values.yml.

Generated note regions (a "<!-- notes: KEY -->" line and the comment after it) are skipped: `facts.py
sync` rewrites them from the templates.
"""

from __future__ import annotations

import calendar
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
LITERALS = HERE / "literals"

# --- scope (the same files facts/visible_values.py scans) ---------------------------------------

BOOK_DIRS = ["front-matter", "chapters", "cases", "appendices", "back-matter", "shared/fragments"]
CODE_GLOBS = ["shared/calculations/*.py", "scripts/figures/*.py", "scripts/companion/xlbuild/*.py",
              "scripts/companion/pbibuild/*.py", "scripts/companion/sqlbuild/*.py", "facts/notes/*.py",
              "facts/notes/templates/**/*.md"]
# Code of the slide project that mirrors the text (the refresh scripts and their tests): scanned for years, IDs and
# dates; the exact values in them are the slide project's own facts (facts/visible_values.py does not scan them).
YEAR_ONLY_GLOBS = ["scripts/slides/*.py", "tests/test_slide*.py"]
# Generated, never classified or rewritten (scripts/build_all.py --refresh-shared rebuilds them):
# shared/generated/, slides/_shared/, slides/_variables.yml, slides/_build/.


def excluded(rel: str) -> bool:
    """Reference lists and further reading: their years are publication years."""
    name = rel.rsplit("/", 1)[-1]
    return name in ("_references.qmd", "_further-reading.qmd") or name.startswith("_reference-")


def scope_files(root: Path = REPO, code: bool = True) -> list[Path]:
    out = [root / "index.qmd"]
    for d in BOOK_DIRS:
        out += sorted((root / d).rglob("*.qmd"))
    out += sorted(root.glob("slides/chapter-*/index.qmd"))
    if code:
        for g in CODE_GLOBS + YEAR_ONLY_GLOBS:
            out += sorted(root.glob(g))
    return [p for p in out if p.is_file() and not excluded(rel_of(p, root))]


def values_scanned(rel: str) -> bool:
    """Whether facts/visible_values.py scans this file for exact values."""
    from fnmatch import fnmatch
    return not any(fnmatch(rel, g) for g in YEAR_ONLY_GLOBS)


def rel_of(path: Path, root: Path = REPO) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    """A file's text with LF line ends (what the scanners and the rewriter's offsets use)."""
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def is_code(rel: str) -> bool:
    return rel.endswith(".py")


# --- generated note regions --------------------------------------------------------------------

NOTE_REGION = re.compile(r"<!-- notes: (?P<key>[\w.-]+) -->\r?\n<!--.*?-->", re.S)


def note_spans(text: str) -> list[tuple[int, int]]:
    return [m.span() for m in NOTE_REGION.finditer(text)]


def masked(text: str) -> str:
    """The text with the generated note regions blanked (same length, newlines kept)."""
    return NOTE_REGION.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


# --- literal patterns --------------------------------------------------------------------------

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]
MONTH_ABBR = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Sept": 9,
              "Oct": 10, "Nov": 11, "Dec": 12}
MONTH_NUM = {m: i for i, m in enumerate(MONTH_NAMES, 1)} | MONTH_ABBR
MONTH_RX = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|" \
           r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)"

# A document number: a prefix, the fiscal year, a sequence (SI-2025-007947, PROMO-2026-008, V0002-2024-000182).
ID_RX = re.compile(r"(?<![\w-])(?P<id>[A-Z][A-Z0-9]{1,9}-(?P<y>20\d\d)-\d{2,7})(?![\w-]|\.\d)")
# Codes without a year: item codes (FUR-DSK-0075), check numbers (CHK0006076), asset codes (MFG-0006), and the
# workbook's Table names (T17_SalesInvoiceLine, schema names that a roll keeps; contract S1 guards them).
CODE_RX = re.compile(r"(?<![\w-])(?:[A-Z]{3}-[A-Z]{3}-\d{4}|CHK\d{4,}|MFG-\d{4}|T\d{1,3}_[A-Z][A-Za-z]+)(?![\w-])")
# Clock times (10:00:00, 07:00-15:30).
TIME_RX = re.compile(r"(?<![\w:.,$\[])(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?![\w:]|\.\d)")
DATE_RXS = [
    ("iso", re.compile(r"(?<![\w-])(?P<y>20\d\d)-(?P<m>0[1-9]|1[0-2])-(?P<d>0[1-9]|[12]\d|3[01])(?![\w-]|\d)")),
    ("dmy", re.compile(rf"(?<![\w-])(?P<d>[1-9]|[12]\d|3[01]) (?P<mon>{MONTH_RX})\.?,? (?P<y>20\d\d)(?!\d)")),
    ("mdy", re.compile(rf"(?<![\w-])(?P<mon>{MONTH_RX})\.? (?P<d>[1-9]|[12]\d|3[01]),? (?P<y>20\d\d)(?!\d)")),
    ("dm", re.compile(rf"(?<![\w.-])(?P<d>[1-9]|[12]\d|3[01]) (?P<mon>{MONTH_RX})\b(?!,? 20\d\d)")),
    ("md", re.compile(rf"(?<![\w-])(?P<mon>{MONTH_RX})\.? (?P<d>[1-9]|[12]\d|3[01])(?![\d.,:]\d|\d|[%-])(?!,? 20\d\d)")),
]
FENCE_RX = re.compile(r"^\s*```[^\n]*\n.*?^\s*```", re.M | re.S)
YEAR_RX = re.compile(r"(?<![\d.,$])(?P<y>20\d\d)(?![\d]|[.,]\d)")


@dataclass
class Lit:
    """One literal in a file: a year, a document ID, or a date."""
    file: str
    kind: str               # "year" | "id" | "date"
    start: int
    end: int
    text: str
    line: int
    year: int | None = None
    shape: str | None = None    # dates: iso, dmy, mdy, dm, md
    cls: str = ""           # year: role | edition | real; id: key | constant; date: key | shift | structural | real | constant
    key: str | None = None
    rule: str = ""
    context: str = ""
    problem: str = ""       # why the lint fails it (empty: classified)

    def where(self) -> str:
        return f"{self.file}:{self.line}"


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def context_of(text: str, a: int, b: int, width: int = 70) -> str:
    return re.sub(r"\s+", " ", text[max(0, a - width):b + width]).strip()


def date_parts(lit: Lit) -> tuple[int | None, int, int]:
    """(year or None, month, day) of a date literal."""
    for shape, rx in DATE_RXS:
        if shape == lit.shape:
            m = rx.fullmatch(lit.text)
            mon = int(m.group("m")) if shape == "iso" else MONTH_NUM[m.group("mon")]
            y = int(m.group("y")) if "y" in m.groupdict() and m.group("y") else None
            return y, mon, int(m.group("d"))
    raise ValueError(lit.text)


def is_month_end(y: int | None, mon: int, day: int) -> bool:
    if y is None:
        return day == calendar.monthrange(2000 if mon == 2 and day == 29 else 2001, mon)[1] or (mon == 2 and day == 28)
    return day == calendar.monthrange(y, mon)[1]


def render_date(iso: str, shape: str, like: str | None = None) -> str:
    """An ISO date in a literal's shape (ISO, 11 December 2026, December 11, 2026, 11 December, December 11)."""
    y, mon, day = (int(x) for x in iso.split("-"))
    name = MONTH_NAMES[mon - 1]
    if like:   # keep an abbreviated month as the literal wrote it
        m = re.search(MONTH_RX, like)
        if m and m.group(0) in MONTH_ABBR:
            name = next(k for k, v in MONTH_ABBR.items() if v == mon and (len(k) == len(m.group(0)) or k != "Sept"))
        comma = "," in like
    else:
        comma = True
    return {"iso": f"{y:04d}-{mon:02d}-{day:02d}", "dmy": f"{day} {name} {y}",
            "mdy": f"{name} {day}{',' if comma else ''} {y}", "dm": f"{day} {name}", "md": f"{name} {day}"}[shape]


def find(rel: str, text: str, names: tuple[str, ...] = ()) -> list[Lit]:
    """Every year, document ID, and date in the text outside the generated note regions."""
    t = masked(text)
    out: list[Lit] = []
    taken: list[tuple[int, int]] = []

    def free(a, b):
        return not any(a < y and x < b for x, y in taken)

    for m in ID_RX.finditer(t):
        out.append(Lit(rel, "id", m.start("id"), m.end("id"), m.group("id"), line_of(t, m.start()), int(m.group("y"))))
        taken.append(m.span("id"))
    if names:
        name_rx = re.compile(r"(?<![\w-])(?:" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")(?![\w-])")
        for m in name_rx.finditer(t):
            out.append(Lit(rel, "name", m.start(), m.end(), m.group(0), line_of(t, m.start())))
            taken.append(m.span())
    for m in CODE_RX.finditer(t):
        if free(*m.span()):
            out.append(Lit(rel, "code", m.start(), m.end(), m.group(0), line_of(t, m.start())))
            taken.append(m.span())
    for m in TIME_RX.finditer(t):
        if free(*m.span()):
            out.append(Lit(rel, "time", m.start(), m.end(), m.group(0), line_of(t, m.start())))
            taken.append(m.span())
    for shape, rx in DATE_RXS:
        for m in rx.finditer(t):
            a, b = m.span()
            if not free(a, b):
                continue
            y = m.groupdict().get("y")
            out.append(Lit(rel, "date", a, b, m.group(0), line_of(t, a), int(y) if y else None, shape))
            taken.append((a, b))
    for m in YEAR_RX.finditer(t):
        a, b = m.span()
        if not free(a, b):
            continue
        out.append(Lit(rel, "year", a, b, m.group(0), line_of(t, a), int(m.group("y"))))
    for lit in out:
        lit.context = context_of(t, lit.start, lit.end)
    return sorted(out, key=lambda x: x.start)


# --- the classification files ------------------------------------------------------------------

@lru_cache(maxsize=None)
def load(name: str, root: str | None = None) -> dict:
    import yaml
    base = Path(root) / "facts" / "literals" if root else LITERALS
    path = base / f"{name}.yml"
    if not path.exists():
        path = LITERALS / f"{name}.yml"
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}


def _file_entries(section: dict | None, rel: str) -> list:
    """Entries of a per-file section; keys are paths or globs (fnmatch)."""
    from fnmatch import fnmatch
    out = []
    for pattern, entries in (section or {}).items():
        if pattern == rel or fnmatch(rel, pattern):
            out += entries if isinstance(entries, list) else [entries]
    return out


@lru_cache(maxsize=20000)
def _compile(rx: str, year_text: str) -> tuple[re.Pattern, int]:
    """rx with each {Y} replaced by a named group Y0, Y1, ... matching the literal."""
    parts = rx.split("{Y}")
    out = parts[0]
    for i, part in enumerate(parts[1:]):
        out += f"(?P<Y{i}>{re.escape(year_text)})" + part
    return re.compile(out, re.M), len(parts) - 1


def _covers(rx: str, t: str, lit: Lit, window: int = 220, flags=0) -> bool:
    """Does a match of rx (with {Y} standing for this literal) contain the literal?"""
    if rx == "*":
        return True
    a, b = max(0, lit.start - window), min(len(t), lit.end + window)
    pat, groups = _compile(rx, lit.text)
    for m in pat.finditer(t, a, b):
        if groups:
            if any(m.span(f"Y{i}") == (lit.start, lit.end) for i in range(groups)):
                return True
        elif m.start() <= lit.start and lit.end <= m.end():
            return True
    return False


def _near(rx: str, t: str, lit: Lit, window: int) -> re.Match | None:
    """A match of rx within `window` characters of the literal, in the same paragraph."""
    a, b = max(0, lit.start - window), min(len(t), lit.end + window)
    para_a = t.rfind("\n\n", a, lit.start)
    para_b = t.find("\n\n", lit.end, b)
    return re.compile(rx).search(t, para_a + 2 if para_a >= 0 else a, para_b if para_b >= 0 else b)


# --- citations: the authors and years of the book's reference lists ------------------------------

STOP = {"The", "And", "For", "Of", "In", "On", "To", "A", "An", "Guide", "Accounting", "Analytics", "Data", "Audit",
        "Retrieved", "Available", "Journal", "Review", "Report", "Vol", "Learn", "Power", "Desktop", "Microsoft Learn"}


@lru_cache(maxsize=None)
def citation_names(root: str) -> dict[str, frozenset[str]]:
    """Year (with any suffix letter stripped) -> capitalized words of the author parts of the entries citing it."""
    r = Path(root)
    files = list(r.glob("chapters/*/_references.qmd")) + list(r.glob("chapters/*/_further-reading.qmd")) + \
        list(r.glob("appendices/*/_references.qmd")) + list(r.glob("shared/fragments/_reference-*.qmd")) + \
        [r / "front-matter" / "preface.qmd", r / "back-matter" / "closing.qmd"] + list(r.glob("cases/*.qmd"))
    names: dict[str, set[str]] = {}
    entry = re.compile(r"^(?:[-*]\s+|\d+\.\s+)?(?P<auth>[^\n(]{2,400}?)\((?P<y>(?:19|20)\d\d)[a-z]?(?:, [^)]*)?\)\.", re.M)
    for f in files:
        if not f.is_file():
            continue
        for m in entry.finditer(f.read_text(encoding="utf-8")):
            words = set(re.findall(r"\b[A-Z][\w'-]+\b|\[(?:[A-Z&]{2,}[\w&]*)\]", m.group("auth")))
            words = {w.strip("[]") for w in words} - STOP
            names.setdefault(m.group("y"), set()).update(w for w in words if len(w) >= 2)
    return {y: frozenset(v) for y, v in names.items()}


CITE_BEFORE = re.compile(r"\[?(?P<w>[A-Z][\w'’-]*)\]?(?P<etal>\s+et\s+al\.)?"
                         r"(?:,\s+(?:19|20)\d\d[a-z]?(?:,\s+pp?\.\s*[\d–-]+)?)*(?:,\s+|\s+\()$")


def is_citation(t: str, lit: Lit, root: str) -> bool:
    """A year in an in-text citation: "(Kimball & Ross, 2013)", "Ferrari and Russo (2026)", "(AICPA, 2023; IIA, 2024)",
    "Nickell et al. (2023)": the word before it is an author of a reference with that year, an organization's
    abbreviation, or followed by et al."""
    before = t[max(0, lit.start - 60):lit.start]
    m = CITE_BEFORE.search(before)
    if not m or not re.match(r"[a-z]?(?:[);,:]|\s)", t[lit.end:lit.end + 2] or " "):
        return False
    if m.group(0).endswith(" (") and not re.match(r"[a-z]?\)", t[lit.end:lit.end + 2]):
        return False
    w = m.group("w")
    return bool(m.group("etal")) or bool(re.fullmatch(r"[A-Z][A-Z0-9&]{1,7}", w)) or w in citation_names(root).get(lit.text, ())


# --- classification ----------------------------------------------------------------------------

def year_bounds(F: int, N: int, root: str | None = None) -> tuple[int, int]:
    lo, hi = (load("years", root).get("range") or [-1, 2])
    return F + lo, N + hi


def classify(rel: str, text: str, F: int, N: int, ids: dict[str, object] | None = None,
             root: Path = REPO) -> list[Lit]:
    """Find the literals of a file and classify each; Lit.problem says why one is not covered.

    `ids` is the snapshot (key -> value) the ID and date keys are checked against."""
    rs = str(root)
    years, idsy, datesy = load("years", rs), load("ids", rs), load("dates", rs)
    lo, hi = year_bounds(F, N, rs)
    t = masked(text)
    name_keys = dict(idsy.get("names") or {})
    lits = [x for x in find(rel, text, tuple(name_keys)) if x.year is None or lo <= x.year <= hi or x.kind != "year"]
    fences = [] if is_code(rel) else [m.span() for m in FENCE_RX.finditer(t)]
    allow_y = _file_entries(years.get("files"), rel)
    id_keys = dict(idsy.get("ids") or {})
    id_const = _file_entries(idsy.get("constant"), rel)
    d_keys = {str(k): v for k, v in (datesy.get("dates") or {}).items()}
    d_file = _file_entries(datesy.get("files"), rel)

    for lit in lits:
        if lit.kind == "code" and re.fullmatch(r"T\d{1,3}_[A-Za-z]+", lit.text):
            lit.cls, lit.rule = "constant", "a Table name of the workbook (schema; contract S1)"
            continue
        if lit.kind == "name":
            lit.cls, lit.key = "key", name_keys[lit.text]
            if ids is not None and str(ids.get(lit.key)) != lit.text:
                lit.problem = f"{lit.key} is {ids.get(lit.key)!r} on this dataset, the text shows {lit.text!r}"
            continue
        if lit.kind == "time":
            hit = next((e for e in d_file if _covers(e["rx"], t, lit)), None)
            key = {str(k): v for k, v in (datesy.get("times") or {}).items()}.get(lit.text)
            if hit is not None:
                lit.key = hit.get("key")
                lit.cls, lit.rule = ("key" if lit.key else hit.get("class", "constant")), hit.get("why", "")
            elif key is not None:
                lit.cls, lit.key = "key", key
            else:
                lit.problem = "clock time with no key or per-file decision in dates.yml"
            if lit.cls == "key" and ids is not None and str(ids.get(lit.key)) != lit.text:
                lit.problem = f"{lit.key} is {ids.get(lit.key)!r} on this dataset, the text shows {lit.text!r}"
            continue
        if lit.kind in ("id", "code"):
            hit = next((e for e in id_const if _covers(e["rx"], t, lit)), None)
            if hit is not None:
                lit.cls, lit.rule = "constant", hit.get("why", "constant")
                continue
            if lit.year is not None and not (lo <= lit.year <= hi):
                lit.cls, lit.rule = "constant", "outside the window"
                continue
            key = id_keys.get(lit.text)
            if key is None:
                lit.problem = "document ID with no key in ids.yml"
            else:
                lit.cls, lit.key = "key", key
                if ids is not None and str(ids.get(key)) != lit.text:
                    lit.problem = f"{key} is {ids.get(key)!r} on this dataset, the text shows {lit.text!r}"
            continue

        if lit.kind == "date":
            y, mon, day = date_parts(lit)
            if y is not None and not (lo <= y <= hi):
                hit = next((e for e in d_file if _covers(e["rx"], t, lit)), None)
                lit.cls, lit.rule = (hit.get("class", "real"), hit.get("why", "")) if hit else ("real", "outside the window")
                continue
            hit = next((e for e in d_file if _covers(e["rx"], t, lit)), None)
            if hit is not None:
                lit.cls = "key" if hit.get("key") else hit.get("class", "shift")
                lit.rule, lit.key = hit.get("why", ""), hit.get("key")
                if lit.cls == "key" and ids is not None:
                    _check_date_key(lit, ids)
                continue
            key = d_keys.get(f"{y:04d}-{mon:02d}-{day:02d}") if y is not None else None
            if key is not None:
                lit.cls, lit.key = "key", key
                if ids is not None:
                    _check_date_key(lit, ids)
                continue
            if day == 1 or is_month_end(y, mon, day):
                lit.cls, lit.rule = ("structural" if y is not None else "constant"), "first or last day of a month"
                continue
            lit.problem = "date with no key in dates.yml and no per-file decision"
            continue

        # a year
        code = is_code(rel) or any(a <= lit.start < b for a, b in fences)
        if lit.year in set(years.get("account_numbers") or []) and any(
                _covers(rx, t, lit, window=80) for rx in years.get("account_context") or []):
            lit.cls, lit.rule = "constant", "account number"
            continue
        hit = next((e for e in allow_y if _covers(e["rx"], t, lit)), None)
        if hit is not None:
            lit.cls, lit.rule = hit.get("class", "real"), hit.get("why", "per-file decision")
            continue
        real = next((r for r in years.get("real") or [] if _covers(r["rx"], t, lit)), None)
        if real is None and is_citation(t, lit, rs):
            real = {"name": "citation"}
        role = next((r for r in years.get("role") or [] if (not r.get("code") or code) and not
                     (r.get("prose") and code) and _covers(r["rx"], t, lit)), None)
        suspect = next((s for s in years.get("suspect") or [] if (not s.get("code") or code) and
                        _near(s["rx"], t, lit, s.get("window", 80))), None)
        if real is not None and role is not None and real.get("weak"):
            lit.problem = f"ambiguous: real-world ({real['name']}) and role ({role['name']}); decide in years.yml files"
        elif real is not None:
            lit.cls, lit.rule = "real", real["name"]
        elif role is not None and suspect is not None and not role.get("strong"):
            lit.problem = f"ambiguous: role ({role['name']}) near real-world words ({suspect['name']}); decide in years.yml files"
        elif role is not None:
            lit.cls, lit.rule = role.get("class", "role"), role["name"]
        else:
            lit.problem = "year in no known context"
    return lits


def _check_date_key(lit: Lit, ids: dict) -> None:
    v = ids.get(lit.key)
    if v is None:
        lit.problem = f"{lit.key} has no value on this dataset"
        return
    shown = render_date(str(v), lit.shape, lit.text)
    if shown != lit.text:
        lit.problem = f"{lit.key} is {v} on this dataset, which shows {shown!r}; the text shows {lit.text!r}"
