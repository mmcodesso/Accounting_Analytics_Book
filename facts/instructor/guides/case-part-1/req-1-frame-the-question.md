---
uses: [case1.g1]
title: Frame the question (Chapter 1)
kind: requirement
number: '1'
unit: case1
perspective: general
tool: conceptual
minutes: 20
solution: ''
figures: []
---
{% set g = case1_g1 %}
# Requirement 1: Frame the question (Chapter 1)

{{ header() }}

## Purpose and learning outcomes

Requirement 1 is the case's first stage: before anyone touches a worksheet, the request is turned into questions that data can answer. It also sets the case's argument for the rest of the work. The controller asked why the Furniture margin fell, and this case answers only the descriptive half of that and prepares the data for the diagnostic half. Students who see that now read Requirements 2 to 5 as preparation, not as a half-finished analysis.

By the end, students can:

- restate the request as a descriptive question and a diagnostic question, each answerable from data;
- name the type of analytics each question calls for, and say what in its wording shows the type;
- list the six stages of the workflow and mark the ones this case completes and the ones it leaves for Part II.

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis of financial data); IMA Data Literacy, and Decision Analysis within Strategy, Planning, and Performance; IFAC IES 3 (a), evaluating data and information from several sources; AACSB A5 part 5.2 (technology judgment, interpretation and communication). The analytics types exercised are descriptive and diagnostic.

## Before you assign

- Students need Chapter 1: the four types and Table 1.1, the six-stage workflow of Figure 1.2, and the controller's question in the opening scenario. They do not need the workbook for this requirement.
- Table 1.1 already lists this question as its managerial diagnostic example: the decomposition of the decline in Furniture gross margin into price, volume, mix and cost effects. Do not show that cell before students write their own questions.
- The requirement relies on one fact about the data that Requirement 5 establishes: the margin did fall from the third to the fourth quarter of fiscal {{ g.year }}. You do not need to share the figures yet.

## How to run it

Students work alone for 15 minutes and compare in pairs for five. In Plan A of the case note it is done together in the first class, using the deck's check slide on the four types. Hold back the stage table until students have written their two questions. If a pair finishes early, ask them what a predictive and a prescriptive question about the same margin would be. **Collect** half a page: the two questions with their types, and the six stages marked.

## Step-by-step solution

### Phase 1: Restate the request as two questions

**Step 1. Split the request.** The controller's request is "why did gross margins on the Furniture product line decline in the most recent quarter?" Read it twice. The first reading finds a fact the controller assumes (the margin declined, in the most recent quarter) and the second finds the question (why).

a. Write the assumed fact as a question: what was the Furniture gross margin percentage in each of the two most recent complete quarters, and by how much did it change?
b. Write the explanation as a question: which of price, volume, mix and cost explains the change?

**Check:** the descriptive question names a measure (gross margin percentage), a population (the Furniture product line) and two periods. The diagnostic question names candidate drivers. **Watch for:** a single question that mixes both ("why did the margin fall by how much?"), a question that already holds the answer, and "the most recent quarter" left undefined. Requirement 3 settles which quarter it is.

### Phase 2: Name the type of each question

**Step 2. Classify each question and give the reason.** The descriptive question summarizes what happened, so it is descriptive analytics. The diagnostic question asks why a result changed, so it is diagnostic analytics, and it needs a decomposition of the change into its sources. A model answer quotes the cue in each: "what was" and "by how much" for the first, "which explains" for the second.

**Check:** each type is paired with the cue in the wording and with the kind of evidence it needs, a summary or a decomposition. **Watch for:** the labels swapped, and "diagnostic" attached to a question about size. If students propose a forecast of next quarter's margin or a recommended price, they have written the predictive and prescriptive questions; accept them as follow-ups and say the case does not ask them.

### Phase 3: Mark the workflow

**Step 3. List the six stages and mark each one.** Use Figure 1.2. A model marking:

| Stage | Status in this case | Where |
|---|---|---|
{% for s in g.stages %}
| {{ s.n }}. {{ s.name }} | {{ s.status }} | {{ s.by }} |
{% endfor %}

The reasoning behind the marking is the case's title. The question is defined here, the data is identified and accessed (Requirement 2) and then prepared and tested (Requirements 3 to 5). The analysis that decomposes the change and the charts that present it come later. The last stage is only partly done: the memo communicates what the data can and cannot support, not the answer to the question.

**Check:** stages 1 to 3 are marked done, stages 4 and 5 are left, and stage 6 is marked done for the readiness findings only. A student who marks all six done has read the case as the whole analysis. A student who marks stage 3 as left may be thinking of Part II's cleaning with Power Query; point them to Requirements 3 to 5, which test the data and treat the closing entry.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Questions written, by type | Two: one descriptive, one diagnostic | Steps 1 and 2 |
| Stages completed in this case | Four of six: 1, 2, 3 and 6 for the readiness findings | Step 3 |
| Stages left for Part II | Two: 4 and 5 | Step 3 |
| Margin of the earlier quarter that the descriptive question will report | {{ g.m3|pct(2) }} | Requirement 5 |
| Margin of the later quarter | {{ g.m4|pct(2) }} | Requirement 5 |
| Change between them | {{ g.drop|num(2) }} points | Requirement 5 |

## What a strong answer says

- **The two questions.** The descriptive question has a measure, a product line and two periods. The diagnostic question names price, volume, mix and cost, or an equivalent set of drivers, and says it needs product-level data.
- **The types.** Each type is justified by the wording of the question, not just named.
- **The stages.** Stages 1 to 3 and the readiness part of stage 6 are marked done, and stages 4 and 5 are left for Part II, with a sentence on why data readiness comes first.

A weak answer states one question, names the types without a reason, or marks every stage as complete.

## Common mistakes and how to respond

- **One question for both halves.** *Symptom:* "why did the Furniture margin fall?" labeled descriptive. *Response:* ask what you could report with no explanation, and make that the first question.
- **The answer inside the question.** *Symptom:* "did promotions cut the margin?" *Response:* ask what the data would show if the answer were no.
- **An undefined quarter.** *Symptom:* "the most recent quarter" with no dates. *Response:* say that Requirement 3 decides it, and ask what could make the latest rows of the ledger the wrong ones.
- **Types named, not reasoned.** *Symptom:* "descriptive, diagnostic" with nothing more. *Response:* ask which words in the question point to the type.
- **Everything marked done.** *Symptom:* all six stages complete. *Response:* ask where in this case anyone decomposes the change.
- **Stage 3 skipped.** *Symptom:* stage 3 left for Part II. *Response:* ask who tests the data, and point to Requirements 3 to 5.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Descriptive question | 30 | A measure, the product line and two periods | One of the three missing, or a vague period |
| Diagnostic question | 30 | Names the drivers and needs a decomposition | A "why" with no drivers, or the answer built in |
| Types and reasons | 15 | Both types named with the cue in the wording | Types named without reasons |
| Stages marked | 25 | Stages 1 to 3 done, 4 and 5 left, stage 6 qualified, each with a reason | Marked without reasons, or one stage misplaced |

## Extensions and discussion questions

- Write a predictive and a prescriptive question about the same margin, and say what data each would need that this case does not touch.
- Rewrite the controller's request as it might arrive from a different role: an auditor or the sales manager. Which words change the type of analytics?
- Discuss: why does the case put readiness before the diagnosis, and what would go wrong if the order were reversed?
- Discuss: Requirement 2 asks where the revenue and cost are recorded. Which of your two questions needs that answer first?
