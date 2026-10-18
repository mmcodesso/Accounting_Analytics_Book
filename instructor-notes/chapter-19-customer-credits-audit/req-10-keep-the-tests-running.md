# Requirement 10: Keep the tests running (Chapter 16)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 10 |
| Perspective | Auditing |
| Tools | Power BI Desktop |
| Time | About 90 minutes |
| Solution file | Chapter19-capstone-pbi-monitoring.zip: Audit Monitoring/Audit Monitoring.pbip (the pages Credits Cycle, Anomalies and Change Log added to those of Chapter 16; the Tests and Checks tabs in DAX query view) |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

An audit that ends with a report tests the past. The register of Chapter 16 already runs earlier chapters' rule tests with every refresh, and adding this cycle's rules to it, under that chapter's change control, turns the audit into monitoring. Two judgments carry the requirement. A rule test, where a document either passes or fails, belongs in the register; an anomaly, a reason to look, stays outside it. And the historical exceptions of the new tests are recorded once, as a finding grouped by a supported cause (which may concern design or operation), so that they do not flood the review while each exception stays in the register. The analytics type is prescriptive: the tests are the action that outlasts the report.

Students can add rule tests and their populations to a register (Part 1), keep anomalies outside it (Part 2), link historical exceptions to a finding by supported cause and close it on a retest (Part 3), build the small alternative when no register exists (Part 4), and recheck the date the data run through and log the change (Part 5).

**Competencies practiced.** CPA Evolution ISC M2 (tests of internal controls, logical access and change management) and Core S2 M9; IMA Reporting and Control (internal control); IFAC IES 2 (g) and (i); AACSB A5 part 5.1 (Power BI).

## Before you assign

- **Files.** Audit Monitoring.pbix as Chapter 16 leaves it, CharlesRiver.xlsx, and Power BI Desktop (Windows only). Students use the definitions of Requirement 4; a different definition of "before the payment" changes a count (51 refunds by the receipts' dates, and a register of 985 rows).
- **Data conditions.** The credits end 2026-12-26 and the refunds 2026-12-22, after payroll's last pay date, 2026-12-18, so Data Through stays where it is. No exception of the new tests is dated after the audited year.
- **Verify first.** In DAX query view, run the Checks tab: 107 rows for the requirement and the register's chain, 7 and 6 for the milestones, all agree.

## How to run it

Pairs, about 90 minutes: 35 for the flags and the exception queries, 10 for the tests and the populations, 15 for the anomalies, 15 for the findings, 15 for Data Through and the change log. Hold back the design finding until the register shows the flood, then ask what the committee would do with it. **Collect** the project and a screenshot of the Tests tab.

## Step-by-step solution

### Part 1: Add the four rule tests and the two processes

**Step 1. Build the flags in Power Query.** Two queries from CashReceiptApplication do not load (clear **Enable load**): Last Payments, the last application date of each invoice, and Appliers, the applications grouped by invoice and applier.

```
    #"Grouped Rows" = Table.Group(Source, {"SalesInvoiceID"}, {{"LastPayment", each List.Max([ApplicationDate]), type nullable date}})
    #"Grouped Rows" = Table.Group(Source, {"SalesInvoiceID", "AppliedByEmployeeID"}, {{"Applications", each Table.RowCount(_), Int64.Type}})
```

CreditMemo then merges the approver's limit and the appliers and adds its two flags.

```
    #"Merged Queries1" = Table.NestedJoin(#"Renamed Columns", {"OriginalSalesInvoiceID", "ApprovedByEmployeeID"}, Appliers, {"SalesInvoiceID", "AppliedByEmployeeID"}, "Appliers", JoinKind.LeftOuter)
    #"Added Custom1" = Table.AddColumn(#"Added Custom", "CashAndCredit", each if [ApproverApplications] <> null then 1 else 0)
```

CustomerRefund merges the limit, the credit's invoice and the last application, and adds its two.

```
    #"Merged Queries2" = Table.NestedJoin(#"Expanded CreditMemo", {"OriginalSalesInvoiceID"}, #"Last Payments", {"SalesInvoiceID"}, "Last Payments", JoinKind.LeftOuter)
    #"Added Custom1" = Table.AddColumn(#"Added Custom", "BeforePayment", each if [LastPayment] <> null and [RefundDate] < [LastPayment] then 1 else 0)
```

BeforePayment is a retrospective timing screen: it flags a refund only after an application dated later is recorded. In an event-date replay of the 58 cases the first such application comes 1 to 14 days after the refund (mean 5.22) and the last 1 to 19 days after it (mean 5.62), two different quantities; entry and refresh latency is not in the data. It does not show that a refund was supported when approved, and it misses an unpaid invoice with no later application. Prompt monitoring needs a separate as-of supported-balance test on the approved receipt or clearance basis, with credits and earlier refunds.

**Check:** the flags count 414, 206, 163 and 58. **Watch for:** the appliers merged on the invoice alone, which flags 567 of 612 credits instead of those whose approver applied the cash, and a refund compared with `<=`, which flags 64 instead of 58.

**Step 2. Turn each flag into register rows.** One query for the credits and one for the refunds unpivots its two flags, keeps the ones, and names the test; the register's Source step then combines them with the existing queries.

```
    #"Unpivoted Only Selected Columns" = Table.Unpivot(Source, {"AboveLimit", "CashAndCredit"}, "Attribute", "Value")
    #"Added Custom" = Table.AddColumn(#"Filtered Rows", "TestID", each "CM " & [Attribute])
```

![How the flags reach the register, the picture a student needs when a rate comes out blank.](../figures/chapter-19-customer-credits-audit/IF-19-10-B.pdf)

**Check:** the register grows from 151 to 992 rows, and each test and document pair is still unique. **Watch for:** a TestID that differs from the one in the Tests table.

**Step 3. Add the tests and the processes.** Four rows join the Tests table (TestID, Test, Process, Source), with the processes Credit memos and Refunds, and the Population measure counts them; relate the credit and refund dates to Date.

```
Population =
SWITCH (
    SELECTEDVALUE ( Tests[Process] ),
    "Journal entries", COUNTROWS ( JournalEntry ),
    "Purchase orders", COUNTROWS ( PurchaseOrder ),
    "Payroll", COUNTROWS ( PayrollRegister ),
    "Credit memos", COUNTROWS ( CreditMemo ),
    "Refunds", COUNTROWS ( CustomerRefund )
)
```

| Test | Exceptions | By year | `Rate per 1,000` by year | Overall |
|---|---:|---|---|---:|
| CM AboveLimit | 414 | 104 / 157 / 153 | 658.2 / 676.7 / 689.2 | 676.5 |
| CM CashAndCredit | 206 | 60 / 77 / 69 | 379.7 / 331.9 / 310.8 | 336.6 |
| RF AboveLimit | 163 | 43 / 61 / 59 | 781.8 / 726.2 / 710.8 | 734.2 |
| RF BeforePayment | 58 | 10 / 29 / 19 | 181.8 / 345.2 / 228.9 | 261.3 |

**Check:** the counts and yearly rates in the table, and the overall rates, from populations of 158 / 232 / 222 credits and 55 / 84 / 83 refunds. **Watch for:** a process spelled differently from the measure's, which leaves the population and the rate blank while the exceptions still count.

### Part 2: Keep the refund method and the missing offset outside the register

**Step 4. Add them as columns of the refund table (MethodMismatch and OffsetMissed, in the model's CustomerRefund query), with their own measures and page.**

**Check:** 153 refunds by a method no receipt on the invoice used, and 124 paid while the customer's past-due balance was at least the refund. They stay out because no customer pays by one method only and a method chosen at random would mismatch about as often, and because the records hold no policy that requires an offset. **Watch for:** adding them to the register, which makes it 1,269 rows and buries the rule failures.

### Part 3: Link the historical exceptions to findings by supported cause

**Step 5. Link each exception to its finding and keep every exception.** The model keeps one Findings row for each supported cause (credits, refunds): the finding, design or operation, its owner, the period it covers and the due date, with the fix date, retest date and result and closure approval left blank. A Finding Exceptions table (**Home > Enter data**) maps each historical exception, by TestID and DocumentNumber, to its finding, so coverage is a reviewed mapping and not a date rule: a late-loaded historical record stays open for review until mapped. Merge the mapping into the register, add a Covered column, relate Findings to Exceptions on FindingID, and measure the open exceptions without the covered ones. A finding's status names its first unmet step; it closes only when the fix is made, a retest after it passes and the closure is approved, and a target date reached with no fix stays open.

```
    #"Added Custom" = Table.AddColumn(#"Expanded Finding Exceptions", "Covered", each if [FindingID] <> null then 1 else 0)
Open Exceptions = CALCULATE ( [Exceptions], ISBLANK ( Exceptions[Disposition] ), Exceptions[Covered] = 0 )
Design Finding Exceptions = CALCULATE ( [Exceptions], Exceptions[Covered] = 1 )
```

![A mock of the Credits Cycle page, where the new tests and the design findings show.](../figures/chapter-19-customer-credits-audit/IF-19-10-A.pdf)

**Check:** the findings cover exceptions dated through the end of the audited year and are to be fixed by 2027-12-31; 841 exceptions are covered, 15 reviewed, and 136 open, as before, and both findings are open (nothing is fixed, retested or approved). Covered rows stay traceable under their open finding, and later exceptions stay open for review. **Watch for:** the open measure without the Covered condition, which reads 977, the covered period set to the fix-by date, which would hide later exceptions, and a finding closed on its date. After remediation all four tests remain subject to retest; the as-of supported-balance control addresses an unfunded refund at approval.

### Part 4: If you did not build Audit Monitoring.pbix

**Step 6. Build a small register in Credits Analytics.** A Tests table by Enter data with the four rows and their processes, an exceptions table that combines the two unpivoted flag queries, as in Steps 1 to 3 (the refund flags of Requirement 4's export hold two of the four tests), a population measure for each process, and Enter data tables for the findings and the change log. The model answer builds only the Audit Monitoring path, so grade this path by its structure: four tests, two processes, a unique pair on each row; dispositions and the Data Through check are beyond a minimal fallback and count as a plus.

**Check:** 841 exceptions, one row for each test and document.

### Part 5: Recheck Data Through and record the change

**Step 7. Take the earliest of the processes' last dates, and log the change.** The measure adds the last credit and refund dates to the earlier three; the Change Log table (Enter data) records what changed and why.

```
Data Through =
MINX (
    {
        MAX ( JournalEntry[PostingDate] ),
        MAX ( PurchaseOrder[OrderDate] ),
        MAX ( PayrollRegister[PayDate] ),
        MAX ( CreditMemo[CreditMemoDate] ),
        MAX ( CustomerRefund[RefundDate] )
    },
    [Value]
)
```

**Check:** Data Through reads 2026-12-18, set by payroll, the earliest of the five; the Change Log has 5 rows. **Watch for:** the latest date in place of the earliest, which reads 2026-12-31 and claims more than payroll's records show. In DAX query view, rerun Tests 1 to 6; Test 6 counts the register's rows, test and document pairs, reviewed, covered and open exceptions.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Exceptions of the four tests | 414; 206; 163; 58 | 1 |
| Register rows, before and after | 151; 992 | 2 |
| Covered by a design finding; reviewed; open | 841; 15; 136 | 5 |
| Anomalies: method mismatch; missed offset | 153; 124 | 4 |
| Data Through; Change Log rows | 2026-12-18; 5 | 7 |

> **Instructor notes, Requirement 10:** exceptions and rates per 1,000 (2024 / 2025 / 2026; three years): CM AboveLimit 414 (104 / 157 / 153; 658.2 / 676.7 / 689.2; 676.5); CM CashAndCredit 206 (60 / 77 / 69; 379.7 / 331.9 / 310.8; 336.6); RF AboveLimit 163 (43 / 61 / 59; 781.8 / 726.2 / 710.8; 734.2); RF BeforePayment 58 (10 / 29 / 19; 181.8 / 345.2 / 228.9; 261.3). Populations: credits 158 / 232 / 222, refunds 55 / 84 / 83. The register grows from 151 to 992 rows, (TestID, DocumentNumber) still unique. BeforePayment is a retrospective screen, not a test of support at approval (the first later application comes 1-14 days after the refund, mean 5.22, the last 1-19, mean 5.62). For BeforePayment, group the applications by invoice for the last ApplicationDate and merge it (by the receipts' ReceiptDate instead, RF BeforePayment has 51 exceptions, 9 / 24 / 18, per 1,000 163.6 / 285.7 / 216.9, and the register 985 rows: accepted with the definition stated); for CashAndCredit, merge the applications and test whether the credit's approver is among their appliers, the rule Requirement 4 states (testing the people who recorded the receipts too, an accepted extension when stated, gives 356 exceptions, 102 / 132 / 122, and a register of 1,142 rows). Findings: link each mapped historical exception to a finding by supported cause, design or operation (the model: two findings, credits and refunds, rated provisionally in Requirement 8), keeping every exception in the register, and review later or unmapped exceptions as they arrive; a finding closes only after the fix, a passed retest and approval, never on its planned date. Data Through stays 2026-12-18 (payroll, whose last two pay periods are open and scheduled to pay in January 2027), the earliest of the processes' last dates: what the tests can have seen, not proof that every record through it was loaded; credits end 2026-12-26 and refunds 2026-12-22. After remediation all four tests remain subject to retest and monitoring; an as-of supported-balance control, defined apart, addresses an unfunded refund at approval.

## What a strong answer says

- **The four tests use Requirement 4's definitions,** and the definition of "before the payment" is stated.
- **The processes are in the populations,** so each rule has a `Rate per 1,000` by year.
- **Anomalies stay outside the register,** with the reason.
- **The historical exceptions are linked to findings by supported cause,** design or operation stated, with the covered period, the fix-by date, the date of the fix and the retest kept apart, each exception kept in the register, later exceptions reviewed, and a finding closed on a retest.
- **Data Through is rechecked and the change is logged.**

A weak answer floods the register with the anomalies or the history, or closes the finding on the date.

## Common mistakes and how to respond

- **Appliers merged on the invoice alone.** *Symptom:* 567 credits flagged. *Response:* ask whom the control is about.
- **A same-day refund flagged.** *Symptom:* 64 refunds. *Response:* ask what the records say about the order within a day.
- **A process label that does not match.** *Symptom:* a blank rate beside a count. *Response:* compare the Tests table with the measure.
- **The anomalies in the register.** *Symptom:* 1,269 rows. *Response:* ask which of them is a rule failure.
- **No finding.** *Symptom:* 977 open exceptions. *Response:* ask who reviews that many.
- **The finding closed on the date.** *Symptom:* closed with no fix or retest. *Response:* ask what shows the control works.
- **The latest date as Data Through.** *Symptom:* 2026-12-31. *Response:* ask which process ends first.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Four rule tests with Requirement 4's definitions | 30 | All four, counts agreeing | Three, or a changed definition unstated |
| Two processes in the populations | 15 | A `Rate per 1,000` by year | Counts only |
| Anomalies kept outside | 10 | Columns, measures and a page, with the reason | In the register |
| Findings by supported cause | 20 | Covered period, fix-by date, later exceptions open | History left open |
| Data Through rechecked | 10 | The earliest date, with the reason | Latest date |
| Change recorded | 15 | Log with object, change and reason | No record |

## Extensions and discussion questions

- Record a disposition for the largest refund's exception with Chapter 16's Dispositions merge, and watch Reviewed Exceptions rise by one.
- Add the anomaly tests to the register once a refund policy exists, and say what the policy must state.
- Discuss: after the fix, which tests should fall to zero, and what would a timing screen that fires only after a later application miss?
