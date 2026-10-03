"""Chapter 16's instructor notes: the values each note states, and the claims its wording makes.

The chapter's Power BI values are reproduced here with SQL, as the book verified them: the exception register of
Tutorials 16.1 and 16.2 is rebuilt from the flag rules of the tutorials' Power Query steps, and Tutorial 16.3's
dispositions follow the rule of tbl-16-04 (the year-end closes are Expected, the documents of the employee who had
left are Deficiencies, and the payments made before approval are Follow ups).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import date
from functools import lru_cache

from notes import note

T1 = "chapters/16-audit-monitoring/_tutorial-01.qmd"
T2 = "chapters/16-audit-monitoring/_tutorial-02.qmd"
T3 = "chapters/16-audit-monitoring/_tutorial-03.qmd"
EXERCISES = "chapters/16-audit-monitoring/_exercises.qmd"
MCQ = "chapters/16-audit-monitoring/_multiple-choice.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
# The tests of tbl-16-01, in the table's order, and the process each runs on.
TESTS = ["JE Weekend", "JE Backdated", "JE SelfApproved", "JE AboveLimit", "JE RoundAmount",
         "PO SelfApproved", "PO AboveLimit", "PO AfterTermination",
         "PR PaidBeforeApproval", "PR AfterTermination", "PR SelfApproved"]
PROCESSES = ["JE", "PO", "PR"]
# Exercise 16.1's buckets (Chapter 8's): the first day past due of each bucket.
BUCKETS = [(-10**9, "Current"), (1, "1-30"), (31, "31-60"), (61, "61-90"), (91, "over 90")]
# Nigrini's first-digit MAD ranges (Chapter 8): close, acceptable, marginally acceptable, nonconformity.
MAD_RANGES = [0.006, 0.012, 0.015]
SHORT_TITLES = {"Chief Financial Officer": "CFO"}


def word(n: int) -> str:
    return WORDS[n] if n < len(WORDS) else f"{n:,}"


def asof(d) -> str:
    return f"{d.C}-12-31"


def month_year(day: str) -> str:
    return f"{MONTHS[int(day[5:7]) - 1]} {day[:4]}"


def runs(numbers: list[str], pairs: bool = True) -> list[str]:
    """Document numbers grouped by year as the notes list them: three or more consecutive numbers as "first to last",
    two as "first and last" (if `pairs`), the later numbers shortened to their sequence; anything else in full."""
    by_prefix = defaultdict(list)
    for n in sorted(numbers):
        prefix, seq = n.rsplit("-", 1)
        by_prefix[prefix].append(seq)
    out = []
    for prefix, seqs in by_prefix.items():
        ints = [int(s) for s in seqs]
        consecutive = ints == list(range(ints[0], ints[0] + len(ints)))
        if len(seqs) >= 3 and consecutive:
            out.append(f"{prefix}-{seqs[0]} to {seqs[-1]}")
        elif len(seqs) == 2 and pairs:
            out.append(f"{prefix}-{seqs[0]} and {seqs[1]}")
        else:
            out += [f"{prefix}-{s}" for s in seqs]
    return out


# --- the exception register (Tutorials 16.1 and 16.2) ---------------------------------------------

@lru_cache(maxsize=None)
def entries(d) -> tuple[dict, ...]:
    """Tutorial 16.1's JournalEntry query: each entry with its five flags and risk score."""
    out = []
    for jid, number, posted, created, etype, amount, creator, approver, limit, weekday in d.q(
            "SELECT j.JournalEntryID, j.EntryNumber, j.PostingDate, j.CreatedDate, j.EntryType, j.TotalAmount, "
            "j.CreatedByEmployeeID, j.ApprovedByEmployeeID, e.MaxApprovalAmount, CAST(strftime('%w', j.CreatedDate) AS INTEGER) "
            "FROM JournalEntry j LEFT JOIN Employee e ON e.EmployeeID = j.ApprovedByEmployeeID ORDER BY j.JournalEntryID"):
        flags = dict(Weekend=weekday in (0, 6), Backdated=created[:10] > posted, SelfApproved=creator == approver,
                     AboveLimit=limit is not None and amount > limit, RoundAmount=math.fmod(amount, 1000) == 0)
        out.append(dict(id=jid, number=number, date=posted, type=etype, amount=amount, approver=approver, limit=limit,
                        flags=flags, score=sum(flags.values())))
    return tuple(out)


@lru_cache(maxsize=None)
def orders(d) -> tuple[dict, ...]:
    """Tutorial 16.2's PurchaseOrder query with its three flags."""
    out = []
    for number, ordered, total, creator, approver, limit, terminated in d.q(
            "SELECT p.PONumber, p.OrderDate, p.OrderTotal, p.CreatedByEmployeeID, p.ApprovedByEmployeeID, e.MaxApprovalAmount, "
            "e.TerminationDate FROM PurchaseOrder p LEFT JOIN Employee e ON e.EmployeeID = p.ApprovedByEmployeeID "
            "ORDER BY p.PurchaseOrderID"):
        flags = dict(SelfApproved=creator == approver, AboveLimit=limit is not None and total > limit,
                     AfterTermination=terminated is not None and ordered > terminated)
        out.append(dict(number=number, date=ordered, amount=total, creator=creator, approver=approver, limit=limit,
                        flags=flags))
    return tuple(out)


@lru_cache(maxsize=None)
def registers(d) -> tuple[dict, ...]:
    """Tutorial 16.2's PayrollRegister query: each register with its payment, period, payee, and three flags."""
    out = []
    for rid, payee, net, approver, approved, paid, period_end, pay_date, terminated in d.q(
            "SELECT r.PayrollRegisterID, r.EmployeeID, r.NetPay, r.ApprovedByEmployeeID, r.ApprovedDate, p.PaymentDate, "
            "pp.PeriodEndDate, pp.PayDate, e.TerminationDate FROM PayrollRegister r "
            "LEFT JOIN PayrollPayment p ON p.PayrollRegisterID = r.PayrollRegisterID "
            "JOIN PayrollPeriod pp ON pp.PayrollPeriodID = r.PayrollPeriodID JOIN Employee e ON e.EmployeeID = r.EmployeeID "
            "ORDER BY r.PayrollRegisterID"):
        flags = dict(PaidBeforeApproval=paid is not None and paid < approved,
                     AfterTermination=terminated is not None and period_end > terminated, SelfApproved=payee == approver)
        out.append(dict(id=rid, number=f"Register {rid}", date=pay_date, amount=net, payee=payee, approver=approver,
                        approved=approved, paid=paid, flags=flags))
    return tuple(out)


@lru_cache(maxsize=None)
def register(d) -> tuple[dict, ...]:
    """The appended Exceptions query: one row per failed test, with the register's columns, and the disposition of
    Tutorial 16.3 merged on the test and the document."""
    out = []
    for prefix, docs in (("JE", entries(d)), ("PO", orders(d)), ("PR", registers(d))):
        for doc in docs:
            for name, failed in doc["flags"].items():
                if failed:
                    out.append(dict(test=f"{prefix} {name}", process=prefix, name=name, doc=doc["number"],
                                    date=doc["date"], amount=doc["amount"], emp=doc["approver"]))
    for e in out:
        e["disposition"] = disposition(d, e)
    return tuple(out)


def disposition(d, e: dict) -> str | None:
    """The rule of tbl-16-04: the year-end closes above every limit are expected, the documents of the employee who
    had left are deficiencies, and the payments made before approval need a question for payroll."""
    if e["test"] == "JE AboveLimit" and e["doc"] in d.closes:
        return "Expected"
    if e["test"] in ("PO AfterTermination", "PR AfterTermination"):
        return "Deficiency"
    if e["test"] == "PR PaidBeforeApproval":
        return "Follow up"
    return None


def populations(d) -> dict[str, list[str]]:
    """Each process's documents by the date the register relates to the Date table."""
    return dict(JE=[e["date"] for e in entries(d)], PO=[o["date"] for o in orders(d)], PR=[r["date"] for r in registers(d)])


def per_year(d, dates: list[str]) -> list[int]:
    counts = Counter(int(x[:4]) for x in dates)
    return [counts[y] for y in d.years]


def employees(d) -> dict[int, dict]:
    return {r[0]: dict(id=r[0], name=r[1], title=r[2], limit=r[3], terminated=r[4]) for r in d.q(
        "SELECT EmployeeID, EmployeeName, JobTitle, MaxApprovalAmount, TerminationDate FROM Employee")}


def by_process(items: list[tuple[str, object]]) -> list[tuple[str, list[tuple[str, object]]]]:
    """(TestID, value) pairs grouped as the notes write them: "JE Weekend 17, Backdated 6; PO ..."."""
    out = []
    for p in PROCESSES:
        group = [(t.split(" ", 1)[1], v) for t, v in items if t.startswith(p + " ")]
        if group:
            out.append((p, group))
    return out


# --- Tutorial 16.1 --------------------------------------------------------------------------------

@note("ch16.t1", T1)
def t1(d, claim):
    je = entries(d)
    flags = [(name, sum(e["flags"][name] for e in je)) for name in je[0]["flags"]]
    top_score = max(e["score"] for e in je)
    scores = [dict(score=s, n=sum(1 for e in je if e["score"] == s), amount=sum(e["amount"] for e in je if e["score"] == s))
              for s in range(top_score + 1)]
    top = [e for e in je if e["score"] == top_score]
    claim(len(top) == 1, "one entry has the highest score")
    top = top[0]
    lines = d.q("SELECT SourceDocumentID, COUNT(*), SUM(Debit), SUM(Credit) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry' "
                "GROUP BY SourceDocumentID")
    by_entry = {r[0]: r[1:] for r in lines}
    n_lines, debits, credits = sum(r[1] for r in lines), sum(r[2] for r in lines), sum(r[3] for r in lines)
    top_lines = by_entry[top["id"]]
    claim(abs(top_lines[1] - top_lines[2]) < 0.005, f"{top['number']}'s debits equal its credits")
    total = sum(e["amount"] for e in je)
    claim(abs(total - debits) < 0.005 and abs(total - credits) < 0.005, "the entries' total equals the line debits and credits")
    claim(all(e["limit"] is not None for e in je), "no approver has a null MaxApprovalAmount")
    return dict(n=len(je), flags=flags, exceptions=sum(k for _, k in flags), scores=scores,
                top=dict(number=top["number"], type=top["type"], lines=top_lines[0], debits=top_lines[1]),
                two=[dict(number=e["number"], type=e["type"]) for e in je if e["score"] == 2],
                lines=n_lines, total=total, debits=debits, credits=credits)


# --- Tutorial 16.2 --------------------------------------------------------------------------------

@note("ch16.t2", T2)
def t2(d, claim):
    ex = register(d)
    emp = employees(d)
    pops = populations(d)
    regs = registers(d)
    payments = d.one("SELECT COUNT(*) FROM PayrollPayment")
    unpaid = [r["id"] for r in regs if r["paid"] is None]
    count = Counter(e["test"] for e in ex)
    process_n = Counter(e["process"] for e in ex)
    tests = {p: [(t.split(" ", 1)[1], count[t]) for t in TESTS if t.startswith(p + " ")] for p in PROCESSES}
    rates = [(t, 1000 * count[t] / len(pops[t[:2]])) for t in TESTS]
    # payroll exceptions
    pba = [r for r in regs if r["flags"]["PaidBeforeApproval"]]
    cfo = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Chief Financial Officer'")
    claim(all(r["payee"] == cfo for r in pba), "the registers paid before approval pay the CFO")
    claim(all((date.fromisoformat(r["approved"]) - date.fromisoformat(r["paid"])).days == 1 for r in pba),
          "each was paid one day before approval")
    after = [r for r in regs if r["flags"]["AfterTermination"]]
    claim(len({r["payee"] for r in after}) == 1, "the registers after termination pay one employee")
    selfs = [r for r in regs if r["flags"]["SelfApproved"]]
    claim(len({r["approver"] for r in selfs}) == 1, "one employee approved all the self-approved registers")
    self_approver = selfs[0]["approver"]
    claim(emp[self_approver]["title"] == "Accounting Manager", "the self-approving employee is the Accounting Manager")
    # months
    months = Counter(int(e["date"][5:7]) for e in ex)
    january = sorted((t, n) for t, n in Counter(e["test"] for e in ex if e["date"][5:7] == "01").items())
    december = [e["doc"] for e in ex if e["test"] == "JE AboveLimit" and e["date"][5:7] == "12"]
    claim(sorted(december) == sorted(d.closes), "December's JE AboveLimit exceptions are the year-end closes")
    self_months = Counter(int(e["date"][5:7]) for e in ex if e["test"] == "PR SelfApproved")
    claim(len(self_months) == 12, "PR SelfApproved has exceptions in every month")
    # approvers: the five with the most exceptions by name, the rest by job title (ties by EmployeeID, descending,
    # the order of the reference model's visual)
    ranked = sorted(Counter(e["emp"] for e in ex).items(), key=lambda kv: (-kv[1], -kv[0]))
    claim(len(ranked) > 5 and ranked[4][1] > ranked[5][1], "the five approvers named have more exceptions than the rest")
    named = []
    for k, n in ranked[:5]:
        e = emp[k]
        extra = f", terminated {e['terminated']}" if e["terminated"] else ""
        named.append(f"{e['name']} ({SHORT_TITLES.get(e['title'], e['title'])}{extra}) {n}")
    groups: dict[str, list[int]] = {}
    for k, n in ranked[5:]:
        groups.setdefault(emp[k]["title"], []).append(n)
    named += [f"{t}{'s' if len(ns) > 1 else ''} {' and '.join(str(n) for n in ns)}" for t, ns in groups.items()]
    # PO AfterTermination
    po_after = [o for o in orders(d) if o["flags"]["AfterTermination"]]
    claim(len({o["approver"] for o in po_after}) == 1, "one employee approved the orders after termination")
    claim(all(o["flags"]["AboveLimit"] for o in po_after), "the orders after termination are also above the limit")
    years = {p: per_year(d, [e["date"] for e in ex if e["process"] == p]) for p in PROCESSES}
    return dict(po=dict(n=len(pops["PO"]), years=per_year(d, pops["PO"])),
                pr=dict(n=len(pops["PR"]), years=per_year(d, pops["PR"])), payments=payments, unpaid=unpaid,
                n=len(ex), process_n=process_n, tests=tests,
                po_docs=len({e["doc"] for e in ex if e["process"] == "PO"}),
                pba=dict(ids=[r["id"] for r in pba], paid=[r["paid"] for r in pba]),
                after=dict(ids=[r["id"] for r in after], payee=after[0]["payee"]),
                selfs=dict(n=len(selfs), approver=self_approver),
                rates=by_process(rates), months=[(MONTHS[m - 1][:3], months[m]) for m in range(1, 13) if months[m]],
                january=by_process(january), december=len(december), n_closes=word(len(d.closes)),
                self_low=min(self_months.values()), self_high=max(self_months.values()), approvers=named,
                po_after=[dict(number=o["number"], when=month_year(o["date"])) for o in po_after],
                po_after_by=po_after[0]["approver"], po_after_limit=emp[po_after[0]["approver"]]["limit"],
                years=years, je_rates=[1000 * n / p for n, p in zip(years["JE"], per_year(d, pops["JE"]))])


# --- Tutorial 16.3 --------------------------------------------------------------------------------

@note("ch16.t3", T3)
def t3(d, claim):
    ex = register(d)
    emp = employees(d)
    reviewed = [e for e in ex if e["disposition"]]
    open_ = [e for e in ex if not e["disposition"]]
    keys = Counter((e["test"], e["doc"]) for e in ex)
    claim(max(keys.values()) == 1, "each test and document number is unique in the register")
    by_test = []
    for t in sorted({e["test"] for e in reviewed}):
        rows = [e for e in ex if e["test"] == t]
        by_test.append(dict(test=t, reviewed=sum(1 for e in rows if e["disposition"]), total=len(rows),
                            open=[e["doc"] for e in rows if not e["disposition"]]))
    kinds = Counter(e["disposition"] for e in reviewed)
    claim(set(kinds) == {"Expected", "Deficiency", "Follow up"}, "the dispositions are Expected, Deficiency, and Follow up")
    open_years = {p: per_year(d, [e["date"] for e in open_ if e["process"] == p]) for p in PROCESSES}
    pr_self = per_year(d, [e["date"] for e in ex if e["test"] == "PR SelfApproved"])
    claim(open_years["PR"] == pr_self, "the open payroll exceptions are the PR SelfApproved ones (the rest of PR reviewed)")
    # documents that fail two tests or more
    docs = Counter(e["doc"] for e in ex)
    multi = {k: n for k, n in docs.items() if n >= 2}
    claim(not any(k.startswith("Register ") for k in multi), "no payroll register fails two tests")
    je_multi = sorted(k for k in multi if k.startswith("JE-"))
    je_top = max(je_multi, key=lambda k: multi[k])
    claim(sum(1 for k in je_multi if multi[k] == multi[je_top]) == 1 and all(multi[k] == 2 for k in je_multi if k != je_top),
          "one journal entry fails the most tests, and the others fail two each")
    po = {o["number"]: o for o in orders(d)}
    po_multi = sorted(k for k in multi if k.startswith("PO-"))
    claim(all(multi[k] == 2 for k in po_multi), "each order in the list fails two tests")
    small = [k for k in po_multi if po[k]["flags"]["SelfApproved"] and po[k]["limit"] == 0]
    departed = [k for k in po_multi if po[k]["flags"]["AfterTermination"]]
    capital = [k for k in po_multi if po[k]["flags"]["SelfApproved"] and po[k]["limit"] > 0]
    claim(sorted(small + departed + capital) == po_multi, "the orders fall into the three groups the note lists")
    claim(all(po[k]["flags"]["AboveLimit"] for k in small), "the small self-approved orders are also above the limit")
    claim({emp[po[k]["approver"]]["title"] for k in small} == {"Buyer", "Procurement Analyst"},
          "the small orders were self-approved by buyers and procurement analysts")
    claim(len({po[k]["approver"] for k in departed}) == 1 and all(po[k]["flags"]["AboveLimit"] and po[k]["limit"] == 0
                                                                   for k in departed),
          "one employee approved the departed orders, after termination and above a limit of 0")
    departed_open = {sum(1 for e in open_ if e["doc"] == k) for k in departed}
    claim(len(departed_open) == 1, "the departed employee's orders have the same number of open exceptions")
    claim(len({po[k]["approver"] for k in capital}) == 1 and all(po[k]["creator"] == po[k]["approver"] for k in capital),
          "one employee created and approved the capital orders")
    capital_by = emp[po[capital[0]]["approver"]]
    claim(capital_by["title"] == "Purchasing Manager", "the capital orders' approver is the Purchasing Manager")
    claim(all(po[k]["amount"] % 1000 == 0 for k in capital), "the capital orders are in whole thousands")
    # Test 4
    numbers = [int(o["number"][-6:]) for o in orders(d)]
    claim(len(set(numbers)) == len(numbers) == max(numbers) - min(numbers) + 1, "no purchase order number is missing")
    claim(len({o["number"][3:7] for o in orders(d)}) > 1 and min(numbers) == 1, "PO numbers continue across years")
    regs = registers(d)
    unpaid = [r for r in regs if r["paid"] is None]
    orphans = {r[0] for r in d.q("SELECT DISTINCT SourceDocumentID FROM GLEntry WHERE SourceDocumentType = 'PayrollPayment' "
                                 "AND SourceDocumentID NOT IN (SELECT PayrollPaymentID FROM PayrollPayment)")}
    claim(d.one("SELECT COUNT(*) FROM PayrollPayment WHERE PayrollPaymentID <> PayrollRegisterID") == 0
          and orphans == {r["id"] for r in unpaid}, "the unpaid registers' PayrollPayment GL rows are the trace orphans")
    flagged = {e["doc"] for e in ex if e["process"] == "PR"}
    ceo = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Chief Executive Officer'")
    not_flagged = [r for r in unpaid if r["number"] not in flagged]
    claim(len(not_flagged) == 1 and not_flagged[0]["payee"] == ceo
          and not_flagged[0]["id"] == min(r["id"] for r in regs if r["payee"] == ceo),
          "the one unpaid register that is not an exception is the CEO's first register")
    # Data Through
    last = dict(JE=max(e["date"] for e in entries(d)), PO=max(o["date"] for o in orders(d)), PR=max(r["date"] for r in regs))
    through_years = [min(max((x for x in xs if x[:4] == str(y)), default="9999") for xs in populations(d).values())
                     for y in d.years]
    # The package's Tests 1, 3, and 5 (Chapters 14-15)
    test1 = d.q("SELECT CAST(substr(si.InvoiceDate, 1, 4) AS INTEGER), COUNT(*), SUM(l.LineTotal) FROM SalesInvoiceLine l "
                "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID GROUP BY 1 ORDER BY 1")
    claim([r[0] for r in test1] == d.years, "the invoice lines cover the fiscal years of the window")
    closes = d.closes_of(d.C)
    tb = [r[0] for r in d.q("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE PostingDate <= ? AND VoucherNumber "
                            "NOT IN (%s) GROUP BY AccountID" % ",".join("?" * len(closes)), asof(d), *closes)]
    tb_debit, tb_credit = sum(b for b in tb if b > 0), -sum(b for b in tb if b < 0)
    claim(abs(tb_debit - tb_credit) < 0.005, "the pre-closing trial balance balances")
    cut = d.one("SELECT MAX(WorkDate) FROM LaborTimeEntry")
    hours = dict(d.q("SELECT CAST(substr(WorkDate, 1, 4) AS INTEGER), SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry "
                     "WHERE LaborType <> 'NonManufacturing' GROUP BY 1"))
    standard = dict(d.q("SELECT CAST(substr(pc.CompletionDate, 1, 4) AS INTEGER), SUM(pcl.QuantityCompleted * "
                        "i.StandardLaborHoursPerUnit) FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc "
                        "ON pc.ProductionCompletionID = pcl.ProductionCompletionID JOIN Item i ON i.ItemID = pcl.ItemID "
                        "WHERE pc.CompletionDate <= ? GROUP BY 1", cut))
    return dict(n=len(ex), n_disp=len(reviewed), reviewed=len(reviewed), open=len(open_), by_test=by_test,
                kinds=[(k, kinds[k]) for k in ("Expected", "Deficiency", "Follow up")], open_years=open_years,
                pr_self=pr_self, pr_self_n=sum(pr_self), n_multi=len(multi), je_top=je_top, je_top_n=multi[je_top],
                je_rest=[k for k in je_multi if k != je_top], small=runs(small),
                departed=departed, departed_by=po[departed[0]]["approver"], departed_open=departed_open.pop(),
                capital=capital, capital_amounts=[po[k]["amount"] for k in capital], capital_by=capital_by["id"],
                capital_limit=capital_by["limit"], orders=len(numbers), first=min(numbers), last_number=max(numbers),
                registers=len(regs), unpaid=[r["id"] for r in unpaid], ceo_register=not_flagged[0]["id"] if not_flagged else None, last=last,
                through=min(last.values()),
                through_years=through_years, test1=[(n, rev) for _, n, rev in test1], tb_accounts=len(tb), tb=tb_debit,
                test5=[hours[y] / standard[y] for y in d.years])


# --- Exercise 16.1 --------------------------------------------------------------------------------

@note("ch16.ex1", EXERCISES)
def ex1(d, claim):
    end = asof(d)
    rows = d.q("WITH Applied AS (SELECT SalesInvoiceID, SUM(AppliedAmount) AS Applied FROM CashReceiptApplication "
               "WHERE ApplicationDate <= ?1 GROUP BY SalesInvoiceID), "
               "Credited AS (SELECT OriginalSalesInvoiceID AS SalesInvoiceID, SUM(GrandTotal) AS Credited FROM CreditMemo "
               "WHERE CreditMemoDate <= ?1 GROUP BY OriginalSalesInvoiceID) "
               "SELECT si.SalesInvoiceID, si.CustomerID, ROUND(si.GrandTotal - COALESCE(a.Applied, 0) - COALESCE(c.Credited, 0), 2), "
               "julianday(?1) - julianday(si.DueDate), COALESCE(a.Applied, 0) FROM SalesInvoice si "
               "LEFT JOIN Applied a ON a.SalesInvoiceID = si.SalesInvoiceID LEFT JOIN Credited c ON c.SalesInvoiceID = si.SalesInvoiceID "
               "WHERE si.InvoiceDate <= ?1", end)
    positive = [r for r in rows if r[2] > 0]
    buckets = [dict(name=name, balances=[]) for _, name in BUCKETS]
    for r in positive:
        buckets[[i for i, (low, _) in enumerate(BUCKETS) if r[3] >= low][-1]]["balances"].append(r[2])
    oldest = buckets[-1]["balances"]
    claim(sum(1 for b in oldest if b < 1) > len(oldest) / 2, "most balances over 90 days past due are cent residuals")
    total = sum(r[2] for r in positive)
    entry = d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Opening' ORDER BY PostingDate LIMIT 1")
    opening = d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?",
                    d.account("1020"), entry)
    ledger = d.balance(["1020"], end)
    claim(abs(ledger - total - opening) < 0.005, "the difference is the receivables line of the opening entry")
    claim(d.one("SELECT COUNT(*) FROM CashReceiptApplication a LEFT JOIN SalesInvoice si ON si.SalesInvoiceID = "
                "a.SalesInvoiceID WHERE si.SalesInvoiceID IS NULL") == 0,
          "every cash application is to an invoice, so no invoice supports the opening balance")
    negative = [r for r in rows if r[2] < 0]
    ids = ",".join(str(r[0]) for r in negative)
    to_2060 = d.one(f"SELECT COUNT(DISTINCT cm.OriginalSalesInvoiceID) FROM CreditMemo cm JOIN GLEntry g "
                    f"ON g.SourceDocumentType = 'CreditMemo' AND g.SourceDocumentID = cm.CreditMemoID "
                    f"WHERE g.AccountID = ? AND g.Credit > 0 AND cm.OriginalSalesInvoiceID IN ({ids})", d.account("2060"))
    claim(to_2060 == len(negative), "every invoice with a negative balance has a credit memo credited to 2060")
    claim(all(r[4] > 0 for r in negative), "every invoice with a negative balance has been paid")
    refunded = d.one(f"SELECT COUNT(DISTINCT cm.OriginalSalesInvoiceID) FROM CreditMemo cm JOIN CustomerRefund r "
                     f"ON r.CreditMemoID = cm.CreditMemoID WHERE cm.OriginalSalesInvoiceID IN ({ids})")
    claim(refunded >= 0.95 * len(negative), "the credits on those invoices are (almost all) refunded")
    return dict(asof=end, n=len(positive), total=total, customers=len({r[1] for r in positive}),
                b=[dict(name=b["name"], amount=sum(b["balances"])) for b in buckets], ledger=ledger,
                difference=ledger - total, entry=entry, n_negative=len(negative), negative=sum(r[2] for r in negative))


# --- Exercise 16.2 --------------------------------------------------------------------------------

@note("ch16.ex2", EXERCISES)
def ex2(d, claim):
    rows = d.q("SELECT si.InvoiceNumber, si.InvoiceDate, MIN(s.DeliveryDate), MAX(s.DeliveryDate), MIN(s.ShipmentDate), si.SubTotal, "
               "(SELECT MIN(g.PostingDate) FROM GLEntry g WHERE g.SourceDocumentType = 'SalesInvoice' "
               "AND g.SourceDocumentID = si.SalesInvoiceID) FROM SalesInvoice si "
               "JOIN SalesInvoiceLine l ON l.SalesInvoiceID = si.SalesInvoiceID JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID "
               "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID GROUP BY si.SalesInvoiceID ORDER BY si.InvoiceNumber")
    invoices = [dict(number=r[0], date=r[1], first=r[2], last=r[3], shipped=r[4], sub=r[5], posted=r[6]) for r in rows]
    prior = [i for i in invoices if i["last"][:4] < i["date"][:4]]
    claim(all(i["date"][5:7] == "01" and i["last"][5:7] == "12" and int(i["last"][:4]) == int(i["date"][:4]) - 1 for i in prior),
          "every invoice delivered in the prior year is dated in January for a December delivery")
    years = sorted({int(i["date"][:4]) for i in prior})
    claim(years == [d.P, d.C], "the invoices for prior-year deliveries are dated in the prior and current years")
    groups = [dict(year=y, n=sum(1 for i in prior if int(i["date"][:4]) == y)) for y in years]
    late = [i for i in invoices if i["posted"][:4] > i["last"][:4]]
    posted_groups = [sum(1 for i in late if int(i["posted"][:4]) == y) for y in years]
    odd = [i for i in late if i not in prior]
    claim(len(odd) == 1 and {i["number"] for i in prior} <= {i["number"] for i in late},
          "by posting date, exactly one more invoice is late")
    odd = odd[0]
    claim(odd["date"][:4] == odd["shipped"][:4] < odd["posted"][:4],
          "the extra invoice is dated and shipped in the year before it was posted (a revenue cutoff error)")
    unbilled = d.q("SELECT s.DeliveryDate, sl.ExtendedStandardCost FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
                   "LEFT JOIN SalesInvoiceLine l ON l.ShipmentLineID = sl.ShipmentLineID WHERE l.SalesInvoiceLineID IS NULL")
    claim(all(r[0][:7] == f"{d.C}-12" for r in unbilled), f"the shipment lines never invoiced are all December {d.C} deliveries")
    before = [i["number"] for i in invoices if i["date"][:4] < i["first"][:4]]
    return dict(n_prior=len(prior), g=groups, sub=sum(i["sub"] for i in prior), posted=posted_groups,
                odd=dict(number=odd["number"], dated=month_year(odd["date"]), posted=odd["posted"], shipped=odd["shipped"],
                         joins=month_year(odd["posted"])),
                unbilled=len(unbilled), cost=sum(r[1] for r in unbilled),
                n_before=word(len(before)).capitalize(), before=runs(before, pairs=False))


# --- Exercise 16.3 --------------------------------------------------------------------------------

@note("ch16.ex3", EXERCISES)
def ex3(d, claim):
    days = d.q("SELECT tc.WorkDate, COUNT(*), COUNT(DISTINCT tc.RegularHours + tc.OvertimeHours), MIN(tc.RegularHours), "
               "MIN(tc.OvertimeHours), MAX(tc.RegularHours), MAX(tc.OvertimeHours) "
               "FROM TimeClockEntry tc JOIN Employee e ON e.EmployeeID = tc.EmployeeID "
               "JOIN CostCenter c ON c.CostCenterID = e.CostCenterID WHERE c.CostCenterName = 'Manufacturing' "
               "GROUP BY tc.WorkDate ORDER BY tc.WorkDate")
    surge = [r for r in days if r[1] > 1 and r[2] == 1]
    per_month = Counter(r[0][:7] for r in surge)
    several = next(m for m in sorted(per_month) if per_month[m] > 1)
    cut = d.one("SELECT MAX(WorkDate) FROM TimeClockEntry")
    span = (int(cut[:4]) - int(several[:4])) * 12 + int(cut[5:7]) - int(several[5:7]) + 1
    claim(sum(n for m, n in per_month.items() if m >= several) / span >= 2,
          "from that month on, surge days average at least two a month (several a month)")
    peak = max(per_month.values())
    peaks = [m for m, n in per_month.items() if n == peak]
    claim(len(peaks) == 1, "one month has the most surge days")
    hourly = {r[0]: d.one("SELECT COUNT(*) FROM Employee e JOIN CostCenter c ON c.CostCenterID = e.CostCenterID "
                          "WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Hourly' AND e.HireDate <= ?1 "
                          "AND (e.TerminationDate IS NULL OR e.TerminationDate >= ?1)", r[0]) for r in surge}
    claim(all(r[1] == hourly[r[0]] for r in surge) and len({r[1] for r in surge}) == 1,
          "every surge day has all the hourly manufacturing employees, the same number on every day")
    claim(len({r[3:7] for r in surge}) == 1 and surge[0][3:5] == surge[0][5:7],
          "every entry of every surge day has the same regular and overtime hours")
    marks = ",".join(f"'{r[0]}'" for r in surge)
    overtime = {(int(y), s): h for y, s, h in d.q(
        f"SELECT substr(tc.WorkDate, 1, 4), tc.WorkDate IN ({marks}), SUM(tc.OvertimeHours) FROM TimeClockEntry tc "
        f"JOIN Employee e ON e.EmployeeID = tc.EmployeeID JOIN CostCenter c ON c.CostCenterID = e.CostCenterID "
        f"WHERE c.CostCenterName = 'Manufacturing' GROUP BY 1, 2")}
    on_surge = [overtime.get((y, 1), 0.0) for y in d.years]
    other = [overtime.get((y, 0), 0.0) for y in d.years]
    claim(max(other) / min(other) < 1.1, "overtime on other days is flat")
    manager = d.one("SELECT EmployeeID FROM Employee WHERE JobTitle = 'Production Manager'")
    approvals = d.q(f"SELECT oa.ApprovedByEmployeeID, oa.ApprovedDate, tc.WorkDate FROM TimeClockEntry tc "
                    f"JOIN Employee e ON e.EmployeeID = tc.EmployeeID JOIN CostCenter c ON c.CostCenterID = e.CostCenterID "
                    f"LEFT JOIN OvertimeApproval oa ON oa.OvertimeApprovalID = tc.OvertimeApprovalID "
                    f"WHERE c.CostCenterName = 'Manufacturing' AND tc.WorkDate IN ({marks})")
    claim(all(r[0] == manager and r[1] == r[2] for r in approvals),
          "every surge entry was approved by the Production Manager on the work date")
    by_year = Counter(int(r[0][:4]) for r in surge)
    return dict(by_year=[(y, by_year[y]) for y in d.years], total=len(surge), first=surge[0][0],
                several=month_year(several + "-01"), peak=peak, peak_month=month_year(peaks[0] + "-01"),
                employees=surge[0][1], regular=surge[0][3], overtime=surge[0][4], on_surge=on_surge,
                shares=[s / (s + o) for s, o in zip(on_surge, other)], other=other, entries=len(approvals))


# --- Exercise 16.4 --------------------------------------------------------------------------------

@note("ch16.ex4", EXERCISES)
def ex4(d, claim):
    ex = register(d)
    pops = {p: per_year(d, dates) for p, dates in populations(d).items()}
    counts = {p: per_year(d, [e["date"] for e in ex if e["process"] == p]) for p in PROCESSES}
    rates = {p: [1000 * n / pop for n, pop in zip(counts[p], pops[p])] for p in PROCESSES}
    unexplained_n = {p: per_year(d, [e["date"] for e in ex if e["process"] == p and e["disposition"] != "Expected"
                                      and e["test"] != "PR SelfApproved"]) for p in PROCESSES}
    unexplained = {p: [1000 * n / pop for n, pop in zip(unexplained_n[p], pops[p])] for p in PROCESSES}
    claim(all(len(d.closes_of(y)) == 2 for y in d.years)
          and all(sum(1 for e in ex if e["disposition"] == "Expected" and e["date"][:4] == str(y)) == 2 for y in d.years),
          "the expected exceptions are the two closes of each year")
    claim(unexplained_n["PO"] == counts["PO"], "the purchase orders' unexplained rate is unchanged")
    po_n, po_r, po_pop = counts["PO"], rates["PO"], pops["PO"]
    claim(abs(po_n[2] / po_n[1] - 4 / 3) < 0.05, f"the order exceptions rose by a third from {d.P} to {d.C}")
    claim(abs(po_r[2] / po_r[1] - 1) < 0.1, "the order rate barely moved")
    claim(abs((1 - po_r[2] / po_r[0]) - 2 / 3) < 0.05, f"from {d.F} the order rate fell by two-thirds")
    claim(po_pop[2] / po_pop[0] > 2, f"orders more than doubled from {d.F}")
    je = unexplained["JE"]
    claim(je[1] < je[0] and je[2] > je[1], f"the journal entries' unexplained rate fell in {d.P} and rose in {d.C}")
    # the documents that fail several tests
    entry_rows = entries(d)
    opening = next(e for e in entry_rows if e["type"] == "Opening")
    claim(int(opening["date"][:4]) == d.F, "the opening entry is in the first year")
    reclass = [e for e in entry_rows if e["type"] == "Debt Reclass"]
    claim(len({e["score"] for e in reclass}) == 1, "the debt reclassifications fail the same number of tests")
    unexplained_je = [e for e in ex if e["process"] == "JE" and e["disposition"] != "Expected"]
    docs = Counter(e["doc"] for e in unexplained_je)
    multi = per_year(d, [e["date"] for e in unexplained_je if docs[e["doc"]] > 1])
    single = per_year(d, [e["date"] for e in unexplained_je if docs[e["doc"]] == 1])
    claim(max(single) - min(single) < max(multi) - min(multi),
          "the change in the journal entries comes mostly from documents that fail several tests")
    stable = [(name, per_year(d, [e["date"] for e in ex if e["test"] == f"JE {name}"]))
              for name in ("Weekend", "Backdated", "SelfApproved")]
    claim(all(max(v) - min(v) <= 1 for _, v in stable), "Weekend, Backdated, and SelfApproved barely move")
    pr_left = unexplained_n["PR"]
    claim(len(set(pr_left)) == 1, "payroll's unexplained exceptions are the same number every year")
    pr_self = per_year(d, [e["date"] for e in ex if e["test"] == "PR SelfApproved"])
    claim(all(s / n > 0.9 for s, n in zip(pr_self, counts["PR"])), "payroll's rate is almost entirely the design finding")
    return dict(table=[(p, list(zip(counts[p], pops[p], rates[p]))) for p in ("JE", "PO", "PR")], unexplained=unexplained,
                po_n=po_n, po_r=po_r, growth=po_pop[2] / po_pop[1] - 1, opening=word(opening["score"]),
                opening_year=int(opening["date"][:4]), reclass=word(reclass[0]["score"]),
                reclass_years=[int(e["date"][:4]) for e in reclass], stable=stable, pr_left=word(pr_left[0]))


# --- Exercise 16.5 --------------------------------------------------------------------------------

def mad(amounts: list[float]) -> float:
    digits = Counter(int(f"{a:.8E}"[0]) for a in amounts)
    n = sum(digits.values())
    return sum(abs(digits[k] / n - math.log10(1 + 1 / k)) for k in range(1, 10)) / 9


def conformity(x: float) -> int:
    """0 close, 1 acceptable, 2 marginally acceptable, 3 nonconformity."""
    return sum(1 for limit in MAD_RANGES if x > limit)


@note("ch16.ex5", EXERCISES)
def ex5(d, claim):
    payments = d.q("SELECT p.Amount, pi.GrandTotal FROM DisbursementPayment p JOIN PurchaseInvoice pi "
                   "ON pi.PurchaseInvoiceID = p.PurchaseInvoiceID WHERE p.PaymentDate <= ?", asof(d))
    full = [a for a, g in payments if abs(a - g) < 0.005]
    partial = [(a, g) for a, g in payments if a < g - 0.005]
    claim(len(full) + len(partial) == len(payments), "every payment is full or partial (none above its invoice)")
    values = dict(all=mad([a for a, _ in payments]), full=mad(full), partial=mad([a for a, _ in partial]))
    claim(conformity(values["all"]) == 2, "all payments: marginally acceptable conformity")
    claim(conformity(values["full"]) == 1, "full payments: acceptable conformity")
    claim(conformity(values["partial"]) == 3, "partial payments: nonconformity")
    claim(min(g for _, g in partial) >= 1000, "only invoices of $1,000 or more are paid in parts")
    small = [a for a, _ in payments if a < 1]
    claim(all(a > 0 for a in small), "the payments below $1 are positive, so their text begins with 0")
    return dict(asof=asof(d), n=len(payments), n_full=len(full), n_partial=len(partial), mad=values, small=len(small))


# --- Exercise 16.6 --------------------------------------------------------------------------------

@note("ch16.ex6", EXERCISES)
def ex6(d, claim):
    end = asof(d)
    pairs = d.q("SELECT julianday(b.PaymentDate) - julianday(a.PaymentDate), a.PurchaseInvoiceID = b.PurchaseInvoiceID "
                "FROM DisbursementPayment a JOIN DisbursementPayment b ON b.SupplierID = a.SupplierID AND b.Amount = a.Amount "
                "AND b.DisbursementID > a.DisbursementID WHERE a.PaymentDate <> b.PaymentDate AND a.PaymentDate <= ?1 "
                "AND b.PaymentDate <= ?1", end)
    claim(not any(r[1] for r in pairs), "no pair pays the same invoice")
    emp = employees(d)
    approved = {table: Counter(r[0] for r in d.q(f"SELECT ApprovedByEmployeeID FROM {table}"))
                for table in ("PurchaseOrder", "JournalEntry", "PayrollRegister")}
    totals = {t: sum(c.values()) for t, c in approved.items()}

    def top(table: str) -> dict:
        k, n = approved[table].most_common(1)[0]
        return dict(emp[k], n=n, share=n / totals[table])

    def share(table: str, k: int) -> dict:
        return dict(n=approved[table][k], share=approved[table][k] / totals[table])

    cfo, controller, manager = top("PurchaseOrder"), top("JournalEntry"), top("PayrollRegister")
    claim(cfo["title"] == "Chief Financial Officer", "the CFO approves the most orders")
    claim(manager["title"] == "Accounting Manager", "the Accounting Manager approves the most registers")
    claim(set(approved["JournalEntry"]) == {cfo["id"], controller["id"], manager["id"]},
          "the journal entries are approved by the CFO, the Controller, and the Accounting Manager")
    claim(all(t["share"] > 0.9 for t in (cfo, controller, manager)), "each of three processes rests on one person")
    claim(manager["share"] == 1, "the Accounting Manager approved every register")
    others = {k: n for k, n in approved["PurchaseOrder"].items() if k != cfo["id"]}
    titles = Counter(emp[k]["title"] for k in others)
    claim(set(titles) == {"Buyer", "Procurement Analyst", "Purchasing Manager", "Production Manager", "Production Supervisor",
                          "Account Executive"}, "the other orders' approvers are the roles the note lists")
    claim(titles["Buyer"] > 1 and titles["Procurement Analyst"] > 1
          and all(titles[t] == 1 for t in ("Purchasing Manager", "Production Manager", "Production Supervisor", "Account Executive")),
          "several buyers and procurement analysts, and one each of the other roles")
    executive = next(k for k in others if emp[k]["title"] == "Account Executive")
    claim(emp[executive]["terminated"] is not None, "the Account Executive has departed")
    ex = register(d)
    ranked = Counter(e["emp"] for e in ex).most_common()
    claim(ranked[0][0] == manager["id"] and ranked[1][0] == cfo["id"],
          "the exceptions by approver put the Accounting Manager first and the CFO second")
    return dict(asof=end, pairs=len(pairs), within30=sum(1 for r in pairs if abs(r[0]) <= 30),
                cfo=cfo, cfo_entries=share("JournalEntry", cfo["id"]), controller=controller, manager=manager,
                manager_entries=share("JournalEntry", manager["id"]), other_orders=sum(others.values()),
                other_people=word(len(others)), executive=others[executive], first=ranked[0][1], second=ranked[1][1])


# --- Multiple-choice answer key -------------------------------------------------------------------

@note("ch16.mcq", MCQ)
def mcq(d, claim):
    pops = {p: per_year(d, dates) for p, dates in populations(d).items()}
    claim(all(100 <= n < 1000 for n in pops["JE"]) and all(1000 <= n < 10000 for n in pops["PO"]),
          "hundreds of entries against thousands of orders a year")
    regs = registers(d)
    approvers = {r["approver"] for r in regs}
    claim(len(approvers) == 1 and any(r["payee"] == r["approver"] for r in regs),
          "one approver approves every register, including the approver's own")
    last = dict(JE=max(e["date"] for e in entries(d)), PO=max(o["date"] for o in orders(d)), PR=max(r["date"] for r in regs))
    claim(min(last.values()) == last["PR"] < min(last["JE"], last["PO"]), "the last pay date is the earliest of the last dates")
    claim(d.one("SELECT COUNT(*) FROM PayrollPeriod WHERE Status <> 'Processed' AND PeriodStartDate <= ?", asof(d)) > 0,
          "pay periods of the year are open")
    return dict(pay_day=f"{MONTHS[int(last['PR'][5:7]) - 1]} {int(last['PR'][8:])}")
