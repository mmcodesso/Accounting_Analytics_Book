"""Figures of the appendix on publishing, securing, and sharing reports.

These figures were Chapter 16's until its security and sharing sections moved to the appendix. The
cost-center roles of Guided Tutorial A.1 were checked against Power BI Desktop 2.158's engine on a
reference model of the tutorial, and every value here is computed from the dataset.
"""

from __future__ import annotations

import excel as xl
import powerbi as pbi
from data import one, q
from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, CORAL, CORAL_TINT, GRAY, GRAY_TINT, RULE, SMALL, TEAL,
                    TEAL_TINT, WHITE, Diagram, esc)


def money(v: float) -> str:
    return pbi.amount(v) if abs(v) >= 0.005 else "0.00"


def mdy(s: str) -> str:
    return f"{int(s[5:7])}/{int(s[8:10])}/{s[:4]}"


def note(d: Diagram, text: str, y: float, h: float = 40) -> None:
    d.text(f"<i>{text}</i>", 0, y, 860, h, size=SMALL, color=GRAY)


# -- fig-a-01 --------------------------------------------------------------------------------

def fig_a_01() -> Diagram:
    d = Diagram("What the Security Rules Reach")

    def rule_tag(t, text):
        d.box(f"<b>Rule</b>: {esc(text)}", t.x, t.y - 26, t.w, 22, fill=AMBER_TINT, stroke=AMBER, size=SMALL,
              align="left", rounded=False)

    sec = pbi.model_table(d, "Security", 0, 30, ["UserPrincipalName", "CostCenterID"], w=170)
    d.text("Not related to any table; the rules read it, and its own rule shows each user only their rows.",
           0, sec.y + sec.h + 4, 170, 80, size=SMALL, color=GRAY)
    cc = pbi.model_table(d, "CostCenter", 250, 30, ["CostCenterID", "CostCenterName"], w=170)
    rule_tag(cc, "the user's cost centers")
    emp = pbi.model_table(d, "Employee", 250, 196, ["EmployeeID", "CostCenterID"], w=170)
    rule_tag(emp, "the user's cost centers")
    item = pbi.model_table(d, "Item", 250, 340, ["ItemID", "ItemGroup"], w=170)
    rule_tag(item, "user is in Security")
    facts = [("GLEntry", 0, ["CostCenterID"], "Income Statement, Budget", cc, "CostCenterID"),
             ("BudgetLine", 86, ["CostCenterID"], "Budget", cc, "CostCenterID"),
             ("LaborTimeEntry", 196, ["EmployeeID"], "Plant", emp, "EmployeeID"),
             ("SalesInvoiceLine", 300, ["ItemID"], "Sales and Discounts, Promotions, Margins", item, "ItemID"),
             ("ProductionCompletionLine", 386, ["ItemID"], "Plant (standard hours)", item, "ItemID")]
    for name, y, cols, pages, dim, key in facts:
        t = pbi.model_table(d, name, 520, y + 30, cols, w=190)
        pbi.relationship(d, dim.right(key), t.left(cols[0]), [(470, dim.rows[key]), (470, t.rows[cols[0]])])
        d.text(f"<b>Pages</b>: {esc(pages)}", 716, y + 30, 144, 50, size=SMALL)
    note(d, "Each rule filters its table and, through active relationships, the fact tables on the many side. "
            "A page shows only the rows its reader may see: the Income Statement of a department manager is that "
            "department's alone, and nothing on the page says so unless a card names the cost centers shown.", 470, 56)
    return d


# -- fig-a-02 --------------------------------------------------------------------------------

def fig_a_02() -> Diagram:
    d = Diagram("The Access Review")
    rows = q("SELECT cc.CostCenterName, cc.ManagerID, e.EmployeeName, e.JobTitle, e.EmploymentStatus, "
             "e.TerminationDate FROM CostCenter cc LEFT JOIN Employee e ON e.EmployeeID = cc.ManagerID "
             "ORDER BY cc.CostCenterName")
    terminated = [r[0] for r in rows if r[4] == "Terminated"]
    assert terminated == ["Executive", "Sales", "Warehouse"], terminated
    missing = q("SELECT EmployeeName, JobTitle FROM Employee WHERE JobTitle IN ('Sales Manager', 'Warehouse Manager') "
                "AND EmployeeID NOT IN (SELECT ManagerID FROM CostCenter) ORDER BY JobTitle")
    assert [m[1] for m in missing] == ["Sales Manager", "Warehouse Manager"]
    pbi.canvas(d, 0, 0, 860, 330)
    d.text("<b>Access Review</b>", 16, 12, 300, 20, size=SMALL, color=GRAY)
    widths = [170, 74, 140, 176, 124, 120]
    t = pbi.table_visual(d, 16, 36, ["CostCenterName", "ManagerID", "EmployeeName", "JobTitle", "EmploymentStatus",
                                     "TerminationDate"], widths,
                         [[r[0], str(r[1]), r[2], r[3], r[4], mdy(r[5]) if r[5] else ""] for r in rows])
    for i, r in enumerate(rows):
        if r[4] == "Terminated":
            x0, y0, _, _ = t["geometry"][(i, 0)]
            xl.emphasis(d, x0, y0, sum(widths), pbi.ROW)
    rd = [i for i, r in enumerate(rows) if r[0] == "Research and Development"][0]
    x0, y0, _, _ = t["geometry"][(rd, 3)]
    d.box("", x0, y0, widths[3], pbi.ROW, fill="none", stroke=AMBER, stroke_width=2, dashed=True, rounded=False)
    y = t["bottom"] + 8
    d.text("<b>In the employee records but not managers of record</b>: "
           + "; ".join(f"{esc(n)}, {esc(j)}" for n, j in missing), 16, y, 828, 22, size=SMALL)
    note(d, "Outlined in red: cost centers whose manager of record has left. Dashed: a manager of record who is "
            "an analyst. Access built on this column would go to the wrong people.", 340)
    return d


# -- fig-a-03 --------------------------------------------------------------------------------

RULE_LINES = ["[CostCenterID] IN CALCULATETABLE (",
              "    VALUES ( Security[CostCenterID] ),",
              "    Security[UserPrincipalName] = USERPRINCIPALNAME ()",
              ")"]


def fig_a_03() -> Diagram:
    d = Diagram("The Manage Security Roles Dialog")
    d.box("", 0, 0, 860, 420, fill=WHITE, stroke=GRAY, stroke_width=2, rounded=False)
    d.text("<b>Manage security roles</b>", 16, 10, 400, 24, size=14)
    d.text("Create new security roles and use filters to define row-level data restrictions.", 16, 36, 700, 20,
           size=SMALL, color=GRAY)
    d.box("Close Dialog", 750, 10, 96, 24, fill=WHITE, stroke=RULE, size=SMALL)
    # Roles.
    d.text("<b>Roles</b>", 16, 70, 200, 20, size=SMALL)
    xl.button(d, 16, 94, 120, "New role")
    for i, (name, on) in enumerate([("Cost Center Managers", True), ("Finance", False)]):
        d.box(f"<b>{name}</b>" if on else name, 16, 130 + i * 30, 200, 26, fill=BLUE_TINT if on else WHITE,
              stroke=BLUE if on else RULE, size=SMALL, align="left", rounded=False)
    # Tables.
    d.text("<b>Tables</b>", 236, 70, 200, 20, size=SMALL)
    tables = ["Account", "BudgetLine", "CostCenter", "Customer", "Date", "Employee", "GLEntry", "Item",
              "LaborTimeEntry", "Security"]
    filtered = {"CostCenter", "Employee", "Item", "Security"}
    for i, name in enumerate(tables):
        on = name == "CostCenter"
        label = f"{esc(name)}&nbsp;&nbsp;<i>(filter)</i>" if name in filtered else esc(name)
        d.box(f"<b>{label}</b>" if on else label, 236, 94 + i * 26, 190, 24, fill=BLUE_TINT if on else WHITE,
              stroke=BLUE if on else RULE, size=SMALL, align="left", rounded=False)
    # Rules, in the DAX editor.
    d.text("<b>Rules</b>", 446, 70, 200, 20, size=SMALL)
    xl.button(d, 446, 94, 190, "Switch to default editor")
    d.box("", 446, 130, 398, 120, fill=WHITE, stroke=BLUE, rounded=False)
    for i, line in enumerate(RULE_LINES):
        d.text(pbi.highlight_dax(line), 452, 136 + i * 22, 386, 22, size=SMALL)
    d.text("A rule returns true or false for each row of the table; only the rows that return true stay visible "
           "to the role's members.", 446, 262, 398, 60, size=SMALL, color=GRAY)
    xl.button(d, 676, 380, 76, "Save", primary=True)
    xl.button(d, 760, 380, 76, "Close")
    note(d, "The real dialog marks a table that has a rule with an icon; the mock writes the word filter. The "
            "Cost Center Managers role is selected, and its rule on CostCenter is open in the DAX editor.", 430)
    return d


# -- fig-a-04 --------------------------------------------------------------------------------

def fig_a_04() -> Diagram:
    d = Diagram("The Package Viewed as Two Managers")
    sales = one("SELECT SUM(b.BudgetAmount) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
                "WHERE b.FiscalYear = 2026 AND b.CostCenterID = 2 AND a.AccountSubType = 'Operating Expense'")[0]
    act = one("SELECT SUM(g.Debit - g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
              "WHERE g.FiscalYear = 2026 AND g.CostCenterID = 2 AND a.AccountSubType = 'Operating Expense' "
              "AND g.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297')")[0]
    assert abs(sales - 2734179.05) < 0.01 and abs(act - 1018872.21) < 0.01
    wh = q("SELECT a.AccountSubType, SUM(g.Credit - g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
           "WHERE g.FiscalYear = 2026 AND g.CostCenterID = 3 AND a.AccountType IN ('Revenue', 'Expense') "
           "AND g.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297') GROUP BY 1")
    assert len(wh) == 1 and wh[0][0] == "Operating Expense"
    panels = [(0, "employee006@charlesriver.example", "Budget"), (436, "employee007@charlesriver.example",
                                                                   "Income Statement")]
    for x, user, page in panels:
        d.text(f"<b>{page}</b>, viewed as the {'Sales' if x == 0 else 'Warehouse'} Manager", x, 0, 424, 20,
               size=SMALL)
        pbi.canvas(d, x, 24, 424, 300)
        d.box(f"Viewing as <b>{user}</b> in the role <b>Cost Center Managers</b>", x + 8, 32, 316, 40,
              fill=AMBER_TINT, stroke=AMBER, size=SMALL, align="left", rounded=False)
        xl.button(d, x + 330, 40, 86, "Stop viewing")
        if x == 0:
            pbi.table_visual(d, x + 16, 86, ["CostCenterName", "Budget", "Actual", "Variance %"], [110, 92, 92, 84],
                             [["Sales", money(sales), money(act), f"{100 * (act - sales) / sales:.1f}%"]])
            pbi.card(d, x + 16, 170, 200, 64, "Cost centers shown", "Sales")
        else:
            pbi.table_visual(d, x + 16, 86, ["AccountSubType", "P&L Amount"], [200, 140],
                             [[wh[0][0], money(wh[0][1])]], total=["Net Income", money(wh[0][1])])
            pbi.card(d, x + 16, 194, 200, 64, "Cost centers shown", "Warehouse")
    note(d, "The bar names the user and the role while View as is on; its exact wording in Desktop may differ. "
            "The card is the only sign on each page that it shows part of the company.", 336)
    return d


# -- fig-a-05 --------------------------------------------------------------------------------

def fig_a_05() -> Diagram:
    d = Diagram("From Desktop to the Report's Readers")
    desk = d.box("<b>Power BI Desktop</b><br>Charles River Reports.pbix", 0, 40, 180, 64, fill=WHITE, stroke=BLUE,
                 stroke_width=2, size=SMALL)
    ws = d.box("", 250, 0, 330, 250, fill=BLUE_TINT, stroke=BLUE, rounded=False)
    d.text("<b>Workspace in the Power BI service</b>", 258, 6, 314, 20, size=SMALL)
    d.box("<b>Semantic model</b> and <b>report</b>", 262, 32, 306, 30, fill=WHITE, stroke=BLUE, size=SMALL)
    d.box("<b>Admin, Member, Contributor</b><br>edit the content; row-level security does not apply",
          262, 74, 306, 50, fill=WHITE, stroke=GRAY, size=SMALL, align="left")
    d.box("<b>Viewer</b><br>reads; row-level security applies", 262, 134, 306, 44, fill=WHITE, stroke=TEAL,
          size=SMALL, align="left")
    d.text("Roles get their members under <b>Security</b>; <b>Test as role</b> checks them.", 262, 186, 306, 44,
           size=SMALL)
    d.arrow(desk, ws, exit=(1, 0.5), entry=(0, 0.3), label="Home > Publish")
    app = d.box("", 650, 0, 210, 250, fill=WHITE, stroke=BLUE, stroke_width=2, rounded=False)
    d.text("<b>App</b>", 658, 6, 194, 20, size=SMALL)
    d.box("<b>Audience: managers</b><br>the department report", 660, 34, 190, 60, fill=TEAL_TINT, stroke=TEAL,
          size=SMALL, align="left")
    d.box("<b>Audience: finance</b><br>the full package, with the Income Statement and Validation pages",
          660, 104, 190, 80, fill=BLUE_TINT, stroke=BLUE, size=SMALL, align="left")
    d.text("Readers need Pro or Premium Per User, unless the workspace is on a capacity.", 660, 192, 190, 56,
           size=SMALL)
    d.arrow(ws, app, exit=(1, 0.3), entry=(0, 0.3), label="Create app")
    # Refresh.
    src = d.box("<b>CharlesRiver.xlsx</b><br>on a local drive", 0, 300, 180, 50, fill=WHITE, stroke=GRAY, size=SMALL)
    gw = d.box("<b>On-premises data gateway</b>", 250, 300, 200, 50, fill=WHITE, stroke=GRAY, size=SMALL)
    d.arrow(src, gw, exit=(1, 0.5), entry=(0, 0.5))
    d.arrow(gw, ws, exit=(0.5, 0), entry=(0.3, 1), label="scheduled refresh")
    d.box("Or keep the workbook in OneDrive for work or school or SharePoint, refreshed without a gateway.",
          0, 370, 450, 44, fill=GRAY_TINT, stroke=RULE, size=SMALL, align="left")
    # Publish to web.
    pub = d.box("<b>Publish to web</b><br>a public link, no sign-in, all the model's data; no row-level security",
                650, 300, 210, 80, fill=CORAL_TINT, stroke=CORAL, stroke_width=2, size=SMALL, align="left")
    d.text("<b>Anyone on the internet: avoid for financial data</b>", 560, 384, 300, 20, size=SMALL, color=CORAL,
           align="right")
    d.arrow(ws, pub, exit=(1, 0.95), entry=(0, 0.4), points=[(615, 237), (615, 332)], label="Publish to web")
    note(d, "Sharing the .pbix file itself bypasses all of this: whoever opens it in Desktop sees every row.", 424)
    return d


FIGURES = {
    "fig-a-01-rls-reach": fig_a_01,
    "fig-a-02-access-review": fig_a_02,
    "fig-a-03-manage-roles": fig_a_03,
    "fig-a-04-view-as": fig_a_04,
    "fig-a-05-sharing-paths": fig_a_05,
}
