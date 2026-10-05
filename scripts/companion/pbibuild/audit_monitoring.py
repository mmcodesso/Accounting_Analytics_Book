"""Audit Monitoring.pbip: internal audit's monitoring file, as Tutorials 16.1 to 16.3 build it.

Each function applies one tutorial's steps to the project as the previous tutorial left it: the queries with the Power
Query Editor's step names (Merged Queries, Added Custom, Unpivoted Only Selected Columns, the Append as New query), the
Enter data tables, relationships, measures, pages, visuals, and the queries of the DAX query tab Tests. The DAX the
text prints (the Date table, the measures, the test queries) and the rows it has the reader type (the Tests and
Dispositions tables) are read from the chapter's .qmd files, so the file and the text cannot drift.

The checks compare the model with the exception register rebuilt in SQL by facts/notes/ch16.py, which applies the
tutorials' flag rules to CharlesRiver.sqlite (the values the chapter's hidden notes state).
"""

from __future__ import annotations

import re
import sys
import textwrap
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from paths import REPO
from pbibuild.model import MEASURES_TABLE, Column, Measure, Model, Query, Table, query_table
from pbibuild.pbir import Page, Report, Visual, agg, col, lit, meas
from pbibuild.project import Project
from xlbuild import pq

sys.path.insert(0, str(REPO / "facts"))
from db import Data  # noqa: E402
from notes import ch16  # noqa: E402

FILE = "Audit Monitoring"
MONEY = "#,0.00"
COUNT = "#,0"
MEASURES = MEASURES_TABLE        # Key Measures: Desktop 2.158 rejects a table named Measures
CHAPTER = REPO / "chapters" / "16-audit-monitoring"
JE_FLAGS = ["Weekend", "Backdated", "SelfApproved", "AboveLimit", "RoundAmount"]
PO_FLAGS = ["SelfApproved", "AboveLimit", "AfterTermination"]
PR_FLAGS = ["PaidBeforeApproval", "AfterTermination", "SelfApproved"]
REGISTER = ["TestID", "DocumentNumber", "EventDate", "Amount", "EmployeeID"]     # tbl-16-02
LIGHT, DARK = "#FEF5E7", "#F39C12"     # the book's amber tint and highlight fill, both read with ink text


# --- the text --------------------------------------------------------------------------------------------------------

def dax_blocks(qmd: str, kind: str) -> list[str]:
    """The DAX blocks of a tutorial file marked <!-- dax-check: kind -->, in order, without their common indent."""
    text = (CHAPTER / qmd).read_text(encoding="utf-8")
    return [textwrap.dedent(m.group(1)).strip("\n") for m in
            re.finditer(r"<!-- dax-check: " + kind + r" -->\s*\n```\s*\n(.*?)\n```", text, re.S)]


def definitions(body: str) -> list[tuple[str, str]]:
    """(name, expression) of each definition in a block: a line `Name = ...` starts one, other lines continue it."""
    out = []
    for line in body.split("\n"):
        m = re.match(r"^([A-Za-z][^=\n]*?) =(?: (.*))?$", line)
        if m and not line.startswith(("VAR", "RETURN", "EVALUATE")):
            out.append((m.group(1).strip(), [m.group(2)] if m.group(2) else []))
        else:
            out[-1][1].append(line)
    return [(name, "\n".join(lines).strip("\n")) for name, lines in out]


def measures(qmd: str, names: list[str], formats: dict[str, str]) -> list[Measure]:
    found = [d for body in dax_blocks(qmd, "measure") for d in definitions(body)]
    assert [n for n, _ in found] == names, f"{qmd}: measures {[n for n, _ in found]}"
    return [Measure(n, dax, formats.get(n)) for n, dax in found]


def md_table(path: Path, label: str) -> list[list[str]]:
    """The body rows of the Markdown table captioned {#label}, cells without their code backticks."""
    lines = path.read_text(encoding="utf-8").split("\n")
    i = next(i for i, l in enumerate(lines) if "{#" + label + "}" in l) - 1
    while not lines[i].strip():
        i -= 1
    rows = []
    while lines[i].startswith("|"):
        rows.insert(0, lines[i])
        i -= 1
    cells = [[c.strip().strip("`") for c in r.strip().strip("|").split("|")] for r in rows]
    return cells[2:]                                  # without the header and the separator


# --- queries ---------------------------------------------------------------------------------------------------------

def mlist(names: list[str]) -> str:
    return "{" + ", ".join(pq.m_string(n) for n in names) + "}"


def flags(q: Query, rules: list[tuple[str, str]]) -> Query:
    """Add Column > Custom Column for each flag, then one Changed Type that makes them Whole Number."""
    for name, formula in rules:
        q.custom(name, formula)
    return q.types({name: "Int64.Type" for name, _ in rules})


def exceptions(name: str, of: Query, flag_names: list[str], prefix: str) -> Query:
    """Reference, Unpivot Only Selected Columns on the flags, Value filtered to 1, and the TestID column."""
    q = Query.reference(name, of)
    cols = {c: t for c, t in q.columns.items() if c not in flag_names}
    cols.update({"Attribute": "type text", "Value": "type any"})
    q.raw("Unpivoted Only Selected Columns", f'Table.Unpivot({pq.PREV}, {mlist(flag_names)}, "Attribute", "Value")', cols)
    return q.filter("([Value] = 1)").custom("TestID", f'"{prefix} " & [Attribute]')


class Append(Query):
    """A query made with Home > Append Queries > Append Queries as New."""

    def __init__(self, name: str, parts: list[Query]):
        super().__init__(name)
        self.parts = parts
        self.columns = {c: (parts[0].columns[c] if len({p.columns[c] for p in parts}) == 1 else "type any")
                        for c in parts[0].columns}
        self.source = ("append",)

    def m(self, path: str) -> str:
        names = ", ".join(pq.step(p.name) for p in self.parts)
        return pq.steps_query([("Source", f"Table.Combine({{{names}}})")] + self.steps)


def entered(name: str, columns: list[str], rows: list[list[str]], hidden: bool = False) -> Table:
    """A table typed with Home > Enter data: text columns."""
    return Table(name, [Column(c, "string") for c in columns], entered=rows, hidden=hidden)


# --- report pieces ---------------------------------------------------------------------------------------------------

def _source(field_: dict) -> tuple[str, str, dict]:
    kind = next(iter(field_))
    entity = field_[kind]["Expression"]["SourceRef"]["Entity"]
    alias = entity[0].lower()
    return entity, alias, {kind: {"Expression": {"SourceRef": {"Source": alias}}, "Property": field_[kind]["Property"]}}


def at_least(name: str, field_: dict, value: int) -> dict:
    """Filters pane, Filters on this visual: show items when the value is greater than or equal to `value`."""
    entity, alias, ref = _source(field_)
    return {"name": name, "field": field_, "type": "Advanced", "howCreated": "User",
            "filter": {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"Comparison": {"ComparisonKind": 2, "Left": ref,
                                                                 "Right": {"Literal": {"Value": f"{value}L"}}}}}]}}


def drillthrough(page: Page, field_: dict, value: str) -> None:
    """Make `page` a drill-through page on `field_` (the Drillthrough well), as left after a drill-through to `value`;
    Desktop adds the back button."""
    entity, alias, ref = _source(field_)
    fname = f"{page.name}Drill"
    page.page_type = "Drillthrough"
    page.extra = {
        "filterConfig": {"filters": [{
            "name": fname, "field": field_, "type": "Categorical", "howCreated": "Drillthrough",
            "filter": {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [ref],
                                                       "Values": [[{"Literal": {"Value": f"'{value}'"}}]]}}}]}}]},
        "pageBinding": {"name": f"{page.name}Binding", "type": "Drillthrough", "referenceScope": "Default",
                        "parameters": [{"name": f"{page.name}Param", "boundFilter": fname, "fieldExpr": field_}]}}
    page.add(Visual("backButton", "actionButton", 20, 20, 40, 40,
                    objects={"icon": [{"properties": {"shapeType": lit("back")}, "selector": {"id": "default"}}]},
                    container_objects={"visualLink": [{"properties": {"show": lit(True), "type": lit("Back")}}]}))


def rules_fill(measure: dict, metadata: str) -> dict:
    """Conditional formatting > Background color with Rules: a light fill from 1 up to 5, a darker fill from 5."""
    def cmp(kind, v):
        return {"Comparison": {"ComparisonKind": kind, "Left": measure, "Right": {"Literal": {"Value": f"{v}L"}}}}
    cases = [{"Condition": {"And": {"Left": cmp(2, 1), "Right": cmp(3, 5)}}, "Value": {"Literal": {"Value": f"'{LIGHT}'"}}},
             {"Condition": cmp(2, 5), "Value": {"Literal": {"Value": f"'{DARK}'"}}}]
    return {"values": [{"properties": {"backColor": {"solid": {"color": {"expr": {"Conditional": {"Cases": cases}}}}}},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": metadata}}]}


def docs_of(*filters: str) -> str:
    """DAX: the register's document numbers under the filters, in text order, separated by commas."""
    return ("CONCATENATEX ( CALCULATETABLE ( VALUES ( Exceptions[DocumentNumber] ), " + ", ".join(filters) + " ), "
            "Exceptions[DocumentNumber], \", \", Exceptions[DocumentNumber], ASC )")


def card(name: str, x, y, w, h, field_: dict, title: str | None = None) -> Visual:
    return Visual(name, "cardVisual", x, y, w, h, {"Data": [field_]}, title=title)


# --- the build -------------------------------------------------------------------------------------------------------

@dataclass
class Build:
    xlsx: Path
    exp: object
    year: int
    project: Project = None
    q: dict = field(default_factory=dict)
    tests: list[str] = field(default_factory=list)          # the queries of the Tests tab, in order

    def __post_init__(self):
        self.project = Project(FILE, Model(FILE), Report())
        self.d = Data()
        self.claims: list[str] = []
        self.facts = {k: fn(self.d, self.claim) for k, fn in (("t1", ch16.t1), ("t2", ch16.t2), ("t3", ch16.t3))}

    def claim(self, ok: bool, text: str) -> None:
        if not ok:
            self.claims.append(text)

    @property
    def model(self) -> Model:
        return self.project.model

    @property
    def report(self) -> Report:
        return self.project.report

    def check(self, section: str, label: str, expected, dax: str, tolerance: float = 0.005) -> None:
        self.project.check(section, label, expected, dax, tolerance)

    def add_tests(self, qmd: str) -> None:
        self.tests += dax_blocks(qmd, "query")
        self.project.queries["Tests"] = "\n\n".join(self.tests) + "\n"
        if "Checks" in self.project.queries:                 # keep Tests first, the tab the text renames
            self.project.queries["Checks"] = self.project.queries.pop("Checks")


def t16_1(b: Build) -> None:
    d, m, x = b.d, b.model, b.xlsx
    t = "Tutorial 16.1"
    # Steps 1-3: the two Tables, the columns the tests need, and the approver's limit
    emp = (Query.navigator("Employee", x, 74, "Employee")
           .select(["EmployeeID", "EmployeeName", "CostCenterID", "JobTitle", "EmploymentStatus", "TerminationDate",
                    "MaxApprovalAmount"])
           .types({"TerminationDate": "type date"}))
    je = (Query.navigator("JournalEntry", x, 2, "JournalEntry")
          .select(["JournalEntryID", "EntryNumber", "PostingDate", "EntryType", "TotalAmount", "CreatedByEmployeeID",
                   "CreatedDate", "ApprovedByEmployeeID"])
          .types({"PostingDate": "type date", "CreatedDate": "type datetime"})
          .merge(emp, "ApprovedByEmployeeID", "EmployeeID", ["MaxApprovalAmount"])
          .rename({"MaxApprovalAmount": "ApproverLimit"}))
    # Steps 4-5: the flags and the score
    flags(je, [("Weekend", "if Date.DayOfWeek([CreatedDate], Day.Monday) >= 5 then 1 else 0"),
               ("Backdated", "if Date.From([CreatedDate]) > [PostingDate] then 1 else 0"),
               ("SelfApproved", "if [CreatedByEmployeeID] = [ApprovedByEmployeeID] then 1 else 0"),
               ("AboveLimit", "if [TotalAmount] > [ApproverLimit] then 1 else 0"),
               ("RoundAmount", "if Number.Mod([TotalAmount], 1000) = 0 then 1 else 0"),
               ("RiskScore", "[Weekend] + [Backdated] + [SelfApproved] + [AboveLimit] + [RoundAmount]")])
    b.q.update(JournalEntry=je, Employee=emp)
    # Step 6: load, the Date table, and the two relationships
    # RiskScore: Don't summarize (Step 8), so the table lists each entry's score and the filter offers Advanced filtering
    m.add(query_table(je, formats={"TotalAmount": MONEY, "ApproverLimit": MONEY},
                      summarize={k: "none" for k in ("JournalEntryID", "CreatedByEmployeeID", "ApprovedByEmployeeID",
                                                     "RiskScore")}))
    m.add(query_table(emp, formats={"MaxApprovalAmount": MONEY},
                      summarize={"EmployeeID": "none", "CostCenterID": "none"}))
    (date_body,) = dax_blocks("_tutorial-01.qmd", "table")
    (name, expr), = definitions(date_body)
    assert name == "Date"
    m.add(Table("Date", [
        Column("Date", "dateTime", source="[Date]", fmt="Short Date", extra=("isKey",)),
        Column("Year", "int64", source="[Year]"), Column("Quarter", "string", source="[Quarter]"),
        Column("YearQuarter", "string", source="[YearQuarter]"), Column("YearMonth", "string", source="[YearMonth]"),
        Column("MonthNumber", "int64", source="[MonthNumber]"),
        Column("MonthName", "string", source="[MonthName]", sort_by="MonthNumber")],
        dax=expr, props=("dataCategory: Time",)))
    m.relate("JournalEntry.PostingDate", "Date.Date")
    m.relate("JournalEntry.ApprovedByEmployeeID", "Employee.EmployeeID")
    # Step 7: the Measures table (Enter data, its empty Column1 hidden) and the first measures
    m.add(Table(MEASURES, [Column("Column1", "string", hidden=True)], entered=[],
                measures=measures("_tutorial-01.qmd", ["Entries", "Entry Amount"],
                                  {"Entries": COUNT, "Entry Amount": MONEY})))
    m.query_order.append(MEASURES)
    # Step 9: the journal entries' ledger lines, with the account (Enable load cleared on Account)
    account = Query.navigator("Account", x, 1, "Account").select(["AccountID", "AccountNumber", "AccountName"])
    lines = (Query.navigator("JournalLines", x, 3, "GLEntry").filter('([SourceDocumentType] = "JournalEntry")')
             .select(["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "SourceDocumentID"])
             .merge(account, "AccountID", "AccountID", ["AccountNumber", "AccountName"]))
    m.add(query_table(lines, formats={"Debit": MONEY, "Credit": MONEY},
                      summarize={k: "none" for k in ("GLEntryID", "AccountID", "SourceDocumentID", "AccountNumber")}))
    m.stage(account)
    m.relate("JournalLines.SourceDocumentID", "JournalEntry.JournalEntryID")
    # Step 11: JE Exceptions (Enable load cleared)
    jex = (exceptions("JE Exceptions", je, JE_FLAGS, "JE")
           .select(["TestID", "EntryNumber", "PostingDate", "TotalAmount", "ApprovedByEmployeeID"])
           .rename({"EntryNumber": "DocumentNumber", "PostingDate": "EventDate", "TotalAmount": "Amount",
                    "ApprovedByEmployeeID": "EmployeeID"}))
    m.stage(jex)
    b.q.update(JournalLines=lines, Account=account, **{"JE Exceptions": jex})

    # the expected values, from the register rebuilt in SQL
    f1 = b.facts["t1"]
    entries = ch16.entries(d)
    counts = dict(f1["flags"])
    top = f1["top"]
    risky = sorted((e for e in entries if e["score"] >= 2), key=lambda e: -e["score"])
    lines_of_top = d.q("SELECT a.AccountNumber, a.AccountName, g.Debit, g.Credit FROM GLEntry g JOIN Account a "
                       "ON a.AccountID = g.AccountID JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
                       "WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryNumber = ? ORDER BY g.Debit DESC",
                       top["number"])
    # Steps 7-8: the Journal Entries page
    page = b.report.add(Page("journalEntries", "Journal Entries"))
    page.add(Visual("scores", "pivotTable", 20, 20, 460, 260, {
        "Rows": [col("JournalEntry", "RiskScore")],
        "Values": [meas(MEASURES, "Entries"), meas(MEASURES, "Entry Amount")]}))
    page.add(Visual("riskiest", "tableEx", 500, 20, 760, 320, {"Values": [
        col("JournalEntry", "EntryNumber"), col("JournalEntry", "PostingDate"), col("JournalEntry", "EntryType"),
        col("JournalEntry", "RiskScore")]},
        filters=[at_least("riskScoreAtLeast2", col("JournalEntry", "RiskScore"), 2)],
        sort=[(col("JournalEntry", "RiskScore"), "Descending")]))
    zero = f1["scores"][0]
    page.expect = ["RiskScore", "Entry Amount", f"{zero['n']:,}", f"{zero['amount']:,.2f}", top["number"],
                   risky[-1]["number"]]
    # Step 10: the Entry Lines drill-through page, as left after drilling through on the top entry
    page = b.report.add(Page("entryLines", "Entry Lines"))
    drillthrough(page, col("JournalEntry", "EntryNumber"), top["number"])
    page.add(Visual("lines", "tableEx", 20, 80, 900, 560, {"Values": [
        col("JournalLines", "AccountNumber"), col("JournalLines", "AccountName"),
        agg("JournalLines", "Debit"), agg("JournalLines", "Credit")]}))
    page.expect = ["AccountName", lines_of_top[0][1], f"{top['debits']:,.2f}"]
    # Step 12: the Validation page and Test 1
    page = b.report.add(Page("validation", "Validation"))
    page.add(card("entries", 20, 20, 300, 160, meas(MEASURES, "Entries")))
    page.add(card("entryAmount", 340, 20, 300, 160, meas(MEASURES, "Entry Amount")))
    page.add(card("lineDebits", 660, 20, 300, 160, agg("JournalLines", "Debit")))
    # the card shows Display units Auto, as a reader leaves it: 129.86M
    page.expect = [f"Entries, {f1['n']} card", f"Entry Amount, {f1['total'] / 1e6:,.2f}M card",
                   f"Debit, {f1['debits'] / 1e6:,.2f}M card"]
    b.add_tests("_tutorial-01.qmd")

    # checks
    b.check(t, "JournalEntry rows", f1["n"], "COUNTROWS ( JournalEntry )", 0)
    b.check(t, "Employee rows", d.one("SELECT COUNT(*) FROM Employee"), "COUNTROWS ( Employee )", 0)
    for name in JE_FLAGS:
        b.check(t, f"{name} flags", counts[name], f"SUM ( JournalEntry[{name}] )", 0)
    for s in f1["scores"]:
        r = f"JournalEntry[RiskScore] = {s['score']}"
        b.check(t, f"entries scoring {s['score']}", s["n"], f"CALCULATE ( [Entries], {r} )", 0)
        b.check(t, f"amount of the entries scoring {s['score']}", round(s["amount"], 2),
                f"CALCULATE ( [Entry Amount], {r} )")
    b.check(t, "the entry with the highest score", top["number"],
            f"CALCULATE ( MAX ( JournalEntry[EntryNumber] ), JournalEntry[RiskScore] = {f1['scores'][-1]['score']} )")
    b.check(t, "entries scoring 2 or more (the table on the Journal Entries page)", len(risky),
            "COUNTROWS ( FILTER ( JournalEntry, JournalEntry[RiskScore] >= 2 ) )", 0)
    for e in risky:
        b.check(t, f"{e['number']} risk score", e["score"],
                f'CALCULATE ( MAX ( JournalEntry[RiskScore] ), JournalEntry[EntryNumber] = "{e["number"]}" )', 0)
    b.check(t, "entries with no approver limit", 0,
            "COUNTROWS ( FILTER ( JournalEntry, ISBLANK ( JournalEntry[ApproverLimit] ) ) )", 0)
    for y in d.years:
        b.check(t, f"{y} entries (the Date relationship)", sum(1 for e in entries if e["date"][:4] == str(y)),
                f"CALCULATE ( [Entries], 'Date'[Year] = {y} )", 0)
    approver, n_approved = Counter(e["approver"] for e in entries).most_common(1)[0]
    b.check(t, f"entries approved by employee {approver} (the Employee relationship)", n_approved,
            f"CALCULATE ( [Entries], Employee[EmployeeID] = {approver} )", 0)
    days = (date(d.N, 12, 31) - date(d.F, 1, 1)).days + 1
    b.check(t, "Date rows", days, "COUNTROWS ( 'Date' )", 0)
    b.check(t, "JournalLines rows", f1["lines"], "COUNTROWS ( JournalLines )", 0)
    b.check(t, "journal lines with no entry", 0,
            "COUNTROWS ( FILTER ( JournalLines, ISBLANK ( RELATED ( JournalEntry[EntryNumber] ) ) ) )", 0)
    b.check(t, "journal lines with no account name", 0,
            "COUNTROWS ( FILTER ( JournalLines, ISBLANK ( JournalLines[AccountName] ) ) )", 0)
    e = f'JournalEntry[EntryNumber] = "{top["number"]}"'
    b.check(t, f"{top['number']} lines", top["lines"], f"CALCULATE ( COUNTROWS ( JournalLines ), {e} )", 0)
    b.check(t, f"{top['number']} debits", round(top["debits"], 2), f"CALCULATE ( SUM ( JournalLines[Debit] ), {e} )")
    b.check(t, f"{top['number']} credits", round(sum(r[3] for r in lines_of_top), 2),
            f"CALCULATE ( SUM ( JournalLines[Credit] ), {e} )")
    b.check(t, "JE Exceptions rows (the five flags summed; the query is not loaded)", f1["exceptions"],
            " + ".join(f"SUM ( JournalEntry[{n}] )" for n in JE_FLAGS), 0)
    b.check(t, "Test 1: entries", f1["n"], "[Entries]", 0)
    b.check(t, "Test 1: entry amount", round(f1["total"], 2), "ROUND ( [Entry Amount], 2 )")
    b.check(t, "Test 1: line debits", round(f1["debits"], 2), "ROUND ( SUM ( JournalLines[Debit] ), 2 )")
    b.check(t, "Test 1: line credits", round(f1["credits"], 2), "ROUND ( SUM ( JournalLines[Credit] ), 2 )")


def t16_2(b: Build) -> None:
    d, m, x = b.d, b.model, b.xlsx
    t = "Tutorial 16.2"
    emp = b.q["Employee"]
    # Steps 1-2
    po = (Query.navigator("PurchaseOrder", x, 33, "PurchaseOrder")
          .select(["PurchaseOrderID", "PONumber", "OrderDate", "CreatedByEmployeeID", "ApprovedByEmployeeID",
                   "OrderTotal"])
          .types({"OrderDate": "type date"}))
    pr = (Query.navigator("PayrollRegister", x, 69, "PayrollRegister")
          .select(["PayrollRegisterID", "PayrollPeriodID", "EmployeeID", "NetPay", "ApprovedByEmployeeID",
                   "ApprovedDate"])
          .types({"ApprovedDate": "type date"}))
    pay = (Query.navigator("PayrollPayment", x, 71, "PayrollPayment").select(["PayrollRegisterID", "PaymentDate"])
           .types({"PaymentDate": "type date"}))
    period = (Query.navigator("PayrollPeriod", x, 59, "PayrollPeriod")
              .select(["PayrollPeriodID", "PeriodEndDate", "PayDate"])
              .types({"PeriodEndDate": "type date", "PayDate": "type date"}))
    # Step 3: the purchase order flags
    po.merge(emp, "ApprovedByEmployeeID", "EmployeeID", ["MaxApprovalAmount", "TerminationDate"]).rename(
        {"MaxApprovalAmount": "ApproverLimit", "TerminationDate": "ApproverTermination"})
    flags(po, [("SelfApproved", "if [CreatedByEmployeeID] = [ApprovedByEmployeeID] then 1 else 0"),
               ("AboveLimit", "if [OrderTotal] > [ApproverLimit] then 1 else 0"),
               ("AfterTermination",
                "if [ApproverTermination] <> null and [OrderDate] > [ApproverTermination] then 1 else 0")])
    # Steps 4-5: the payment, the period, the payee, and the payroll flags
    pr.merge(pay, "PayrollRegisterID", "PayrollRegisterID", ["PaymentDate"])
    pr.merge(period, "PayrollPeriodID", "PayrollPeriodID", ["PeriodEndDate", "PayDate"])
    pr.merge(emp, "EmployeeID", "EmployeeID", ["TerminationDate"])
    flags(pr, [("PaidBeforeApproval", "if [PaymentDate] <> null and [PaymentDate] < [ApprovedDate] then 1 else 0"),
               ("AfterTermination", "if [TerminationDate] <> null and [PeriodEndDate] > [TerminationDate] then 1 else 0"),
               ("SelfApproved", "if [EmployeeID] = [ApprovedByEmployeeID] then 1 else 0")])
    # Step 6: the two exception queries
    pox = (exceptions("PO Exceptions", po, PO_FLAGS, "PO")
           .select(["TestID", "PONumber", "OrderDate", "OrderTotal", "ApprovedByEmployeeID"])
           .rename({"PONumber": "DocumentNumber", "OrderDate": "EventDate", "OrderTotal": "Amount",
                    "ApprovedByEmployeeID": "EmployeeID"}))
    prx = (exceptions("Payroll Exceptions", pr, PR_FLAGS, "PR")
           .custom("DocumentNumber", '"Register " & Text.From([PayrollRegisterID])')
           .select(["TestID", "DocumentNumber", "PayDate", "NetPay", "ApprovedByEmployeeID"])
           .rename({"PayDate": "EventDate", "NetPay": "Amount", "ApprovedByEmployeeID": "EmployeeID"}))
    # Step 7: the register, appended as new
    jex = b.q["JE Exceptions"]
    for q in (jex, pox, prx):
        q.columns = {c: q.columns[c] for c in REGISTER}          # the order Table.SelectColumns gives them
    reg = Append("Exceptions", [jex, pox, prx]).types({"EventDate": "type date"})
    m.add(query_table(po, formats={"OrderTotal": MONEY, "ApproverLimit": MONEY},
                      summarize={k: "none" for k in ("PurchaseOrderID", "CreatedByEmployeeID", "ApprovedByEmployeeID")},
                      hidden={"PurchaseOrderID", "CreatedByEmployeeID", "ApprovedByEmployeeID", *PO_FLAGS}))
    m.add(query_table(pr, formats={"NetPay": MONEY},
                      summarize={k: "none" for k in ("PayrollRegisterID", "PayrollPeriodID", "EmployeeID",
                                                     "ApprovedByEmployeeID")},
                      hidden={"PayrollRegisterID", "PayrollPeriodID", "EmployeeID", "ApprovedByEmployeeID", *PR_FLAGS}))
    m.stage(pay)
    m.stage(period)
    m.stage(pox)
    m.stage(prx)
    m.add(query_table(reg, formats={"Amount": MONEY}, summarize={"EmployeeID": "none"}))
    # Step 8: the Tests table (Enter data), the rows of tbl-16-01
    tests = md_table(CHAPTER / "chapter.qmd", "tbl-16-01")
    m.add(entered("Tests", ["TestID", "Test", "Process", "Source"], tests))
    m.query_order.append("Tests")
    # Step 9: relationships, and the keys and flags of the populations hidden
    m.relate("Exceptions.TestID", "Tests.TestID")
    m.relate("Exceptions.EventDate", "Date.Date")
    m.relate("Exceptions.EmployeeID", "Employee.EmployeeID")
    m.relate("PurchaseOrder.OrderDate", "Date.Date")
    m.relate("PayrollRegister.PayDate", "Date.Date")
    for c in m.tables["JournalEntry"].columns:
        if c.name in ("JournalEntryID", "CreatedByEmployeeID", "ApprovedByEmployeeID", *JE_FLAGS):
            c.hidden = True
    # Step 10: the measures
    m.tables[MEASURES].measures += measures("_tutorial-02.qmd", ["Exceptions", "Population", "Rate per 1,000"],
                                              {"Exceptions": COUNT, "Population": COUNT, "Rate per 1,000": "0.0"})
    b.q.update(PurchaseOrder=po, PayrollRegister=pr, PayrollPayment=pay, PayrollPeriod=period, Exceptions=reg,
               **{"PO Exceptions": pox, "Payroll Exceptions": prx})

    # the expected values
    f2 = b.facts["t2"]
    register = ch16.register(d)
    pops = ch16.populations(d)
    process = {row[0][:2]: row[2] for row in tests}           # JE -> Journal entries, ...
    by_test = Counter(e["test"] for e in register)
    approvers = Counter(e["emp"] for e in register).most_common()
    names = {r[0]: r[1] for r in d.q("SELECT EmployeeID, EmployeeName FROM Employee")}
    po_after = [e for e in register if e["test"] == "PO AfterTermination"]
    # Steps 11-12: the Monitoring page
    page = b.report.add(Page("monitoring", "Monitoring"))
    page.add(Visual("yearSlicer", "slicer", 20, 20, 160, 170, {"Values": [col("Date", "Year")]}))
    exc = meas(MEASURES, "Exceptions")
    page.add(Visual("heatMap", "pivotTable", 200, 20, 680, 330, {
        "Rows": [col("Tests", "TestID")], "Columns": [col("Date", "MonthName")], "Values": [exc]},
        objects=rules_fill(exc, f"{MEASURES}.Exceptions")))
    page.add(Visual("approvers", "clusteredBarChart", 20, 370, 600, 330, {      # sorted as Desktop sorts a new bar chart
        "Category": [col("Employee", "EmployeeName")], "Y": [exc]}, sort=[(exc, "Descending")]))
    page.add(Visual("rates", "tableEx", 640, 370, 620, 330, {"Values": [
        col("Tests", "TestID"), exc, meas(MEASURES, "Population"), meas(MEASURES, "Rate per 1,000")]}))
    months = Counter(int(e["date"][5:7]) for e in register)
    page.expect = ["TestID", "PR SelfApproved", "Jan", f"{months[1]:,}", names[approvers[0][0]],
                   f"{1000 * by_test['JE Weekend'] / len(pops['JE']):.1f}"]
    # Step 13: the Exception Detail drill-through page, as left after drilling through on PO AfterTermination
    page = b.report.add(Page("exceptionDetail", "Exception Detail"))
    drillthrough(page, col("Tests", "TestID"), "PO AfterTermination")
    page.add(Visual("documents", "tableEx", 20, 80, 1000, 400, {"Values": [
        col("Exceptions", "DocumentNumber"), col("Exceptions", "EventDate"), agg("Exceptions", "Amount"),
        col("Employee", "EmployeeName"), col("Employee", "JobTitle")]}))
    page.expect = ["DocumentNumber", "JobTitle"] + [e["doc"] for e in po_after] + [names[po_after[0]["emp"]]]
    b.add_tests("_tutorial-02.qmd")

    # checks
    for y, n in zip(d.years, f2["po"]["years"]):
        b.check(t, f"{y} purchase orders (by OrderDate)", n, f"CALCULATE ( COUNTROWS ( PurchaseOrder ), 'Date'[Year] = {y} )", 0)
    b.check(t, "PurchaseOrder rows", f2["po"]["n"], "COUNTROWS ( PurchaseOrder )", 0)
    for y, n in zip(d.years, f2["pr"]["years"]):
        b.check(t, f"{y} payroll registers (by PayDate)", n,
                f"CALCULATE ( COUNTROWS ( PayrollRegister ), 'Date'[Year] = {y} )", 0)
    b.check(t, "PayrollRegister rows", f2["pr"]["n"], "COUNTROWS ( PayrollRegister )", 0)
    b.check(t, "registers with no payment", len(f2["unpaid"]),
            "COUNTROWS ( FILTER ( PayrollRegister, ISBLANK ( PayrollRegister[PaymentDate] ) ) )", 0)
    for name in PO_FLAGS:
        b.check(t, f"PO {name} flags", by_test[f"PO {name}"], f"SUM ( PurchaseOrder[{name}] )", 0)
    for name in PR_FLAGS:
        b.check(t, f"PR {name} flags", by_test[f"PR {name}"], f"SUM ( PayrollRegister[{name}] )", 0)
    b.check(t, "Exceptions rows", len(register), "COUNTROWS ( Exceptions )", 0)
    b.check(t, "test and document pairs (each unique)", len({(e["test"], e["doc"]) for e in register}),
            "COUNTROWS ( SUMMARIZE ( Exceptions, Exceptions[TestID], Exceptions[DocumentNumber] ) )", 0)
    for rel, dax in (("a test", "RELATED ( Tests[Process] )"), ("a date", "RELATED ( 'Date'[Year] )"),
                     ("an employee", "RELATED ( Employee[EmployeeName] )"), ("an event date", "Exceptions[EventDate]"),
                     ("a document number", "Exceptions[DocumentNumber]")):
        b.check(t, f"exceptions without {rel}", 0, f"COUNTROWS ( FILTER ( Exceptions, ISBLANK ( {dax} ) ) )", 0)
    b.check(t, "Tests rows", len(ch16.TESTS), "COUNTROWS ( Tests )", 0)
    for p in ch16.PROCESSES:
        f = f'Tests[Process] = "{process[p]}"'
        b.check(t, f"{p} exceptions", sum(1 for e in register if e["process"] == p), f"CALCULATE ( [Exceptions], {f} )", 0)
        b.check(t, f"{p} population", len(pops[p]), f"CALCULATE ( [Population], {f} )", 0)
    b.check(t, "Population blank with no single process (1 = blank)", 1, "IF ( ISBLANK ( [Population] ), 1, 0 )", 0)
    for test in ch16.TESTS:
        f = f'Tests[TestID] = "{test}"'
        b.check(t, f"Test 2: {test} exceptions", by_test[test], f"CALCULATE ( [Exceptions], {f} )", 0)
        b.check(t, f"Test 2: {test} rate per 1,000", round(1000 * by_test[test] / len(pops[test[:2]]), 4),
                f"CALCULATE ( [Rate per 1,000], {f} )", 0.0001)
    for test in ("PO AfterTermination", "PR PaidBeforeApproval", "PR AfterTermination"):
        b.check(t, f"{test} documents", ", ".join(sorted(e["doc"] for e in register if e["test"] == test)),
                docs_of(f'Tests[TestID] = "{test}"'))
    b.check(t, "PO exceptions: distinct orders", f2["po_docs"],
            f'CALCULATE ( DISTINCTCOUNT ( Exceptions[DocumentNumber] ), Tests[Process] = "{process["PO"]}" )', 0)
    january = Counter(e["test"] for e in register if e["date"][5:7] == "01")
    for test in ch16.TESTS:
        b.check(t, f"January {test}", january[test],
                f"CALCULATE ( [Exceptions], 'Date'[MonthNumber] = 1, Tests[TestID] = \"{test}\" )", 0)
    for k in range(1, 13):
        b.check(t, f"{ch16.MONTHS[k - 1][:3]} exceptions (all years)", months[k],
                f"CALCULATE ( [Exceptions], 'Date'[MonthNumber] = {k} )", 0)
    b.check(t, "December JE AboveLimit (the year-end closes)", f2["december"],
            "CALCULATE ( [Exceptions], 'Date'[MonthNumber] = 12, Tests[TestID] = \"JE AboveLimit\" )", 0)
    b.check(t, "January PO AfterTermination (the drill-through of Step 13)",
            sum(1 for e in po_after if e["date"][5:7] == "01"),
            "CALCULATE ( [Exceptions], 'Date'[MonthNumber] = 1, Tests[TestID] = \"PO AfterTermination\" )", 0)
    b.check(t, "month names with PR SelfApproved exceptions", 12,
            "COUNTROWS ( FILTER ( VALUES ( 'Date'[MonthNumber] ), "
            "CALCULATE ( [Exceptions], Tests[TestID] = \"PR SelfApproved\" ) > 0 ) )", 0)
    for emp_id, n in approvers[:5]:
        b.check(t, f"exceptions approved by {names[emp_id]}", n, f"CALCULATE ( [Exceptions], Employee[EmployeeID] = {emp_id} )", 0)
    for p in ch16.PROCESSES:
        for y, n in zip(d.years, f2["years"][p]):
            f = f'Tests[Process] = "{process[p]}", \'Date\'[Year] = {y}'
            b.check(t, f"{p} exceptions in {y}", n, f"CALCULATE ( [Exceptions], {f} )", 0)
            pop = sum(1 for x_ in pops[p] if x_[:4] == str(y))
            b.check(t, f"{p} rate per 1,000 in {y}", round(1000 * n / pop, 4), f"CALCULATE ( [Rate per 1,000], {f} )",
                    0.0001)


def t16_3(b: Build) -> None:
    d, m = b.d, b.model
    t = "Tutorial 16.3"
    # Step 1: the Dispositions table (Enter data, the rows of tbl-16-04), hidden in report view
    rows = md_table(CHAPTER / "_tutorial-03.qmd", "tbl-16-04")
    m.add(entered("Dispositions", ["TestID", "DocumentNumber", "Disposition", "Note"], rows, hidden=True))
    m.query_order.append("Dispositions")
    disp = Query("Dispositions")
    disp.columns = {c: "type text" for c in ("TestID", "DocumentNumber", "Disposition", "Note")}
    # Step 2: merged into the register on the test and the document
    reg = b.q["Exceptions"].merge(disp, ["TestID", "DocumentNumber"], ["TestID", "DocumentNumber"],
                                  ["Disposition", "Note"])
    m.tables["Exceptions"] = query_table(reg, formats={"Amount": MONEY}, summarize={"EmployeeID": "none"})
    # Steps 3 and 7: the measures
    m.tables[MEASURES].measures += measures("_tutorial-03.qmd", ["Reviewed Exceptions", "Open Exceptions",
                                                                    "Data Through"],
                                              {"Reviewed Exceptions": COUNT, "Open Exceptions": COUNT,
                                               "Data Through": "Short Date"})

    f3 = b.facts["t3"]
    register = ch16.register(d)
    reviewed = [e for e in register if e["disposition"]]
    open_ = [e for e in register if not e["disposition"]]
    docs = Counter(e["doc"] for e in register)
    multi = {k: n for k, n in docs.items() if n >= 2}
    top = max(multi, key=multi.get)
    through = date.fromisoformat(f3["through"])
    # Steps 4-5: the Review page
    page = b.report.add(Page("review", "Review"))
    page.add(card("reviewed", 20, 20, 280, 140, meas(MEASURES, "Reviewed Exceptions")))
    page.add(card("open", 320, 20, 280, 140, meas(MEASURES, "Open Exceptions")))
    page.add(Visual("openByYear", "pivotTable", 20, 180, 580, 380, {
        "Rows": [col("Tests", "TestID")], "Columns": [col("Date", "Year")],
        "Values": [meas(MEASURES, "Open Exceptions")]}))
    page.add(Visual("multiple", "tableEx", 620, 20, 640, 680, {"Values": [
        col("Exceptions", "DocumentNumber"), meas(MEASURES, "Exceptions"), meas(MEASURES, "Open Exceptions")]},
        filters=[at_least("exceptionsAtLeast2", meas(MEASURES, "Exceptions"), 2)],
        sort=[(meas(MEASURES, "Exceptions"), "Descending")]))
    page.expect = ["Reviewed Exceptions", "Open Exceptions", f"{len(open_):,}", top, sorted(multi)[-1]]
    # Step 7: the Data through card on the Monitoring page
    mon = b.report.page("monitoring")
    mon.add(card("dataThrough", 900, 20, 360, 150, meas(MEASURES, "Data Through"), title="Data through"))
    mon.expect = mon.expect + ["Data through", f"Data Through, {through.month}/{through.day}/{through.year} card"]
    b.add_tests("_tutorial-03.qmd")

    # checks
    kinds = Counter(e["disposition"] for e in reviewed)
    process = {p: next(r[2] for r in md_table(CHAPTER / "chapter.qmd", "tbl-16-01") if r[0].startswith(p))
               for p in ch16.PROCESSES}
    b.check(t, "Dispositions rows", len(rows), "COUNTROWS ( Dispositions )", 0)
    b.check(t, "Test 3: reviewed exceptions (every disposition found its exception)", len(reviewed),
            "[Reviewed Exceptions]", 0)
    b.check(t, "Test 3: open exceptions", len(open_), "[Open Exceptions]", 0)
    for k in ("Expected", "Deficiency", "Follow up"):
        b.check(t, f"{k} dispositions", kinds[k], f'CALCULATE ( [Exceptions], Exceptions[Disposition] = "{k}" )', 0)
    for p in ch16.PROCESSES:
        for y, n in zip(d.years, f3["open_years"][p]):
            b.check(t, f"{p} open exceptions in {y}", n,
                    f"CALCULATE ( [Open Exceptions], Tests[Process] = \"{process[p]}\", 'Date'[Year] = {y} )", 0)
    b.check(t, "documents failing two tests or more", len(multi),
            "COUNTROWS ( FILTER ( VALUES ( Exceptions[DocumentNumber] ), [Exceptions] >= 2 ) )", 0)
    b.check(t, f"{top} exceptions", multi[top], f'CALCULATE ( [Exceptions], Exceptions[DocumentNumber] = "{top}" )', 0)
    b.check(t, "open JE AboveLimit documents", ", ".join(sorted(e["doc"] for e in open_ if e["test"] == "JE AboveLimit")),
            docs_of('Tests[TestID] = "JE AboveLimit"', "ISBLANK ( Exceptions[Disposition] )"))
    b.check(t, "the documents failing two tests or more", ", ".join(sorted(multi)),
            "CONCATENATEX ( FILTER ( VALUES ( Exceptions[DocumentNumber] ), [Exceptions] >= 2 ), "
            "Exceptions[DocumentNumber], \", \", Exceptions[DocumentNumber], ASC )")
    for doc in f3["departed"]:
        b.check(t, f"{doc} open exceptions (one of its two)", f3["departed_open"],
                f'CALCULATE ( [Open Exceptions], Exceptions[DocumentNumber] = "{doc}" )', 0)
    numbers = "SELECTCOLUMNS ( PurchaseOrder, \"Number\", VALUE ( RIGHT ( PurchaseOrder[PONumber], 6 ) ) )"
    b.check(t, "Test 4: orders", f3["orders"], "COUNTROWS ( PurchaseOrder )", 0)
    b.check(t, "Test 4: first number", f3["first"], f"MINX ( {numbers}, [Number] )", 0)
    b.check(t, "Test 4: last number", f3["last_number"], f"MAXX ( {numbers}, [Number] )", 0)
    b.check(t, "Test 4: registers", f3["registers"], "COUNTROWS ( PayrollRegister )", 0)
    b.check(t, "Test 4: registers not paid", len(f3["unpaid"]),
            "COUNTROWS ( FILTER ( PayrollRegister, ISBLANK ( PayrollRegister[PaymentDate] ) ) )", 0)
    b.check(t, "Data Through", f3["through"], 'FORMAT ( [Data Through], "yyyy-mm-dd" )')
    for y, day in zip(d.years, f3["through_years"]):
        b.check(t, f"Data Through with {y} selected", day,
                f"CALCULATE ( FORMAT ( [Data Through], \"yyyy-mm-dd\" ), 'Date'[Year] = {y} )")


TUTORIALS = [("16.1", t16_1), ("16.2", t16_2), ("16.3", t16_3)]
