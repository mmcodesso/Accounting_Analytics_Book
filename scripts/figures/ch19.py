"""Chapter 19 figures (auditing the customer credits cycle).

Figure 19.1 maps the cycle's documents, who records each, its control points, and its postings; the postings and the
departments are asserted against the ledger and the documents. Figure 19.2 is a generic evaluation flow.
"""

from __future__ import annotations

from data import q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, HEAD, SMALL, WHITE,
                    Diagram)

BOTTOM, TOP, LEFT, RIGHT = (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)

CONTROLS = [
    ("C1", "Every credit rests on a return received outside customer service"),
    ("C2", "Credits approved within the approver's authority"),
    ("C3", "Credits at the invoice price, for no more than was shipped"),
    ("C4", "The credit approver does not handle that customer's cash"),
    ("C5", "A clawback for every credit line, at the accrual's rate"),
    ("C6", "Refunds approved within authority, outside customer service"),
    ("C7", "A refund only of a credit balance the customer has paid"),
    ("C8", "Refunds to the payer's own method or account, net of open balances"),
    ("C9", "Cash applied promptly to the remitting customer's invoices"),
]


def postings() -> dict[str, set[tuple[str, int]]]:
    """(side, account) pairs each document type posts, from the ledger."""
    out: dict[str, set[tuple[str, int]]] = {}
    for src, acct, d, c in q("""SELECT g.SourceDocumentType, a.AccountNumber, SUM(g.Debit), SUM(g.Credit) FROM GLEntry g
            JOIN Account a ON a.AccountID = g.AccountID WHERE g.SourceDocumentType IN ('CashReceipt', 'CashReceiptApplication',
            'SalesReturn', 'CreditMemo', 'SalesCommissionAdjustment', 'CustomerRefund') GROUP BY 1, 2"""):
        if d:
            out.setdefault(src, set()).add(("Dr", acct))
        if c:
            out.setdefault(src, set()).add(("Cr", acct))
    return out


def departments() -> dict[str, set[str]]:
    """Job titles of the people each document records, from the documents."""
    sql = {
        "CashReceipt": "SELECT DISTINCT e.JobTitle FROM CashReceipt t JOIN Employee e ON e.EmployeeID = t.RecordedByEmployeeID",
        "SalesReturn": "SELECT DISTINCT e.JobTitle FROM SalesReturn t JOIN Employee e ON e.EmployeeID = t.ReceivedByEmployeeID",
        "CreditMemo": "SELECT DISTINCT e.JobTitle FROM CreditMemo t JOIN Employee e ON e.EmployeeID = t.ApprovedByEmployeeID",
        "SalesCommissionAdjustment": "SELECT DISTINCT e.JobTitle FROM SalesCommissionAdjustment t JOIN Employee e ON e.EmployeeID = t.ApprovedByEmployeeID",
        "CustomerRefund": "SELECT DISTINCT e.JobTitle FROM CustomerRefund t JOIN Employee e ON e.EmployeeID = t.ApprovedByEmployeeID",
    }
    return {k: {r[0] for r in q(v)} for k, v in sql.items()}


def fig_19_01() -> Diagram:
    d = Diagram("The Customer Credits Cycle")
    post = postings()
    assert post["CashReceipt"] == {("Dr", 1010), ("Cr", 2060)}, post["CashReceipt"]
    assert post["CashReceiptApplication"] == {("Dr", 2060), ("Cr", 1020)}, post["CashReceiptApplication"]
    assert post["SalesReturn"] == {("Dr", 1040), ("Cr", 5010), ("Cr", 5020), ("Cr", 5030), ("Cr", 5040)}, post["SalesReturn"]
    assert post["CreditMemo"] == {("Dr", 4060), ("Dr", 4050), ("Dr", 2050), ("Cr", 1020), ("Cr", 2060)}, post["CreditMemo"]
    assert post["SalesCommissionAdjustment"] == {("Dr", 2034), ("Cr", 6290)}, post["SalesCommissionAdjustment"]
    assert post["CustomerRefund"] == {("Dr", 2060), ("Cr", 1010)}, post["CustomerRefund"]
    dept = departments()
    assert dept["CashReceipt"] <= {"Customer Service Manager", "Customer Service Representative"}
    assert dept["SalesReturn"] <= {"Warehouse Manager", "Inventory Specialist", "Shipping Clerk"}
    assert dept["CreditMemo"] <= {"Customer Service Manager", "Customer Service Representative"}
    assert dept["SalesCommissionAdjustment"] <= {"Customer Service Manager", "Customer Service Representative"}
    assert dept["CustomerRefund"] <= {"Accounting Manager", "Staff Accountant", "Administrative Specialist"}

    docs = [
        ("CashReceipt and its applications", "Customer service", "cash received and applied to invoices", ["C9"],
         "Receipt: Dr 1010, Cr <b>2060</b><br>Application: Dr <b>2060</b>, Cr 1020"),
        ("SalesReturn", "Warehouse", "goods received back", ["C1"],
         "Dr 1040 Inventory<br>Cr 5010–5040 Cost of goods sold"),
        ("CreditMemo", "Customer service", "credit approved", ["C2", "C3", "C4"],
         "Dr 4060, 4050, 2050<br>Cr 1020 or <b>2060</b>"),
        ("SalesCommission<br>Adjustment", "Customer service", "commission clawed back", ["C5"],
         "Dr 2034 Commission payable<br>Cr 6290 Commission expense"),
        ("CustomerRefund", "Accounting", "refund approved and paid", ["C6", "C7", "C8"],
         "Dr <b>2060</b><br>Cr 1010 Cash"),
    ]
    w, gap, y, h = 156, 20, 44, 92
    boxes, posts = [], []
    for i, (name, who, what, ctrl, entry) in enumerate(docs):
        x = i * (w + gap)
        boxes.append(d.box(f"<b>{name}</b><br><i>{what}</i>", x, y, w, h, fill=BLUE_TINT, stroke=BLUE, size=SMALL))
        d.text(f"<b>{who}</b>", x, y - 22, w - 8, 20, size=SMALL, color=GRAY, align="left", valign="bottom")
        for j, c in enumerate(ctrl):
            d.marker(c, x + w - 26 - 28 * (len(ctrl) - 1 - j), y + h - 14)
        posts.append(d.box(entry, x, 214, w, 76, fill=AMBER_TINT, stroke=AMBER, size=SMALL))
        d.arrow(boxes[-1], posts[-1], color=AMBER, dashed=True, exit=BOTTOM, entry=TOP)
    d.arrow(boxes[1], boxes[2], exit=RIGHT, entry=LEFT)
    d.arrow(boxes[2], boxes[3], exit=RIGHT, entry=LEFT)
    d.arrow(boxes[2], boxes[4], exit=(0.8, 0), entry=(0.5, 0), points=[(2 * (w + gap) + 0.8 * w, 8), (4 * (w + gap) + w / 2, 8)])
    d.arrow(boxes[0], boxes[2], exit=(0.5, 1), entry=(0.2, 1), points=[(w / 2, 160), (2 * (w + gap) + 0.2 * w, 160)],
            label="has the invoice been paid?")
    d.text("<b>Account 2060 Customer Deposits and Unapplied Cash</b> joins receipts, credits on paid invoices, and "
           "refunds: every receipt passes through it, and every refund is paid from it.", 0, 298, 860, 40, align="left")
    y0 = 350
    d.text("<b>Control points</b>", 0, y0, 860, 22, size=HEAD, align="left")
    for i, (c, text) in enumerate(CONTROLS):
        col, row = divmod(i, 5)
        x, yy = col * 440, y0 + 30 + row * 34
        d.marker(c, x, yy + 2)
        d.text(text, x + 32, yy, 388, 30, size=SMALL, align="left", valign="middle")
    d.line_sample(0, y0 + 210, 44, color=GRAY, end="blockThin")
    d.text("Document flow", 52, y0 + 200, 200, 20, size=SMALL, align="left")
    d.line_sample(260, y0 + 210, 44, color=AMBER, dashed=True, end="blockThin")
    d.text("Posting to the ledger", 312, y0 + 200, 250, 20, size=SMALL, align="left")
    return d


def fig_19_02() -> Diagram:
    d = Diagram("Evaluating a Control Deficiency")
    lw = 380
    steps = [
        "<b>Identify the deficiency</b>: a control that is missing, or one that did not operate as designed",
        "<b>Likelihood</b>: is a misstatement reasonably possible, whether or not one occurred?",
        "<b>Magnitude</b>: how large could it be, against materiality?",
        "<b>Compensating controls</b>: do other controls catch it, precisely enough?",
        "<b>Combine</b> the deficiencies that affect the same account or assertion",
    ]
    ids = []
    for i, text in enumerate(steps):
        ids.append(d.box(text, 0, i * 92, lw, 64, fill=WHITE, stroke=BLUE, stroke_width=1.5, align="left"))
        if i:
            d.arrow(ids[i - 1], ids[i], exit=BOTTOM, entry=TOP)
    outcomes = [
        ("<b>Material weakness</b>: a reasonable possibility that a material misstatement is not prevented or "
         "detected on time", CORAL_TINT, CORAL),
        ("<b>Significant deficiency</b>: less severe, but important enough to merit the attention of those "
         "who oversee financial reporting", AMBER_TINT, AMBER),
        ("<b>Deficiency</b>: reported to management, with the action that will fix it", GRAY_TINT, GRAY),
    ]
    oids = []
    for i, (text, fill, stroke) in enumerate(outcomes):
        oids.append(d.box(text, 470, 92 + i * 102, 390, 76, fill=fill, stroke=stroke, align="left"))
        d.arrow(ids[-1], oids[-1], exit=RIGHT, entry=LEFT, points=[(425, 400), (425, 130 + i * 102)])
    d.box("<b>Then report</b>: internal audit rates each finding, agrees on action plans with management, and "
          "monitors them until they are complete", 0, 476, 860, 56, fill=BLUE_TINT, stroke=BLUE, align="left")
    return d


FIGURES = {
    "fig-19-01-credits-cycle": fig_19_01,
    "fig-19-02-deficiency-evaluation": fig_19_02,
}
