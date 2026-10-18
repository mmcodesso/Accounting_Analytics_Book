"""Chapter 9's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 9 is the first SQL chapter (DB Browser for SQLite, SELECT, WHERE and NULL on one table at a time), so, as in the Excel
chapters, the contexts do three jobs:

- they supply the values the tutorials' checkpoints show (the row counts the message pane reports, the variance postings, the
  largest closes), which no registered note covers,
- they supply what each exercise's steps need beyond its registered note (ch09.ex1 to ch09.ex6): above all the result of each
  wrong variant a guide names (an OR without parentheses, a comparison with NULL, a LIKE that matches too much), run read-only,
  so the symptom a guide describes is the symptom the data gives,
- they check, with claim(), every table and column the guides name and every statement about the data that another dataset
  could falsify, so a roll flags the wording instead of leaving it stale.

Keys: ch09.chapter (the chapter note and its three tutorials) and ch09.g1 to ch09.g6 (the exercises; each is used next to the
registered note ch09.ex1 to ch09.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter09-exercises-sql (Ex 9.1.sql to Ex 9.6.sql).

The SQL a guide quotes is the solution scripts' own text (the check verifies it); the numbers beside it come from here.
"""

from __future__ import annotations

import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "09-sql-essentials"
DECK = REPO / "slides" / "chapter-09" / "index.qmd"
THRESHOLD = 1000                                  # Tutorial 9.3, Step 4: ABS(TotalVarianceAmount) > 1000
TOP = 10                                          # Tutorial 9.3, Step 1: LIMIT 10

SCHEMA = {
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType", "ParentAccountID",
                "NormalBalance", "IsActive"],
    "GLEntry": ["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "FiscalYear", "VoucherNumber",
                "SourceDocumentType", "Description"],
    "WorkOrderClose": ["WorkOrderCloseID", "WorkOrderID", "CloseDate", "MaterialVarianceAmount", "DirectLaborVarianceAmount",
                       "OverheadVarianceAmount", "ConversionVarianceAmount", "TotalVarianceAmount"],
    "WorkOrder": ["WorkOrderNumber", "Status", "ReleasedDate", "DueDate", "CompletedDate", "ClosedDate", "PlannedQuantity"],
    "Item": ["ItemCode", "ItemName", "ItemGroup", "SupplyMode", "StandardCost", "StandardLaborHoursPerUnit",
             "StandardDirectLaborCost", "StandardVariableOverheadCost", "StandardFixedOverheadCost", "StandardConversionCost"],
    "Shipment": ["ShipmentID", "ShipmentNumber", "ShipmentDate", "DeliveryDate", "ShippedBy", "TrackingNumber", "Status"],
    "LaborTimeEntry": ["LaborTimeEntryID", "EmployeeID", "WorkOrderID", "WorkDate", "RegularHours", "OvertimeHours",
                       "LaborType", "WorkOrderOperationID"],
    "WorkOrderOperation": ["WorkOrderOperationID"],
    "TimeClockEntry": ["TimeClockEntryID", "EmployeeID", "WorkDate", "ClockInTime", "ClockOutTime", "RegularHours",
                       "OvertimeHours", "ClockStatus"],
    "Employee": ["EmployeeID", "EmployeeName", "JobTitle", "EmploymentStatus", "TerminationDate", "IsActive"],
}


# --- helpers -------------------------------------------------------------------------------------------------------

def need(d, claim, *tables: str) -> None:
    """Claims that each table and the columns the guides name are in the database."""
    schema(d, claim, {t: SCHEMA[t] for t in tables})


def rows(d, sql: str, *args) -> int:
    """The number of rows a query returns: what the message pane reports."""
    return d.one(f"SELECT COUNT(*) FROM ({sql})", *args)


def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise \d+\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import package
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/09-sql-essentials/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 9\b")
    letters, _ = package.answer_key(comment)
    key = {i: a for i, a in enumerate(letters, 1)}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def and_list(items) -> str:
    items = [str(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    return items[0] + " and " + items[1] if len(items) == 2 else ", ".join(items[:-1]) + ", and " + items[-1]


# --- the chapter note and its tutorials ------------------------------------------------------------------------------

def tutorial_91(d, claim) -> dict:
    var, clearing = d.account("5080"), d.account("1090")
    n_close = d.one("SELECT COUNT(*) FROM WorkOrderClose")
    exact = d.one("SELECT COUNT(*) FROM WorkOrderClose WHERE ROUND(MaterialVarianceAmount + ConversionVarianceAmount "
                  "- TotalVarianceAmount, 2) <> 0")
    raw = d.one("SELECT COUNT(*) FROM WorkOrderClose WHERE MaterialVarianceAmount + ConversionVarianceAmount "
                "- TotalVarianceAmount <> 0")
    claim(exact == 0, "the material and conversion parts of every work order close add up to its total to the cent")
    claim(raw > 0, "without ROUND, the check column is not exactly zero in some rows (binary fractions of a cent)")
    claim(var != 5080 and clearing != 1090, "the AccountIDs of 1090 and 5080 differ from their account numbers")
    gl_n = d.one("SELECT COUNT(*) FROM GLEntry")
    claim(gl_n > 800_000, "the ledger holds more than 800,000 rows, as the opening scenario says")
    claim(d.one("SELECT AccountName FROM Account WHERE AccountNumber = 5080") == "Manufacturing Variance"
          and d.one("SELECT AccountName FROM Account WHERE AccountNumber = 1090") == "Manufacturing Cost Clearing",
          "5080 is the manufacturing variance and 1090 the manufacturing cost clearing account")
    return dict(no=dict(variance=5080, clearing=1090), accounts=d.one("SELECT COUNT(*) FROM Account"), clearing_id=clearing, variance_id=var, n_close=n_close,
                raw_rows=raw, gl_n=gl_n, tables=d.one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"))


def tutorial_92(d, claim) -> dict:
    var, year, prior = d.account("5080"), d.C, d.P
    postings = d.q("SELECT SourceDocumentType, COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? GROUP BY 1", var, year)
    by_type = dict(postings)
    claim(set(by_type) == {"WorkOrderClose", "JournalEntry"}, f"fiscal {year}'s postings to 5080 come from WorkOrderClose and one JournalEntry")
    claim(by_type.get("JournalEntry") == 1, "exactly one journal entry posts to 5080 in the year: the close")
    close = d.q("SELECT VoucherNumber, Credit, Debit, PostingDate, Description FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                "AND SourceDocumentType = 'JournalEntry'", var, year)[0]
    claim(close[0] in d.closes_of(year) and close[1] > 0 and close[2] == 0, "that journal entry is the year-end close, a credit")
    like = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND VoucherNumber LIKE ?", var, year, f"JE-{year}-%")
    claim(like == 1, "the voucher pattern JE-<year>-% finds the same single posting")
    net = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ?", var, year)
    claim(abs(net) < 0.005, "the postings of the whole year net to zero, because the close clears the account")
    wo_docs = d.one("SELECT COUNT(DISTINCT SourceDocumentID) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? "
                    "AND SourceDocumentType = 'WorkOrderClose'", var, year)
    claim(wo_docs == d.one("SELECT COUNT(*) FROM WorkOrderClose WHERE CloseDate BETWEEN ? AND ?", f"{year}-01-01", f"{year}-12-31")
          and wo_docs < by_type["WorkOrderClose"] <= 2 * wo_docs,
          "the year's WorkOrderClose postings to 5080 come from the year's closes, most of which post more than one row "
          "(material and conversion), so the rows are postings, not closes")
    wrong = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? OR FiscalYear = ?", var, prior, year)
    right = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND (FiscalYear = ? OR FiscalYear = ?)", var, prior, year)
    claim(wrong > 10 * right, "an OR without parentheses returns the whole year's ledger, more than ten times the intended rows")
    claim(d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate IS NULL AND SUBSTR(WorkOrderNumber, 4, 4) = ?", year) == 0
          and d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate IS NULL AND SUBSTR(WorkOrderNumber, 4, 4) = ?", str(year)) > 0,
          "SUBSTR's text year equals no open work order as a number and every open work order as text")
    open_n = d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate IS NULL")
    claim(d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate = NULL") == 0, "a comparison with NULL finds no work order")
    return dict(year=year, prior=prior, rows=sum(by_type.values()), wo_rows=by_type["WorkOrderClose"], wo_docs=wo_docs, close=close[0],
                close_credit=close[1], close_date=close[3], close_text=close[4], wrong=wrong, right=right, open_n=open_n,
                substr_text=d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate IS NULL AND SUBSTR(WorkOrderNumber, 4, 4) = ?", str(year)),
                statuses=[(r[0], r[1]) for r in d.q("SELECT Status, COUNT(*) FROM WorkOrder WHERE ClosedDate IS NULL GROUP BY 1 "
                                                    "ORDER BY COUNT(*) DESC")])


def tutorial_93(d, claim) -> dict:
    lo, hi = f"{d.C}-01-01", f"{d.C}-12-31"
    base = "FROM WorkOrderClose WHERE CloseDate BETWEEN ? AND ?"
    n_year = d.one(f"SELECT COUNT(*) {base}", lo, hi)
    top = [dict(id=r[0], total=r[1], overhead=r[2], share=r[3], parts=r[4] + r[5]) for r in d.q(
        f"SELECT WorkOrderCloseID, TotalVarianceAmount, OverheadVarianceAmount, "
        f"ROUND(OverheadVarianceAmount / TotalVarianceAmount, 2), MaterialVarianceAmount, DirectLaborVarianceAmount {base} "
        f"ORDER BY TotalVarianceAmount DESC LIMIT {TOP}", lo, hi)]
    claim(all(t["overhead"] > t["parts"] for t in top), "in each of the ten largest closes, overhead exceeds material and labor together")
    claim(all(t["share"] > 0.7 for t in top), "overhead is more than 70 percent of each of the ten largest closes")
    over = sum(1 for t in top if t["share"] > 0.8)
    claim(0 < over < TOP, "more than four-fifths overhead in some, not all, of the ten largest closes (most of them)")
    asc = [r[0] for r in d.q(f"SELECT TotalVarianceAmount {base} ORDER BY TotalVarianceAmount LIMIT {TOP}", lo, hi)]
    claim(all(a < 0 for a in asc) and abs(asc[0]) < min(t["total"] for t in top), "the ascending ranking starts with favorable (negative) totals, smaller than the unfavorable ones")
    thr, fav = d.q(f"SELECT COUNT(*), SUM(TotalVarianceAmount < 0) {base} AND ABS(TotalVarianceAmount) > {THRESHOLD}", lo, hi)[0]
    claim(0.2 < thr / n_year < 0.3, "the review threshold keeps about a quarter of the year's closes")
    claim(fav < thr * 0.15, "only a small share (under a seventh) of the closes above the threshold are favorable")
    one_way = d.one(f"SELECT COUNT(*) {base} AND TotalVarianceAmount > {THRESHOLD}", lo, hi)
    claim(one_way < thr, "a test without ABS misses the favorable closes above the threshold")
    return dict(n_year=n_year, top=top, top_max=top[0]["total"], top_min=top[-1]["total"], over=over, share_low=min(t["share"] for t in top),
                share_high=max(t["share"] for t in top), asc_low=asc[0], asc_high=asc[-1], thr=thr, fav=fav, thr_share=thr / n_year,
                one_way=one_way, threshold=THRESHOLD, top_n=TOP)


@context("ch09.chapter")
def chapter(d, claim):
    need(d, claim, *SCHEMA)
    t1, t2, t3 = tutorial_91(d, claim), tutorial_92(d, claim), tutorial_93(d, claim)
    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    claim(n_q == 15, "the chapter has fifteen multiple-choice questions (the key's rationales and the note's plan use their numbers)")
    # Question 2, 3, 15: the values a SELECT without a table returns, and the lowercase value that matches nothing.
    q15 = d.q("SELECT 7 / 2, 7 / 2.0, '2026' = 2026")[0]
    claim(tuple(q15) == (3, 3.5, 0), "7 / 2 is 3, 7 / 2.0 is 3.5 and the text '2026' is not equal to the number 2026")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'workorderclose'") == 0
          and d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType LIKE 'workorderclose'") > 0,
          "'workorderclose' matches nothing with = and every WorkOrderClose posting with LIKE")
    claim(len(d.q("SELECT AccountNumber AccountName FROM Account LIMIT 1")[0]) == 1, "the missing comma runs and returns one column")
    return dict(f=d.F, p=d.P, y=d.C, n=d.N, n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(),
                n_questions=n_q, longest_correct=and_list(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3,
                q15=list(q15), version="3.13.1")


# --- Exercise 9.1: the chart of accounts -----------------------------------------------------------------------------------

@context("ch09.g1")
def g1(d, claim):
    need(d, claim, "Account", "GLEntry")
    n = d.one("SELECT COUNT(*) FROM Account")
    clearing_id, variance_id = d.account("1090"), d.account("5080")
    claim(d.one("SELECT COUNT(*) FROM Account a JOIN Account b ON a.AccountID < b.AccountID AND a.AccountNumber > b.AccountNumber") > 0,
          "AccountID order is not account-number order, so no sorting rule can be read from AccountID (the guide says so)")
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountID < ? AND AccountNumber > 1090", clearing_id) > 0
          and d.one("SELECT COUNT(*) FROM Account WHERE AccountID < ? AND AccountNumber > 5080", variance_id) > 0,
          "accounts with lower AccountIDs than 1090 and 5080 carry higher account numbers, the example the guide gives")
    before = d.q("SELECT AccountID, AccountNumber FROM Account WHERE AccountID < ? AND AccountNumber > 1090 "
                 "ORDER BY AccountID DESC LIMIT 1", clearing_id)[0]
    pairs = rows(d, "SELECT DISTINCT AccountType, AccountSubType FROM Account")
    subtypes = d.one("SELECT COUNT(DISTINCT AccountSubType) FROM Account")
    claim(d.one("SELECT COUNT(DISTINCT AccountType) FROM Account") == 5, "the chart has five account types")
    claim(rows(d, "SELECT DISTINCT AccountType, AccountSubType, AccountName FROM Account") == n,
          "adding AccountName to the DISTINCT list returns every account, so DISTINCT removes nothing")
    claim(d.one("SELECT COUNT(DISTINCT AccountType) FROM Account WHERE AccountSubType = 'Header'") == 5,
          "every account type has a Header subtype")
    header_lower = d.one("SELECT COUNT(*) FROM Account WHERE AccountSubType = 'header'")
    headers = d.one("SELECT COUNT(*) FROM Account WHERE AccountSubType = 'Header'")
    claim(header_lower == 0 and headers > 0, "'header' in small letters matches no account, because = compares text exactly")
    parent_eq = d.one("SELECT COUNT(*) FROM Account WHERE AccountSubType = 'Header' AND ParentAccountID = NULL")
    parent_is = d.one("SELECT COUNT(*) FROM Account WHERE AccountSubType = 'Header' AND ParentAccountID IS NULL")
    claim(parent_eq == 0 and parent_is > 0, "ParentAccountID = NULL finds no header and IS NULL finds the top-level headers")
    credit_half = d.one("SELECT COUNT(*) FROM Account WHERE AccountType IN ('Asset', 'Expense') AND NormalBalance = 'Credit'")
    debit_half = d.one("SELECT COUNT(*) FROM Account WHERE AccountType IN ('Liability', 'Equity', 'Revenue') AND NormalBalance = 'Debit'")
    claim(credit_half > 0 and debit_half > 0, "both halves of the opposite-balance test find accounts")
    unparenthesized = d.one(
        "SELECT COUNT(*) FROM Account WHERE AccountType = 'Asset' OR AccountType = 'Expense' AND NormalBalance = 'Credit' "
        "OR AccountType = 'Liability' OR AccountType = 'Equity' OR AccountType = 'Revenue' AND NormalBalance = 'Debit'")
    claim(unparenthesized > 3 * (credit_half + debit_half), "types listed with OR and no parentheses return a large share of the chart")
    like_all = [dict(number=r[0], name=r[1], active=r[2]) for r in d.q(
        "SELECT AccountNumber, AccountName, IsActive FROM Account WHERE AccountName LIKE '%manufacturing%' ORDER BY AccountNumber")]
    like_active = [a for a in like_all if a["active"]]
    claim(len(like_all) == len(like_active) + 1, "without IsActive = 1 the pattern also returns exactly one inactive account")
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountName = '%manufacturing%'") == 0, "= with a wildcard pattern matches nothing")
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountName LIKE '%factory%' AND IsActive = 0") == 1,
          "the inactive factory overhead account does not contain the word manufacturing, so the LIKE test cannot find it")
    claim(d.one("SELECT COUNT(*) FROM Account WHERE AccountNumber IN (1090, 5080) AND AccountName LIKE '%manufacturing%' AND IsActive = 1") == 2,
          "1090 and 5080 are both active accounts whose names mention manufacturing")
    no = dict(clearing=1090, variance=5080, allowance=1030, discount=4070, equipment=1185)
    names = {1090: "Manufacturing Cost Clearing", 5080: "Manufacturing Variance", 1030: "Allowance for Doubtful Accounts",
             4070: "Sales Discounts", 1185: "Manufacturing Equipment"}
    claim(all(d.one("SELECT AccountName FROM Account WHERE AccountNumber = ?", num) == name for num, name in names.items()),
          "the accounts the guide names by number have the names the guide gives them")
    claim(d.one("SELECT MAX(AccountID) FROM Account") < d.one("SELECT MIN(AccountNumber) FROM Account WHERE AccountSubType = 'Header'"),
          "every AccountID is smaller than every header account number, so a posting test written with account numbers returns nothing")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", d.account("1090")) > 0, "account 1090 has postings, so the test can return rows")
    sources = [r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? ORDER BY 1", d.account("1090"))]
    return dict(n=n, no=no, sources_1090=sources, before=dict(id=before[0], number=before[1]), pairs=pairs, n_sub=subtypes, header_lower=header_lower, parent_eq=parent_eq, parent_is=parent_is,
                credit_half=credit_half, debit_half=debit_half, unparenthesized=unparenthesized, like_all=like_all,
                like_active=like_active, like_text="; ".join(f"{a['number']} {a['name']}" for a in like_active), n_like_all=len(like_all), n_like_active=len(like_active),
                header_postings=d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (SELECT AccountID FROM Account WHERE AccountSubType = 'Header')"),
                inactive_postings=d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID IN (SELECT AccountID FROM Account WHERE IsActive = 0)"),
                allowance_postings=d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", d.account("1030")),
                clearing_id=d.account("1090"), variance_id=d.account("5080"))


# --- Exercise 9.2: the purchase price variance ---------------------------------------------------------------------------------

@context("ch09.g2")
def g2(d, claim):
    need(d, claim, "Account", "GLEntry")
    ppv, year = d.account("5060"), d.C
    claim(ppv != 5060, "the AccountID of 5060 differs from its account number")
    as_id = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = 5060")
    claim(as_id == 0, "no ledger row has the account number 5060 as its AccountID")
    year_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ?", ppv, year)
    all_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", ppv)
    claim(all_rows > year_rows, "the account has postings in other fiscal years, so a missing year filter returns more rows")
    like_fav = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description LIKE '%favorable%'", ppv, year)
    unf = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description = 'Record unfavorable purchase variance'", ppv, year)
    fav = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description = 'Record favorable purchase variance'", ppv, year)
    claim(like_fav == unf + fav, "LIKE '%favorable%' matches the favorable and the unfavorable descriptions, because unfavorable contains favorable")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description = 'Unfavorable purchase variance'", ppv, year) == 0,
          "the description is matched exactly, with its first word Record and capitals as stored")
    amounts = [r[0] for r in d.q("SELECT Debit FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description = 'Record unfavorable purchase variance' "
                                 "ORDER BY Debit DESC LIMIT 11", ppv, year)]
    ties = {a for a in amounts[:10] if amounts[:10].count(a) > 1}
    claim(len(ties) == 1 and amounts[9] != amounts[10], "one amount appears twice among the ten largest, and the tenth is not tied with the eleventh, so the ten postings are certain but their order needs a tie-break")
    smallest = d.one("SELECT MIN(Debit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description = 'Record unfavorable purchase variance'", ppv, year)
    credit_max = d.one("SELECT MAX(Credit) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND Description = 'Record unfavorable purchase variance'", ppv, year)
    claim(credit_max == 0, "the unfavorable postings carry no credit, so a sort on Credit leaves them in no order")
    claim(smallest <= 0.01, "the smallest unfavorable posting is one cent, so a sort from the smallest shows cents")
    unf_all = d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND Description = 'Record unfavorable purchase variance'", ppv)
    claim(unf_all > unf, "the unfavorable postings of all years outnumber those of the year")
    top_all = d.q("SELECT FiscalYear, Debit FROM GLEntry WHERE AccountID = ? AND Description = 'Record unfavorable purchase variance' "
                  "ORDER BY Debit DESC, PostingDate, VoucherNumber LIMIT 10", ppv)
    claim(len({r[0] for r in top_all}) > 1 and top_all[0][1] > amounts[0],
          "without the year condition the ten largest come from more than one fiscal year, and the largest is not the year's")
    desc_all = d.one("SELECT COUNT(DISTINCT Description) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ?", ppv, year)
    desc_pi = d.one("SELECT COUNT(DISTINCT Description) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'PurchaseInvoice'", ppv, year)
    claim(desc_all == desc_pi + 1, "without the SourceDocumentType condition, the close's own description is a fourth value")
    close_date = d.one("SELECT PostingDate FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'JournalEntry'", ppv, year)
    claim(d.one("SELECT AccountName FROM Account WHERE AccountNumber = 5060") == "Purchase Price Variance", "account 5060 is the purchase price variance")
    return dict(unf_all=unf_all, top_all_first=top_all[0][1], ppv=ppv, no5060=5060, close_date=close_date, year=year, desc_all=desc_all, as_id=as_id, year_rows=year_rows, all_rows=all_rows, like_fav=like_fav, tie=sorted(ties)[0], smallest=smallest,
                variance_id=d.account("5080"), purchase_variance_account=d.account("2020"),
                kinds=rows(d, "SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? AND FiscalYear = ?", ppv, year))


# --- Exercise 9.3: the standard cost components --------------------------------------------------------------------------------------

@context("ch09.g3")
def g3(d, claim):
    need(d, claim, "Item")
    n_all = d.one("SELECT COUNT(*) FROM Item")
    made = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured'")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'manufactured'") == 0, "'manufactured' in small letters matches no item")
    bought = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode <> 'Manufactured'")
    claim(n_all == made + bought and bought > made, "the item master holds more items that are not manufactured than manufactured items")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode <> 'Manufactured' AND StandardLaborHoursPerUnit = 0") == bought,
          "every item that is not manufactured has zero standard labor hours, so the labor rate divides by zero (NULL) without the SupplyMode filter")
    no_filter_null = d.one("SELECT COUNT(*) FROM Item WHERE StandardDirectLaborCost / StandardLaborHoursPerUnit IS NULL")
    claim(no_filter_null == bought, "dividing by zero hours returns NULL, not an error, for exactly those items")
    unrounded = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured' AND StandardDirectLaborCost + StandardVariableOverheadCost "
                      "+ StandardFixedOverheadCost <> StandardConversionCost")
    rounded = d.one("SELECT COUNT(*) FROM Item WHERE SupplyMode = 'Manufactured' AND ROUND(StandardDirectLaborCost + StandardVariableOverheadCost "
                    "+ StandardFixedOverheadCost, 2) <> ROUND(StandardConversionCost, 2)")
    claim(unrounded > 0 and rounded == 0, "the component test without ROUND returns items whose parts add up to the cent, and with ROUND returns none")
    rates = [r[0] for r in d.q("SELECT ROUND(StandardDirectLaborCost / StandardLaborHoursPerUnit, 2) FROM Item WHERE SupplyMode = 'Manufactured' "
                               "ORDER BY 1")]
    low = d.q("SELECT ItemCode FROM Item WHERE SupplyMode = 'Manufactured' ORDER BY StandardDirectLaborCost / StandardLaborHoursPerUnit, ItemCode LIMIT 1")[0][0]
    high = d.q("SELECT ItemCode FROM Item WHERE SupplyMode = 'Manufactured' ORDER BY StandardDirectLaborCost / StandardLaborHoursPerUnit DESC, ItemCode LIMIT 1")[0][0]
    asc_groups = sorted({r[0] for r in d.q("SELECT ItemGroup FROM Item WHERE SupplyMode = 'Manufactured' ORDER BY StandardConversionCost LIMIT 10")})
    desc_groups = {r[0] for r in d.q("SELECT ItemGroup FROM Item WHERE SupplyMode = 'Manufactured' ORDER BY StandardConversionCost DESC LIMIT 10")}
    claim("Furniture" not in asc_groups and len(desc_groups) == 1, "the ten lowest conversion costs are in other groups than the ten highest, which are all one group")
    furniture_range = d.q("SELECT MIN(ROUND(StandardDirectLaborCost / StandardLaborHoursPerUnit, 2)), MAX(ROUND(StandardDirectLaborCost / StandardLaborHoursPerUnit, 2)) "
                          "FROM Item WHERE SupplyMode = 'Manufactured' AND ItemGroup = 'Furniture'")[0]
    inverted = d.one("SELECT MAX(ROUND(StandardLaborHoursPerUnit / StandardDirectLaborCost, 2)) FROM Item WHERE SupplyMode = 'Manufactured'")
    claim(inverted < 0.1, "dividing hours by cost gives values far below one, not a rate")
    biggest = d.q("SELECT ItemGroup FROM Item WHERE SupplyMode = 'Manufactured' GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 1")[0][0]
    claim(biggest in desc_groups, "the group of the ten highest conversion costs is the group with the most manufactured items")
    return dict(inverted=inverted, n_all=n_all, made=made, bought=bought, no_filter_null=no_filter_null, unrounded=unrounded, distinct_rates=len(set(rates)),
                rate_low_item=low, rate_high_item=high, asc_groups=and_list(asc_groups), furniture_low=furniture_range[0],
                furniture_high=furniture_range[1])


# --- Exercise 9.4: the open work orders ----------------------------------------------------------------------------------------------------------

@context("ch09.g4")
def g4(d, claim):
    need(d, claim, "WorkOrder")
    end = f"{d.C}-12-31"
    base = "FROM WorkOrder WHERE ClosedDate IS NULL"
    open_n = d.one(f"SELECT COUNT(*) {base}")
    eq_null = d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate = NULL")
    claim(eq_null == 0 and open_n > 0, "ClosedDate = NULL finds no work order, while IS NULL finds the open ones")
    claim(d.one("SELECT COUNT(*) FROM WorkOrder WHERE ClosedDate = ''") == 0, "no ClosedDate is an empty string, so the open work orders are NULL")
    substr_num = d.one(f"SELECT COUNT(*) {base} AND SUBSTR(WorkOrderNumber, 4, 4) = ?", d.C)
    substr_txt = d.one(f"SELECT COUNT(*) {base} AND SUBSTR(WorkOrderNumber, 4, 4) = ?", str(d.C))
    cast_int = d.one(f"SELECT COUNT(*) {base} AND CAST(SUBSTR(WorkOrderNumber, 4, 4) AS INTEGER) = ?", d.C)
    claim(substr_num == 0 and substr_txt == open_n and cast_int == open_n,
          "SUBSTR's text compared with a number finds no open work order, and compared with text or CAST finds every one")
    lower = d.one(f"SELECT COUNT(*) {base} AND Status = 'In progress'")
    claim(lower == 0, "'In progress' with a small p matches no work order (the status is In Progress)")
    lt = d.one(f"SELECT COUNT(*) {base} AND DueDate < ?", end)
    le = d.one(f"SELECT COUNT(*) {base} AND DueDate <= ?", end)
    claim(lt == le, "no open work order is due on the year-end itself, so < and <= return the same rows here (not in general)")
    slashed = d.one(f"SELECT COUNT(*) {base} AND DueDate <= '12/31/{d.C}'")
    claim(slashed == 0, "a date written as 12/31 in the year-first stored form compares after every stored date, so the filter keeps nothing")
    claim(d.one(f"SELECT COUNT(*) {base} AND Status = 'Completed' AND CompletedDate IS NULL") == 0, "every Completed work order has a CompletedDate")
    claim(d.one(f"SELECT COUNT(*) {base} AND Status <> 'Completed' AND CompletedDate IS NOT NULL") == 0, "no Released or In Progress work order has a CompletedDate")
    claim(d.one("SELECT COUNT(*) FROM WorkOrder WHERE Status = 'Released' AND ClosedDate IS NOT NULL") == 0,
          "a Released work order is always open, so a missing ClosedDate test adds nothing to Status = 'Released'")
    claim(d.one(f"SELECT COUNT(*) {base} AND DueDate <= ? GROUP BY DueDate ORDER BY DueDate LIMIT 1", end) == 1,
          "the oldest due date belongs to one work order, so the oldest needs no tie-break")
    claim(d.one("SELECT AccountName FROM Account WHERE AccountNumber = 5080") == "Manufacturing Variance"
          and d.one("SELECT AccountName FROM Account WHERE AccountNumber = 1090") == "Manufacturing Cost Clearing",
          "5080 is the manufacturing variance and 1090 the manufacturing cost clearing account")
    return dict(no=dict(variance=5080, clearing=1090), end=end, open_n=open_n, eq_null=eq_null, substr_num=substr_num, substr_txt=substr_txt, lower=lower, lt=lt, le=le,
                slashed=slashed, all_wo=d.one("SELECT COUNT(*) FROM WorkOrder"))


# --- Exercise 9.5: the shipments --------------------------------------------------------------------------------------------------------------------------

@context("ch09.g5")
def g5(d, claim):
    need(d, claim, "Shipment")
    end = f"{d.C}-12-31"
    eq_null = d.one("SELECT COUNT(*) FROM Shipment WHERE TrackingNumber = NULL")
    eq_empty = d.one("SELECT COUNT(*) FROM Shipment WHERE TrackingNumber = ''")
    is_null = d.one("SELECT COUNT(*) FROM Shipment WHERE TrackingNumber IS NULL")
    claim(eq_null == 0 and eq_empty == 0 and is_null > 0, "the blank tracking numbers are NULL, not empty text, so only IS NULL finds them")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In transit'") == 0, "'In transit' with a small t matches no shipment")
    le = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate <= ?", end)
    lt = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", end)
    last = d.q("SELECT ShipmentNumber, ShipmentDate, DeliveryDate FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate >= ?", end)
    claim(len(last) == 1 and last[0][1] == end and last[0][2] == end and le == lt + 1,
          "one In Transit shipment was shipped and is due on the last shipment date, so <= adds it and < leaves it out")
    no_status = d.one("SELECT COUNT(*) FROM Shipment WHERE DeliveryDate < ?", end)
    claim(no_status > 10 * lt, "without the Status condition the date test keeps nearly every shipment, mostly delivered ones")
    carriers = [r[1] for r in d.q("SELECT ShippedBy, COUNT(*) FROM Shipment WHERE TrackingNumber IS NULL GROUP BY 1")]
    claim(len(carriers) == d.one("SELECT COUNT(DISTINCT ShippedBy) FROM Shipment") and min(carriers) > 0.8 * max(carriers),
          "shipments with no tracking number are spread over every carrier, none more than a fifth below the largest")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE DeliveryDate IS NULL") == 0, "every shipment has a DeliveryDate, so the date test has no NULL to skip")
    claim(d.one("SELECT MAX(ShipmentDate) FROM Shipment") == end, f"{end} is the last shipment date, which is why the test stops there")
    return dict(end=end, eq_null=eq_null, eq_empty=eq_empty, le=le, lt=lt, last_number=last[0][0], no_status=no_status,
                carrier_low=min(carriers), carrier_high=max(carriers), transit_no_track=d.one(
                    "SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND TrackingNumber IS NULL"))


# --- Exercise 9.6: the time and labor records ------------------------------------------------------------------------------------------------------------------------------------

@context("ch09.g6")
def g6(d, claim):
    need(d, claim, "LaborTimeEntry", "WorkOrderOperation", "TimeClockEntry", "Employee")
    types = dict(d.q("SELECT LaborType, COUNT(*) FROM LaborTimeEntry WHERE WorkOrderOperationID IS NULL GROUP BY 1"))
    claim(set(types) == {"Direct Manufacturing", "Indirect Manufacturing", "NonManufacturing"},
          "labor time is Direct Manufacturing, Indirect Manufacturing or NonManufacturing, and every type has rows with no operation")
    claim(d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE LaborType = 'Direct' AND WorkOrderOperationID IS NULL") == 0,
          "LaborType = 'Direct' matches nothing: the value is Direct Manufacturing")
    claim(d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE LaborType = 'Direct Manufacturing' AND WorkOrderOperationID = NULL") == 0,
          "a comparison with NULL finds no direct labor row")
    totals = dict(d.q("SELECT LaborType, COUNT(*) FROM LaborTimeEntry GROUP BY 1"))
    claim(types["Indirect Manufacturing"] == totals["Indirect Manufacturing"] and types["NonManufacturing"] == totals["NonManufacturing"],
          "every indirect and non-manufacturing labor row has no operation, as no routing step applies to that time")
    years = {r[0][:4] for r in d.q("SELECT WorkDate FROM LaborTimeEntry WHERE LaborType = 'Direct Manufacturing' AND WorkOrderOperationID IS NULL")}
    claim(len(years) == types["Direct Manufacturing"], "the direct rows with no operation fall in different years, one a year")
    unfiltered = sum(types.values())
    direct = types["Direct Manufacturing"]
    orphans = d.one("SELECT COUNT(*) FROM LaborTimeEntry l WHERE l.LaborType = 'Direct Manufacturing' AND l.WorkOrderOperationID IS NOT NULL "
                    "AND NOT EXISTS (SELECT 1 FROM WorkOrderOperation o WHERE o.WorkOrderOperationID = l.WorkOrderOperationID)")
    claim(orphans > direct, "more direct labor rows point at an operation that does not exist than hold no operation at all (the test for missing values cannot find them; Chapter 10's join can)")
    claim(d.one("SELECT COUNT(*) FROM LaborTimeEntry WHERE RegularHours IS NULL OR OvertimeHours IS NULL") == 0,
          "no labor hours are NULL, so RegularHours + OvertimeHours is never NULL")
    claim(d.one("SELECT COUNT(*) FROM TimeClockEntry WHERE ClockOutTime = ''") == 0 and d.one("SELECT COUNT(*) FROM TimeClockEntry WHERE ClockOutTime = NULL") == 0,
          "no ClockOutTime is empty text, and a comparison with NULL finds none")
    pending = d.one("SELECT COUNT(*) FROM TimeClockEntry WHERE ClockStatus = 'Pending'")
    missing = d.one("SELECT COUNT(*) FROM TimeClockEntry WHERE ClockOutTime IS NULL")
    pending_out = d.one("SELECT COUNT(*) FROM TimeClockEntry WHERE ClockStatus = 'Pending' AND ClockOutTime IS NOT NULL")
    claim(pending > missing and pending_out == pending - missing and d.one(
        "SELECT COUNT(*) FROM TimeClockEntry WHERE ClockOutTime IS NULL AND ClockStatus <> 'Pending'") == 0,
          "every entry with no ClockOutTime is Pending, and some Pending entries do have a clock-out, so the two are not the same test")
    claim(d.one("SELECT MIN(RegularHours + OvertimeHours) FROM TimeClockEntry WHERE ClockOutTime IS NULL") > 0,
          "each entry with no clock-out records hours")
    after = d.one("SELECT COUNT(*) FROM TimeClockEntry t JOIN Employee e ON e.EmployeeID = t.EmployeeID WHERE t.ClockOutTime IS NULL "
                  "AND e.TerminationDate IS NOT NULL AND t.WorkDate > e.TerminationDate")
    claim(0 < after < missing, "some, not all, of the entries with no clock-out fall after the employee's termination date")
    wrong = d.one("SELECT COUNT(*) FROM Employee WHERE TerminationDate IS NULL AND EmploymentStatus = 'Terminated' OR IsActive = 0")
    right = d.one("SELECT COUNT(*) FROM Employee WHERE TerminationDate IS NULL AND (EmploymentStatus = 'Terminated' OR IsActive = 0)")
    claim(right == 0 and wrong > 0, "without parentheses the consistency test returns the terminated employees, as if they disagreed")
    n_term = d.one("SELECT COUNT(*) FROM Employee WHERE TerminationDate IS NOT NULL")
    return dict(n_term=n_term, unfiltered=unfiltered, indirect=types["Indirect Manufacturing"], nonmfg=types["NonManufacturing"], direct=direct,
                orphans=orphans, pending=pending, missing=missing, pending_out=pending_out, after=after, wrong=wrong,
                hours=d.q("SELECT ROUND(MIN(RegularHours + OvertimeHours), 2), ROUND(MAX(RegularHours + OvertimeHours), 2) FROM TimeClockEntry WHERE ClockOutTime IS NULL")[0],
                emp_term=d.one("SELECT TerminationDate FROM Employee WHERE EmployeeID = (SELECT EmployeeID FROM TimeClockEntry "
                               "WHERE ClockOutTime IS NULL ORDER BY WorkDate LIMIT 1)"))
