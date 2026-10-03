"""The instructor notes of the appendix on publishing and security: the values each note states, and the
claims its wording makes.

The security table of Guided Tutorial A.1 (tbl-a-02) and the sign-in names the tutorial types are book
constants; the notes test them against the employee records. What a role sees is reproduced in SQL: the
rule on CostCenter filters the ledger and the budget lines by their cost center, the rule on Employee
filters the labor time by the employee's cost center, and the rule on Item shows every item to a listed
user and none to anyone else, as the CR16 reference model did in Power BI Desktop's engine.
"""

from __future__ import annotations

from notes import note

TUTORIAL1 = "appendices/a-publishing-security/_tutorial-01.qmd"
EXERCISES = "appendices/a-publishing-security/_exercises.qmd"
MCQ = "appendices/a-publishing-security/_multiple-choice.qmd"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]

# tbl-a-02, the security table as the controller approved it (UserPrincipalName, CostCenterID), in its order.
SECURITY = [("employee001@charlesriver.example", 1), ("employee006@charlesriver.example", 2),
            ("employee007@charlesriver.example", 3), ("employee004@charlesriver.example", 4),
            ("employee010@charlesriver.example", 5), ("employee005@charlesriver.example", 6),
            ("employee011@charlesriver.example", 7), ("employee012@charlesriver.example", 9),
            ("employee014@charlesriver.example", 10)]
# The users the tutorial views the report as (Steps 7 and 8): the Sales, Warehouse, and Production Managers,
# and the terminated employee recorded as manager of Sales, who is not in the security table.
SALES, WAREHOUSE, PRODUCTION = ("employee006@charlesriver.example", "employee007@charlesriver.example",
                                "employee004@charlesriver.example")
FORMER = "employee083@charlesriver.example"
PRODUCT_REVENUE = ("4010", "4020", "4030", "4040")       # the revenue the commission budget is planned on
COMMISSION = "6290"


def word(n: int) -> str:
    return WORDS[n] if n < len(WORDS) else f"{n:,}"


def employees(d) -> dict[int, dict]:
    return {r[0]: dict(id=r[0], name=r[1], title=r[2], cc=r[3], status=r[4], terminated=r[5], email=r[6])
            for r in d.q("SELECT EmployeeID, EmployeeName, JobTitle, CostCenterID, EmploymentStatus, TerminationDate, "
                         "Email FROM Employee")}


def by_email(d) -> dict[str, dict]:
    return {e["email"].lower(): e for e in employees(d).values() if e["email"]}


def centers(d) -> dict[int, str]:
    return dict(d.q("SELECT CostCenterID, CostCenterName FROM CostCenter"))


def access_review(d) -> dict:
    """Step 1's review: each cost center's manager of record. A cost center is flagged when that manager has left or
    does not hold a manager's job; the actual manager of a flagged department is the active employee titled after it."""
    emp = employees(d)
    rows = []
    for cc, name, manager in d.q("SELECT CostCenterID, CostCenterName, ManagerID FROM CostCenter ORDER BY CostCenterID"):
        e = emp[manager]
        rows.append(dict(cc=cc, center=name, id=manager, name=e["name"], title=e["title"], status=e["status"],
                         terminated=e["terminated"], own_cc=e["cc"],
                         flagged=e["status"] != "Active" or not e["title"].endswith("Manager")))
    actual = []
    for r in rows:
        if r["status"] == "Terminated":
            found = [e for e in emp.values() if e["title"] == f"{r['center']} Manager" and e["status"] == "Active"]
            if found:
                actual.append(dict(center=r["center"], cc=r["cc"], id=found[0]["id"], name=found[0]["name"],
                                   title=found[0]["title"], n=len(found), own_cc=found[0]["cc"]))
    return dict(rows=rows, flagged=[r for r in rows if r["flagged"]], others=[r for r in rows if not r["flagged"]],
                terminated=[r for r in rows if r["status"] == "Terminated"], actual=actual,
                managers_of_record={r["id"] for r in rows})


def users(d) -> list[dict]:
    """The security table's users, each with the employee whose Email is the user's name (None if no one's is)."""
    emails = by_email(d)
    return [dict(upn=upn, cc=cc, employee=emails.get(upn.lower())) for upn, cc in SECURITY]


def gl_by_type(d, ccs: list[int]) -> dict[str, float]:
    """Debits less credits of fiscal year C by AccountType and AccountSubType, without the closes, on the ledger lines
    of these cost centers (a role's filter reaches GLEntry through CostCenter, so lines without one drop out)."""
    where = f"AND g.CostCenterID IN ({','.join(map(str, ccs))})" if ccs else "AND 0"
    return {(t, s): b for t, s, b in d.q(
        f"SELECT a.AccountType, a.AccountSubType, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a "
        f"ON a.AccountID = g.AccountID WHERE substr(g.PostingDate, 1, 4) = ? AND {d.no_closes()} {where} GROUP BY 1, 2",
        str(d.C))}


def company_net_income(d) -> float:
    rows = {(t, s): b for t, s, b in d.q(
        f"SELECT a.AccountType, a.AccountSubType, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a "
        f"ON a.AccountID = g.AccountID WHERE substr(g.PostingDate, 1, 4) = ? AND {d.no_closes()} GROUP BY 1, 2", str(d.C))}
    return -sum(b for (t, _), b in rows.items() if t in ("Revenue", "Expense"))


def budget(d, ccs: list[int] | None, accounts: list[str] | None = None, subtype: str | None = None) -> float:
    """BudgetLine amounts of fiscal year C, for these cost centers (None: all lines, with or without one)."""
    sql = ("SELECT COALESCE(SUM(b.BudgetAmount), 0) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
           "WHERE b.FiscalYear = ?")
    if ccs is not None:
        sql += f" AND b.CostCenterID IN ({','.join(map(str, ccs)) or 'NULL'})"
    if accounts is not None:
        sql += f" AND a.AccountNumber IN ({','.join(accounts)})"
    if subtype is not None:
        sql += f" AND a.AccountSubType = '{subtype}'"
    return d.one(sql, d.C)


def invoice_revenue(d, services: bool = True) -> float:
    return d.one("SELECT SUM(l.LineTotal) FROM SalesInvoiceLine l JOIN SalesInvoice s ON s.SalesInvoiceID = l.SalesInvoiceID "
                 "JOIN Item i ON i.ItemID = l.ItemID WHERE substr(s.InvoiceDate, 1, 4) = ?"
                 + ("" if services else " AND i.ItemGroup <> 'Services'"), str(d.C))


def flexed(d, ccs: list[int] | None, rate_ccs: list[int] | None) -> float:
    """Tutorial 15.2's Flexed Budget over the operating expense of these cost centers: the commission budget is replaced
    by the budget's commission rate (over the lines `rate_ccs` can see) times actual product revenue."""
    commission = budget(d, ccs, [COMMISSION], "Operating Expense")
    static = budget(d, ccs, subtype="Operating Expense")
    if not commission:                       # IF ( NOT ISBLANK ( CommissionBudget ), ... ) adds nothing
        return static
    rate = budget(d, rate_ccs, [COMMISSION]) / budget(d, rate_ccs, list(PRODUCT_REVENUE))
    return static - commission + rate * invoice_revenue(d, services=False)


def standard_hours_to_cutoff(d, last: str | None) -> float | None:
    """Tutorial 15.3's Standard Hours to Cut-off for fiscal year C: the standard hours of the completions up to the last
    day with time records the viewer can see (blank when the viewer sees no time records)."""
    if last is None:
        return None
    return d.one("SELECT SUM(l.QuantityCompleted * i.StandardLaborHoursPerUnit) FROM ProductionCompletionLine l "
                 "JOIN ProductionCompletion p ON p.ProductionCompletionID = l.ProductionCompletionID "
                 "JOIN Item i ON i.ItemID = l.ItemID WHERE substr(p.CompletionDate, 1, 4) = ? AND p.CompletionDate <= ?",
                 str(d.C), last)


def view_as(d, upn: str) -> dict:
    """What the role Cost Center Managers shows a user in fiscal year C."""
    ccs = [cc for u, cc in SECURITY if u == upn]
    names = centers(d)
    emp = by_email(d).get(upn.lower())
    gl = gl_by_type(d, ccs)
    rev = -sum(b for (t, _), b in gl.items() if t == "Revenue")
    exp = sum(b for (t, _), b in gl.items() if t == "Expense")
    marks = ",".join(map(str, ccs)) or "NULL"
    last = d.one(f"SELECT MAX(l.WorkDate) FROM LaborTimeEntry l JOIN Employee e ON e.EmployeeID = l.EmployeeID "
                 f"WHERE e.CostCenterID IN ({marks})")
    hours = d.one(f"SELECT SUM(l.RegularHours + l.OvertimeHours) FROM LaborTimeEntry l JOIN Employee e "
                  f"ON e.EmployeeID = l.EmployeeID WHERE e.CostCenterID IN ({marks}) AND l.LaborType <> 'NonManufacturing' "
                  f"AND substr(l.WorkDate, 1, 4) = ?", str(d.C))
    std = standard_hours_to_cutoff(d, last)
    budget_types = {r[0] for r in d.q(f"SELECT DISTINCT a.AccountSubType FROM BudgetLine b JOIN Account a "
                                      f"ON a.AccountID = b.AccountID WHERE b.FiscalYear = ? AND b.CostCenterID IN ({marks})",
                                      d.C)}
    return dict(upn=upn, ccs=ccs, centers=[names[cc] for cc in ccs], title=emp["title"] if emp else None,
                budget=budget(d, ccs, subtype="Operating Expense"), actual=gl.get(("Expense", "Operating Expense"), 0.0),
                flexed=flexed(d, ccs, ccs), rev=rev, exp=exp, ni=rev - exp, last=last, hours=hours, std=std,
                ratio=hours / std if hours and std else None, budget_types=budget_types,
                employees=d.one(f"SELECT COUNT(*) FROM Employee WHERE CostCenterID IN ({marks})"))


@note("appendix_a.t1", TUTORIAL1)
def t1(d, claim):
    review = access_review(d)
    others = review["others"]
    claim(all(r["status"] == "Active" and r["title"].endswith("Manager") and r["own_cc"] == r["cc"] for r in others),
          "the other cost centers' managers of record are active managers of their own departments")
    claim(all(a["n"] == 1 for a in review["actual"]), "one active employee holds each actual manager's title")
    us = users(d)
    claim(all(u["employee"] is not None for u in us), "every address in the security table is an employee's Email")
    claim(all(u["employee"]["status"] == "Active" and u["employee"]["cc"] == u["cc"] for u in us if u["employee"]),
          "every user is an active employee whose own CostCenterID is the cost center the table gives them")
    company = company_net_income(d)
    s, w, p = view_as(d, SALES), view_as(d, WAREHOUSE), view_as(d, PRODUCTION)
    # The Sales Manager.
    claim(len(s["ccs"]) == 1, "the Sales Manager is mapped to one cost center (sees it only)")
    full_row = flexed(d, s["ccs"], None)      # the same row of the Budget page without a role
    claim(abs(s["flexed"] - full_row) < 0.005, "the Sales row's flexed budget is unchanged under the role")
    revenue = invoice_revenue(d)
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l LEFT JOIN Item i ON i.ItemID = l.ItemID "
                "WHERE i.ListPrice IS NULL") == 0,
          "every invoice line's item is in the model's Item table (items with a ListPrice), so a listed user sees all sales")
    claim(s["last"] is None, "no employee of the Sales Manager's cost center records labor time, so the Plant page is blank")
    # The Warehouse Manager.
    claim(not w["hours"], "the Warehouse's employees record no manufacturing time in the year (Plant hours blank)")
    overall = standard_hours_to_cutoff(d, d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry"))
    claim(w["std"] is not None and abs(w["std"] - overall) < 0.005, "the Warehouse Manager still sees the full standard hours")
    # The Production Manager.
    claim(len(p["ccs"]) == 1, "the Production Manager is mapped to one cost center")
    claim(p["budget_types"] == {"COGS"}, "the Manufacturing cost center has COGS budget lines only")
    claim(p["budget"] == 0 and p["actual"] == 0, "the Production Manager's Budget page (operating expense) is empty")
    # The former employee, and no role.
    claim(FORMER not in {u for u, _ in SECURITY}, "the former employee is not in the security table")
    claim(any(r["id"] == by_email(d)[FORMER]["id"] and r["cc"] in s["ccs"] for r in review["terminated"]),
          "the former employee is the terminated manager of record of the Sales Manager's cost center")
    n_centers = d.one("SELECT COUNT(DISTINCT CostCenterName) FROM CostCenter")
    return dict(flagged=review["flagged"], others=others, n_others=word(len(others)), actual=review["actual"],
                user_ids=[u["employee"]["id"] for u in us], s=s, w=w, p=p, company=company, revenue=revenue,
                times=s["ni"] / company,
                customers=d.one("SELECT COUNT(*) FROM Customer"), former=FORMER.split("@")[0],
                n_centers=word(n_centers))


@note("appendix_a.ex2", EXERCISES)
def ex2(d, claim):
    emp = employees(d)
    names = centers(d)
    mapped = {cc for _, cc in SECURITY}
    unmapped = [cc for cc in sorted(names) if cc not in mapped]
    claim(len(unmapped) == 1, "one cost center has no row in the security table")
    manager = d.one("SELECT ManagerID FROM CostCenter WHERE CostCenterID = ?", unmapped[0])
    title = emp[manager]["title"]
    upns = [u for u, _ in SECURITY]
    claim(len(set(upns)) == len(upns), "no user is mapped to more than one cost center")
    us = users(d)
    claim(all(u["employee"] is not None and u["employee"]["status"] == "Active" for u in us),
          "every name matches the Email of an active employee")
    claim(all(u["employee"]["cc"] == u["cc"] for u in us if u["employee"]),
          "each user is in the cost center the table gives them, so no user is flagged")
    return dict(center=names[unmapped[0]], cc=unmapped[0], an="an" if title[0] in "AEIOU" else "a", title=title,
                users=word(len(set(upns))), ccs=word(len(mapped)),
                matches=[(u["employee"]["id"], u["employee"]["title"]) for u in us],
                n_employees=len(emp))


@note("appendix_a.mcq", MCQ)
def mcq(d, claim):
    review = access_review(d)
    claim(len(review["terminated"]) >= 2, "several managers of record are terminated")
    claim(all(a["id"] not in review["managers_of_record"] for a in review["actual"]),
          "the actual Sales and Warehouse Managers are not managers of record")
    claim(len(review["actual"]) >= 1, "some departments' actual managers are not recorded")
    return dict(terminated=[r["id"] for r in review["terminated"]], actual=review["actual"])
