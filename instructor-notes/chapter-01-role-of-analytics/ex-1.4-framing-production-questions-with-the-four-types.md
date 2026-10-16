# Exercise 1.4: Framing Production Questions with the Four Types of Analytics

| | |
|---|---|
| Unit | Chapter 1: The Role of Analytics in Accounting |
| Item | Exercise 1.4 |
| Perspective | Managerial accounting |
| Tools | Workbook browsing and written work |
| Time | About 45 minutes |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This exercise turns the chapter's four types from definitions into a skill: writing a question that really is descriptive, diagnostic, predictive or prescriptive, and checking that the workbook can answer it. Writing the question is the first stage of the workflow, and the memo is the last. Students also meet the limits of a dataset, because a good-sounding production question about scrap or downtime has no data behind it here. The exercise uses all four types, and it is the main practice for chapter outcomes 1 and 2.

By the end, students can:

- write a production question of each type and say why it has that type (chapter outcome 1);
- name the table group and worksheets that hold the data for each question;
- explain why a prescriptive question is the hardest to answer, in terms of data, assumptions and judgment;
- order the questions by complexity in a short memo and recommend which to tackle first (chapter outcome 2).

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis of financial data); IMA Data Analysis, and Decision Analysis; IFAC IES 2 (b), management accounting, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.2.

## Before you assign

- Students need CharlesRiver.xlsx, the chapter's section on the four types (Figure 1.1 and Table 1.1) and Tutorial 1.1.
- The exercise relies on these conditions: the Manufacturing worksheets hold completions, work order closes and operations; DemandForecast and the work center tables (WorkCenter, WorkCenterCalendar, RoutingOperation and RoughCutCapacityPlan) hold plans and capacity; the completions run through the end of the last quarter of the data; and the dataset has no table of actual scrap, defects or downtime. The only scrap column is the planned scrap factor of BillOfMaterialLine.
- Quantities in the production tables are not whole numbers. Tell students to report them as they are.
- Do the exercise yourself first. Writing the four questions takes ten minutes and shows you where students will stumble.

## How to run it

Individual or pairs. For about 45 minutes: 10 minutes browsing the worksheets (requirement 2), 15 writing the four questions (requirement 1), 5 on the prescriptive question (requirement 3) and 15 for the memo (requirement 4).

A useful variation: students swap their four questions and classify each other's before they see your model set. A disagreement about a type is the best discussion in the chapter.

**Hints.** If a question has no verb, ask what the manager would do with the answer. If a prescriptive question has no constraint, ask what limits the choice. Hold back the work center worksheets until a student asks what limits production.

**Collect** the memo with the four questions.

## Step-by-step solution

### Requirement (1): Write one question of each type

**Step 1. Test each question against the type.** Use these tests, which follow the chapter's definitions.

| Type | The question asks | The answer is |
|---|---|---|
| Descriptive | What happened? | A summary of recorded data |
| Diagnostic | Why did it happen? | A decomposition, a comparison of segments, or a trace to documents |
| Predictive | What might happen? | An expectation or forecast from historical patterns, about a future period |
| Prescriptive | What should we do? | A recommended action that optimizes an objective under constraints |

**Step 2. Compare with a model set.**

| Type | A model question | Tables that hold the data |
|---|---|---|
| Descriptive | How many units of each item group did the plant complete in Q4 2026, compared with Q3 2026? | ProductionCompletion, ProductionCompletionLine, Item |
| Diagnostic | Why did the total variance on closed work orders rise from fiscal 2024 to fiscal 2026 while the units completed barely changed? | WorkOrderClose, WorkOrder, ProductionCompletionLine, Item, LaborTimeEntry |
| Predictive | How many units will the plant complete next quarter, and what total variance does that suggest, if recent trends continue? | ProductionCompletionLine, WorkOrderClose, DemandForecast |
| Prescriptive | Given the hours each work center has next quarter, which items should the plant schedule to maximize contribution margin? | WorkCenter, WorkCenterCalendar, RoutingOperation, RoughCutCapacityPlan, Item, DemandForecast |

**Check:** each question has a verb that matches its type and names a period, and the descriptive question can be answered by adding up what is recorded. **Watch for:** a question that mixes two types, such as "what happened and why?". Ask students to split it in two.

### Requirement (2): Name the table group and the worksheets

**Step 3. Browse the worksheets and assign the groups.**

a. Click **ProductionCompletionLine**, **WorkOrderClose**, **LaborTimeEntry**, **DemandForecast**, **WorkCenterCalendar** and **RoutingOperation**.
b. Read row 1 of each and decide which question it serves.
c. Use Table 1.3 for the group names.

A model assignment: the descriptive question needs Manufacturing and Master Data (Item, for ItemGroup). The diagnostic question needs Manufacturing and Master Data, and Payroll and Time for the hours (LaborTimeEntry). The predictive question needs Manufacturing and Demand Planning and MRP (DemandForecast, with its Lifecycle Adjusted, Planner Adjusted, and Seasonal Trend methods). The prescriptive question needs the work center and routing tables of Manufacturing, Demand Planning and MRP for the capacity plan, and Master Data for cost and price.

**Check:** the worksheets named exist, and each question has at least one worksheet that could answer it. **Watch for:** a question that names a worksheet that does not hold the data, such as a scrap rate.

### Requirement (3): Explain why the prescriptive question is hardest

**Step 4. Write two or three sentences on data, assumptions and judgment.** A model outline:

1. *Data.* It needs the other three types first: a baseline of what happened, an explanation of the costs, and a forecast of demand. It also needs the figures for its objective and constraints, such as the contribution margin of each item and the hours of each work center. List price less StandardCost is not that margin, because the standard cost of a manufactured item includes fixed overhead and actual prices are net of discounts.
2. *Assumptions.* It assumes setup and run times stay as routed, that capacity is available as the calendar says, and that the forecast holds. The dataset has planned hours and a calendar with maintenance days, but no record of actual downtime, defects or scrap, so these assumptions cannot be tested here.
3. *Judgment.* Someone must choose the objective and the trade-offs, such as margin against service or overtime, and must explain the recommendation to people who will act on it.

**Check:** the three considerations of the requirement (the data, the assumptions and the judgment) are all addressed. **Watch for:** "it needs more math". The difficulty is in the inputs and the choices, not the calculation.

### Requirement (4): Write the memo

**Step 5. Outline a half-page to one-page memo.** A strong memo has a header and a one-sentence purpose; the four questions in order of complexity (descriptive, diagnostic, predictive, prescriptive), each with its type and its table groups; a recommendation of the first question to tackle; and the reason.

The usual recommendation is the descriptive question: it needs one group, it answers quickly, it checks that the data can be trusted, and its result is the baseline for the diagnostic question. A recommendation to start with the diagnostic question is also acceptable, when the manager's worry is already visible in the data and the memo says so. Starting with the prescriptive question is not, because its inputs do not exist yet.

**Check:** the order of the questions is by complexity, and the recommendation has a reason.

## Expected results

A student who answers the model questions finds these values.

| Quantity | Value | Where |
|---|---:|---|
| Units completed, Furniture, Q3 2026 and Q4 2026 | 7,186.54 and 7,458.21 | Step 2 |
| Units completed, Lighting, Q3 2026 and Q4 2026 | 4,699.67 and 6,106.82 | Step 2 |
| Units completed, Textiles, Q3 2026 and Q4 2026 | 845.90 and 1,188.32 | Step 2 |
| Units completed, all groups, Q3 2026 and Q4 2026 | 12,732.11 and 14,753.35 | Step 2 |
| Units completed in 2024 | 52,263 | Step 2 |
| Units completed in 2025 | 48,961 | Step 2 |
| Units completed in 2026 | 51,160 | Step 2 |
| Total variance on work orders closed in 2024 | 1,297,051.56 | Step 2 |
| Total variance on work orders closed in 2025 | 1,861,950.08 | Step 2 |
| Total variance on work orders closed in 2026 | 2,265,636.88 | Step 2 |
| Change in units, fiscal 2024 to fiscal 2026 | -2.1% | Step 2 |
| Change in total variance, fiscal 2024 to fiscal 2026 | +74.7% | Step 2 |
| Work centers | 5: Cutting Work Center, Assembly Work Center, Finishing and Test Work Center, Packing Work Center, and Quality Assurance Work Center | Step 3 |
| Rows in DemandForecast, WorkCenterCalendar, RoughCutCapacityPlan | 66,496; 5,900; 55,051 | Step 3 |

Only the descriptive and diagnostic figures can be computed from the data at this stage, and students are not asked to compute them. The values tell you the stories the questions point to: output is flat and the variance on closed work orders grows. The diagnostic question is the one that Part III answers.

## What a strong answer says

- **Requirement (1).** Four questions that pass the tests, with a verb and a period, and each answerable from the tables.
- **Requirement (2).** Worksheets that exist and could answer the question, with the table group named.
- **Requirement (3).** Reasons in terms of the inputs it needs, the assumptions behind it and the choices it asks for, and a remark that the data lack actual downtime and scrap.
- **Requirement (4).** An ordered memo with a choice and a reason.

A weak answer writes "why" questions and calls them descriptive, writes a "predictive" question about the past, or names worksheets from memory.

## Common mistakes and how to respond

- **A descriptive question that asks why.** *Symptom:* "Why did output fall?" *Response:* ask whether the answer is a total or an explanation.
- **A predictive question with no future.** *Symptom:* "What was the average yield?" *Response:* ask which period the answer is about.
- **A prescriptive question with no decision or constraint.** *Symptom:* "What should we do about variance?" *Response:* ask what is chosen, and what limits the choice.
- **A question the data cannot answer.** *Symptom:* scrap rate, defect rate, machine downtime. *Cause:* the tables hold plans and standards only. *Response:* ask which worksheet holds it, then help rewrite the question for what the data has.
- **The wrong group.** *Symptom:* work order data placed in Order-to-Cash. *Response:* point to Table 1.3.
- **Whole units.** *Symptom:* rounded quantities. *Response:* point to the fractional quantities in the worksheet.
- **A memo with no recommendation, or in the wrong order.** *Response:* ask what the manager should do on Monday.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: four questions of the right types | 30 | Four questions that pass the tests, each with a period | One or two questions of the wrong type |
| Requirement 2: groups and worksheets | 25 | Real worksheets that could answer each question | Names that do not exist or do not fit |
| Requirement 3: why prescriptive is hardest | 20 | Data, assumptions and judgment, each addressed | One of the three, or "more math" |
| Requirement 4: the memo | 25 | Ordered by complexity, with a choice and a reason | A list with no recommendation |

## Extensions and discussion questions

- Rewrite a question the data cannot answer so that it can be answered with what the worksheets hold, and say what was lost.
- Choose the question from Table 1.1 that is closest to the diagnostic production question, and compare the two.
- Discuss: Part III takes up the diagnostic question with SQL. Which tables would you join first, and why?
- Discuss: what would you need to add to the dataset to answer a question about scrap, and which group would it join?
