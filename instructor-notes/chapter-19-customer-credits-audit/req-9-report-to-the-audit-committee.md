# Requirement 9: Report to the audit committee

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 9 |
| Tools | Excel |
| Time | About 150 minutes |
| Solution file | Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Report (key figures linked live, the conclusion, findings F1 to F6, the clean results and the action plans); the appendix is the workbook's own sheets |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The audit ends in a report that the committee can act on and the owners can accept. This requirement asks for judgment in writing: a conclusion that says what the tests covered and what they could not reach, findings that carry six elements each, clean results reported with the same care, and action plans with an owner and a date. It also asks students to expect the owners' answers, because managers resist a weakness when no error has been detected and argue that a review control would have caught the problem (Cohen et al., 2020). The analytics type is prescriptive. Students write from the workbook's Report sheet, whose key figures link to the Tests and Deficiencies sheets so that no number is typed twice.

Students can draft a bounded conclusion and keep every figure tied to its source (Part 1), write findings and a scope that report clean results (Part 2), and build action plans with the response each owner is likely to give and the evidence that answers it (Part 3).

**Competencies practiced.** CPA Evolution Core S1 M8 (visualization and communicating results); IMA Leadership (communication skills); IFAC IES 3 (b); AACSB A5 part 5.2 (judgment and communication).

## Before you assign

- **Files.** The workbook and script of Requirements 1 to 8, a word processor for the report, and the Report sheet of the model workbook for comparison. No new analysis is required.
- **Data conditions.** The ratings of Requirement 8 are provisional; the next year's commission rates are requested, not reported missing, because the records end with the data. Counts carry their definitions: the refunds before payment are 58 by application date and 51 by receipt date.
- **Verify first.** The key-figure block reads the counts of Requirement 4 and the classification count of Requirement 8.

## How to run it

Individual or pairs, about 150 minutes: 20 for the key figures and the conclusion, 40 for the findings, 15 for the scope and clean results, 35 for the action plans and expected responses, 25 for the page fit and the appendix, 15 for a self-check against the criteria. Ask first for the conclusion in two sentences, as the debrief does, before the report is drafted. **Collect** the report and the workbook. A quick read: the conclusion and the evaluation table first, then one number in each row traced to its sheet.

## Step-by-step solution

### Part 1: Fix the numbers and the conclusion

**Step 1. Link the key figures.** Build a block at the top of the Report sheet whose cells point at the Tests and Deficiencies sheets, and quote them from there.

```
=Tests!H5
=Deficiencies!D26
=Deficiencies!D28
```

**Check:** the block holds six figures: the four counts of Requirement 4, the number of significant deficiencies (2) and the overall classification. **Watch for:** a count with no definition. A committee member who recomputes the refunds before payment by the receipts' dates finds 51, not 58; the report names the definition.

**Step 2. Write the conclusion.** Two or three sentences, in this order: what the tests covered (the populations reconcile to the ledger by year, which supports completeness relative to those records only, every credit recomputes within the stated limits of rounding, tax and freight, the lapping tests found no trace, on the definitions stated); what they could not reach (the customers' requests, the payee checks, the inspection of returned goods, independent bank evidence, since the database records each refund's ClearedDate and it was not verified, and the operation of the compensating controls, with no assurance on them); and the finding (credits and refunds approved above the recorded general limits, with effective delegation and enforcement unverified, whether by a gap in design or in operation still to be settled, rated provisionally as two significant deficiencies, with no material weakness identified and one refund under follow-up).

**Check:** the conclusion says what was not tested before it gives a rating. **Watch for:** assurance words ("the controls are effective"), accusation words, and the three-year amount set against materiality: the first pattern's $421,606.55 exceeds $225,180.56, but materiality is the year's judgment, and the year's exposure is $172,307.40.

### Part 2: Findings, scope and clean results

**Step 3. Write the six findings.** One row each in a table of condition, criteria, cause, effect, rating and recommendation; the criteria are the control points of the cycle's map.

| Finding | Rating |
|---|---|
| F1. Credits approved above the recorded general limits, in the department that handles the customer's cash (D1, D2) | Significant deficiency (provisional) |
| F2. Refunds approved above the recorded general limits (effective delegation and enforcement unverified) and dated before the customer's payments were applied, with no preparer recorded (D3, D4, D6) | Significant deficiency (provisional) |
| F3. Concentration of duties with the Accounting Manager (D7) | Deficiency (may combine entity-wide) |
| F4. No offset of past-due balances, and refunds by another method (D5) | Follow up |
| F5. Damaged goods restocked at standard cost (D8) | Valuation follow-up |
| F6. The largest refund (follow-up) | Follow up |

**Check:** every finding has all six elements, the condition carries its count and definition, the effect says whether a misstatement is reasonably possible, and the rating is provisional. **Watch for:** a finding without a cause ("not yet known" is an answer when it is true), and a condition worded as an act.

**Step 4. State the scope, the reconciliations and the clean results.** The populations (612 returns, 612 credits, 222 refunds, 637 clawbacks), the materiality of $225,180.56 and its base, a statement that the documentary testing plan (A1 to A3) was prepared and its selection frozen, that the documents were not supplied so those attributes remain untested and must be requested, and that D1 was shown on database records and compared with the full remainder, and a paragraph of the clean results.

**Check:** each population reconciles by year with no difference, and the clean results list the tests that found nothing. **Watch for:** a report of exceptions only.

### Part 3: Action plans and the owners' answers

**Step 5. Build the action plans.** A table of action, owner by role, date, the response expected and where disagreement is expected, with the evidence that answers it.

![The report's page budget, the plan a student fits the work into.](../figures/chapter-19-customer-credits-audit/IF-19-9-A.pdf)

**Check:** the model has 10 plans with 8 owners by role, dated 2027-10-31 to 2028-06-30, and each finding has at least one. The model expects three answers:

| Owner | Expected response | Where disagreement is expected, and the evidence |
|---|---|---|
| Customer service manager | Will point to the warehouse receipt as the compensating control | The receiving record documents a return; it needs authenticating, with inspection evidence, before it shows that the goods arrived, in the stated condition, or justified the credit, and it says nothing of who handled the customer's cash; show the credits whose approver applied the invoice's cash. |
| Accounting manager | Will point to the review of each credit balance | The review did not stop refunds before payment or to customers past due by at least the refund; show its precision with those counts. |
| Chief financial officer | May argue that the team is small | The audit partners Cohen et al. (2020) interviewed describe managers who resist a weakness when no error has been detected: answer with the likelihood and the absence of evidence of an independent review, not with a detected error. |

**Watch for:** an action with no owner or date, and an owner assumed to agree.

**Step 6. Fit the pages.** Three pages and an appendix of at most three, of selected, condensed exhibits (the map, the reconciliation, the test results, the sample plan, the evaluation, the action plans), not every workbook sheet. The model's text (conclusion, findings, clean results and action plans) runs to about 1,725 words; count yours, then cut the findings' prose before the clean results.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Credits above authority; cash and credit; refunds above authority | 414; 206; 163 | 1 |
| Refunds before payment, by application date; by receipt date | 58; 51 | 1 |
| Significant deficiencies; the overall conclusion | 2; No material weakness identified (provisional) | 1 |
| Findings; action plans; owners | 6; 10; 8 | 3, 5 |
| Materiality; the first pattern's exposure for the last year | $225,180.56; $172,307.40 | 2 |

> **Instructor notes, Requirement 9:** the conclusion is bounded and describes rather than accuses: the recorded populations reconcile to the ledger by year, and the trace and recomputation tests agree, on the definitions stated, which supports completeness relative to those records and cannot detect an event omitted from both; the customer's requests, the payee checks, the inspection of returned goods, independent bank evidence (the database records each refund's ClearedDate, which was not independently verified, and no bank evidence for refunds paid or funds received was supplied), and the operation of the compensating controls remain untested, so the report gives no assurance on them or on the balances beyond the records. Credits and refunds were approved above the approvers' recorded general limits, with the effective delegation and its enforcement unverified, and whether that is a gap in the design or in the operation of the controls waits on the delegation of authority; two significant deficiencies, rated provisionally; one refund under follow-up; no trace of lapping in the tests run. The sampling plan for the documentary attributes was prepared and the selection frozen, but the documents were not supplied, so those attributes remain untested and the listed documents must be requested; D1 was shown on the database records and compared with the full remainder. Actions: an approved delegation of authority for credits and refunds, enforced in the system; credits approved by someone who does not handle the customer's cash; credits on unpaid invoices reduce the receivable, and refunds wait for cleared payment; verify the customer terms and the applicable policy, and offset eligible open balances before a refund where they require or permit it; a preparer recorded on credits and refunds; review of the Accounting Manager's concentration; a request for the approved 2027 commission rates (the records end with 2026, so their absence is a question, not a finding); inspection of returned goods, and a write-down where the inspection finds one is needed. Expected pushback: the customer service manager points to the warehouse receiving record, which documents a return but needs authenticating, with inspection evidence; the accounting manager points to the review of each credit balance; managers resist a weakness without a detected error, as the audit partners Cohen et al. (2020) interviewed describe, so answer with the precision and the evidence of each compensating control.

## What a strong answer says

- **The conclusion is bounded:** it says what the tests covered and what they could not reach, and gives no assurance on the second.
- **Each finding has condition, criteria, cause, effect, rating and recommendation,** in words about what the records show.
- **The clean results are reported** and the ratings are provisional.
- **Every action has an owner by role and a date,** and the report names where each owner will disagree and the evidence that answers it, not a detected error.

A weak answer opens with ratings, states assurance, or leaves the owners' answers to chance.

## Common mistakes and how to respond

- **An unbounded conclusion.** *Symptom:* no mention of what the tests could not reach. *Response:* ask which documents the database cannot show.
- **The three-year amount against materiality.** *Symptom:* $421,606.55 "above materiality". *Response:* ask which year materiality was set on.
- **A count without a definition.** *Symptom:* 58 refunds, no date named. *Response:* ask what a reader who uses receipts finds.
- **A finding without a cause or an effect.** *Symptom:* a condition and a recommendation. *Response:* ask what would have to fail for a misstatement.
- **An accusation.** *Symptom:* "diverted" or "stolen" in a condition. *Response:* reword as what the records show.
- **No clean results.** *Symptom:* only exceptions. *Response:* ask what the tests found nothing in.
- **Plans without owners.** *Symptom:* "management will fix". *Response:* ask which role and which date.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Page limits and structure | 10 | Three pages, appendix within three | Over the limit |
| A bounded conclusion | 20 | Covered, not reached, then ratings | Ratings without limits |
| Findings with six elements | 25 | All six for each finding, provisional ratings | Missing cause or effect |
| Scope, reconciliations, clean results | 10 | Populations by year, clean results named | Exceptions only |
| Action plans | 20 | Owner by role, date, expected response | Actions without owners |
| The expected pushback | 15 | Evidence for each compensating control | Disagreement ignored |

## Extensions and discussion questions

- Give the conclusion in two sentences aloud, then rewrite the report's first page for the committee chair in half a page.
- Role-play: one student is the owner who points to the warehouse receipt; the other answers with the credits whose approver applied the cash.
- Discuss: what should the committee hear first?
- Discuss: should the report give the owners the draft before the meeting, and what changes if they answer with evidence?
