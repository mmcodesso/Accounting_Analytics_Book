"""Chapter 2 figures."""

from __future__ import annotations

from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HEAD,
                    HIGHLIGHT, INK, RULE, ROW_H, SMALL, TEAL, TEAL_TINT, WHITE, Diagram, esc,
                    money)


def fig_02_01() -> Diagram:
    d = Diagram("The Spectrum of Data Structure")
    zones = [
        ("Structured Data", BLUE, WHITE, BLUE_TINT, BLUE,
         "Data organized into predefined rows and columns, with each column having a defined "
         "data type.",
         "The Charles River GLEntry table with columns for PostingDate, AccountID, Debit, Credit, "
         "SourceDocumentType, and FiscalPeriod. Each row is one posted ledger entry."),
        ("Semi-Structured Data", TEAL, WHITE, TEAL_TINT, TEAL,
         "Data with some organizational elements (tags, labels, hierarchy) but not in a strict "
         "row-and-column format.",
         "An XBRL financial filing with tagged data elements organized hierarchically, or a bank "
         "statement in PDF format containing embedded transaction tables."),
        ("Unstructured Data", HIGHLIGHT, INK, AMBER_TINT, AMBER,
         "Data with no predefined tabular format. Information is stored as free-form text, "
         "images, or documents.",
         "The text of a lease agreement, narrative disclosures in an annual report, email "
         "correspondence between auditors and clients, or scanned invoice images."),
    ]
    for i, (name, fill, color, tint, border, body, example) in enumerate(zones):
        x = i * 295
        d.header_box(name, x, 0, 270, 34, fill=fill, color=color)
        d.box(body, x, 34, 270, 72, fill=tint, stroke=RULE, align="left", valign="top",
              rounded=False)
        d.box(f"<b>Accounting example:</b> {example}", x, 118, 270, 104, stroke=border,
              stroke_width=1.5, align="left", valign="top")
    a, b = d.anchor(12, 244), d.anchor(847, 244)
    d.edge(a, b, start="block", end="block", color=GRAY)
    d.text("More structure", 0, 252, 200, 20, color=GRAY)
    d.text("Less structure", 660, 252, 200, 20, color=GRAY, align="right")
    d.text("<i>Excel, SQL, and Power BI are designed for structured data. The Charles River dataset "
           "is entirely structured.</i>", 0, 282, 860, 22, color=GRAY, align="center")
    return d


def fig_02_02() -> Diagram:
    d = Diagram("Sources of Accounting Data")
    sources = [
        ("General Ledger", BLUE, WHITE, BLUE_TINT, 0, 0,
         "Central repository of all financial transactions. Every debit and credit entry that "
         "affects the financial statements."),
        ("Sub-Ledgers", BLUE, WHITE, BLUE_TINT, 610, 0,
         "Detailed records for specific account categories such as accounts receivable, accounts "
         "payable, and inventory."),
        ("Trial Balance", TEAL, WHITE, TEAL_TINT, 0, 196,
         "Summary listing of all account balances at a point in time. Starting point for "
         "financial statement preparation."),
        ("ERP System", TEAL, WHITE, TEAL_TINT, 610, 196,
         "Integrated platform capturing financial, sales, purchasing, production, and HR data in "
         "a single database."),
        ("External Data Feeds", HIGHLIGHT, INK, AMBER_TINT, 305, 330,
         "Bank statements, market price feeds, credit ratings, tax rate tables, and industry "
         "benchmarking data from outside the organization."),
    ]
    hub = d.vertex(
        f'<font style="font-size:{HEAD}px"><b>Accounting<br>Analytics</b></font>',
        f"ellipse;whiteSpace=wrap;html=1;fillColor={BLUE};strokeColor={BLUE};fontColor={WHITE};"
        "fontSize=13;fontFamily=Helvetica;align=center;verticalAlign=middle;",
        330, 150, 200, 110)
    for name, fill, color, tint, x, y, text in sources:
        d.header_box(name, x, y, 250, 32, fill=fill, color=color)
        body = d.box(text, x, y + 32, 250, 82, fill=tint, stroke=RULE, align="left",
                     valign="top", rounded=False)
        src = d.container(x, y, 250, 114)
        if name == "External Data Feeds":
            d.arrow(src, hub, exit=(0.5, 0), entry=(0.5, 1))
        else:
            d.arrow(body if y else src, hub, exit=(1, 0.5) if x == 0 else (0, 0.5),
                    entry=(0, 0.5) if x == 0 else (1, 0.5))
    return d


def fig_02_03() -> Diagram:
    d = Diagram("Common Data Quality Problems")

    def panel(x: float, y: float, title: str, caption: str, headers: list[str],
              widths: list[float], rows: list[tuple], marks: set, label: str, note: str) -> None:
        d.header_box(title, x, y, 420, 30)
        d.text(f"<b>{caption}</b>", x, y + 34, 420, 18, size=SMALL, color=GRAY)
        d.grid(x, y + 56, headers, widths, rows, highlight=marks)
        top = y + 56 + ROW_H * (len(rows) + 1) + 8
        d.text(f'<b><font color="{CORAL}">{label}</font></b> {note}', x, top, 420, 56)

    def shipments(numbers: list[str], columns: str) -> list[tuple]:
        marks = ",".join("?" * len(numbers))
        rows = q(f"SELECT {columns} FROM Shipment WHERE ShipmentNumber IN ({marks}) "
                 "ORDER BY ShipmentNumber", *numbers)
        assert len(rows) == len(numbers), rows
        return rows

    miss = shipments(["SH-2024-000028", "SH-2024-000029", "SH-2024-000049"],
                     "ShipmentNumber, ShipmentDate, FreightCost, TrackingNumber")
    panel(0, 0, "Missing Values", "Charles River: Shipment table (Order-to-Cash)",
          ["ShipmentNumber", "ShipmentDate", "FreightCost", "TrackingNumber"], [115, 90, 80, 135],
          [(n, dt, money(f), t or "(blank)") for n, dt, f, t in miss],
          {(i, 3) for i, r in enumerate(miss, 1) if r[3] is None},
          "Completeness problem:",
          "TrackingNumber is blank, so there is no carrier record for these shipments.")

    dup = q("SELECT SupplierID, InvoiceNumber, InvoiceDate, GrandTotal FROM PurchaseInvoice "
            "WHERE SupplierID = 2 AND InvoiceNumber IN ('V0002-2024-000182', 'V0002-2024-000204') "
            "ORDER BY InvoiceDate")
    assert [r[1] for r in dup].count("V0002-2024-000182") == 2, dup
    panel(440, 0, "Duplicate Records", "Charles River: PurchaseInvoice table (Procure-to-Pay)",
          ["SupplierID", "InvoiceNumber", "InvoiceDate", "GrandTotal"], [80, 145, 95, 100],
          [(str(s), n, dt, money(t)) for s, n, dt, t in dup],
          {(i, 1) for i, r in enumerate(dup, 1) if r[1] == "V0002-2024-000182"},
          "Duplicate:",
          "The same supplier invoice number is recorded twice, with different dates and amounts. "
          "This is a duplicate-payment risk that requires investigation.")

    stat = shipments(["SH-2024-000001", "SH-2024-000004", "SH-2024-000038"],
                     "ShipmentNumber, ShipmentDate, Status, DeliveryDate")
    panel(0, 250, "Inconsistent Values", "Charles River: Shipment table (Order-to-Cash)",
          ["ShipmentNumber", "ShipmentDate", "Status", "DeliveryDate"], [120, 95, 95, 110],
          stat, {(i, 2) for i, r in enumerate(stat, 1) if r[2] == "In Transit"},
          "Consistency problem:",
          "These shipments are still marked In Transit, although their DeliveryDate passed years "
          "before the data was extracted.")

    out = shipments(["SH-2024-000001", "SH-2024-000002", "SH-2024-000003", "SH-2026-008319"],
                    "ShipmentNumber, WarehouseID, FreightCost")
    average, largest = one("SELECT AVG(FreightCost), MAX(FreightCost) FROM Shipment")
    assert out[-1][2] == largest, (out, largest)
    panel(440, 250, "Outliers", "Charles River: Shipment table (Order-to-Cash)",
          ["ShipmentNumber", "WarehouseID", "FreightCost"], [140, 120, 160],
          [(n, str(w), money(f)) for n, w, f in out], {(len(out), 2)},
          "Outlier:",
          f"A FreightCost of {money(largest)} is several times the average shipment (about "
          f"${round(average, -1):,.0f}). It may be a legitimate large or rush shipment, so "
          "investigate before treating it as an error.")
    return d


def fig_02_04() -> Diagram:
    d = Diagram("Messy Versus Tidy Data")
    budgets = q(
        "SELECT cc.CostCenterName, b.Month, b.BudgetAmount FROM Budget b "
        "JOIN CostCenter cc USING (CostCenterID) JOIN Account a USING (AccountID) "
        "WHERE b.FiscalYear = 2025 AND b.Month <= 3 AND a.AccountNumber IN (6010, 6030, 6240) "
        "ORDER BY cc.CostCenterID, b.Month")
    assert len(budgets) == 9, budgets
    months = {1: "January", 2: "February", 3: "March"}
    departments = list(dict.fromkeys(name for name, _, _ in budgets))
    amount = {(name, m): v for name, m, v in budgets}

    def cell(value, x, y, w, i, header=None):
        if header:
            return d.box(f"<b>{value}</b>", x, y, w, 28, fill=header, stroke=RULE, color=WHITE,
                         rounded=False)
        numeric = value.startswith("$")
        return d.box(esc(value), x, y, w, ROW_H, fill=WHITE if i % 2 == 0 else GRAY_TINT,
                     stroke=RULE, align="right" if numeric else "left", rounded=False)

    d.text(f'<font color="{CORAL}"><b>Messy (wide format)</b></font>', 0, 0, 480, 22, size=HEAD)
    widths, xs = [150, 110, 110, 110], [0, 150, 260, 370]
    for head, x, w, fill in zip(["Department", *months.values()], xs, widths,
                                [BLUE, CORAL, CORAL, CORAL]):
        cell(head, x, 26, w, 0, header=fill)
    for i, dept in enumerate(departments):
        y = 54 + i * ROW_H
        cell(dept, xs[0], y, widths[0], i)
        for m, x, w in zip(months, xs[1:], widths[1:]):
            cell(money(amount[(dept, m)]), x, y, w, i)
    d.box(f'<font color="{CORAL}"><b>Tidy data principles violated:</b></font><br>'
          "1. Month is stored in column headers, not in its own column.<br>"
          "2. Each row contains three observations (three months), not one.<br>"
          "This layout prevents direct use in PivotTables, SQL GROUP BY queries, or Power BI "
          "data models.", 510, 26, 350, 124, fill=CORAL_TINT, stroke=CORAL, align="left",
          valign="top")

    top = d.anchor(200, 136)
    bottom = d.anchor(200, 196)
    d.edge(top, bottom, end="block", color=TEAL, width=3)
    d.text(f'<font color="{TEAL}"><b>Reshape to tidy format</b></font>', 216, 152, 240, 22)

    d.text(f'<font color="{TEAL}"><b>Tidy (long format)</b></font>', 0, 206, 480, 22, size=HEAD)
    widths, xs = [150, 110, 140], [0, 150, 260]
    for head, x, w, fill in zip(["Department", "Month", "Budget Amount"], xs, widths,
                                [BLUE, TEAL, TEAL]):
        cell(head, x, 232, w, 0, header=fill)
    shown = [(dept, m) for dept in departments for m in months][:4]
    for i, (dept, m) in enumerate(shown):
        y = 260 + i * ROW_H
        for value, x, w in zip([dept, months[m], money(amount[(dept, m)])], xs, widths):
            cell(value, x, y, w, i)
    d.box(f"<i>... {len(budgets)} rows in all: {len(departments)} departments × 3 months</i>",
          0, 260 + 4 * ROW_H, 400, ROW_H, stroke=RULE, color=GRAY, rounded=False)
    d.box(f'<font color="{TEAL}"><b>Tidy data principles satisfied:</b></font><br>'
          "1. Each variable (Department, Month, Budget Amount) has its own column.<br>"
          "2. Each observation (one department in one month) has its own row.<br>"
          "3. This single table holds one type of observational unit (monthly budgets).",
          510, 232, 350, 136, fill=TEAL_TINT, stroke=TEAL, align="left", valign="top")
    d.text("<i>Amounts: Charles River Budget table, salaries expense budgets for fiscal year "
           "2025.</i>", 0, 392, 860, 20, size=SMALL, color=GRAY)
    return d


FIGURES = {
    "fig-02-01-spectrum-data-structure": fig_02_01,
    "fig-02-02-sources-accounting-data": fig_02_02,
    "fig-02-03-data-quality-problems": fig_02_03,
    "fig-02-04-messy-vs-tidy-data": fig_02_04,
}

