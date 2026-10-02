"""Chapter 17 figures (financial statements for a lender).

Figure 17.1 is an ER figure in Chapter 3's notation: its crow's feet are computed from the data,
and the table of postings below it is asserted against the ledger's postings to account 2040.
Figure 17.2 is generic and carries no values.
"""

from __future__ import annotations

from ch03 import legend, table as er_table
from data import q, relate, trace
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, BODY, GRAY, GRAY_TINT, HEAD, RULE, SMALL,
                    WHITE, Diagram)

BOTTOM, TOP, LEFT, RIGHT = (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)


def postings_2040() -> dict[tuple[str, str | None], str]:
    """The side of account 2040 that each kind of posting takes, from the ledger."""
    rows = q("""SELECT g.SourceDocumentType, je.EntryType, SUM(g.Debit), SUM(g.Credit)
        FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID
        LEFT JOIN JournalEntry je ON g.SourceDocumentType = 'JournalEntry'
            AND je.JournalEntryID = g.SourceDocumentID
        WHERE a.AccountNumber = 2040 GROUP BY 1, 2""")
    sides = {}
    for source, entry_type, debit, credit in rows:
        assert not (debit and credit), (source, entry_type, debit, credit)
        sides[(source, entry_type)] = "Debit" if debit else "Credit"
    return sides


def fig_17_01() -> Diagram:
    d = Diagram("How an Accrued Expense Is Recorded and Cleared")
    je = er_table(d, "JournalEntry", 24, 40, [("PK", "JournalEntryID"), ("", "EntryNumber"),
                                              ("", "PostingDate"), ("", "EntryType"),
                                              ("", "TotalAmount"), ("FK", "ReversesJournalEntryID")],
                  w=240)
    pil = er_table(d, "PurchaseInvoiceLine", 320, 40, [("PK", "PILineID"), ("FK", "PurchaseInvoiceID"),
                                                       ("FK", "AccrualJournalEntryID"), ("FK", "ItemID"),
                                                       ("", "LineTotal")],
                   w=250, focus=False, group="Procure-to-Pay")
    shp = er_table(d, "Shipment", 620, 40, [("PK", "ShipmentID"), ("", "ShipmentNumber"),
                                            ("", "ShipmentDate"), ("", "FreightCost")],
                   w=220, focus=False, group="Order-to-Cash")
    pi = er_table(d, "PurchaseInvoice", 320, 250, [("PK", "PurchaseInvoiceID"), ("", "InvoiceNumber"),
                                                   ("", "ReceivedDate")],
                  w=250, focus=False, group="Procure-to-Pay")
    gl = er_table(d, "GLEntry", 320, 420, [("PK", "GLEntryID"), ("", "PostingDate"), ("FK", "AccountID"),
                                           ("", "Debit"), ("", "Credit"), ("", "SourceDocumentType"),
                                           ("", "SourceDocumentID"), ("", "SourceLineID")], w=250)

    relate(d, "JournalEntry", "JournalEntryID", "JournalEntry", "ReversesJournalEntryID",
           je.rows["JournalEntryID"], je.rows["ReversesJournalEntryID"], exit=LEFT, entry=LEFT,
           points=[(8, je.cy("JournalEntryID")), (8, je.cy("ReversesJournalEntryID"))])
    relate(d, "JournalEntry", "JournalEntryID", "PurchaseInvoiceLine", "AccrualJournalEntryID",
           je.rows["JournalEntryID"], pil.rows["AccrualJournalEntryID"], color=AMBER, exit=RIGHT,
           entry=LEFT)
    relate(d, "PurchaseInvoice", "PurchaseInvoiceID", "PurchaseInvoiceLine", "PurchaseInvoiceID",
           pi.rows["PurchaseInvoiceID"], pil.rows["PurchaseInvoiceID"], exit=RIGHT, entry=RIGHT,
           points=[(594, pi.cy("PurchaseInvoiceID")), (594, pil.cy("PurchaseInvoiceID"))])
    lane = 392
    trace(d, "JournalEntry", "JournalEntryID", je.id, gl.id, exit=BOTTOM, entry=(0.2, 0),
          points=[(144, lane), (370, lane)])
    trace(d, "PurchaseInvoice", "PurchaseInvoiceID", pi.id, gl.id, exit=BOTTOM, entry=TOP)
    trace(d, "Shipment", "ShipmentID", shp.id, gl.id, exit=BOTTOM, entry=(0.8, 0),
          points=[(730, lane), (520, lane)])
    d.text("<i>An invoice's ledger rows carry the invoice line in SourceLineID, so each debit "
           "to 2040 leads back to the accrual it clears.</i>", 604, 440, 256, 80, size=SMALL,
           color=AMBER)
    legend(d, 0, 430, 290, trace_item=True, stacked=True)

    sides = postings_2040()
    rows = [
        ("Accrual entry", ("JournalEntry", "Accrual"),
         "Services received and not yet billed, at month-end"),
        ("Supplier invoice", ("PurchaseInvoice", None),
         "Clears the accrual its line refers to, up to the amount accrued"),
        ("Accrual Adjustment entry", ("JournalEntry", "Accrual Adjustment"),
         "Clears what remains of the accrual it reverses"),
        ("Shipment", ("Shipment", None), "Freight owed to carriers for the goods shipped"),
        ("Freight Settlement entry", ("JournalEntry", "Freight Settlement"),
         "Pays the carriers for the month's freight"),
        ("Opening entry", ("JournalEntry", "Opening"), "A balance with no document behind it"),
    ]
    assert set(sides) == {key for _, key, _ in rows}, sides
    settle_cash = q("""SELECT SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID
        JOIN JournalEntry je ON je.JournalEntryID = g.SourceDocumentID AND g.SourceDocumentType = 'JournalEntry'
        WHERE je.EntryType = 'Freight Settlement' AND a.AccountNumber = 1010""")[0][0]
    assert settle_cash and settle_cash > 0
    grid_rows = [(name, key[0], sides[key], meaning) for name, key, meaning in rows]
    d.text("<b>What posts to account 2040 Accrued Expenses</b>", 0, 668, 860, 22, size=HEAD,
           align="left")
    d.grid(0, 694, ["Posting", "Source table", "Side of 2040", "What it records"],
           [190, 150, 110, 410], grid_rows)
    return d


def fig_17_02() -> Diagram:
    d = Diagram("How a Year-End Adjustment Moves Across the Periods Presented")
    label_w, col_w, gap = 176, 128, 8
    heads = ["Retained earnings<br>1 January 2025", "Income<br>fiscal 2025",
             "Balance sheet<br>31 December 2025", "Income<br>fiscal 2026",
             "Balance sheet<br>31 December 2026"]
    xs = [label_w + 8 + i * (col_w + gap) for i in range(len(heads))]
    for x, head in zip(xs, heads):
        d.box(f"<b>{head}</b>", x, 0, col_w, 64, fill=BLUE, stroke=BLUE, color=WHITE, size=BODY)
    rows = [
        ("Item missed at the end of 2024", {0: "Adjusted", 1: "Reverses"}, [(0, 1)]),
        ("Item missed at the end of 2025", {1: "Adjusted", 2: "Adjusted", 3: "Reverses"}, [(2, 3)]),
        ("Item missed at the end of 2026", {3: "Adjusted", 4: "Adjusted"}, []),
    ]
    y = 76
    for label, cells, arrows in rows:
        d.box(f"<b>{label}</b>", 0, y, label_w, 50, fill=GRAY_TINT, stroke=RULE, align="left")
        ids = {}
        for i, x in enumerate(xs):
            text = cells.get(i)
            if text == "Adjusted":
                ids[i] = d.box("<b>Adjusted</b>", x, y, col_w, 50, fill=BLUE_TINT, stroke=BLUE)
            elif text == "Reverses":
                ids[i] = d.box("<b>Reverses</b>", x, y, col_w, 50, fill=AMBER_TINT, stroke=AMBER)
            else:
                ids[i] = d.box("No effect", x, y, col_w, 50, fill=WHITE, stroke=RULE, color=GRAY)
        for a, b in arrows:
            d.arrow(ids[a], ids[b], exit=RIGHT, entry=LEFT)
        y += 60
    d.text("Each missed item reverses in the next year. An error that recurs every year can leave "
           "income nearly right while the balance sheet stays wrong.", 0, y + 2, 860, 40,
           align="left")
    py = y + 60
    panels = [
        ("Correction of an error", BLUE_TINT, BLUE,
         "The facts existed at the year-end and were missed or misapplied. The correction goes "
         "to the period in which they existed: the prior year's figures are restated, and an "
         "earlier error enters opening retained earnings."),
        ("Change in estimate", AMBER_TINT, AMBER,
         "The year-end estimate was reasonable on the facts then available. A later difference "
         "goes to the period in which it becomes known, and to later periods if they are "
         "affected. Nothing is restated."),
    ]
    for i, (title, fill, stroke, body) in enumerate(panels):
        x = i * 440
        d.box("", x, py, 420, 136, fill=fill, stroke=stroke)
        d.text(f"<b>{title}</b>", x + 14, py + 10, 392, 22, size=HEAD, align="left")
        d.text(body, x + 14, py + 36, 392, 92, align="left", valign="top")
    return d


FIGURES = {
    "fig-17-01-accrual-trace": fig_17_01,
    "fig-17-02-adjustment-timeline": fig_17_02,
}
