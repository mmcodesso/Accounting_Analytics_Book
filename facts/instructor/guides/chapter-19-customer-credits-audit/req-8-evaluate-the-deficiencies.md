---
note: ch19.r8
uses: [ch19.g8]
title: Evaluate the deficiencies (Chapter 8)
kind: requirement
number: '8'
unit: '19'
perspective: auditing
tool: excel
minutes: 120
solution: "Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Deficiencies (the matrix D1 to D8, the combined evaluation G1 to G5, the clean results and the model answer)"
figures:
  - id: IF-19-8-A
    kind: excel-mock
    purpose: The evaluation matrix the committee's ratings rest on.
    shows: "The Deficiencies worksheet: the three threshold cells at the top, then one row for each of D1 to D8 with its control point, design or operation, the exposure of the last year, the band against the thresholds, the compensating control and the classification, and below it the combined groups with their exposure and potential magnitude."
    data: The Deficiencies worksheet of the model workbook, linked to the Tests sheet.
---
{% set g = ch19_g8 %}
# Requirement 8: Evaluate the deficiencies (Chapter 8)

{{ header() }}

## Purpose and learning outcomes

Requirements 4 to 7 produced patterns; this requirement turns them into judgments. Severity turns on whether a misstatement is reasonably possible and how large it could be, not on how many exceptions the tests found or whether a misstatement occurred, and a compensating control counts only if it is precise enough. An evaluation matrix keeps the judgment and its arithmetic in one workbook, with every exposure compared with the threshold cells of Requirement 3. The analytics type is diagnostic, with the judgment that makes a rating.

Students can record each pattern with its control, kind, frequency and exposure (Part 1), assess together the deficiencies on the same account without counting a document twice and classify them with the evidence and what could change it (Part 2), and report the clean results as carefully as the exceptions (Part 3).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls); IMA Reporting and Control (internal control); IFAC IES 2 (g) and IES 4 (a); AACSB A5 part 5.2 (judgment and communication).

## Before you assign

- **Files.** Credits Audit.xlsx with the Materiality sheet (named cells Materiality, PerformanceMateriality and ClearlyTrivial), the Tests sheet of Requirement 4 and the results of Requirements 5 to 7.
- **Data conditions.** An exposure is the amount of the documents that failed a control, not a misstatement. MaxApprovalAmount is a general limit and no table records a preparer, so two of the patterns rest on what the records cannot show. No compensating control has been tested for operation.
- **Verify first.** The matrix links to the Tests sheet and not to typed numbers, and the first pattern's exposure for the last year falls between performance materiality and materiality.

## How to run it

Individual, about 120 minutes: 25 for the matrix, 30 for likelihood and compensating controls, 25 for combining and classifying, 15 for the clean results, 25 for dispositions and what would change each rating. Hold back the classification until the exposures are computed, and ask for the evidence behind each rating before accepting it. Remind students that the ratings are provisional. **Collect** the Deficiencies sheet.

## Step-by-step solution

### Part 1: Record each pattern in the matrix

**Step 1. Link the thresholds and each pattern's counts.**

a. Use the named threshold cells of Requirement 3 at the top of the sheet.
b. Give each pattern a row: control point, design or operation, frequency for the three years and the last year, and exposure, each a link to the Tests sheet or a formula on the workbook's Tables.
c. Add the band as a formula that reads the exposure against the three thresholds.

```jinja
{{ g.f_exposure }}
{{ g.f_band }}
```

| ID | Control point | Kind | Last-year exposure | Band | Classification |
|---|---|---|---:|---|---|
{% for x in g.rows %}
| {{ x.id }} | {{ x.point }} | {{ x.kind }} | ${{ x.e26|money }} | {{ x.short }} | {{ x.cls }} |
{% endfor %}

**Check:** the model matrix has {{ g.rows|length }} rows, D5 on two (the offset and the method). The first pattern's exposure for the last year is ${{ g.rows[0].e26|money }}, above performance materiality (${{ g.perf|money }}) and below materiality (${{ g.mat|money }}). **Watch for:** the three-year exposure in the band. The first pattern's ${{ g.d1_3y|money }} is above materiality, but materiality is a judgment on one year's income, so the year it applies to is the year to compare.

**Step 2. State the likelihood and the compensating controls.** For each row, write the likelihood in words ("reasonably possible", "an anomaly", "an evidence gap") and name each compensating control with the requirement that supports it and the evidence that it operates.

{{ figure('IF-19-8-A') }}

**Check:** each control cited rests on a result of Requirements 4 to 7 (every credit traces to a return received in the warehouse, refunds are approved outside customer service, no lapping), and none is shown to operate, since the receiving records and the delegation of authority lie outside the database. **Watch for:** a compensating control assumed precise. The receiving record documents a return: authenticate it and obtain inspection evidence before concluding that the goods physically arrived, were in the stated condition, or justified the credit.

### Part 2: Combine, classify and say what could change the rating

**Step 3. Assess the deficiencies on the same account together and count each document once.** The credits that fail the authority test or the cash test make one group; the refunds that fail authority or timing another. A SUMPRODUCT adds each document's amount once.

```jinja
{{ g.f_union }}
```

**Check:** {{ g.union12_n }} credits, ${{ g.union12|money }}, for the credits; {{ u34[0] }} refunds, ${{ g.groups[1].e26|money }}, for the refunds. The potential magnitude is the year's credits, ${{ g.potential_credits|money }}, at or above materiality. **Watch for:** adding the two credit exposures, ${{ g.sum12|money }}, which counts credits that fail both and crosses materiality. Counted once, the group stays below it.

**Step 4. Classify each group and give it a disposition.** For each group write the classification, the evidence it rests on, and what evidence would change it, then a disposition in Chapter 8's terms: a deficiency to report, or a follow-up with its question and document.

```jinja
{{ g.f_overall }}
```

**Check:** {{ g.n_sig }} significant deficiencies (credits and refunds), the Accounting Manager's concentration a deficiency, the offset and method a follow-up, the restocked goods a valuation follow-up, {{ g.n_mw }} material weaknesses: "{{ g.overall }}". Evidence that would change a rating: no approved delegation of authority, receiving records that do not support the returns, or access that lets customer service record returns. **Watch for:** two things. A rating by count: the method mismatch has {{ g.mism }} exceptions against {{ g.d4_n }} refunds before payment, yet the first is a follow-up and the second part of a significant deficiency. And a material weakness from potential magnitude alone: it is accepted only if the answer addresses likelihood and the compensating link.

### Part 3: Report the clean results

**Step 5. List the clean results with their tests.**

```jinja
{{ g.f_clean }}
{% if g.f_clean_concl %}{{ g.f_clean_concl }}{% endif %}
```

**Check:** {{ g.n_clean }} rows, each with its test, its count and its conclusion: the reconciliations, the clawbacks, the approvers' employment dates, the refund approver apart from the credit approver, returns received in the warehouse, one refund per credit, the recomputed credits and the lapping tests. The reconciliation cell sums the selected Difference rows and reads {{ g.resid }}, a floating-point residue far below a cent, so the conclusion says it reconciles to the cent. A clean result requires every selected difference to be numeric and error-free: a failed or missing difference must block the summary (the model reads "Not evaluable"), never be replaced with zero, and any nonzero difference is investigated, telling a valid rounding residue from an unavailable result. **Watch for:** a matrix of exceptions only, a clean result with no test named, or errors hidden by IFERROR.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Matrix rows | {{ g.rows|length }} | 1 |
| Last-year exposure of the first pattern | ${{ g.rows[0].e26|money }} | 1 |
| Credits failing authority or cash, once; exposure | {{ g.union12_n }}; ${{ g.union12|money }} | 3 |
| Refunds failing authority or timing, once; exposure | {{ u34[0] }}; ${{ u34[1]|money }} | 3 |
| Potential magnitude of the credits | ${{ g.potential_credits|money }} | 3 |
| Significant deficiencies; material weaknesses | {{ g.n_sig }}; {{ g.n_mw }} | 4 |
| Clean results | {{ g.n_clean }} | 5 |

{{ expected() }}

## What a strong answer says

- **The matrix is live:** thresholds are named cells, exposures link to the Tests sheet, and each pattern says design or operation.
- **Likelihood, magnitude and compensating controls decide the rating,** and the compensating controls are named with the evidence they would need.
- **Deficiencies on the same account are assessed together,** and each document is counted once.
- **Every classification says what would change it,** and the ratings are called provisional.
- **The clean results sit beside the exceptions,** each with its test.

A weak answer ranks by count, rates from magnitude alone, or leaves out the clean results.

## Common mistakes and how to respond

- **Three-year exposure in the band.** *Symptom:* "at or above materiality" for ${{ g.d1_3y|money }}. *Response:* ask which year materiality was set on.
- **Adding overlapping exposures.** *Symptom:* ${{ g.sum12|money }}. *Response:* ask how many credits fail both tests.
- **Rating by count.** *Symptom:* the method mismatch ranked above the refunds before payment. *Response:* ask what a misstatement through each would need.
- **A material weakness from magnitude alone.** *Symptom:* no mention of the warehouse receipt. *Response:* ask what would have to fail for a misstatement.
- **A compensating control assumed to operate.** *Symptom:* "the warehouse receipt covers it". *Response:* ask what it shows and what it does not.
- **The ledger's creator read as the preparer.** *Symptom:* {{ g.self_all }} credits and refunds "self-approved". *Response:* ask what the column says on the sales invoices.
- **No clean results.** *Symptom:* a matrix of exceptions. *Response:* ask what the tests found nothing in.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Matrix against the threshold cells | 20 | Named cells, linked exposures, the band formula | Typed numbers |
| Design or operation, frequency, exposure | 15 | All three for every pattern | Counts only |
| Likelihood and compensating controls | 20 | Controls named with the evidence they need | Controls assumed |
| Combined once | 10 | Each document counted once | Sums of overlapping exposures |
| Classification with what could change it | 20 | Reasons and changing evidence for each | A label |
| Dispositions in Chapter 8's terms | 5 | Report or follow-up with the question | No disposition |
| Clean results | 10 | Each with its test | Omitted |

## Extensions and discussion questions

- Re-rate the credits as if a delegation of authority with limits existed, and say which exposure falls and which does not.
- Add the request for the approved rates of the next year as a follow-up and word it as a question.
- Discuss: a significant deficiency with no detected misstatement. How would you answer the owner who asks where the error is?
- Discuss: what evidence would move the credits' rating up to a material weakness?
