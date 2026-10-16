# Comprehensive Case, Part II: Deciding on the 2027 Promotion Calendar

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Tools | Excel |
| Time | About 150 minutes of class time |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## At a glance

| | |
|---|---|
| Part | Part II, Accounting Analytics with Excel. The case closes the Part and integrates Chapters 4 to 8 |
| Analytics types | The case text does not label them. Read together: descriptive (Requirement 2), diagnostic (Requirements 3 and 5), predictive and prescriptive (Requirements 4 and 6) |
| Tools | Excel only: Power Query, PivotTables and charts, SUMIFS and lookup formulas, a data table, Goal Seek and named cells |
| Components | Six requirements, no tutorials, no milestones and no multiple-choice questions; the deck has 33 slides |
| Files students need | CharlesRiver.xlsx, from the Downloads page; the workbook they build, `Charles River Promotion Case.xlsx`; their commission rate from Tutorial 7.3. The Downloads page lists no start file; its solution is PartII-case.zip (Excel) |
| Deliverable | A memorandum of at most two pages to the controller, a one-page appendix of five exhibits, and the workbook with its Documentation sheet complete |
| Time | Class: about 150 minutes in Plan A. Students: about eight hours, from 60 minutes for Requirement 6 to 100 for Requirement 4 |

The case depends on these conditions of the data, all visible in the workbook:

- The company ran nine promotions in three fiscal years, one collection, one item group and one customer segment a year. Of the order lines, 1,650 carry a promotion, and no other line has a discount.
- Revenue is recorded net of every price reduction. The discount account exists and has no postings, so the ledger cannot show what the promotions cost.
- The recorded end dates of the collection promotions fall on or before their start dates, so none of their lines was ordered inside them.
- Volume in each promotion's months is within the scope's normal month-to-month variation on an informal screen, and far below the increase the promotion would need to pay for itself.
- The 2027 budget prices every month alike, plans no promotion, and plans several times the volume actually ordered.
- One employee approved every promotion and every approved price override.

## What students should be able to do afterward

1. Build and document a refreshable workbook from several Tables with Power Query, and check it against its sources with control totals. Practiced in Requirement 1.
2. Quantify a cost that no account records, tie billed revenue to the ledger, and say where the cost does and does not appear. Practiced in Requirement 2.
3. Test a claimed effect against an expectation and the normal variation of the data, and state what the data cannot show. Practiced in Requirement 3.
4. Model a decision with a contribution margin model, a data table and Goal Seek, and cost it against a plan on a justified volume. Practiced in Requirement 4.
5. Test controls line by line, use evidence outside the record under test, and classify each exception provisionally as design or operation, with the evidence that would confirm it. Practiced in Requirement 5.
6. Write a short memo that recommends an action, with exhibits a reviewer can trace. Practiced in Requirement 6.

## Preparing to teach

**Before the first class**

- Check the software. The model answer uses functions of Excel for Microsoft 365 (FILTER, LET, XLOOKUP, SORT, UNIQUE, CHOOSECOLS, HSTACK), and the README of the solution file says that older versions of Excel lack some of them. Some requirement guides give a simpler route; any formula that gives the same answer is fine.
- Ask students to confirm the path to CharlesRiver.xlsx and to keep the chapter workbooks unchanged: the case builds a new workbook beside it. A student who skipped Tutorial 7.3 needs the commission rate, which Requirement 1 shows how to recompute.
- Build your own answer once, or open the solution workbook. Its queries read C:\CharlesRiver\CharlesRiver.xlsx; **Data > Get Data > Data Source Settings > Change Source** points them at your copy, and **Data > Refresh All** refreshes them. Note how long the refresh takes.
- Open the deck. Slides 3 to 6 set out the decision, the deliverable and the criteria, which are the six bullets of "What a Strong Submission Includes"; read them aloud at kickoff.

**Pitfalls that cost class time**

- Three columns of PromotionProgram share names with Item and Customer. Unrenamed, the merge stops. Slide 15 is the Watch out; repeat it at the first merge.
- Power Query types Discount as a whole number from the first 200 rows, which carry no discount, and every rate rounds to 0. **Replace current** fixes it. The no-discount checks then pass trivially, because every rate is 0.
- The order date, the invoice date and the ledger's posting date answer different questions (slides 16 and 17). Students use whichever they have open, and the tie to the ledger in Requirement 2 needs the last two.
- A data table's input cells must sit on the sheet that holds the table, so the proposal's rates on Parameters cannot be the input cells.
- A PivotTable ignores the worksheet's filters. A student who filters `OrderLines` to one scope and builds a PivotTable still sums every scope.
- Goal Seek leaves the changing cell at the value it found unless the student cancels or resets it.

## Teaching approaches

**Plan A: take-home work with four class touchpoints (150 minutes in class).** It fits a lecture course that wants the case done mostly outside class, and it catches the errors that compound: the workbook, the volume test and the controls. The risk is a late start, so assign Requirement 1 at kickoff.

| Touchpoint | Minutes | Activity | Slides |
|---|---:|---|---|
| 1. Kickoff | 10 | The decision, the deliverable and the criteria | 3 to 6 |
| 1. Kickoff | 10 | The situation and the controller's four questions | 8 to 10 |
| 1. Kickoff | 5 | The queries and the Watch out | 13 to 15 |
| 1. Kickoff | 5 | The date check; assign Requirements 1 and 2 | 16, 17 |
| 2. Checkpoint | 15 | Requirement 1: compare completeness checks and resolve disagreements | 20 |
| 2. Checkpoint | 20 | Requirement 2: gross to net, the tie and why the ledger hides the cost; assign Requirements 3 and 4 | 21 |
| 3. Checkpoint | 20 | Requirement 3: the largest difference, and whether it is big | 22 |
| 3. Checkpoint | 15 | Requirement 4: break-even, data table, the check question | 23 to 25 |
| 3. Checkpoint | 5 | Assign Requirements 5 and 6 | |
| 4. Debrief | 20 | Requirement 5: tests, evidence and dispositions | 26 to 28 |
| 4. Debrief | 15 | Requirement 6: read two openings, and state the recommendation | 29, 30 |
| 4. Debrief | 10 | Looking ahead to Part III | 31 to 32 |
| | 150 | Total | |

**Plan B: lab sessions (three sessions of 90 minutes, 270 minutes in all).** Students work in class and you circulate. It fits a computer lab or a course that does not want to depend on outside work. The budgets, the approvals and the memo go home, and the memo is collected the week after.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 15 | Kickoff: the decision, the criteria and the Watch out | 3 to 15 |
| 1 | 45 | Requirement 1: the queries and the Parameters sheet | 20 |
| 1 | 30 | Requirement 1: completeness checks | 20 |
| 2 | 30 | Requirement 2: PivotTable, gross to net and the tie | 21 |
| 2 | 45 | Requirement 3: months, grids and the comparison | 22 |
| 2 | 15 | Requirement 3: first orders of customers | 22 |
| 3 | 45 | Requirement 4: the model, the data table and Goal Seek | 23 to 25 |
| 3 | 30 | Requirement 5: the line tests and the evidence | 26 to 28 |
| 3 | 15 | Plan the memo from the Requirement 6 outline | 29 |
| | 270 | Total | |

**Plan C: memo workshop (75 minutes).** Students arrive with Requirements 1 to 5 done. It fits an upper-level or graduate class and moves the learning to the writing. Its risk is that an early mistake is found late, so collect the tables of Requirements 2 to 5 the day before and mark them.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval: each pair states the cost by year, the largest difference, the break-even range and the exceptions | 19 |
| 10 | Each pair states its recommendation in one sentence; the room compares | 29 |
| 25 | Draft the opening and the Auditing section in pairs, from the Requirement 6 outline | 29 |
| 25 | Swap drafts and review them against the Requirement 6 grading guide | 30 |
| 5 | Looking ahead to Part III | 31 to 32 |
| 75 | Total | |

## Difficult ideas and misconceptions

- **Three dates, three purposes.** A promotion applies by order date, billed revenue follows the invoice date, and the ledger records each invoice on its posting date. The first two show as a Q4 share of 51% by order date against 64% by invoice date, and as 160 lines of the fall promotion invoiced after it ended. Ask which date answers the question in hand, and which one the ledger used.
- **List amount measures volume; net amount measures revenue.** A student who measures volume at LineTotal sees nearly every promotion fall, from -30.2% to +0.9%. Ask what the discount does to the number in the promotion's own months.
- **A difference is not an increase until it is compared with normal variation.** A two-month total's difference read against one month's standard deviation makes promotion 2 look unusual. The average month read against the monthly variation, or the total against the variation scaled to its months, does not. Either like-for-like comparison is fine, and both are an informal screen, not a test of significance. Ask how much a two-month total varies.
- **A break-even is a threshold, not a forecast.** Students write that the promotion will lift volume by the break-even. Put the break-even beside the measured difference and ask which is evidence.
- **No evidence of an effect is not evidence of no effect.** The volume comparisons describe the orders and cannot show what would have sold without a promotion. The first-order test finds no promotional first order, but the data begins in the first year and almost no new customers appear in it. Ask what each test could have shown.
- **An exception is a symptom.** The failing dates look like unauthorized discounts. The orders and the budgets suggest the promotion ran when it was meant to and its end date was entered wrongly, which the approved campaign calendar would confirm. Ask which other records speak to the question, and which would settle it.
- **A vacuous test is not a clean result.** A completeness test on the recorded dates of the 3 failing promotions examines no lines and returns zero. Ask how many lines it looked at.
- **The ledger cannot show what it does not record.** Students look for the discounts in the income statement. Revenue is net, so there is nothing to find; the cost lives in a schedule.

The timeline separates the two dates and is worth putting on the board before Requirement 2.

![The two dates of a promotion, the order date that sets its months and the invoice date that sets when the discount reaches revenue.](../figures/case-part-2/IF-C2-0-B.pdf)

## Discussion prompts

1. The ledger records revenue net of discounts. Should Charles River record promotional discounts in the discount account? A good discussion reaches presentation versus net income, and what a reader of the statements would gain.
2. A promotion's months show a gain of a tenth. What would you have to believe to call it a success? A good discussion reaches variation, a comparison group and the break-even.
3. The sales team says promotions bring in new customers. What would the data have to show for you to agree? A good discussion reaches first orders, the start of the data and the limits of the test.
4. The sales manager approves promotions and price overrides. Who should, and what does a second approval cost? A good discussion reaches segregation of duties and what finance would review.
5. The three collection promotions fail the date test, yet the discounts look intended. Do you report them, and how do you word the finding? A good discussion reaches evidence, provisional wording and design versus operation.
6. If you recommend a small test, how would you design it? A good discussion reaches a comparison scope, a stated expectation and a review date.
7. The memo has two pages. What goes in the appendix, and what stays out of the memo entirely? A good discussion separates the decision from the working papers.

## Using the requirements

| Requirement | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1. Build and validate the case workbook (Chapters 4 and 5) | General | Excel | 90 min | Intermediate | 1 |
| 2. Measure what the promotions cost (Chapter 6) | Financial | Excel | 75 min | Intermediate | 2 |
| 3. Test whether the promotions brought in sales (Chapters 6 and 7) | Managerial | Excel | 90 min | Advanced | 3 |
| 4. Model the proposed calendar (Chapter 7) | Managerial | Excel | 100 min | Advanced | 4 |
| 5. Test the controls over promotions (Chapter 8) | Auditing | Excel | 80 min | Intermediate | 5 |
| 6. Write the decision memo | General | Written, with Excel exhibits | 60 min | Advanced | 6 |

Every requirement is part of the case, and each depends on the first. The figure shows how their results feed the memo and its appendix.

![How the six requirements build the memo and its appendix, and the chapter each one draws on.](../figures/case-part-2/IF-C2-0-A.pdf)

Three bundles:

- **The full case (the default).** All six requirements, graded with the rubric below. About eight hours.
- **A shorter version.** Requirements 1 to 4 as a workbook, graded on the numbers, and a one-page memo on Requirement 6's financial and managerial sections. It skips the controls.
- **Teams of three.** One workbook and one memo for the team, with one student leading each perspective (Requirement 2 for financial, Requirements 3 and 4 for managerial, Requirement 5 for auditing), and an individual one-page reflection on the recommendation.

The deck's check slides on dates, break-even and design versus operation suit class discussion. Requirements 1, 2 and 5 suit grading from the tables, Requirements 3 and 4 from the workbook, and Requirement 6 from the memo.

## Assessment rubric

| Requirement | Weight | What carries the points |
|---|---:|---|
| 1. Build and validate | 10 | Named queries, types corrected, control totals that agree, a complete Documentation sheet |
| 2. Cost and ledger | 15 | The cost by year, a schedule that foots, a tie to the ledger and the reason the ledger hides the cost |
| 3. Did promotions bring sales | 15 | List-price volume, two expectations, variation compared like for like and the limits of the data |
| 4. Model the calendar | 20 | Break-evens, data table, Goal Seek, the budgets and a cost by quarter on a stated volume |
| 5. Controls | 15 | Four guarded tests, evidence for the likely cause, provisional dispositions and conditions |
| 6. The memo | 25 | Organization, accuracy, judgment, length and a usable recommendation |
| Total | 100 | |

Four criteria run through every requirement.

| Criterion | Full credit looks like | Assessed mainly in |
|---|---|---|
| Accuracy | Totals tie to the sources and the ledger, formulas right, no silent type errors | Requirements 1, 2 and 4 |
| Evidence | Every number in the memo traces to a query, a cell or an exhibit, and exceptions have evidence from outside the record tested | Requirements 3, 5 and 6 |
| Judgment | Differences judged against variation, break-even read as a threshold, design and operation classified provisionally, limits stated | Requirements 3, 4 and 5 |
| Communication | A memo organized by the controller's questions, within two pages, ending in a recommendation | Requirement 6 |

Each requirement guide has its own grading table out of 100; scale it by the weight above to place it in the case grade.

## Connections

**Builds on.** Chapter 4 supplies the new workbook, Power Query and the Documentation sheet (Tutorials 4.1 and 4.3, Exercises 4.2 and 4.6). Chapter 5 supplies the merges and the two dates of a line. Chapter 6 supplies PivotTables, the gross-to-net view and the tie from the ledger to the statements (Exercise 6.1, with its cutoff invoices). Chapter 7 supplies expectations, the contribution model, the data table and Goal Seek (Tutorial 7.3), and Exercise 7.6 shows why the budget's volume cannot be trusted. Chapter 8 supplies audit tests and dispositions (Exercise 8.6). The Part I case supplies the memo form. The finished guides for Chapters 4 to 8 hold the tutorial and exercise detail each requirement here relies on.

**What builds on it.** Part III asks the same kinds of questions of the database with SQL: a join and a grouped query do the work of a merge and a PivotTable, and Chapter 12 tests the revenue cutoff across the whole window in SQL. Part IV turns evidence like this into reports that management can explore.

**Appendix D** maps each requirement to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each requirement guide names the competencies it practices.
