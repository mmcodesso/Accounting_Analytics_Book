---
uses: [ch18.g0, ch18.m1, ch18.m2, ch18.m3, ch18.m4]
title: 'Chapter 18: Make, Buy, or Reprice'
kind: case-notes
unit: '18'
minutes: 240
tool: mixed
figures:
  - id: IF-18-0-A
    kind: diagram
    purpose: How the ten requirements, the three files and the four milestones fit together, for the kickoff.
    shows: "Four columns, one for each phase, holding ten boxes for the requirements in order (1 to 3; 4 and 5; 6 to 8; 9 and 10). Each box carries a tag for its tool: SQL, Excel or Power BI, two tags where a requirement uses more than one. Arrows run from the SQL results to the workbook, from the workbook's item costs to the explorer, and from all three files to the memo. Four checkpoints, one for each milestone, sit under the columns."
    data: none; the boxes and tags come from the case's requirements and its tools table.
  - id: IF-18-0-B
    kind: chart
    purpose: The same inputs to the clearing account cut three ways, the picture behind the three costing views.
    shows: "Three horizontal bars of equal length, each the year's inputs to the clearing account. Standard: the part released to products at standard, the rest the variance. Actual absorption: one segment, every dollar spread over the units made. Time-driven: the products' conversion and the unused capacity, with the crew's part of the unused capacity marked. Dollar labels on the segments."
    data: The inputs to the clearing account, the standard cost released, the products' conversion and the unused capacity (Requirements 2 and 4).
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% macro sg(x) %}{{ "-" if x < 0 else "+" }}${{ (x|abs)|money }}{% endmacro %}
{% set c = ch18_g0 %}
{% set s = c.s %}
{% set m1 = ch18_m1 %}
{% set m2 = ch18_m2 %}
{% set m3 = ch18_m3 %}
{% set m4 = ch18_m4 %}
# Chapter 18: Make, Buy, or Reprice

{{ header() }}

## At a glance

| | |
|---|---|
| Part | Part V, Capstone Cases. The case is an independent final-project option: it asks for nothing from another capstone, and the Part III and Part IV case files are only an optional head start |
| Analytics types | Descriptive (Requirements 1 and 3), diagnostic (2 and 4), predictive (7 and 8) and prescriptive (the make, buy and reprice decisions, the standards and the memo) |
| Tools | SQL in DB Browser for SQLite, Excel (Goal Seek, Data Tables and, optionally, Solver) and Power BI Desktop. Where the choice is clear the requirement says why a tool fits; where it is not, students choose and explain |
| Components | Ten requirements in four phases, with a milestone after each; no tutorials, exercises or questions. The deck has {{ c.slides }} slides. The model answer is three files: MakeBuy.sql ({{ c.n_queries }} queries), Make Buy Reprice.xlsx ({{ c.n_sheets }} worksheets) and the Power BI project Product Costs ({{ c.n_pages }} pages, {{ c.checks }} checks) |
| Files students need | CharlesRiver.sqlite, copied as CharlesRiver_Capstone.sqlite; CharlesRiver.xlsx; and the three files they build. Solutions: Chapter18-capstone-sql.zip, Chapter18-capstone-excel.zip and Chapter18-capstone-pbi.zip |
| Deliverables | The script; the workbook; the explorer; a memo of at most two pages, including the decision table, with at most three pages of exhibits |
| Time | Class: about {{ meta.minutes }} minutes in Plan A. Students: a planning estimate of {{ c.required }} for the required work, from 90 minutes for Requirements 1, 3 and 10 to 180 for Requirement 4, plus {{ c.solver_minutes }} minutes for the optional growth test. The estimates assume students fluent in the prerequisite tools, are not measured times, count class work toward the total, and leave setup and debugging to be budgeted apart |

The case depends on these conditions of the data, all visible in the files students build:

- The manufactured furniture earns {{ m1.g0.m_std|pct(2) }} at standard and {{ m1.g0.m_year|pct(2) }} once the year's manufacturing variance of ${{ m1.variance|money }}, equal to the ledger's variance account, is charged; the purchased furniture earns about its standard margin.
- The year's inputs to the clearing account are ${{ m1.inputs|money }} against ${{ m1.released|money }} released at standard; the plant uses {{ m1.use|pct(1) }} of its practical capacity.
- Payroll posts on its pay dates, so some months carry a third payroll, and the first month of the data is a start-up month. The records end on different dates: invoices {{ c.dt.invoice }}, closes {{ c.dt.close }}, time records {{ c.dt.time }}.
- The dataset keeps no history of its master data, so "prices and standards did not change" can be supported by the records but not proved.
- The quote, the margin floor and the 2028 price lists are the case's assumptions, not data.

## What students should be able to do afterward

1. Reconcile a cost study to the ledger, test the premises behind a claim about costs, and classify the plant's costs as varying, committed or unused, with evidence. Practiced in Requirements 1, 2 and 3.
2. Compute standard, absorption and time-driven costs for product families, and say which question each answers. Practiced in Requirements 4 and 5.
3. Evaluate a supplier's quote on relevant costs, separating the costs that stop from those that stay, and value the capacity that buying would free. Practiced in Requirements 6 and 7.
4. Analyze a price increase with contribution margins and the volume it can lose, and judge the evidence on how customers respond to price. Practiced in Requirement 8.
5. Propose standard costs on a stated capacity, measure their effect on statements already issued, and recommend how to report it. Practiced in Requirement 9.
6. Choose SQL, Excel or Power BI for each step, and write a recommendation, family by family, that two decision makers who disagree can act on. Practiced in Requirements 1 and 5 (the tool choices) and in Requirement 10.

## Preparing to teach

**Before the first class**

- Check the software. Students need DB Browser for SQLite, Excel for Microsoft 365 (the model workbook uses XLOOKUP, LET and FILTER; Solver only for the optional part of Requirement 7) and Power BI Desktop, which runs only on Windows. Students on a Mac need a Windows computer for Requirement 5.
- Open the model answer as Opening a Companion File on the Downloads page describes. Product Costs reads two workbooks, CharlesRiver.xlsx and Make Buy Reprice.xlsx, from one folder: copy both there or use **Change Source**, and refresh once before class.
- In **DAX query view**, run the Checks tab: all {{ c.checks }} rows should agree. Run MakeBuy.sql top to bottom on a copy of the database; two queries save views.
- Run Goal Seek and Solver once yourself. The workbook holds their results and the saved Solver models, but the notes' optimum was computed outside Solver, so rerun **Data > Solver** on a growth sheet and compare.
- Open the deck. Slides {{ s.criteria }} set out the criteria, which are the seven bullets of "What a Strong Submission Includes", and slides {{ s.flow }} show the make-or-buy test in three stages.

**Pitfalls that cost class time**

- Fan-out (slide {{ s.r1 }}). One join chain from the sales lines to the closes multiplies the variance by a large factor. Ask students for the ledger's total before they read a margin.
- Units (slides {{ s.watch }}). Quantities are fractional, and the variance of the year's closes includes earlier work. A margin divided by the units sold coincides with the whole-year margin, so students think they have two measures.
- Recorded time (slides {{ s.r3 }} and {{ s.watch }}). Recorded direct time exceeds one work center's capacity; routing time does not.
- Payroll dates (slide {{ s.r2 }}). Grouping payroll by the period's month looks better and no longer ties to the ledger.
- A missing year filter (slides {{ s.r4 }} and {{ s.r5 }}). Item costs are one year's, sales are three.
- Absorption as a relevant cost (slide {{ s.spiral }}). It includes costs that do not stop when a family is bought. The make-or-buy answer turns on the crew, which belongs to the production manager.
- Statements (slides {{ s.r9 }}). A plan for the next year applied to earlier stock is a sensitivity, not a finding of error; the memo must name the evidence that would show an error.
- Wording. Both decision makers are right about part of the cost. The memo should say so in their terms.

{{ figure('IF-18-0-B') }}

## Teaching approaches

**Plan A: take-home work with five class touchpoints ({{ meta.minutes }} minutes in class).** It fits a course that wants the work done outside class and catches the errors that compound: the fan-out, the units, the crew assumption and the standards. The risk is a late start, so assign Requirements 1 to 3 at the kickoff. Class work counts toward the students' hours.

| Touchpoint | Minutes | Activity | Slides |
|---|---:|---|---|
| 1. Kickoff | 10 | The question, the deliverables and the criteria | {{ s.kick }} |
| 1. Kickoff | 25 | The situation and the data, with the two Watch outs | {{ s.situation }}, {{ s.data }} |
| 1. Kickoff | 15 | Set up the files; choose the tool for each step | {{ s.setup }} |
| 2. Milestone 1 | 15 | The family results, reconciled to the variance account | {{ s.r1 }} |
| 2. Milestone 1 | 15 | The overhead taken apart | {{ s.r2 }} |
| 2. Milestone 1 | 10 | The capacity table; self-check | {{ s.r3 }}, {{ s.m1 }} |
| 3. Milestone 2 | 15 | Three costing views and what each leaves out | {{ s.views }} |
| 3. Milestone 2 | 15 | The three costs and the unused capacity | {{ s.r4 }} |
| 3. Milestone 2 | 10 | The explorer | {{ s.r5 }} |
| 3. Milestone 2 | 10 | Check your understanding; self-check | {{ s.check2 }}, {{ s.m2 }} |
| 4. Milestone 3 | 15 | The make-or-buy test in three stages | {{ s.flow }} |
| 4. Milestone 3 | 15 | The decision, family by family; absorption is not relevant | {{ s.r6 }}, {{ s.spiral }} |
| 4. Milestone 3 | 10 | Freed capacity | {{ s.r7 }} |
| 4. Milestone 3 | 10 | Prices; check your understanding; self-check | {{ s.r8 }}, {{ s.check3 }}, {{ s.m3 }} |
| 4. Milestone 3 | 5 | Assign Requirements 9 and 10 | {{ s.p4g }} |
| 5. Debrief | 20 | The standards and the statements | {{ s.r9 }} |
| 5. Debrief | 15 | The memo | {{ s.r10 }}, {{ s.m4 }} |
| 5. Debrief | 10 | Looking ahead | {{ s.ahead }} |
| | {{ meta.minutes }} | Total | |

**Plan B: lab sessions (four sessions of 150 minutes, 600 minutes in all).** Students work in class on the data-heavy phases and you circulate. It fits a computer lab. Requirements 6 to 10 are done outside class; use touchpoints 4 and 5 of Plan A for them, 100 more minutes in class and 700 in all.

| Session | Minutes | Activity | Slides |
|---|---:|---|---|
| 1 | 30 | Kickoff: deliverables, criteria and the two Watch outs | {{ s.kick }}, {{ s.watch }} |
| 1 | 120 | Requirement 1 | {{ s.r1 }} |
| 2 | 150 | Requirement 2: the extracts, the tests and the classification | {{ s.r2 }}, {{ s.m1 }} |
| 3 | 60 | Requirement 3 | {{ s.r3 }} |
| 3 | 90 | Requirement 4: the assumptions, the pay class and the item costs | {{ s.views }}, {{ s.r4 }} |
| 4 | 60 | Requirement 4: the reconciliation, the summary and the Data Table | {{ s.r4 }} |
| 4 | 90 | Requirement 5: the model and the switching measure | {{ s.r5 }}, {{ s.m2 }} |
| | 600 | Total | |

**Plan C: decision workshop (90 minutes).** Students arrive with Requirements 1 to 9 done. Groups of three play the CFO, the production manager and the controller. It fits an upper-level or graduate class and moves the learning to the negotiation. The risk is an early error found late, so collect the workbook the day before and read its make-or-buy sheet.

| Minutes | Activity | Slides |
|---:|---|---|
| 10 | Retrieval: which cost answers each question | {{ s.check2 }}, {{ s.check3 }} |
| 20 | Each group states its recommendation in one sentence per family; the room compares | {{ s.r6 }} |
| 30 | Negotiate the crew assumption: the CFO and the production manager argue from the same table | {{ s.flow }}, {{ s.r7 }} |
| 20 | Revise the decision table and the one decision left to the production manager | {{ s.r10 }} |
| 10 | Looking ahead | {{ s.ahead }} |
| 90 | Total | |

## Milestone guide

Students hand in a milestone, and you may then release its checkpoint values so an early error does not carry through the case. A quick check for each is to compare one or two numbers before reading anything else.

### Milestone 1: What the records show

Students hold the family results reconciled to the variance account, the monthly tests with each input classified, and the capacity table.

| Quantity | Value |
|---|---|
| Furniture margin: standard; per unit completed; year's variance | {{ m1.g0.m_std|pct(2) }}; {{ m1.g0.m_unit|pct(2) }}; {{ m1.g0.m_year|pct(2) }} |
| Lighting and Textiles with the year's variance | {{ m1.rest[0].m_year|pct(2) }}; {{ m1.rest[1].m_year|pct(2) }} |
| Variance of the closes, equal to the ledger | ${{ m1.variance|money }} |
| Inputs to the clearing account; released at standard | ${{ m1.inputs|money }}; ${{ m1.released|money }} |
| r with output: Factory Overhead entries; payroll; direct regular; indirect regular | {{ m1.r_fo|num(2) }}; {{ m1.r_pay|num(2) }}; {{ m1.r_dreg|num(2) }}; {{ m1.r_ireg|num(2) }} |
| Practical capacity used | {{ m1.use|pct(1) }} |

**Quick check:** the families' variance equals the ledger's before anything else is read. Payroll does not move with output, and the Factory Overhead entries do.

### Milestone 2: What a product costs

Students hold three costs for every item, the unused capacity reconciled to the inputs, and the explorer with its Tests tab.

| Quantity | Value |
|---|---|
| Committed cost; rate per practical hour; the crew's part | ${{ m2.committed|money }}; ${{ m2.td_rate|num(2) }}; ${{ m2.crew_rate|num(2) }} |
| Unused capacity: hours; cost | {{ m2.unused_h|num(1) }}; ${{ m2.unused|money }} |
| Time-driven margin: Furniture; Lighting; Textiles | {{ m2.groups[0].m_td|pct(2) }}; {{ m2.groups[1].m_td|pct(2) }}; {{ m2.groups[2].m_td|pct(2) }} |
| Explorer margins: standard; absorption; time-driven | ${{ m2.e.exact.std|money }}; ${{ m2.e.exact.absorp|money }}; ${{ m2.e.exact.td|money }} |
| Explorer revenue, finished goods | ${{ m2.e.rev|money }} |

**Quick check:** products plus unused capacity equal the inputs to the clearing account, with the setup-allocation difference as its own line. Each view's margin in the explorer equals the workbook's.

### Milestone 3: Make, buy, or reprice

Students hold a decision for every quoted family under both crew cases, the value of the freed capacity, and the price increases.

| Quantity | Value |
|---|---|
| Families to buy, and only with the crew reduced | {{ m3.buy|map(attribute='short')|join(', ') }} |
| Their annual effect; positions freed | {{ sg(m3.gain) }}; {{ m3.positions|num(2) }} |
| Two-year net, after tooling and severance | {{ sg(m3.net) }} |
| Buying them with the crew kept costs, a year | ${{ m3.kept_cost|money }} |
| Families that lose either way | {{ m3.lose|map(attribute='short')|join(', ') }} |
| Families below the floor; revenue from the increases | {{ m3.n_floor }}; {{ sg(m3.reprice) }} |
| The path that buys and reprices the rest: a year; once | {{ sg(m3.paths.buy) }}; ${{ m3.paths.once|money }} |

**Quick check:** a decision that does not say what happens to the crew is not yet a decision. The two-year net uses the quote's two fixed years, before taxes and without discounting.

### Milestone 4: Standards and the memo

Students hold the proposed rate with its comparisons, the effect on the statements already issued, and the memo.

| Quantity | Value |
|---|---|
| Proposed rate per standard hour; the current rate | ${{ m4.new_rate|num(2) }}; ${{ m4.current|num(2) }} |
| At the lower and higher normal capacity | ${{ m4.normal[0].rate|num(2) }}; ${{ m4.normal[1].rate|num(2) }} |
| With no indirect hours (a labor-content case) | ${{ m4.one_rate|num(2) }} |
| Revaluation of stock at each year-end | {{ sg(m4.stock[0].plan) }}; {{ sg(m4.stock[1].plan) }}; {{ sg(m4.stock[2].plan) }} |
| Income effect, the last two years | {{ sg(m4.incomes[0].amount) }}; {{ sg(m4.incomes[1].amount) }} |

**Quick check:** the revaluation is a sensitivity, not an error. The memo must say what evidence would show whether the old standards misstated the statements, and read the decision table and the production manager's decision first.

## Difficult ideas and misconceptions

- **Absorption is not a relevant cost.** It includes supervision, depreciation and the crew's idle hours, which do not stop when a family is bought. Ask which costs would stop, and what must happen for each to stop.
- **"Direct labor is variable."** Direct regular pay moves with output (r = {{ m1.r_dreg|num(2) }}) only because the same crew is recorded as direct when there is work. Ask what the indirect pay did over the same months.
- **An allocation is not a measurement.** A family's share of the overhead variance depends on the work order's actual labor, not on what the family consumed. Ask what the share would be if the labor were recorded differently.
- **Routing time against recorded time.** Recorded time says where hours were charged, not what the products needed. Ask which work center's recorded hours exceed its capacity.
- **Unused capacity cuts both ways.** It is not the products' fault, as the production manager says, and it is still a cost the plant pays. It is also an annual estimate from standard times, not a staffing plan. Ask who can act on it, and in which weeks and work centers the spare hours fall.
- **A threshold is not a forecast.** The volume an increase can afford to lose says nothing about how customers will respond, and the promotion screen cannot measure it. Ask what evidence a price test would add.
- **A sensitivity is not an error.** A plan for the next year applied to earlier stock shows what the standard would do, not that the statements were wrong. Ask what facts at the time would have given a different inventory.
- **One cost for every question.** Relevant costs decide make or buy, time-driven costs price, standards on normal capacity value inventory, and absorption fits none of them.

## Discussion prompts

1. Is Charles River selling below cost? A good discussion reaches the margins under all three views, that no item loses money, and why the answer depends on the question.
2. Whose reading of the overhead is right? A good discussion reaches the CFO's gap (the committed costs the standards leave out) and the production manager's point (idle capacity is not the products' fault, though it is still a cost).
3. When is buying right if the crew stays? A good discussion reaches the hours freed having another use, as growth would give them.
4. What would you need to believe for a price increase to pay? A good discussion reaches the break-even volume loss and the weak evidence on customers.
5. Should the standards change, and what should the shareholders hear? A good discussion separates a change in estimate from an error and names the evidence.
6. What does the memo leave to the production manager, and why? A good discussion reaches the crew decision and what it would cost.
7. Which tool did you choose for each step, and what would have changed with another? A good discussion reaches the reasons the requirements give.

## Using the requirements

| Requirement | Perspective | Tool | Time | Difficulty | Outcome |
|---|---|---|---:|---|---|
| 1. Test the CFO's numbers and the premises behind them (Chapters 9 to 11) | Managerial | SQL and Excel | {{ c.plan[1] }} min | Intermediate | 1, 6 |
| 2. Take the overhead apart (Chapters 7, 10, and 11) | Managerial | SQL and Excel | {{ c.plan[2] }} min | Advanced | 1 |
| 3. Measure the activities and the capacity (Chapters 10 and 11) | Managerial | SQL and Excel | {{ c.plan[3] }} min | Intermediate | 1 |
| 4. Compute three costs for each family (Chapter 7) | Managerial | Excel, SQL and Power Query | {{ c.plan[4] }} min | Advanced | 2 |
| 5. Build the explorer for the meeting (Chapters 13 to 15) | Managerial | Power BI | {{ c.plan[5] }} min | Intermediate | 2, 6 |
| 6. Decide make or buy, family by family (Chapter 7) | Managerial | Excel and SQL | {{ c.plan[6] }} min | Advanced | 3 |
| 7. Value the capacity that buying would free (Chapter 7) | Managerial | Excel and SQL | {{ c.plan[7] }} min | Intermediate | 3 |
| 8. Reprice the families below the floor (Chapter 7) | Managerial | Excel and SQL | {{ c.plan[8] }} min | Intermediate | 4 |
| 9. Revise the standards, and measure what they mean for the statements (Chapter 9) | Financial | Excel and SQL | {{ c.plan[9] }} min | Advanced | 5 |
| 10. Write the decision memo | General | Excel and a written memo | {{ c.plan[10] }} min | Advanced | 6 |

Every requirement is part of the case, and each phase uses what the one before found. The figure shows how the files feed one another and the memo.

{{ figure('IF-18-0-A') }}

Four bundles. Publish the deliverable and the rubric of the bundle you assign, because the weights below cover the full case, and have a reduced bundle's memo cover only what the bundle contains:

- **The full case (the default).** All ten requirements, graded with the rubric below. About {{ c.required }} of work, with the optional growth test on top.
- **A managerial accounting version.** Requirements 1 to 4 and 6 to 8, with the decision table and a one-page memo, in the script and the workbook only. It leaves out the explorer and the standards.
- **An analytics version.** Requirements 1 to 5 and 10: the costs, the explorer and a memo on what the three views show. It leaves out the decisions on the quote and the prices.
- **Teams of three.** One student leads each tool (SQL for Requirements 1 to 3, Excel for 4 and 6 to 9, Power BI for 5), the memo is shared, and each writes a one-page reflection on the crew assumption and explains in class one calculation that another member built.

The check slides suit class discussion. Requirements 1 and 3 suit grading from the script, because each ends in totals that agree or do not; Requirements 4 and 6 from the workbook; Requirement 5 from the Tests tab; Requirements 9 and 10 from the written work. A fast way to grade is to read the memo's decision table, then trace one number in each row back to the workbook.

## Assessment rubric

| Requirement | Weight | What carries the points |
|---|---:|---|
| 1. The CFO's numbers | {{ c.weights[1] }} | Family results without fan-out, three margins, the premise test and its limits, the tie to the variance account |
| 2. The overhead | {{ c.weights[2] }} | Extracts that tie, tests from the right month on, the pay-date grouping, each input classified with evidence |
| 3. Activities and capacity | {{ c.weights[3] }} | Setup and issue lines counted once, capacity and its shares, why routing time |
| 4. Three costs | {{ c.weights[4] }} | Formulas over named assumptions, the unused capacity as its own line, the reconciliation, the Data Table |
| 5. The explorer | {{ c.weights[5] }} | The switching measure, the year filter, the blank decided, the Tests tab |
| 6. Make or buy | {{ c.weights[6] }} | Relevant costs under both crew cases, one-time costs, break-even quotes, the terms left out |
| 7. Freed capacity | {{ c.weights[7] }} | Hours freed by work center, the comparison with unused capacity, the remaining families' cost |
| 8. Prices | {{ c.weights[8] }} | Floor prices, the volume each increase can lose, the evidence and its limits |
| 9. Standards | {{ c.weights[9] }} | The rate on normal capacity, the revaluation with its sensitivities, the evidence for error or estimate |
| 10. The memo | {{ c.weights[10] }} | A decision table, the page maximums, the crew decision left open, a usable recommendation |
| Total | 100 | |

Four criteria run through every requirement.

| Criterion | Full credit looks like | Assessed mainly in |
|---|---|---|
| Accuracy | Totals tie to the variance account and the inputs to the clearing account, with the units stated | Requirements 1 to 4 |
| Evidence | Every number traces to a query, a formula or a test; a different cost for each question; the limits of each test named | Requirements 2, 5, 8 and 9 |
| Judgment | The crew assumption explicit, the unused capacity treated as the plant's cost, error and estimate told apart | Requirements 6, 7 and 9 |
| Communication | A memo two people who disagree can act on, ending in what only the production manager can decide | Requirement 10 |

Each requirement guide has its own grading table out of 100; scale it by the weight above to place it in the case grade. Full credit goes to what the requirement asks. Named cells, Tables, documentation and the extensions are a plus, and a supported alternative (keeping all six families with staged increases, for example) earns the same credit as the model answer. A concise submission below the page maximums earns full credit.

## Connections

**Builds on.** Chapter 7 supplies regression, Goal Seek, Data Tables, Solver and the promotion lift; Chapters 9 to 11 the standard costs, the joins that fan out, the clearing account and the plant's hours; Chapter 5 the item-code structure; Chapter 6 the statements the last requirement returns to; Chapter 8 Exercise 8.6's price-list tests; Chapters 13 to 15 the model, the switching measure and the validation habit. The Part III case built the plan the assumptions table states, which students do not need to have done.

**What builds on it.** Nothing in the book depends on this case. The workbook and the explorer are the tools for the next round of quotes and price lists, which is the point of its Looking Ahead.

**Appendix D** maps each requirement to the CPA Evolution model curriculum, the IMA framework, the IFAC education standards and the AACSB standard. Each requirement guide names the competencies it practices.
