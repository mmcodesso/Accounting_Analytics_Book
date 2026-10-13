---
note: ch08.chapter
title: 'Chapter 8: Audit Analytics in Excel'
kind: chapter-notes
unit: '8'
minutes: 240
tool: excel
figures:
  - id: IF-08-0-A
    kind: diagram
    purpose: One journal entry reached by three different tests, for the discussion at the end of Tutorial 8.3.
    shows: "A hub with three spokes. In the centre, a box for the opening balance entry, labeled with its entry number and with the chief financial officer as creator. Three boxes around it, each joined to the hub by an arrow. The receivables reconciliation of Tutorial 8.2, whose difference is the entry's line to account 1020. The journal entry tests of Tutorial 8.3, where it is the only entry that scores four. The payables reconciliation of Exercise 8.2, whose difference is the entry's credit to account 2010, balanced by a debit to cash of the same amount. Each outer box names its dollar amount."
    data: JournalEntry and GLEntry for the opening entry; the receivables and payables lines are the opening amounts in the Expected results of Exercises 8.1 and 8.2.
  - id: IF-08-0-B
    kind: diagram
    purpose: Choosing a test by the kind of records, for the discussion of the exercises.
    shows: "A decision tree read from left to right. The root asks what the records are. Five branches. Amounts with no upper limit lead to strata, then a first-digit test of the subsets. Documents numbered in a series lead to a uniqueness check, then a gap test. Documents approved against a limit lead to flags and threshold bands. Pairs of records that could repeat lead to a near-duplicate test on supplier and amount, then the invoice. A balance that should equal a ledger account leads to a reconciliation, an aging and a confirmation sample. Each leaf names the tutorial step or exercise requirement that practices it."
    data: The chapter's own tests; no dataset values.
---
# Chapter 8: Audit Analytics in Excel

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part II, Accounting Analytics with Excel: the fifth and last Excel chapter. It takes the auditor's view of the data and ends Part II before the comprehensive case |
| Analytics types | Descriptive (stratification, aging, reconciliation) and diagnostic (flags, risk scores, digit tests, exceptions). Exercise 8.1's expected credit loss is a small predictive step |
| Tools | Excel with Power Query: Group By, merges and date filters; COUNTIFS, SUMIFS, MINIFS, XLOOKUP, FILTER, SORTBY, RANDARRAY and SEQUENCE; PivotTables with Show Details; a combo chart. No SQL or Power BI |
| Components | {{ unit.tutorials|length }} guided tutorials, {{ n_exercises }} exercises ({{ per_perspective }} for each perspective), {{ n_questions }} multiple-choice questions and a deck of {{ slides }} slides |
| Files students need | CharlesRiver.xlsx, never edited. AuditAnalytics.xlsx starts blank in Tutorial 8.1. Chapter08-companion.zip holds it at the start of Tutorials 8.2 and 8.3 and at the end of the chapter, and Chapter08-exercises.zip the model answers (Chapter 8 Exercises - Solutions.xlsx). The companion files read `C:\CharlesRiver\CharlesRiver.xlsx` |
| Time | Class: about 240 minutes. Students: about two hours of reading, 75 to 90 minutes for each tutorial and 75 to 150 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The three fiscal years hold {{ t1.n|count }} supplier payments, which agree in count and total with the ledger's cash credits. A further {{ t1.after|count }} payments are dated {{ n }}, so a date filter must leave them out on both sides.
- Charles River pays only larger invoices in parts (the smallest is ${{ t1.min_part|money }}), which is why the partial payments fail a first-digit test that the full payments pass.
- Account 1020 exceeds the open invoices by exactly one journal entry line of ${{ t2.opening|money }}, and accounts 1030 and 6170 have no postings. The same entry credits payables with ${{ t3.ap_opening|money }}.
- Of {{ t3.n }} journal entries, {{ t3.flagged }} have at least one flag. Most flags have an ordinary explanation (weekend depreciation, year-end closes); one entry carries four.
- The purchasing and pricing exercises rest on planted conditions: self-approved orders, orders approved under the ID of an employee whose recorded termination precedes the order, requisitions clustered just under an approval limit, promotions with impossible dates, and expired price lists still cited.
- Two tests are clean on purpose: no purchase order number repeats or goes missing, and no near-duplicate pair pays the same invoice.

## What students should be able to do afterward

1. Reconcile a population to the ledger before testing it, and stratify it to see where the value lies. Practiced in Tutorial 8.1 (Steps 1 to 4), Exercises 8.2 and 8.4 (requirement 2) and questions 1 and 2.
2. Run a first-digit test, judge it with the mean absolute deviation and trace a nonconformity to a subset with a business cause. Practiced in Tutorial 8.1 (Steps 5 to 8) and questions 3 to 7. No exercise repeats it; Exercise 8.4's extension does.
3. Age receivables at an as-of date, reconcile them to the ledger, select balances for confirmation and estimate an allowance. Practiced in Tutorial 8.2, Exercises 8.1 to 8.3 and questions 8 to 10 and 14.
4. Test journal entries, orders and invoices for management override with flags and a risk score. Practiced in Tutorial 8.3, Exercise 8.5 (requirements 1 to 3) and questions 11 to 13.
5. Design duplicate, gap, threshold and pricing tests. Practiced in Exercises 8.5 (requirements 4 to 6) and 8.6 and question 15.
6. Document a test in a workpaper and give every exception a disposition, separating weaknesses in a control's design from failures in its operation. Practiced in the last step of each tutorial, in every exercise's memo and most in Exercises 8.5 and 8.6.

## Preparing to teach
**Before the first class**

- Students need desktop Excel with Power Query (on a Mac, Excel for Microsoft 365). The tutorials use XLOOKUP, FILTER, SORTBY, RANDARRAY and SEQUENCE, so Microsoft 365 or Excel 2021 or later. The model answers also use LET, HSTACK, VSTACK, MAP and LAMBDA, which need Microsoft 365 or Excel 2024.
- A late student takes the start file from Chapter08-companion.zip, points its queries at their copy of CharlesRiver.xlsx (**Data > Get Data > Data Source Settings**, **Change Source**) and chooses **Data > Refresh All**. Its Solution Notes worksheet then checks every control total.
- Do the three tutorials yourself. Each imports T3_GLEntry, a Table of {{ gl_n|count }} rows, so students choose **Transform Data**, never **Load**. Time the first refresh of each.
- - Get the PowerPoint deck from the Downloads page. Its modules follow the chapter's sections, and each tutorial has a checkpoint slide.

**Pitfalls that cost class time**

- **Connection only.** The **Close & Load To** choice in Tutorials 8.1 to 8.3 applies to every new query, so nothing loads until the student loads the main query from **Data > Queries & Connections**. A missing worksheet is usually this.
- **Typed dates.** The cutoff is typed in several date filters and in the AsOfDate cell. A student who reruns the work on a later extract must change them all.
- **Frozen results.** RANDARRAY reshuffles on every recalculation, so the confirmation sample must be pasted as values the moment it is drawn, and a disposition typed beside a query's output drifts when the query refreshes.
- **Spills.** FILTER, SORTBY and the drill-down formula need empty cells below them, or they return #SPILL!.
- **Slow formulas.** The near-duplicate test of Exercise 8.5 compares every payment with every other, so the sheet recalculates slowly.

## Teaching approaches

**Plan A: lecture with live demonstration (three sessions of 80 minutes, 240 minutes in all).** It fits a lecture course with time at home for the exercises. One tutorial anchors each session; demonstrate the steps that carry the ideas and leave the rest to students.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 15 | The audit committee's request, the objectives, audit analytics and the workflow | 2 to 9 |
| 1 | 15 | Reconciling and stratifying a population | 10 to 13 |
| 1 | 20 | Benford's Law and the MAD; the check and the answer | 14 to 20 |
| 1 | 30 | Tutorial 8.1: Steps 2, 5 and 6 live; students finish at home | 21 to 27 |
| 2 | 20 | Aging, reconciliation and confirmations; the check and the answer | 28 to 33 |
| 2 | 45 | Tutorial 8.2: Steps 2, 3, 5 and 6 live | 34 to 38 |
| 2 | 15 | The allowance and the unsupported balance: launch Exercise 8.1 | |
| 3 | 20 | Journal entry testing, scores and dispositions; the check and the answer | 39 to 45 |
| 3 | 35 | Tutorial 8.3: Steps 2, 3 and 6 live | 46 to 51 |
| 3 | 10 | Duplicate, gap and threshold tests | 52 to 56 |
| 3 | 5 | The workpaper | 57 to 59 |
| 3 | 10 | The findings, the summary; assign the exercises | 60 to 65 |
| | 240 | Total | |

**Plan B: lab first (one session of 180 minutes, with the exercises as homework).** Students build before they hear the vocabulary, so each finding arrives as a result they produced. It fits a computer lab; pairs take the next start file when they fall behind.

| Minutes | Activity | Slides |
|---:|---|---|
| 5 | Pose the audit committee's request | 5 |
| 45 | Tutorial 8.1 in pairs, to the checkpoint | 21 to 27 |
| 10 | Debrief: the strata, the MAD and the partial payments | 13 to 18 |
| 45 | Tutorial 8.2 in pairs, from the Tutorial 8.2 start file | 34 to 38 |
| 10 | Debrief: the difference of a round amount | 30, 36 |
| 45 | Tutorial 8.3 in pairs, to Step 6 | 46 to 50 |
| 15 | Debrief: three tests, one entry; dispositions | 43, 49 to 51 |
| 5 | Assign the exercises | 64 |
| 180 | Total | |

**Plan C: flipped, with one 90-minute class.** Students read the chapter and build the tutorials at home. It fits upper-level and graduate classes and opens with a quiz.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Quiz on questions 1, 5, 8, 9, 13 and 14 | |
| 25 | Review clinic: partners swap workbooks and check Population!B4 and C4, Aging!C13 and JE Summary!B15 and B16 | 27, 38, 51 |
| 25 | Break it: a first-digit shortcut, a null left in an open balance, a flag column on text dates, a sample never pasted as values | 24, 35, 47 |
| 20 | Start Exercise 8.1 or 8.5 in pairs | |
| 10 | Discussion prompts 2 and 3; assign the exercises | 61 |
| 90 | Total | |

Plan A is the safest. Plan B gives students ownership of the findings and needs a lab. Plan C leaves no room for demonstration.

## Tutorial guide
### Guided Tutorial 8.1: Stratifying and Testing Supplier Payments

**Purpose.** Students start the audit workbook, agree a population to the ledger, stratify it, examine the largest items and run a first-digit test that fails for a reason the data explains. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (Group By before loading) and Steps 5 and 6 (the first-digit formula and the MAD). Leave Steps 1, 4 and 9 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1, 2 | Payments Table and the ledger's cash credits on Population, with the differences in B4 and C4 | {{ t1.n|count }} payments, ${{ t1.total|money }}; {{ t1.ledger_n|count }} credits, ${{ t1.ledger_total|money }}; both differences 0 |
| 3 | The strata: the smallest stratum and the middle one | {{ t1.strata[0].count|count }} payments ({{ t1.strata[0].share_n|pct(0) }}) hold {{ t1.strata[0].share_v|pct(0) }} of the value; {{ t1.strata[2].count|count }} payments from 10,000 to 50,000 hold {{ t1.strata[2].share_v|pct(0) }} |
| 4 | The top two strata | {{ t1.top_n }} payments to {{ t1.top_suppliers }} suppliers, ${{ t1.top_total|money }} in all, each paying one invoice in full |
| 5 | Payments with LeadDigit 0 (Population!B6) | {{ t1.zero }} |
| 6 | MAD of all payments (Benford!E12) | {{ t1.all.mad|num(5) }}, {{ t1.all.label }}; digit 1 at {{ t1.digit1|pct(1) }} against {{ t1.digit1_expected|pct(1) }} expected |
| 7, 8 | Full and partial payments, their MADs and the smallest invoice paid in parts (Benford!I14) | {{ t1.full.n|count }} full, {{ t1.full.mad|num(5) }}, {{ t1.full.label }}; {{ t1.part.n|count }} partial, {{ t1.part.mad|num(5) }}, {{ t1.part.label }}; ${{ t1.min_part|money }} |

**Stumbles to expect**

- Step 1: the Payments worksheet missing, because **Only Create Connection** applied to the query, or a date filter of **After** for **Before**, which shifts the count by the {{ t1.after|count }} payments of {{ n }}.
- Step 2: **Load** chosen for T3_GLEntry, which freezes Excel.
- Step 5: the shortcut formulas. `LEFT([@Amount],1)` returns 0 for the {{ t1.below1|count }} payments below $1, and `LEFT(TEXT([@Amount],"0"),1)` rounds before it takes the digit. Together they misclassify {{ t1.wrong_either|count }} payments, so B6 is not zero.
- Step 6: the combo chart with the Expected series as columns, or a selection of the wrong columns.

**The checkpoint to look for.** The four bullets. A strong student says the payments agree with the ledger and that the nonconformity points to a subset, not to fraud: the invoices themselves conform ({{ t1.inv.mad|num(4) }}).

### Guided Tutorial 8.2: Aging Receivables and Reconciling Them to the Ledger

**Purpose.** Students calculate each invoice's open balance at the year-end, age it with a lookup Table, reconcile the total to account 1020, trace the difference and select customers for confirmation. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (the merges and the null replacement), Step 3 (the XLOOKUP) and Step 6 (the PivotTable and **Show Details**). Leave Steps 1, 7 and 8 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 2 | Rows of OpenInvoices, with no balance of zero or less | {{ t2.n|count }} invoices; the {{ t2.neg_n|count }} paid and then credited are removed |
| 4 | The aging total, and the share of it that is current | ${{ t2.total|money }}; {{ t2.buckets[0].share|pct(0) }} current, {{ t2.buckets[1].share|pct(0) }} at 1 to 30 days; the three older buckets hold {{ (t2.buckets[2].n + t2.buckets[3].n + t2.buckets[4].n)|count }} invoices |
| 5 | Account 1020 against the open invoices (Aging!C12 and C13) | ${{ t2.gl|money }}; a difference of ${{ t2.diff|money }}, a round amount |
| 6 | The PivotTable by source document, and the Show Details sheet | four source types; one JournalEntry row, {{ t2.entry }}; no rows for accounts 1030 and 6170 |
| 7 | Key items, other customers and the sample | {{ t2.key_n }} key items holding {{ t2.key_share|pct(0) }}; {{ t2.others_n }} other customers; a sample of {{ t2.sample }}, pasted as values |

**Stumbles to expect**

- Step 2: the null left in AppliedTotal or CreditedTotal. Of the open invoices, {{ t2.neither|count }} have neither a receipt nor a credit memo, so nearly all of them disappear at the filter.
- Step 3: the last argument of XLOOKUP left out, which returns #N/A for every invoice that is not exactly on a bucket boundary.
- Step 5: **And** chosen in the AccountID filter instead of **Or**, which returns no rows.
- Step 7: the sample not pasted as values, so it changes on every recalculation and no longer matches the workpaper. Two customers named {{ t2.shared }} are kept apart only because the grouping includes CustomerID.

**The checkpoint to look for.** The five bullets. A strong student says that most of the balance is not yet due, that the aging shows what is owed and not how promptly customers paid, and that the difference traces to one line that no invoice supports.

### Guided Tutorial 8.3: Testing Journal Entries for Management Override

**Purpose.** Students add five flags and a risk score, explain the patterns with PivotTables, record a disposition for each flagged entry and trace the top score to its ledger lines. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Step 2 (the five flag formulas) and Step 6 (the drill-down). Leave Steps 1, 4 and 7 to students.

**What students should see.**

| Step | Look for | Value |
|---|---|---|
| 1 | Rows of JournalEntries | {{ t3.n }} entries |
| 2, 3 | The flag counts (Weekend, Backdated, SelfApproved, AboveLimit, RoundAmount) | {{ t3.flags.Weekend }}, {{ t3.flags.Backdated }}, {{ t3.flags.SelfApproved }}, {{ t3.flags.AboveLimit }}, {{ t3.flags.RoundAmount }} |
| 3 | Entries scoring 0 to 4 | {{ t3.scores[0] }}, {{ t3.scores[1] }}, {{ t3.scores[2] }}, {{ t3.scores[3] }}, {{ t3.scores[4] }}; the one that scores four is {{ t3.number }} |
| 4 | Who creates entries; why flags come in groups | the accounting manager creates {{ t3.n_am }}; the controller the depreciation and the closes; the chief financial officer one |
| 5 | Dispositions for every flagged entry | {{ t3.flagged }} entries: {{ t3.expected }} expected, {{ t3.follow }} to follow up |
| 6 | JE Summary!B15 and B16, and the spilled lines | both ${{ t3.total|money }}; {{ t3.olines }} lines, one of them the ${{ t3.ar_line|money }} debit to 1020 |

**Stumbles to expect**

- Step 1: CreatedDate left as text, which makes every flag formula that reads it return #VALUE!.
- Step 2: `WEEKDAY([@CreatedDate],2)>5` written without the second argument, which numbers Sunday as 1 and flags the wrong days. The count of Weekend flags is the check.
- Step 5: the filtered rows pasted without **Paste Special > Values**, or dispositions typed in the live Table, where a refresh moves them.
- Step 6: **Load** instead of **Transform Data** for T3_GLEntry, and a drill-down with no empty cells below it.

**The checkpoint to look for.** The four bullets. A strong student says that the weekend depreciation entries and the year-end closes are expected, with the evidence still to examine, that the approval weaknesses go to follow-up, and that one entry is the first item for the audit committee.

{{ figure('IF-08-0-A') }}

## Difficult ideas and misconceptions
**Agreeing totals is not completeness.** Question 1 and Tutorial 8.1 Step 2. Students write "complete" after a zero difference. Ask: what two errors would leave the totals equal, and what could the ledger itself have missed?

**A nonconforming digit test is not a finding.** Questions 5 and 6, and the partial payments. Students say "fraud" when the MAD is high, or "fine" when it is marginal, and read a significant chi-square as proof. Ask: which subset drives it, what in the business explains it, and why does the book use the MAD?

**A shortcut formula can pass a glance.** Question 4. `LEFT` and `TEXT(...,"0")` look right on most rows. Ask: which payments break each?

**The as-of date decides the balance.** Question 8. A payment after the date does not reduce the balance, and the aging shows what is owed, not how promptly customers paid. Ask: what would a later extract change?

**An unsupported balance is a finding.** Exercises 8.1 and 8.2. Students age it, reserve it or write it off from the extract. Ask: who can decide whether the balance is a receivable, and what evidence would they ask for?

**A risk score ranks.** Question 13. Students read a score of 2 as proof. Ask: why are the weights a judgment?

**Exceptions are not errors.** Tutorial 8.3 and Exercises 8.5 and 8.6. Students list every flag as a problem or clear it with a guess. Ask: what evidence turns an exception into an expected one?

**Design or operation.** Exercises 8.5 and 8.6. A control that the data cannot stop is a design weakness; one that was bypassed is a failure of operation. Ask: what would you need to see to decide, and what do you say until you have it?

**Clean results count.** Exercise 8.5 (5) and (6). Students leave out a test that flags nothing. Ask: what does the clean result exclude, and what does it leave open?

## Discussion prompts
1. **The first-digit test of the payments is marginally acceptable. What does the audit committee hear?** A good discussion reaches the MAD as a distance and not a cause, the subsets, the explanation in the payment process, and the need for other evidence before anyone says fraud.
2. **The ledger holds ${{ t2.opening|money }} that no invoice supports, and no allowance. What do you tell the controller?** It reaches the request for the conversion-date detail, an allowance on the supported invoices, and a refusal to age or write off the unsupported line from the extract.
3. **One entry shows up in three tests. Is that a stronger finding or one finding counted three times?** The routes are independent, the fact is one, and the next step is the entry's support.
4. **Weekend depreciation entries are expected. When is "expected" not enough?** It reaches the evidence (the depreciation schedule, the approval) that a disposition records.
5. **Five customers exceed their credit limits and none is past due. Do you stop shipments?** Limits and payment behavior are different questions; review the approvals and the history first.
6. **An order was approved under the ID of an employee whose recorded termination precedes the order. Control failure or data problem?** The records cannot say; ask for approval timestamps and access logs, and call the classification provisional.
7. **A test finds nothing. Do you record it?** Yes, with what it excludes: a gap test says nothing about records never created.

## Using the exercises

All six exercises are Excel builds with a model answer in the solution workbook (a large file, because it holds ledger extracts; open it once before class). The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 8.1 Estimating the Allowance for Credit Losses | Financial | Excel | 90 | Intermediate | 3, 6 |
| 8.2 Reconciling Accounts Payable to the Ledger | Financial | Excel | 90 | Intermediate | 1, 6 |
| 8.3 Customer Credit Exposure | Managerial | Excel | 75 | Basic | 3 |
| 8.4 Supplier Concentration and Payment Timing | Managerial | Excel | 75 | Intermediate | 1 |
| 8.5 Testing Purchasing and Payment Controls | Auditing | Excel | 150 | Advanced | 4, 5, 6 |
| 8.6 Testing Pricing Controls | Auditing | Excel | 135 | Advanced | 5, 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 8.1 and 8.2, managerial students 8.3 and 8.4, auditing students 8.5 and 8.6. A swap of memos lets each track hear the others; the opening balance appears in 8.1 and 8.2, and the capital orders of 8.2 return in 8.5.
- *One exercise a session.* Take them in the order 8.3, 8.4, 8.1, 8.2, 8.5, 8.6, from the lightest to the longest.
- *A light load.* Exercises 8.1 and 8.5 take about four hours and cover outcomes 3 to 6.

**Grading and discussion.** Each exercise guide holds a rubric. Exercises 8.3 and 8.4 suit grading from the workbook, because their numbers have one answer. Exercises 8.1, 8.2, 8.5 and 8.6 end in a judgment and suit class discussion, with the workbook still graded for its numbers. Collect the workbook, not a screenshot: the formulas show the work.

{{ figure('IF-08-0-B') }}

## Multiple-choice questions

{{ mcq_key() }}

**Questions where a wrong option tempts**

- **Question 4.** Option A is the `LEFT` shortcut and option C the `TEXT(...,"0")` shortcut; both look right on most payments.
- **Question 5.** Option A reads a significant chi-square as fraud, option B a MAD below 0.015 as close conformity.
- **Question 6.** Option A reads nonconformity as proof of invented amounts, option D blames the formula.
- **Question 8.** Option C drops an invoice paid after the as-of date, which the aging at that date must keep.
- **Question 9.** Option C calls the difference the allowance. Accounts 1030 and 6170 have no postings.
- **Question 14.** Option A invents a rule against formulas; only pasted values preserve a RANDARRAY selection.
{% if n_longest %}
- **Length.** The correct option is also the longest in {{ n_longest }} of the {{ n_questions }} questions ({{ longest_correct }}), so wording alone can give it away. If you grade with these, ask students to explain their answer or reword the options.
{% endif %}

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 and 2 make a quiz of populations, 3 to 7 of digit tests, 8 to 10 and 14 of receivables, and 11 to 13 and 15 of journal entries, gaps and scores.

## Connections
**Builds on.** Exercises 2.5 and 2.6 found the requisitions without an approver and the reused references that this chapter tests again. Chapter 4 taught Power Query, Tables, the control total and the documentation sheet, Tutorial 4.1 Step 10 showed why agreeing totals proves little, and Chapter 5 set the as-of date and tested invoice numbers and the supplier and item masters. Chapters 6 and 7 supplied the ledger to statements, the analytical procedures and the year-end closes that the Watch out explains.

**Later chapters.** The Part II case follows. Part III repeats the tests in SQL (Chapter 12's audit library and Exercise 12.6 reproduce the first-digit, duplicate and gap tests), Chapter 16 rebuilds the journal entry, order and payroll tests as a monitoring report in Power BI, and Chapter 19 audits the credits cycle with the same exception and disposition vocabulary.

**Appendices.** The quick reference lists every Excel and Power Query function the chapter uses. **Appendix D** maps each exercise to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard; each exercise guide names the competencies it practices.
