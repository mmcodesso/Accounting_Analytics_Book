"""Chapter 11's exercise solutions in SQL (instructor files): one script per exercise, `Ex 11.1.sql` to `Ex 11.6.sql`.

Each function adds the queries an exercise's numbered requirements ask for, in order, with checks whose expected values
come from the note context functions of `facts/notes/ch11.py` (the values of the generated instructor notes) or from
read-only SQL of this module, and model answers built from the same values. The scripts use what Chapters 9 to 11 teach:
CASE, dates, conditional aggregation, window functions, common table expressions, and views.
"""

from __future__ import annotations

from sqlbuild.script import Check

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def context(b, name: str) -> dict:
    """The values of a generated note: its context function, called with a claim function that ignores its arguments."""
    d = b.data                                   # puts facts/ on sys.path
    from notes import ch11
    return getattr(ch11, name)(d, lambda *a, **k: None)


def money(x: float) -> str:
    return f"{x:,.2f}"


# --- Exercise 11.1 ---------------------------------------------------------------------------------------------------

PARAMS = """\
WITH Params AS (
    SELECT '2026-12-31' AS AsOfDate
),
Closes AS (
    SELECT EntryNumber
    FROM JournalEntry
    WHERE EntryType LIKE 'Year-End Close%'
        AND PostingDate = (SELECT AsOfDate FROM Params)
)"""

TRIAL_BALANCE = """\
TrialBalance AS (
    SELECT a.AccountID, a.AccountNumber, a.AccountName,
        a.AccountType, a.AccountSubType,
        ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE gl.PostingDate <= (SELECT AsOfDate FROM Params)
        AND gl.VoucherNumber NOT IN (SELECT EntryNumber FROM Closes)
    GROUP BY a.AccountID, a.AccountNumber, a.AccountName,
        a.AccountType, a.AccountSubType
)"""

LINES = """\
Lines AS (
    SELECT
        CASE
            WHEN AccountType = 'Revenue'
                AND AccountSubType = 'Operating Revenue'
                THEN 'Operating revenue'
            WHEN AccountType = 'Revenue'
                AND AccountSubType = 'Contra Revenue'
                THEN 'Contra revenue'
            WHEN AccountType = 'Expense' AND AccountSubType = 'COGS'
                THEN 'Cost of goods sold'
            WHEN AccountType = 'Expense'
                AND AccountSubType = 'Operating Expense'
                THEN 'Operating expenses'
            WHEN AccountType IN ('Revenue', 'Expense')
                THEN 'Other income and expense'
            WHEN AccountType = 'Asset' AND AccountSubType
                IN ('Current Asset', 'Contra Current Asset')
                THEN 'Current assets'
            WHEN AccountType = 'Asset'
                AND AccountSubType = 'Fixed Asset'
                THEN 'Fixed assets'
            WHEN AccountType = 'Asset'
                AND AccountSubType = 'Contra Fixed Asset'
                THEN 'Contra fixed assets'
            WHEN AccountType = 'Liability'
                AND AccountSubType = 'Current Liability'
                THEN 'Current liabilities'
            WHEN AccountType = 'Liability'
                AND AccountSubType = 'Long-Term Liability'
                THEN 'Long-term liabilities'
            WHEN AccountType = 'Equity' THEN 'Equity'
            ELSE 'Unassigned'
        END AS StatementLine,
        SUM(CASE WHEN AccountType = 'Asset'
            THEN -Balance ELSE Balance END) AS Amount
    FROM TrialBalance
    GROUP BY StatementLine
)"""

TOTALS = """\
Totals AS (
    SELECT
        SUM(CASE StatementLine WHEN 'Operating revenue'
            THEN Amount ELSE 0 END) AS Revenue,
        SUM(CASE StatementLine WHEN 'Contra revenue'
            THEN Amount ELSE 0 END) AS ContraRevenue,
        SUM(CASE StatementLine WHEN 'Cost of goods sold'
            THEN Amount ELSE 0 END) AS COGS,
        SUM(CASE StatementLine WHEN 'Operating expenses'
            THEN Amount ELSE 0 END) AS OperatingExpenses,
        SUM(CASE StatementLine WHEN 'Other income and expense'
            THEN Amount ELSE 0 END) AS OtherIncomeExpense,
        SUM(CASE StatementLine WHEN 'Current assets'
            THEN Amount ELSE 0 END) AS CurrentAssets,
        SUM(CASE StatementLine WHEN 'Fixed assets'
            THEN Amount ELSE 0 END) AS FixedAssets,
        SUM(CASE StatementLine WHEN 'Contra fixed assets'
            THEN Amount ELSE 0 END) AS ContraFixedAssets,
        SUM(CASE StatementLine WHEN 'Current liabilities'
            THEN Amount ELSE 0 END) AS CurrentLiabilities,
        SUM(CASE StatementLine WHEN 'Long-term liabilities'
            THEN Amount ELSE 0 END) AS LongTermLiabilities,
        SUM(CASE StatementLine WHEN 'Equity'
            THEN Amount ELSE 0 END) AS Equity
    FROM Lines
)"""

STATEMENT_ORDER = ["Operating revenue", "Contra revenue", "Net revenue", "Cost of goods sold", "Gross margin",
                   "Operating expenses", "Operating income", "Other income and expense", "Net income",
                   "Current assets", "Fixed assets", "Contra fixed assets", "Total assets", "Current liabilities",
                   "Long-term liabilities", "Equity", "Liabilities, equity, and net income"]


def ex1(b):
    v = context(b, "ex1")
    d = b.data
    s = b.script("Ex 11.1.sql", "the income statement and the balance sheet check from the ledger",
                 "the closes found by the as-of date; the trial balance nets to zero; assets equal liabilities, "
                 "equity, and net income; net income equals the closing entry")
    accounts, credits = d.q(
        "SELECT COUNT(*), SUM(CASE WHEN b > 0 THEN b ELSE 0 END) FROM (SELECT ROUND(SUM(Credit) - SUM(Debit), 2) AS b "
        "FROM GLEntry WHERE PostingDate <= ? AND VoucherNumber NOT IN (?, ?) GROUP BY AccountID)",
        v["asof"], v["close1"], v["close2"])[0]
    s.query("Requirement (1), step 1: the closing entries dated on the as-of date",
            f"Population: journal entries; expected: the two closes of {v['asof']}",
            f"""\
{PARAMS}
SELECT EntryNumber
FROM Closes
ORDER BY EntryNumber;""",
            [Check("closes found", 2, len),
             Check("first close", v["close1"], lambda r: r.cell(0, "EntryNumber")),
             Check("second close", v["close2"], lambda r: r.cell(1, "EntryNumber"))])
    s.query("Requirement (1), step 2: the pre-closing trial balance at the as-of date",
            "Population: ledger rows to the as-of date without the closes; expected: balances net to zero",
            f"""\
{PARAMS},
{TRIAL_BALANCE}
SELECT COUNT(*) AS Accounts, ROUND(SUM(Balance), 2) AS NetBalance,
    ROUND(SUM(CASE WHEN Balance > 0 THEN Balance ELSE 0 END), 2)
        AS CreditBalances
FROM TrialBalance;""",
            [Check("accounts with postings", accounts, lambda r: r.value("Accounts")),
             Check("net of the balances", 0.0, lambda r: r.value("NetBalance")),
             Check("credit balances (equal to the debit balances of Tutorial 10.2)", credits,
                   lambda r: r.value("CreditBalances"))])
    line_values = {"Operating revenue": v["opr"], "Contra revenue": v["contra"], "Cost of goods sold": v["cogs"],
                   "Operating expenses": v["opex"], "Other income and expense": v["oexp"] + v["oie"],
                   "Current assets": v["current"], "Fixed assets": v["fixed"], "Contra fixed assets": -v["contra_fixed"],
                   "Current liabilities": v["cl"], "Long-term liabilities": v["ltl"], "Equity": v["equity"]}
    s.query("Requirement (2): each account assigned to a statement line with CASE",
            "Population: the trial balance accounts; expected: eleven lines, none unassigned",
            f"""\
{PARAMS},
{TRIAL_BALANCE},
{LINES}
SELECT StatementLine, ROUND(Amount, 2) AS Amount
FROM Lines
ORDER BY StatementLine;""",
            [Check("statement lines (no Unassigned line)", len(line_values), len)] +
            [Check(line, round(amount, 2), lambda r, line=line: r.where(StatementLine=line)["Amount"])
             for line, amount in line_values.items()])
    s.query("Requirement (3): net revenue, gross margin, operating income, and net income",
            "Population: the statement lines; expected: net income equal to Chapter 6's",
            f"""\
{PARAMS},
{TRIAL_BALANCE},
{LINES},
{TOTALS}
SELECT ROUND(Revenue + ContraRevenue, 2) AS NetRevenue,
    ROUND(Revenue + ContraRevenue + COGS, 2) AS GrossMargin,
    ROUND(100.0 * (Revenue + ContraRevenue + COGS)
        / (Revenue + ContraRevenue), 2) AS GrossMarginPct,
    ROUND(Revenue + ContraRevenue + COGS + OperatingExpenses, 2)
        AS OperatingIncome,
    ROUND(100.0 * (Revenue + ContraRevenue + COGS + OperatingExpenses)
        / (Revenue + ContraRevenue), 2) AS OperatingIncomePct,
    ROUND(Revenue + ContraRevenue + COGS + OperatingExpenses
        + OtherIncomeExpense, 2) AS NetIncome
FROM Totals;""",
            [Check("net revenue", v["net_rev"], lambda r: r.value("NetRevenue")),
             Check("gross margin", v["gm"], lambda r: r.value("GrossMargin")),
             Check("gross margin %", round(100 * v["gm_pct"], 2), lambda r: r.value("GrossMarginPct")),
             Check("operating income", v["oi"], lambda r: r.value("OperatingIncome")),
             Check("operating income %", round(100 * v["oi_pct"], 2), lambda r: r.value("OperatingIncomePct")),
             Check("net income", v["ni"], lambda r: r.value("NetIncome"))])
    retained = d.one("SELECT g.Credit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                     "WHERE g.VoucherNumber = ? AND a.AccountNumber = 3030", v["close2"])
    s.query("Requirement (4): assets against liabilities, equity, and net income, and the closing entry",
            f"Population: the statement lines and the closes; expected: no difference, net income = {v['close2']}",
            f"""\
{PARAMS},
{TRIAL_BALANCE},
{LINES},
{TOTALS},
Closing AS (
    SELECT SUM(gl.Credit) - SUM(gl.Debit) AS ToRetainedEarnings
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber = 3030
        AND gl.VoucherNumber IN (SELECT EntryNumber FROM Closes)
)
SELECT ROUND(CurrentAssets + FixedAssets + ContraFixedAssets, 2)
        AS TotalAssets,
    ROUND(CurrentLiabilities + LongTermLiabilities, 2) AS Liabilities,
    ROUND(Equity, 2) AS Equity,
    ROUND(Revenue + ContraRevenue + COGS + OperatingExpenses
        + OtherIncomeExpense, 2) AS NetIncome,
    ROUND(CurrentAssets + FixedAssets + ContraFixedAssets
        - CurrentLiabilities - LongTermLiabilities - Equity
        - (Revenue + ContraRevenue + COGS + OperatingExpenses
            + OtherIncomeExpense), 2) AS Difference,
    ROUND((SELECT ToRetainedEarnings FROM Closing), 2)
        AS ClosingEntry
FROM Totals;""",
            [Check("total assets", v["assets"], lambda r: r.value("TotalAssets")),
             Check("liabilities", v["cl"] + v["ltl"], lambda r: r.value("Liabilities")),
             Check("equity", v["equity"], lambda r: r.value("Equity")),
             Check("liabilities, equity, and net income", v["le_total"],
                   lambda r: r.value("Liabilities") + r.value("Equity") + r.value("NetIncome")),
             Check("difference", 0.0, lambda r: r.value("Difference")),
             Check(f"credit of {v['close2']} to retained earnings", retained, lambda r: r.value("ClosingEntry"))])
    s.query("Requirement (5), step 1: the statement saved as a view, without an ORDER BY",
            "Population: the statement lines and totals; expected: the view is created",
            f"""\
DROP VIEW IF EXISTS Ex11_1_IncomeStatement;
CREATE VIEW Ex11_1_IncomeStatement AS
{PARAMS},
{TRIAL_BALANCE},
{LINES},
{TOTALS}
SELECT StatementLine, ROUND(Amount, 2) AS Amount
FROM Lines
UNION ALL
SELECT 'Net revenue', ROUND(Revenue + ContraRevenue, 2)
FROM Totals
UNION ALL
SELECT 'Gross margin', ROUND(Revenue + ContraRevenue + COGS, 2)
FROM Totals
UNION ALL
SELECT 'Operating income',
    ROUND(Revenue + ContraRevenue + COGS + OperatingExpenses, 2)
FROM Totals
UNION ALL
SELECT 'Net income',
    ROUND(Revenue + ContraRevenue + COGS + OperatingExpenses
        + OtherIncomeExpense, 2)
FROM Totals
UNION ALL
SELECT 'Total assets',
    ROUND(CurrentAssets + FixedAssets + ContraFixedAssets, 2)
FROM Totals
UNION ALL
SELECT 'Liabilities, equity, and net income',
    ROUND(CurrentLiabilities + LongTermLiabilities + Equity
        + Revenue + ContraRevenue + COGS + OperatingExpenses
        + OtherIncomeExpense, 2)
FROM Totals;""")
    order = "\n".join(f"    WHEN '{line}' THEN {i}" for i, line in enumerate(STATEMENT_ORDER, 1))
    s.query("Requirement (5), step 2: the view in statement order, sorted by a CASE expression",
            "Population: the view; expected: seventeen lines in statement order",
            f"""\
SELECT StatementLine, Amount
FROM Ex11_1_IncomeStatement
ORDER BY CASE StatementLine
{order}
    END;""",
            [Check("lines in the view", len(STATEMENT_ORDER), len),
             Check("statement order", STATEMENT_ORDER, lambda r: r.col("StatementLine")),
             Check("net income in the view", v["ni"], lambda r: r.where(StatementLine="Net income")["Amount"]),
             Check("total assets in the view", v["assets"], lambda r: r.where(StatementLine="Total assets")["Amount"]),
             Check("liabilities, equity, and net income in the view", v["le_total"],
                   lambda r: r.where(StatementLine="Liabilities, equity, and net income")["Amount"])])
    s.answer("Deliverable", f"""\
The view reproduces Chapter 6's statements from the pre-closing trial balance at {v['asof']} ({accounts} accounts,
closes {v['close1']} and {v['close2']} left out): operating revenue {money(v['opr'])}, contra revenue
{money(v['contra'])}, net revenue {money(v['net_rev'])}, gross margin {money(v['gm'])} ({100 * v['gm_pct']:.2f}% of
net revenue), operating income {money(v['oi'])} ({100 * v['oi_pct']:.2f}%), and net income {money(v['ni'])}, equal to
the credit of {v['close2']} to retained earnings.

Total assets of {money(v['assets'])} equal liabilities of {money(v['cl'] + v['ltl'])} plus equity of
{money(v['equity'])} plus net income, because the year's revenue and expense accounts have not yet been closed into
retained earnings. The as-of date is the one parameter: the closes are found by their EntryType and that date, so
changing the date in Params produces the statements of another year-end without any other edit.""")


# --- Exercise 11.2 ---------------------------------------------------------------------------------------------------

MONTHLY = """\
WITH Monthly AS (
    SELECT gl.FiscalYear, gl.FiscalPeriod, a.AccountNumber,
        CASE a.AccountNumber
            WHEN 4010 THEN 'Furniture'
            WHEN 4020 THEN 'Lighting'
            WHEN 4030 THEN 'Textiles'
            WHEN 4040 THEN 'Accessories'
            WHEN 4080 THEN 'Services'
        END AS ProductLine,
        SUM(gl.Credit) - SUM(gl.Debit) AS Revenue
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber IN (4010, 4020, 4030, 4040, 4080)
        AND gl.FiscalYear BETWEEN 2024 AND 2026
        AND gl.VoucherNumber NOT IN (
            SELECT EntryNumber
            FROM JournalEntry
            WHERE EntryType LIKE 'Year-End Close%')
    GROUP BY gl.FiscalYear, gl.FiscalPeriod, a.AccountNumber
)"""

YTD = """\
SUM(Revenue) OVER (PARTITION BY ProductLine, FiscalYear
            ORDER BY FiscalPeriod)"""

PRIOR = """\
LAG(Revenue) OVER (PARTITION BY ProductLine, FiscalPeriod
            ORDER BY FiscalYear)"""

COMPARED = f"""\
Compared AS (
    SELECT ProductLine, FiscalYear, FiscalPeriod, Revenue,
        {YTD} AS RevenueYTD,
        {PRIOR} AS PriorYear
    FROM Monthly
)"""


def ex2(b):
    v = context(b, "ex2")
    ytd = dict(v["ytd"])
    down, up = v["down"], v["up"]
    s = b.script("Ex 11.2.sql", "monthly revenue by product line with year-to-date and prior-year comparisons",
                 "180 months of five product lines; December year to date equals the trial balance")
    s.query("Requirement (1): revenue by fiscal year, period, and account, without the closes",
            f"Population: postings to 4010-4040 and 4080, fiscal 2024-2026; expected: {v['rows']} rows",
            f"""\
{MONTHLY}
SELECT ProductLine, AccountNumber, FiscalYear, FiscalPeriod,
    ROUND(Revenue, 2) AS Revenue
FROM Monthly
ORDER BY ProductLine, FiscalYear, FiscalPeriod;""",
            [Check("rows (five lines x 36 months)", v["rows"], len),
             Check("product lines", 5, lambda r: len(set(r.col("ProductLine"))))])
    s.query("Requirement (2): a year-to-date running total by product line and fiscal year",
            "Population: the monthly revenue; expected: December 2026 year to date as the trial balance",
            f"""\
{MONTHLY}
SELECT ProductLine, FiscalYear, FiscalPeriod,
    ROUND(Revenue, 2) AS Revenue,
    ROUND({YTD}, 2) AS RevenueYTD
FROM Monthly
ORDER BY ProductLine, FiscalYear, FiscalPeriod;""",
            [Check(f"{line} December 2026 year to date", round(value, 2),
                   lambda r, line=line: r.where(ProductLine=line, FiscalYear=2026, FiscalPeriod=12)["RevenueYTD"])
             for line, value in ytd.items()])
    s.query("Requirement (3): the same month of the prior year with LAG, and the percentage change",
            "Population: the monthly revenue; expected: no prior year for fiscal 2024",
            f"""\
{MONTHLY},
{COMPARED}
SELECT ProductLine, FiscalYear, FiscalPeriod,
    ROUND(Revenue, 2) AS Revenue, ROUND(RevenueYTD, 2) AS RevenueYTD,
    ROUND(PriorYear, 2) AS PriorYear,
    ROUND(100.0 * (Revenue - PriorYear) / PriorYear, 1) AS PctChange
FROM Compared
ORDER BY ProductLine, FiscalYear, FiscalPeriod;""",
            [Check("months without a prior year (fiscal 2024)", 60, lambda r: r.col("PriorYear").count(None)),
             Check(f"Furniture {down['month']} 2026", round(down["now"], 2),
                   lambda r: r.where(ProductLine="Furniture", FiscalYear=2026,
                                     FiscalPeriod=MONTHS.index(down["month"]) + 1)["Revenue"]),
             Check(f"Furniture {down['month']} 2025 (prior year)", round(down["before"], 2),
                   lambda r: r.where(ProductLine="Furniture", FiscalYear=2026,
                                     FiscalPeriod=MONTHS.index(down["month"]) + 1)["PriorYear"]),
             Check(f"Furniture {up['month']} 2025 (prior year)", round(up["before"], 2),
                   lambda r: r.where(ProductLine="Furniture", FiscalYear=2026,
                                     FiscalPeriod=MONTHS.index(up["month"]) + 1)["PriorYear"])])
    s.query("Requirement (4): December 2026 year to date against the trial balance of Tutorial 10.2",
            "Population: the five revenue accounts at 2026-12-31; expected: no differences",
            f"""\
{MONTHLY},
YearToDate AS (
    SELECT ProductLine, AccountNumber, FiscalYear, FiscalPeriod,
        {YTD} AS RevenueYTD
    FROM Monthly
),
TrialBalance AS (
    SELECT a.AccountNumber,
        ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2) AS Balance
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountNumber IN (4010, 4020, 4030, 4040, 4080)
        AND gl.PostingDate <= '2026-12-31'
        AND gl.VoucherNumber NOT IN ('JE-2026-000296', 'JE-2026-000297')
    GROUP BY a.AccountNumber
)
SELECT y.ProductLine, y.AccountNumber,
    ROUND(y.RevenueYTD, 2) AS DecemberYTD, tb.Balance AS TrialBalance,
    ROUND(y.RevenueYTD - tb.Balance, 2) AS Difference
FROM YearToDate AS y
    INNER JOIN TrialBalance AS tb ON tb.AccountNumber = y.AccountNumber
WHERE y.FiscalYear = 2026 AND y.FiscalPeriod = 12
ORDER BY y.AccountNumber;""",
            [Check("accounts compared", 5, len),
             Check("accounts with a difference", 0, lambda r: sum(1 for x in r.col("Difference") if abs(x) > 0.005)),
             Check("total of the trial balance", round(v["total"], 2), lambda r: r.total("TrialBalance"))])
    s.query("Requirement (5): Furniture's months of fiscal 2026 ranked by the change against 2025",
            f"Population: Furniture, fiscal 2026; expected: largest decline {down['month']}, "
            f"largest increase {up['month']}",
            f"""\
{MONTHLY},
{COMPARED}
SELECT FiscalPeriod, ROUND(Revenue, 2) AS Revenue,
    ROUND(PriorYear, 2) AS PriorYear,
    ROUND(100.0 * (Revenue - PriorYear) / PriorYear, 1) AS PctChange,
    RANK() OVER (ORDER BY (Revenue - PriorYear) / PriorYear)
        AS DeclineRank
FROM Compared
WHERE ProductLine = 'Furniture' AND FiscalYear = 2026
ORDER BY DeclineRank;""",
            [Check("months", 12, len),
             Check("largest decline (month)", MONTHS.index(down["month"]) + 1, lambda r: r.cell(0, "FiscalPeriod")),
             Check("largest decline (%)", round(100 * down["pct"], 1), lambda r: r.cell(0, "PctChange")),
             Check("largest increase (month)", MONTHS.index(up["month"]) + 1, lambda r: r.cell(11, "FiscalPeriod")),
             Check("largest increase (%)", round(100 * up["pct"], 1), lambda r: r.cell(11, "PctChange")),
             Check(f"Furniture {up['month']} 2026", round(up["now"], 2), lambda r: r.cell(11, "Revenue"))])
    later = " and ".join(v["later"])
    s.answer("Deliverable", f"""\
Every December year-to-date figure of fiscal 2026 equals the trial balance of its account (Furniture
{money(ytd['Furniture'])}, Lighting {money(ytd['Lighting'])}, Textiles {money(ytd['Textiles'])}, Accessories
{money(ytd['Accessories'])}, Services {money(ytd['Services'])}; {money(v['total'])} in all), so the monthly report
starts from the same numbers as the statements. The only journal entries to these accounts are the year-end closes,
which the query leaves out by their EntryType.

Furniture's largest decline against 2025 is {down['month']} ({money(down['now'])} against {money(down['before'])},
{100 * down['pct']:+.1f}%), and its largest increase is {up['month']} ({money(up['now'])} against
{money(up['before'])}, {100 * up['pct']:+.1f}%). {down['month']} 2025 was Furniture's
{v['base'] or 'a high'} month of 2025, so part of the decline is a high base. The fiscal 2026 Furniture promotion
(Chapter 6) priced orders in {' and '.join(v['priced'])}, and its orders were invoiced through {later}, so the next
step is to look at the timing of invoicing and promotions: Furniture revenue by invoice month and promotion, the
order dates of the lines invoiced in each month, and the volume and price per unit behind each month, as the bridge of
Tutorial 6.3 separates them.""")


# --- Exercise 11.3 ---------------------------------------------------------------------------------------------------

MARGINS = """\
WITH Margins AS (
    SELECT ItemGroup, ItemCode, ItemName, ListPrice, StandardCost,
        ROUND(ListPrice - StandardCost, 2) AS UnitMargin,
        ROUND(100.0 * (ListPrice - StandardCost) / ListPrice, 1)
            AS MarginPct
    FROM Item
    WHERE ListPrice IS NOT NULL
)"""

RANKED = """\
Ranked AS (
    SELECT ItemGroup, ItemCode, ItemName, UnitMargin, MarginPct,
        RANK() OVER w AS MarginRank,
        DENSE_RANK() OVER w AS MarginDenseRank,
        ROW_NUMBER() OVER w AS MarginRowNumber
    FROM Margins
    WINDOW w AS (PARTITION BY ItemGroup ORDER BY UnitMargin DESC)
)"""


def ex3(b):
    v = context(b, "ex3")
    counts = dict(v["counts"])
    top = {t[0]: t for t in v["top"]}                       # group -> (group, code, name, margin)
    ranges = {g: (low, high) for g, low, high in v["ranges"]}
    d = b.data
    top3 = d.one("SELECT COUNT(*) FROM (SELECT RANK() OVER (PARTITION BY ItemGroup ORDER BY ROUND(ListPrice - "
                 "StandardCost, 2) DESC) AS r FROM Item WHERE ListPrice IS NOT NULL) WHERE r <= 3")
    s = b.script("Ex 11.3.sql", "items ranked by unit margin at list price within each product line",
                 f"{v['items']} items with a list price; the three rankings agree; the top three of each group")
    s.query("Requirement (1): the unit margin at list price and the margin percentage",
            f"Population: items with a list price; expected: {v['items']} items",
            f"""\
SELECT ItemGroup, ItemCode, ItemName, ListPrice, StandardCost,
    ROUND(ListPrice - StandardCost, 2) AS UnitMargin,
    ROUND(100.0 * (ListPrice - StandardCost) / ListPrice, 1) AS MarginPct
FROM Item
WHERE ListPrice IS NOT NULL
ORDER BY ItemGroup, UnitMargin DESC;""",
            [Check("items", v["items"], len)] +
            [Check(f"{g} items", n, lambda r, g=g: r.col("ItemGroup").count(g)) for g, n in counts.items()])
    s.query("Requirement (2), step 1: RANK, DENSE_RANK, and ROW_NUMBER within each item group",
            "Population: items with a list price; expected: the three agree when no margins tie",
            f"""\
{MARGINS},
{RANKED}
SELECT ItemGroup, ItemCode, UnitMargin, MarginPct, MarginRank,
    MarginDenseRank, MarginRowNumber
FROM Ranked
ORDER BY ItemGroup, MarginRank;""",
            [Check("items ranked", v["items"], len)] +
            [Check(f"{g} rank 1: {t[1]}", t[1], lambda r, g=g: r.where(ItemGroup=g, MarginRank=1)["ItemCode"])
             for g, t in top.items()])
    s.query("Requirement (2), step 2: the items whose three rankings differ",
            "Population: the ranked items; expected: none, because no two items in a group share a margin",
            f"""\
{MARGINS},
{RANKED}
SELECT COUNT(*) AS Items,
    SUM(CASE WHEN MarginRank <> MarginRowNumber
        OR MarginDenseRank <> MarginRowNumber THEN 1 ELSE 0 END)
        AS RankingsDiffer
FROM Ranked;""",
            [Check("items", v["items"], lambda r: r.value("Items")),
             Check("items whose rankings differ", 0, lambda r: r.value("RankingsDiffer"))])
    s.query("Requirement (3): the top three items of each item group, by an outer filter",
            f"Population: the ranked items; expected: {top3} rows, three per group",
            f"""\
{MARGINS},
{RANKED}
SELECT ItemGroup, MarginRank, ItemCode, ItemName, UnitMargin, MarginPct
FROM Ranked
WHERE MarginRank <= 3
ORDER BY ItemGroup, MarginRank;""",
            [Check("rows", top3, len)] +
            [Check(f"{g} top unit margin", round(t[3], 2), lambda r, g=g: r.where(ItemGroup=g, MarginRank=1)["UnitMargin"])
             for g, t in top.items()])
    s.query("Requirement (4): each group's highest and lowest unit margins and items, beside every item",
            f"Population: items with a list price; expected: {v['items']} rows, each with its group's range",
            f"""\
{MARGINS}
SELECT ItemGroup, ItemCode, UnitMargin,
    MAX(UnitMargin) OVER (PARTITION BY ItemGroup) AS GroupHighest,
    MIN(UnitMargin) OVER (PARTITION BY ItemGroup) AS GroupLowest,
    COUNT(*) OVER (PARTITION BY ItemGroup) AS GroupItems
FROM Margins
ORDER BY ItemGroup, UnitMargin DESC;""",
            [Check("rows", v["items"], len)] +
            [c for g, (low, high) in ranges.items() for c in (
                Check(f"{g} highest", round(high, 2), lambda r, g=g: r.where(ItemCode=top[g][1])["GroupHighest"]),
                Check(f"{g} lowest", round(low, 2), lambda r, g=g: r.where(ItemCode=top[g][1])["GroupLowest"]),
                Check(f"{g} items", counts[g], lambda r, g=g: r.where(ItemCode=top[g][1])["GroupItems"]))])
    s.answer("Requirement (2)", """\
RANK gives tied rows the same rank and skips the ranks that follow (1, 2, 2, 4); DENSE_RANK gives ties the same rank
without a gap (1, 2, 2, 3); ROW_NUMBER numbers every row once, breaking ties arbitrarily unless the ORDER BY decides
them. They differ only where two items of a group share a unit margin. Here no two items in a group share one, so the
three columns agree on every row (step 2 counts no differences), and the top three by any of them are the same items.""")
    lines = "; ".join(f"{g} {t[1]} ({money(t[3])}, range {money(ranges[g][0])} to {money(ranges[g][1])})"
                      for g, t in top.items())
    s.answer("Requirement (5)", f"""\
Top items and ranges: {lines}.

The Services items are design services whose StandardCost is zero, because their cost is the design staff's payroll,
which posts to operating expense rather than to inventory (Chapter 6); their unit margin therefore equals their price.
The measure is a gross margin at list price, not a contribution margin: for the {v['manufactured']} manufactured items
StandardCost includes fixed overhead, which does not vary with one more unit (the {v['purchased']} purchased finished
goods carry none), and for every item it leaves out variable selling costs such as commissions, freight, and
discounts. List price is also not the price charged, since price lists, overrides, and promotions lower it. For a
pricing or product-mix decision, the product manager should use the variable cost and the net price.""")


# --- Exercise 11.4 ---------------------------------------------------------------------------------------------------

OVERTIME = """\
WITH Overtime AS (
    SELECT lt.EmployeeID, e.JobTitle,
        SUM(lt.OvertimeHours) AS OvertimeHours
    FROM LaborTimeEntry AS lt
        INNER JOIN Employee AS e ON e.EmployeeID = lt.EmployeeID
    WHERE lt.LaborType <> 'NonManufacturing'
        AND lt.WorkDate BETWEEN '2026-01-01' AND '2026-12-31'
    GROUP BY lt.EmployeeID, e.JobTitle
    HAVING SUM(lt.OvertimeHours) > 0
)"""

RUNNING = """\
Running AS (
    SELECT EmployeeID, JobTitle, OvertimeHours,
        RANK() OVER (ORDER BY OvertimeHours DESC) AS OvertimeRank,
        ROW_NUMBER() OVER (ORDER BY OvertimeHours DESC, EmployeeID)
            AS RunningRank,
        SUM(OvertimeHours) OVER (ORDER BY OvertimeHours DESC, EmployeeID
            ROWS UNBOUNDED PRECEDING)
            / SUM(OvertimeHours) OVER () AS RunningShare
    FROM Overtime
)"""


def ex4(b):
    v = context(b, "ex4")
    s = b.script("Ex 11.4.sql", "is manufacturing overtime concentrated in a few employees?",
                 f"{v['employees']} employees with overtime in fiscal {v['year']}; the running share reaches 1")
    s.query("Requirement (1): fiscal 2026 overtime hours by employee, by work date, with the job title",
            f"Population: manufacturing labor time of 2026; expected: {v['employees']} employees",
            """\
SELECT lt.EmployeeID, e.JobTitle,
    ROUND(SUM(lt.OvertimeHours), 1) AS OvertimeHours
FROM LaborTimeEntry AS lt
    INNER JOIN Employee AS e ON e.EmployeeID = lt.EmployeeID
WHERE lt.LaborType <> 'NonManufacturing'
    AND lt.WorkDate BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY lt.EmployeeID, e.JobTitle
HAVING SUM(lt.OvertimeHours) > 0
ORDER BY OvertimeHours DESC, lt.EmployeeID;""",
            [Check("employees with overtime", v["employees"], len),
             Check("total overtime hours", v["total"], lambda r: r.total("OvertimeHours"), tolerance=1.0)] +
            [Check(f"rank {i} employee", emp, lambda r, i=i: r.cell(i - 1, "EmployeeID"))
             for i, (emp, _, _) in enumerate(v["top"], 1)] +
            [Check(f"employee {emp} hours", round(h, 1), lambda r, emp=emp: r.where(EmployeeID=emp)["OvertimeHours"])
             for emp, _, h in v["top"]])
    s.query("Requirement (2): the employees ranked, with a running share of all overtime",
            "Population: the employees with overtime; expected: the running share reaches 1.000",
            f"""\
{OVERTIME},
{RUNNING}
SELECT EmployeeID, JobTitle, ROUND(OvertimeHours, 1) AS OvertimeHours,
    OvertimeRank, ROUND(RunningShare, 3) AS RunningShare
FROM Running
ORDER BY RunningRank;""",
            [Check("employees", v["employees"], len),
             Check("first employee", v["top"][0][0], lambda r: r.cell(0, "EmployeeID")),
             Check("running share of the last employee", 1.0, lambda r: r.cell(len(r) - 1, "RunningShare"))])
    s.query("Requirement (3): the number of employees that account for half of the overtime",
            f"Population: the ranked employees; expected: {v['half']} of {v['employees']}",
            f"""\
{OVERTIME},
{RUNNING}
SELECT MIN(RunningRank) AS EmployeesForHalf,
    (SELECT COUNT(*) FROM Overtime) AS Employees,
    (SELECT ROUND(SUM(OvertimeHours), 0) FROM Overtime) AS TotalOvertime
FROM Running
WHERE RunningShare >= 0.5;""",
            [Check("employees for half of the overtime", v["half"], lambda r: r.value("EmployeesForHalf")),
             Check("employees", v["employees"], lambda r: r.value("Employees")),
             Check("total overtime hours", round(v["total"]), lambda r: r.value("TotalOvertime"))])
    titles = [(t, n, h) for t, n, h in v["titles"]]
    s.query("Requirement (4): overtime hours and the average per employee by job title",
            f"Population: the employees with overtime; expected: {len(titles)} job titles",
            f"""\
{OVERTIME}
SELECT JobTitle, COUNT(*) AS Employees,
    ROUND(SUM(OvertimeHours), 0) AS OvertimeHours,
    ROUND(AVG(OvertimeHours), 1) AS AveragePerEmployee
FROM Overtime
GROUP BY JobTitle
ORDER BY OvertimeHours DESC;""",
            [Check("job titles", len(titles), len)] +
            [c for t, n, h in titles for c in (
                Check(f"{t} employees", n, lambda r, t=t: r.where(JobTitle=t[:-1])["Employees"]),
                Check(f"{t} hours", round(h), lambda r, t=t: r.where(JobTitle=t[:-1])["OvertimeHours"]),
                Check(f"{t} average", round(h / n, 1), lambda r, t=t: r.where(JobTitle=t[:-1])["AveragePerEmployee"]))])
    top = ", ".join(f"employee {e} ({t}) {h:,.1f}" for e, t, h in v["top"])
    by_title = "; ".join(f"{t} {n} employees, {h:,.0f} hours ({h / n:,.1f} each)" for t, n, h in titles)
    s.answer("Requirement (5), memo to the controller", f"""\
To: the controller. Subject: is overtime a problem of a few people?

In fiscal {v['year']}, {v['employees']} employees recorded {v['total']:,.0f} hours of manufacturing overtime (labor
time by work date; the payroll year of Chapter 10 gives {v['payroll']:,.0f}). The largest totals are close together:
{top}. Half of the overtime is reached at rank {v['half']}, half of the employees, and the running share climbs in an
almost straight line, which is what an even spread looks like; a concentrated pattern would reach half within a
handful of names.

By job title: {by_title}. The averages are nearly the same, about {v['weekly']} hours a week for every employee.

The plant manager's claim is not supported: overtime is plant-wide, not the habit of a few people. It points to a
plant-level cause, such as the surge days and the hours paid beyond the work that Chapter 12 examines, rather than
to individual scheduling, so the response should address how much overtime the plant plans and approves, not who
works it.""")


# --- Exercise 11.5 ---------------------------------------------------------------------------------------------------

FLAGS = """\
WITH Flags AS (
    SELECT je.EntryNumber, je.EntryType, je.PostingDate, je.TotalAmount,
        CASE WHEN strftime('%w', je.CreatedDate) IN ('0', '6')
            THEN 1 ELSE 0 END AS Weekend,
        CASE WHEN date(je.CreatedDate) > je.PostingDate
            THEN 1 ELSE 0 END AS Backdated,
        CASE WHEN je.CreatedByEmployeeID = je.ApprovedByEmployeeID
            THEN 1 ELSE 0 END AS SelfApproved,
        CASE WHEN je.TotalAmount > COALESCE(e.MaxApprovalAmount, 0)
            THEN 1 ELSE 0 END AS AboveLimit,
        CASE WHEN je.TotalAmount = ROUND(je.TotalAmount / 1000, 0) * 1000
            THEN 1 ELSE 0 END AS RoundAmount
    FROM JournalEntry AS je
        LEFT JOIN Employee AS e ON e.EmployeeID = je.ApprovedByEmployeeID
)"""

SCORED = """\
Scored AS (
    SELECT *,
        Weekend + Backdated + SelfApproved + AboveLimit + RoundAmount
            AS RiskScore
    FROM Flags
)"""


def ex5(b):
    v = context(b, "ex5")
    counts = dict(v["counts"])
    scores = dict(v["scores"])
    high = sum(n for s_, n in scores.items() if s_ >= 2)
    s = b.script("Ex 11.5.sql", "the five journal entry tests of Tutorial 8.3 and their risk score",
                 f"{v['entries']} entries; the counts by test and by score equal Tutorial 8.3's")
    s.query("Requirements (1) and (2), step 1: the entries flagged by each test",
            f"Population: all {v['entries']} journal entries; expected: Tutorial 8.3's counts",
            f"""\
{FLAGS}
SELECT COUNT(*) AS Entries, SUM(Weekend) AS Weekend,
    SUM(Backdated) AS Backdated, SUM(SelfApproved) AS SelfApproved,
    SUM(AboveLimit) AS AboveLimit, SUM(RoundAmount) AS RoundAmount
FROM Flags;""",
            [Check("entries", v["entries"], lambda r: r.value("Entries"))] +
            [Check(f"{f} flags", n, lambda r, f=f: r.value(f)) for f, n in counts.items()])
    s.query("Requirement (2), step 2: the entries at each risk score",
            f"Population: all journal entries; expected: {len(scores)} scores, as Tutorial 8.3",
            f"""\
{FLAGS},
{SCORED}
SELECT RiskScore, COUNT(*) AS Entries,
    ROUND(SUM(TotalAmount), 2) AS TotalAmount
FROM Scored
GROUP BY RiskScore
ORDER BY RiskScore;""",
            [Check("scores present", sorted(scores), lambda r: r.col("RiskScore"))] +
            [Check(f"entries scoring {k}", n, lambda r, k=k: r.where(RiskScore=k)["Entries"]) for k, n in scores.items()])
    s.query("Requirement (4): the entries scoring 2 or more, ranked by score and amount",
            f"Population: the scored entries; expected: {high} entries, {v['top_entry']} first",
            f"""\
{FLAGS},
{SCORED}
SELECT RANK() OVER (ORDER BY RiskScore DESC, TotalAmount DESC)
        AS ReviewRank,
    EntryNumber, EntryType, PostingDate, TotalAmount, RiskScore,
    Weekend, Backdated, SelfApproved, AboveLimit, RoundAmount
FROM Scored
WHERE RiskScore >= 2
ORDER BY ReviewRank;""",
            [Check("entries scoring 2 or more", high, len),
             Check("first entry", v["top_entry"], lambda r: r.cell(0, "EntryNumber")),
             Check("its score", v["top_score"], lambda r: r.cell(0, "RiskScore"))])
    s.query("Requirement (5), step 1: the tests saved as a view",
            "Population: all journal entries; expected: the view is created",
            f"""\
DROP VIEW IF EXISTS Ex11_5_JournalEntryTests;
CREATE VIEW Ex11_5_JournalEntryTests AS
{FLAGS},
{SCORED}
SELECT EntryNumber, EntryType, PostingDate, TotalAmount, Weekend,
    Backdated, SelfApproved, AboveLimit, RoundAmount, RiskScore
FROM Scored;""")
    s.query("Requirement (5), step 2: the view rerun, by test",
            "Population: the view; expected: the counts of step 1",
            """\
SELECT COUNT(*) AS Entries, SUM(Weekend) AS Weekend,
    SUM(Backdated) AS Backdated, SUM(SelfApproved) AS SelfApproved,
    SUM(AboveLimit) AS AboveLimit, SUM(RoundAmount) AS RoundAmount,
    SUM(CASE WHEN RiskScore >= 2 THEN 1 ELSE 0 END) AS ScoreTwoOrMore
FROM Ex11_5_JournalEntryTests;""",
            [Check("entries in the view", v["entries"], lambda r: r.value("Entries"))] +
            [Check(f"{f} flags in the view", n, lambda r, f=f: r.value(f)) for f, n in counts.items()] +
            [Check("entries scoring 2 or more in the view", high, lambda r: r.value("ScoreTwoOrMore"))])
    missing = ", ".join(str(m) for m in v["missing"])
    flag_text = ", ".join(f"{f} {n}" for f, n in counts.items())
    score_text = ", ".join(f"{k}: {n:,}" for k, n in scores.items())
    s.answer("Requirement (3)", f"""\
The SQL tests give the counts of Tutorial 8.3 on all {v['entries']} journal entries: {flag_text}; scores {score_text}
(no entry scores {missing}, so that row does not appear). The highest score, {v['top_score']}, belongs to
{v['top_entry']}, the opening balance entry created by the chief financial officer. Weekend and Backdated read the
time-stamped CreatedDate (strftime and date take the date part), and RoundAmount compares the amount with its value
rounded to thousands, because the % operator truncates decimals in SQLite and is not safe on amounts.""")
    s.answer("Requirement (5)", """\
A saved query is stronger evidence than a formula copied down a column because it is one definition applied to the
whole population: it cannot skip rows, be overwritten in a single cell, or be left behind when new entries are
added, and anyone can rerun it on the same file and get the same result. Its text documents exactly how each flag is
calculated, so a reviewer can inspect the test itself rather than sample the cells, and next year's entries are
tested by running the view again, without rebuilding a workbook.""")


# --- Exercise 11.6 ---------------------------------------------------------------------------------------------------

AMOUNTS = """\
WITH Amounts AS (
    SELECT RequisitionID, RequisitionNumber, RequestDate,
        RequestedByEmployeeID, ApprovedByEmployeeID, Status,
        ROUND(Quantity * EstimatedUnitCost, 2) AS Amount
    FROM PurchaseRequisition
)"""

RUNS = """\
Neighbors AS (
    SELECT RequisitionID, Amount,
        LAG(Amount) OVER (ORDER BY RequisitionID) AS PreviousAmount,
        LEAD(Amount) OVER (ORDER BY RequisitionID) AS NextAmount,
        LAG(RequisitionID) OVER (ORDER BY RequisitionID) AS PreviousID,
        LEAD(RequisitionID) OVER (ORDER BY RequisitionID) AS NextID
    FROM Amounts
),
Runs AS (
    SELECT RequisitionID AS MiddleID, PreviousID, NextID
    FROM Neighbors
    WHERE Amount = PreviousAmount AND Amount = NextAmount
)"""


def ex6(b):
    v = context(b, "ex6")
    d = b.data
    band = d.q("SELECT RequisitionNumber, RequestedByEmployeeID, ApprovedByEmployeeID FROM PurchaseRequisition "
               "WHERE ROUND(Quantity * EstimatedUnitCost, 2) BETWEEN 4950 AND 4999.99 ORDER BY RequisitionID")
    members = d.q("SELECT RequisitionID, RequestedByEmployeeID, ApprovedByEmployeeID FROM PurchaseRequisition "
                  "WHERE RequisitionID BETWEEN ? AND ? OR RequisitionID BETWEEN ? AND ? ORDER BY RequisitionID",
                  v["middles"][0] - 1, v["middles"][0] + 1, v["middles"][1] - 1, v["middles"][1] + 1)
    cfo_title = d.one("SELECT JobTitle FROM Employee WHERE EmployeeID = ?", v["cfo"])
    s = b.script("Ex 11.6.sql", "requisitions just under the $5,000 approval limit, and runs that look split",
                 "the requisitions by $50 band; the runs of three equal amounts; the requisitions without an approver")
    s.query("Requirement (1): requisitions in $50 bands from $4,700 to $5,250",
            "Population: all purchase requisitions; expected: the band just below $5,000 the largest",
            f"""\
{AMOUNTS}
SELECT 4700 + 50 * CAST((Amount - 4700) / 50 AS INTEGER) AS BandFrom,
    COUNT(*) AS Requisitions
FROM Amounts
WHERE Amount >= 4700 AND Amount < 5250
GROUP BY BandFrom
ORDER BY BandFrom;""",
            [Check("bands", list(range(4700, 5250, 50)), lambda r: r.col("BandFrom")),
             Check("requisitions by band", v["bands"], lambda r: r.col("Requisitions"))])
    s.query("Requirement (2): the requisitions from $4,950.00 to $4,999.99",
            f"Population: all purchase requisitions; expected: {v['bands'][5]} requisitions",
            f"""\
{AMOUNTS}
SELECT a.RequisitionNumber, a.Amount, a.RequestDate, a.Status,
    a.RequestedByEmployeeID, rq.JobTitle AS RequestedBy,
    a.ApprovedByEmployeeID, ap.JobTitle AS ApprovedBy
FROM Amounts AS a
    INNER JOIN Employee AS rq ON rq.EmployeeID = a.RequestedByEmployeeID
    LEFT JOIN Employee AS ap ON ap.EmployeeID = a.ApprovedByEmployeeID
WHERE a.Amount BETWEEN 4950 AND 4999.99
ORDER BY a.Amount DESC, a.RequisitionNumber;""",
            [Check("requisitions in the band", len(band), len),
             Check("in the band without an approver", sum(1 for r in band if r[2] is None),
                   lambda r: r.col("ApprovedByEmployeeID").count(None))])
    s.query("Requirement (3): each run of three consecutive requisitions for the same amount",
            "Population: requisitions in RequisitionID order; expected: the rows of each run",
            f"""\
{AMOUNTS},
{RUNS}
SELECT r.MiddleID, a.RequisitionID, a.RequisitionNumber, a.RequestDate,
    a.Amount, a.RequestedByEmployeeID, a.ApprovedByEmployeeID, a.Status
FROM Runs AS r
    INNER JOIN Amounts AS a
        ON a.RequisitionID BETWEEN r.PreviousID AND r.NextID
ORDER BY a.RequisitionID;""",
            [Check("rows in the runs", 3 * len(v["middles"]), len),
             Check("middle rows flagged by LAG and LEAD", v["middles"], lambda r: sorted(set(r.col("MiddleID")))),
             Check("the requisitions", [m[0] for m in members], lambda r: r.col("RequisitionID")),
             Check("amount of every row", v["amount"], lambda r: max(r.col("Amount"))),
             Check("one amount", 1, lambda r: len(set(r.col("Amount")))),
             Check("requisitions without an approver", v["unapproved"],
                   lambda r: [i for i, a in zip(r.col("RequisitionID"), r.col("ApprovedByEmployeeID")) if a is None]),
             Check("statuses", ["Converted to PO"], lambda r: sorted(set(r.col("Status"))))])
    s.query("Requirement (4): the requesters and approvers of each run",
            "Population: the runs of three; expected: two runs, each with requisitions that have no approver",
            f"""\
{AMOUNTS},
{RUNS}
SELECT r.MiddleID, MIN(a.RequisitionNumber) AS FirstRequisition,
    MAX(a.RequisitionNumber) AS LastRequisition,
    MIN(a.RequestDate) AS RequestDate,
    GROUP_CONCAT(a.RequestedByEmployeeID, ', ') AS Requesters,
    GROUP_CONCAT(ap.JobTitle, ', ') AS Approvers,
    SUM(CASE WHEN a.ApprovedByEmployeeID IS NULL THEN 1 ELSE 0 END)
        AS WithoutApprover
FROM Runs AS r
    INNER JOIN Amounts AS a
        ON a.RequisitionID BETWEEN r.PreviousID AND r.NextID
    LEFT JOIN Employee AS ap ON ap.EmployeeID = a.ApprovedByEmployeeID
GROUP BY r.MiddleID
ORDER BY r.MiddleID;""",
            [Check("runs", len(v["runs"]), len)] +
            [c for i, run in enumerate(v["runs"]) for c in (
                Check(f"run {i + 1} first requisition", run["first"], lambda r, i=i: r.cell(i, "FirstRequisition")),
                Check(f"run {i + 1} date", run["date"], lambda r, i=i: r.cell(i, "RequestDate")),
                Check(f"run {i + 1} requesters", sorted(str(x) for x in run["requesters"]),
                      lambda r, i=i: sorted(r.cell(i, "Requesters").split(", "))),
                Check(f"run {i + 1} without an approver", 2, lambda r, i=i: r.cell(i, "WithoutApprover")),
                Check(f"run {i + 1} approver", cfo_title, lambda r, i=i: r.cell(i, "Approvers")))])
    runs = "; ".join(f"{run['first']} to {run['last']} on {run['date']} (requesters "
                     f"{', '.join(str(x) for x in run['requesters'])})" for run in v["runs"])
    s.answer("Requirement (5), memo to the audit senior", f"""\
To: the audit senior. Subject: requisitions just under the approval limit.

Counting requisitions in $50 bands from $4,700 to $5,250 gives {', '.join(str(n) for n in v['bands'])}: the band
from $4,950.00 to $4,999.99 holds {v['bands'][5]}, {'twice as many as' if v['twice'] else 'more than'} its
neighbors, just below the lowest nonzero approval limit of $5,000. LAG and LEAD find two runs of three consecutive
requisitions for the same amount, {money(v['amount'])}, each on January 1: {runs}. In each run two requisitions have
no approver and the third was approved by the {cfo_title.lower()}; all six were converted to purchase orders. The
unapproved ones are among the six requisitions without an approver of Exercise 2.5, and all six of those fall just
below $5,000 ({money(v['low'])} to {money(v['high'])}).

The pattern is consistent with a purchase split to stay under the limit and with requisitions that bypassed approval.
Next procedures: obtain the purchase orders and supplier invoices behind the two runs and test whether each run is a
single need; ask the requesters and the purchasing manager why the requisitions were raised separately and how they
were converted without approval; test the system control that should block conversion of an unapproved requisition;
and extend the band test to the other approval limits and to requisitions of the same item and requester within a
few days.""")


EXERCISES = [("11.1", ex1), ("11.2", ex2), ("11.3", ex3), ("11.4", ex4), ("11.5", ex5), ("11.6", ex6)]
