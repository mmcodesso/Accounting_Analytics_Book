"""The exact values the visible text shows, and the lint that finds the ones not yet classified.

Phase 7 of the companion-files and yearly-roll program keeps readable literals in the source and
rewrites them at each roll (scripts/roll_text.py). This module owns the exact values:

- values(d) -> {"val.<name>": value}: every data value the visible text (and the code that mirrors
  it) shows, computed read-only from the dataset through facts/db.Data's window, reusing the context
  functions of the generated notes (facts/notes/*.py) wherever a note already computes the value;
- display(value, fmt) -> str: a value in a literal's display format (formats: see FORMATS below);
- classify(path, text) -> [Occurrence]: every numeric literal in a file in scope, with its class
  (a key, "constant", or a structural rule) from facts/literals/values.yml;
- unclassified(path, text) -> [dict]: the literals that no rule and no values.yml entry covers (the
  hook that `python scripts/facts.py lint` calls);
- check(d) -> [str]: every classified literal whose key, displayed in its format, differs from what
  the text shows (on the edition's dataset this list must be empty).

What counts as an exact value. A numeric literal written with digits in a file in scope, outside the
generated note regions (a "<!-- notes: KEY -->" line and the comment after it), and outside what agent
A's registry classifies: years (any bare 1900-2099 number), ISO and spelled dates, clock times,
year-quarters and year-months, and document numbers or codes (SI-2025-007947, FUR-DSK-0075,
CHK0006076, T17_SalesInvoiceLine). Every other literal is either structural (a rule below: a
reference such as Tutorial 4.1 or Step 3, a list or requirement number, a slide timing, a multiple
choice key, a software version, an account number, a single digit not counting data) or must be
classified in values.yml as a key or as a constant (a teaching constant or threshold that a roll keeps,
such as 1,000 rows or $50,000). In Python files only the literals that can mirror the text are
scanned: numbers in assert statements and value-shaped text inside string literals. Spelled-out
numbers ("three cutoff invoices") are not literals; the notes' claims and the impact review cover them.

    python facts/visible_values.py check              # every key against today's text (exit 1 on a mismatch)
    python facts/visible_values.py lint [FILES]        # unclassified literals
    python facts/visible_values.py report [--out F]   # counts by file and class, and the mismatches
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
# %e, 6.884200e+02). A unit in words follows the body after a space: " percent", " million",
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
         "x": 1, "e": 1}


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
        word = self.unit if self.unit.startswith(" ") else ""
        body = ("$" if self.dollar else "") + self.sep + f".{self.places}" + ("" if word else self.unit)
        return " ".join(flags + [body]) + word


BODY = re.compile(r"(?P<dollar>\$)?(?P<sep>[,_])?\.(?P<places>\d+)(?P<unit>%|M|K|x|e)?")


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
    if f.sep == "_":
        digits = digits.replace(",", "_")
    unit = {"x": "×"}.get(f.unit, f.unit)
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
            minus=sign if sign in ("−", "-") else MINUS, parens=parens)
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
                          r"At line|at line|lines? of the script|Rows?|rows?|[Cc]olumns?|[Pp]ages?|[Pp]ositions?|"
                          r"[Dd]igits?|[Dd]ecimals?|[Dd]ecimal places|places|IFS|level|[Ss]ection|Opus|GTAG|Volume|"
                          r"[Ff]unction numbers?|[Ff]unction|[Ss]ource|[Ll]ayer|[Ww]eek|Release|Exam|edition|"
                          r"[Ss]ize|[Ff]ont|zoom|Zoom|[Dd]PI|[Tt]ier|Phase|Milestone|Requirement|deck|Deck|Shift|"
                          r"[Ss]lide|Stage|[Hh]eading|[Hh]eader row|[Aa]pproach|[Pp]erspective|Table tab")

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
    cls: str = ""                 # "key", "constant", or "structural:<rule>"
    key: str | None = None
    fmt: str | None = None
    note: str = ""

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("file", "line", "literal", "context", "kind", "cls", "key", "fmt", "note")}


def _mask(text: str) -> str:
    t = text
    for rx in MASKS:
        t = rx.sub(lambda m: _blank(m.group(0)), t)
    return t


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
        if ID_WORD.search(t[max(0, a - 40):a]):
            return None                                # an ID: Register 2, AccountID 3
        if not in_code and DATA_NOUN.match(t[b:b + 40]):
            return None                                # a count of data: 6 rows
        return "small"                                 # a single digit that does not count data
    return None


def _year_like(lit: str) -> bool:
    core = lit.strip("()")
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
                   "notes": range(4, 20), "solutions": range(4, 20), "exa": [], "appendix_a": []}


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

    in_assert = False
    chapters = module_chapters(rel_path(path))
    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME and tok.string == "assert" and (i == 0 or tokens[i - 1].type in (
                tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT)):
            in_assert = True
        elif tok.type == tokenize.NEWLINE:
            in_assert = False
        a, b = pos(*tok.start), pos(*tok.end)
        ctx = text[max(0, a - 70): b + 50].replace("\n", " ")
        if tok.type == tokenize.NUMBER and in_assert:
            lit = tok.string
            occ = Occurrence(rel_path(path), tok.start[0], a, b, lit, ctx, "code")
            prev = tokens[i - 1].string if i else ""
            if prev == "-" and i > 1:
                pass
            try:
                v = float(lit.replace("_", ""))
            except ValueError:
                v = None
            if v is not None and (v in (0, 1, -1) or (abs(v) < 0.1 and "." in lit and len(lit) <= 6) or "e" in lit.lower()):
                occ.cls = "structural:tolerance" if v not in (0, 1) else "structural:small"
            elif _year_like(lit):
                occ.cls = "structural:year"
            elif re.fullmatch(r"\d{4}", lit) and int(lit) in _accounts():
                occ.cls = "structural:account"
            elif re.fullmatch(r"\d", lit):
                occ.cls = "structural:small"
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
                                 text[max(0, sa - 70): sa + len(o.literal) + 50].replace("\n", " "), "code")
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
        text = (p if p.is_absolute() else REPO / p).read_text(encoding="utf-8")
    rel = rel_path(p)
    if rel.endswith(".py"):
        return find_py(rel, text)
    if rel.startswith("facts/notes/templates/"):
        return find_template(rel, text)
    return find_qmd(rel, text)


# --- the classification (facts/literals/values.yml) --------------------------------------------

_YML: dict | None = None


def load_yml(force: bool = False) -> dict:
    global _YML
    if _YML is None or force:
        import yaml
        _YML = yaml.safe_load(VALUES_YML.read_text(encoding="utf-8")) if VALUES_YML.exists() else {}
        _YML = _YML or {}
    return _YML


def _entries_for(rel: str) -> dict:
    files = load_yml().get("files", {}) or {}
    return files.get(rel, {}) or {}


def _norm_entry(e) -> list[dict]:
    """An entry is a key string, "constant", a dict {key|class, format, context, note}, or a list of dicts."""
    if isinstance(e, str):
        return [{"class": "constant"} if e == "constant" else {"key": e}]
    if isinstance(e, dict):
        return [e]
    return [x if isinstance(x, dict) else ({"class": "constant"} if x == "constant" else {"key": x}) for x in e]


def classify(path: Path | str, text: str | None = None) -> list[Occurrence]:
    rel = rel_path(path)
    occs = find(path, text)
    entries = _entries_for(rel)
    shared = load_yml().get("everywhere", {}) or {}
    for o in occs:
        if o.cls.startswith("structural:"):
            continue
        cands = _norm_entry(entries[o.literal]) if o.literal in entries else []
        if not cands and o.literal in shared:
            cands = _norm_entry(shared[o.literal])
        chosen = None
        for c in cands:
            ctx = c.get("context")
            if ctx is None or re.search(ctx, o.context):
                if ctx is not None or chosen is None:
                    chosen = c
                if ctx is not None:
                    break
        if chosen is None:
            continue
        if "key" in chosen:
            o.cls, o.key = "key", chosen["key"]
            o.fmt = chosen.get("format") or (infer_format(o.literal) if parse_literal(o.literal) else None)
        else:
            o.cls = chosen.get("class", "constant")
        o.note = chosen.get("note", "")
    return occs


def unclassified(path: Path | str, text: str | None = None) -> list[dict]:
    """The literals in a file that no structural rule and no values.yml entry covers."""
    return [o.as_dict() for o in classify(path, text) if not o.cls]


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
    problems = []
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
    for p in files:
        for o in classify(p):
            by_file[o.file][o.cls.split(":")[0] if o.cls.startswith("structural") else (o.cls or "UNCLASSIFIED")] += 1
    lines = ["| File | key | constant | structural | unclassified |", "|---|---:|---:|---:|---:|"]
    for f, c in sorted(by_file.items()):
        lines.append(f"| {f} | {c['key']} | {c['constant']} | {c['structural']} | {c['UNCLASSIFIED']} |")
    out = "\n".join(lines)
    if a.out:
        Path(a.out).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
