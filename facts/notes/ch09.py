"""Chapter 9's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

from notes import note

EXERCISES = "chapters/09-sql-essentials/_exercises.qmd"
MCQ = "chapters/09-sql-essentials/_multiple-choice.qmd"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
# The account types in the order of the chart, and the subtypes Exercise 9.1's note names (a selection, so it says "including").
TYPES = ["Asset", "Liability", "Equity", "Revenue", "Expense"]
SUBTYPES = ["Header", "Current Asset", "Fixed Asset", "Contra Fixed Asset", "Contra Current Asset", "Current Liability",
            "Long-Term Liability", "Operating Revenue", "Contra Revenue", "COGS", "Operating Expense", "Closing"]
# The variance descriptions of 5060's PurchaseInvoice postings, with the side each posts to.
PPV = [("unf", "Record unfavorable purchase variance", "debit"), ("fav", "Record favorable purchase variance", "credit"),
       ("tax", "Record nonrecoverable purchase tax", "debit")]
OPEN_STATUSES = ["Released", "In Progress", "Completed"]          # Exercise 9.4's order: the work order's lifecycle
SHIPMENT_STATUSES = ["Delivered", "In Transit"]
CLOCK_STATUSES = ["Approved", "Pending"]


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def article(title: str) -> str:
    return ("an " if title[0] in "AEIOU" else "a ") + title


def anomalies(d, kind: str) -> list[int]:
    """The primary keys the generator's AnomalyLog lists for one anomaly type."""
    keys = d.anomalies(kind)
    if keys is None:
        raise FileNotFoundError(f"no AnomalyLog beside {d.path}")
    return keys


def account_name(d, number: str) -> str:
    return d.one("SELECT AccountName FROM Account WHERE AccountNumber = ?", number)


# --- Exercise 9.1 --------------------------------------------------------------------------------

@note("ch09.ex1", EXERCISES)
def ex1(d, claim):
    accounts = [dict(id=r[0], number=r[1], name=r[2], type=r[3], subtype=r[4], parent=r[5], normal=r[6], active=r[7],
                     postings=r[8]) for r in d.q(
        "SELECT a.AccountID, a.AccountNumber, a.AccountName, a.AccountType, a.AccountSubType, a.ParentAccountID, "
        "a.NormalBalance, a.IsActive, (SELECT COUNT(*) FROM GLEntry g WHERE g.AccountID = a.AccountID) "
        "FROM Account a ORDER BY a.AccountNumber")]
    by_id = {a["id"]: a for a in accounts}
    claim({a["type"] for a in accounts} == set(TYPES), "the chart has the five account types the note lists")
    types = [(t, sum(1 for a in accounts if a["type"] == t)) for t in TYPES]
    subtypes = {s: sum(1 for a in accounts if a["subtype"] == s) for s in {a["subtype"] for a in accounts}}
    claim(all(subtypes.get(s, 0) > 0 for s in SUBTYPES), "every subtype the note names is in use")
    headers = [a for a in accounts if a["subtype"] == "Header"]
    top = [a for a in headers if a["parent"] is None]
    subs = [dict(number=a["number"], name=a["name"], parent=by_id[a["parent"]]["number"]) for a in headers
            if a["parent"] is not None]
    claim(len(subs) == 2, "two header accounts have a parent (the wording pairs them with 'and')")
    claim(all(by_id[a["parent"]]["subtype"] == "Header" and by_id[a["parent"]]["parent"] is None
              for a in headers if a["parent"] is not None),
          "the sub-headers sit directly under top-level headers, so the chart has two levels of headers")
    claim(all(a["postings"] == 0 for a in headers), "no header account has a posting")
    opposite = [a for a in accounts if (a["type"] in ("Asset", "Expense") and a["normal"] == "Credit")
                or (a["type"] in ("Liability", "Equity", "Revenue") and a["normal"] == "Debit")]
    assets = [a for a in opposite if a["type"] == "Asset"]
    depreciation = [a for a in assets if a["name"].startswith("Accumulated Depreciation")]
    asset_other = [a for a in assets if a not in depreciation]
    equity = [a for a in opposite if a["type"] == "Equity"]
    revenue = [a for a in opposite if a["type"] == "Revenue"]
    claim({a["type"] for a in opposite} == {"Asset", "Equity", "Revenue"},
          "the accounts with an opposite normal balance are assets, equity, and revenue accounts")
    claim(all(a["subtype"].startswith("Contra") for a in opposite), "every account with an opposite normal balance is a contra account")
    claim(len(asset_other) == 1 and len(equity) == 1 and len(revenue) == 2,
          "one contra asset besides the accumulated depreciation, one contra equity account, and two contra revenue accounts")
    inactive = [a for a in accounts if not a["active"]]
    claim(all(a["postings"] == 0 for a in inactive), "no inactive account has a posting")
    clearing, variance = d.account("1090"), d.account("5080")
    sources = {(r[0], r[1]): r[2] for r in d.q(
        "SELECT g.SourceDocumentType, COALESCE(j.EntryType, ''), SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g "
        "LEFT JOIN JournalEntry j ON g.SourceDocumentType = 'JournalEntry' AND j.JournalEntryID = g.SourceDocumentID "
        "WHERE g.AccountID = ? GROUP BY 1, 2", clearing)}
    claim(sources.get(("PayrollSummary", ""), 0) > 0 and sources.get(("JournalEntry", "Factory Overhead"), 0) > 0,
          "manufacturing payroll and factory overhead entries are charged to 1090")
    claim(sources.get(("ProductionCompletion", ""), 0) < 0 and sources.get(("WorkOrderClose", ""), 0) < 0,
          "1090 is cleared by production completions (to inventory) and work order closes")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'WorkOrderClose'", variance) > 0
          and by_id[variance]["subtype"] == "COGS", "work order closes post to 5080, a cost of goods sold account")
    claim(by_id[d.account("1030")]["postings"] == 0, "1030 has no postings")
    claim(not by_id[d.account("4070")]["active"], "4070 is inactive")
    return dict(n=len(accounts), types=types, n_subtypes=word(len(subtypes)).capitalize(),
                subtypes=[(s, subtypes[s]) for s in SUBTYPES], headers=len(headers), n_top=word(len(top)),
                top=[a["number"] for a in top], subs=subs, n_opposite=len(opposite),
                asset_other=asset_other, depreciation=[a["number"] for a in depreciation], equity=equity, revenue=revenue,
                inactive=inactive, n_inactive=len(inactive), clearing=clearing, clearing_name=account_name(d, "1090"),
                variance_name=account_name(d, "5080"))


# --- Exercise 9.2 --------------------------------------------------------------------------------

@note("ch09.ex2", EXERCISES)
def ex2(d, claim):
    ppv = d.account("5060")
    types = {r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? AND FiscalYear = ?", ppv, d.C)}
    claim(types == {"PurchaseInvoice", "JournalEntry"}, f"fiscal {d.C}'s postings to 5060 come from PurchaseInvoice and JournalEntry")
    je = d.q("SELECT VoucherNumber, Debit, Credit FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
             "AND SourceDocumentType = 'JournalEntry'", ppv, d.C)
    claim(len(je) == 1, "one JournalEntry row")
    close, debit, credit = je[0]
    claim(close in d.closes_of(d.C), "the JournalEntry row is a year-end close")
    claim(debit == 0 and credit > 0, "the close is a credit")
    rows = {r[0]: dict(n=r[1], debits=r[2], credits=r[3], amount=r[4] + r[5]) for r in d.q(
        "SELECT Description, COUNT(*), SUM(Debit > 0), SUM(Credit > 0), ROUND(SUM(Debit), 2), ROUND(SUM(Credit), 2) "
        "FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'PurchaseInvoice' GROUP BY 1", ppv, d.C)}
    claim(set(rows) == {text for _, text, _ in PPV}, "the PurchaseInvoice postings carry the three descriptions")
    claim(all(rows[text]["n"] == rows[text][side + "s"] for _, text, side in PPV),
          "unfavorable variances and purchase tax are debits, favorable variances credits")
    net = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                "AND SourceDocumentType = 'PurchaseInvoice'", ppv, d.C)
    claim(abs(net - credit) < 0.005, "the net of the PurchaseInvoice postings equals the close, which clears the account")
    lines = d.q("SELECT g.Description, g.Debit - g.Credit, pil.Quantity, pil.UnitCost, pol.UnitCost FROM GLEntry g "
                "JOIN PurchaseInvoiceLine pil ON pil.PILineID = g.SourceLineID "
                "JOIN PurchaseOrderLine pol ON pol.POLineID = pil.POLineID WHERE g.AccountID = ? AND g.FiscalYear = ? "
                "AND g.SourceDocumentType = 'PurchaseInvoice' AND g.Description LIKE '%purchase variance'", ppv, d.C)
    claim(len(lines) == rows[PPV[0][1]]["n"] + rows[PPV[1][1]]["n"]
          and all(abs(r[1] - round(r[2] * (r[3] - r[4]), 2)) < 0.011 for r in lines),
          "each variance is the invoice price against the purchase-order price, times the quantity")
    # A handful of one-cent variances on lines billed at the order price come from rounding (both sides); allow them.
    claim(all(r[3] < r[4] or (r[3] == r[4] and abs(r[1]) <= 0.01) for r in lines if r[1] < 0),
          "a credit means the supplier billed below the order price (apart from one-cent roundings at the order price)")
    grni = d.q("SELECT g.Debit - g.Credit, pil.Quantity, pol.UnitCost FROM GLEntry g "
               "JOIN PurchaseInvoiceLine pil ON pil.PILineID = g.SourceLineID "
               "JOIN PurchaseOrderLine pol ON pol.POLineID = pil.POLineID WHERE g.AccountID = ? AND g.FiscalYear = ? "
               "AND g.SourceDocumentType = 'PurchaseInvoice'", d.account("2020"), d.C)
    claim(len(grni) > 0 and all(abs(r[0] - round(r[1] * r[2], 2)) < 0.011 for r in grni),
          "the invoice clears goods received not invoiced (2020) at the order price of the goods received")
    top = [dict(amount=r[0], date=r[1], voucher=r[2]) for r in d.q(
        "SELECT Debit, PostingDate, VoucherNumber FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
        "AND Description = ? ORDER BY Debit DESC LIMIT 4", ppv, d.C, PPV[0][1])]
    claim(top[0]["amount"] > top[1]["amount"] > top[2]["amount"] > top[3]["amount"],
          "the three largest unfavorable variances have no ties")
    return dict(account=ppv, name=account_name(d, "5060"), close=close, close_amount=credit,
                pi_rows=sum(r["n"] for r in rows.values()), **{key: rows[text] for key, text, _ in PPV}, net=net, top=top)


# --- Exercise 9.3 --------------------------------------------------------------------------------

@note("ch09.ex3", EXERCISES)
def ex3(d, claim):
    items = d.q("SELECT ItemCode, ItemName, ItemGroup, ROUND(StandardCost - StandardConversionCost, 2), "
                "ROUND(StandardDirectLaborCost + StandardVariableOverheadCost + StandardFixedOverheadCost, 2) = "
                "ROUND(StandardConversionCost, 2), ROUND(StandardDirectLaborCost / StandardLaborHoursPerUnit, 2), "
                "StandardConversionCost FROM Item WHERE SupplyMode = 'Manufactured' ORDER BY StandardConversionCost DESC")
    groups = {}
    for r in items:
        groups[r[2]] = groups.get(r[2], 0) + 1
    claim(all(r[4] for r in items), "the component check returns no rows")
    rates = [r[5] for r in items]
    claim(len(set(rates)) >= len(items) / 2, "labor rates are item-specific, not one plant rate")
    claim(items[2][6] > items[3][6], "the three highest conversion costs are not tied with the fourth")
    top_groups = {r[2] for r in items[:10]}
    claim(len(top_groups) == 1, "the top ten items by conversion cost are in one item group")
    return dict(n=len(items), groups=sorted(groups.items(), key=lambda kv: -kv[1]),
                material_low=min(r[3] for r in items), material_high=max(r[3] for r in items),
                rate_low=min(rates), rate_high=max(rates),
                top=[dict(code=r[0], name=r[1], cost=r[6]) for r in items[:3]], top_group=top_groups.pop())


# --- Exercise 9.4 --------------------------------------------------------------------------------

@note("ch09.ex4", EXERCISES)
def ex4(d, claim):
    end = f"{d.C}-12-31"
    claim(d.one("SELECT COUNT(*) FROM WorkOrder WHERE substr(WorkOrderNumber, 4, 4) <> substr(ReleasedDate, 1, 4)") == 0,
          "every WorkOrderNumber carries the year of its ReleasedDate")
    rows = d.q("SELECT WorkOrderNumber, Status, ReleasedDate, DueDate, CompletedDate FROM WorkOrder "
               "WHERE ClosedDate IS NULL ORDER BY DueDate, WorkOrderNumber")
    claim({r[1] for r in rows} == set(OPEN_STATUSES), "the open work orders are Released, In Progress, or Completed")
    status = {s: sum(1 for r in rows if r[1] == s) for s in OPEN_STATUSES}
    claim(all(r[2][:4] == str(d.C) for r in rows), f"every open work order is a {d.C} work order")
    claim(all((r[4] is None) == (r[1] != "Completed") for r in rows),
          "the released and in-progress work orders have no CompletedDate, and the completed ones have one")
    due = [r for r in rows if r[3] <= end]
    due_status = sorted(((s, sum(1 for r in due if r[1] == s)) for s in {r[1] for r in due}), key=lambda kv: -kv[1])
    claim(due[0][3] < due[1][3] < due[2][3] < due[3][3], "the four oldest due dates are distinct (no ties for the oldest three)")
    claim(due[0][1] == "Released", "the oldest is still Released")
    released = sum(1 for r in due if r[1] == "Released")
    claim(200 <= released < 1000, "hundreds of released work orders are past due")
    return dict(end=end, n=len(rows), status=status, not_completed=status["Released"] + status["In Progress"],
                released_low=min(r[2] for r in rows), released_high=max(r[2] for r in rows),
                due=len(due), due_status=due_status,
                oldest=dict(number=due[0][0], released=due[0][2], due=due[0][3]),
                next=[dict(number=r[0], due=r[3]) for r in due[1:3]])


# --- Exercise 9.5 --------------------------------------------------------------------------------

@note("ch09.ex5", EXERCISES)
def ex5(d, claim):
    end = f"{d.C}-12-31"
    status = dict(d.q("SELECT Status, COUNT(*) FROM Shipment GROUP BY 1"))
    claim(set(status) == set(SHIPMENT_STATUSES), "the shipment statuses are Delivered and In Transit")
    carriers = [r[0] for r in d.q("SELECT DISTINCT ShippedBy FROM Shipment ORDER BY 1")]
    n, low, high = d.q("SELECT COUNT(*), MIN(ShipmentDate), MAX(ShipmentDate) FROM Shipment WHERE TrackingNumber IS NULL")[0]
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE TRIM(TrackingNumber) = ''") == 0,
          "no tracking number is an empty string, so the NULLs are the blanks of the Excel filter")
    claim(d.one("SELECT MAX(ShipmentDate) FROM Shipment") == end, f"{end} is the last shipment date of the data")
    transit, oldest = d.q("SELECT COUNT(*), MIN(DeliveryDate) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", end)[0]
    later = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate >= ?", end)
    claim(later == 1, "one more In Transit shipment has a DeliveryDate on or after the last day")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate IS NULL") == 0,
          "every In Transit shipment has a DeliveryDate")
    return dict(end=end, status=[(s, status[s]) for s in SHIPMENT_STATUSES], carriers=carriers, n=n, low=low, high=high,
                transit=transit, oldest=oldest)


# --- Exercise 9.6 --------------------------------------------------------------------------------

@note("ch09.ex6", EXERCISES)
def ex6(d, claim):
    titles = dict(d.q("SELECT EmployeeID, JobTitle FROM Employee"))
    labor = [dict(id=r[0], employee=r[1], work_order=r[2], date=r[3], hours=r[4]) for r in d.q(
        "SELECT LaborTimeEntryID, EmployeeID, WorkOrderID, WorkDate, RegularHours + OvertimeHours FROM LaborTimeEntry "
        "WHERE LaborType = 'Direct Manufacturing' AND WorkOrderOperationID IS NULL ORDER BY LaborTimeEntryID")]
    employees = list(dict.fromkeys(r["employee"] for r in labor))
    claim(len(employees) >= 2, "the unlinked labor rows belong to more than one employee (the wording says 'employees ... are')")
    claim(len({titles[e] for e in employees}) == 1, "the employees on the unlinked labor rows share one job title")
    claim([r["id"] for r in labor] == anomalies(d, "invalid_direct_labor_operation_link"),
          "the unlinked labor rows are the planted invalid direct labor operation links")
    clock = dict(d.q("SELECT ClockStatus, COUNT(*) FROM TimeClockEntry GROUP BY 1"))
    claim(set(clock) == set(CLOCK_STATUSES), "ClockStatus has the values Approved and Pending")
    missing = d.q("SELECT TimeClockEntryID, EmployeeID, WorkDate, ClockStatus FROM TimeClockEntry "
                  "WHERE ClockOutTime IS NULL ORDER BY WorkDate")
    claim(len({r[1] for r in missing}) == 1, "the entries with no ClockOutTime are all for one employee")
    claim([r[2] for r in missing] == [f"{y}-01-01" for y in (d.F, d.P, d.C)],
          "the entries with no ClockOutTime are on January 1 of each year")
    claim(all(r[3] == "Pending" for r in missing), "the entries with no ClockOutTime are Pending")
    claim(sorted(r[0] for r in missing) == anomalies(d, "missing_clock_out"),
          "the entries with no ClockOutTime are the planted missing clock-outs")
    staff = d.q("SELECT TerminationDate IS NOT NULL, EmploymentStatus, IsActive, COUNT(*) FROM Employee GROUP BY 1, 2, 3")
    terminated = sum(r[3] for r in staff if r[0])
    claim(all(r[1] == "Terminated" and r[2] == 0 for r in staff if r[0]),
          "every employee with a TerminationDate is Terminated with IsActive 0")
    claim(all(r[1] != "Terminated" and r[2] == 1 for r in staff if not r[0]),
          "no employee without a TerminationDate is Terminated or inactive")
    return dict(n_labor=word(len(labor)), labor=labor, employees=employees,
                title=titles[employees[0]].lower() + "s", clock=[(s, clock[s]) for s in CLOCK_STATUSES],
                n_missing=word(len(missing)).capitalize(), clock_employee=missing[0][1],
                clock_title=article(titles[missing[0][1]]), terminated=word(terminated).capitalize())


# --- Multiple-choice answer key ------------------------------------------------------------------

@note("ch09.mcq", MCQ)
def mcq(d, claim):
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'WorkOrderClose'") > 0
          and d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'workorderclose'") == 0,
          "the stored value is WorkOrderClose, so the lowercase value matches nothing")
    return dict(variance=d.account("5080"))
