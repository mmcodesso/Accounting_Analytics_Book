"""The exact values the visible text shows, and the lint that finds the ones not yet classified.

Phase 7 of the companion-files and yearly-roll program keeps readable literals in the source and rewrites them at each
roll (facts/roll_text.py). This module owns the exact values, with facts/visible_values_data.py (the queries) and
facts/literals/values.yml (the classification; hand-written parts in facts/literals/_parts/):

- values(d) -> {"val.<name>": value}: every data value the text and the code that mirrors it show, computed read-only from
  the dataset through facts/db.Data's window (F, P, C, N), reusing the context functions of the generated notes
  (facts/notes/*.py) wherever a note already computes the value, so a roll recomputes it. A group of values that cannot
  be computed on a dataset leaves its keys out and records why in visible_values_data.ERRORS.
- display(value, fmt) -> str, parse_literal(literal) -> (value, Fmt), infer_format(literal) -> fmt: a value written in a
  literal's display format ("$,.2" dollars; ".2%" a fraction as a percentage; ".1M"; "+ ,.2" signed; "abs ,.2"; "~10 $.0"
  about; "floor100000 ,.0" more than; "zero6 .0" zero-padded; ".0p" a percentage number without the sign). The format
  is inferred from the literal, so values.yml states one only where the inference is not enough.
- classify(path, text=None) -> [Occurrence]: every numeric literal of a file in scope with its class: "key" (a value the
  roll rewrites: Occurrence.key and .fmt), "constant" (a teaching constant, threshold or real-world figure that a roll
  keeps), "computed" (code that computes it), "review" (it may change with a roll and has no key: the impact report lists
  it, Occurrence.note says what to check), or "structural:<rule>" (a reference such as Tutorial 4.1, a list number, a slide
  timing, a multiple-choice key, an account number, a cell reference, a tolerance, a year: years belong to the rules of
  facts/literals/years.yml). Offsets (start, end) address the text as read with newline="" (CRLF kept).
- edits(path, values, text=None) -> (edits, problems): the replacements a roll makes in a file for the keys it uses
  (a list of (start, end, new literal), from the end of the file to its start) and the occurrences whose key has no
  value in `values` (pass the merged registry of facts/visible.py, which includes the id.* keys that some literals use).
- unclassified(path, text=None) -> [dict]: the literals that no structural rule and no values.yml entry covers (the hook
  of `python scripts/facts.py lint`).
- roll_classification(old_values, new_values) -> (yml text, problems): values.yml after a roll, the literals of the keyed
  entries following the rewritten text (entries are found by their literal, so a second roll needs it).
- roll_classification(old_values, new_values) -> (yml text, problems): values.yml after a roll. Entries are found by
  their literal, so the literals of the keyed entries must follow the rewritten text before the next lint or roll.
- check(d=None) -> [str]: every keyed literal whose key, written in its format, differs from what the text shows (empty on
  the edition's dataset; a literal that is wrong in the text is classified "review" instead of keyed).
- scope_files(code=True): the files in scope (the book's .qmd files and shared/fragments, the slides decks, and the code
  that mirrors the text); generated regions and files (shared/generated, slides/_shared) are never in scope.

What counts as an exact value. A numeric literal written with digits in a file in scope, outside what agent A's registry
classifies: years (any bare 1900-2099 number), ISO and spelled dates, clock times, year-quarters and year-months, and
document numbers (SI-2025-007947). Item codes (FUR-DSK-0075), check numbers and fixed-asset tags are found here and
classified through id.* keys. In Python files only the literals that can mirror the text are scanned: numbers in assert
statements and in assignments to UPPER_CASE constants (other than 0, 1, tolerances and subscripts), and value-shaped
text inside string literals. Spelled-out
numbers ("three cutoff invoices") and names (customers, items) are not numeric literals; the notes' claims and the impact
review cover them.

    python facts/visible_values.py check            # every key against today's text (exit 1 on a mismatch)
    python facts/visible_values.py lint [FILES]      # unclassified literals (exit 1 if any)
    python facts/visible_values.py report [--out F]  # counts by file and class, and the review list
    python facts/visible_values.py dump --out F      # every occurrence as JSON
"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
VALUES_YML = HERE / "literals" / "values.yml"

# --- scope -------------------------------------------------------------------------------------

BOOK_DIRS = ["front-matter", "chapters", "cases", "appendices", "back-matter", "shared/fragments"]
CODE_GLOBS = ["shared/calculations/*.py", "scripts/figures/*.py", "scripts/companion/xlbuild/*.py",
              "scripts/companion/pbibuild/*.py", "scripts/companion/sqlbuild/*.py", "facts/notes/*.py",
              "facts/notes/templates/**/*.md"]


def excluded(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return name in ("_references.qmd", "_further-reading.qmd") or name.startswith("_reference-")


def scope_files(code: bool = True) -> list[Path]:
    """Every file in scope: the book, the slide decks, and (with code) the code that mirrors the text."""
    out = [REPO / "index.qmd"]
    for d in BOOK_DIRS:
        out += sorted((REPO / d).rglob("*.qmd"))
    out += sorted(REPO.glob("slides/chapter-*/index.qmd"))
    if code:
        for g in CODE_GLOBS:
            out += sorted(REPO.glob(g))
    return [p for p in out if p.is_file() and not excluded(rel_path(p))]


def rel_path(path: Path | str) -> str:
    p = Path(path)
    try:
        p = p.resolve().relative_to(REPO)
    except ValueError:
        pass
    return str(p).replace("\\", "/")


# --- display formats ---------------------------------------------------------------------------
#
# A format says how a literal writes its number. It is the body, optionally preceded by flags,
# separated by spaces ("abs $,.2", "+ ,.2", "~10 $.0", ".1 percent").
#
# The body: "$" (a dollar sign after any sign: −$3.5), "," or "_" (thousands separators, "_" as Python
# writes 380_000), ".N" (N decimals; required), then the unit: "%" (a fraction shown as a percentage,
# 0.4749 -> 47.49%), "M" or "K" (millions or thousands, 29.8M), "x" (a trailing ×, 2.33×), or "e" (C's
# %e, 6.884200e+02), "p" (a fraction shown as a percentage number without the sign: 8 in "8, 10, and 12 percent"). A unit in words follows the body after a space: " percent", " million",
# " billion" (31 percent, $100 million).
#
# The flags: "abs" (the absolute value; the text states the direction in words), "()" (a negative
# value in parentheses), "+" (always signed), "-" (a hyphen as the minus sign; the default is U+2212,
# as the book writes it), "~N" (round to the nearest multiple of N in the displayed unit, for "about"
# values: ~10 shows 152.20 as 150), "floorN" and "ceilN" (round down or up to a multiple of N: "more
# than 800,000 rows" is floor100000).
#
# Numbers round half away from zero on 15 significant digits, as Excel and the notes show them
# (facts/notes/__init__.py). infer_format(literal) gives the format a literal is written in;
# values.yml states a format only where the inference is not enough.

MINUS = "−"
UNITS = {"": 1, "%": 100, " percent": 100, "M": 1e-6, "K": 1e-3, " million": 1e-6, " billion": 1e-9,
         "x": 1, "e": 1, "p": 100}


@dataclass(frozen=True)
class Fmt:
    dollar: bool = False
    sep: str = ""           # "", ",", "_"
    places: int = 0
    unit: str = ""
    plus: bool = False
    minus: str = MINUS
    parens: bool = False
    absolute: bool = False
    step: float | None = None
    mode: str = ""          # "" (half away from zero), "~", "floor", "ceil"
    pad: int = 0            # zero-pad the integer part to this width (007947)

    def spec(self) -> str:
        flags = []
        if self.absolute:
            flags.append("abs")
        if self.parens:
            flags.append("()")
        if self.plus:
            flags.append("+")
        if self.minus != MINUS:
            flags.append(self.minus)
        if self.step is not None:
            flags.append(f"{self.mode}{self.step:g}")
        if self.pad:
            flags.append(f"zero{self.pad}")
        word = self.unit if self.unit.startswith(" ") else ""
        body = ("$" if self.dollar else "") + self.sep + f".{self.places}" + ("" if word else self.unit)
        return " ".join(flags + [body]) + word


BODY = re.compile(r"(?P<dollar>\$)?(?P<sep>[,_])?\.(?P<places>\d+)(?P<unit>%|M|K|x|e|p)?")


def parse_format(fmt: str) -> Fmt:
    tokens = fmt.strip().split(" ")
    kw: dict[str, Any] = {}
    if tokens[-1] in ("percent", "million", "billion"):
        kw["unit"] = " " + tokens.pop()
    m = BODY.fullmatch(tokens.pop()) if tokens else None
    if not m:
        raise ValueError(f"bad format {fmt!r}")
    kw.update(dollar=bool(m.group("dollar")), sep=m.group("sep") or "", places=int(m.group("places")))
    if m.group("unit"):
        if "unit" in kw:
            raise ValueError(f"two units in {fmt!r}")
        kw["unit"] = m.group("unit")
    for flag in tokens:
        if flag == "abs":
            kw["absolute"] = True
        elif flag == "()":
            kw["parens"] = True
        elif flag == "+":
            kw["plus"] = True
        elif flag in ("-", MINUS):
            kw["minus"] = flag
        elif re.fullmatch(r"zero\d+", flag):
            kw["pad"] = int(flag[4:])
        elif re.fullmatch(r"(~|floor|ceil)\d+(?:\.\d+)?", flag):
            mode = re.match(r"~|floor|ceil", flag).group(0)
            kw["mode"], kw["step"] = mode, float(flag[len(mode):])
        else:
            raise ValueError(f"unknown flag {flag!r} in format {fmt!r}")
    return Fmt(**kw)


def _decimal(x: float) -> Decimal:
    return Decimal(repr(float(f"{x:.15g}")))


def _round(x: float, f: Fmt) -> Decimal:
    q = Decimal(1).scaleb(-f.places)
    v = _decimal(x)
    if f.step is not None:
        step = _decimal(f.step)
        how = {"~": ROUND_HALF_UP, "floor": ROUND_FLOOR, "ceil": ROUND_CEILING}[f.mode]
        v = (v / step).quantize(Decimal(1), rounding=how) * step
    return v.quantize(q, rounding=ROUND_HALF_UP)


def display(value: float | int | str, fmt: str | Fmt) -> str:
    """The value written in the format `fmt` (a string value is shown as it is)."""
    if isinstance(value, str):
        return value
    f = parse_format(fmt) if isinstance(fmt, str) else fmt
    if f.unit == "e":
        x = abs(float(value)) if f.absolute else float(value)
        return f"{x:.{f.places}e}"
    x = float(value) * UNITS[f.unit]
    if f.absolute:
        x = abs(x)
    q = _round(x, f)
    neg = q < 0
    digits = f"{abs(q):{',' if f.sep else ''}.{f.places}f}"
    if f.pad:
        head, _, tail = digits.partition(".")
        digits = head.zfill(f.pad) + ("." + tail if tail else "")
    if f.sep == "_":
        digits = digits.replace(",", "_")
    unit = {"x": "×", "p": ""}.get(f.unit, f.unit)
    core = ("$" if f.dollar else "") + digits + unit
    if neg:
        return f"({core})" if f.parens else f.minus + core
    if f.plus and q != 0:
        return "+" + core
    return core


LIT = re.compile(r"""^(?P<open>\()?(?P<sign>[+−-])?(?P<dollar>\$)?(?P<sign2>[−-])?
                     (?P<digits>\d{1,3}(?:[,_]\d{3})+|\d+)(?:\.(?P<dec>\d+))?
                     (?P<unit>%|\s?[MK]|\s(?:percent|million|billion)|×|e[+-]\d{2})?(?P<close>\))?$""", re.X)


def parse_literal(literal: str) -> tuple[float, Fmt] | None:
    """The number a literal shows and the format it is written in (None if it is not a number)."""
    m = LIT.match(literal.strip())
    if not m:
        return None
    parens = bool(m.group("open") and m.group("close"))
    if bool(m.group("open")) != bool(m.group("close")):
        return None
    sign = m.group("sign") or m.group("sign2") or ""
    unit = (m.group("unit") or "").strip()
    if unit in ("percent", "million", "billion"):
        unit = " " + unit
    elif unit == "×":
        unit = "x"
    elif unit.startswith("e"):
        x = float(literal.strip().lstrip("(").rstrip(")").replace("−", "-"))
        return x, Fmt(places=len(m.group("dec") or ""), unit="e")
    dec = m.group("dec") or ""
    digits = m.group("digits")
    x = float(digits.replace(",", "").replace("_", "") + ("." + dec if dec else "")) / UNITS[unit]
    if sign in ("−", "-") or parens:
        x = -x
    sep = "," if "," in digits else "_" if "_" in digits else ""
    f = Fmt(dollar=bool(m.group("dollar")), sep=sep, places=len(dec), unit=unit, plus=sign == "+",
            minus=sign if sign in ("−", "-") else MINUS, parens=parens, pad=(len(digits) if (len(digits) > 1 and digits[0] == "0" and not dec and not sep) else 0))
    return x, f


def infer_format(literal: str) -> str:
    p = parse_literal(literal)
    if p is None:
        raise ValueError(f"not a number: {literal!r}")
    return p[1].spec()


# --- finding literals in the text --------------------------------------------------------------

def _blank(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?"

# Masked before the search: these belong to agent A's registry (dates, document numbers) or are not text.
MASKS = [
    re.compile(r"<!-- notes: [\w.-]+ -->\r?\n<!--.*?-->", re.S),             # generated notes
    re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.S),                         # YAML front matter
    re.compile(r"\{\{<.*?>\}\}", re.S),                                       # shortcodes
    re.compile(r"\b(?:CC )?BY-SA \d\.\d|\bShareAlike \d\.\d"),                  # the license
    re.compile(r"https?://[^\s)>\]\"'`]+"),                                   # URLs
    re.compile(r"\]\([^)\s]*\)"),                                             # link targets
    re.compile(r"[#@](?:fig|tbl|sec|eq|lst)-[\w-]+"),                        # cross-reference ids
    re.compile(r"(?<=[\s(])/(?:visuals|downloads|chapters)/\S+"),            # asset paths
    re.compile(r"\{[.#][^}\n]*?(?=fig-alt=|\})"),                             # attribute blocks (fig-alt text is kept)
    re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?"),        # ISO dates and timestamps
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b(?:\s?[AP]M)?"),                 # clock times
    re.compile(r"\b(?:19|20)\d{2}-(?:Q[1-4]|\d{2})\b"),                       # year-quarters, year-months
    re.compile(r"\b(?:19|20)\d{2}\s?Q[1-4]\b|\bQ[1-4]\s(?:19|20)\d{2}\b|\bQ[1-4]\b|\bH[12]\b"),
    re.compile(r"\b" + MONTHS + r"\s\d{1,2}(?:st|nd|rd|th)?(?:,?\s(?:19|20)\d{2})?\b"),   # January 1, 2024
    re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s" + MONTHS + r"(?:\s(?:19|20)\d{2})?\b"),      # 1 January 2024
    re.compile(r"\b\d{1,2}(?:–|-)\d{1,2}\s" + MONTHS + r"(?:\s(?:19|20)\d{2})?\b"),        # 14-31 December 2026
    re.compile(r"\b[A-Za-z]*[A-Z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+\b"),        # codes and document numbers
    re.compile(r"\b[A-Z][A-Za-z]*\d+[A-Za-z0-9]*\b"),                         # CHK0006076, H1, Q4, B3, R2_2025
    re.compile(r"\b[A-Z]{1,3}\d+:[A-Z]{1,3}\d+\b|\b[A-Z]{1,3}:[A-Z]{1,3}\b"), # cell ranges
    re.compile(r"\$[A-Z]{1,3}\$?\d+"),                                         # absolute cell references $C$500
    re.compile(r"\b\d+(?:\.\d+)+\.\d+\b"),                                     # versions 3.13.1, 2.158.1177.0
    re.compile(r"\b\d+(?:px|pt|ms|em|rem|KB|MB|GB|kB|dpi|x\d+)\b"),           # units of layout and size
    re.compile(r"\b\d+\s?(?:px|pt|KB|MB|GB)\b"),
    re.compile(r"(?<![\w.])\d+(?:st|nd|rd|th)\b"),                            # ordinals
    re.compile(r"\b(?:Microsoft|Office) 365\b|\bWindows 1[01]\b|\b(?:SUBTOTAL|AGGREGATE)\(\d+"),   # products, function numbers
    re.compile(r"\bwidth=\"?\d+%\"?|\bheight=\"?\d+%\"?"),                    # layout attributes
    re.compile(r"\b(?:BY-SA|ShareAlike|BY) \d\.\d\b"),                         # the license
    re.compile(r"\*\d+\*(?:\(\d+\))?|\b\d+\(\d+\),? ?\d+[–-]\d+|, \d+[–-]\d+\.|\bArticle \d+|\bpp?\. \d+(?:[–-]\d+)?"),  # citations
    re.compile(r"\bDATE ?\( ?(?:19|20)\d{2}, ?\d{1,2}, ?\d{1,2} ?\)"),        # DAX and Excel DATE(y, m, d)
    re.compile(r"\b\d\.\d{6}e[+-]\d{2}\b"),                                    # scientific notation (found as CODE)
]

# A single digit counts data, and must be classified, when an ID word precedes it (Register 2,
# employee 5, AccountID 3) or a data noun follows it (6 rows); other single digits are structural.
ID_WORD = re.compile(r"(?:\b[A-Z][A-Za-z]*ID|\b[Rr]egisters?|\b[Ee]mployees?|\b[Cc]ustomers?|\b[Ss]uppliers?|"
                     r"\b[Pp]romotions?|\b[Ii]tems?|\b[Cc]ost centers?|\b[Ww]ork centers?|\b[Pp]eriods?|"
                     r"\b[Pp]rice lists?|\b[Ll]ists?|\b[Oo]rders?|\b[Ii]nvoices?|\b[Pp]ayments?|\b[Ee]ntry)"
                     r"\s?(?:\(|=\s?|`)?$")

def _ref_numbers(word_rx: str) -> re.Pattern:
    item = r"\d+(?:\.\d+)*[a-z]?"
    return re.compile(r"\b(?:" + word_rx + r")\.?\s?=?\s?(?P<nums>" + item +
                      r"(?:(?:\s?(?:,|–|-|/)\s?|,?\s(?:and|or|to|through|&)\s)" + item + r")*)")


# references whose numbers are structural (they number the book itself)
STRUCT_REF = _ref_numbers(r"Guided Tutorials?|Tutorials?|Exercises?|Ex|Figures?|Tables?|Steps?|Chapters?|Parts?|"
                          r"Requirements?|Milestones?|Questions?|Sections?|Phases?|Appendix|Levels?|Versions?|versions?|"
                          r"Desktop|SQLite|Python|Quarto|Draw\.io|Windows|BY-SA|Attribution-ShareAlike|APA|[Rr]eleases?|"
                          r"[Ee]ditions?|Topics?|ASC|AS|ISO|UTF-?|Office|pandas|numpy|Faker|PyYAML|openpyxl|"
                          r"XlsxWriter|Lua|Pandoc|TinyTeX|Modules?|[Ss]lides?|[Ss]tages?|Exhibits?|Deliverables?|"
                          r"IES|SAS|AU-C|AU|SSAE|ASU|No\.|Vol\.|vol\.|pp?\.|chapters?|steps?|parts?|requirements?|"
                          r"milestones?|questions?|exercises?|tutorials?|figures?|tables?|[Mm]odule|Test|Tests|test|"
                          r"tests|Rule|rules?|Case|Check|Checks|Scenario|Option|Options|Criterion|Query|[Ll]ine numbers?|"
                          r"At line|at line|lines? of the script|[Cc]olumns?|[Pp]ages?|[Pp]ositions?|"
                          r"[Dd]igits?|[Dd]ecimals?|[Dd]ecimal places|places|IFS|level|[Ss]ection|Opus|GTAG|Volume|"
                          r"[Ff]unction numbers?|[Ff]unction|[Ss]ource|[Ll]ayer|[Ww]eek|Release|Exam|edition|"
                          r"[Ss]ize|[Ff]ont|zoom|Zoom|[Dd]PI|[Tt]ier|Phase|Milestone|Requirement|deck|Deck|Shift|"
                          r"[Ss]lide|Stage|[Hh]eading|[Hh]eader row|[Aa]pproach|[Pp]erspective|Table tab")

LIST_PREFIX = re.compile(r"\d+(?:\.\d+)?(?:,\s|,?\s(?:and|or|to)\s|\s?[–-]\s?)$")
TIMING = re.compile(r"(?:\b(?:Allow|allow|Timing:?|timing:?|Spend|spend|Take|take|takes|lasts?|about|approximately|"
                    r"[Uu]p to|[Rr]oughly|for|Total|total)\s(?:about\s|approximately\s)?)"
                    r"(?P<nums>\d+(?:\s?(?:–|-|to)\s?\d+)?)(?=\s(?:seconds|minutes|secs?|mins?|hours? of class|"
                    r"-minute|-second))|(?P<nums2>\d+(?:\s?(?:–|-)\s?\d+)?)(?=[\s-](?:seconds|minutes|secs?|mins?)\b)")
MCQ_KEY = re.compile(r"(?<![\w.,])(?P<nums>\d{1,2})(?=\s?[A-D](?:[,.:;)]|\s|$))")
ENUM = re.compile(r"(?<![\w.])(?P<nums>\((?:\d{1,2}|[ivx]+)\))(?=\s|$|[,.;:])")
LISTMARK = re.compile(r"(?m)^(?P<lead>[ \t>]*(?:[-*+]\s+)?(?:\*\*)?)(?P<nums>\d{1,3})(?=[.)](?:\*\*)?(?:\s|$))")
BOLDNUM = re.compile(r"\*\*(?P<nums>\d{1,3})[.)]\*\*")
TABLE_ROWNUM = re.compile(r"(?m)^\|\s*(?P<nums>\d{1,2})\s*\|")
ACCOUNT_CTX = re.compile(r"(?i)\baccount(?:s|number)?\b|\bto\b|\bfrom\b|\band\b|\bor\b|\bon\b|[,(|=]\s*$")

NUM = re.compile(r"""(?<![\w.,/\\$−+-])
    (?P<lit>
      \(?[−+-]?\$?[−-]?
      (?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?
      \)?
      (?:%|\s?[MK](?![\w])|\s(?:percent|million|billion)\b|×)?
    )
    (?![\w]|\.\d|,\d{3}|\$)""", re.X)

DATA_NOUN = re.compile(r"^\s?(?:of\s(?:the|them|its)\s)?(?:\w+[\s-]){0,3}?(?:lines?|invoices?|entries|entry|rows?|"
                       r"payments?|days?|employees?|customers?|suppliers?|accounts?|orders?|closes?|registers?|"
                       r"requisitions?|items?|promotions?|exceptions?|documents?|receipts?|credits?|refunds?|"
                       r"returns?|shipments?|work orders?|records?|pairs?|checks?|numbers?|postings?|months?|"
                       r"operations?|users?|managers?|tests?|flags?|weekends?|approvals?|people|hours?|"
                       r"periods?|years?|quarters?|weeks?|pages?|POs?)\b", re.I)


@dataclass
class Occurrence:
    file: str
    line: int
    start: int
    end: int
    literal: str
    context: str
    kind: str = "prose"           # prose | code
    origin: str = ""              # Python files: assert | constant (an UPPER_CASE assignment) | string
    nth: int = 0                  # the position among the same literal on its line (1-based; set by classify)
    spec: dict | None = None      # the spec that classified it
    entry: tuple | None = None    # where the classification came from: ("files", path, literal) | ("rules", name, literal) | ("everywhere", "", literal)
    cls: str = ""                 # "key", "constant", or "structural:<rule>"
    key: str | None = None
    fmt: str | None = None
    note: str = ""

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("file", "line", "literal", "context", "kind", "origin", "cls", "key", "fmt", "note")}


def _mask(text: str) -> str:
    t = text
    for rx in MASKS:
        t = rx.sub(lambda m: _blank(m.group(0)), t)
    return t.replace("\\$", " $")          # a dollar sign escaped for Markdown (same length)


def _struct_spans(t: str) -> list[tuple[int, int, str]]:
    spans = []
    for rx, name in ((STRUCT_REF, "reference"), (TIMING, "timing"), (ENUM, "enumerator"),
                     (LISTMARK, "list"), (BOLDNUM, "list"), (TABLE_ROWNUM, "list")):
        for m in rx.finditer(t):
            for g in ("nums", "nums2"):
                if g in rx.groupindex and m.group(g):
                    spans.append((m.start(g), m.end(g), name))
    return spans


def _mcq_key_spans(t: str) -> list[tuple[int, int, str]]:
    """The question numbers of an answer key ("1 D, 2 A, ..." or "6 D: the extract ...")."""
    spans = []
    for m in re.finditer(r"<!--\s*Answer key.*?-->", t, re.S):
        for k in MCQ_KEY.finditer(m.group(0)):
            spans.append((m.start() + k.start("nums"), m.start() + k.end("nums"), "mcq-key"))
    return spans


def _in(spans, a, b):
    for s, e, name in spans:
        if s <= a and b <= e:
            return name
    return None


def _code_spans(text: str) -> list[tuple[int, int]]:
    spans = [(m.start(), m.end()) for m in re.finditer(r"(?ms)^(`{3,}|~{3,}).*?^\1\s*$", text)]
    spans += [(m.start(), m.end()) for m in re.finditer(r"`[^`\n]+`", text)]
    return spans


ACCOUNTS: set[int] | None = None


def _accounts() -> set[int]:
    global ACCOUNTS
    if ACCOUNTS is None:
        try:
            sys.path.insert(0, str(HERE))
            from db import Data  # noqa: E402
            d = Data()
            ACCOUNTS = {int(r[0]) for r in d.q("SELECT AccountNumber FROM Account")}
        except Exception:
            ACCOUNTS = set(range(1000, 9000, 10))
    return ACCOUNTS


def _structural_number(lit: str, t: str, a: int, b: int, in_code: bool) -> str | None:
    """A rule that makes a bare number structural, or None."""
    if not re.fullmatch(r"\d+", lit):
        return None
    v = int(lit)
    if len(lit) == 4 and v in _accounts():
        return "account"
    if len(lit) == 4 and 1900 <= v <= 2099:
        return "year"                                  # agent A's registry
    if v < 10:
        pre = t[max(0, a - 70):a]
        for _ in range(8):                             # a list of IDs: "promotions 7, 8, and 9"
            m = LIST_PREFIX.search(pre)
            if not m:
                break
            pre = pre[:m.start()]
        if ID_WORD.search(pre[-40:]):
            return None                                # an ID: Register 2, AccountID 3
        if not in_code and DATA_NOUN.match(t[b:b + 40]):
            return None                                # a count of data: 6 rows
        if re.match(r"[^.;\n]{0,25}(?:percent|%)", t[b:b + 40]):
            return None                                # a rate in a list: 8, 10, and 12 percent
        return "small"                                 # a single digit that does not count data
    return None


def _year_like(lit: str) -> bool:
    core = lit.strip("()").rstrip("%")
    return bool(re.fullmatch(r"(?:19|20)\d{2}", core))


def find_qmd(path: str, text: str) -> list[Occurrence]:
    t = _mask(text)
    spans = _struct_spans(t) + _mcq_key_spans(t)
    code = _code_spans(text)
    out = []
    for m in NUM.finditer(t):
        lit = m.group("lit")
        a, b = m.start("lit"), m.end("lit")
        # trim punctuation parentheses that are not a negative amount
        if lit.startswith("(") and not lit.endswith(")"):
            lit, a = lit[1:], a + 1
        elif lit.endswith(")") and not lit.startswith("("):
            lit, b = lit[:-1], b - 1
        elif lit.startswith("(") and re.fullmatch(r"\(\d+%?\)", lit) and not ENUM.fullmatch(lit):
            lit, a, b = lit[1:-1], a + 1, b - 1        # a number in parentheses, not a negative amount
        if not re.search(r"\d", lit):
            continue
        line = text.count("\n", 0, a) + 1
        ctx = text[max(0, a - 70): b + 50].replace("\r", "").replace("\n", " ")
        in_code = any(s <= a < e for s, e in code)
        occ = Occurrence(rel_path(path), line, a, b, lit, ctx, "code" if in_code else "prose")
        rule = _in(spans, a, b)
        if rule is None and _year_like(lit):
            rule = "year"
        if rule is None:
            rule = _structural_number(lit, t, a, b, in_code)
        if rule:
            occ.cls = "structural:" + rule
        out.append(occ)
    notes = [n.span() for n in MASKS[0].finditer(text)]
    for m in CODE.finditer(text):
        if any(x <= m.start() < y for x, y in notes):
            continue
        a, b = m.span()
        out.append(Occurrence(rel_path(path), text.count("\n", 0, a) + 1, a, b, m.group(0),
                              text[max(0, a - 70): b + 50].replace("\r", "").replace("\n", " "),
                              "code" if any(s <= a < e for s, e in code) else "prose"))
    return sorted(out, key=lambda o: o.start)


# Codes without a year (agent A's registry takes the document numbers that carry one): item codes,
# check numbers, and fixed-asset tags. A roll keeps the catalog, but a code chosen by its role (the
# traced item, the largest line) is a key.
CODE = re.compile(r"(?<![\w-])(?:[A-Z]{3}-[A-Z]{3}-\d{4}|CHK\d{7}|MFG-\d{4}|\d\.\d{6}e[+-]\d{2})(?![\w-])")


VALUE_IN_STRING = re.compile(r"""(?<![\w.,$])(?P<lit>[−+-]?\$?[−-]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+)
                                 (?:%|[MK](?![\w])|\s(?:percent|million))?)(?![\w]|\.\d|,\d{3})""", re.X)


NUMBER_FORMAT = re.compile(r"""[\s#0.,%$;()\[\]<>=E+\-"a-zA-Z_\/?*@]*[0#][\s#0.,%$;()\[\]<>=E+\-"a-zA-Z_\/?*@]*""")
CELL_DOLLAR = re.compile(r"(?:[A-Z}{]|\$)\$?$")

MODULE_CHAPTERS = {"analysis": range(4, 8), "audit": [8], "case2": range(4, 9), "case3": range(9, 13),
                   "case4": range(13, 17), "reports": range(13, 16), "audit_monitoring": [16], "excel_analysis": range(4, 8),
                   "chapter01": [1], "foundations": [2, 3], "invoice_margin": [1, 2, 3, 6], "expected": range(4, 9),
                   "notes": range(4, 20), "solutions": range(4, 20), "exb": [], "appendix_b": []}


def module_chapters(path: str) -> set[int]:
    stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    m = re.search(r"(\d{1,2})$", stem.replace("_monitoring", ""))
    if stem in MODULE_CHAPTERS:
        return set(MODULE_CHAPTERS[stem])
    return {int(m.group(1))} if m else set()


def _code_structural(s: str, a: int, b: int, lit: str, chapters: set[int]) -> str:
    """A rule that makes a literal inside a code string structural, or ''."""
    before = s[max(0, a - 3): a]
    if lit.startswith("$") and re.fullmatch(r"\$\d+", lit) and re.search(r"[A-Z}{]\$?$|\$$", s[:a]):
        return "structural:cell"                          # $B$4, {c}$3
    if re.fullmatch(r"\$\d+", lit) and re.match(r"[:,)]", s[b:b + 1] or " "):
        return "structural:cell"
    m = re.fullmatch(r"(\d{1,2})\.(\d)", lit)
    if m and int(m.group(1)) in chapters and m.group(2) != "0":
        return "structural:reference"                     # Ex 7.4, Exercise 16.2, Tutorial 4.3
    try:
        v = abs(float(re.sub(r"[^\d.]", "", lit) or "nan"))
    except ValueError:
        v = None
    if v is not None and "." in lit and v <= 0.011 and not lit.endswith("%"):
        return "structural:tolerance"                     # 0.005, 0.0001, 1e-6 written out
    return ""


REGISTRY_NAMES = {"FIGURES", "CHAPTERS", "APPENDICES", "TUTORIALS", "EXERCISES", "QUERIES"}   # tables of functions and chapter numbers


def _is_index(tokens, i: int) -> bool:
    """Is the number token a subscript (rows[2], x[-1]) or a slice bound: the token before is '[' (or '[-') after a
    name, ')' or ']', or a ':' inside brackets?"""
    j = i - 1
    if j >= 0 and tokens[j].string == "-":
        j -= 1
    if j >= 0 and tokens[j].string in ("[", ":"):
        if tokens[j].string == ":":
            return True
        k = j - 1
        return k >= 0 and (tokens[k].type == tokenize.NAME or tokens[k].string in (")", "]"))
    return False


def find_py(path: str, text: str) -> list[Occurrence]:
    """Python: numbers in assert statements, and value-shaped text in string literals."""
    out = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return out
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln))

    def pos(row, col):
        return offsets[row - 1] + col

    in_assert, origin = False, ""
    chapters = module_chapters(rel_path(path))
    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME and tok.string == "assert" and (i == 0 or tokens[i - 1].type in (
                tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT)):
            in_assert, origin = True, "assert"
        elif (tok.type == tokenize.NAME and tok.string.isupper() and len(tok.string) >= 4 and tok.string not in REGISTRY_NAMES
              and i + 1 < len(tokens) and tokens[i + 1].string in ("=", ":")
              and (i == 0 or tokens[i - 1].type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT,
                                                    tokenize.COMMENT))):
            in_assert, origin = True, "constant"    # NAME = ...: a constant that may mirror the text
        elif tok.type == tokenize.NEWLINE:
            in_assert = False
        a, b = pos(*tok.start), pos(*tok.end)
        ctx = text[max(0, a - 70): b + 50].replace("\n", " ")
        if tok.type == tokenize.NUMBER and in_assert:
            lit = tok.string
            occ = Occurrence(rel_path(path), tok.start[0], a, b, lit, ctx, "code", origin=origin)
            prev = tokens[i - 1].string if i else ""
            if prev == "-" and i > 1:
                pass
            try:
                v = float(lit.replace("_", ""))
            except ValueError:
                v = None
            if lit.lower().startswith("0x"):
                occ.cls = "structural:color"         # a hexadecimal color or constant
            elif v is not None and (v in (0, 1, -1) or (abs(v) <= 0.011 and "." in lit) or "e" in lit.lower()):
                occ.cls = "structural:tolerance" if v not in (0, 1) else "structural:small"
            elif _year_like(lit):
                occ.cls = "structural:year"
            elif re.fullmatch(r"\d{4}", lit) and int(lit) in _accounts():
                occ.cls = "structural:account"
            elif re.fullmatch(r"\d", lit) and _is_index(tokens, i):
                occ.cls = "structural:index"          # rows[2], x[-1]: a position, not a value
            out.append(occ)
        elif tok.type == tokenize.STRING or tok.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
            s = tok.string
            is_sql = bool(re.search(r"\b(SELECT|WHERE|HAVING|CASE WHEN|ROUND|JOIN|EVALUATE|CALCULATE|FILTER)\b", s))
            if NUMBER_FORMAT.fullmatch(s.strip("'\"rbfRBF")):
                continue                                  # an Excel or DAX number format such as "0.0%"
            for o in find_qmd(path, s):
                if o.cls:
                    continue
                shaped = bool(re.search(r"\$|\d,\d{3}|%|\d\.\d|[MK]$|percent|million|×", o.literal)) or bool(CODE.fullmatch(o.literal))
                if not shaped and not (is_sql and re.fullmatch(r"\d+", o.literal) and int(o.literal) >= 10):
                    continue
                if s[max(0, o.start - 1): o.start] == "{" or re.match(r"[}:]", s[o.end: o.end + 1] or " "):
                    continue                              # inside an f-string field or a format spec
                sa = a + o.start
                occ = Occurrence(rel_path(path), text.count("\n", 0, sa) + 1, sa, sa + len(o.literal), o.literal,
                                 text[max(0, sa - 70): sa + len(o.literal) + 50].replace("\n", " "), "code", origin="string")
                occ.cls = _code_structural(s, o.start, o.end, o.literal, chapters)
                out.append(occ)
    return out


def find_template(path: str, text: str) -> list[Occurrence]:
    """A note template: the literal text outside Jinja expressions and statements."""
    t = re.sub(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", lambda m: _blank(m.group(0)), text, flags=re.S)
    occs = find_qmd(path, t if not t.startswith("---") else " " + t[1:])
    for o in occs:
        o.kind = "template"
        if not o.cls and text[o.start - 1: o.start] == "}" and re.fullmatch(r"-\d{2}", o.literal):
            o.cls = "structural:date"                     # {{ d.C }}-12-31: the month of a date
        o.context = text[max(0, o.start - 70): o.end + 50].replace("\n", " ")
    return occs


def find(path: Path | str, text: str | None = None) -> list[Occurrence]:
    p = Path(path)
    if text is None:
        with open(p if p.is_absolute() else REPO / p, encoding="utf-8", newline="") as fh:
            text = fh.read()                    # raw text, so offsets address the bytes' characters (CRLF kept)
    rel = rel_path(p)
    if rel.endswith(".py"):
        return find_py(rel, text)
    if rel.startswith("facts/notes/templates/"):
        return find_template(rel, text)
    return find_qmd(rel, text)


# --- the classification (facts/literals/values.yml) --------------------------------------------
#
# values.yml has three sections, consulted in this order for a literal that no structural rule covers:
#
#   files:       path -> {literal as written: spec or [spec, ...]}     (the most specific)
#   rules:       [{name, class|key, files: [globs], literal: regex, context: regex, format}]   (patterns)
#   everywhere:  literal -> spec or [spec, ...]                         (a literal that means one thing anywhere)
#
# A spec is "constant", a key ("val.x" or another registry key such as "id.trace.invoice_id"), or a dict
# {key, format, context, class, note}. `context` is a regular expression searched in the text around the
# literal (70 characters before, 50 after), so one literal can mean two things in one file; a spec with a
# context wins over one without, and a spec with `line` (and `nth`, the position among the same literal on that
# line) pins one occurrence, for a list of values such as [17, 6, 7, 9, 4]. Classes: key (a value the roll rewrites), constant (a teaching constant,
# threshold, or software fact that a roll keeps), computed (code that computes the value from the data, so
# nothing to rewrite).

_YML: dict | None = None
_RULES: list | None = None


def load_yml(force: bool = False, text: str | None = None) -> dict:
    """The classification (cached). `text` loads a classification from a string instead of the file (the rehearsal of a
    roll uses it for the rewritten classification); load_yml(force=True) goes back to the file."""
    global _YML, _RULES
    if _YML is None or force or text is not None:
        import yaml
        if text is not None:
            _YML = yaml.safe_load(text) or {}
        else:
            _YML = yaml.safe_load(VALUES_YML.read_text(encoding="utf-8")) if VALUES_YML.exists() else {}
            _YML = _YML or {}
        _RULES = None
    return _YML


def _norm_spec(e) -> list[dict]:
    if isinstance(e, str):
        if e in ("constant", "computed"):
            return [{"class": e}]
        return [{"key": e}]
    if isinstance(e, dict):
        return [e]
    out: list[dict] = []
    for x in e:
        out += _norm_spec(x)
    return out


def _rules() -> list[dict]:
    global _RULES
    if _RULES is None:
        from fnmatch import fnmatch  # noqa: F401
        _RULES = []
        for r in load_yml().get("rules", []) or []:
            r = dict(r)
            r["_lit"] = re.compile(r.get("literal", ".*"))
            _RULES.append(r)
    return _RULES


def _pick(cands: list[dict], ctx: str, line: int = 0, nth: int = 0, literal: str = "") -> dict | None:
    """The spec for an occurrence: the first whose conditions all hold and that states at least one (`line`, `nth`:
    the position among the same literal on its line, or a `context` regex), else one with no conditions."""
    best = None
    for c in cands:
        if "line" in c and c["line"] != line:
            continue
        if "nth" in c and c["nth"] != nth:
            continue
        rx = c.get("context")
        if rx is not None and not re.search(rx.replace("{lit}", re.escape(literal)), ctx, re.S):
            continue
        if "line" in c or "nth" in c or rx is not None:
            return c
        best = best or c
    return best


def _expand_file_entries(block: dict) -> dict:
    """A file block may list literals under the reserved keys `constants` and `computed` (a list of literals),
    and `review` (a mapping literal -> what to check), besides the literal -> spec entries."""
    out = {k: v for k, v in block.items() if k not in ("constants", "computed", "review")}
    for lit in block.get("constants", []) or []:
        out.setdefault(str(lit), "constant")
    for lit in block.get("computed", []) or []:
        out.setdefault(str(lit), "computed")
    for lit, why in (block.get("review", {}) or {}).items():
        out.setdefault(str(lit), {"class": "review", "note": why})
    return out


def classify(path: Path | str, text: str | None = None) -> list[Occurrence]:
    from fnmatch import fnmatch
    rel = rel_path(path)
    occs = find(path, text)
    yml = load_yml()
    entries = _expand_file_entries((yml.get("files", {}) or {}).get(rel, {}) or {})
    shared = yml.get("everywhere", {}) or {}
    seen: dict = {}
    for o in occs:
        if o.cls.startswith("structural:"):
            continue
        nth = seen[(o.line, o.literal)] = seen.get((o.line, o.literal), 0) + 1
        chosen = entry_spec = None
        o.nth = nth
        if o.literal in entries:
            chosen = entry_spec = _pick(_norm_spec(entries[o.literal]), o.context, o.line, nth, o.literal)
            if chosen is not None:
                o.entry = ("files", rel, o.literal)
        if chosen is None:
            for r in _rules():
                if r.get("files") and not any(fnmatch(rel, g) for g in r["files"]):
                    continue
                if r.get("origin") and r["origin"] != o.origin:
                    continue
                spec = r
                if "map" in r:                       # a rule that maps several literals to their own specs
                    if o.literal not in r["map"]:
                        continue
                    entry_spec = _norm_spec(r["map"][o.literal])[0]
                    spec = {**r, **entry_spec}
                elif not r["_lit"].fullmatch(o.literal):
                    continue
                if r.get("context"):
                    rx = r["context"].replace("{lit}", re.escape(o.literal))
                    if not re.search(rx, o.context, re.S):
                        continue
                chosen = spec
                o.entry = ("rules", r.get("name", ""), o.literal)
                break
        if chosen is None and o.literal in shared:
            chosen = entry_spec = _pick(_norm_spec(shared[o.literal]), o.context, o.line, nth, o.literal)
            if chosen is not None:
                o.entry = ("everywhere", "", o.literal)
        if chosen is None:
            continue
        if "key" in chosen:
            o.cls, o.key = "key", chosen["key"]
            o.fmt = chosen.get("format") or (infer_format(o.literal) if parse_literal(o.literal) else None)
        else:
            o.cls = chosen.get("class", "constant")
        o.spec = entry_spec
        o.note = chosen.get("note", chosen.get("name", ""))
    return occs


def unclassified(path: Path | str, text: str | None = None) -> list[dict]:
    """The literals in a file that no structural rule and no values.yml entry covers (the hook of
    `python scripts/facts.py lint`)."""
    return [o.as_dict() for o in classify(path, text) if not o.cls]


def edits(path: Path | str, values_: dict, text: str | None = None) -> tuple[list[tuple[int, int, str]], list[str]]:
    """The replacements a roll makes in one file, for the keyed literals: (start, end, new literal) from the end of the
    file to its start (apply them in order), and the problems (an occurrence whose key has no value in `values_`)."""
    out: list[tuple[int, int, str]] = []
    problems: list[str] = []
    for o in classify(path, text):
        if o.cls != "key":
            continue
        if o.key not in values_ or values_[o.key] is None:
            problems.append(f"{o.file}:{o.line}: {o.literal!r} -> {o.key}: no value on this dataset")
            continue
        new = display(values_[o.key], o.fmt) if o.fmt else str(values_[o.key])
        if new != o.literal:
            out.append((o.start, o.end, new))
            if _year_like(new) and not _year_like(o.literal):
                problems.append(f"{o.file}:{o.line}: {o.literal!r} -> {new!r} ({o.key}) looks like a year, so the next roll "
                                f"would read it as one")
    out.sort(key=lambda e: -e[0])
    return out, problems


KEY_LINE = re.compile(r'^(?P<indent>\s+)"(?P<lit>(?:[^"\\]|\\.)*)":\s*(?P<rest>\S.*?)\s*$')


def _spec_id(spec) -> str:
    import json
    return json.dumps(spec, sort_keys=True, default=str, ensure_ascii=False)


def roll_classification(old_values: dict, new_values: dict, yml_text: str | None = None,
                        texts: dict | None = None) -> tuple[str, list[str]]:
    """values.yml after a roll. Entries are found by their literal, so once a roll has rewritten the text, the literal of
    every keyed entry has to follow it, or the next lint and the next roll would not find them: each keyed spec whose
    key has a value in both datasets moves to the key's new value in its format (a rule's `map` entries too). Specs
    without a context that now share a literal are pinned to their lines (`line`, `nth`), because the text can no
    longer tell them apart. `texts` maps paths to the old text (default: the files as they are).
    Returns the new text and the problems (a key with no value in one dataset; an entry that would split or collide
    where it cannot be pinned). Constants, computed literals and review items keep their literals."""
    import json
    import yaml
    text = yml_text if yml_text is not None else VALUES_YML.read_text(encoding="utf-8")
    problems: list[str] = []
    load_yml(text=text)
    try:
        # 1. the new literal of every keyed occurrence, by entry and spec
        by_spec: dict = {}
        for p in scope_files():
            for o in classify(p, (texts or {}).get(p)):
                if o.cls != "key" or o.entry is None or o.spec is None:
                    continue
                key = o.key
                if key not in old_values or key not in new_values:
                    problems.append(f"{o.file}:{o.line} {o.literal!r} -> {key}: no value in the "
                                    f"{'old' if key not in old_values else 'new'} dataset")
                    continue
                shown = display(old_values[key], o.fmt) if o.fmt else str(old_values[key])
                if shown != o.literal:
                    problems.append(f"{o.file}:{o.line} {o.literal!r} -> {key}: the old value shows {shown!r}")
                    continue
                new = display(new_values[key], o.fmt) if o.fmt else str(new_values[key])
                if _year_like(new) and not _year_like(o.literal):
                    problems.append(f"{o.file}:{o.line} {o.literal!r} -> {new!r} ({key}) looks like a year: the next lint "
                                    f"and roll cannot find the entry")
                by_spec.setdefault((o.entry, _spec_id(o.spec)), []).append((o, new))
        # 2. the entries of the file, in order
        lines = text.split("\n")
        entries: list[dict] = []
        sec = own = ""
        skip_indent = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip(" "))
            if skip_indent is not None:
                if stripped and indent <= skip_indent:
                    skip_indent = None
                else:
                    continue
            if re.match(r"^(rules|everywhere|files):", line):
                sec, own = line.split(":")[0], ""
                continue
            if re.match(r"^\s+(constants|computed|review):", line):
                skip_indent = indent
                continue
            if sec == "files" and re.match(r"^  [^\s\"'#-].*:\s*$", line):
                own = stripped[:-1]
                continue
            rm = re.match(r"^\s+- name:\s*(.*?)\s*$", line)
            if sec == "rules" and rm:
                own = rm.group(1)
                continue
            m = KEY_LINE.match(line)
            if not m or sec not in ("files", "everywhere", "rules"):
                continue
            try:
                specs = _norm_spec(yaml.safe_load("v: " + m.group("rest"))["v"])
            except yaml.YAMLError:
                continue
            entries.append({"i": i, "sec": sec, "own": own if sec != "everywhere" else "", "lit": m.group("lit"),
                            "indent": m.group("indent"), "specs": specs, "m": m})
        # 3. the target literal of every spec
        for e in entries:
            e["targets"] = []
            for spec in e["specs"]:
                found = by_spec.get(((e["sec"], e["own"], e["lit"]), _spec_id(spec)))
                new = {n for _, n in found} if found else {e["lit"]}
                if len(new) > 1:
                    problems.append(f"{e['own'] or e['sec']}: {e['lit']!r} would split into {sorted(new)}")
                e["targets"].append((next(iter(new)) if len(new) == 1 else e["lit"], spec, found or []))
        # 4. entries that now share a literal within a block
        owners: dict = {}
        for e in entries:
            for t, spec, found in e["targets"]:
                owners.setdefault((e["sec"], e["own"], t), set()).add(e["lit"])
        collide = {k for k, v in owners.items() if len(v) > 1}
        for k in collide:
            if k[0] != "files":
                problems.append(f"{k[0]} {k[1] or ''}: two entries now share the literal {k[2]!r}")
        # 5. emit
        emitted: dict = {}
        replace: dict = {}
        drop: set = set()
        for e in entries:
            groups: dict = {}
            for t, spec, found in e["targets"]:
                tk = (e["sec"], e["own"], t)
                if tk in collide and e["sec"] == "files" and "key" in spec and not (
                        "line" in spec or "nth" in spec or spec.get("context")) and found:
                    for o, n in found:
                        groups.setdefault(t, []).append({**spec, "line": o.line, "nth": o.nth})
                else:
                    groups.setdefault(t, []).append(spec)
            new_lines = []
            for t, group in groups.items():
                tk = (e["sec"], e["own"], t)
                if tk in collide and tk in emitted:
                    emitted[tk]["specs"] += group          # merged into the first line of this literal
                    continue
                rec = {"indent": e["indent"], "lit": t, "specs": list(group)}
                if tk in collide:
                    emitted[tk] = rec
                new_lines.append(rec)
            replace[e["i"]] = (e, new_lines)

        def render(rec, e) -> str:
            same = len(rec["specs"]) == len(e["specs"]) and all(a == b for a, b in zip(rec["specs"], e["specs"]))
            if same and rec["lit"] != e["lit"] and rec is not None:
                return lines[e["i"]][:e["m"].start("lit")] + rec["lit"] + lines[e["i"]][e["m"].end("lit"):]
            if same and rec["lit"] == e["lit"]:
                return lines[e["i"]]
            specs = rec["specs"]
            return f'{rec["indent"]}"{rec["lit"]}": ' + json.dumps(specs[0] if len(specs) == 1 else specs, ensure_ascii=False)

        out = []
        for i, line in enumerate(lines):
            if i in replace:
                e, new_lines = replace[i]
                out += [render(rec, e) for rec in new_lines]
            else:
                out.append(line)
        return "\n".join(out), problems
    finally:
        load_yml(force=True)


# --- the values --------------------------------------------------------------------------------

def values(d) -> dict[str, float | int | str]:
    """Every val.<name> the classified literals use, computed from the dataset of `d`."""
    from visible_values_data import compute   # the queries live beside this module
    return compute(d)


def check(d=None) -> list[str]:
    """The classified literals whose key, in the literal's format, differs from the text (empty on the edition)."""
    if d is None:
        sys.path.insert(0, str(HERE))
        from db import Data
        d = Data()
    vals = values(d)
    try:                                       # the registry keys of facts/visible.py (id.*, date.*, fy.*)
        import visible
        vals = {**vals, **visible.compute(d)[0]}
    except Exception as exc:
        print(f"note: facts/visible.py not available ({exc}); id.* keys cannot be checked")
    from visible_values_data import ERRORS
    problems = [f"group {g} failed: {why}" for g, why in ERRORS.items()]
    for p in scope_files():
        for o in classify(p):
            if o.cls != "key":
                continue
            if o.key not in vals:
                problems.append(f"{o.file}:{o.line}: {o.literal!r} -> {o.key}: no such key")
                continue
            shown = display(vals[o.key], o.fmt) if o.fmt else str(vals[o.key])
            if shown != o.literal:
                problems.append(f"{o.file}:{o.line}: text {o.literal!r}, {o.key} = {vals[o.key]!r} shows {shown!r}")
    return problems


def main(argv=None) -> int:
    import argparse
    import collections
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "lint", "report", "dump"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(HERE))
    files = [REPO / f for f in a.files] if a.files else scope_files()
    if a.cmd == "lint":
        n = 0
        for p in files:
            for u in unclassified(p):
                n += 1
                print(f"{u['file']}:{u['line']}: {u['literal']}  | {u['context']}")
        print(f"{n} unclassified literal(s)")
        return 1 if n else 0
    if a.cmd == "dump":
        import json
        rows = [o.as_dict() for p in files for o in classify(p)]
        Path(a.out).write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
        return 0
    if a.cmd == "check":
        probs = check()
        for p in probs:
            print(p)
        print(f"{len(probs)} mismatch(es)")
        return 1 if probs else 0
    # report
    by_file = collections.defaultdict(collections.Counter)
    key_uses: collections.Counter = collections.Counter()
    review: list = []
    for p in files:
        for o in classify(p):
            c = o.cls.split(":")[0] if o.cls else "UNCLASSIFIED"
            by_file[o.file][c] += 1
            if o.cls == "key":
                key_uses[o.key] += 1
            elif o.cls == "review":
                review.append(o)
    cols = ["key", "constant", "review", "computed", "structural", "UNCLASSIFIED"]
    lines = ["| File | " + " | ".join(cols) + " |", "|---|" + "---:|" * len(cols)]
    total: collections.Counter = collections.Counter()
    for f, c in sorted(by_file.items()):
        lines.append(f"| {f} | " + " | ".join(str(c[k]) for k in cols) + " |")
        total.update(c)
    lines.append("| **Total** | " + " | ".join(str(total[k]) for k in cols) + " |")
    lines += ["", f"{len(key_uses)} distinct keys; {sum(key_uses.values())} keyed uses.", "", "Review (may change with a roll; no key):"]
    lines += [f"- {o.file}:{o.line} {o.literal}: {o.note}" for o in review]
    out = chr(10).join(lines)
    if a.out:
        Path(a.out).write_text(out + chr(10), encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
