"""The Solution Notes worksheet of a companion workbook.

It states which file this is and which dataset it was built from, lists what the workbook holds, the tutorial steps
it completes (their titles read from the tutorial text, so the two cannot drift), checks each control total against
the value the dataset gives (Expected, from expected.py) with a live formula (Actual), and repeats what each
tutorial's checkpoint says the results mean.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from paths import REPO

NOTES_SHEET = "Solution Notes"


@dataclass
class Check:
    label: str
    expected: object
    actual: str            # a formula, starting with =
    tolerance: float = 0.005
    number_format: str = "#,##0.00"


def tutorial_file(tutorial: str) -> Path:
    chapter, k = tutorial.split(".")
    if not chapter.isdigit():                         # an appendix's Guided Tutorial B.1
        return next((REPO / "appendices").glob(f"{chapter.lower()}-*")) / f"_tutorial-{int(k):02d}.qmd"
    return next((REPO / "chapters").glob(f"{int(chapter):02d}-*")) / f"_tutorial-{int(k):02d}.qmd"


def plain(text: str) -> str:
    """Markdown to plain text: no emphasis, no figure references, link text only, code without backticks."""
    text = re.sub(r"\(@fig-[\w-]+\)|@fig-[\w-]+", "the figure", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"(?<!\w)\*(?!\s)([^*]+)\*", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def tutorial_info(tutorial: str) -> tuple[str, list[str], str]:
    """The tutorial's title, its step titles, and the closing interpretation of its checkpoint."""
    text = re.sub(r"<!--.*?-->", "", tutorial_file(tutorial).read_text(encoding="utf-8"), flags=re.S)
    title = re.search(r"^## Guided Tutorial [\w.]+: (.+)$", text, flags=re.M).group(1).strip()
    steps = [f"Step {n}. {plain(t)}" for n, t in re.findall(r"^\*\*Step (\d+)\. (.+?)\*\*", text, flags=re.M)]
    checkpoint = text.split("**Checkpoint.**", 1)[1]
    paragraphs = [p.strip() for p in checkpoint.strip().split("\n\n") if p.strip()]
    meaning = plain(paragraphs[-1]) if paragraphs and not paragraphs[-1].lstrip().startswith("-") else ""
    return title, steps, meaning


def tutorial_sections(done: list[str]) -> list[dict]:
    """The sections of a tutorial checkpoint: each tutorial's title, its step titles, and its checkpoint meaning."""
    out = []
    for t in done:
        title, steps, meaning = tutorial_info(t)
        out.append(dict(label=f"Tutorial {t}", title=title, items=steps, meaning=meaning))
    return out


def write(wb, *, file_name: str, role: str, sections: list[dict], stamp: dict, contents: dict[str, list[str]],
          checks: list[tuple[str, Check]], items_heading: str = "Steps completed",
          meaning_heading: str = "What the results mean", check_prefix: str = "Tutorial"):
    """(Re)write the Solution Notes worksheet. `sections` holds, for each tutorial or exercise, its label, title, the
    items done (step titles or requirements), and what its results mean; `checks` pairs each check with its label."""
    from xlbuild.xl import add_sheet, wait_ready
    wait_ready(wb.Application)
    existing = [ws for ws in wb.Worksheets if ws.Name == NOTES_SHEET]
    if existing:                       # reused, never deleted: deleting a worksheet can crash Excel once a slicer exists
        ws = existing[0]
        ws.Cells.Clear()
        ws.Cells.RowHeight = ws.StandardHeight
    else:
        ws = add_sheet(wb)
        ws.Name = NOTES_SHEET
    ws.Tab.Color = 0x00C0FF            # amber (BGR)
    rows: list[tuple] = []

    def line(*cells, style: str = ""):
        rows.append((style, cells))

    line("Solution Notes", style="title")
    line(f"{file_name}: {role}")
    line()
    line("About this file", style="head")
    line("Book", stamp["book"])
    line("Dataset", stamp["dataset"])
    line("Source", stamp["source"])
    line("Built", stamp["built"])
    line()
    line("What the workbook holds", style="head")
    for label, items in contents.items():
        line(label, "; ".join(items) if items else "none")
    line()
    line(items_heading, style="head")
    for sec in sections:
        line(sec["label"], sec["title"], style="bold")
        for item in sec["items"]:
            line("", item)
    line()
    line("Checks", style="head")
    line("Check", "Expected", "Actual", "Agrees", style="bold")
    first = len(rows) + 1
    for t, c in checks:
        line(f"{check_prefix} {t}".strip() + f": {c.label}", c.expected, c.actual, "check",
             style=f"check:{c.tolerance}:{c.number_format}")
    last = len(rows)
    line("All checks agree", "", "", f"=AND(D{first}:D{last})", style="bold")
    line()
    line(meaning_heading, style="head")
    for sec in sections:
        if sec["meaning"]:
            line(sec["label"], sec["meaning"])

    for r, (style, cells) in enumerate(rows, start=1):
        for c, value in enumerate(cells, start=1):
            cell = ws.Cells(r, c)
            if style.startswith("check") and c == 3:
                cell.Formula2 = value
            elif style.startswith("check") and c == 4:
                tol = float(style.split(":")[1])
                cell.Formula = (f"=ABS(C{r}-B{r})<={tol}" if not isinstance(cells[1], str) else f"=C{r}=B{r}")
            elif isinstance(value, str) and value.startswith("="):
                cell.Formula = value
            else:
                cell.Value = value
        if style.startswith("check"):
            fmt = style.split(":", 2)[2]
            ws.Range(f"B{r}:C{r}").NumberFormat = fmt
        if style == "title":
            ws.Cells(r, 1).Font.Size = 14
            ws.Cells(r, 1).Font.Bold = True
        elif style == "head":
            ws.Cells(r, 1).Font.Bold = True
            ws.Cells(r, 1).Font.Size = 12
        elif style == "bold":
            ws.Range(f"A{r}:D{r}").Font.Bold = True
    ws.Columns("A").ColumnWidth = 48
    ws.Columns("B").ColumnWidth = 80
    ws.Columns("C").ColumnWidth = 18
    ws.Columns("D").ColumnWidth = 10
    ws.Columns("A:D").VerticalAlignment = -4160          # top
    for r, (style, cells) in enumerate(rows, start=1):
        if not style.startswith("check") and len(cells) == 2 and len(str(cells[1])) > 70:
            ws.Range(f"B{r}").WrapText = True
            ws.Rows(r).AutoFit()
    ws.Range(f"B{first}:B{last}").HorizontalAlignment = -4152   # right, like the numbers beside them
    return ws, first, last


def read_result(ws, first: int, last: int) -> tuple[bool, list[str]]:
    """Whether every check agrees, and the labels of those that do not."""
    failed = []
    for r in range(first, last + 1):
        if ws.Cells(r, 4).Value is not True:
            failed.append(f"{ws.Cells(r, 1).Value}: expected {ws.Cells(r, 2).Value}, actual {ws.Cells(r, 3).Value}")
    return not failed, failed


def locate(ws) -> tuple[object, int, int]:
    """The rows of the checks in a Solution Notes worksheet: after the "Check" header, before "All checks agree"."""
    used = ws.UsedRange.Rows.Count
    labels = [ws.Cells(r, 1).Value for r in range(1, used + 1)]
    first = labels.index("Check") + 2
    last = labels.index("All checks agree")
    return ws, first, last
