"""Instructor SQL solution to the Chapter 17 capstone case, "Financial Statements for a Lender": LenderPackage.sql, the
SQL part of the case's three files (with Charles River Lender Package.xlsx and Charles River Lender Review.pbix).

The script holds what the case gives to SQL (@tbl-17-02): the three trial balances (one query with its as-of date in a
Params CTE, rerun for each year-end), the accrued expenses rebuilt from their documents, the cutoff populations (tests
L5 to L8 of Audit.sql), the receivables aging and returns behind the passed items, and the note schedules, with the
records after the year-end. The queries whose results the Excel solution (xlbuild/cap17.py) pastes on its SQL Results
worksheet (LateInvoices, UnbilledLines, GroupAccounts, PayrollAccounts, ReceivableAging, ReturnsAfterYearEnd,
SegmentRevenue) return exactly those rows: each is checked row for row against the same computation the workbook
uses, so the two instructor files agree.

Every expected value comes from the context functions of the chapter's instructor notes (facts/notes/ch17.py) or from
read-only SQL of this module that mirrors the workbook's; every actual value is read from the query's result. Years are
the fiscal window's (F, P, C), so a rolled dataset rebuilds the script for its own window.
"""

from __future__ import annotations

import sys

from paths import REPO
from sqlbuild.script import Build, Check

FILE = "LenderPackage.sql"
TITLE = "the lender package: trial balances, accrued expenses, cutoff, and the note schedules"
DATABASE = "CharlesRiver_Capstone.sqlite (a copy of CharlesRiver.sqlite)"
GROUP_ORDER = ["Furniture", "Lighting", "Textiles", "Accessories"]
BUCKET_NAMES = ["Current", "1-30 days", "31-60 days", "61-90 days", "Over 90 days"]
WRITE_DOWN = ("Damaged", "Quality Concern")


def notes(b: Build):
    b.data                                       # puts facts/ on sys.path
    from notes import ch17
    return ch17


def context(b: Build, name: str) -> dict:
    return getattr(notes(b), name)(b.data, lambda *a, **k: None)


def audit_sql(key: str) -> str:
    """A test of Audit.sql as Tutorial 12.1 wrote it (the shared definitions of the book's figures)."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from shared.calculations.sql_ch12 import QUERIES
    return next(text for k, _, text in QUERIES if k == key)


def money(x: float) -> str:
    return f"{x:,.2f}"


def num(x: float) -> str:
    return f"{x:,.0f}"


def ye(year: int) -> str:
    return f"{year}-12-31"


def sub(text: str, col: int) -> str:
    """Multi-line SQL placed at column `col` of a query written in the source: every line after the first is
    indented by `col`, so that the query's own dedent keeps the inserted lines in place."""
    lines = text.split("\n")
    return "\n".join([lines[0]] + [" " * col + line if line else line for line in lines[1:]])


def r2(x):
    """A value as compared row for row: floats rounded to the cent."""
    return round(x, 2) if isinstance(x, float) else x


def rows2(r) -> list[list]:
    return [[r2(v) for v in row] for row in r.rows]


def script(b: Build):
    return b.script(FILE, TITLE,
                    "each trial balance balances and ties to Chapter 6; 2040 rebuilt to the ledger at each year-end; "
                    "cutoff reruns Audit.sql L5-L8; each note schedule ties to the ledger",
                    database=DATABASE)


CLOSES = """\
Closes AS (
    SELECT EntryNumber
    FROM JournalEntry
    WHERE EntryType LIKE 'Year-End Close%'
)"""


def year_ends(years) -> str:
    """A YearEnds CTE listing the as-of dates."""
    parts = [f"    SELECT '{ye(years[0])}' AS AsOfDate"] + [f"    UNION ALL\n    SELECT '{ye(y)}'" for y in years[1:]]
    return "YearEnds AS (\n" + "\n".join(parts) + "\n)"


def balances(years) -> str:
    """Each account's balance (debits less credits) at each year-end: postings on or before the date, a close left
    out only when it is dated on that date."""
    return year_ends(years) + ",\n" + CLOSES + """,
Balances AS (
    SELECT ye.AsOfDate, a.AccountID, a.AccountNumber, a.AccountName,
        a.AccountType, a.AccountSubType,
        SUM(gl.Debit - gl.Credit) AS Balance
    FROM YearEnds AS ye
        INNER JOIN GLEntry AS gl ON gl.PostingDate <= ye.AsOfDate
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE NOT (gl.VoucherNumber IN (SELECT EntryNumber FROM Closes)
        AND gl.PostingDate = ye.AsOfDate)
    GROUP BY ye.AsOfDate, a.AccountID, a.AccountNumber, a.AccountName,
        a.AccountType, a.AccountSubType
)"""


# --- Requirement 1: the trial balances and the recorded statements --------------------------------------------------

def tb_sql(asof: str) -> str:
    return f"""
        WITH Params AS (
            SELECT '{asof}' AS AsOfDate
        ),
        {sub(CLOSES, 8)}
        SELECT a.AccountNumber, a.AccountName, a.AccountType,
            a.AccountSubType,
            ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2) AS Balance,
            CASE WHEN SUM(gl.Debit) - SUM(gl.Credit) > 0
                THEN ROUND(SUM(gl.Debit) - SUM(gl.Credit), 2)
                ELSE 0 END AS DebitBalance,
            CASE WHEN SUM(gl.Debit) - SUM(gl.Credit) < 0
                THEN ROUND(SUM(gl.Credit) - SUM(gl.Debit), 2)
                ELSE 0 END AS CreditBalance,
            COUNT(*) AS Postings
        FROM GLEntry AS gl
            INNER JOIN Account AS a ON a.AccountID = gl.AccountID
        WHERE gl.PostingDate <= (SELECT AsOfDate FROM Params)
            AND NOT (gl.VoucherNumber IN (SELECT EntryNumber FROM Closes)
                AND gl.PostingDate = (SELECT AsOfDate FROM Params))
        GROUP BY a.AccountID, a.AccountNumber, a.AccountName,
            a.AccountType, a.AccountSubType
        ORDER BY a.AccountNumber;
        """


INCOME = """\
Income AS (
    SELECT gl.FiscalYear,
        SUM(CASE WHEN a.AccountSubType = 'Operating Revenue'
            THEN gl.Credit - gl.Debit ELSE 0 END) AS OperatingRevenue,
        SUM(CASE WHEN a.AccountSubType = 'Contra Revenue'
            THEN gl.Debit - gl.Credit ELSE 0 END) AS Returns,
        SUM(CASE WHEN a.AccountSubType = 'COGS'
            THEN gl.Debit - gl.Credit ELSE 0 END) AS CostOfGoodsSold,
        SUM(CASE WHEN a.AccountSubType = 'Operating Expense'
            THEN gl.Debit - gl.Credit ELSE 0 END) AS OperatingExpense,
        SUM(CASE WHEN a.AccountSubType = 'Other Expense'
            THEN gl.Debit - gl.Credit ELSE 0 END) AS InterestExpense,
        SUM(CASE WHEN a.AccountNumber = 7020
            THEN gl.Debit - gl.Credit ELSE 0 END) AS LossOnDisposal,
        SUM(gl.Credit - gl.Debit) AS NetIncome
    FROM GLEntry AS gl
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE a.AccountType IN ('Revenue', 'Expense')
        AND gl.VoucherNumber NOT IN (SELECT EntryNumber FROM Closes)
    GROUP BY gl.FiscalYear
)"""


def r1(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r1")
    rec = dict(zip(d.years, n["rec"]))
    for y in reversed(d.years):
        x = rec[y]
        s.query(f"Requirement 1: the trial balance at {ye(y)}, one query with its as-of date in a Params CTE",
                f"Population: GLEntry to {ye(y)}, a close left out only when dated then; expected: {x['n']} accounts, "
                f"{x['zero']} at zero, debit and credit balances of {money(x['debits'])}",
                tb_sql(ye(y)),
                [Check("accounts with postings", x["n"], len),
                 Check("accounts at zero", x["zero"], lambda r: sum(1 for v in r.col("Balance") if v == 0)),
                 Check("debit balances", x["debits"], lambda r: round(r.total("DebitBalance"), 2)),
                 Check("credit balances", x["credits"], lambda r: round(r.total("CreditBalance"), 2)),
                 Check("debit balances less credit balances", 0.0,
                       lambda r: round(r.total("DebitBalance") - r.total("CreditBalance"), 2))])

    closes = n["closes"]
    s.query("Requirement 1: net income of each fiscal year against its Income Summary close to retained earnings",
            f"Population: revenue and expense postings, closes excluded; expected: "
            f"{', '.join(money(v) for v in n['ni'])}, each equal to its close ({', '.join(closes)})",
            f"""
            WITH {sub(CLOSES, 12)},
            Closed AS (
                SELECT gl.FiscalYear,
                    SUM(gl.Credit - gl.Debit) AS ClosedToRetainedEarnings
                FROM GLEntry AS gl
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                    INNER JOIN JournalEntry AS je
                        ON je.EntryNumber = gl.VoucherNumber
                WHERE gl.SourceDocumentType = 'JournalEntry'
                    AND je.EntryType LIKE 'Year-End Close - Income Summary%'
                    AND a.AccountNumber = 3030
                GROUP BY gl.FiscalYear
            ),
            {sub(INCOME, 12)}
            SELECT i.FiscalYear, ROUND(i.NetIncome, 2) AS NetIncome,
                ROUND(c.ClosedToRetainedEarnings, 2) AS ClosedToRetainedEarnings
            FROM Income AS i
                INNER JOIN Closed AS c ON c.FiscalYear = i.FiscalYear
            ORDER BY i.FiscalYear;
            """,
            [Check("fiscal years", d.years, lambda r: r.col("FiscalYear")),
             Check("net income", n["ni"], lambda r: r.col("NetIncome")),
             Check("each equal to its close", n["ni"], lambda r: r.col("ClosedToRetainedEarnings"))])

    s.query("Requirement 1: the recorded balance sheet totals at the three year-ends",
            f"Population: the trial balances of the three year-ends; expected: total assets "
            f"{', '.join(money(rec[y]['ta']) for y in d.years)}",
            f"""
            WITH {sub(balances(d.years), 12)}
            SELECT AsOfDate,
                ROUND(SUM(CASE WHEN AccountType = 'Asset'
                    THEN Balance ELSE 0 END), 2) AS TotalAssets,
                ROUND(SUM(CASE WHEN AccountSubType IN ('Current Asset',
                    'Contra Current Asset') THEN Balance ELSE 0 END), 2)
                    AS CurrentAssets,
                ROUND(-SUM(CASE WHEN AccountSubType = 'Current Liability'
                    THEN Balance ELSE 0 END), 2) AS CurrentLiabilities,
                ROUND(-SUM(CASE WHEN AccountNumber = 2110
                    THEN Balance ELSE 0 END), 2) AS NotesPayable,
                ROUND(-SUM(CASE WHEN AccountNumber = 3030
                    THEN Balance ELSE 0 END), 2) AS RetainedEarnings,
                ROUND(-SUM(CASE WHEN AccountNumber = 3010
                    THEN Balance ELSE 0 END), 2) AS CommonStock
            FROM Balances
            GROUP BY AsOfDate
            ORDER BY AsOfDate;
            """,
            [c for y in d.years for k, col in (("ta", "TotalAssets"), ("ca", "CurrentAssets"),
                                                ("cl", "CurrentLiabilities"), ("notes", "NotesPayable"),
                                                ("re", "RetainedEarnings"), ("stock", "CommonStock"))
             for c in [Check(f"{y} {col}", rec[y][k], lambda r, y=y, col=col: r.where(AsOfDate=ye(y))[col])]])

    inc = dict(zip((d.P, d.C), n["inc"]))
    s.query(f"Requirement 1: the recorded statements of income, {d.P} and {d.C}, by AccountSubType",
            f"Population: revenue and expense postings, closes excluded; expected: operating income "
            f"{money(inc[d.P]['op'])} and {money(inc[d.C]['op'])}",
            f"""
            WITH {sub(CLOSES, 12)},
            {sub(INCOME, 12)}
            SELECT FiscalYear, ROUND(OperatingRevenue, 2) AS OperatingRevenue,
                ROUND(Returns, 2) AS Returns,
                ROUND(OperatingRevenue - Returns, 2) AS NetRevenue,
                ROUND(CostOfGoodsSold, 2) AS CostOfGoodsSold,
                ROUND(OperatingRevenue - Returns - CostOfGoodsSold, 2)
                    AS GrossMargin,
                ROUND(OperatingExpense, 2) AS OperatingExpense,
                ROUND(OperatingRevenue - Returns - CostOfGoodsSold
                    - OperatingExpense, 2) AS OperatingIncome,
                ROUND(InterestExpense, 2) AS InterestExpense,
                ROUND(LossOnDisposal, 2) AS LossOnDisposal,
                ROUND(NetIncome, 2) AS NetIncome
            FROM Income
            WHERE FiscalYear IN ({d.P}, {d.C})
            ORDER BY FiscalYear;
            """,
            [c for y in (d.P, d.C) for k, col in (("opr", "OperatingRevenue"), ("ret", "Returns"), ("net_rev", "NetRevenue"),
                                                  ("cogs", "CostOfGoodsSold"), ("gm", "GrossMargin"),
                                                  ("opx", "OperatingExpense"), ("op", "OperatingIncome"),
                                                  ("intr", "InterestExpense"), ("loss", "LossOnDisposal"),
                                                  ("ni", "NetIncome"))
             for c in [Check(f"{y} {col}", inc[y][k], lambda r, y=y, col=col: r.where(FiscalYear=y)[col])]])

    never = notes(b).never_posted(d)
    s.query("Requirement 1: the accounts never posted, with an anti-join",
            f"Population: the chart without its headers; expected: {n['n_never']} accounts, {n['n_active']} active "
            f"and {n['n_inactive']} inactive",
            """
            SELECT a.AccountNumber, a.AccountName, a.AccountType, a.IsActive
            FROM Account AS a
                LEFT JOIN GLEntry AS gl ON gl.AccountID = a.AccountID
            WHERE gl.GLEntryID IS NULL
                AND a.AccountSubType <> 'Header'
            ORDER BY a.AccountNumber;
            """,
            [Check("accounts", [int(x[0]) for x in never], lambda r: r.col("AccountNumber")),
             Check("active", n["n_active"], lambda r: sum(r.col("IsActive"))),
             Check("inactive", n["n_inactive"], lambda r: sum(1 for v in r.col("IsActive") if not v))])

    taxes = [nm for (nm,) in d.q("SELECT AccountName FROM Account WHERE AccountName LIKE '%Tax%' ORDER BY AccountNumber")]
    s.query("Requirement 1: the accounts named for taxes, to see what the chart lacks",
            "Population: the chart; expected: sales tax and payroll taxes only, no income tax account",
            """
            SELECT AccountNumber, AccountName, AccountType, AccountSubType
            FROM Account
            WHERE AccountName LIKE '%Tax%'
            ORDER BY AccountNumber;
            """,
            [Check("accounts named for taxes", taxes, lambda r: r.col("AccountName")),
             Check("accounts named for income tax", 0, lambda r: sum(1 for v in r.col("AccountName")
                                                                    if "income tax" in v.lower()))])

    s.answer("Requirement 1", f"""
        The trial balance is one query with its as-of date in a Params CTE, rerun for each year-end. It keeps every
        posting dated on or before the date and leaves out only the closes dated on it: the closes of earlier years
        moved those years' income into retained earnings, so leaving them out would count that income twice. At
        {', '.join(ye(y) for y in d.years)} it lists {', '.join(str(rec[y]['n']) for y in d.years)} accounts with
        debit and credit balances of {', '.join(money(rec[y]['debits']) for y in d.years)}; the last is Chapter 6's
        pre-closing trial balance, and each year's net income equals its Income Summary close to 3030.

        Never posted: {n['n_never']} accounts ({n['n_active']} active: {n['active']}; {n['n_inactive']} inactive:
        {n['inactive']}). The chart has no income tax account at all, neither an expense nor a payable: the accounts
        named for taxes are sales tax and payroll taxes. The unused 2080, 2120, 1140, 1030, and 7010 each lead to a
        later requirement.""")


def m1(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "m1")
    rec = dict(zip(d.years, n["rec"]))
    s.query("Milestone 1: the checkpoints of the ledger as it stands, at each year-end",
            f"Population: the trial balances of the three year-ends and the year's postings; expected: "
            f"{', '.join(str(rec[y]['n']) for y in d.years)} accounts; net income "
            f"{', '.join(money(v) for v in n['ni'])}",
            f"""
            WITH {sub(balances(d.years), 12)}
            SELECT b.AsOfDate, COUNT(*) AS Accounts,
                SUM(CASE WHEN ROUND(b.Balance, 2) = 0 THEN 1 ELSE 0 END)
                    AS AtZero,
                ROUND(SUM(CASE WHEN b.Balance > 0 THEN b.Balance ELSE 0 END), 2)
                    AS DebitBalances,
                ROUND(-SUM(CASE WHEN b.Balance < 0 THEN b.Balance ELSE 0 END), 2)
                    AS CreditBalances,
                ROUND(SUM(CASE WHEN b.AccountType = 'Asset'
                    THEN b.Balance ELSE 0 END), 2) AS TotalAssets,
                ROUND(-SUM(CASE WHEN b.AccountType IN ('Revenue', 'Expense')
                    THEN b.Balance ELSE 0 END), 2) AS NetIncome
            FROM Balances AS b
            GROUP BY b.AsOfDate
            ORDER BY b.AsOfDate;
            """,
            [c for y, ni in zip(d.years, n["ni"]) for c in (
                Check(f"{y} accounts", rec[y]["n"], lambda r, y=y: r.where(AsOfDate=ye(y))["Accounts"]),
                Check(f"{y} at zero", rec[y]["zero"], lambda r, y=y: r.where(AsOfDate=ye(y))["AtZero"]),
                Check(f"{y} debit balances", rec[y]["debits"], lambda r, y=y: r.where(AsOfDate=ye(y))["DebitBalances"]),
                Check(f"{y} credit balances", rec[y]["credits"], lambda r, y=y: r.where(AsOfDate=ye(y))["CreditBalances"]),
                Check(f"{y} total assets", rec[y]["ta"], lambda r, y=y: r.where(AsOfDate=ye(y))["TotalAssets"]),
                Check(f"{y} net income (the year's revenue and expense balances)", ni,
                      lambda r, y=y: r.where(AsOfDate=ye(y))["NetIncome"]))])


# --- Requirement 2: the review of the recorded statements ------------------------------------------------------------

def r2_(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r2")
    s.query("Requirement 2: the controller's materiality, 5% of income before income taxes as the ledger records it",
            f"Population: revenue and expense postings, closes excluded (no income tax is recorded); expected: "
            f"{money(n['mat_p'])} ({d.P}) and {money(n['mat_c'])} ({d.C})",
            f"""
            WITH {sub(CLOSES, 12)},
            {sub(INCOME, 12)}
            SELECT FiscalYear,
                ROUND(NetIncome, 2) AS IncomeBeforeIncomeTaxes,
                ROUND(NetIncome * 0.05, 2) AS Materiality
            FROM Income
            WHERE FiscalYear IN ({d.P}, {d.C})
            ORDER BY FiscalYear;
            """,
            [Check(f"{d.P} materiality", n["mat_p"], lambda r: r.where(FiscalYear=d.P)["Materiality"]),
             Check(f"{d.C} materiality", n["mat_c"], lambda r: r.where(FiscalYear=d.C)["Materiality"])])

    above = n["above"]
    s.query(f"Requirement 2: the changes from {ye(d.P)} to {ye(d.C)} above the {d.C} materiality",
            f"Population: the two trial balances, retained earnings aside; expected: {len(above)} accounts, "
            f"{', '.join(a['n'] for a in above)}",
            f"""
            WITH {sub(balances((d.P, d.C)), 12)},
            Changes AS (
                SELECT AccountNumber, AccountName,
                    SUM(CASE WHEN AsOfDate = '{ye(d.C)}' THEN Balance ELSE 0 END)
                    - SUM(CASE WHEN AsOfDate = '{ye(d.P)}' THEN Balance ELSE 0 END)
                        AS Change
                FROM Balances
                WHERE AccountNumber <> 3030
                GROUP BY AccountID, AccountNumber, AccountName
            )
            SELECT AccountNumber, AccountName, ROUND(Change, 2) AS Change
            FROM Changes
            WHERE ABS(Change) > {notes(b).materiality(d, d.C)}
            ORDER BY ABS(Change) DESC;
            """,
            [Check("accounts", [int(a["n"]) for a in above], lambda r: r.col("AccountNumber")),
             Check("changes on each account's normal side", [round(a["v"], 2) for a in above],
                   lambda r: [round(-v if a["credit"] else v, 2) for v, a in zip(r.col("Change"), above)])])

    entry = n["entry"]
    s.query(f"Requirement 2: the balances that rest on the opening entry {entry}",
            f"Population: the opening entry's {n['lines']} lines and every other posting to their accounts; expected: "
            f"1050 {money(n['prepaid'])} alone, 2030 {money(n['payroll'])} with the rest netting to zero",
            f"""
            WITH Opening AS (
                SELECT EntryNumber
                FROM JournalEntry
                WHERE EntryType = 'Opening'
            )
            SELECT a.AccountNumber, a.AccountName,
                ROUND(SUM(CASE WHEN gl.VoucherNumber IN (SELECT EntryNumber FROM Opening)
                    THEN gl.Debit - gl.Credit ELSE 0 END), 2) AS OpeningLine,
                SUM(CASE WHEN gl.VoucherNumber IN (SELECT EntryNumber FROM Opening)
                    THEN 0 ELSE 1 END) AS OtherPostings,
                ROUND(SUM(CASE WHEN gl.VoucherNumber IN (SELECT EntryNumber FROM Opening)
                    THEN 0 ELSE gl.Debit - gl.Credit END), 2) AS OtherNet
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.AccountID IN (
                SELECT AccountID
                FROM GLEntry
                WHERE VoucherNumber IN (SELECT EntryNumber FROM Opening))
            GROUP BY a.AccountID, a.AccountNumber, a.AccountName
            ORDER BY a.AccountNumber;
            """,
            [Check("accounts of the opening entry", n["lines"], len),
             Check("1050 opening line", n["prepaid"], lambda r: r.where(AccountNumber=1050)["OpeningLine"]),
             Check("1050 other postings", 0, lambda r: r.where(AccountNumber=1050)["OtherPostings"]),
             Check("2030 opening line", -n["payroll"], lambda r: r.where(AccountNumber=2030)["OpeningLine"]),
             Check("2030 other postings net", 0.0, lambda r: r.where(AccountNumber=2030)["OtherNet"]),
             Check("1020 opening line", n["receivable"], lambda r: r.where(AccountNumber=1020)["OpeningLine"]),
             Check("2010 opening line", -n["payable"], lambda r: r.where(AccountNumber=2010)["OpeningLine"]),
             Check("2010 equal to the opening cash line", n["payable"],
                   lambda r: r.where(AccountNumber=1010)["OpeningLine"]),
             Check("2040 opening line", -n["accrued"], lambda r: r.where(AccountNumber=2040)["OpeningLine"])])

    s.answer("Requirement 2", f"""
        Materiality is {money(n['mat_c'])} for {d.C} and {money(n['mat_p'])} for {d.P}. At a year-end a revenue or
        expense account's balance is that year's activity, because the prior close zeroed it, so the change for those
        accounts is this year's activity less last year's. The changes above {d.C} materiality, on each account's
        normal side, are {', '.join(f"{a['n']} {a['v']:+,.2f}" for a in above)}; retained earnings moves by {d.P}'s net income, closed into it. The opening
        entry ({entry}, {n['lines']} lines) supports nothing with a document: 1050 Prepaid Expenses
        {money(n['prepaid'])} is its only posting, 2030 Accrued Payroll keeps {money(n['payroll'])} because every
        payroll posting to it nets to zero, and parts of 1020 ({money(n['receivable'])}), 2010
        ({money(n['payable'])}, equal to the opening cash to the cent), and 2040 ({money(n['accrued'])}) rest on it.
        The questions go to the Questions table of the Review file, each with the requirement that answers it.""")


# --- Requirement 3: accrued expenses rebuilt -------------------------------------------------------------------------

ACCRUALS = """\
Accruals AS (
    SELECT je.JournalEntryID, je.EntryNumber, je.PostingDate,
        MAX(CASE WHEN gl.Debit > 0 THEN a.AccountNumber END)
            AS ExpenseAccount,
        SUM(CASE WHEN a.AccountNumber = 2040 THEN gl.Credit ELSE 0 END)
            AS Amount
    FROM JournalEntry AS je
        INNER JOIN GLEntry AS gl
            ON gl.SourceDocumentType = 'JournalEntry'
            AND gl.SourceDocumentID = je.JournalEntryID
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE je.EntryType = 'Accrual'
    GROUP BY je.JournalEntryID, je.EntryNumber, je.PostingDate
),
Clearing AS (
    SELECT pil.AccrualJournalEntryID AS JournalEntryID,
        gl.PostingDate, gl.Debit AS Amount, 'Invoice' AS Kind
    FROM PurchaseInvoiceLine AS pil
        INNER JOIN GLEntry AS gl
            ON gl.SourceDocumentType = 'PurchaseInvoice'
            AND gl.SourceDocumentID = pil.PurchaseInvoiceID
            AND gl.SourceLineID = pil.PILineID
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE pil.AccrualJournalEntryID IS NOT NULL
        AND a.AccountNumber = 2040
    UNION ALL
    SELECT je.ReversesJournalEntryID, je.PostingDate, gl.Debit,
        'Adjustment'
    FROM JournalEntry AS je
        INNER JOIN GLEntry AS gl
            ON gl.SourceDocumentType = 'JournalEntry'
            AND gl.SourceDocumentID = je.JournalEntryID
        INNER JOIN Account AS a ON a.AccountID = gl.AccountID
    WHERE je.EntryType = 'Accrual Adjustment'
        AND a.AccountNumber = 2040
),
Lags AS (
    SELECT ac.JournalEntryID,
        julianday(MIN(cl.PostingDate)) - julianday(ac.PostingDate)
            AS LagDays
    FROM Accruals AS ac
        INNER JOIN Clearing AS cl ON cl.JournalEntryID = ac.JournalEntryID
    WHERE cl.Kind = 'Invoice'
    GROUP BY ac.JournalEntryID, ac.PostingDate
)"""


def r3(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r3")
    comp = dict(zip(d.years, n["comp"]))
    s.query("Requirement 3: the populations behind 2040, accrual entries, the invoice lines and adjustments that "
            "clear them",
            f"Population: JournalEntry, PurchaseInvoiceLine, and their 2040 postings; expected: {n['n']} accruals, "
            f"{money(n['amount'])}; {n['n_lines']} lines clearing {money(n['cleared'])}; {n['n_adj']} adjustments",
            """
            SELECT
                (SELECT COUNT(*)
                 FROM JournalEntry
                 WHERE EntryType = 'Accrual') AS AccrualEntries,
                (SELECT ROUND(SUM(gl.Credit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN JournalEntry AS je
                         ON je.JournalEntryID = gl.SourceDocumentID
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE gl.SourceDocumentType = 'JournalEntry'
                     AND je.EntryType = 'Accrual'
                     AND a.AccountNumber = 2040) AS Accrued,
                (SELECT COUNT(*)
                 FROM PurchaseInvoiceLine
                 WHERE AccrualJournalEntryID IS NOT NULL) AS LinesReferring,
                (SELECT COUNT(DISTINCT AccrualJournalEntryID)
                 FROM PurchaseInvoiceLine) AS AccrualsReferred,
                (SELECT ROUND(SUM(gl.Debit), 2)
                 FROM PurchaseInvoiceLine AS pil
                     INNER JOIN GLEntry AS gl
                         ON gl.SourceDocumentType = 'PurchaseInvoice'
                         AND gl.SourceDocumentID = pil.PurchaseInvoiceID
                         AND gl.SourceLineID = pil.PILineID
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE pil.AccrualJournalEntryID IS NOT NULL
                     AND a.AccountNumber = 2040) AS ClearedByInvoices,
                (SELECT COUNT(*)
                 FROM PurchaseInvoiceLine
                 WHERE AccrualJournalEntryID IS NULL) AS LinesWithout,
                (SELECT COUNT(*)
                 FROM JournalEntry
                 WHERE EntryType = 'Accrual Adjustment') AS AdjustmentEntries,
                (SELECT COUNT(DISTINCT ReversesJournalEntryID)
                 FROM JournalEntry
                 WHERE EntryType = 'Accrual Adjustment') AS AdjustmentTargets,
                (SELECT ROUND(SUM(gl.Debit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN JournalEntry AS je
                         ON je.JournalEntryID = gl.SourceDocumentID
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE gl.SourceDocumentType = 'JournalEntry'
                     AND je.EntryType = 'Accrual Adjustment'
                     AND a.AccountNumber = 2040) AS ClearedByAdjustments;
            """,
            [Check("accrual entries", n["n"], lambda r: r.value("AccrualEntries")),
             Check("amount accrued", n["amount"], lambda r: r.value("Accrued")),
             Check("invoice lines referring to an accrual", n["n_lines"], lambda r: r.value("LinesReferring")),
             Check("at most one line per accrual", n["n_lines"], lambda r: r.value("AccrualsReferred")),
             Check("cleared by invoices", n["cleared"], lambda r: r.value("ClearedByInvoices")),
             Check("lines without an accrual", n["null_lines"], lambda r: r.value("LinesWithout")),
             Check("Accrual Adjustment entries", n["n_adj"], lambda r: r.value("AdjustmentEntries")),
             Check("their targets", n["targets"], lambda r: r.value("AdjustmentTargets")),
             Check("cleared by adjustments", n["adj_amount"], lambda r: r.value("ClearedByAdjustments"))])

    s.query("Requirement 3: invoice lines that cleared an accrual, the excess charged to expense by fiscal year",
            f"Population: the referring invoice lines' expense postings; expected: "
            f"{', '.join(money(v) for v in n['excess'])} on {', '.join(map(str, n['excess_lines']))} lines",
            """
            SELECT gl.FiscalYear, COUNT(DISTINCT pil.PILineID) AS Lines,
                ROUND(SUM(gl.Debit), 2) AS ExcessToExpense
            FROM PurchaseInvoiceLine AS pil
                INNER JOIN GLEntry AS gl
                    ON gl.SourceDocumentType = 'PurchaseInvoice'
                    AND gl.SourceDocumentID = pil.PurchaseInvoiceID
                    AND gl.SourceLineID = pil.PILineID
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE pil.AccrualJournalEntryID IS NOT NULL
                AND a.AccountType = 'Expense'
                AND gl.Debit > 0
            GROUP BY gl.FiscalYear
            ORDER BY gl.FiscalYear;
            """,
            [Check("fiscal years", d.years, lambda r: r.col("FiscalYear")),
             Check("lines", n["excess_lines"], lambda r: r.col("Lines")),
             Check("excess to expense", n["excess"], lambda r: r.col("ExcessToExpense"))])

    s.query("Requirement 3: how long invoices took to clear the accruals",
            f"Population: accruals cleared by an invoice; expected: {n['lag_low']} to {n['lag_high']} days, median "
            f"{n['median']}, {n['at_window']} at the longest",
            f"""
            WITH {sub(ACCRUALS, 12)},
            Ranked AS (
                SELECT LagDays,
                    ROW_NUMBER() OVER (ORDER BY LagDays) AS Position,
                    COUNT(*) OVER () AS Accruals
                FROM Lags
            )
            SELECT MAX(Accruals) AS Accruals, MIN(LagDays) AS Shortest,
                MAX(LagDays) AS Longest,
                MAX(CASE WHEN Position = Accruals / 2 + 1 THEN LagDays END)
                    AS Median,
                SUM(CASE WHEN LagDays = (SELECT MAX(LagDays) FROM Lags)
                    THEN 1 ELSE 0 END) AS AtLongest
            FROM Ranked;
            """,
            [Check("shortest", float(n["lag_low"]), lambda r: r.value("Shortest")),
             Check("longest", float(n["lag_high"]), lambda r: r.value("Longest")),
             Check("median", float(n["median"]), lambda r: r.value("Median")),
             Check("at the longest", notes(b).accruals(d)["lags"].count(n["window"]), lambda r: r.value("AtLongest"))])

    s.query("Requirement 3: the open accruals at each year-end saved as a view, aged against the longest wait",
            "Population: Accrual entries less what cleared them by each year-end; expected: the view OpenAccruals",
            f"""
            DROP VIEW IF EXISTS OpenAccruals;
            CREATE VIEW OpenAccruals AS
            WITH {sub(year_ends(d.years), 12)},
            {sub(ACCRUALS, 12)},
            Cleared AS (
                SELECT ye.AsOfDate, ac.JournalEntryID,
                    SUM(CASE WHEN cl.PostingDate <= ye.AsOfDate
                        THEN cl.Amount ELSE 0 END) AS Cleared
                FROM YearEnds AS ye
                    INNER JOIN Accruals AS ac ON ac.PostingDate <= ye.AsOfDate
                    LEFT JOIN Clearing AS cl
                        ON cl.JournalEntryID = ac.JournalEntryID
                GROUP BY ye.AsOfDate, ac.JournalEntryID
            )
            SELECT c.AsOfDate, ac.JournalEntryID, ac.EntryNumber,
                ac.PostingDate, ac.ExpenseAccount, ac.Amount, c.Cleared,
                ROUND(ac.Amount - c.Cleared, 2) AS OpenAmount,
                julianday(c.AsOfDate) - julianday(ac.PostingDate) AS AgeDays,
                CASE WHEN julianday(c.AsOfDate) - julianday(ac.PostingDate)
                    > (SELECT MAX(LagDays) FROM Lags)
                    THEN 1 ELSE 0 END AS IsOld,
                CASE WHEN ac.JournalEntryID IN (
                    SELECT JournalEntryID FROM Clearing WHERE Kind = 'Invoice')
                    THEN 1 ELSE 0 END AS Invoiced
            FROM Cleared AS c
                INNER JOIN Accruals AS ac ON ac.JournalEntryID = c.JournalEntryID
            WHERE ROUND(ac.Amount - c.Cleared, 2) > 0;
            """)

    s.query("Requirement 3: the open accruals at each year-end, within the clearing window and older",
            f"Population: the view OpenAccruals; expected: old items {', '.join(money(comp[y]['old']) for y in d.years)} "
            f"({', '.join(str(comp[y]['n_old']) for y in d.years)})",
            """
            SELECT AsOfDate,
                SUM(CASE WHEN IsOld = 0 THEN 1 ELSE 0 END) AS YoungItems,
                ROUND(SUM(CASE WHEN IsOld = 0 THEN OpenAmount ELSE 0 END), 2)
                    AS Young,
                SUM(IsOld) AS OldItems,
                ROUND(SUM(CASE WHEN IsOld = 1 THEN OpenAmount ELSE 0 END), 2)
                    AS Old
            FROM OpenAccruals
            GROUP BY AsOfDate
            ORDER BY AsOfDate;
            """,
            [c for y in d.years for c in (
                Check(f"{y} young", comp[y]["young"], lambda r, y=y: r.where(AsOfDate=ye(y))["Young"]),
                Check(f"{y} old", comp[y]["old"], lambda r, y=y: r.where(AsOfDate=ye(y))["Old"]),
                Check(f"{y} old items", comp[y]["n_old"], lambda r, y=y: r.where(AsOfDate=ye(y))["OldItems"]))])

    wrong = n["wrong"]
    s.query("Requirement 3: the accruals a rule of older than the last two month-ends would flag inside the window",
            f"Population: the view OpenAccruals, accruals dated before November and within the window; expected: "
            + ", ".join(f"{w['number']} at {ye(w['year'])}, {w['age']} days old, invoiced on {w['cleared']}" for w in wrong),
            """
            SELECT oa.AsOfDate, oa.EntryNumber, oa.PostingDate, oa.AgeDays,
                oa.OpenAmount,
                (SELECT MIN(gl.PostingDate)
                 FROM PurchaseInvoiceLine AS pil
                     INNER JOIN GLEntry AS gl
                         ON gl.SourceDocumentType = 'PurchaseInvoice'
                         AND gl.SourceDocumentID = pil.PurchaseInvoiceID
                         AND gl.SourceLineID = pil.PILineID
                 WHERE pil.AccrualJournalEntryID = oa.JournalEntryID)
                    AS InvoicedOn
            FROM OpenAccruals AS oa
            WHERE oa.IsOld = 0
                AND oa.PostingDate < date(oa.AsOfDate, 'start of month',
                    '-1 month')
            ORDER BY oa.AsOfDate, oa.EntryNumber;
            """,
            [Check("flagged though inside the window, and invoiced after the year-end",
                   [[ye(w["year"]), w["number"], float(w["age"]), w["cleared"]] for w in wrong],
                   lambda r: [[x[0], x[1], x[3], x[5]] for x in r.rows if x[5] and x[5] > x[0]])])

    s.query("Requirement 3: the freight accrued on shipments and the settlements that pay the carriers",
            f"Population: postings to 2040 and 5050, closes excluded; expected: shipment credits {money(n['shipped'])} "
            f"equal to the 5050 debits; {n['settlements']} settlements, {money(n['settled'])}",
            """
            SELECT
                (SELECT ROUND(SUM(gl.Credit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 2040
                     AND gl.SourceDocumentType = 'Shipment') AS ShipmentCredits,
                (SELECT ROUND(SUM(gl.Debit - gl.Credit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 5050
                     AND gl.VoucherNumber NOT IN (
                         SELECT EntryNumber
                         FROM JournalEntry
                         WHERE EntryType LIKE 'Year-End Close%')) AS FreightOut5050,
                (SELECT COUNT(*)
                 FROM JournalEntry
                 WHERE EntryType = 'Freight Settlement') AS Settlements,
                (SELECT ROUND(SUM(TotalAmount), 2)
                 FROM JournalEntry
                 WHERE EntryType = 'Freight Settlement') AS Settled,
                (SELECT MAX(PostingDate)
                 FROM JournalEntry
                 WHERE EntryType = 'Freight Settlement') AS LastSettlement;
            """,
            [Check("shipment credits to 2040", n["shipped"], lambda r: r.value("ShipmentCredits")),
             Check("equal to the 5050 debits", n["shipped"], lambda r: r.value("FreightOut5050")),
             Check("settlements", n["settlements"], lambda r: r.value("Settlements")),
             Check("settled", n["settled"], lambda r: r.value("Settled")),
             Check(f"none in the data for December {d.C}", True, lambda r: r.value("LastSettlement") <= ye(d.C))])

    s.query("Requirement 3: account 2040 at each year-end split into its parts and reconciled to the ledger",
            f"Population: the opening line, shipment freight less settlements, the view OpenAccruals, and 2040's "
            f"balance; expected: {', '.join(money(comp[y]['total']) for y in d.years)}, no difference",
            f"""
            WITH {sub(year_ends(d.years), 12)},
            Postings AS (
                SELECT gl.PostingDate, gl.SourceDocumentType, gl.Debit,
                    gl.Credit, je.EntryType
                FROM GLEntry AS gl
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                    LEFT JOIN JournalEntry AS je
                        ON gl.SourceDocumentType = 'JournalEntry'
                        AND je.JournalEntryID = gl.SourceDocumentID
                WHERE a.AccountNumber = 2040
            ),
            Parts AS (
                SELECT ye.AsOfDate,
                    SUM(CASE WHEN p.EntryType = 'Opening'
                        THEN p.Credit - p.Debit ELSE 0 END) AS Opening,
                    SUM(CASE WHEN p.SourceDocumentType = 'Shipment'
                        THEN p.Credit ELSE 0 END)
                    - SUM(CASE WHEN p.EntryType = 'Freight Settlement'
                        THEN p.Debit ELSE 0 END) AS Freight,
                    SUM(CASE WHEN p.SourceDocumentType = 'Shipment'
                        AND p.PostingDate >= date(ye.AsOfDate, 'start of month')
                        THEN p.Credit ELSE 0 END) AS DecemberFreight,
                    SUM(p.Credit - p.Debit) AS Ledger
                FROM YearEnds AS ye
                    INNER JOIN Postings AS p ON p.PostingDate <= ye.AsOfDate
                GROUP BY ye.AsOfDate
            )
            SELECT pa.AsOfDate, ROUND(pa.Opening, 2) AS Opening,
                ROUND(pa.Freight, 2) AS FreightNotSettled,
                ROUND(pa.DecemberFreight, 2) AS DecemberFreight,
                ROUND(SUM(CASE WHEN oa.IsOld = 0 THEN oa.OpenAmount ELSE 0 END), 2)
                    AS YoungAccruals,
                ROUND(SUM(CASE WHEN oa.IsOld = 1 THEN oa.OpenAmount ELSE 0 END), 2)
                    AS OldAccruals,
                ROUND(pa.Opening + pa.Freight + SUM(oa.OpenAmount), 2) AS Parts,
                ROUND(pa.Ledger, 2) AS Ledger,
                ROUND(pa.Opening + pa.Freight + SUM(oa.OpenAmount)
                    - pa.Ledger, 2) AS Difference
            FROM Parts AS pa
                INNER JOIN OpenAccruals AS oa ON oa.AsOfDate = pa.AsOfDate
            GROUP BY pa.AsOfDate, pa.Opening, pa.Freight, pa.DecemberFreight,
                pa.Ledger
            ORDER BY pa.AsOfDate;
            """,
            [c for y in d.years for k, col in (("opening", "Opening"), ("freight", "FreightNotSettled"),
                                                ("december", "DecemberFreight"), ("young", "YoungAccruals"),
                                                ("old", "OldAccruals"), ("total", "Parts"), ("ledger", "Ledger"))
             for c in [Check(f"{y} {col}", comp[y][k], lambda r, y=y, col=col: r.where(AsOfDate=ye(y))[col])]]
            + [Check("no difference at any year-end", [0.0] * len(d.years),
                     lambda r: [abs(v) for v in r.col("Difference")])])

    last = d.C
    s.query(f"Requirement 3: the accruals older than the window at {ye(last)}, the items to reverse",
            f"Population: the view OpenAccruals at {ye(last)}; expected: {n['n_old']} items, "
            f"{money(comp[last]['old'])}, none ever invoiced",
            f"""
            SELECT EntryNumber, PostingDate, ExpenseAccount,
                ROUND(Amount, 2) AS Amount, ROUND(Cleared, 2) AS Cleared,
                OpenAmount, AgeDays, Invoiced
            FROM OpenAccruals
            WHERE AsOfDate = '{ye(last)}'
                AND IsOld = 1
            ORDER BY PostingDate, EntryNumber;
            """,
            [Check("items", n["n_old"], len),
             Check("open amount", comp[last]["old"], lambda r: round(r.total("OpenAmount"), 2)),
             Check("none invoiced", 0, lambda r: r.total("Invoiced")),
             Check("partly cleared by a cleanup", n["cleanups"], lambda r: sum(1 for v in r.col("Cleared") if v > 0))]
            + [Check(f"recorded in {y}", [v, k], lambda r, y=y: [round(sum(x[5] for x in r.rows if x[1][:4] == str(y)), 2),
                                                                  sum(1 for x in r.rows if x[1][:4] == str(y))])
               for y, v, k in n["by_year"]]
            + [Check(f"expense account {a}", v, lambda r, a=a: round(sum(x[5] for x in r.rows if str(x[2]) == a), 2))
               for a, v in n["by_account"]])

    yf, yp = n["young_f"], n["young_p"]
    s.query(f"Requirement 3: accruals young at {ye(d.F)} or {ye(d.P)} that no invoice ever cleared, and what of them "
            f"is open at {ye(d.C)}",
            f"Population: the view OpenAccruals; expected: {money(yf['left'])} of {d.F}'s young items and "
            f"{money(yp['left'])} of {d.P}'s still open at {ye(d.C)}",
            f"""
            SELECT y.AsOfDate, y.EntryNumber, y.PostingDate,
                y.OpenAmount AS OpenThen,
                COALESCE(c.OpenAmount, 0) AS OpenAt{d.C}
            FROM OpenAccruals AS y
                LEFT JOIN OpenAccruals AS c
                    ON c.JournalEntryID = y.JournalEntryID
                    AND c.AsOfDate = '{ye(d.C)}'
            WHERE y.AsOfDate IN ('{ye(d.F)}', '{ye(d.P)}')
                AND y.IsOld = 0
                AND y.Invoiced = 0
            ORDER BY y.AsOfDate, y.EntryNumber;
            """,
            [Check(f"{d.F} items", yf["entries"], lambda r: [x[1] for x in r.rows if x[0] == ye(d.F)]),
             Check(f"{d.P} items", yp["entries"], lambda r: [x[1] for x in r.rows if x[0] == ye(d.P)]),
             Check(f"{d.F} items open at {ye(d.C)}", yf["left"],
                   lambda r: round(sum(x[4] for x in r.rows if x[0] == ye(d.F)), 2)),
             Check(f"{d.P} items open at {ye(d.C)}", yp["left"],
                   lambda r: round(sum(x[4] for x in r.rows if x[0] == ye(d.P)), 2))])

    a3 = n["a3"]
    s.answer("Requirement 3", f"""
        Account 2040 at {', '.join(ye(y) for y in d.years)} is the opening line {money(n['opening'])} (no document),
        the freight accrued on shipments and not yet settled ({', '.join(money(comp[y]['freight']) for y in d.years)}),
        the accruals open {n['window']} days or less ({', '.join(money(comp[y]['young']) for y in d.years)}), and the
        accruals open longer ({', '.join(money(comp[y]['old']) for y in d.years)}): in total
        {', '.join(money(comp[y]['total']) for y in d.years)}, equal to the ledger. Invoices cleared accruals in
        {n['lag_low']} to {n['lag_high']} days (median {n['median']}), and {n['at_window']} cleared at exactly
        {n['window']} days, so "older than {n['window']} days" is the rule.

        An accrual past the invoicing window at a year-end should have been reversed then, because the facts existed:
        the old items are corrections of errors at each year-end (retained earnings at 1 January {d.P}
        {a3['re']:+,.2f}; {d.P} expense {-a3['P']:+,.2f}; {d.C} expense {-a3['C']:+,.2f}). An accrual within the window
        is an estimate, and one that later proves unneeded is a change in estimate in the year it goes stale. Keep the
        {money(n['young_c'])} of young {d.C} accruals, and leave the {money(n['opening'])} to Requirement 9.""")


# --- Requirement 4: cutoff -------------------------------------------------------------------------------------------

SHIPPED = """\
Shipped AS (
    SELECT sil.SalesInvoiceID, MAX(s.DeliveryDate) AS DeliveryDate
    FROM SalesInvoiceLine AS sil
        INNER JOIN ShipmentLine AS sl
            ON sl.ShipmentLineID = sil.ShipmentLineID
        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
    GROUP BY sil.SalesInvoiceID
),
Posted AS (
    SELECT SourceDocumentID AS SalesInvoiceID,
        MIN(PostingDate) AS PostingDate
    FROM GLEntry
    WHERE SourceDocumentType = 'SalesInvoice'
    GROUP BY SourceDocumentID
)"""

UNBILLED_FROM = """\
FROM ShipmentLine AS sl
    INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
    INNER JOIN SalesOrderLine AS sol
        ON sol.SalesOrderLineID = sl.SalesOrderLineID
    INNER JOIN Item AS i ON i.ItemID = sl.ItemID
    INNER JOIN SalesOrder AS so ON so.SalesOrderID = s.SalesOrderID
    INNER JOIN Customer AS c ON c.CustomerID = so.CustomerID
    LEFT JOIN SalesInvoiceLine AS sil
        ON sil.ShipmentLineID = sl.ShipmentLineID
WHERE sil.SalesInvoiceLineID IS NULL"""


def unbilled_rows(d) -> list[list]:
    """The workbook's UnbilledLines (xlbuild/cap17.unbilled_lines), computed the same way."""
    return [list(r) for r in d.q(
        "SELECT sl.ShipmentLineID, s.ShipmentNumber, s.ShipmentDate, s.DeliveryDate, i.ItemCode, i.ItemGroup, "
        "c.CustomerSegment, sl.QuantityShipped, sol.UnitPrice, sol.Discount, sl.ExtendedStandardCost, "
        "ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2) FROM ShipmentLine sl "
        "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID JOIN SalesOrderLine sol ON sol.SalesOrderLineID = sl.SalesOrderLineID "
        "JOIN Item i ON i.ItemID = sl.ItemID JOIN SalesOrder so ON so.SalesOrderID = s.SalesOrderID "
        "JOIN Customer c ON c.CustomerID = so.CustomerID LEFT JOIN SalesInvoiceLine sil ON sil.ShipmentLineID = sl.ShipmentLineID "
        "WHERE sil.SalesInvoiceLineID IS NULL ORDER BY sl.ShipmentLineID")]


def cutoff_groups(b: Build) -> list[str]:
    """The item-group columns of the workbook's LateInvoices (xlbuild/cap17.cutoff_groups)."""
    d = b.data
    groups = {g for i in notes(b).late(d) for g in i["groups"]} | {u[5] for u in unbilled_rows(d)}
    return [g for g in GROUP_ORDER if g in groups] + sorted(g for g in groups if g not in GROUP_ORDER)


def periods_sql(d) -> str:
    return f"""\
LastEight AS (
    SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate
    FROM PayrollPeriod
    WHERE Status = 'Processed'
    ORDER BY PeriodEndDate DESC
    LIMIT 8
),
Days AS (
    SELECT
        (SELECT COUNT(DISTINCT CalendarDate)
         FROM WorkCenterCalendar
         WHERE IsWorkingDay = 1
             AND CalendarDate
                 BETWEEN (SELECT MIN(PeriodStartDate) FROM LastEight)
                 AND (SELECT MAX(PeriodEndDate) FROM LastEight)) AS PeriodDays,
        (SELECT COUNT(DISTINCT CalendarDate)
         FROM WorkCenterCalendar
         WHERE IsWorkingDay = 1
             AND CalendarDate > (SELECT MAX(PeriodEndDate) FROM LastEight)
             AND CalendarDate <= '{ye(d.C)}') AS DaysLeft
)"""


def r4(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r4")
    ch = notes(b)
    groups = cutoff_groups(b)
    late = sorted(ch.late(d), key=lambda i: (i["posted"], i["number"]))
    expected_late = [[i["number"], i["date"], i["posted"], i["delivered"], i["segment"], i["sub"], i["tax"], i["freight"]]
                     + [i["groups"].get(g, 0.0) for g in groups] for i in late]
    columns = ",\n".join(f"    ROUND(SUM(CASE WHEN i.ItemGroup = '{g}'\n        THEN sil.LineTotal ELSE 0 END), 2) AS {g}"
                         for g in groups)
    cf, cp, cc = n["cf"], n["cp"], n["cc"]
    s.query("Requirement 4: test L5, invoices posted in another year than the latest delivery they bill "
            "(LateInvoices)",
            f"Population: every sales invoice with shipped lines; expected: {cf['n']} for {d.F} deliveries "
            f"({money(cf['total'])}) and {cp['n']} for {d.P} ({money(cp['total'])})",
            f"""
            WITH {sub(SHIPPED, 12)}
            SELECT si.InvoiceNumber, si.InvoiceDate, p.PostingDate,
                sh.DeliveryDate, c.CustomerSegment, si.SubTotal,
                si.TaxAmount, si.FreightAmount,
            {sub(columns, 12)}
            FROM SalesInvoice AS si
                INNER JOIN Shipped AS sh ON sh.SalesInvoiceID = si.SalesInvoiceID
                INNER JOIN Posted AS p ON p.SalesInvoiceID = si.SalesInvoiceID
                INNER JOIN Customer AS c ON c.CustomerID = si.CustomerID
                INNER JOIN SalesInvoiceLine AS sil
                    ON sil.SalesInvoiceID = si.SalesInvoiceID
                INNER JOIN Item AS i ON i.ItemID = sil.ItemID
            WHERE strftime('%Y', p.PostingDate) <> strftime('%Y', sh.DeliveryDate)
            GROUP BY si.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate,
                p.PostingDate, sh.DeliveryDate, c.CustomerSegment,
                si.SubTotal, si.TaxAmount, si.FreightAmount
            ORDER BY p.PostingDate, si.InvoiceNumber;
            """,
            [Check("the rows the workbook pastes (LateInvoices)", [[r2(v) for v in row] for row in expected_late], rows2)]
            + [c for y, x in ((d.F, cf), (d.P, cp)) for c in (
                Check(f"{y} deliveries: invoices", x["n"], lambda r, y=y: sum(1 for v in r.col("DeliveryDate")
                                                                            if v[:4] == str(y))),
                Check(f"{y} deliveries: SubTotal", x["total"], lambda r, y=y: round(sum(
                    row[5] for row in r.rows if row[3][:4] == str(y)), 2)),
                Check(f"{y} deliveries: tax", x["tax"], lambda r, y=y: round(sum(
                    row[6] for row in r.rows if row[3][:4] == str(y)), 2)))]
            + [Check("freight on these invoices", n["late_freight"], lambda r: round(r.total("FreightAmount"), 2))]
            + [Check(f"{y} {seg}", v, lambda r, y=y, seg=seg: round(sum(row[5] for row in r.rows
                                                                      if row[3][:4] == str(y) and row[4] == seg), 2))
               for y, x in ((d.F, cf), (d.P, cp)) for seg, v in x["segments"]]
            + [Check(f"{y} {g}", v, lambda r, y=y, g=g: round(sum(row[r.columns.index(g)] for row in r.rows
                                                                if row[3][:4] == str(y)), 2))
               for y, x in ((d.F, cf), (d.P, cp)) for g, v in x["groups"]])

    expected_unbilled = unbilled_rows(d)
    s.query("Requirement 4: test L6, shipment lines never invoiced, at order price less discount (UnbilledLines)",
            f"Population: every shipment line; expected: {cc['n_lines']} December {d.C} lines, {money(cc['total'])} "
            f"at order price, standard cost {money(cc['std'])}",
            f"""
            SELECT sl.ShipmentLineID, s.ShipmentNumber, s.ShipmentDate,
                s.DeliveryDate, i.ItemCode, i.ItemGroup, c.CustomerSegment,
                sl.QuantityShipped, sol.UnitPrice, sol.Discount,
                sl.ExtendedStandardCost,
                ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2)
                    AS Value
            {sub(UNBILLED_FROM, 12)}
            ORDER BY sl.ShipmentLineID;
            """,
            [Check("the rows the workbook pastes (UnbilledLines)", [[r2(v) for v in row] for row in expected_unbilled],
                   rows2),
             Check("value at order price", cc["total"], lambda r: round(r.total("Value"), 2)),
             Check("standard cost", cc["std"], lambda r: round(r.total("ExtendedStandardCost"), 2))]
            + [Check(f"{seg}", v, lambda r, seg=seg: round(sum(x[11] for x in r.rows if x[6] == seg), 2))
               for seg, v in cc["segments"]]
            + [Check(f"{g}", v, lambda r, g=g: round(sum(x[11] for x in r.rows if x[5] == g), 2)) for g, v in cc["groups"]])

    accounts = ch.revenue_accounts(d)
    expected_groups = [[g, int(accounts[g])] for g in GROUP_ORDER + sorted(set(accounts) - set(GROUP_ORDER))
                       if g in accounts]
    s.query("Requirement 4: the revenue account each item group's invoice lines are credited to (GroupAccounts)",
            f"Population: SalesInvoice postings joined to their invoice lines and items; expected: "
            f"{len(expected_groups)} item groups, one account each",
            """
            SELECT i.ItemGroup, a.AccountNumber AS RevenueAccount
            FROM GLEntry AS gl
                INNER JOIN SalesInvoiceLine AS sil
                    ON sil.SalesInvoiceID = gl.SourceDocumentID
                    AND sil.SalesInvoiceLineID = gl.SourceLineID
                INNER JOIN Item AS i ON i.ItemID = sil.ItemID
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.SourceDocumentType = 'SalesInvoice'
                AND a.AccountSubType = 'Operating Revenue'
            GROUP BY i.ItemGroup, a.AccountID, a.AccountNumber
            ORDER BY CASE i.ItemGroup
                    WHEN 'Furniture' THEN 1 WHEN 'Lighting' THEN 2
                    WHEN 'Textiles' THEN 3 WHEN 'Accessories' THEN 4
                    ELSE 5 END,
                i.ItemGroup;
            """,
            [Check("the rows the workbook pastes (GroupAccounts)", expected_groups, lambda r: [list(x) for x in r.rows])])

    pf, pp, pc = n["pf"], n["pp"], n["pc"]
    l7 = audit_sql("payroll_cutoff")
    last_starts = [x[0] for x in d.q("SELECT PeriodStartDate FROM PayrollPeriod WHERE PayrollPeriodID IN (%s) ORDER BY 1"
                                     % ",".join(map(str, pc["periods"])))]
    s.query("Requirement 4: test L7 of Audit.sql rerun, the pay periods that cross each year-end",
            f"Population: every pay period; expected: the periods of {pf['full']['start']} and "
            f"{pf['cross']['start']}, {pp['full']['start']} and {pp['cross']['start']}, and two {d.C} periods with no "
            f"registers",
            l7,
            [Check("periods starting", [pf["full"]["start"], pf["cross"]["start"], pp["full"]["start"],
                                        pp["cross"]["start"]] + last_starts,
                   lambda r: r.col("PeriodStartDate")),
             Check(f"registers of the {d.C} periods", [0] * len(pc["periods"]),
                   lambda r: [x[5] for x in r.rows if x[1][:4] == str(d.C)]),
             Check(f"cost of the period of {pf['full']['start']}", pf["full"]["cost"],
                   lambda r: r.where(PeriodStartDate=pf["full"]["start"])["PayrollCost"]),
             Check(f"cost of the period of {pp['full']['start']}", pp["full"]["cost"],
                   lambda r: r.where(PeriodStartDate=pp["full"]["start"])["PayrollCost"])])

    opening_2030 = ch.opening_line(d, "2030")
    others_2030 = round(d.one("SELECT COALESCE(SUM(g.Credit - g.Debit), 0) FROM GLEntry g WHERE g.AccountID = ? AND "
                              "g.PostingDate <= ? AND g.SourceDocumentType <> 'JournalEntry'", d.account("2030"), ye(d.C)), 2)
    s.query("Requirement 4: test L8 of Audit.sql rerun, account 2030 at the year-end by source document type",
            f"Population: account 2030 to {ye(d.C)}; expected: the opening {money(opening_2030)} alone, the payroll "
            f"postings netting to zero, so no year-end has accrued wages",
            audit_sql("accrued_payroll").replace("'2026-12-31'", f"'{ye(d.C)}'"),
            [Check("the opening line", opening_2030, lambda r: r.where(SourceDocumentType="JournalEntry")["Balance"]),
             Check("the payroll postings net", others_2030,
                   lambda r: round(sum(x[2] for x in r.rows if x[0] != "JournalEntry"), 2))])

    s.query(f"Requirement 4: the payroll owed at {ye(d.F)} and {ye(d.P)}, the registers of the periods paid after "
            f"the year-end prorated by working day",
            f"Population: PayrollPeriod and PayrollRegister, WorkCenterCalendar; expected: {money(pf['total'])} and "
            f"{money(pp['total'])}",
            f"""
            WITH {sub(year_ends((d.F, d.P)), 12)},
            Periods AS (
                SELECT ye.AsOfDate, pp.PayrollPeriodID,
                    (SELECT COUNT(DISTINCT c.CalendarDate)
                     FROM WorkCenterCalendar AS c
                     WHERE c.IsWorkingDay = 1
                         AND c.CalendarDate BETWEEN pp.PeriodStartDate
                             AND pp.PeriodEndDate
                         AND c.CalendarDate <= ye.AsOfDate) AS DaysInYear,
                    (SELECT COUNT(DISTINCT c.CalendarDate)
                     FROM WorkCenterCalendar AS c
                     WHERE c.IsWorkingDay = 1
                         AND c.CalendarDate BETWEEN pp.PeriodStartDate
                             AND pp.PeriodEndDate) AS WorkingDays
                FROM YearEnds AS ye
                    INNER JOIN PayrollPeriod AS pp
                        ON pp.PeriodStartDate <= ye.AsOfDate
                        AND pp.PayDate > ye.AsOfDate
            )
            SELECT p.AsOfDate, COUNT(DISTINCT p.PayrollPeriodID) AS Periods,
                ROUND(SUM((pr.GrossPay + pr.EmployerPayrollTax
                    + pr.EmployerBenefits) * p.DaysInYear / p.WorkingDays), 2)
                    AS PayrollOwed,
                ROUND(SUM(pr.GrossPay * p.DaysInYear / p.WorkingDays), 2)
                    AS GrossPay,
                ROUND(SUM(pr.EmployerPayrollTax * p.DaysInYear / p.WorkingDays), 2)
                    AS EmployerTaxes,
                ROUND(SUM(pr.EmployerBenefits * p.DaysInYear / p.WorkingDays), 2)
                    AS Benefits,
                ROUND(SUM(CASE WHEN cc.CostCenterName = 'Manufacturing'
                    THEN (pr.GrossPay + pr.EmployerPayrollTax
                        + pr.EmployerBenefits) * p.DaysInYear / p.WorkingDays
                    ELSE 0 END), 2) AS Manufacturing
            FROM Periods AS p
                INNER JOIN PayrollRegister AS pr
                    ON pr.PayrollPeriodID = p.PayrollPeriodID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
            GROUP BY p.AsOfDate
            ORDER BY p.AsOfDate;
            """,
            [c for y, x in ((d.F, pf), (d.P, pp)) for k, col in (("total", "PayrollOwed"), ("gross", "GrossPay"),
                                                                  ("tax", "EmployerTaxes"), ("ben", "Benefits"),
                                                                  ("mfg", "Manufacturing"))
             for c in [Check(f"{y} {col}", x[k], lambda r, y=y, col=col: r.where(AsOfDate=ye(y))[col], 0.015)]]
            + [Check(f"{y} periods", x["n_full"] + x["n_cross"], lambda r, y=y: r.where(AsOfDate=ye(y))["Periods"])
               for y, x in ((d.F, pf), (d.P, pp))])

    p = pc["p"]
    s.query(f"Requirement 4: the payroll owed at {ye(d.C)}, the last eight processed periods' cost per working day",
            f"Population: the last eight processed pay periods, WorkCenterCalendar; expected: {money(p['cost'])} over "
            f"{p['wd']} working days x {p['left']} days = {money(pc['total'])}",
            f"""
            WITH {sub(periods_sql(d), 12)},
            Cost AS (
                SELECT SUM(pr.GrossPay) AS GrossPay,
                    SUM(pr.EmployerPayrollTax) AS EmployerTaxes,
                    SUM(pr.EmployerBenefits) AS Benefits,
                    SUM(CASE WHEN cc.CostCenterName = 'Manufacturing'
                        THEN pr.GrossPay + pr.EmployerPayrollTax
                            + pr.EmployerBenefits ELSE 0 END) AS Manufacturing
                FROM PayrollRegister AS pr
                    INNER JOIN CostCenter AS cc ON cc.CostCenterID = pr.CostCenterID
                WHERE pr.PayrollPeriodID IN (SELECT PayrollPeriodID FROM LastEight)
            )
            SELECT ROUND(GrossPay + EmployerTaxes + Benefits, 2) AS PeriodCost,
                (SELECT PeriodDays FROM Days) AS PeriodDays,
                (SELECT DaysLeft FROM Days) AS DaysLeft,
                ROUND((GrossPay + EmployerTaxes + Benefits)
                    / (SELECT PeriodDays FROM Days), 2) AS CostPerDay,
                ROUND((GrossPay + EmployerTaxes + Benefits)
                    / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days), 2) AS PayrollOwed,
                ROUND(GrossPay / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days), 2) AS GrossPay,
                ROUND(EmployerTaxes / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days), 2) AS EmployerTaxes,
                ROUND(Benefits / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days), 2) AS Benefits,
                ROUND(Manufacturing / (SELECT PeriodDays FROM Days)
                    * (SELECT DaysLeft FROM Days), 2) AS Manufacturing
            FROM Cost;
            """,
            [Check("cost of the eight periods", p["cost"], lambda r: r.value("PeriodCost")),
             Check("their working days", p["wd"], lambda r: r.value("PeriodDays")),
             Check("working days left", p["left"], lambda r: r.value("DaysLeft")),
             Check("cost per working day", round(p["daily"], 2), lambda r: r.value("CostPerDay")),
             Check("payroll owed", pc["total"], lambda r: r.value("PayrollOwed")),
             Check("gross pay", pc["gross"], lambda r: r.value("GrossPay")),
             Check("employer taxes", pc["tax"], lambda r: r.value("EmployerTaxes")),
             Check("benefits", pc["ben"], lambda r: r.value("Benefits")),
             Check("manufacturing", pc["mfg"], lambda r: r.value("Manufacturing"))])

    expected_accounts = [[cname, int(a)] for cname, a in d.q(
        "SELECT c.CostCenterName, a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
        "JOIN CostCenter c ON c.CostCenterID = g.CostCenterID WHERE g.SourceDocumentType = 'PayrollSummary' "
        "AND g.Debit > 0 AND a.AccountNumber <> 6060 AND g.FiscalYear = ? GROUP BY 1, 2 ORDER BY 1", d.C)]
    s.query(f"Requirement 4: the account each cost center's gross pay is debited to (PayrollAccounts)",
            f"Population: PayrollSummary debits of {d.C} other than 6060; expected: Manufacturing to 1090, the others "
            f"to their salary accounts",
            f"""
            SELECT cc.CostCenterName, a.AccountNumber AS PayrollAccount
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                INNER JOIN CostCenter AS cc ON cc.CostCenterID = gl.CostCenterID
            WHERE gl.SourceDocumentType = 'PayrollSummary'
                AND gl.Debit > 0
                AND a.AccountNumber <> 6060
                AND gl.FiscalYear = {d.C}
            GROUP BY cc.CostCenterID, cc.CostCenterName, a.AccountID,
                a.AccountNumber
            ORDER BY cc.CostCenterName;
            """,
            [Check("the rows the workbook pastes (PayrollAccounts)", expected_accounts,
                   lambda r: [list(x) for x in r.rows])])

    ints = n["ints"]
    s.query("Requirement 4: the interest each note had accrued at each year-end, from DebtScheduleLine",
            f"Population: DebtAgreement and DebtScheduleLine; each payment's interest covers the days since the one "
            f"before, counted from that day; expected: {', '.join(money(x['total']) for x in ints)}",
            f"""
            WITH {sub(year_ends(d.years), 12)},
            Notes AS (
                SELECT ye.AsOfDate, da.DebtAgreementID, da.AgreementNumber,
                    COALESCE(
                        (SELECT MAX(dl.PaymentDate)
                         FROM DebtScheduleLine AS dl
                         WHERE dl.DebtAgreementID = da.DebtAgreementID
                             AND dl.PaymentDate <= ye.AsOfDate),
                        da.OriginationDate) AS PreviousDate,
                    (SELECT MIN(dl.PaymentDate)
                     FROM DebtScheduleLine AS dl
                     WHERE dl.DebtAgreementID = da.DebtAgreementID
                         AND dl.PaymentDate > ye.AsOfDate) AS NextPaymentDate
                FROM YearEnds AS ye
                    INNER JOIN DebtAgreement AS da
                        ON da.OriginationDate <= ye.AsOfDate
            )
            SELECT n.AsOfDate, n.AgreementNumber, n.PreviousDate,
                n.NextPaymentDate, dl.InterestAmount AS NextInterest,
                julianday(n.NextPaymentDate) - julianday(n.PreviousDate)
                    AS DaysInPeriod,
                julianday(n.AsOfDate) - julianday(n.PreviousDate) + 1
                    AS DaysAccrued,
                ROUND(dl.InterestAmount
                    * CASE WHEN julianday(n.AsOfDate) + 1
                            < julianday(n.NextPaymentDate)
                        THEN julianday(n.AsOfDate) - julianday(n.PreviousDate) + 1
                        ELSE julianday(n.NextPaymentDate)
                            - julianday(n.PreviousDate) END
                    / (julianday(n.NextPaymentDate) - julianday(n.PreviousDate)),
                    2) AS InterestAccrued
            FROM Notes AS n
                INNER JOIN DebtScheduleLine AS dl
                    ON dl.DebtAgreementID = n.DebtAgreementID
                    AND dl.PaymentDate = n.NextPaymentDate
            ORDER BY n.AsOfDate, n.AgreementNumber;
            """,
            [Check(f"{x['year']} total", x["total"], lambda r, x=x: round(sum(
                row[7] for row in r.rows if row[0] == ye(x["year"])), 2)) for x in ints]
            + [Check(f"{x['year']} note {i['note']}", [i["prev"], i["date"], i["interest"], float(i["span"]),
                                                       float(i["elapsed"]), i["amount"]],
                     lambda r, x=x, k=k: [r2(v) for v in [row for row in r.rows if row[0] == ye(x["year"])][k][2:]])
               for x in ints for k, i in enumerate(x["items"])])

    s.answer("Requirement 4", f"""
        Revenue, by the latest delivery of each invoice's shipments against the year of its posting (SubTotal; these
        invoices carry no freight): {cf['n']} invoices for {d.F} deliveries posted in {d.P}, {money(cf['total'])}; {cp['n']}
        for {d.P} deliveries posted in {d.C}, {money(cp['total'])}; and {cc['n_lines']} December {d.C} shipment lines
        never invoiced, {money(cc['total'])} at order price, whose standard cost ({money(cc['std'])}) is already in cost
        of goods sold. Sales tax is recorded on invoicing and is not adjusted.

        Payroll, by working day: {money(pf['total'])} at {ye(d.F)}, {money(pp['total'])} at {ye(d.P)}, and
        {money(pc['total'])} at {ye(d.C)} from the last eight processed periods' cost per working day. The
        manufacturing part goes to 1090 and, with no completion to absorb it, ends in 5080 and cost of goods sold; the
        rest goes to the cost centers' salary accounts and 6060. Interest (2080 has never been used): each payment's
        interest covers the days since the one before; the day count includes the year-end: {', '.join(
            f"{money(x['total'])} at {ye(x['year'])}" for x in ints)}. Prorating a pay period or a payment is a
        formula a reviewer should see, so the workbook holds the prorations and this script the populations.""")


# --- Requirement 5: the adjustments ----------------------------------------------------------------------------------

def aging(d, year: int) -> tuple[list[float], list[int]]:
    """The workbook's ReceivableAging columns at a year-end (xlbuild/cap17.aging), computed the same way."""
    asof = ye(year)
    from notes.ch08 import bucket_of, xr
    amounts, counts = [0.0] * 5, [0] * 5
    for due, balance in d.q(
            "SELECT si.DueDate, si.GrandTotal - COALESCE((SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a "
            "WHERE a.SalesInvoiceID = si.SalesInvoiceID AND a.ApplicationDate <= ?1), 0) - COALESCE((SELECT SUM(c.GrandTotal) "
            "FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID AND c.CreditMemoDate <= ?1), 0) "
            "FROM SalesInvoice si WHERE si.InvoiceDate <= ?1", asof):
        balance = xr(balance)
        if balance > 0:
            k = bucket_of(notes_days(due, asof))
            amounts[k] += balance
            counts[k] += 1
    return [xr(a) for a in amounts], counts


def notes_days(a: str, b: str) -> int:
    from datetime import date
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def r5(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r5")
    ch = notes(b)
    P, C = d.P, d.C
    s.query(f"Requirement 5: the open receivables at {ye(P)} and {ye(C)} saved as a view, aged in Exercise 8.1's "
            f"buckets",
            "Population: each invoice dated by the year-end less the receipts applied and the credit memos dated by "
            "then, rounded, kept if greater than zero; expected: the view OpenReceivables",
            f"""
            DROP VIEW IF EXISTS OpenReceivables;
            CREATE VIEW OpenReceivables AS
            WITH {sub(year_ends((P, C)), 12)},
            Applied AS (
                SELECT ye.AsOfDate, a.SalesInvoiceID,
                    SUM(a.AppliedAmount) AS Applied
                FROM YearEnds AS ye
                    INNER JOIN CashReceiptApplication AS a
                        ON a.ApplicationDate <= ye.AsOfDate
                GROUP BY ye.AsOfDate, a.SalesInvoiceID
            ),
            Credited AS (
                SELECT ye.AsOfDate, cm.OriginalSalesInvoiceID AS SalesInvoiceID,
                    SUM(cm.GrandTotal) AS Credited
                FROM YearEnds AS ye
                    INNER JOIN CreditMemo AS cm
                        ON cm.CreditMemoDate <= ye.AsOfDate
                GROUP BY ye.AsOfDate, cm.OriginalSalesInvoiceID
            ),
            Balances AS (
                SELECT ye.AsOfDate, si.SalesInvoiceID, si.CustomerID,
                    ROUND(si.GrandTotal - COALESCE(ap.Applied, 0)
                        - COALESCE(cr.Credited, 0), 2) AS Balance,
                    julianday(ye.AsOfDate) - julianday(si.DueDate)
                        AS DaysPastDue
                FROM YearEnds AS ye
                    INNER JOIN SalesInvoice AS si
                        ON si.InvoiceDate <= ye.AsOfDate
                    LEFT JOIN Applied AS ap
                        ON ap.AsOfDate = ye.AsOfDate
                        AND ap.SalesInvoiceID = si.SalesInvoiceID
                    LEFT JOIN Credited AS cr
                        ON cr.AsOfDate = ye.AsOfDate
                        AND cr.SalesInvoiceID = si.SalesInvoiceID
            )
            SELECT AsOfDate, SalesInvoiceID, CustomerID, Balance, DaysPastDue,
                CASE
                    WHEN DaysPastDue <= 0 THEN 1
                    WHEN DaysPastDue <= 30 THEN 2
                    WHEN DaysPastDue <= 60 THEN 3
                    WHEN DaysPastDue <= 90 THEN 4
                    ELSE 5
                END AS BucketOrder
            FROM Balances
            WHERE Balance > 0;
            """)

    ap, kp = aging(d, P)
    ac, kc = aging(d, C)
    expected = [[BUCKET_NAMES[k], ap[k], kp[k], ac[k], kc[k]] for k in range(5)]
    s.query(f"Requirement 5: the receivables aging at the two year-ends (ReceivableAging)",
            f"Population: the view OpenReceivables; expected: {sum(kp):,} and {sum(kc):,} open invoices, "
            f"{money(sum(ap))} and {money(sum(ac))}",
            f"""
            SELECT CASE BucketOrder
                    WHEN 1 THEN 'Current' WHEN 2 THEN '1-30 days'
                    WHEN 3 THEN '31-60 days' WHEN 4 THEN '61-90 days'
                    ELSE 'Over 90 days'
                END AS Bucket,
                ROUND(SUM(CASE WHEN AsOfDate = '{ye(P)}'
                    THEN Balance ELSE 0 END), 2) AS Balance{P},
                SUM(CASE WHEN AsOfDate = '{ye(P)}' THEN 1 ELSE 0 END)
                    AS Invoices{P},
                ROUND(SUM(CASE WHEN AsOfDate = '{ye(C)}'
                    THEN Balance ELSE 0 END), 2) AS Balance{C},
                SUM(CASE WHEN AsOfDate = '{ye(C)}' THEN 1 ELSE 0 END)
                    AS Invoices{C}
            FROM OpenReceivables
            GROUP BY BucketOrder
            ORDER BY BucketOrder;
            """,
            [Check("the rows the workbook pastes (ReceivableAging)", [[r2(v) for v in row] for row in expected], rows2)])

    s.query("Requirement 5: passed item P1, an allowance at Exercise 8.1's rates at each year-end",
            f"Population: the view OpenReceivables; rates 0.5%, 2%, 5%, 15%, 40%; expected: {money(-n['p1_prior'])} "
            f"({P}) and {money(-n['p1'])} ({C})",
            f"""
            WITH Buckets AS (
                SELECT AsOfDate, BucketOrder,
                    ROUND(SUM(Balance), 2) AS Balance
                FROM OpenReceivables
                GROUP BY AsOfDate, BucketOrder
            )
            SELECT AsOfDate,
                ROUND(SUM(ROUND(Balance * CASE BucketOrder
                    WHEN 1 THEN 0.005 WHEN 2 THEN 0.02 WHEN 3 THEN 0.05
                    WHEN 4 THEN 0.15 ELSE 0.40 END, 2)), 2) AS Allowance
            FROM Buckets
            GROUP BY AsOfDate
            ORDER BY AsOfDate;
            """,
            [Check(f"{P} allowance", -n["p1_prior"], lambda r: r.where(AsOfDate=ye(P))["Allowance"]),
             Check(f"{C} allowance", -n["p1"], lambda r: r.where(AsOfDate=ye(C))["Allowance"]),
             Check(f"effect on {C} income", n["p1_income"],
                   lambda r: round(r.where(AsOfDate=ye(P))["Allowance"] - r.where(AsOfDate=ye(C))["Allowance"], 2))])

    ra = ch.returns_across(d)
    expected_returns = [[ry, dy, ra["by_year"][ry]["n"], ra["by_year"][ry]["rev"], ra["by_year"][ry]["cost"]]
                        for ry, dy in sorted(ra["pairs"])]
    p2 = n["p2"]
    s.query("Requirement 5: passed item P2, returns made in a later year than the delivery (ReturnsAfterYearEnd)",
            f"Population: returns, each dated by the delivery of its first line, their credit memos, and the returned "
            f"lines' standard cost; expected: {p2['n']} returns in {C}, {money(p2['rev'])} less {money(p2['cost'])}",
            """
            WITH FirstLine AS (
                SELECT SalesReturnID, MIN(ShipmentLineID) AS ShipmentLineID
                FROM SalesReturnLine
                GROUP BY SalesReturnID
            ),
            Returned AS (
                SELECT CAST(strftime('%Y', sr.ReturnDate) AS INTEGER)
                        AS ReturnYear,
                    CAST(strftime('%Y', s.DeliveryDate) AS INTEGER)
                        AS DeliveryYear,
                    COUNT(DISTINCT sr.SalesReturnID) AS Returns,
                    ROUND(SUM(cm.SubTotal), 2) AS CreditMemoRevenue
                FROM SalesReturn AS sr
                    INNER JOIN CreditMemo AS cm
                        ON cm.SalesReturnID = sr.SalesReturnID
                    INNER JOIN FirstLine AS fl
                        ON fl.SalesReturnID = sr.SalesReturnID
                    INNER JOIN ShipmentLine AS sl
                        ON sl.ShipmentLineID = fl.ShipmentLineID
                    INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
                WHERE strftime('%Y', sr.ReturnDate)
                    <> strftime('%Y', s.DeliveryDate)
                GROUP BY ReturnYear, DeliveryYear
            ),
            LineCost AS (
                SELECT CAST(strftime('%Y', sr.ReturnDate) AS INTEGER)
                        AS ReturnYear,
                    ROUND(SUM(srl.ExtendedStandardCost), 2) AS StandardCost
                FROM SalesReturn AS sr
                    INNER JOIN SalesReturnLine AS srl
                        ON srl.SalesReturnID = sr.SalesReturnID
                    INNER JOIN ShipmentLine AS sl
                        ON sl.ShipmentLineID = srl.ShipmentLineID
                    INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
                WHERE strftime('%Y', sr.ReturnDate)
                    <> strftime('%Y', s.DeliveryDate)
                GROUP BY ReturnYear
            )
            SELECT r.ReturnYear, r.DeliveryYear, r.Returns,
                r.CreditMemoRevenue, COALESCE(lc.StandardCost, 0) AS StandardCost
            FROM Returned AS r
                LEFT JOIN LineCost AS lc ON lc.ReturnYear = r.ReturnYear
            ORDER BY r.ReturnYear, r.DeliveryYear;
            """,
            [Check("the rows the workbook pastes (ReturnsAfterYearEnd)",
                   [[r2(v) for v in row] for row in expected_returns], rows2),
             Check(f"P2 at {ye(C)}", p2["effect"], lambda r: round(-(r.where(ReturnYear=C)["CreditMemoRevenue"]
                                                                       - r.where(ReturnYear=C)["StandardCost"]), 2))])

    p3 = n["p3"]
    marks = ", ".join(f"'{w}'" for w in WRITE_DOWN)
    s.query("Requirement 5: passed item P3, returns put back into stock at full standard cost, and the "
            "Damaged and Quality Concern ones",
            f"Population: return lines by return year, and the SalesReturn debits to 1040; expected: "
            f"{', '.join(money(v) for v in p3['years'])} restocked damaged or of concern",
            f"""
            WITH Restocked AS (
                SELECT CAST(strftime('%Y', sr.ReturnDate) AS INTEGER) AS FiscalYear,
                    SUM(srl.ExtendedStandardCost) AS ReturnedCost,
                    SUM(CASE WHEN sr.ReasonCode IN ({marks})
                        THEN srl.ExtendedStandardCost ELSE 0 END) AS WriteDownCandidates
                FROM SalesReturn AS sr
                    INNER JOIN SalesReturnLine AS srl
                        ON srl.SalesReturnID = sr.SalesReturnID
                GROUP BY FiscalYear
            ),
            Ledger AS (
                SELECT gl.FiscalYear, SUM(gl.Debit) AS RestockedToInventory
                FROM GLEntry AS gl
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                WHERE gl.SourceDocumentType = 'SalesReturn'
                    AND a.AccountNumber = 1040
                GROUP BY gl.FiscalYear
            )
            SELECT r.FiscalYear, ROUND(r.ReturnedCost, 2) AS ReturnedCost,
                ROUND(l.RestockedToInventory, 2) AS RestockedToInventory,
                ROUND(r.WriteDownCandidates, 2) AS DamagedOrOfConcern
            FROM Restocked AS r
                INNER JOIN Ledger AS l ON l.FiscalYear = r.FiscalYear
            ORDER BY r.FiscalYear;
            """,
            [Check("damaged or of concern by year", p3["years"], lambda r: r.col("DamagedOrOfConcern")),
             Check("since the first year", p3["total"], lambda r: round(r.total("DamagedOrOfConcern"), 2)),
             Check("restocked at full standard cost", [True] * len(d.years),
                   lambda r: [abs(x[1] - x[2]) < 0.005 for x in r.rows])])

    s.query(f"Requirement 5: reclassification R1, the principal of the notes due within a year of each year-end",
            f"Population: DebtScheduleLine of the notes originated by each year-end; expected: {money(n['cur_p'])} "
            f"({P}) and {money(n['cur_c'])} ({C})",
            f"""
            WITH {sub(year_ends((P, C)), 12)}
            SELECT ye.AsOfDate,
                ROUND(SUM(dl.PrincipalAmount), 2) AS CurrentPortion,
                COUNT(DISTINCT dl.DebtAgreementID) AS Notes
            FROM YearEnds AS ye
                INNER JOIN DebtScheduleLine AS dl
                    ON dl.PaymentDate > ye.AsOfDate
                    AND dl.PaymentDate <= date(ye.AsOfDate, '+1 year')
                INNER JOIN DebtAgreement AS da
                    ON da.DebtAgreementID = dl.DebtAgreementID
                    AND da.OriginationDate <= ye.AsOfDate
            GROUP BY ye.AsOfDate
            ORDER BY ye.AsOfDate;
            """,
            [Check(f"{P} current portion", n["cur_p"], lambda r: r.where(AsOfDate=ye(P))["CurrentPortion"]),
             Check(f"{C} current portion", n["cur_c"], lambda r: r.where(AsOfDate=ye(C))["CurrentPortion"]),
             Check(f"notes at {ye(P)}", sum(1 for x in ch.notes_payable(d) if x["origin"] <= ye(P)),
                   lambda r: r.where(AsOfDate=ye(P))["Notes"])])

    s.query(f"Requirement 5: reclassification R2, the credit balance of 1090 and work in process at both year-ends",
            f"Population: the trial balances at {ye(P)} and {ye(C)}; expected: 1090 {money(n['c1090_p'])} and "
            f"{money(n['c1090_c'])}, 1046 {money(n['wip_p'])} and {money(n['wip_c'])}",
            f"""
            WITH {sub(balances((P, C)), 12)}
            SELECT AsOfDate,
                ROUND(SUM(CASE WHEN AccountNumber = 1090
                    THEN Balance ELSE 0 END), 2) AS ClearingAccount1090,
                ROUND(SUM(CASE WHEN AccountNumber = 1046
                    THEN Balance ELSE 0 END), 2) AS WorkInProcess1046
            FROM Balances
            WHERE AccountNumber IN (1046, 1090)
            GROUP BY AsOfDate
            ORDER BY AsOfDate;
            """,
            [Check(f"1090 at {ye(P)}", n["c1090_p"], lambda r: r.where(AsOfDate=ye(P))["ClearingAccount1090"]),
             Check(f"1090 at {ye(C)}", n["c1090_c"], lambda r: r.where(AsOfDate=ye(C))["ClearingAccount1090"]),
             Check(f"1046 at {ye(P)}", n["wip_p"], lambda r: r.where(AsOfDate=ye(P))["WorkInProcess1046"]),
             Check(f"1046 at {ye(C)}", n["wip_c"], lambda r: r.where(AsOfDate=ye(C))["WorkInProcess1046"])])

    a, tot = n["a"], n["total"]
    s.answer("Requirement 5", f"""
        Recorded adjustments, effect on retained earnings at 1 January {P} / {P} income / {C} income: A1 payroll
        accrual {a['A1']['re']:+,.2f} / {a['A1']['P']:+,.2f} / {a['A1']['C']:+,.2f}; A2 revenue cutoff
        {a['A2']['re']:+,.2f} / {a['A2']['P']:+,.2f} / {a['A2']['C']:+,.2f}; A3 old accruals {a['A3']['re']:+,.2f} /
        {a['A3']['P']:+,.2f} / {a['A3']['C']:+,.2f}; A4 interest {a['A4']['re']:+,.2f} / {a['A4']['P']:+,.2f} /
        {a['A4']['C']:+,.2f}; totals {tot['re']:+,.2f} / {tot['P']:+,.2f} / {tot['C']:+,.2f}. Adjusted net income
        {money(n['adj_ni_p'])} ({P}) and {money(n['adj_ni_c'])} ({C}). Reclassifications: R1 the current portion of the
        notes ({money(n['cur_p'])} and {money(n['cur_c'])}); R2 the credit balance of 1090 netted into work in process.

        Materiality {money(n['mat_c'])} ({C}, on recorded income as the controller set it) and {money(n['mat_p'])}
        ({P}). {C}'s income effect is {n['share']:.0%} of materiality, but the payroll liability
        ({money(n['pay_c']['total'])}) exceeds it, current liabilities at {C} rise by {money(n['rise'])} before the
        reclassification, and the missing payroll accrual recurs every year. Record A1-A4, R1, and R2, and present {P} as
        restated, with the Topic 250 disclosures, because the shareholders received {P} statements. Passed items: P1 the
        allowance {money(n['p1'])} ({n['p1_income']:+,.2f} on {C} income), P2 expected returns about
        {money(p2['effect'])} ({p2['income']:+,.2f}), P3 the damaged and quality-concern returns restocked at full cost
        {money(p3['effect'])}; aggregate {money(n['aggregate'])}, {n['agg_share']:.0%} of materiality
        ({n['agg_income']:+,.2f} on {C} income). Pass all three and list them for the CFO's approval, with the freight
        residual of {money(n['residual'])} as trivial.""")


# --- Requirement 6: the statements -----------------------------------------------------------------------------------

def r6(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r6")
    cf = {d.P: n["cf_p"], d.C: n["cf_c"]}
    cash = {y: d.balance(["1010"], ye(y)) for y in d.years}
    s.query("Requirement 6: the change in cash and the interest paid each year, which no adjustment changes",
            f"Population: postings to 1010 and the Interest Payment entries; expected: cash "
            f"{', '.join(money(cash[y]) for y in d.years)}; interest paid {money(cf[d.P]['interest_paid'])} and "
            f"{money(cf[d.C]['interest_paid'])}",
            f"""
            WITH {sub(CLOSES, 12)},
            Cash AS (
                SELECT gl.FiscalYear, SUM(gl.Debit - gl.Credit) AS Change
                FROM GLEntry AS gl
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                WHERE a.AccountNumber = 1010
                    AND gl.VoucherNumber NOT IN (SELECT EntryNumber FROM Closes)
                GROUP BY gl.FiscalYear
            ),
            Interest AS (
                SELECT gl.FiscalYear, SUM(gl.Debit) AS InterestPaid
                FROM GLEntry AS gl
                    INNER JOIN JournalEntry AS je
                        ON je.JournalEntryID = gl.SourceDocumentID
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                WHERE gl.SourceDocumentType = 'JournalEntry'
                    AND je.EntryType = 'Interest Payment'
                    AND a.AccountNumber = 7030
                GROUP BY gl.FiscalYear
            )
            SELECT c.FiscalYear, ROUND(c.Change, 2) AS ChangeInCash,
                ROUND((SELECT SUM(c2.Change) FROM Cash AS c2
                    WHERE c2.FiscalYear <= c.FiscalYear), 2) AS CashAtYearEnd,
                ROUND(COALESCE(i.InterestPaid, 0), 2) AS InterestPaid
            FROM Cash AS c
                LEFT JOIN Interest AS i ON i.FiscalYear = c.FiscalYear
            WHERE c.FiscalYear <= {d.C}
            ORDER BY c.FiscalYear;
            """,
            [Check(f"{y} cash at year-end", round(cash[y], 2), lambda r, y=y: r.where(FiscalYear=y)["CashAtYearEnd"])
             for y in d.years]
            + [c for y in (d.P, d.C) for c in (
                Check(f"{y} change in cash", cf[y]["cash"], lambda r, y=y: r.where(FiscalYear=y)["ChangeInCash"]),
                Check(f"{y} interest paid", cf[y]["interest_paid"], lambda r, y=y: r.where(FiscalYear=y)["InterestPaid"]))])

    notes_financed = d.q("SELECT CAST(substr(EventDate, 1, 4) AS INTEGER), SUM(Amount) FROM FixedAssetEvent WHERE "
                         "FinancingType = 'Note' GROUP BY 1 ORDER BY 1")
    disposals = notes(b).disposals
    s.query("Requirement 6: the investing events that moved no cash, equipment financed by a note and disposals with "
            "no proceeds",
            f"Population: FixedAssetEvent; expected: equipment financed by notes "
            f"{', '.join(f'{money(v)} in {y}' for y, v in notes_financed)}",
            """
            SELECT strftime('%Y', fe.EventDate) AS FiscalYear, fe.EventType,
                fe.FinancingType, fa.AssetCode, fe.Amount, fe.ProceedsAmount
            FROM FixedAssetEvent AS fe
                INNER JOIN FixedAsset AS fa ON fa.FixedAssetID = fe.FixedAssetID
            WHERE fe.FinancingType IN ('Note', 'None')
            ORDER BY fe.EventDate;
            """,
            [Check("financed by a note", [[str(y), v] for y, v in notes_financed],
                   lambda r: [[x[0], x[4]] for x in r.rows if x[2] == "Note"]),
             Check("years with a disposal without proceeds", [y for y in d.years for x in disposals(d, y)
                                                              if x["proceeds"] == 0],
                   lambda r: [int(x[0]) for x in r.rows if x[1] == "Disposal" and not x[5]])])


# --- Requirement 7: the note schedules -------------------------------------------------------------------------------

REGISTER = """\
Register AS (
    SELECT fa.AssetCode, ca.AccountNumber AS CostAccount,
        aa.AccountNumber AS DepreciationAccount, fa.InServiceDate,
        fa.DisposalDate, fa.OriginalCost, fa.UsefulLifeMonths,
        fa.ResidualValue,
        ROUND(fa.OriginalCost * 1.0 / fa.UsefulLifeMonths, 2) AS Monthly,
        CAST(strftime('%Y', fa.InServiceDate) AS INTEGER) * 12
            + CAST(strftime('%m', fa.InServiceDate) AS INTEGER) AS FirstMonth,
        CASE
            WHEN fa.DisposalDate IS NULL
                OR CAST(strftime('%Y', fa.DisposalDate) AS INTEGER) * 12
                    + CAST(strftime('%m', fa.DisposalDate) AS INTEGER) - 2
                    > CAST(strftime('%Y', fa.InServiceDate) AS INTEGER) * 12
                    + CAST(strftime('%m', fa.InServiceDate) AS INTEGER) - 1
                    + fa.UsefulLifeMonths
                THEN CAST(strftime('%Y', fa.InServiceDate) AS INTEGER) * 12
                    + CAST(strftime('%m', fa.InServiceDate) AS INTEGER) - 1
                    + fa.UsefulLifeMonths
            ELSE CAST(strftime('%Y', fa.DisposalDate) AS INTEGER) * 12
                + CAST(strftime('%m', fa.DisposalDate) AS INTEGER) - 2
        END AS LastMonth
    FROM FixedAsset AS fa
        INNER JOIN Account AS ca ON ca.AccountID = fa.AssetAccountID
        INNER JOIN Account AS aa
            ON aa.AccountID = fa.AccumulatedDepreciationAccountID
)"""


def r7(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r7")
    ch = notes(b)
    F, P, C = d.F, d.P, d.C
    register = ch.register(d)
    by_cost = {}
    for a in register:
        x = by_cost.setdefault(int(a["account"]), {y: 0.0 for y in ("f", "addp", "dispp", "p", "addc", "dispc", "c")})
        inservice = lambda y: a["service"] <= ye(y) and not (a["disposal"] and a["disposal"] <= ye(y))
        x["f"] += a["cost"] if inservice(F) else 0
        x["p"] += a["cost"] if inservice(P) else 0
        x["c"] += a["cost"] if inservice(C) else 0
        x["addp"] += a["cost"] if a["service"][:4] == str(P) else 0
        x["addc"] += a["cost"] if a["service"][:4] == str(C) else 0
        x["dispp"] += a["cost"] if a["disposal"] and a["disposal"][:4] == str(P) else 0
        x["dispc"] += a["cost"] if a["disposal"] and a["disposal"][:4] == str(C) else 0
    s.query("Requirement 7: property and equipment, the cost rolled forward by class from FixedAsset",
            f"Population: FixedAsset by cost account; expected: cost {money(n['cost_f'])} -> {money(n['cost_p'])} -> "
            f"{money(n['cost_c'])}",
            f"""
            WITH {sub(REGISTER, 12)}
            SELECT CostAccount,
                SUM(CASE WHEN InServiceDate <= '{ye(F)}'
                    AND (DisposalDate IS NULL OR DisposalDate > '{ye(F)}')
                    THEN OriginalCost ELSE 0 END) AS Cost{F},
                SUM(CASE WHEN InServiceDate BETWEEN '{P}-01-01' AND '{ye(P)}'
                    THEN OriginalCost ELSE 0 END) AS Additions{P},
                SUM(CASE WHEN DisposalDate BETWEEN '{P}-01-01' AND '{ye(P)}'
                    THEN OriginalCost ELSE 0 END) AS Disposals{P},
                SUM(CASE WHEN InServiceDate <= '{ye(P)}'
                    AND (DisposalDate IS NULL OR DisposalDate > '{ye(P)}')
                    THEN OriginalCost ELSE 0 END) AS Cost{P},
                SUM(CASE WHEN InServiceDate BETWEEN '{C}-01-01' AND '{ye(C)}'
                    THEN OriginalCost ELSE 0 END) AS Additions{C},
                SUM(CASE WHEN DisposalDate BETWEEN '{C}-01-01' AND '{ye(C)}'
                    THEN OriginalCost ELSE 0 END) AS Disposals{C},
                SUM(CASE WHEN InServiceDate <= '{ye(C)}'
                    AND (DisposalDate IS NULL OR DisposalDate > '{ye(C)}')
                    THEN OriginalCost ELSE 0 END) AS Cost{C},
                MIN(UsefulLifeMonths) AS ShortestLife,
                MAX(UsefulLifeMonths) AS LongestLife,
                SUM(ResidualValue) AS ResidualValue
            FROM Register
            GROUP BY CostAccount
            ORDER BY CostAccount;
            """,
            [Check("cost accounts", sorted(by_cost), lambda r: r.col("CostAccount")),
             Check(f"cost at {ye(F)}", n["cost_f"], lambda r: r.total(f"Cost{F}")),
             Check(f"cost at {ye(P)}", n["cost_p"], lambda r: r.total(f"Cost{P}")),
             Check(f"cost at {ye(C)}", n["cost_c"], lambda r: r.total(f"Cost{C}")),
             Check(f"additions {P}", n["add_p"]["total"], lambda r: r.total(f"Additions{P}")),
             Check(f"additions {C}", n["add_c"]["total"], lambda r: r.total(f"Additions{C}")),
             Check(f"disposals {P}", n["disp_p"]["cost"], lambda r: r.total(f"Disposals{P}")),
             Check(f"disposals {C}", n["disp_c"]["cost"], lambda r: r.total(f"Disposals{C}")),
             Check("lives in months", [n["life_low"], n["life_high"]],
                   lambda r: [min(r.col("ShortestLife")), max(r.col("LongestLife"))]),
             Check("no residual value", 0, lambda r: r.total("ResidualValue"))]
            + [Check(f"additions {P}, account {g['account']}", g["cost"],
                     lambda r, g=g: r.where(CostAccount=int(g["account"]))[f"Additions{P}"]) for g in n["add_p"]["groups"]]
            + [Check(f"cost by class at {ye(C)}, register against the ledger",
                     [round(d.balance([a], ye(C)), 2) for a in sorted(str(k) for k in by_cost)],
                     lambda r: [float(v) for v in r.col(f"Cost{C}")])])

    classes = {c["name"]: c for c in n["classes"]}
    contra_names = {"1150": "furniture and fixtures", "1160": "warehouse", "1170": "office", "1186": "manufacturing"}
    s.query("Requirement 7: depreciation by class and year, the register against the ledger",
            f"Population: FixedAsset (each asset's cost over its life in months, from the month after it is placed in "
            f"service through the month before disposal) and the Depreciation entries; expected: "
            f"{money(n['dep_p'])} ({P}) and {money(n['dep_c'])} ({C})",
            f"""
            WITH {sub(REGISTER, 12)},
            Ledger AS (
                SELECT a.AccountNumber, gl.FiscalYear,
                    SUM(gl.Credit - gl.Debit) AS Depreciation
                FROM GLEntry AS gl
                    INNER JOIN JournalEntry AS je
                        ON je.JournalEntryID = gl.SourceDocumentID
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                WHERE gl.SourceDocumentType = 'JournalEntry'
                    AND je.EntryType = 'Depreciation'
                    AND a.AccountSubType = 'Contra Fixed Asset'
                GROUP BY a.AccountNumber, gl.FiscalYear
            ),
            Months AS (
                SELECT DISTINCT CAST(strftime('%Y', CalendarDate) AS INTEGER)
                        AS CalendarYear,
                    CAST(strftime('%Y', CalendarDate) AS INTEGER) * 12
                        + CAST(strftime('%m', CalendarDate) AS INTEGER) - 1
                        AS MonthIndex
                FROM WorkCenterCalendar
                WHERE CalendarDate BETWEEN '{P}-01-01' AND '{ye(C)}'
            ),
            Schedule AS (
                SELECT r.DepreciationAccount,
                    SUM(CASE WHEN m.CalendarYear = {P}
                        THEN r.Monthly ELSE 0 END) AS Register{P},
                    SUM(CASE WHEN m.CalendarYear = {C}
                        THEN r.Monthly ELSE 0 END) AS Register{C}
                FROM Register AS r
                    INNER JOIN Months AS m
                        ON m.MonthIndex BETWEEN r.FirstMonth AND r.LastMonth
                GROUP BY r.DepreciationAccount
            )
            SELECT s.DepreciationAccount,
                ROUND(s.Register{P}, 2) AS Register{P},
                ROUND(lp.Depreciation, 2) AS Ledger{P},
                ROUND(s.Register{C}, 2) AS Register{C},
                ROUND(lc.Depreciation, 2) AS Ledger{C}
            FROM Schedule AS s
                LEFT JOIN Ledger AS lp
                    ON lp.AccountNumber = s.DepreciationAccount
                    AND lp.FiscalYear = {P}
                LEFT JOIN Ledger AS lc
                    ON lc.AccountNumber = s.DepreciationAccount
                    AND lc.FiscalYear = {C}
            ORDER BY s.DepreciationAccount;
            """,
            [c for acct, name in contra_names.items() for c in (
                Check(f"{name} {P}", classes[name]["p"], lambda r, a=acct: r.where(DepreciationAccount=int(a))[f"Ledger{P}"]),
                Check(f"{name} {C}", classes[name]["c"], lambda r, a=acct: r.where(DepreciationAccount=int(a))[f"Ledger{C}"]))]
            + [Check(f"total {P}", n["dep_p"], lambda r: round(r.total(f"Ledger{P}"), 2)),
               Check(f"total {C}", n["dep_c"], lambda r: round(r.total(f"Ledger{C}"), 2)),
               Check("the register reproduces the ledger", [True] * len(contra_names),
                     lambda r: [abs(x[1] - x[2]) < 0.005 and abs(x[3] - x[4]) < 0.005 for x in r.rows])])

    s.query("Requirement 7: where depreciation is charged, 6130 and 1090",
            f"Population: Depreciation entries' debits; expected: 6130 {money(n['to6130_p'])} and "
            f"{money(n['to6130_c'])}, 1090 {money(n['to1090_p'])} and {money(n['to1090_c'])}",
            f"""
            SELECT a.AccountNumber,
                ROUND(SUM(CASE WHEN gl.FiscalYear = {P}
                    THEN gl.Debit ELSE 0 END), 2) AS Debits{P},
                ROUND(SUM(CASE WHEN gl.FiscalYear = {C}
                    THEN gl.Debit ELSE 0 END), 2) AS Debits{C}
            FROM GLEntry AS gl
                INNER JOIN JournalEntry AS je
                    ON je.JournalEntryID = gl.SourceDocumentID
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.SourceDocumentType = 'JournalEntry'
                AND je.EntryType = 'Depreciation'
                AND gl.Debit > 0
            GROUP BY a.AccountID, a.AccountNumber
            ORDER BY a.AccountNumber;
            """,
            [Check("accounts charged", [1090, 6130], lambda r: r.col("AccountNumber")),
             Check(f"6130 {P}", n["to6130_p"], lambda r: r.where(AccountNumber=6130)[f"Debits{P}"]),
             Check(f"6130 {C}", n["to6130_c"], lambda r: r.where(AccountNumber=6130)[f"Debits{C}"]),
             Check(f"1090 {P}", n["to1090_p"], lambda r: r.where(AccountNumber=1090)[f"Debits{P}"]),
             Check(f"1090 {C}", n["to1090_c"], lambda r: r.where(AccountNumber=1090)[f"Debits{C}"])])

    s.query("Requirement 7: accumulated depreciation at the three year-ends and net book value by class",
            f"Population: the trial balances; expected: accumulated depreciation {money(n['acc_f'])} -> "
            f"{money(n['acc_p'])} -> {money(n['acc_c'])}",
            f"""
            WITH {sub(balances(d.years), 12)},
            Classes AS (
                SELECT AsOfDate, AccountNumber, AccountSubType, Balance,
                    CASE AccountNumber
                        WHEN 1150 THEN 1110 WHEN 1160 THEN 1120
                        WHEN 1170 THEN 1130 WHEN 1186 THEN 1185
                        ELSE AccountNumber END AS CostAccount
                FROM Balances
                WHERE AccountSubType IN ('Fixed Asset', 'Contra Fixed Asset')
            )
            SELECT CostAccount,
                ROUND(-SUM(CASE WHEN AccountSubType = 'Contra Fixed Asset'
                    AND AsOfDate = '{ye(F)}' THEN Balance ELSE 0 END), 2)
                    AS Accumulated{F},
                ROUND(-SUM(CASE WHEN AccountSubType = 'Contra Fixed Asset'
                    AND AsOfDate = '{ye(P)}' THEN Balance ELSE 0 END), 2)
                    AS Accumulated{P},
                ROUND(-SUM(CASE WHEN AccountSubType = 'Contra Fixed Asset'
                    AND AsOfDate = '{ye(C)}' THEN Balance ELSE 0 END), 2)
                    AS Accumulated{C},
                ROUND(SUM(CASE WHEN AsOfDate = '{ye(C)}'
                    THEN Balance ELSE 0 END), 2) AS NetBookValue{C}
            FROM Classes
            GROUP BY CostAccount
            ORDER BY CostAccount;
            """,
            [Check(f"accumulated at {ye(F)}", n["acc_f"], lambda r: round(r.total(f"Accumulated{F}"), 2)),
             Check(f"accumulated at {ye(P)}", n["acc_p"], lambda r: round(r.total(f"Accumulated{P}"), 2)),
             Check(f"accumulated at {ye(C)}", n["acc_c"], lambda r: round(r.total(f"Accumulated{C}"), 2)),
             Check(f"net book value by class at {ye(C)}", n["nbv"], lambda r: r.col(f"NetBookValue{C}"))])

    dp, dc = n["disp_p"], n["disp_c"]
    s.query("Requirement 7: the disposals, cost removed, depreciation written off, proceeds, and loss",
            f"Population: the Asset Disposal entries; expected: {dp['code']} (loss {money(dp['loss'])}, proceeds "
            f"{money(dp['proceeds'])}) and {dc['code']} (loss {money(dc['loss'])}, no proceeds)",
            """
            SELECT je.EntryNumber, je.PostingDate,
                ROUND(SUM(CASE WHEN a.AccountSubType = 'Fixed Asset'
                    THEN gl.Credit - gl.Debit ELSE 0 END), 2) AS CostRemoved,
                ROUND(SUM(CASE WHEN a.AccountSubType = 'Contra Fixed Asset'
                    THEN gl.Debit - gl.Credit ELSE 0 END), 2)
                    AS DepreciationWrittenOff,
                ROUND(SUM(CASE WHEN a.AccountNumber = 1010
                    THEN gl.Debit - gl.Credit ELSE 0 END), 2) AS Proceeds,
                ROUND(SUM(CASE WHEN a.AccountNumber = 7020
                    THEN gl.Debit - gl.Credit ELSE 0 END), 2) AS Loss
            FROM JournalEntry AS je
                INNER JOIN GLEntry AS gl
                    ON gl.SourceDocumentType = 'JournalEntry'
                    AND gl.SourceDocumentID = je.JournalEntryID
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE je.EntryType = 'Asset Disposal'
            GROUP BY je.JournalEntryID, je.EntryNumber, je.PostingDate
            ORDER BY je.PostingDate;
            """,
            [Check(f"{y} disposal", [x["cost"], x["written"], float(x["proceeds"]), x["loss"]],
                   lambda r, y=y: [v for row in r.rows if row[1][:4] == str(y) for v in row[2:]])
             for y, x in ((P, dp), (C, dc))])

    notes_ = n["notes"]
    s.query("Requirement 7: the notes payable, their terms, the asset each finances, and the balance at each "
            "year-end",
            f"Population: DebtAgreement and DebtScheduleLine; expected: {money(n['notes_total'])} at {ye(C)}, equal "
            f"to 2110",
            f"""
            SELECT da.AgreementNumber, fa.AssetCode, da.OriginationDate,
                da.PrincipalAmount, da.AnnualInterestRate, da.TermMonths,
                da.PaymentStartDate, da.ScheduledPaymentAmount,
                CASE WHEN da.OriginationDate <= '{ye(P)}'
                    THEN ROUND(SUM(CASE WHEN dl.PaymentDate > '{ye(P)}'
                        THEN dl.PrincipalAmount ELSE 0 END), 2) END
                    AS Outstanding{P},
                ROUND(SUM(CASE WHEN dl.PaymentDate > '{ye(C)}'
                    THEN dl.PrincipalAmount ELSE 0 END), 2) AS Outstanding{C},
                (SELECT ROUND(SUM(gl.Credit - gl.Debit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 2110
                     AND gl.PostingDate <= '{ye(C)}') AS Ledger2110
            FROM DebtAgreement AS da
                LEFT JOIN FixedAsset AS fa ON fa.FixedAssetID = da.FixedAssetID
                INNER JOIN DebtScheduleLine AS dl
                    ON dl.DebtAgreementID = da.DebtAgreementID
            GROUP BY da.DebtAgreementID, da.AgreementNumber, fa.AssetCode,
                da.OriginationDate, da.PrincipalAmount, da.AnnualInterestRate,
                da.TermMonths, da.PaymentStartDate, da.ScheduledPaymentAmount
            ORDER BY da.OriginationDate, da.DebtAgreementID;
            """,
            [Check("assets financed", [x["asset"] for x in notes_], lambda r: r.col("AssetCode")),
             Check("principal", [x["principal"] for x in notes_], lambda r: r.col("PrincipalAmount")),
             Check("terms", [x["term"] for x in notes_], lambda r: r.col("TermMonths")),
             Check("payments", [x["payment"] for x in notes_], lambda r: r.col("ScheduledPaymentAmount")),
             Check(f"outstanding at {ye(P)}", [x["p"] for x in notes_], lambda r: r.col(f"Outstanding{P}")),
             Check(f"outstanding at {ye(C)}", [x["c"] for x in notes_], lambda r: r.col(f"Outstanding{C}")),
             Check("total equal to 2110", n["notes_total"], lambda r: r.rows[0][10])])

    s.query(f"Requirement 7: the principal due in each of the five years after {C}",
            f"Population: DebtScheduleLine after {ye(C)}; expected: "
            f"{', '.join(f'{y} {money(v)}' for y, v in n['maturities'])}",
            f"""
            SELECT CAST(strftime('%Y', PaymentDate) AS INTEGER) AS DueYear,
                ROUND(SUM(PrincipalAmount), 2) AS PrincipalDue
            FROM DebtScheduleLine
            WHERE PaymentDate > '{ye(C)}'
            GROUP BY DueYear
            ORDER BY DueYear;
            """,
            [Check("maturities", [[y, v] for y, v in n["maturities"]], lambda r: [list(x) for x in r.rows])])

    expected_segments = [list(x) for x in d.q(
        "SELECT c.CustomerSegment, CAST(substr(p.pd, 1, 4) AS INTEGER), ROUND(SUM(sil.LineTotal), 2) FROM SalesInvoiceLine sil "
        "JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID JOIN Customer c ON c.CustomerID = si.CustomerID "
        "JOIN (SELECT SourceDocumentID AS id, MIN(PostingDate) AS pd FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' "
        "GROUP BY 1) p ON p.id = si.SalesInvoiceID WHERE substr(p.pd, 1, 4) IN (?, ?) GROUP BY 1, 2 ORDER BY 1, 2",
        str(P), str(C))]
    s.query("Requirement 7: invoice lines by customer segment and the year their invoice was posted (SegmentRevenue)",
            f"Population: SalesInvoiceLine with its invoice, customer, and first posting, {P} and {C}; expected: "
            f"{len(expected_segments)} rows",
            f"""
            WITH Posted AS (
                SELECT SourceDocumentID AS SalesInvoiceID,
                    MIN(PostingDate) AS PostingDate
                FROM GLEntry
                WHERE SourceDocumentType = 'SalesInvoice'
                GROUP BY SourceDocumentID
            )
            SELECT c.CustomerSegment,
                CAST(strftime('%Y', p.PostingDate) AS INTEGER) AS PostingYear,
                ROUND(SUM(sil.LineTotal), 2) AS Revenue
            FROM SalesInvoiceLine AS sil
                INNER JOIN SalesInvoice AS si
                    ON si.SalesInvoiceID = sil.SalesInvoiceID
                INNER JOIN Customer AS c ON c.CustomerID = si.CustomerID
                INNER JOIN Posted AS p ON p.SalesInvoiceID = si.SalesInvoiceID
            WHERE p.PostingDate BETWEEN '{P}-01-01' AND '{ye(C)}'
            GROUP BY c.CustomerSegment, PostingYear
            ORDER BY c.CustomerSegment, PostingYear;
            """,
            [Check("the rows the workbook pastes (SegmentRevenue)", expected_segments, lambda r: [list(x) for x in r.rows])])

    revenue = {x["label"]: x for x in n["revenue"]}
    s.query(f"Requirement 7: revenue by product line on the adjusted basis, the ledger plus the cutoff by delivery year",
            f"Population: revenue postings by item group's account, closes excluded, and the cutoff items of "
            f"Requirement 4; expected: Furniture {money(revenue['Furniture']['p'])} ({P}) and "
            f"{money(revenue['Furniture']['c'])} ({C}); design services {money(n['svc_p'])} and {money(n['svc_c'])}",
            f"""
            WITH {sub(CLOSES, 12)},
            {sub(SHIPPED, 12)},
            GroupAccounts AS (
                SELECT DISTINCT i.ItemGroup, gl.AccountID
                FROM GLEntry AS gl
                    INNER JOIN SalesInvoiceLine AS sil
                        ON sil.SalesInvoiceID = gl.SourceDocumentID
                        AND sil.SalesInvoiceLineID = gl.SourceLineID
                    INNER JOIN Item AS i ON i.ItemID = sil.ItemID
                    INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                WHERE gl.SourceDocumentType = 'SalesInvoice'
                    AND a.AccountSubType = 'Operating Revenue'
            ),
            Ledger AS (
                SELECT ga.ItemGroup, gl.FiscalYear,
                    SUM(gl.Credit - gl.Debit) AS Revenue
                FROM GLEntry AS gl
                    INNER JOIN GroupAccounts AS ga ON ga.AccountID = gl.AccountID
                WHERE gl.FiscalYear IN ({P}, {C})
                    AND gl.VoucherNumber NOT IN (SELECT EntryNumber FROM Closes)
                GROUP BY ga.ItemGroup, gl.FiscalYear
            ),
            Late AS (
                SELECT i.ItemGroup, sil.LineTotal,
                    CAST(strftime('%Y', sh.DeliveryDate) AS INTEGER)
                        AS DeliveryYear,
                    CAST(strftime('%Y', p.PostingDate) AS INTEGER) AS PostingYear
                FROM SalesInvoiceLine AS sil
                    INNER JOIN Shipped AS sh
                        ON sh.SalesInvoiceID = sil.SalesInvoiceID
                    INNER JOIN Posted AS p ON p.SalesInvoiceID = sil.SalesInvoiceID
                    INNER JOIN Item AS i ON i.ItemID = sil.ItemID
                WHERE strftime('%Y', p.PostingDate)
                    <> strftime('%Y', sh.DeliveryDate)
            ),
            Cutoff AS (
                SELECT ItemGroup, DeliveryYear AS FiscalYear, LineTotal AS Amount
                FROM Late
                UNION ALL
                SELECT ItemGroup, PostingYear, -LineTotal
                FROM Late
                UNION ALL
                SELECT i.ItemGroup,
                    CAST(strftime('%Y', s.DeliveryDate) AS INTEGER),
                    ROUND(sl.QuantityShipped * sol.UnitPrice
                        * (1 - sol.Discount), 2)
                {sub(UNBILLED_FROM, 16)}
            ),
            Adjusted AS (
                SELECT l.ItemGroup, l.FiscalYear,
                    l.Revenue + COALESCE((SELECT SUM(cu.Amount)
                        FROM Cutoff AS cu
                        WHERE cu.ItemGroup = l.ItemGroup
                            AND cu.FiscalYear = l.FiscalYear), 0) AS Revenue
                FROM Ledger AS l
            )
            SELECT ItemGroup,
                ROUND(SUM(CASE WHEN FiscalYear = {P} THEN Revenue ELSE 0 END), 2)
                    AS Revenue{P},
                ROUND(SUM(CASE WHEN FiscalYear = {C} THEN Revenue ELSE 0 END), 2)
                    AS Revenue{C}
            FROM Adjusted
            GROUP BY ItemGroup
            ORDER BY CASE ItemGroup
                    WHEN 'Furniture' THEN 1 WHEN 'Lighting' THEN 2
                    WHEN 'Textiles' THEN 3 WHEN 'Accessories' THEN 4
                    ELSE 5 END;
            """,
            [c for g, x in revenue.items() for c in (
                Check(f"{g} {P}", x["p"], lambda r, g=g: r.where(ItemGroup=g)[f"Revenue{P}"]),
                Check(f"{g} {C}", x["c"], lambda r, g=g: r.where(ItemGroup=g)[f"Revenue{C}"]))]
            + [Check(f"design services {P}", n["svc_p"], lambda r: r.where(ItemGroup="Services")[f"Revenue{P}"]),
               Check(f"design services {C}", n["svc_c"], lambda r: r.where(ItemGroup="Services")[f"Revenue{C}"]),
               Check(f"{P} products equal Exercise 14.2's revenue by ship date", n["ship_p"],
                     lambda r: round(sum(x[1] for x in r.rows if x[0] in GROUP_ORDER), 2)),
               Check(f"{C} products equal revenue by ship date plus the lines never invoiced",
                     round(n["ship_c"] + n["unbilled"], 2),
                     lambda r: round(sum(x[2] for x in r.rows if x[0] in GROUP_ORDER), 2))])

    s.query("Requirement 7: freight billed, the revenue with no invoice line, and the timing of transfer",
            f"Population: SalesInvoice postings to revenue with no SourceLineID, closes excluded; expected: "
            f"{money(n['fr_p'])} ({P}) and {money(n['fr_c'])} ({C})",
            f"""
            SELECT a.AccountNumber, a.AccountName,
                ROUND(SUM(CASE WHEN gl.FiscalYear = {P}
                    THEN gl.Credit - gl.Debit ELSE 0 END), 2) AS Revenue{P},
                ROUND(SUM(CASE WHEN gl.FiscalYear = {C}
                    THEN gl.Credit - gl.Debit ELSE 0 END), 2) AS Revenue{C}
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE a.AccountID IN (
                    SELECT g2.AccountID
                    FROM GLEntry AS g2
                        INNER JOIN Account AS a2 ON a2.AccountID = g2.AccountID
                    WHERE g2.SourceDocumentType = 'SalesInvoice'
                        AND a2.AccountSubType = 'Operating Revenue'
                        AND g2.SourceLineID IS NULL)
                AND gl.FiscalYear IN ({P}, {C})
                AND gl.VoucherNumber NOT IN (
                    SELECT EntryNumber
                    FROM JournalEntry
                    WHERE EntryType LIKE 'Year-End Close%')
            GROUP BY a.AccountID, a.AccountNumber, a.AccountName;
            """,
            [Check("freight account", [int(x) for x in ch.freight_account(d)], lambda r: r.col("AccountNumber")),
             Check(f"freight {P}", n["fr_p"], lambda r: r.value(f"Revenue{P}")),
             Check(f"freight {C}", n["fr_c"], lambda r: r.value(f"Revenue{C}"))])

    s.query("Requirement 7: contract balances, customer credits in 2060 and contract liabilities in 2070",
            f"Population: the trial balances and CreditMemo; expected: 2060 {', '.join(money(v) for v in n['credits'])}; "
            f"{n['issued_n']} Issued credit memos; 2070 unused",
            f"""
            WITH {sub(balances(d.years), 12)}
            SELECT AsOfDate,
                ROUND(-SUM(CASE WHEN AccountNumber = 2060
                    THEN Balance ELSE 0 END), 2) AS CustomerCredits2060,
                ROUND(-SUM(CASE WHEN AccountNumber = 2070
                    THEN Balance ELSE 0 END), 2) AS DeferredRevenue2070,
                (SELECT COUNT(*) FROM CreditMemo WHERE Status = 'Issued')
                    AS IssuedCreditMemos,
                (SELECT ROUND(SUM(GrandTotal), 2)
                 FROM CreditMemo
                 WHERE Status = 'Issued') AS IssuedAmount
            FROM Balances
            GROUP BY AsOfDate
            ORDER BY AsOfDate;
            """,
            [Check("2060 at the year-ends", n["credits"], lambda r: r.col("CustomerCredits2060")),
             Check("2070", [0.0] * len(d.years), lambda r: [abs(v) for v in r.col("DeferredRevenue2070")]),
             Check("Issued credit memos", n["issued_n"], lambda r: r.rows[0][3]),
             Check(f"equal to 2060 at {ye(C)}", n["credits"][-1], lambda r: r.rows[0][4])])

    engs = n["engs"]
    s.query("Requirement 7: design services worked and not billed, the engagements not fully billed",
            f"Population: ServiceEngagement, ServiceTimeEntry, ServiceBillingLine; expected: {money(n['billable'])} "
            f"billable hours, all billed; engagement {', '.join(str(e['id']) for e in engs)} billed every hour worked",
            """
            WITH Worked AS (
                SELECT ServiceEngagementID, SUM(BillableHours) AS Worked,
                    MAX(WorkDate) AS LastWorkDate
                FROM ServiceTimeEntry
                GROUP BY ServiceEngagementID
            ),
            Billed AS (
                SELECT ServiceEngagementID, SUM(BilledHours) AS Billed
                FROM ServiceBillingLine
                GROUP BY ServiceEngagementID
            )
            SELECT se.ServiceEngagementID, se.Status, se.EndDate,
                se.PlannedHours, ROUND(w.Worked, 2) AS Worked,
                ROUND(b.Billed, 2) AS Billed, w.LastWorkDate,
                (SELECT ROUND(SUM(BillableHours), 2) FROM ServiceTimeEntry)
                    AS AllBillable,
                (SELECT ROUND(SUM(BilledHours), 2) FROM ServiceBillingLine)
                    AS AllBilled
            FROM ServiceEngagement AS se
                LEFT JOIN Worked AS w
                    ON w.ServiceEngagementID = se.ServiceEngagementID
                LEFT JOIN Billed AS b
                    ON b.ServiceEngagementID = se.ServiceEngagementID
            WHERE se.Status <> 'Billed'
            ORDER BY se.ServiceEngagementID;
            """,
            [Check("engagements not Billed", [e["id"] for e in engs], lambda r: r.col("ServiceEngagementID")),
             Check("billed every hour worked", [round(e["billed"], 2) for e in engs], lambda r: r.col("Worked")),
             Check("billed hours", [round(e["billed"], 2) for e in engs], lambda r: r.col("Billed")),
             Check("planned hours", [e["planned"] for e in engs], lambda r: r.col("PlannedHours")),
             Check("all billable hours", n["billable"], lambda r: r.rows[0][7]),
             Check("all billed", n["billable"], lambda r: r.rows[0][8])])

    sc, sp = notes(b).statement(d, C), notes(b).statement(d, P)
    s.query("Requirement 7: inventories and accrued liabilities as recorded, by component, at both year-ends",
            f"Population: the trial balances at {ye(P)} and {ye(C)}; expected: finished goods {money(sp['fg'])} and "
            f"{money(sc['fg'])}; materials {money(sp['mat'])} and {money(sc['mat'])}",
            f"""
            WITH {sub(balances((P, C)), 12)}
            SELECT AsOfDate,
                ROUND(SUM(CASE WHEN AccountNumber = 1040
                    THEN Balance ELSE 0 END), 2) AS FinishedGoods,
                ROUND(SUM(CASE WHEN AccountNumber = 1045
                    THEN Balance ELSE 0 END), 2) AS MaterialsAndPackaging,
                ROUND(SUM(CASE WHEN AccountNumber IN (1046, 1090)
                    THEN Balance ELSE 0 END), 2) AS WorkInProcessNet,
                ROUND(-SUM(CASE WHEN AccountNumber BETWEEN 2030 AND 2033
                    THEN Balance ELSE 0 END), 2) AS PayrollRecorded,
                ROUND(-SUM(CASE WHEN AccountNumber = 2034
                    THEN Balance ELSE 0 END), 2) AS Commissions,
                ROUND(-SUM(CASE WHEN AccountNumber = 2040
                    THEN Balance ELSE 0 END), 2) AS AccruedExpenses2040
            FROM Balances
            GROUP BY AsOfDate
            ORDER BY AsOfDate;
            """,
            [c for y, st in ((P, sp), (C, sc)) for c in (
                Check(f"{y} finished goods", st["fg"], lambda r, y=y: r.where(AsOfDate=ye(y))["FinishedGoods"]),
                Check(f"{y} materials", st["mat"], lambda r, y=y: r.where(AsOfDate=ye(y))["MaterialsAndPackaging"]),
                Check(f"{y} work in process net of 1090", st["wip"],
                      lambda r, y=y: r.where(AsOfDate=ye(y))["WorkInProcessNet"]),
                Check(f"{y} commissions", st["comm"], lambda r, y=y: r.where(AsOfDate=ye(y))["Commissions"]),
                Check(f"{y} payroll recorded (the opening 2030 alone)", n["opening_2030"] + (n["w_p"] if y == P else n["w_c"]),
                      lambda r, y=y: r.where(AsOfDate=ye(y))["PayrollRecorded"]),
                Check(f"{y} 2040", round(st["accexp"] + (notes(b).adjustments(d)["old"][y]), 2),
                      lambda r, y=y: r.where(AsOfDate=ye(y))["AccruedExpenses2040"]))])


# --- Requirement 8: after the balance-sheet date ---------------------------------------------------------------------

def r8(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r8")
    C, N = d.C, d.N
    s.query(f"Requirement 8: the records dated after fiscal {C}",
            f"Population: GLEntry after {ye(C)}; expected: {n['rows']} supplier-payment rows, {n['first_day']} to "
            f"{n['last_day']} {N}, debiting 2010 and crediting 1010",
            f"""
            SELECT gl.SourceDocumentType, a.AccountNumber,
                COUNT(*) AS Postings,
                ROUND(SUM(gl.Debit), 2) AS Debits,
                ROUND(SUM(gl.Credit), 2) AS Credits,
                MIN(gl.PostingDate) AS FirstDate, MAX(gl.PostingDate) AS LastDate
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.PostingDate > '{ye(C)}'
            GROUP BY gl.SourceDocumentType, a.AccountID, a.AccountNumber
            ORDER BY a.AccountNumber;
            """,
            [Check("source documents", ["DisbursementPayment"], lambda r: sorted(set(r.col("SourceDocumentType")))),
             Check("accounts", [1010, 2010], lambda r: r.col("AccountNumber")),
             Check("rows", n["rows"], lambda r: r.total("Postings")),
             Check("credits to cash", n["paid"], lambda r: r.where(AccountNumber=1010)["Credits"]),
             Check("debits to payables", n["paid"], lambda r: r.where(AccountNumber=2010)["Debits"])])

    s.query(f"Requirement 8: the {N} supplier payments and the invoices they paid, a search for unrecorded "
            f"liabilities",
            f"Population: DisbursementPayment after {ye(C)}; expected: {n['n_pay']} payments, {money(n['paid'])}, "
            f"{n['n_inv']} invoices of {n['n_sup']} suppliers received by {ye(C)}, {n['full']} paid in full",
            f"""
            WITH Paid AS (
                SELECT dp.PurchaseInvoiceID, COUNT(*) AS Payments,
                    SUM(dp.Amount) AS Amount
                FROM DisbursementPayment AS dp
                WHERE dp.PaymentDate > '{ye(C)}'
                GROUP BY dp.PurchaseInvoiceID
            )
            SELECT SUM(p.Payments) AS Payments, ROUND(SUM(p.Amount), 2) AS Amount,
                COUNT(*) AS Invoices,
                COUNT(DISTINCT pi.SupplierID) AS Suppliers,
                MIN(pi.ReceivedDate) AS FirstReceived,
                MAX(pi.ReceivedDate) AS LastReceived,
                SUM(CASE WHEN ABS(pi.GrandTotal - p.Amount) < 0.005
                    THEN 1 ELSE 0 END) AS PaidInFull,
                (SELECT COUNT(*)
                 FROM PurchaseInvoice
                 WHERE ReceivedDate > '{ye(C)}') AS ReceivedAfterYearEnd
            FROM Paid AS p
                INNER JOIN PurchaseInvoice AS pi
                    ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID;
            """,
            [Check("payments", n["n_pay"], lambda r: r.value("Payments")),
             Check("amount", n["paid"], lambda r: r.value("Amount")),
             Check("invoices", n["n_inv"], lambda r: r.value("Invoices")),
             Check("suppliers", n["n_sup"], lambda r: r.value("Suppliers")),
             Check("received by the year-end", True, lambda r: r.value("LastReceived") <= ye(C)),
             Check("paid in full", n["full"], lambda r: r.value("PaidInFull")),
             Check("invoices received after the year-end",
                   d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE ReceivedDate > ?", ye(C)),
                   lambda r: r.value("ReceivedAfterYearEnd"))])

    last = d.one("SELECT MAX(PaymentDate) FROM DisbursementPayment")
    same_end = f"{C}-{last[5:]}"
    s.query(f"Requirement 8: the same weeks of {C}, and the payables at {ye(C)} due in the weeks the extract covers",
            f"Population: DisbursementPayment and PurchaseInvoice; expected: {n['same_n']:,} payments, "
            f"{money(n['same_amount'])} in {C}; {money(n['due'])} due in {n['due_months']} {N}",
            f"""
            SELECT
                (SELECT COUNT(*)
                 FROM DisbursementPayment
                 WHERE PaymentDate BETWEEN '{C}-01-01' AND '{same_end}')
                    AS PaymentsSameWeeks,
                (SELECT ROUND(SUM(Amount), 2)
                 FROM DisbursementPayment
                 WHERE PaymentDate BETWEEN '{C}-01-01' AND '{same_end}')
                    AS AmountSameWeeks,
                (SELECT ROUND(SUM(pi.GrandTotal - COALESCE(
                    (SELECT SUM(dp.Amount)
                     FROM DisbursementPayment AS dp
                     WHERE dp.PurchaseInvoiceID = pi.PurchaseInvoiceID
                         AND dp.PaymentDate <= '{ye(C)}'), 0)), 2)
                 FROM PurchaseInvoice AS pi
                 WHERE pi.ReceivedDate <= '{ye(C)}'
                     AND pi.DueDate BETWEEN '{N}-01-01'
                         AND date('{last}', 'start of month', '+1 month',
                             '-1 day')) AS PayablesDue;
            """,
            [Check("payments in the same weeks", n["same_n"], lambda r: r.value("PaymentsSameWeeks")),
             Check("their amount", n["same_amount"], lambda r: r.value("AmountSameWeeks")),
             Check("payables due", n["due"], lambda r: r.value("PayablesDue"))])

    s.query(f"Requirement 8: what the extract cannot contain, the pay dates and note payments it covers",
            f"Population: PayrollPeriod and DebtScheduleLine from {N}-01-01 to {last}; expected: pay periods "
            f"{', '.join(map(str, n['periods']))} with no registers; note payments on {n['note_dates']}, all Scheduled",
            f"""
            SELECT 'Pay period' AS Record, pp.PeriodNumber AS Reference,
                pp.PayDate AS DueDate, pp.Status,
                (SELECT COUNT(*)
                 FROM PayrollRegister AS pr
                 WHERE pr.PayrollPeriodID = pp.PayrollPeriodID) AS Recorded
            FROM PayrollPeriod AS pp
            WHERE pp.PayDate BETWEEN '{N}-01-01' AND '{last}'
            UNION ALL
            SELECT 'Note payment', da.AgreementNumber, dl.PaymentDate,
                dl.Status,
                CASE WHEN dl.JournalEntryID IS NULL THEN 0 ELSE 1 END
            FROM DebtScheduleLine AS dl
                INNER JOIN DebtAgreement AS da
                    ON da.DebtAgreementID = dl.DebtAgreementID
            WHERE dl.PaymentDate BETWEEN '{N}-01-01' AND '{last}'
            ORDER BY Record DESC, DueDate;
            """,
            [Check("pay dates", n["pay_dates"], lambda r: [x[2] for x in r.rows if x[0] == "Pay period"]),
             Check("registers recorded", [0] * len(n["periods"]), lambda r: [x[4] for x in r.rows if x[0] == "Pay period"]),
             Check("note payments", d.q("SELECT COUNT(*) FROM DebtScheduleLine WHERE PaymentDate BETWEEN ? AND ?",
                                        f"{N}-01-01", last)[0][0],
                   lambda r: sum(1 for x in r.rows if x[0] == "Note payment")),
             Check("all Scheduled, none recorded", [["Scheduled", 0]],
                   lambda r: [list(v) for v in sorted({(x[3], x[4]) for x in r.rows if x[0] == "Note payment"})])])

    s.query(f"Requirement 8: materials on hand at {ye(C)} against twelve months of issues",
            f"Population: account 1045; expected: {money(n['mat'])} on hand against {money(n['issues'])} issued in {C}",
            f"""
            SELECT
                (SELECT ROUND(SUM(gl.Debit - gl.Credit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 1045
                     AND gl.PostingDate <= '{ye(C)}') AS MaterialsOnHand,
                (SELECT ROUND(SUM(gl.Credit - gl.Debit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 1045
                     AND gl.SourceDocumentType = 'MaterialIssue'
                     AND gl.FiscalYear = {C}) AS IssuedInYear;
            """,
            [Check("materials on hand", n["mat"], lambda r: r.value("MaterialsOnHand")),
             Check("twelve months of issues", n["issues"], lambda r: r.value("IssuedInYear"))])

    s.answer("Requirement 8", f"""
        The {N} records are {n['n_pay']} supplier payments, {money(n['paid'])}, from {n['first_day']} to
        {n['last_day']} {N} ({n['rows']} ledger rows, Dr 2010, Cr 1010), paying {n['n_inv']} invoices of {n['n_sup']}
        suppliers, all received from {n['recv_first']} to {n['recv_last']} {C} and recorded in payables at the
        year-end; no invoice was received after {C}, so no unrecorded liability is found. The same weeks of {C} had
        {n['same_n']:,} payments, {money(n['same_amount'])}, and payables due in {n['due_months']} {N} were
        {money(n['due'])}. The extract has no payroll for the pay dates it covers, no note payments, no freight
        settlement, and no rent, sales, or receipts, so it is incomplete: it does not show that the company stopped
        paying. Going-concern conditions: cash net of sales tax {money(n['cash_net'])}; quick ratio {n['qr_c']:.2f},
        down from {n['qr_p']:.2f}; operating cash flow {money(n['op_c'])} against {money(n['op_p'])}; materials
        ({money(n['mat'])}) above twelve months of issues ({money(n['issues'])}); {money(n['opening_ap'])} of opening
        payables unchanged for {n['years']} years. The ledger alone does not establish substantial doubt, but the
        CFO's evaluation needs evidence from outside the database.""")


# --- Requirement 9: the matters for the CFO --------------------------------------------------------------------------

def r9(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "r9")
    s.query("Requirement 9: rent paid each year, straight from cash with no lease recorded",
            f"Population: the Rent entries; expected: {', '.join(money(v) for v in n['rent'])}",
            """
            SELECT gl.FiscalYear, a.AccountNumber, a.AccountName,
                ROUND(SUM(gl.Debit), 2) AS Debits,
                ROUND(SUM(gl.Credit), 2) AS Credits
            FROM GLEntry AS gl
                INNER JOIN JournalEntry AS je
                    ON je.JournalEntryID = gl.SourceDocumentID
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE gl.SourceDocumentType = 'JournalEntry'
                AND je.EntryType = 'Rent'
            GROUP BY gl.FiscalYear, a.AccountID, a.AccountNumber, a.AccountName
            ORDER BY gl.FiscalYear, a.AccountNumber;
            """,
            [Check("rent by year", n["rent"], lambda r: [round(sum(x[3] for x in r.rows if x[0] == y), 2)
                                                         for y in d.years]),
             Check("paid from cash", [n["rent"][k] for k in range(len(d.years))],
                   lambda r: [round(sum(x[4] for x in r.rows if x[0] == y and x[1] == 1010), 2) for y in d.years])])

    s.query(f"Requirement 9: sales tax payable, what credits and debits it, and its balance at {ye(d.C)}",
            f"Population: account 2050 to {ye(d.C)}; expected: credits only from invoices, debits only from credit "
            f"memos ({money(n['memo_debits'])}), balance {money(n['stax'])}",
            f"""
            SELECT gl.SourceDocumentType, COUNT(*) AS Postings,
                ROUND(SUM(gl.Debit), 2) AS Debits,
                ROUND(SUM(gl.Credit), 2) AS Credits,
                ROUND(SUM(gl.Credit - gl.Debit), 2) AS Balance
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
            WHERE a.AccountNumber = 2050
                AND gl.PostingDate <= '{ye(d.C)}'
            GROUP BY gl.SourceDocumentType
            ORDER BY gl.SourceDocumentType;
            """,
            [Check("source documents", ["CreditMemo", "SalesInvoice"], lambda r: r.col("SourceDocumentType")),
             Check("credit memo debits", n["memo_debits"], lambda r: r.where(SourceDocumentType="CreditMemo")["Debits"]),
             Check("no credits from credit memos", 0.0, lambda r: r.where(SourceDocumentType="CreditMemo")["Credits"]),
             Check("no debits from invoices", 0.0, lambda r: r.where(SourceDocumentType="SalesInvoice")["Debits"]),
             Check("balance", n["stax"], lambda r: round(r.total("Balance"), 2))])

    s.query("Requirement 9: the opening balances no document supports, and the equity effect if none is real",
            f"Population: the opening entry's lines to 1020, 1050, 2010, 2030, 2040; expected: assets "
            f"{money(n['assets'])}, liabilities {money(n['liabilities'])}, equity {n['equity']:+,.2f}",
            """
            SELECT
                ROUND(SUM(CASE WHEN a.AccountNumber IN (1020, 1050)
                    THEN gl.Debit - gl.Credit ELSE 0 END), 2) AS Assets,
                ROUND(SUM(CASE WHEN a.AccountNumber IN (2010, 2030, 2040)
                    THEN gl.Credit - gl.Debit ELSE 0 END), 2) AS Liabilities,
                ROUND(SUM(CASE WHEN a.AccountNumber IN (2010, 2030, 2040)
                    THEN gl.Credit - gl.Debit ELSE 0 END)
                    - SUM(CASE WHEN a.AccountNumber IN (1020, 1050)
                    THEN gl.Debit - gl.Credit ELSE 0 END), 2)
                    AS EquityIfNoneIsReal
            FROM GLEntry AS gl
                INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                INNER JOIN JournalEntry AS je
                    ON gl.SourceDocumentType = 'JournalEntry'
                    AND je.JournalEntryID = gl.SourceDocumentID
            WHERE je.EntryType = 'Opening';
            """,
            [Check("assets", n["assets"], lambda r: r.value("Assets")),
             Check("liabilities", n["liabilities"], lambda r: r.value("Liabilities")),
             Check("equity if none is real", n["equity"], lambda r: r.value("EquityIfNoneIsReal"))])

    s.answer("Requirement 9", f"""
        The matters the records cannot settle, with what this script measures (the memo itself is in the package
        workbook). Tax status: no tax account and no tax recorded in {n['years']} years; if the company is a C
        corporation, 21% federal on adjusted {d.C} income of {money(n['adj_ni'])} alone is about {num(n['provision'])},
        several times materiality, so state it and record no number. Leases: rent of
        {', '.join(money(v) for v in n['rent'])} is paid from cash each month while 2120 and 1140 are unused; the
        agreements decide the right-of-use assets and lease liabilities. Sales tax: {money(n['stax'])} collected with
        no remittance recorded (2050 credits only from invoices, debits only from credit memos,
        {money(n['memo_debits'])}). Opening balances: assets {money(n['assets'])} and liabilities
        {money(n['liabilities'])} that no document supports; if none is real, equity rises by {money(n['equity'])}.
        Standards unchanged since {d.F}: at a standard rebuilt on normal capacity the manufactured finished goods would
        be about {num(n['reval_c'])} higher at the end of {d.C} and {num(n['reval_p'])} at the end of {d.P}, so a strong
        memo recommends a cost study. Recommendation: record A1-A4 and R1-R2, and do not release the package until the
        tax status, the leases, the sales tax, and the opening balances are settled.""")


def m4(b: Build) -> None:
    d = b.data
    s = script(b)
    n = context(b, "m4")
    s.query("Milestone 4: the checkpoints of what the data cannot settle",
            f"Population: DisbursementPayment after {ye(d.C)}, account 2050, the opening entry; expected: "
            f"{n['payments']} payments ({money(n['amount'])}), sales tax payable {money(n['stax'])}, equity "
            f"{n['equity']:+,.2f} if no opening balance is real",
            f"""
            SELECT
                (SELECT COUNT(*)
                 FROM DisbursementPayment
                 WHERE PaymentDate > '{ye(d.C)}') AS PaymentsAfterYearEnd,
                (SELECT ROUND(SUM(Amount), 2)
                 FROM DisbursementPayment
                 WHERE PaymentDate > '{ye(d.C)}') AS AmountAfterYearEnd,
                (SELECT ROUND(SUM(gl.Credit - gl.Debit), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                 WHERE a.AccountNumber = 2050
                     AND gl.PostingDate <= '{ye(d.C)}') AS SalesTaxPayable,
                (SELECT ROUND(SUM(CASE
                        WHEN a.AccountNumber IN (1020, 1050, 2010, 2030, 2040)
                            THEN gl.Credit - gl.Debit
                        ELSE 0 END), 2)
                 FROM GLEntry AS gl
                     INNER JOIN Account AS a ON a.AccountID = gl.AccountID
                     INNER JOIN JournalEntry AS je
                         ON gl.SourceDocumentType = 'JournalEntry'
                         AND je.JournalEntryID = gl.SourceDocumentID
                 WHERE je.EntryType = 'Opening') AS OpeningEquityEffect;
            """,
            [Check("payments", n["payments"], lambda r: r.value("PaymentsAfterYearEnd")),
             Check("amount", n["amount"], lambda r: r.value("AmountAfterYearEnd")),
             Check("sales tax payable", n["stax"], lambda r: r.value("SalesTaxPayable")),
             Check("equity if none is real", n["equity"], lambda r: r.value("OpeningEquityEffect"))])


EXERCISES = [("Requirement 1", r1), ("Milestone 1", m1), ("Requirement 2", r2_), ("Requirement 3", r3),
             ("Requirement 4", r4), ("Requirement 5", r5), ("Requirement 6", r6), ("Requirement 7", r7),
             ("Requirement 8", r8), ("Requirement 9", r9), ("Milestone 4", m4)]
