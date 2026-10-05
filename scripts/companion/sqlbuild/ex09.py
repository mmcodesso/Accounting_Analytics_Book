"""Instructor SQL solutions to the exercises of Chapter 9 (one table per query, no joins or aggregates: the chapter
teaches SELECT, calculated columns, scalar functions, DISTINCT, WHERE, NULL, ORDER BY and LIMIT; counts come from the
message pane, one query per value).

Every expected value comes from the context functions of Chapter 9's instructor notes (facts/notes/ch09.py) or from
read-only SQL of this module; every actual value is read from the query's result. The SQL names the fiscal window's
years and the account IDs as the data give them, so a rolled dataset rebuilds the scripts for its own window.
"""

from __future__ import annotations

import sys

from paths import REPO
from sqlbuild.script import Build, Check

if str(REPO / "facts") not in sys.path:
    sys.path.insert(0, str(REPO / "facts"))
from notes import ch09, money, num  # noqa: E402


def claim(*_args, **_kw) -> None:
    """The notes' claims are tested by scripts/facts.py check; here only their values are read."""


def count(column: str, value):
    return lambda r: sum(1 for v in r.col(column) if v == value)


def ids_list(values) -> str:
    return ", ".join(str(v) for v in values)


def cap(k: int) -> str:
    """A count that opens a sentence, in words."""
    return ch09.word(k).capitalize()


def wording(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# --- Exercise 9.1 --------------------------------------------------------------------------------

def ex1(b: Build) -> None:
    d = b.data
    n = ch09.ex1(d, claim)
    opposite = n["depreciation"] + [a["number"] for a in n["asset_other"] + n["equity"] + n["revenue"]]
    inactive = [a["number"] for a in n["inactive"]]
    headers = d.q("SELECT AccountID, AccountNumber FROM Account WHERE AccountSubType = 'Header' ORDER BY AccountNumber")
    combos = d.q("SELECT AccountType, AccountSubType, COUNT(*) FROM Account GROUP BY 1, 2 ORDER BY 1, 2")
    n_subtypes = d.one("SELECT COUNT(DISTINCT AccountSubType) FROM Account")
    clearing_sources = [r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? "
                                          "ORDER BY 1", n["clearing"])]
    mfg = d.q("SELECT AccountNumber, AccountName FROM Account WHERE AccountName LIKE '%manufacturing%' "
              "AND IsActive = 1 ORDER BY AccountNumber")
    allowance = n["asset_other"][0]
    # the two inactive accounts named for manufacturing salaries and factory overhead (requirement (5))
    idle = [a for a in n["inactive"] if "Manufacturing" in a["name"] or "Factory" in a["name"]]
    assert len(idle) == 2, idle
    s = b.script("Ex 9.1.sql", "reviewing the chart of accounts",
                 f"{n['n']} accounts; {n['n_opposite']} opposite normal balances; no posting to a header or "
                 f"inactive account")

    s.query("Requirement (1): every account of the chart, sorted by number",
            f"Population: Account, every row; expected: {n['n']} accounts, "
            + ", ".join(f"{t} {k}" for t, k in n["types"]),
            """
            SELECT AccountID, AccountNumber, AccountName, AccountType,
                AccountSubType, ParentAccountID, NormalBalance, IsActive
            FROM Account
            ORDER BY AccountNumber;
            """,
            [Check("accounts", n["n"], len)]
            + [Check(f"{t} accounts", k, count("AccountType", t)) for t, k in n["types"]]
            + [Check(f"{st} subtype accounts", k, count("AccountSubType", st)) for st, k in n["subtypes"]])

    s.query("Requirement (2): the account types",
            f"Population: Account; expected: {len(n['types'])} types",
            """
            SELECT DISTINCT AccountType
            FROM Account
            ORDER BY AccountType;
            """,
            [Check("account types", sorted(t for t, _ in n["types"]), lambda r: sorted(r.col("AccountType")))])

    s.query("Requirement (2): the combinations of type and subtype",
            f"Population: Account; expected: {len(combos)} combinations of {n_subtypes} subtypes, "
            f"a Header subtype in every type",
            """
            SELECT DISTINCT AccountType, AccountSubType
            FROM Account
            ORDER BY AccountType, AccountSubType;
            """,
            [Check("type and subtype combinations", len(combos), len),
             Check("distinct subtypes", n_subtypes, lambda r: len(set(r.col("AccountSubType")))),
             Check("types with a Header subtype", len(n["types"]), count("AccountSubType", "Header"))])

    sub = n["subs"]
    s.query("Requirement (3): the header accounts and their parents",
            f"Population: Account, AccountSubType Header; expected: {n['headers']} headers, "
            f"{len(n['top'])} without a ParentAccountID",
            """
            SELECT AccountID, AccountNumber, AccountName, AccountType,
                ParentAccountID
            FROM Account
            WHERE AccountSubType = 'Header'
            ORDER BY AccountNumber;
            """,
            [Check("header accounts", n["headers"], len),
             Check("top-level headers (no ParentAccountID)", n["top"],
                   lambda r: [x for x, p in zip(r.col("AccountNumber"), r.col("ParentAccountID")) if p is None])]
            + [Check(f"{h['number']} sits under", h["parent"],
                     lambda r, h=h: r.where(AccountID=r.where(AccountNumber=h["number"])["ParentAccountID"])
                     ["AccountNumber"]) for h in sub])

    s.query("Requirement (3): postings to the header accounts",
            "Population: GLEntry, the header accounts' AccountIDs; expected: no rows",
            f"""
            SELECT GLEntryID, PostingDate, AccountID, Debit, Credit
            FROM GLEntry
            WHERE AccountID IN ({ids_list(i for i, _ in headers)});
            """,
            [Check("postings to header accounts", 0, len)])

    s.query("Requirement (4): accounts whose normal balance is opposite to their type",
            f"Population: Account; expected: {n['n_opposite']} contra accounts",
            """
            SELECT AccountID, AccountNumber, AccountName, AccountType,
                AccountSubType, NormalBalance
            FROM Account
            WHERE (AccountType IN ('Asset', 'Expense')
                    AND NormalBalance = 'Credit')
                OR (AccountType IN ('Liability', 'Equity', 'Revenue')
                    AND NormalBalance = 'Debit')
            ORDER BY AccountNumber;
            """,
            [Check("accounts with an opposite normal balance", n["n_opposite"], len),
             Check("their account numbers", sorted(opposite), lambda r: sorted(r.col("AccountNumber"))),
             Check("every one a contra subtype", True,
                   lambda r: all(st.startswith("Contra") for st in r.col("AccountSubType")))])

    s.query("Requirement (5): the inactive accounts",
            f"Population: Account, IsActive 0; expected: {n['n_inactive']} accounts",
            """
            SELECT AccountID, AccountNumber, AccountName, AccountType,
                AccountSubType
            FROM Account
            WHERE IsActive = 0
            ORDER BY AccountNumber;
            """,
            [Check("inactive accounts", n["n_inactive"], len),
             Check("their account numbers", inactive, lambda r: r.col("AccountNumber"))])

    s.query("Requirement (5): postings to the inactive accounts",
            "Population: GLEntry, the inactive accounts' AccountIDs; expected: no rows",
            f"""
            SELECT GLEntryID, PostingDate, AccountID, Debit, Credit
            FROM GLEntry
            WHERE AccountID IN ({ids_list(a["id"] for a in n["inactive"])});
            """,
            [Check("postings to inactive accounts", 0, len)])

    s.query("Requirement (5): active accounts whose names mention manufacturing",
            f"Population: Account, IsActive 1; expected: {len(mfg)} accounts, among them 1090 and 5080",
            """
            SELECT AccountID, AccountNumber, AccountName, AccountType,
                AccountSubType
            FROM Account
            WHERE AccountName LIKE '%manufacturing%' AND IsActive = 1
            ORDER BY AccountNumber;
            """,
            [Check("active manufacturing accounts", [a for a, _ in mfg], lambda r: r.col("AccountNumber")),
             Check("1090 is", n["clearing_name"], lambda r: r.where(AccountNumber=1090)["AccountName"]),
             Check("1090's AccountID", n["clearing"], lambda r: r.where(AccountNumber=1090)["AccountID"]),
             Check("5080 is", n["variance_name"], lambda r: r.where(AccountNumber=5080)["AccountName"])])

    s.query("Requirement (5): the source documents that post to 1090",
            f"Population: GLEntry, AccountID {n['clearing']}; expected: {wording(clearing_sources)}",
            f"""
            SELECT DISTINCT SourceDocumentType
            FROM GLEntry
            WHERE AccountID = {n['clearing']}
            ORDER BY SourceDocumentType;
            """,
            [Check("source types posting to 1090", clearing_sources, lambda r: r.col("SourceDocumentType"))])

    s.query("Requirement (6): postings to 1030 Allowance for Doubtful Accounts",
            f"Population: GLEntry, AccountID {allowance['id']}; expected: no rows",
            f"""
            SELECT GLEntryID, PostingDate, Debit, Credit, Description
            FROM GLEntry
            WHERE AccountID = {allowance['id']};
            """,
            [Check("postings to 1030", 0, len)])

    by_type = {}
    for t, st, k in combos:
        if st != "Header":
            by_type.setdefault(t, []).append(f"{st} ({k})")
    split = "; ".join(f"{t} into {wording(by_type[t])}" for t, _ in n["types"])
    s.answer("Requirement (2)",
             f"The chart has {n['n']} accounts of {len(n['types'])} types "
             f"({', '.join(f'{t} {k}' for t, k in n['types'])}) and {n_subtypes} subtypes. Every type has its own "
             f"Header subtype for its header accounts, and the other subtypes divide the types as a balance sheet and "
             f"an income statement do: {split}.")
    s.answer("Requirement (3)",
             f"{cap(n['headers'])} accounts are headers. {cap(len(n['top']))} of them ({ids_list(n['top'])}) have no "
             f"ParentAccountID and head a section of the chart. "
             + " and ".join(f"{h['number']} {h['name']}" for h in sub)
             + f" have a parent ({' and '.join(str(h['parent']) for h in sub)}), so they are sub-headers and the chart "
             f"has two levels of headers. A header only groups the accounts below it: none has a posting, and none "
             f"should, because balances belong to the detail accounts.")
    s.answer("Requirement (4)",
             f"{cap(n['n_opposite'])} accounts carry a normal balance opposite to their type, and all are contra accounts: "
             f"{allowance['number']} {allowance['name']} and the accumulated depreciation accounts "
             f"{ids_list(n['depreciation'])} reduce assets with a credit; "
             + "; ".join(f"{a['number']} {a['name']} reduces equity with a debit" for a in n["equity"]) + "; "
             + " and ".join(f"{a['number']} {a['name']}" for a in n["revenue"])
             + " reduce revenue with a debit. AND binds before OR, so the parentheses do not change this result, but "
             "they make the two conditions explicit to a reviewer, and the query no longer depends on the default "
             "order.")
    s.answer("Requirement (5)",
             f"{cap(n['n_inactive'])} accounts are inactive and none has a posting: "
             + ", ".join(f"{a['number']} {a['name']}" for a in n["inactive"])
             + f". Manufacturing salaries and factory overhead are not expensed: they are charged to 1090 "
             f"{n['clearing_name']} (AccountID {n['clearing']}), whose postings come from "
             f"{wording(clearing_sources)} documents. Payroll and overhead entries debit it, production completions "
             f"release standard cost to inventory, and work order closes clear what is left to 5080 "
             f"{n['variance_name']}, so the costs reach cost of goods sold through inventory and the variance.")
    s.answer("Requirement (6), memo to the controller",
             f"The chart of accounts holds {n['n']} accounts in {len(n['types'])} types and {n_subtypes} subtypes, "
             f"organized under {ch09.word(len(n['top']))} top-level headers with two sub-headers, so it reads like the "
             f"financial statements. {cap(n['n_opposite'])} contra accounts carry the opposite normal balance, as they "
             f"should, and {n['n_inactive']} inactive accounts have no postings, so nothing is posted where it should "
             f"not be. Manufacturing salaries and factory overhead are recorded through 1090 "
             f"{n['clearing_name']} rather than the inactive {' and '.join(str(a['number']) for a in idle)}, so manufacturing cost reaches cost of goods "
             f"sold through inventory and 5080 {n['variance_name']}.\n\n"
             f"Before year-end, two points deserve review. First, {allowance['number']} {allowance['name']} has no "
             f"postings at all, so no allowance for credit losses has ever been recorded against the receivables "
             f"(Chapter 8 estimates one). Second, 4070 Sales Discounts is inactive, so promotion discounts are netted "
             f"in revenue rather than shown separately (the Part II case); the presentation should be a decision, not "
             f"a default. The inactive accounts should stay closed to posting.")


# --- Exercise 9.2 --------------------------------------------------------------------------------

def ex2(b: Build) -> None:
    d = b.data
    n = ch09.ex2(d, claim)
    ppv, year = n["account"], d.C
    unf, fav, tax = (ch09.PPV[i][1] for i in range(3))
    s = b.script("Ex 9.2.sql", "the purchase price variance in the ledger",
                 f"fiscal {year} postings to 5060 net {money(n['net'])}, the credit of close {n['close']}")

    s.query("Requirement (1): the AccountID of account 5060",
            f"Population: Account; expected: AccountID {ppv}",
            """
            SELECT AccountID, AccountNumber, AccountName
            FROM Account
            WHERE AccountNumber = 5060;
            """,
            [Check("AccountID of 5060", ppv, lambda r: r.value("AccountID")),
             Check("its name", n["name"], lambda r: r.value("AccountName"))])

    s.query(f"Requirement (2): the source document types of 5060's postings in fiscal {year}",
            f"Population: GLEntry, AccountID {ppv}, fiscal {year}; expected: JournalEntry and PurchaseInvoice",
            f"""
            SELECT DISTINCT SourceDocumentType
            FROM GLEntry
            WHERE AccountID = {ppv} AND FiscalYear = {year}
            ORDER BY SourceDocumentType;
            """,
            [Check("source document types", ["JournalEntry", "PurchaseInvoice"], lambda r: r.col("SourceDocumentType"))])

    s.query("Requirement (2): the JournalEntry posting, which the analysis excludes",
            f"Population: GLEntry, AccountID {ppv}, fiscal {year}, JournalEntry; expected: the close {n['close']}",
            f"""
            SELECT GLEntryID, PostingDate, Debit, Credit, VoucherNumber,
                Description
            FROM GLEntry
            WHERE AccountID = {ppv} AND FiscalYear = {year}
                AND SourceDocumentType = 'JournalEntry';
            """,
            [Check("JournalEntry rows", 1, len),
             Check("its voucher", n["close"], lambda r: r.value("VoucherNumber")),
             Check("its credit", n["close_amount"], lambda r: r.value("Credit")),
             Check("its debit", 0, lambda r: r.value("Debit")),
             Check("its date", f"{year}-12-31", lambda r: r.value("PostingDate"))])

    s.query("Requirement (3): the descriptions of the remaining postings",
            f"Population: GLEntry, AccountID {ppv}, fiscal {year}, PurchaseInvoice; expected: three descriptions",
            f"""
            SELECT DISTINCT Description
            FROM GLEntry
            WHERE AccountID = {ppv} AND FiscalYear = {year}
                AND SourceDocumentType = 'PurchaseInvoice'
            ORDER BY Description;
            """,
            [Check("descriptions", sorted([unf, fav, tax]), lambda r: r.col("Description"))])

    s.query("Requirement (4): the ten largest unfavorable purchase variances",
            f"Population: GLEntry, AccountID {ppv}, fiscal {year}, unfavorable variances; "
            f"expected: largest {money(n['largest'])}",
            f"""
            SELECT GLEntryID, PostingDate, VoucherNumber, Debit, Description
            FROM GLEntry
            WHERE AccountID = {ppv} AND FiscalYear = {year}
                AND Description = '{unf}'
            ORDER BY Debit DESC, PostingDate, VoucherNumber
            LIMIT 10;
            """,
            [Check("rows", 10, len),
             Check("largest Debit", n["largest"], lambda r: r.cell(0, "Debit")),
             Check("its posting date", n["postings"][0]["date"], lambda r: r.cell(0, "PostingDate")),
             Check("its voucher", n["postings"][0]["voucher"], lambda r: r.cell(0, "VoucherNumber")),
             Check("the next two amounts", n["next"], lambda r: sorted(set(r.col("Debit")), reverse=True)[1:3])])

    for key, text, side in ch09.PPV:
        v = n[key]
        column = "Debit" if side == "debit" else "Credit"
        other = "Credit" if side == "debit" else "Debit"
        s.query(f"Requirement (5): the postings described as {text[7:]} (count in the message pane)",
                f"Population: GLEntry, AccountID {ppv}, fiscal {year}; expected: {num(v['n'])} {side}s, "
                f"{money(v['amount'])}",
                f"""
                SELECT GLEntryID, PostingDate, VoucherNumber, Debit, Credit
                FROM GLEntry
                WHERE AccountID = {ppv} AND FiscalYear = {year}
                    AND Description = '{text}';
                """,
                [Check("postings", v["n"], len),
                 Check(f"{side}s", v[f"{side}s"], lambda r, c=column: sum(1 for x in r.col(c) if x > 0)),
                 Check(f"total {column}", v["amount"], lambda r, c=column: round(r.total(c), 2)),
                 Check(f"total {other}", 0, lambda r, c=other: round(r.total(c), 2))])

    s.answer("Requirement (2)",
             f"The postings of fiscal {year} come from PurchaseInvoice and JournalEntry documents. The only "
             f"JournalEntry row is the year-end close {n['close']}, a credit of {money(n['close_amount'])} that "
             f"brings the account back to zero for the new year. Including it would net the year's activity to zero, so an "
             f"analysis of the account excludes it, as Tutorial 9.2 excluded the close of 5080.")
    s.answer("Requirements (3) and (5)",
             f"The {num(n['pi_rows'])} PurchaseInvoice postings carry three descriptions: unfavorable variances "
             f"({num(n['unf']['n'])} debits, {money(n['unf']['amount'])}), favorable variances "
             f"({num(n['fav']['n'])} credits, {money(n['fav']['amount'])}), and nonrecoverable purchase tax "
             f"({num(n['tax']['n'])} debits, {money(n['tax']['amount'])}). Their net, {money(n['net'])}, equals the "
             f"close. The account records two kinds of cost: the difference between the supplier's invoice price and "
             f"the purchase-order price at which the goods were received (the invoice clears goods received not "
             f"invoiced, 2020, at the receipt value), and purchase tax that cannot be recovered. A credit means the "
             f"supplier billed below the order price, a favorable variance; {n['rounding']} on lines billed at the "
             f"order price are rounding.")
    s.answer("Requirement (6)",
             "Purchase price variance arises when a supplier invoice is posted: the PurchaseInvoice documents compare "
             "the invoice price with the order price of the goods received. Manufacturing variance arises when a work "
             "order closes: the WorkOrderClose documents compare the actual cost charged to production with the "
             "standard cost released, so one measures buying and the other making.")


# --- Exercise 9.3 --------------------------------------------------------------------------------

def ex3(b: Build) -> None:
    d = b.data
    n = ch09.ex3(d, claim)
    rates = d.one("SELECT COUNT(DISTINCT ROUND(StandardDirectLaborCost / StandardLaborHoursPerUnit, 2)) FROM Item "
                  "WHERE SupplyMode = 'Manufactured'")
    s = b.script("Ex 9.3.sql", "standard cost components of manufactured items",
                 f"{n['n']} manufactured items; labor + overhead = conversion cost on every item")
    columns = """
            SELECT ItemCode, ItemName, ItemGroup, StandardCost,
                StandardLaborHoursPerUnit, StandardDirectLaborCost,
                StandardVariableOverheadCost, StandardFixedOverheadCost,
                StandardConversionCost"""
    groups = ", ".join(f"{g} {k}" for g, k in n["groups"])

    s.query("Requirement (1): the manufactured items and their standards",
            f"Population: Item, SupplyMode Manufactured; expected: {n['n']} items ({groups})",
            columns + """
            FROM Item
            WHERE SupplyMode = 'Manufactured'
            ORDER BY ItemCode;
            """,
            [Check("manufactured items", n["n"], len)]
            + [Check(f"{g} items", k, count("ItemGroup", g)) for g, k in n["groups"]])

    s.query("Requirement (2): the same list with the standard material cost",
            f"Population: as (1); expected: material cost from {money(n['material_low'])} to "
            f"{money(n['material_high'])}",
            columns + """,
                ROUND(StandardCost - StandardConversionCost, 2)
                    AS StandardMaterialCost
            FROM Item
            WHERE SupplyMode = 'Manufactured'
            ORDER BY ItemCode;
            """,
            [Check("items", n["n"], len),
             Check("lowest material cost", n["material_low"], lambda r: min(r.col("StandardMaterialCost"))),
             Check("highest material cost", n["material_high"], lambda r: max(r.col("StandardMaterialCost")))])

    s.query("Requirement (3): items whose conversion components do not add up",
            "Population: Item, SupplyMode Manufactured; expected: no rows",
            """
            SELECT ItemCode, ItemName, StandardDirectLaborCost,
                StandardVariableOverheadCost, StandardFixedOverheadCost,
                StandardConversionCost
            FROM Item
            WHERE SupplyMode = 'Manufactured'
                AND ROUND(StandardDirectLaborCost
                    + StandardVariableOverheadCost
                    + StandardFixedOverheadCost, 2)
                    <> ROUND(StandardConversionCost, 2);
            """,
            [Check("items failing the component check", 0, len)])

    s.query("Requirement (4): the list with the labor rate per standard hour, sorted by it",
            f"Population: as (1); expected: rates from {money(n['rate_low'])} to {money(n['rate_high'])}",
            columns + """,
                ROUND(StandardCost - StandardConversionCost, 2)
                    AS StandardMaterialCost,
                ROUND(StandardDirectLaborCost / StandardLaborHoursPerUnit, 2)
                    AS LaborRatePerHour
            FROM Item
            WHERE SupplyMode = 'Manufactured'
            ORDER BY LaborRatePerHour, ItemCode;
            """,
            [Check("items", n["n"], len),
             Check("lowest rate (first row)", n["rate_low"], lambda r: r.cell(0, "LaborRatePerHour")),
             Check("highest rate (last row)", n["rate_high"], lambda r: r.cell(len(r) - 1, "LaborRatePerHour")),
             Check("distinct rates", rates, lambda r: len(set(r.col("LaborRatePerHour"))))])

    top = n["top"]
    s.query("Requirement (5): the ten items with the highest standard conversion cost",
            f"Population: Item, SupplyMode Manufactured; expected: {top[0]['code']} first "
            f"({money(top[0]['cost'])}), all {n['top_group']}",
            """
            SELECT ItemCode, ItemName, ItemGroup, StandardConversionCost
            FROM Item
            WHERE SupplyMode = 'Manufactured'
            ORDER BY StandardConversionCost DESC
            LIMIT 10;
            """,
            [Check("rows", 10, len)]
            + [Check(f"rank {i + 1}", (t["code"], t["cost"]),
                     lambda r, i=i: (r.cell(i, "ItemCode"), r.cell(i, "StandardConversionCost")))
               for i, t in enumerate(top)]
            + [Check("item groups of the ten", [n["top_group"]], lambda r: sorted(set(r.col("ItemGroup"))))])

    s.answer("How the standards are built",
             f"Charles River makes {n['n']} items ({groups}). Each standard cost is material plus conversion cost: "
             f"the material part, StandardCost less StandardConversionCost, runs from {money(n['material_low'])} to "
             f"{money(n['material_high'])} a unit, and the conversion part is direct labor plus variable and fixed "
             f"overhead. The component check returns no rows, so the three parts add up to the conversion cost on "
             f"every item. Direct labor is the standard hours times an item-specific rate: the rate per standard hour "
             f"runs from {money(n['rate_low'])} to {money(n['rate_high'])}, with {rates} different rates, so there is "
             f"no single plant rate. The highest conversion costs are {top[0]['code']} {top[0]['name']} "
             f"({money(top[0]['cost'])}), {top[1]['code']} ({money(top[1]['cost'])}) and {top[2]['code']} "
             f"({money(top[2]['cost'])}), and all ten of the highest are {n['top_group']} items.")


# --- Exercise 9.4 --------------------------------------------------------------------------------

def ex4(b: Build) -> None:
    d = b.data
    n = ch09.ex4(d, claim)
    end, year = n["end"], d.C
    s = b.script("Ex 9.4.sql", "open work orders at year-end",
                 f"{n['n']} work orders without a ClosedDate; {n['due']} due on or before {end}")
    statuses = ", ".join(f"{st} {n['status'][st]}" for st in ch09.OPEN_STATUSES)

    s.query("Requirement (1): the work orders with no ClosedDate",
            f"Population: WorkOrder, ClosedDate NULL; expected: {n['n']} work orders ({statuses})",
            """
            SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
                CompletedDate, PlannedQuantity
            FROM WorkOrder
            WHERE ClosedDate IS NULL;
            """,
            [Check("open work orders", n["n"], len)]
            + [Check(f"{st} work orders", n["status"][st], count("Status", st)) for st in ch09.OPEN_STATUSES])

    s.query("Requirement (2): the release year and the completion date or a label",
            f"Population: as (1); expected: every release year {year}, not completed on "
            f"{n['not_completed']} work orders",
            """
            SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
                COALESCE(CompletedDate, 'not completed') AS Completed,
                PlannedQuantity,
                CAST(SUBSTR(WorkOrderNumber, 4, 4) AS INTEGER) AS ReleaseYear
            FROM WorkOrder
            WHERE ClosedDate IS NULL;
            """,
            [Check("release years", [int(y) for y, _ in n["by_year"]], lambda r: sorted(set(r.col("ReleaseYear")))),
             Check("not completed", n["not_completed"], count("Completed", "not completed")),
             Check("completed but not closed", n["status"]["Completed"],
                   lambda r: sum(1 for v in r.col("Completed") if v != "not completed")),
             Check("first release date", n["released_low"], lambda r: min(r.col("ReleasedDate"))),
             Check("last release date", n["released_high"], lambda r: max(r.col("ReleasedDate")))])

    s.query("Requirement (3): the statuses of the open work orders",
            f"Population: as (1); expected: {', '.join(ch09.OPEN_STATUSES)}",
            """
            SELECT DISTINCT Status
            FROM WorkOrder
            WHERE ClosedDate IS NULL;
            """,
            [Check("statuses", sorted(ch09.OPEN_STATUSES), lambda r: sorted(r.col("Status")))])

    for st in ch09.OPEN_STATUSES:
        s.query(f"Requirement (3): the open work orders with Status {st} (count in the message pane)",
                f"Population: as (1); expected: {n['status'][st]} work orders",
                f"""
                SELECT WorkOrderNumber, Status, ReleasedDate, DueDate
                FROM WorkOrder
                WHERE ClosedDate IS NULL AND Status = '{st}';
                """,
                [Check(f"{st} work orders", n["status"][st], len)])

    oldest = n["oldest"]
    s.query(f"Requirement (4): the open work orders due on or before {end}",
            f"Population: as (1); expected: {n['due']} work orders, the oldest {oldest['number']}",
            f"""
            SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
                COALESCE(CompletedDate, 'not completed') AS Completed
            FROM WorkOrder
            WHERE ClosedDate IS NULL AND DueDate <= '{end}'
            ORDER BY DueDate, WorkOrderNumber;
            """,
            [Check("work orders due", n["due"], len),
             Check("the oldest", oldest["number"], lambda r: r.cell(0, "WorkOrderNumber")),
             Check("its release date", oldest["released"], lambda r: r.cell(0, "ReleasedDate")),
             Check("its due date", oldest["due"], lambda r: r.cell(0, "DueDate")),
             Check("its status", "Released", lambda r: r.cell(0, "Status")),
             Check("the next two", [(x["number"], x["due"]) for x in n["next"]],
                   lambda r: [(r.cell(i, "WorkOrderNumber"), r.cell(i, "DueDate")) for i in (1, 2)])]
            + [Check(f"{st} among them", k, count("Status", st)) for st, k in n["due_status"]])

    released = dict(n["due_status"])["Released"]
    s.query("Requirement (5): those still Released, where work has not started",
            f"Population: the work orders of (4); expected: {released} work orders",
            f"""
            SELECT WorkOrderNumber, Status, ReleasedDate, DueDate,
                PlannedQuantity
            FROM WorkOrder
            WHERE ClosedDate IS NULL AND DueDate <= '{end}'
                AND Status = 'Released'
            ORDER BY DueDate, WorkOrderNumber;
            """,
            [Check("released and past due", released, len),
             Check("the oldest", oldest["number"], lambda r: r.cell(0, "WorkOrderNumber"))])

    due = ", ".join(f"{st} {k}" for st, k in n["due_status"])
    s.answer("Requirement (2)",
             f"The release year is {year} on every open work order (released {n['released_low']} to "
             f"{n['released_high']}), so nothing from earlier years is still open. COALESCE shows not completed for "
             f"the {n['not_completed']} Released and In Progress work orders and a date for the "
             f"{n['status']['Completed']} that were completed but not closed.")
    s.answer("Requirement (6), memo to the production manager",
             f"At {end}, {n['n']} work orders had no ClosedDate: {statuses}. All were released in {year}. Of them, "
             f"{n['due']} were due on or before {end} ({due}). The oldest, {oldest['number']}, was released on "
             f"{oldest['released']} and due on {oldest['due']}, and it was still Released at the end of the data; the "
             f"next are {n['next'][0]['number']} (due {n['next'][0]['due']}) and {n['next'][1]['number']} (due "
             f"{n['next'][1]['due']}). Of the past-due work orders, {released} have not been started, a backlog worth "
             f"reviewing: are they still needed, or should they be cancelled? The {n['status']['Completed']} completed "
             f"work orders should be closed.\n\n"
             f"A work order's variance is recorded only when it closes, when the WorkOrderClose document posts the "
             f"difference between actual and standard cost to 5080. The cost of these work orders sits in work in "
             f"process and 1090 until then, so their variance is not in the fiscal {year} results and will be recorded "
             f"when they close, after the data ends. (Counting each status takes one query and the message pane; "
             f"COUNT comes in Chapter 10.)")


# --- Exercise 9.5 --------------------------------------------------------------------------------

def ex5(b: Build) -> None:
    d = b.data
    n = ch09.ex5(d, claim)
    end = n["end"]
    s = b.script("Ex 9.5.sql", "shipments that need follow-up",
                 f"{n['n']} shipments without a tracking number; {n['transit']} In Transit past their delivery date")

    s.query("Requirement (1): the values of Status",
            f"Population: Shipment; expected: {' and '.join(st for st, _ in n['status'])}",
            """
            SELECT DISTINCT Status
            FROM Shipment
            ORDER BY Status;
            """,
            [Check("statuses", sorted(st for st, _ in n["status"]), lambda r: r.col("Status"))])

    for st, k in n["status"]:
        s.query(f"Requirement (1): the shipments with Status {st} (count in the message pane)",
                f"Population: Shipment; expected: {num(k)} shipments",
                f"""
                SELECT ShipmentID, ShipmentNumber, ShipmentDate, Status
                FROM Shipment
                WHERE Status = '{st}';
                """,
                [Check(f"{st} shipments", k, len)])

    s.query("Requirement (1): the values of ShippedBy",
            f"Population: Shipment; expected: {len(n['carriers'])} carriers",
            """
            SELECT DISTINCT ShippedBy
            FROM Shipment
            ORDER BY ShippedBy;
            """,
            [Check("carriers", n["carriers"], lambda r: r.col("ShippedBy"))])

    s.query("Requirement (2): shipments with no tracking number",
            f"Population: Shipment, TrackingNumber NULL; expected: {n['n']} shipments, {n['low']} to {n['high']}",
            """
            SELECT ShipmentNumber, ShipmentDate, ShippedBy, Status
            FROM Shipment
            WHERE TrackingNumber IS NULL
            ORDER BY ShipmentDate;
            """,
            [Check("shipments without tracking", n["n"], len),
             Check("first date", n["low"], lambda r: r.cell(0, "ShipmentDate")),
             Check("last date", n["high"], lambda r: r.cell(len(r) - 1, "ShipmentDate"))])

    s.query(f"Requirement (3): shipments In Transit with a DeliveryDate before {end}",
            f"Population: Shipment, Status In Transit; expected: {n['transit']} shipments, oldest {n['oldest']}",
            f"""
            SELECT ShipmentNumber, ShipmentDate, DeliveryDate, ShippedBy,
                TrackingNumber, Status
            FROM Shipment
            WHERE Status = 'In Transit' AND DeliveryDate < '{end}'
            ORDER BY DeliveryDate;
            """,
            [Check("stale In Transit shipments", n["transit"], len),
             Check("oldest DeliveryDate", n["oldest"], lambda r: r.cell(0, "DeliveryDate"))])

    s.query(f"Requirement (3): the other In Transit shipments, delivered on or after {end}",
            f"Population: Shipment, Status In Transit; expected: {n['later']} shipment"
            f"{'' if n['later'] == 1 else 's'}",
            f"""
            SELECT ShipmentNumber, ShipmentDate, DeliveryDate, Status
            FROM Shipment
            WHERE Status = 'In Transit' AND DeliveryDate >= '{end}';
            """,
            [Check("In Transit, delivered on or after the end", n["later"], len)])

    s.answer("Requirement (4)",
             f"The SQL results equal the Excel filters of Tutorial 2.1: the blank TrackingNumber filter shows the "
             f"same {n['n']} shipments (NULL in the database, dated {n['low']} to {n['high']}), and the Status filter "
             f"shows the same {num(dict(n['status'])['In Transit'])} In Transit shipments, of which {n['transit']} have "
             f"a DeliveryDate before {end}, the oldest {n['oldest']}; {n['later_word']} more has a DeliveryDate on or "
             f"after {end}. In Excel the date comparison was left to the eye; in SQL it is part of the condition. The "
             f"SQL tests are easier to rerun because the conditions are written down: the saved script reruns them on "
             f"next year's data in one click, and a reviewer can read exactly which rows were kept, where an Excel "
             f"filter has to be rebuilt by hand and leaves no record of itself.")
    s.answer("Requirement (5)",
             "The missing tracking number is a completeness test: ask the shipping team why these shipments left "
             "without a tracking number recorded, and whether the carrier's records hold one that was never "
             "entered. The In Transit status after the delivery date is a consistency (or timeliness) test, a status "
             "that contradicts the delivery date: ask who updates the status on delivery and why these shipments were "
             "never marked Delivered.")


# --- Exercise 9.6 --------------------------------------------------------------------------------

def ex6(b: Build) -> None:
    d = b.data
    n = ch09.ex6(d, claim)
    labor, clock = n["labor"], dict(n["clock"])
    missing = d.q("SELECT TimeClockEntryID, WorkDate FROM TimeClockEntry WHERE ClockOutTime IS NULL ORDER BY WorkDate")
    titles = dict(d.q(f"SELECT EmployeeID, JobTitle FROM Employee WHERE EmployeeID IN "
                      f"({ids_list(n['employees'] + [n['clock_employee']])})"))
    terminated = d.one("SELECT COUNT(*) FROM Employee WHERE TerminationDate IS NOT NULL")
    left = d.one("SELECT TerminationDate FROM Employee WHERE EmployeeID = ?", n["clock_employee"])
    after = [w for _, w in missing if left is not None and w > left]
    s = b.script("Ex 9.6.sql", "missing values in time and labor records",
                 f"{len(labor)} direct rows without an operation; {len(missing)} clock entries without a "
                 f"clock-out; terminations consistent")

    s.query("Requirement (1): direct labor time with no work order operation",
            f"Population: LaborTimeEntry, Direct Manufacturing; expected: {n['n_labor']} rows "
            f"({ids_list(x['id'] for x in labor)})",
            """
            SELECT LaborTimeEntryID, EmployeeID, WorkOrderID, WorkDate,
                RegularHours, OvertimeHours,
                RegularHours + OvertimeHours AS Hours
            FROM LaborTimeEntry
            WHERE LaborType = 'Direct Manufacturing'
                AND WorkOrderOperationID IS NULL
            ORDER BY LaborTimeEntryID;
            """,
            [Check("rows", len(labor), len),
             Check("the entries", [(x["id"], x["employee"], x["work_order"], x["date"]) for x in labor],
                   lambda r: [(r.cell(i, "LaborTimeEntryID"), r.cell(i, "EmployeeID"), r.cell(i, "WorkOrderID"),
                               r.cell(i, "WorkDate")) for i in range(len(r))])]
            + [Check(f"hours of entry {x['id']}", x["hours"], lambda r, i=x["id"]: r.where(LaborTimeEntryID=i)["Hours"])
               for x in labor])

    s.query("Requirement (1): the employees on those rows",
            f"Population: Employee; expected: {ids_list(n['employees'])}, {n['title']}",
            f"""
            SELECT EmployeeID, EmployeeName, JobTitle, CostCenterID
            FROM Employee
            WHERE EmployeeID IN ({ids_list(n['employees'])});
            """,
            [Check("employees", len(n["employees"]), len)]
            + [Check(f"employee {e}'s job title", titles[e], lambda r, e=e: r.where(EmployeeID=e)["JobTitle"])
               for e in n["employees"]])

    s.query("Requirement (2): the values of ClockStatus",
            f"Population: TimeClockEntry; expected: {' and '.join(clock)}",
            """
            SELECT DISTINCT ClockStatus
            FROM TimeClockEntry
            ORDER BY ClockStatus;
            """,
            [Check("clock statuses", sorted(clock), lambda r: r.col("ClockStatus"))])

    for st, k in n["clock"]:
        s.query(f"Requirement (2): the time clock entries with ClockStatus {st} (count in the message pane)",
                f"Population: TimeClockEntry; expected: {num(k)} entries",
                f"""
                SELECT TimeClockEntryID, EmployeeID, WorkDate, ClockStatus
                FROM TimeClockEntry
                WHERE ClockStatus = '{st}';
                """,
                [Check(f"{st} entries", k, len)])

    s.query("Requirement (2): time clock entries with no ClockOutTime",
            f"Population: TimeClockEntry, ClockOutTime NULL; expected: {len(missing)} entries, employee "
            f"{n['clock_employee']}, Pending",
            """
            SELECT TimeClockEntryID, EmployeeID, WorkDate, ClockInTime,
                COALESCE(ClockOutTime, 'missing') AS ClockOut,
                RegularHours, OvertimeHours, ClockStatus
            FROM TimeClockEntry
            WHERE ClockOutTime IS NULL
            ORDER BY WorkDate;
            """,
            [Check("entries without a clock-out", len(missing), len),
             Check("their employees", [n["clock_employee"]], lambda r: sorted(set(r.col("EmployeeID")))),
             Check("their work dates", [f"{y}-01-01" for y in (d.F, d.P, d.C)], lambda r: r.col("WorkDate")),
             Check("their statuses", ["Pending"], lambda r: sorted(set(r.col("ClockStatus")))),
             Check("ClockOut shows", ["missing"], lambda r: sorted(set(r.col("ClockOut"))))])

    s.query(f"Requirement (2): employee {n['clock_employee']}",
            f"Population: Employee; expected: {n['clock_title']}",
            f"""
            SELECT EmployeeID, EmployeeName, JobTitle, EmploymentStatus,
                TerminationDate
            FROM Employee
            WHERE EmployeeID = {n['clock_employee']};
            """,
            [Check("job title", titles[n["clock_employee"]], lambda r: r.value("JobTitle")),
             Check("termination date", left, lambda r: r.value("TerminationDate"))])

    s.query("Requirement (3): employees with a TerminationDate",
            f"Population: Employee, TerminationDate not NULL; expected: {terminated} employees, all Terminated "
            f"and inactive",
            """
            SELECT EmployeeID, EmployeeName, TerminationDate,
                EmploymentStatus, IsActive
            FROM Employee
            WHERE TerminationDate IS NOT NULL
            ORDER BY TerminationDate;
            """,
            [Check("terminated employees", terminated, len),
             Check("EmploymentStatus values", ["Terminated"], lambda r: sorted(set(r.col("EmploymentStatus")))),
             Check("IsActive values", [0], lambda r: sorted(set(r.col("IsActive"))))])

    s.query("Requirement (3): employees without a TerminationDate who are Terminated or inactive",
            "Population: Employee, TerminationDate NULL; expected: no rows",
            """
            SELECT EmployeeID, EmployeeName, EmploymentStatus, IsActive
            FROM Employee
            WHERE TerminationDate IS NULL
                AND (EmploymentStatus = 'Terminated' OR IsActive = 0);
            """,
            [Check("inconsistent employees", 0, len)])

    rows = "; ".join(f"{x['id']} (employee {x['employee']}, work order {x['work_order']}, {x['date']}, "
                     f"{num(x['hours'], 2)} hours)" for x in labor)
    s.answer("Requirement (4), findings and follow-up questions",
             f"1. {n['n_labor'].capitalize()} Direct Manufacturing rows have no WorkOrderOperationID: {rows}; the "
             f"employees are {n['title']}. Their cost was charged as direct labor but cannot be traced to an "
             f"operation, so it reaches the work order's actual cost (and the variance) without a routing step to "
             f"compare it with. Ask production which operation the time belongs to, and why the time entry system "
             f"accepted direct time without one.\n\n"
             f"2. ClockStatus is {wording([f'{st} ({num(k)})' for st, k in n['clock']])}. {n['n_missing']} entries "
             f"have no ClockOutTime, all for employee {n['clock_employee']} ({n['clock_title']}) on January 1 of "
             f"{d.F}, {d.P} and {d.C}, all Pending, yet each records regular and overtime hours"
             + (f", and {ch09.word(len(after))} of them fall after the employee's termination on {left}" if after else "")
             + ". Hours without a complete time record cannot be verified, and if they were paid they reach labor "
             "cost without support. Ask payroll who entered the hours, on what support, and whether they were "
             "paid, and to whom.\n\n"
             f"3. {cap(terminated)} employees have a TerminationDate; all are Terminated with IsActive 0, and no employee "
             f"without one is Terminated or inactive, so the three columns agree. Ask payroll to confirm that no time "
             f"or pay was recorded for these employees after their termination dates (Chapter 12 tests it).")


EXERCISES = [("9.1", ex1), ("9.2", ex2), ("9.3", ex3), ("9.4", ex4), ("9.5", ex5), ("9.6", ex6)]
