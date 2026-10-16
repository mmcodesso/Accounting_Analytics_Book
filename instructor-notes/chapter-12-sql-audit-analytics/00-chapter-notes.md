# Chapter 12: Audit Analytics in SQL

| | |
|---|---|
| Unit | Chapter 12: Audit Analytics in SQL |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 300 minutes of class time |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part III, Accounting Analytics with SQL: the last of four chapters. Chapters 9 to 11 queried, joined and analyzed; this chapter tests records, and it answers the question of Chapter 9 |
| Analytics types | Diagnostic for most tests; the pay expectation is predictive and the recommendations that close each finding are prescriptive |
| Tools | DB Browser for SQLite 3.13.1 on the working copy. Every test only reads |
| Components | 3 guided tutorials that build one script, Audit.sql, of 24 tests (L1 to L8, P1 to P6, H1 to H10), 6 exercises (2 for each perspective), 15 multiple-choice questions and a deck of 69 slides |
| Files students need | CharlesRiver_Work.sqlite from Tutorial 9.1. Chapter12-companion.zip holds Audit.sql at the start of Tutorials 12.2 and 12.3 and at the end. Chapter12-exercises-sql.zip holds Ex 12.1.sql to Ex 12.6.sql |
| Time | Class: about 300 minutes. Students: about 90 minutes of reading, 60 to 110 for each tutorial and 80 to 120 for each exercise (assign two or three). The times are estimates: time them yourself |

The chapter depends on these conditions of the data:

- The journal entries (851) and the manufacturing payroll reconcile to the ledger to the cent, yet each year-end is misstated: December deliveries are posted in January, and account `2030` holds only its opening $95,000.00, so no year-end accrues late-December wages.
- Six ledger postings point to a payroll payment that does not exist: three registers with no payment record.
- The three-way match has no exception status, 14 purchase orders fail an approval test, and one approver signs nearly all of them.
- Hours clocked, recorded and paid agree in every pay period. On 93 surge days every hourly manufacturing employee clocked the same hours, and the share of direct time recorded after its operation ended reaches 66%. The time records end on 2026-12-11.

## What students should be able to do afterward

1. Reconcile and profile a population before testing it, and say what a reconciliation cannot show. Practiced in Tutorial 12.1 (Steps 1 and 2), Tutorial 12.3 (Steps 1 and 2), Exercise 12.2 (2) and (4), and questions 1 and 8.
2. Trace in both directions, list the exceptions with UNION ALL and test cutoff with the dates of the events. Practiced in Tutorial 12.1 (Steps 3 to 8), Exercise 12.1 and questions 2 to 5.
3. Match purchase orders, receipts and invoices at the order line within a tolerance. Practiced in Tutorial 12.2 (Steps 1 to 3), Exercise 12.2 (4), which sums invoices to the receipt line the same way, and questions 6 and 7.
4. Test approvals against limit, role and dates, and measure concentration. Practiced in Tutorial 12.2 (Steps 4 to 6), Exercises 12.4 and 12.5, and questions 10 and 11.
5. Test the chain behind a cost, compare pay with an expectation, and judge what a pattern supports. Practiced in Tutorial 12.3 (Steps 2 to 9), Exercises 12.3 to 12.5, and questions 9, 12 and 15.
6. Re-perform tests as a documented library. Practiced in Tutorial 12.3 (Step 10), Exercise 12.6 and questions 13 and 14.

## Preparing to teach

**Before the first class**

- Students need CharlesRiver_Work.sqlite and DB Browser for SQLite 3.13.1. `SELECT sqlite_version();` shows the version. `LOG10`, used in Exercise 12.6, is in the Windows release and missing from DB Browser for SQLCipher.
- Do the three tutorials yourself in order and save Audit.sql. Every test runs in a second or two on the working copy.
- A late student takes Audit.sql from Chapter12-companion.zip, from the folder of the tutorial they start. Tutorial 12.1 needs only the working copy. The deck has a checkpoint slide for each tutorial.
- Open the model scripts once. Each query has two comment lines, the library's structure, and the notes at the end repeat the requirements and the checks. The as-of date is typed into the queries: it moves when the test is rerun.

**Pitfalls that cost class time**

- **A test that cannot fail.** An anti-join written with INNER JOIN returns no rows, the same answer as a clean population (figure below).
- **Positional UNION ALL.** The second query's columns can stack under the wrong headings with no error.
- **Exact equality on REAL sums.** Test H2 flags 2 periods that agree, until a tolerance is added.
- **Nothing selected.** Running with no selection runs the whole script and shows only the last result.

![A mock of the demonstration that a clean result may mean nothing, the anti-join of test L4 written two ways.](../figures/chapter-12-sql-audit-analytics/IF-12-0-B.pdf)

## Teaching approaches

**Plan A: lecture with live demonstration (three sessions of 100 minutes, 300 minutes in all).** It fits a lecture course with the exercises at home.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 20 | The committee's questions, populations, reconcile and profile | 2 to 10 |
| 1 | 25 | Tracing both ways, UNION ALL, cutoff; check | 11 to 17 |
| 1 | 55 | Tutorial 12.1: Steps 3, 4, 5 and 7 live; Steps 1, 2, 6 and 8 for students | 18 to 23 |
| 2 | 20 | The three-way match | 24 to 27 |
| 2 | 15 | Approvals and concentration; check | 28 to 32 |
| 2 | 35 | Tutorial 12.2: Steps 1 and 4 live; the rest for students | 33 to 37 |
| 2 | 30 | The chain behind a cost, isolated or systematic, expectations; check | 38 to 44 |
| 3 | 55 | Tutorial 12.3: Steps 2, 5, 7 and 8 live | 45 to 53 |
| 3 | 25 | Chapter 8's tests in SQL; the library | 54 to 62 |
| 3 | 20 | What the audit found; do the standards fit; assign; quiz on questions 2, 5, 9 and 12 | 63 to 69 |
| | 300 | Total | |

**Plan B: lab first (two sessions of 150 minutes, 300 minutes in all).** Students run the tests before they hear the vocabulary. It fits a computer lab; a pair that falls behind takes the next tutorial's start file.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 10 | Pose the three assignments | 5 |
| 1 | 60 | Tutorial 12.1 in pairs | 19 to 23 |
| 1 | 15 | Debrief: both directions, cutoff, the six postings | 12, 15, 20, 21 |
| 1 | 15 | The three-way match, a short lecture | 25 to 27 |
| 1 | 50 | Tutorial 12.2 in pairs | 34 to 37 |
| 2 | 10 | Can the records behind the explanation be trusted? | 39 to 42 |
| 2 | 90 | Tutorial 12.3 in pairs: Steps 1 to 5, then 6 to 10 | 46 to 53 |
| 2 | 25 | Debrief: surge days and what the committee can accept | 48 to 51, 64 |
| 2 | 25 | Chapter 8's tests and the library | 55 to 62 |
| | 300 | Total | |

**Plan C: flipped, with one 120-minute class.** Students build the tutorials at home. It fits upper-level and graduate classes.

| Minutes | Activity | Slides |
|---:|---|---|
| 15 | Quiz on questions 2, 5, 6, 9, 12 and 15 | |
| 30 | Review clinic: partners swap Audit.sql and agree the counts: 6 postings, 14 orders, 93 surge days | 20, 36, 48 |
| 25 | Break it: a test that cannot fail, a fan-out, a boundary with the wrong operator, an integer division | 14, 25, 57 |
| 35 | Start Exercise 12.1, 12.5 or 12.6 in pairs | |
| 15 | Discussion prompts 1 and 2; assign | 64, 65 |
| 120 | Total | |

Plan A is the safest, because the stumbles of this chapter are about reading a result, and a demonstration shows how. Plan B gives students the findings and needs a lab. Plan C leaves no time to demonstrate and fails for students who arrive without a finished script.

![The audit cycle of the chapter, from a population to a disposition, with the positive control that makes a clean result mean something.](../figures/chapter-12-sql-audit-analytics/IF-12-0-A.pdf)

## Tutorial guide

### Guided Tutorial 12.1: Reconciling the Populations, Tracing the Ledger, and Testing Cutoff

**Purpose.** Students reconcile two populations, trace the ledger both ways, explain the six postings and test cutoff at each year-end. **Time.** About 75 to 90 minutes. **Demonstrate, then hand over.** Demonstrate Steps 3 and 4, the anti-joins and the INNER JOIN trap, and Step 5, the CASE. Leave Steps 1, 2, 6 and 8 to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | Both reconcile | 851 entries and $129,860,610.27 on both sides; payroll differs by $0.00 in each year |
| 3, 4 | Six postings, three registers | 6 rows; registers 1, 2646, 5420, two of an employee who had left |
| 5, 6 | Cutoff | 23 invoices posted in another year, 8 dated before shipment, 9 shipment lines never invoiced |
| 7, 8 | Year-end | 6 periods cross a year-end, the last 2 open with no registers; account `2030` at $95,000.00 |

**Stumbles to expect**

- Steps 4 and 6: with INNER JOIN the tests return 0 rows in Step 4 and 0 in Step 6, a clean result that means nothing. Swapping two columns of the second query of Step 3 changes nothing, 6 rows either way, because that query finds no rows.
- Step 5: with the dating branch first, the invoices for the prior year's deliveries read 7 posted in another year and 4 dated before shipment, where the model has one more and one fewer. Without the GROUP BY in Shipped an invoice counts twice.
- Step 7: an INNER JOIN to the registers returns 4 periods and loses the two open ones, the wages recorded nowhere.

**The checkpoint to look for.** The six bullets. A strong student says the ledger holds up in what was tested and fails on timing.

### Guided Tutorial 12.2: Matching Purchases and Testing Their Approvals

**Purpose.** Students match every order line, test prices at two tolerances, reconcile unbilled receipts and test the approvals. **Time.** About 60 to 75 minutes. **Demonstrate, then hand over.** Demonstrate Step 1, summing each side to the order line, and Step 4. Leave Steps 2, 3, 5 and 6 to students.

| Step | Look for | Value |
|---|---|---|
| 1 | Four statuses, no exception | Matched 23,375; Received, not fully invoiced 1,100; Not yet received 277; Partly received 90 |
| 2, 3 | Tolerance, then the ledger | none above three percent, 5,109 above two, the largest increase 2.57%; $1,020,992.80 against $1,020,992.06 |
| 4, 5 | Approvals | Above approver limit 13; Self-approved 9; Dated after approver left 3; 14 orders behind 25 exceptions |
| 6 | Concentration | 9 approvers; the first signs 99.9% |

**Stumbles to expect**

- Step 1: comparing a receipt line with an invoice line row by row returns 40,293 rows and 21,224 disagree; sum to the order line first.
- Step 2: a price test without ABS finds the same lines, because every line above two percent is an increase.
- Step 3: the full value of the open receipt lines, not the part not yet invoiced, reads $1,529,459.73.
- Step 6: grouping by job title returns 7 rows where 9 belong.

**The checkpoint to look for.** The five bullets. A strong student separates the exceptions from the design risk of one approver.

### Guided Tutorial 12.3: Testing the Hours Behind the Variance

**Purpose.** Students profile the time records, reconcile the chain from clock to payment, test whose time was paid, compare pay with an expectation, and test overtime, surge days and late direct time. **Time.** About 90 to 110 minutes, the longest. **Demonstrate, then hand over.** Demonstrate Steps 2, 5, 7 and 8. Leave the rest to students.

| Step | Look for | Value |
|---|---|---|
| 1, 2 | Profile; the chain | 52,967 entries, 5 not approved, 3 with no clock-out; 77 periods, 0 differ |
| 3 | The first year | 8 periods from February to May with at most 80 indirect hours, against 4,931 in the first period |
| 4, 5 | Whose pay; the expectation | 6 lines paid to another employee, 8 on unapproved entries; differences $5.29, $4.81, $4.23, no line above a cent |
| 6 | Overtime | 5,123 short entries, none approved; 3 long entries without a link |
| 7 | Surge days | 12, 32, 49 days a year; share of overtime 35.5%, 58.9%, 70.5% |
| 8, 9 | Late direct time | share after the end 19.5%, 49.8%, 65.8%; Packing 95.4% |

**Stumbles to expect**

- Step 2: exact equality of REAL sums flags 2 periods; use a tolerance.
- Step 5: without the overtime premium, 6,007, 8,672, 10,386 lines are flagged, one for each overtime line.
- Step 6: writing the threshold as `<` puts the entries of exactly half an hour among the longer ones, where 83 lack approval instead of 3.
- Step 7: comparing regular hours alone finds 95 surge days, not 93.

**The checkpoint to look for.** The eight bullets. A strong student says surge-day records cannot show the hours were worked as recorded, and does not say they were not.

![The growth of surge days, for the discussion of the audit's central finding.](../figures/chapter-12-sql-audit-analytics/IF-12-0-C.pdf)

## Difficult ideas and misconceptions

**A clean result needs a test that could fail.** Tutorial 12.1 Steps 4 and 6, Question 2. An anti-join with the wrong join, or run on the wrong population, returns no rows. Ask: what would this test return if the control had failed? A positive control, a planted known exception, answers it.

**Two records can agree and omit the same thing.** Tutorial 12.1 Steps 2, 7 and 8, Question 1. Registers and ledger both record wages when paid. Ask: what does neither record contain?

**Existence runs one way, completeness the other.** Question 3, Tutorial 12.1 Step 3. A completeness test finds only documents that were recorded. Ask: which table is the left side?

**An exception is not a finding.** Exercises 12.1 and 12.5. Eight invoices dated before shipment change no year's revenue, and the supplier invoice that crosses a year-end was accrued. Ask: what is the effect, and what is the disposition?

**Cutoff has a direction.** Question 5, Exercise 12.1. Cost posts at shipment and revenue at the invoice, so margin moves by the whole revenue amount, and the unbilled shipments change the sign of the last year.

**Sum before you compare, and fix the tolerance first.** Questions 6 and 7, Tutorial 12.2. Receipt lines and invoice lines do not pair row by row. A tolerance set after the result is a choice of answer. Goods received and not invoiced are an accrual, not an exception (question 8).

**Concentration is a design risk.** Questions 10 and 11, Exercises 12.4 and 12.5. An approval that never changes a request and comes from one person looks like a record more than an authorization, until the requests and the evidence of review show otherwise. Ask: what could the approver have stopped, and what else would catch an error the approver missed?

**An expectation from the system's own rates recalculates.** Question 15, Tutorial 12.3 Step 5. The pay fits the hours and rates on file; whether the hours were worked is another question.

**A pattern is not proof.** Questions 9 and 12, Exercise 12.3. Surge-day records look entered in bulk and late time is parked on finished operations. Neither shows that hours were not worked, and records that agree do not show that they were. Ask: what would corroborate them from outside the payroll system?

**Plausible numbers from a wrong query.** Questions 4, 13 and 14, Exercise 12.6. A self-join pairs each row twice, a LAG partition skips a boundary, and a first character reads a tenth digit. Ask: what known answer checks this?

## Discussion prompts

1. **The ledger reconciles and traces, yet every year-end is misstated. Is the ledger reliable?** A good discussion reaches what a reconciliation compares, timing, and the missing accrual.
2. **Every hourly employee clocked the same hours on dozens of days. What do you conclude, and what do you ask for?** It reaches "cannot show they were worked", corroboration from outside the payroll system, and not accusing.
3. **A test returns no rows. When do you accept that?** It reaches positive controls, reconciled populations and the logic of the join.
4. **One person approves nearly every order, register and overtime request. Exception or design?** It reaches concentration, segregation of duties and who reviews the reviewer.
5. **The tolerance is two percent or three. Who sets it, and when?** It reaches policy, advance choice and follow-up capacity.
6. **The staff accountant of Chapters 9 to 11 and the auditor of this chapter reach different strengths of conclusion. Why?** It reaches independence, and which conclusions the tests left standing and which need corroboration.
7. **Do the standards still fit?** It reaches the plant-level totals that reproduce, time paid beyond the work, the calendar effect, and what agreeing records cannot show about the work the output required, the answer to Chapter 9.

## Using the exercises

All six exercises are SQL scripts with a model answer in Chapter12-exercises-sql.zip. The outcome column uses the numbers of the list above.

| Exercise | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 12.1 Cutoff at Each Year-End | Financial | SQL | 120 | Advanced | 1, 2 |
| 12.2 Aging the Open Balances | Financial | SQL | 110 | Advanced | 1, 3 |
| 12.3 Where Did the Time Go? | Managerial | SQL | 100 | Intermediate | 5 |
| 12.4 Is the Overtime Approval Doing Its Job? | Managerial | SQL | 80 | Basic | 4, 5 |
| 12.5 Who Was Paid, and Who Approved the Pay? | Auditing | SQL | 80 | Intermediate | 4, 5 |
| 12.6 Chapter 8's Tests in SQL | Auditing | SQL | 120 | Advanced | 6 |

**Assignment bundles**

- *Three tracks.* Financial students do Exercises 12.1 and 12.2, managerial students 12.3 and 12.4, auditing students 12.5 and 12.6. A swap of memos lets each track hear the others.
- *One exercise a session.* Take the basic one first: 12.4, 12.5, 12.3, 12.2, 12.1, 12.6.
- *A light load.* Exercises 12.1 and 12.5 take about three and a half hours and cover outcomes 1, 2, 4 and 5.

**Grading and discussion.** Requirements (1) to (4) of Exercises 12.1 to 12.5 and the tests of 12.6 suit grading from the script and the row counts. The memos, findings and notes suit class discussion. Collect the script, not a screenshot: its comment lines show the population and the expected result.

## Multiple-choice questions

Key: 1 A, 2 D, 3 C, 4 C, 5 B, 6 A, 7 D, 8 C, 9 A, 10 D, 11 C, 12 B, 13 B, 14 A, 15 B.

| Question | Answer | Rationale |
|---:|:---:|---|
| 1 | A | agreement with the ledger supports the population's completeness before testing; it cannot show that neither record omits a transaction. |
| 2 | D | postings whose SourceDocumentID matches no payment point to nothing. |
| 3 | C | completeness asks whether every document was posted. |
| 4 | C | UNION ALL matches columns by position and names them after the first query, without an error. |
| 5 | B | with revenue recognized on delivery, a December delivery posted in January is a cutoff error. |
| 6 | A | quantities must be summed to the purchase order line before comparing. |
| 7 | D | the tolerance comes from policy and is set and documented in advance. |
| 8 | C | two records agreeing supports the balance; completeness also needs a search for unrecorded liabilities. |
| 9 | A | identical times for a whole plant suggest bulk entry; the records cannot show the hours were worked. |
| 10 | D | one approver for nearly everything can indicate a design weakness. |
| 11 | C | a pattern suggests a policy threshold, to be confirmed; test above it. |
| 12 | B | time charged to finished operations cannot reliably be tied to the operations that used it; the share is of the direct hours recorded against operations, not of the variance or the pay. |
| 13 | B | the condition keeps each pair once and excludes a payment paired with itself. |
| 14 | A | scientific notation starts with the first significant digit, given enough decimals that rounding cannot carry it to the next power of ten. |
| 15 | B | a recalculation from the hours and the rates on file tests the pay for the hours; it cannot show that the hours were worked or the rates authorized. |

**Questions where a wrong option tempts**

- **Question 2.** Option A reverses the direction: the postings have no payment, not the payments no posting.
- **Question 3.** Option A is the existence test.
- **Question 4.** Option B says SQLite stops; it stacks by position.
- **Question 7.** Options A and B reward more or fewer exceptions; the policy sets the tolerance.
- **Question 8.** Option A claims completeness; agreement supports the balance only.
- **Question 9.** Options B and D overclaim in either direction.
- **Question 11.** Option A reports every short entry; confirm the policy first.
- **Question 12.** Options A and C claim an overstated variance or unworked pay.
- **Question 15.** Option A treats agreement with an expectation as proof the hours were worked.

Use the questions as a ten-minute quiz, as clickers, or as a review. Questions 1 to 5 make a quiz of reconciliation, tracing and cutoff, questions 6 to 8 of the match, questions 9 to 12 and 15 of the records behind a cost, and questions 13 and 14 of the SQL of the library.

## Connections

**Builds on.** Chapter 1's table groups and source-document traceability and Chapter 3's trace of one sale; Chapter 6's substantive analytical procedure; Chapter 8's tests (Exercises 12.2 and 12.6); Chapter 10's anti-joins, fan-out and data profile, and Exercise 10.5's six postings; Chapter 11's windows, CTEs, views and pay calendar; Exercises 5.2, 6.1 and 10.1, whose invoices dated before shipment test L5 classifies; and Chapter 9's question about the variance, which the chapter answers.

**Later chapters.** The Part III case plans the plant's year and adjusts the statements from these findings. Chapter 16 rebuilds the exception register in Power BI.

**Appendices.** The quick reference lists UNION ALL, the self-join and LAG beside Excel and DAX. **Appendix D** maps each exercise to the professional frameworks; each exercise guide names the competencies it practices.
