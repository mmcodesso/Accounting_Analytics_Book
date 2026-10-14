"""Instructor figures of Chapter 2 (guides in facts/instructor/guides/chapter-02-understanding-data/)."""

from __future__ import annotations

import ctx
import excel as xl
import kit
from check_figures import text_width
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, INK, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc, money)

NUMBER_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine",
                10: "Ten"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def _general(x: float, digits: int = 15) -> str:
    """A number as Excel's General format shows it: 629.9400000000001 reads 629.94, 0 reads 0."""
    return f"{x:.{digits}g}"


def _grid_rows(d: Diagram, x: float, y: float, widths: list[float], rows: list[tuple[str, list[str]]],
               header: list[str] | None = None, letters: list[str] | None = None, style=None,
               number_color: str = BLUE, band: str | None = "visible") -> dict:
    """Part of a worksheet: an optional letter row and Table header, then rows given as (sheet row number, values).
    band is "visible" (a Table's banding follows its visible rows, so a filtered Table alternates from its first row),
    "number" (the parity of the sheet row number, for an unfiltered Table shown with a gap) or None (no Table)."""
    body = list(rows)
    if header is not None:
        body = [("1", header)] + body
    number_of = [n for n, _ in body]

    def cell_style(r: int, c: int, value: str) -> dict:
        out: dict = {}
        if header is not None and r == 0:
            out = dict(fill=BLUE, stroke=BLUE, color=WHITE, align="left", label=f"<b>{esc(value)}</b>")
        elif band == "visible":
            out = dict(fill=WHITE if r % 2 else BLUE_TINT)
        elif band == "number":
            out = dict(fill=WHITE if int(number_of[r]) % 2 == 0 else BLUE_TINT)
        if style:
            out.update(style(r, c, value) or {})
        return out

    return xl.sheet(d, x, y, letters or [], widths, body, cell_style, number_color=number_color,
                    show_letters=letters is not None)


def _check_columns(data, table: str, columns: dict[str, str], free: str | None = None) -> int:
    """The worksheet keeps the schema's column order: each letter holds its column, and the first free letter (where a
    helper column goes) follows the last column.  Returns the number of columns."""
    names = [r[1] for r in data.q(f"PRAGMA table_info({table})")]
    for letter, name in columns.items():
        assert names[ord(letter) - 65] == name, (table, letter, name, names)
    assert free is None or chr(65 + len(names)) == free, (table, free, len(names))
    return len(names)


def _hidden_text(visible: list[str], n: int) -> str:
    """'A to F, H and L to O': the letters among a worksheet's first n columns that the figure hides."""
    letters = [chr(65 + i) for i in range(n) if chr(65 + i) not in visible]
    runs: list[list[str]] = []
    for letter in letters:
        if runs and ord(letter) == ord(runs[-1][-1]) + 1:
            runs[-1].append(letter)
        else:
            runs.append([letter])
    parts = [part for run in runs for part in ([f"{run[0]} to {run[-1]}"] if len(run) > 2 else run)]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def _dropdown(d: Diagram, geo: tuple) -> None:
    """The filter button of a Table header (a small white triangle at the right of the cell)."""
    hx, hy, hw, hh = geo
    d.vertex("", "triangle;direction=south;html=1;fillColor=#FFFFFF;strokeColor=none;", hx + hw - 16, hy + hh / 2 - 3.5,
             9, 7)


def _gap(d: Diagram, x: float, y: float, w: float, text: str, h: float = 24) -> float:
    """A band that stands for the rows of a long worksheet that the figure leaves out."""
    d.box(f"<i>{esc(text)}</i>", x, y, w, h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, rounded=False, dashed=True)
    return y + h


# -- IF-02-0-A: the findings of the two tutorials by quality dimension -------------------------------------------------

DIMENSIONS = ["Accuracy", "Completeness", "Consistency", "Timeliness"]

# (finding, where it sits in the workbook, {dimension: "main" | "also"}, (kind, reason)).  The dimension a finding is
# tested under follows Table 2.3 of the chapter and the guides' own readings: the In Transit rows disagree between two
# columns (consistency) and the status was not updated (timeliness); a pair of customers with one name is a
# consistency risk, and "no duplicate records" is an accuracy test; the rows with no amount are accuracy and
# consistency (Exercise 2.5, Step 9); the small periods are the edge of the extract (timeliness) that reads like
# missing transactions (completeness).
FINDINGS = [
    ("Tutorial 2.1: the Order-to-Cash and Item tables", None, None, None),
    ("Blank tracking numbers", "Shipment, TrackingNumber (Step 2)", {"Completeness": "main"},
     ("error", "evidence should exist")),
    ("In Transit after the delivery date", "Shipment, Status and DeliveryDate (Step 3)",
     {"Consistency": "main", "Timeliness": "also"}, ("error", "two columns disagree")),
    ("Invoice dated before first shipment", "SalesInvoice, InvoiceDate (Steps 6, 7)", {"Accuracy": "main"},
     ("error", "dates out of order")),
    ("Customers that share a name", "Customer, CustomerName (Step 4)", {"Consistency": "main", "Accuracy": "also"},
     ("judgment", "compare the records")),
    ("Freight costs far above the average", "Shipment, FreightCost (Step 5)", {"Accuracy": "main"},
     ("judgment", "ask what shipped")),
    ("Blank list prices", "Item, ListPrice (Step 8)", {"Completeness": "main"}, ("design", "the items are bought")),
    ("Tutorial 2.2: the Accounting Core", None, None, None),
    ("Ledger rows with no amount", "GLEntry, Debit and Credit (Step 7)", {"Accuracy": "main", "Consistency": "also"},
     ("judgment", "investigate and explain")),
    ("Small first and last periods", "GLEntry, FiscalPeriod (Step 6)", {"Timeliness": "main", "Completeness": "also"},
     ("design", "the edge of the extract")),
]

KINDS = {"error": ("Error", CORAL), "judgment": ("Judgment", AMBER), "design": ("By design", TEAL)}


def _kind_marker(d: Diagram, kind: str, x: float, y: float) -> None:
    """A marker that differs in shape and glyph as well as color: circle !, diamond ?, square check mark."""
    glyph = {"error": "!", "judgment": "?", "design": "✓"}[kind]
    shape = {"error": "ellipse", "judgment": "rhombus", "design": "rounded=0;shape=rectangle"}[kind]
    color = KINDS[kind][1]
    style = shape if "=" in shape else f"{shape};"
    size = 26 if kind == "judgment" else 22
    off = (26 - size) / 2
    d.vertex(glyph, f"{style}whiteSpace=wrap;html=1;fillColor={color};strokeColor={color};fontColor={WHITE};"
             f"fontSize=12;fontFamily=Helvetica;align=center;verticalAlign=middle;spacing=0;"
             f"fontStyle={'0' if kind == 'design' else '1'};", x + off, y + off, size, size)


def if_02_0_a() -> Diagram:
    """The findings of Tutorials 2.1 and 2.2 against the four data quality dimensions (Chapter 2 note)."""
    d = Diagram("Where Each Finding Sits Among the Four Data Quality Dimensions")
    widths = [264, 102, 102, 102, 102, 188]
    xs = [0.0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    head_h = 38
    labels = ["Finding"] + DIMENSIONS + ["Error, judgment or by design"]
    for x, w, text in zip(xs, widths, labels):
        d.box(f"<b>{esc(text)}</b>", x, 0, w, head_h, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False,
              align="left" if text in ("Finding", labels[-1]) else "center")
    y = head_h
    row_h = 46
    two = 0
    count = 0
    for finding, where, dims, kind in FINDINGS:
        if where is None:                                       # a heading band for one tutorial
            d.box(f"<b>{esc(finding)}</b>", 0, y, 860, 24, fill=GRAY_TINT, stroke=RULE, size=SMALL, rounded=False,
                  align="left")
            y += 24
            continue
        count += 1
        two += sum(1 for v in dims.values() if v == "also") > 0
        for part, w in ((f"<b>{esc(finding)}</b>", widths[0]), (esc(where), widths[0])):
            assert text_width(part, SMALL, False) <= w - 12, (finding, where)
        d.box(f"<b>{esc(finding)}</b><br>{esc(where)}", xs[0], y, widths[0], row_h, fill=WHITE, stroke=RULE, size=SMALL,
              align="left", rounded=False)
        for c, name in enumerate(DIMENSIONS):
            x = xs[c + 1]
            mark = dims.get(name)
            if mark == "main":
                d.box("<b>tested</b>", x, y, widths[c + 1], row_h, fill=BLUE, stroke=RULE, color=WHITE, size=SMALL,
                      rounded=False)
            elif mark == "also":
                d.box("also touches", x + 3, y + 3, widths[c + 1] - 6, row_h - 6, fill=WHITE, stroke=BLUE,
                      stroke_width=2, size=SMALL, rounded=False)
                d.box("", x, y, widths[c + 1], row_h, fill="none", stroke=RULE, rounded=False)
            else:
                d.box("", x, y, widths[c + 1], row_h, fill=WHITE, stroke=RULE, rounded=False)
        k, reason = kind
        word = KINDS[k][0]
        d.box("", xs[5], y, widths[5], row_h, fill=WHITE, stroke=RULE, rounded=False)
        _kind_marker(d, k, xs[5] + 10, y + (row_h - 26) / 2)
        d.text(f"<b>{word}</b><br>{esc(reason)}", xs[5] + 42, y + 3, widths[5] - 46, row_h - 6, size=SMALL,
               valign="middle")
        y += row_h
    # The key.
    ky = y + 14
    d.box("<b>tested</b>", 0, ky, 70, 24, fill=BLUE, stroke=BLUE, color=WHITE, size=SMALL, rounded=False)
    d.text("The dimension the test examines.", 78, ky, 230, 24, size=SMALL, valign="middle")
    d.box("also touches", 318, ky, 90, 24, fill=WHITE, stroke=BLUE, stroke_width=2, size=SMALL, rounded=False)
    d.text("A second dimension the finding also touches.", 416, ky, 300, 24, size=SMALL, valign="middle")
    ky += 36
    kx = 0.0
    for k, text in (("error", "Error: a genuine problem to correct or explain"),
                    ("judgment", "Judgment: decide on evidence"),
                    ("design", "By design: expected, record it")):
        _kind_marker(d, k, kx, ky - 1)
        width = text_width(text, SMALL, False) + 8
        d.text(text, kx + 32, ky, width, 24, size=SMALL, valign="middle")
        kx += 32 + width + 18
    assert kx <= 860 + 18, kx
    d.text(f"<i>{NUMBER_WORDS[two]} of the {NUMBER_WORDS[count].lower()} findings touch two dimensions, so name the one the "
           f"test examines and add the second when it applies. The small periods look like missing transactions "
           f"(completeness) until you see that they sit at the edge of the extract (timeliness). The counts are in the "
           f"tutorial guides.</i>", 0, ky + 34, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-02-0-B: tidy or messy, clean or dirty -------------------------------------------------------------------------

def _budget_rows() -> list[tuple[str, int, float]]:
    """The salaries budgets of three cost centers for the first three months of the prior fiscal year, as Figure 2.6
    draws them: (cost center, month, amount), cost centers in ID order."""
    data = ctx.data()
    rows = data.q("SELECT cc.CostCenterName, b.Month, b.BudgetAmount FROM Budget b "
                  "JOIN CostCenter cc USING (CostCenterID) JOIN Account a USING (AccountID) "
                  "WHERE b.FiscalYear = ? AND b.Month <= 3 AND a.AccountNumber IN (6010, 6030, 6240) "
                  "ORDER BY cc.CostCenterID, b.Month", data.P)
    assert len(rows) == 9, rows
    return rows


def _transposed(amount: float) -> float:
    """The amount with its last two whole-number digits swapped, the classic keying error."""
    whole, cents = f"{amount:.2f}".split(".")
    digits = list(whole)
    for i in range(len(digits) - 1, 0, -1):
        if digits[i] != digits[i - 1]:
            digits[i], digits[i - 1] = digits[i - 1], digits[i]
            break
    else:
        raise ValueError("no digits to swap")
    return float("".join(digits) + "." + cents)


def _sketch(d: Diagram, x: float, y: float, widths: list[float], header: list[str], rows: list[list[str]],
            wrong: tuple[int, int] | None = None, more: str | None = None, row_h: float = 22) -> float:
    """A small table sketch: a gray header and white rows; the wrong cell is outlined in coral.  Returns the bottom."""
    xs = [x]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    for cx, w, text in zip(xs, widths, header):
        d.box(f"<b>{esc(text)}</b>", cx, y, w, row_h, fill=GRAY, stroke=RULE, color=WHITE, size=SMALL, rounded=False,
              align="left")
    for r, row in enumerate(rows):
        for c, (cx, w, text) in enumerate(zip(xs, widths, row)):
            numeric = text.startswith("$")
            is_wrong = wrong == (r, c)
            d.box(f"<b>{esc(text)}</b>" if is_wrong else esc(text), cx, y + row_h * (r + 1), w, row_h,
                  fill=CORAL_TINT if is_wrong else WHITE, stroke=CORAL if is_wrong else RULE,
                  stroke_width=2 if is_wrong else 1, color=CORAL if is_wrong else INK, size=SMALL, rounded=False,
                  align="right" if numeric else "left")
    bottom = y + row_h * (len(rows) + 1)
    if more:
        d.box(f"<i>{esc(more)}</i>", x, bottom, sum(widths), row_h, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL,
              rounded=False, align="left")
        bottom += row_h
    return bottom


def if_02_0_b() -> Diagram:
    """The 2 x 2 of tidy or messy against clean or dirty, with budget data (Chapter 2 note; Figure 2.6)."""
    rows = _budget_rows()
    centers = list(dict.fromkeys(name for name, _, _ in rows))
    amount = {(name, m): v for name, m, v in rows}
    target = centers[1]                                  # the cost center and month whose amount is keyed wrongly
    right, wrong = amount[(target, 2)], _transposed(amount[(target, 2)])
    d = Diagram("Tidy or Messy, Clean or Dirty")
    label_w, cell_w, gap_x, gap_y = 90, 340, 78, 62
    col_x = [label_w + 6, label_w + 6 + cell_w + gap_x]
    top = 44
    cell_h = 214
    row_y = [top, top + cell_h + gap_y]
    for x, name, sub in ((col_x[0], "Tidy", "each variable in a column, each observation in a row"),
                         (col_x[1], "Messy", "values stored in the column headers")):
        d.box(f"<b>{name}</b><br>{sub}", x, 0, cell_w, 38, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL, rounded=False)
    for y, name, sub in ((row_y[0], "Clean", "every amount right"), (row_y[1], "Dirty", "an amount is wrong")):
        d.box(f"<b>{name}</b><br>{sub}", 0, y, label_w, cell_h, fill=GRAY, stroke=GRAY, color=WHITE, size=SMALL,
              rounded=False)
    quadrants = [
        # (column, row, title, tint, layout, has a wrong amount, the example)
        (0, 0, "Tidy and clean", "teal", "long", False,
         "A long Budget table: every amount agrees with the approved budget."),
        (1, 0, "Clean but messy", "amber", "wide", False,
         "A report with the months across the top: every amount is right."),
        (0, 1, "Tidy but dirty", "amber", "long", True,
         f"The same table with {target}, {MONTHS[1]} keyed as {money(wrong)} for {money(right)}."),
        (1, 1, "Messy and dirty", "coral", "wide", True,
         f"The same report with {target}, {MONTHS[1]} keyed as {money(wrong)} for {money(right)}."),
    ]
    ids = {}
    for c, r, title, tint_name, layout, has_wrong, example in quadrants:
        x, y = col_x[c], row_y[r]
        fill, stroke = kit.tint(tint_name)
        ids[(c, r)] = d.box("", x, y, cell_w, cell_h, fill=fill, stroke=stroke, stroke_width=1.5)
        d.text(f"<b>{title}</b>", x + 10, y + 6, cell_w - 20, 22, size=14)
        if layout == "long":
            shown = [(target, m) for m in (1, 2, 3)]
            body = [[name, MONTHS[m - 1], money(wrong if has_wrong and m == 2 else amount[(name, m)])] for name, m in shown]
            bottom = _sketch(d, x + 12, y + 36, [112, 88, 116], ["Department", "Month", "Budget Amount"], body,
                             wrong=(1, 2) if has_wrong else None, more=f"... {len(rows)} rows in all")
        else:
            body = [[name] + [money(wrong if has_wrong and (name, m) == (target, 2) else amount[(name, m)])
                              for m in (1, 2, 3)] for name in centers]
            bottom = _sketch(d, x + 12, y + 36, [104, 72, 72, 72], ["Department", *MONTHS[:3]], body,
                             wrong=(1, 2) if has_wrong else None)
        d.text(esc(example), x + 10, bottom + 8, cell_w - 20, 40, size=SMALL)
    # Reshaping moves a dataset across the grid (either way); correcting values moves it up.
    for r in (0, 1):
        d.edge(ids[(0, r)], ids[(1, r)], start="blockThin", end="blockThin", color=GRAY, width=2.5,
               exit=(1, 0.5), entry=(0, 0.5))
        d.text("<b>Reshape</b>", col_x[0] + cell_w, row_y[r] + cell_h / 2 - 28, gap_x, 20, size=SMALL, align="center")
    for c in (0, 1):
        d.edge(ids[(c, 1)], ids[(c, 0)], end="blockThin", color=TEAL, width=2.5, exit=(0.5, 0), entry=(0.5, 1))
        d.text("<b>Correct the values</b>", col_x[c] + cell_w / 2 + 14, row_y[0] + cell_h + gap_y / 2 - 10, 160, 20,
               size=SMALL)
    bottom = row_y[1] + cell_h
    kit.callout(d, "Reshaping (Power Query, a PivotTable) changes the layout and leaves every value as it is. Correcting "
                   "a value changes the data and leaves the layout as it is. A dataset can need either, both or neither: "
                   "these are different jobs.", 0, bottom + 16, 860, color="amber")
    d.text(f"<i>Amounts: the Charles River salaries budgets of three cost centers, fiscal {ctx.data().P}, as in Figure 2.6. "
           f"The wrong amount is the same amount with its last two whole-number digits swapped, added for the "
           f"illustration; it is not in the data.</i>", 0, bottom + 78, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-02-1-A: the Difference helper column on SalesInvoiceLine -----------------------------------------------------

def if_02_1_a() -> Diagram:
    """SalesInvoiceLine with the Difference helper column, sorted largest first (Exercise 2.1, Step 6)."""
    data = ctx.data()
    n_columns = _check_columns(data, "SalesInvoiceLine", {"G": "Quantity", "I": "UnitPrice", "J": "Discount", "K": "LineTotal"},
                               free="P")
    first, last, n = data.q("SELECT MIN(SalesInvoiceLineID), MAX(SalesInvoiceLineID), COUNT(*) FROM SalesInvoiceLine")[0]
    assert (first, last) == (1, n), "row numbers assume SalesInvoiceLineID 1..n in worksheet order"
    lines = data.q("SELECT Quantity, UnitPrice, Discount, LineTotal FROM SalesInvoiceLine ORDER BY SalesInvoiceLineID")
    diffs = [abs(q * u * (1 - disc) - total) for q, u, disc, total in lines]      # the order of Excel's arithmetic
    order = sorted(range(n), key=lambda i: -diffs[i])                              # Excel's sort keeps ties in order
    shown = lambda x: f"{x:.7g}"                                                   # General in a default-width column
    biggest, over_cent = max(diffs), sum(1 for x in diffs if x > 0.01)
    assert biggest <= 0.01 and diffs[order[0]] == biggest

    def row_values(i: int) -> list[str]:
        q, u, disc, total = lines[i]
        return [_general(q), _general(u), _general(disc), _general(total), shown(diffs[i])]

    top, bottom_rows = 8, 2
    headers = ["Quantity", "UnitPrice", "Discount", "LineTotal", "Difference"]
    letters = ["G", "I", "J", "K", "P"]
    widths = [56, 150, 150, 140, 160, 204]
    d = Diagram("The SalesInvoiceLine Worksheet with the Difference Column")
    formula = "=ABS(G2*I2*(1-J2)-K2)"
    xl.formula_bar(d, 0, 0, 860, "P2", formula)
    y0 = 40
    part1 = [(str(r + 2), row_values(i)) for r, i in enumerate(order[:top])]
    geo = _grid_rows(d, 0, y0, widths, part1, header=headers, letters=letters, number_color=GRAY, band="number")
    _dropdown(d, geo[(0, 4)])
    y = y0 + 22 + 24 * (top + 1)
    hidden = n - top - bottom_rows
    y = _gap(d, 0, y, 860, f"{hidden} more rows, sorted down to the smallest differences")
    tail = [(str(n + 2 - bottom_rows + k), row_values(i)) for k, i in enumerate(order[-bottom_rows:])]
    last_row = n + 1
    blank = (str(last_row + 1), [""] * 5)
    res1 = (str(last_row + 2), ["", "", "Largest", shown(biggest), ""])
    res2 = (str(last_row + 3), ["", "", "Over one cent", str(over_cent), ""])
    below = lambda r, c, v: dict(fill=WHITE) if r >= bottom_rows else None          # outside the Table: no banding
    geo2 = _grid_rows(d, 0, y, widths, tail + [blank, res1, res2], number_color=GRAY, band="number", style=below)
    # Emphasis: the largest difference, and the two results below the Table.
    xl.emphasis(d, *geo[(1, 4)])
    x1, y1, w1, h1 = geo2[(3, 3)]
    xl.emphasis(d, x1, y1, w1, 24 * 2)
    y = y + 24 * (len(tail) + 3) + 10
    xl.sheet_tabs(d, 0, y, xl.tabs_around("SalesInvoiceLine", 3, 2), "SalesInvoiceLine")
    d.text(f"<i>Columns {_hidden_text(letters, n_columns)} are hidden. The Table has {n} lines and is sorted by Difference, largest first. "
           f"Outlined: the largest difference, {shown(biggest)}, which is half a cent, and the two cells below the Table, "
           f"which hold =MAX(P:P) and =COUNTIF(P:P,&quot;&gt;0.01&quot;). No line differs by more than a cent.</i>",
           0, y + 34, 860, 52, size=SMALL, color=GRAY)
    return d


# -- IF-02-2-A: the PivotTable of ledger rows by fiscal year and period ----------------------------------------------

def _pivot_rows(data) -> tuple[list[tuple[int, int, int]], dict[int, int]]:
    periods = data.q("SELECT FiscalYear, FiscalPeriod, COUNT(*) FROM GLEntry GROUP BY 1, 2 ORDER BY 1, 2")
    totals = dict(data.q("SELECT FiscalYear, COUNT(*) FROM GLEntry GROUP BY 1 ORDER BY 1"))
    return periods, totals


def _expand_box(d: Diagram, x: float, y: float) -> None:
    """The minus button of an expanded PivotTable item."""
    d.box("", x, y, 11, 11, fill=WHITE, stroke=GRAY, rounded=False)
    d.box("", x + 3, y + 5, 5, 1.5, fill=GRAY, stroke=GRAY, rounded=False)


def if_02_2_a() -> Diagram:
    """The PivotTable of GLEntry rows by FiscalYear and FiscalPeriod, with the three small periods marked
    (Exercise 2.2, Step 3)."""
    data = ctx.data()
    t2 = ctx.values("ch02.t2")
    periods, totals = _pivot_rows(data)
    low = [(y, p, n) for y, p, n in periods if n < 0.5 * t2["typical"]]
    assert low == [periods[0]] + periods[-2:] == [tuple(r) for r in t2["low"]], "the small periods are the first and the last two"
    last_year = periods[-1][0]
    last_types = [r[0] for r in data.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE FiscalYear = ?", last_year)]
    # The whole PivotTable in compact form (row 3 is the header): the figure shows its first and its last rows.
    layout: list[tuple[int, str, str, str]] = []            # (sheet row, kind, label, count)
    row = 4
    for year in sorted(totals):
        layout.append((row, "year", str(year), str(totals[year])))
        row += 1
        for y, p, n in periods:
            if y == year:
                layout.append((row, "period", str(p), str(n)))
                row += 1
    layout.append((row, "grand", "Grand Total", str(sum(totals.values()))))
    head = layout[:4]                                        # the first year and its first three periods
    last_rows = layout[-6:]                                  # the last two periods of the year before, the last year, the total
    assert [r[1] for r in head] == ["year", "period", "period", "period"], head
    assert [r[1] for r in last_rows] == ["period", "period", "year", "period", "period", "grand"], last_rows
    assert [int(r[3]) for r in last_rows[3:5]] == [n for _, _, n in low[1:]], (last_rows, low)
    d = Diagram("The PivotTable of Ledger Rows by Fiscal Year and Fiscal Period")
    widths = [44, 156, 166]
    sheet_w = sum(widths)

    def draw(rows, y):
        """Rows of the PivotTable in compact form: bold year rows with a minus button, indented periods."""
        body = [(str(r), [label, count]) for r, kind, label, count in rows]

        def style(i: int, c: int, value: str) -> dict:
            kind = rows[i][1]
            text = esc(value)
            if c == 0:
                text = "&nbsp;" * {"year": 4, "period": 8, "grand": 0}[kind] + (f"<b>{text}</b>" if kind != "period" else text)
            elif kind != "period":
                text = f"<b>{text}</b>"
            fill = WHITE if kind == "period" else BLUE_TINT if kind == "year" else GRAY_TINT
            return dict(fill=fill, label=text, align="left" if c == 0 else "right")

        geo = xl.sheet(d, 0, y, [], widths, body, style, number_color=GRAY, show_letters=False)
        for i, (_, kind, _, _) in enumerate(rows):
            if kind == "year":
                gx, gy, _, _ = geo[(i, 0)]
                _expand_box(d, gx + 8, gy + 6.5)
        return geo

    # Header row (sheet row 3) under the column letters, then the first rows, a gap, and the last rows.
    xl.sheet(d, 0, 0, ["A", "B"], widths, [("3", ["Row Labels", "Count of GLEntryID"])],
             lambda r, c, v: dict(fill=BLUE_TINT, label=f"<b>{esc(v)}</b>", align="left" if c == 0 else "right"),
             number_color=GRAY)
    y = 22 + 24
    g1 = draw(head, y)
    y += 24 * len(head)
    y = _gap(d, 0, y, sheet_w, f"rows {head[-1][0] + 1} to {last_rows[0][0] - 1} are scrolled out of view")
    g2 = draw(last_rows, y)
    bottom = y + 24 * len(last_rows)
    # The three small periods, outlined.
    gx, gy, gw, _ = g1[(1, 0)]
    xl.emphasis(d, gx, gy, gw + g1[(1, 1)][2], 24)
    gx, gy, gw, _ = g2[(3, 0)]
    xl.emphasis(d, gx, gy, gw + g2[(3, 1)][2], 24 * 2)
    xl.sheet_tabs(d, 0, bottom + 8, ["Account", "Sheet1", "GLEntry"], "Sheet1")
    # The PivotTable Fields pane.
    px, pw = 628, 232
    d.box("<b>PivotTable Fields</b>", px, 0, pw, 28, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left", rounded=False)
    areas = [("Filters", []), ("Columns", []), ("Rows", ["FiscalYear", "FiscalPeriod"]), ("Values", ["Count of GLEntryID"])]
    ay = 36
    for name, chips in areas:
        d.text(f"<b>{name}</b>", px, ay, pw, 20, size=SMALL)
        ay += 20
        height = max(30, 26 * len(chips) + 6)
        d.box("", px, ay, pw, height, fill=WHITE, stroke=RULE, rounded=False)
        for k, chip in enumerate(chips):
            d.box(esc(chip), px + 6, ay + 4 + 26 * k, pw - 12, 22, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left",
                  rounded=False)
            d.vertex("", "triangle;direction=south;html=1;fillColor=#5D6D7E;strokeColor=none;", px + pw - 26,
                     ay + 4 + 26 * k + 8, 9, 7)
        ay += height + 8
    # The note beside the table.
    kit.callout(d, f"The outlined periods sit at the edges of the extract. The records begin in the first period, and "
                   f"fiscal {last_year} holds only {', '.join(last_types)} rows, which settle the year before: they are "
                   f"not missing sales or purchases.", sheet_w + 18, 70, px - sheet_w - 36, color="amber")
    d.text(f"<i>Outlined: the first period of the first year and the last two periods of the data. Each holds far fewer "
           f"rows than the {t2['typical']:,.0f} that a period typically holds.</i>", 0, bottom + 42, 860, 36, size=SMALL,
           color=GRAY)
    return d


# -- IF-02-3-A: WorkOrder with the Operations helper column, filtered to zero ------------------------------------------

def if_02_3_a() -> Diagram:
    """WorkOrder with the Operations helper column filtered to 0 (Exercise 2.3, Step 5)."""
    data = ctx.data()
    n_columns = _check_columns(data, "WorkOrder", {"A": "WorkOrderID", "B": "WorkOrderNumber", "C": "ItemID", "H": "ReleasedDate",
                                                    "K": "ClosedDate", "L": "Status"}, free="Q")
    _check_columns(data, "WorkOrderOperation", {"B": "WorkOrderID"})             # the column the COUNTIFS searches
    total = data.one("SELECT COUNT(*) FROM WorkOrder")
    none = data.q("SELECT w.WorkOrderID, w.WorkOrderNumber, w.ItemID, w.ReleasedDate, w.ClosedDate, w.Status FROM WorkOrder w "
                  "WHERE w.WorkOrderID NOT IN (SELECT WorkOrderID FROM WorkOrderOperation) ORDER BY w.WorkOrderID")
    assert none and all(r[5] == "Closed" for r in none), "the work orders with no operation are all Closed"
    spread = data.q("SELECT n, COUNT(*) FROM (SELECT w.WorkOrderID, COUNT(o.WorkOrderOperationID) n FROM WorkOrder w LEFT JOIN "
                    "WorkOrderOperation o USING (WorkOrderID) GROUP BY 1) GROUP BY 1 ORDER BY 1")
    # The worksheet lists WorkOrderID in order, so a work order sits in row (its place in that order) + 1.
    rows = [(str(data.one("SELECT COUNT(*) FROM WorkOrder WHERE WorkOrderID <= ?", r[0]) + 1),
             [r[1], str(r[2]), r[3], r[4], r[5], "0"]) for r in none]
    headers = ["WorkOrderNumber", "ItemID", "ReleasedDate", "ClosedDate", "Status", "Operations"]
    letters = ["B", "C", "H", "K", "L", "Q"]
    widths = [56, 168, 100, 140, 140, 112, 144]
    d = Diagram("The WorkOrder Worksheet Filtered to Work Orders with No Operations")
    xl.formula_bar(d, 0, 0, 860, f"Q{rows[0][0]}", f"=COUNTIFS(WorkOrderOperation!B:B,A{rows[0][0]})")
    y0 = 40
    geo = _grid_rows(d, 0, y0, widths, rows, header=headers, letters=letters)
    ops_col = 5
    hx, hy, hw, hh = geo[(0, ops_col)]
    _dropdown(d, geo[(0, ops_col)])
    xl.emphasis(d, *xl.column_box(geo, ops_col, len(rows) + 1))
    # The open filter list of the Operations header.
    py = y0 + 22 + 24 * (len(rows) + 1) + 26
    pw, item_h = 196, 22
    px = hx + hw - pw
    ph = 8 + 24 + 8 + item_h * (len(spread) + 1) + 10 + 26 + 10
    arrow_x = hx + hw - 11.5
    d.edge(d.anchor(arrow_x, y0 + 22 + 24 * (len(rows) + 1) + 2), d.anchor(arrow_x, py), color=GRAY, width=1.5,
           meta="edgeStyle=none;")
    d.box("", px, py, pw, ph, fill=WHITE, stroke=GRAY, stroke_width=1.5, rounded=False)
    d.box("<i>Search</i>", px + 8, py + 8, pw - 16, 24, fill=WHITE, stroke=RULE, color=GRAY, size=SMALL, align="left",
          rounded=False)
    ly = py + 40
    d.vertex("■", "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#5D6D7E;fontColor=#1A5276;fontSize=12;"
             "fontFamily=Helvetica;align=center;verticalAlign=middle;spacing=0;", px + 12, ly + 4, 14, 14)
    d.text("(Select All)", px + 34, ly, pw - 50, item_h, size=SMALL, valign="middle")
    ly += item_h
    for value, _count in spread:
        xl.checkbox(d, px + 12, ly + 4, value == 0)
        d.text(f"<b>{value}</b>" if value == 0 else str(value), px + 34, ly, pw - 50, item_h, size=SMALL, valign="middle")
        ly += item_h
    by = py + ph - 36
    xl.button(d, px + pw - 162, by, 70, "OK", primary=True)
    xl.button(d, px + pw - 84, by, 70, "Cancel")
    rest = [(v, n) for v, n in spread if v]
    others = " and ".join(f"{n:,} have {NUMBER_WORDS[v].lower()}" for v, n in rest)
    note = (f"Filtering Operations to 0 leaves {len(rows)} of the {total:,} work orders, all of them Closed. Every other work "
            f"order has operations: {others}.")
    kit.callout(d, note, 0, py + 8, px - 16, color="gray")
    bottom = py + ph + 10
    xl.sheet_tabs(d, 0, bottom, xl.tabs_around("WorkOrder", 3, 2), "WorkOrder")
    xl.status_bar(d, 0, bottom + 28, 860, f"{len(rows)} of {total} records found")
    d.text(f"<i>Columns {_hidden_text(letters, n_columns)} are hidden. Outlined: the Operations column, filtered to the "
           f"value 0 (the filter list is open). Blue row numbers mark a filtered Table.</i>", 0, bottom + 60, 860, 36,
           size=SMALL, color=GRAY)
    return d


# -- IF-02-4-A: how BudgetLine rolls up to Budget ------------------------------------------------------------------

def if_02_4_a() -> Diagram:
    """BudgetLine's three bands, and which of them Budget carries (Exercise 2.4, Steps 2 and 4)."""
    data = ctx.data()
    ex4 = ctx.values("ch02.ex4")
    year = data.C
    assert ex4["rolled_diff"] == 0, "every Budget row equals the sum of its BudgetLine rows"
    total = data.one("SELECT COUNT(*) FROM BudgetLine WHERE FiscalYear = ?", year)
    kept, kept_accounts = data.q("SELECT COUNT(*), COUNT(DISTINCT AccountID) FROM BudgetLine WHERE FiscalYear = ? AND "
                                 "BudgetCategory IN ('Revenue', 'COGS', 'Operating Expense') AND CostCenterID IS NOT NULL",
                                 year)[0]
    opex, opex_accounts, opex_amount = data.q("SELECT COUNT(*), COUNT(DISTINCT AccountID), SUM(BudgetAmount) FROM BudgetLine "
                                              "WHERE FiscalYear = ? AND BudgetCategory = 'Operating Expense' AND "
                                              "CostCenterID IS NULL", year)[0]
    sheet, sheet_accounts = data.q("SELECT COUNT(*), COUNT(DISTINCT AccountID) FROM BudgetLine WHERE FiscalYear = ? AND "
                                   "BudgetCategory = 'Balance Sheet'", year)[0]
    assert kept + opex + sheet == total, "the three bands cover every BudgetLine row of the year"
    assert data.one("SELECT COUNT(*) FROM BudgetLine WHERE BudgetCategory = 'Balance Sheet' AND CostCenterID IS NOT NULL") == 0
    budget_rows = ex4["budget_rows"]
    d = Diagram("How BudgetLine Rolls Up to Budget and What Budget Leaves Out")
    left_w = 400
    d.box("<b>BudgetLine</b>", 0, 0, left_w, 30, fill=BLUE, stroke=BLUE, color=WHITE, size=14, rounded=False)
    d.text(f"<i>Fiscal {year}: {total:,} driver lines</i>", 0, 32, left_w, 20, size=SMALL, color=GRAY)
    bands = [
        ("teal", f"<b>Revenue, cost of goods sold and operating expense lines that have a cost center</b><br>"
                 f"{kept:,} lines on {kept_accounts} accounts", 96),
        ("amber", f"<b>Operating expense lines with no cost center</b><br>{opex:,} lines on {opex_accounts} accounts, "
                  f"{money(opex_amount)}", 76),
        ("gray", f"<b>Balance sheet rollforward lines</b><br>{sheet:,} lines on {sheet_accounts} accounts, no cost center", 76),
    ]
    y = 56
    band_boxes = []
    for name, text, h in bands:
        fill, stroke = kit.tint(name)
        band_boxes.append((d.box(text, 0, y, left_w, h, fill=fill, stroke=stroke, stroke_width=1.5, align="left",
                                 rounded=False), y, h))
        y += h + 8
    left_bottom = y - 8
    # Budget: one row for each fiscal year, month, cost center and account.
    bx, bw = 616, 244
    body_y, body_h = 56, 192
    d.box("<b>Budget</b>", bx, 0, bw, 30, fill=BLUE, stroke=BLUE, color=WHITE, size=14, rounded=False)
    d.text(f"<i>Fiscal {year}: {budget_rows:,} rows</i>", bx, 32, bw, 20, size=SMALL, color=GRAY)
    budget = d.box("", bx, body_y, bw, body_h, fill=TEAL_TINT, stroke=TEAL, stroke_width=1.5, rounded=False)
    d.text("<b>One row for each:</b>", bx + 10, body_y + 8, bw - 20, 20, size=SMALL)
    for k, key in enumerate(["fiscal year", "month", "cost center", "account"]):
        d.box(key, bx + 14, body_y + 34 + k * 28, bw - 28, 24, fill=WHITE, stroke=TEAL, size=SMALL, rounded=False,
              align="left")
    d.text("<b>BudgetAmount</b> is the sum of the first band's lines.", bx + 10, body_y + 34 + 4 * 28 + 4, bw - 20, 36,
           size=SMALL)
    # The roll-up arrow with its label above it, and the two arrows that stop before Budget.
    first_box, first_y, first_h = band_boxes[0]
    centre = first_y + first_h / 2
    d.arrow(first_box, budget, color=GRAY, exit=(1, 0.5), entry=(0, (centre - body_y) / body_h), width=2.5,
            meta="edgeStyle=none;")
    d.text("sum by fiscal year, month, cost center and account", left_w + 12, centre - 54, bx - left_w - 24, 48, size=SMALL,
           align="center", valign="bottom")
    stop_x = left_w + 112
    for box, by, bh in band_boxes[1:]:
        cy = by + bh / 2
        d.edge(box, d.anchor(stop_x, cy - 0.5), end="blockThin", color=CORAL, width=2.5, exit=(1, 0.5), entry=(0, 0.5),
               meta="edgeStyle=none;")
        d.box("", stop_x + 2, cy - 16, 5, 32, fill=CORAL, stroke=CORAL, rounded=False)
        d.text("<b>not in Budget</b>", stop_x + 14, cy - 10, 100, 20, size=SMALL, color=CORAL, valign="middle")
    bottom = left_bottom + 16
    kit.callout(d, "Adding BudgetLine to Budget counts the first band twice: Budget already holds its sum. Compare at the "
                   "grain of Budget, or aggregate BudgetLine to that grain first, and keep the second band as a "
                   "\"No cost center\" bucket.", 0, bottom, 860, color="amber")
    d.text(f"<i>Counts are for fiscal {year}. Across all years BudgetLine has {ex4['line_blank']:,} rows with no "
           f"CostCenterID, {ex4['line_opex']:,} operating expense and {ex4['line_bs']:,} balance sheet, which is the count "
           f"Step 4 reads.</i>", 0, bottom + 62, 860, 36, size=SMALL, color=GRAY)
    return d


# -- IF-02-6-A: the Count helper column on PurchaseInvoice -----------------------------------------------------------

def if_02_6_a() -> Diagram:
    """PurchaseInvoice with the Count helper column filtered to repeated invoice numbers (Exercise 2.6, Step 2)."""
    data = ctx.data()
    n_columns = _check_columns(data, "PurchaseInvoice", {"A": "PurchaseInvoiceID", "B": "InvoiceNumber", "C": "InvoiceDate",
                                                          "G": "SupplierID", "J": "GrandTotal"}, free="N")
    first, last, total = data.q("SELECT MIN(PurchaseInvoiceID), MAX(PurchaseInvoiceID), COUNT(*) FROM PurchaseInvoice")[0]
    assert (first, last) == (1, total), "row numbers assume PurchaseInvoiceID 1..n in worksheet order"
    found = data.q("SELECT PurchaseInvoiceID, InvoiceNumber, InvoiceDate, SupplierID, GrandTotal, "
                   "(SELECT COUNT(*) FROM PurchaseInvoice q WHERE q.SupplierID = p.SupplierID AND q.InvoiceNumber = "
                   "p.InvoiceNumber) FROM PurchaseInvoice p ORDER BY PurchaseInvoiceID")
    repeats = [r for r in found if r[5] > 1]
    assert {r[5] for r in repeats} == {2}, "every repeated invoice number appears exactly twice"
    pairs = ctx.values("ch02.ex6g")["pairs"]
    assert len(repeats) == 2 * len(pairs), "the figure and the guide count the same pairs"
    # The Table is filtered to Count above 1 and sorted by SupplierID and InvoiceNumber (Step 2b): Excel puts the sorted
    # rows back into the rows that the filter leaves visible, so the row numbers stay in order.
    slots = [r[0] + 1 for r in repeats]
    ordered = sorted(repeats, key=lambda r: (r[3], r[1]))                # a stable sort keeps a pair in worksheet order
    rows = [(str(slot), [str(r[0]), r[1], r[2], str(r[3]), _general(r[4]), str(r[5])]) for slot, r in zip(slots, ordered)]
    headers = ["PurchaseInvoiceID", "InvoiceNumber", "InvoiceDate", "SupplierID", "GrandTotal", "Count"]
    letters = ["A", "B", "C", "G", "J", "N"]
    widths = [56, 150, 172, 120, 120, 130, 112]
    d = Diagram("The PurchaseInvoice Worksheet Filtered to Repeated Invoice Numbers")
    slot = rows[0][0]
    xl.formula_bar(d, 0, 0, 860, f"N{slot}", f"=COUNTIFS(G:G,G{slot},B:B,B{slot})")
    y0 = 40
    geo = _grid_rows(d, 0, y0, widths, rows, header=headers, letters=letters)
    count_col = 5
    _dropdown(d, geo[(0, count_col)])
    xl.emphasis(d, *xl.column_box(geo, count_col, len(rows) + 1))
    # A heavier rule between the pairs.
    for k in range(2, len(rows), 2):
        gx, gy, gw, gh = geo[(k + 1, 0)]             # the grid's row 0 is the header
        d.box("", 0, gy - 1, sum(widths), 2, fill=GRAY, stroke=GRAY, rounded=False)
    bottom = y0 + 22 + 24 * (len(rows) + 1)
    xl.sheet_tabs(d, 0, bottom + 8, xl.tabs_around("PurchaseInvoice", 3, 2), "PurchaseInvoice")
    xl.status_bar(d, 0, bottom + 36, 860, f"{len(rows)} of {total} records found")
    d.text(f"<i>Columns {_hidden_text(letters, n_columns)} are hidden. Filtered for a Count above 1, which leaves only the value 2, and "
           f"sorted by SupplierID and InvoiceNumber, so each of the {len(pairs)} pairs sits together. Outlined: the Count "
           f"column. Each pair shares a supplier and an invoice number but not the date or the amount. Blue row numbers "
           f"mark a filtered Table.</i>", 0, bottom + 68, 860, 52, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "IF-02-0-A": if_02_0_a,
    "IF-02-0-B": if_02_0_b,
    "IF-02-1-A": if_02_1_a,
    "IF-02-2-A": if_02_2_a,
    "IF-02-3-A": if_02_3_a,
    "IF-02-4-A": if_02_4_a,
    "IF-02-6-A": if_02_6_a,
}
