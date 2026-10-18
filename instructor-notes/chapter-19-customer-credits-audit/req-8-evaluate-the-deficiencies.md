# Requirement 8: Evaluate the deficiencies (Chapter 8)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 8 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 120 minutes |
| Solution file | Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Deficiencies (the matrix D1 to D8, the combined evaluation G1 to G5, the clean results and the model answer) |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

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

```
=Tests!J5
=IF(H8>=Materiality,"At or above materiality",IF(H8>=PerformanceMateriality,"Above performance materiality, below materiality",IF(H8>=ClearlyTrivial,"Above clearly trivial, below performance materiality","Clearly trivial")))
```

| ID | Control point | Kind | Last-year exposure | Band | Classification |
|---|---|---|---:|---|---|
| D1 | C2 | Design, provisional (no delegation in the records) | $172,307.40 | between performance materiality and materiality | Significant deficiency (combined with D2), provisional |
| D2 | C4 | Design, provisional (duties as recorded) | $68,514.82 | between clearly trivial and performance materiality | Significant deficiency (combined with D1), provisional |
| D3 | C6 | Design, provisional (no delegation in the records) | $56,131.84 | between clearly trivial and performance materiality | Significant deficiency (combined with D4 and D6), provisional |
| D4 | C7 | Design, provisional (the refund step as recorded) | $24,893.21 | between clearly trivial and performance materiality | Significant deficiency (combined with D3 and D6), provisional |
| D5 | C8 | Not established: no policy in the records | $52,039.44 | between clearly trivial and performance materiality | Follow up: any policy lies outside the records; recommend one |
| D5 | C8 | Not established: no policy in the records | $62,483.48 | between clearly trivial and performance materiality | Follow up: any policy lies outside the records; recommend one |
| D6 | C2, C6 | Evidence gap, pending the system's design | $85,107.82 | between clearly trivial and performance materiality | Evidence gap; combines with D3 and D4 if the system keeps no preparer |
| D7 | C5, C6 | Design, provisional (no independent review in the records) | $28,975.98 | between clearly trivial and performance materiality | Deficiency (may combine entity-wide into a significant deficiency) |
| D8 | C1 | Not established: valuation follow-up | $40,024.16 | between clearly trivial and performance materiality | Valuation follow-up |

**Check:** the model matrix has 9 rows, D5 on two (the offset and the method). The first pattern's exposure for the last year is $172,307.40, above performance materiality ($168,885.42) and below materiality ($225,180.56). **Watch for:** the three-year exposure in the band. The first pattern's $421,606.55 is above materiality, but materiality is a judgment on one year's income, so the year it applies to is the year to compare.

**Step 2. State the likelihood and the compensating controls.** For each row, write the likelihood in words ("reasonably possible", "an anomaly", "an evidence gap") and name each compensating control with the requirement that supports it and the evidence that it operates.

![A mock of the evaluation matrix the committee's ratings rest on.](../figures/chapter-19-customer-credits-audit/IF-19-8-A.pdf)

**Check:** each control cited rests on a result of Requirements 4 to 7 (every credit traces to a return received in the warehouse, refunds are approved outside customer service, no lapping), and none is shown to operate, since the receiving records and the delegation of authority lie outside the database. **Watch for:** a compensating control assumed precise. The receiving record documents a return: authenticate it and obtain inspection evidence before concluding that the goods physically arrived, were in the stated condition, or justified the credit.

### Part 2: Combine, classify and say what could change the rating

**Step 3. Assess the deficiencies on the same account together and count each document once.** The credits that fail the authority test or the cash test make one group; the refunds that fail authority or timing another. A SUMPRODUCT adds each document's amount once.

```
=SUMPRODUCT((Credits[FiscalYear]=2026)*((Credits[AboveLimit]+Credits[CashAndCredit])>0)*Credits[GrandTotal])
```

**Check:** 172 credits, $197,278.32, for the credits; 64 refunds, $62,474.39, for the refunds. The potential magnitude is the year's credits, $260,457.72, at or above materiality. **Watch for:** adding the two credit exposures, $240,822.22, which counts credits that fail both and crosses materiality. Counted once, the group stays below it.

**Step 4. Classify each group and give it a disposition.** For each group write the classification, the evidence it rests on, and what evidence would change it, then a disposition in Chapter 8's terms: a deficiency to report, or a follow-up with its question and document.

```
=IF(D27=0,"No material weakness identified (provisional)","Material weakness")
```

**Check:** 2 significant deficiencies (credits and refunds), the Accounting Manager's concentration a deficiency, the offset and method a follow-up, the restocked goods a valuation follow-up, 0 material weaknesses: "No material weakness identified (provisional)". Evidence that would change a rating: no approved delegation of authority, receiving records that do not support the returns, or access that lets customer service record returns. **Watch for:** two things. A rating by count: the method mismatch has 153 exceptions against 58 refunds before payment, yet the first is a follow-up and the second part of a significant deficiency. And a material weakness from potential magnitude alone: it is accepted only if the answer addresses likelihood and the compensating link.

### Part 3: Report the clean results

**Step 5. List the clean results with their tests.**

```
=LET(mask,LEFT(Reconciliation!A5:A90,10)="Difference",d,FILTER(Reconciliation!C5:E90,mask),ok,FILTER(ISNUMBER(Reconciliation!C5:E90),mask),IF(AND(ok),SUM(ABS(d)),"Not evaluable: missing or erroneous difference"))
=IF(ISNUMBER(C32),IF(C32<0.005,"Reconciles to the cent","Investigate differences"),C32)```

**Check:** 8 rows, each with its test, its count and its conclusion: the reconciliations, the clawbacks, the approvers' employment dates, the refund approver apart from the credit approver, returns received in the warehouse, one refund per credit, the recomputed credits and the lapping tests. The reconciliation cell sums the selected Difference rows and reads 4.2e-07, a floating-point residue far below a cent, so the conclusion says it reconciles to the cent. A clean result requires every selected difference to be numeric and error-free: a failed or missing difference must block the summary (the model reads "Not evaluable"), never be replaced with zero, and any nonzero difference is investigated, telling a valid rounding residue from an unavailable result. **Watch for:** a matrix of exceptions only, a clean result with no test named, or errors hidden by IFERROR.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Matrix rows | 9 | 1 |
| Last-year exposure of the first pattern | $172,307.40 | 1 |
| Credits failing authority or cash, once; exposure | 172; $197,278.32 | 3 |
| Refunds failing authority or timing, once; exposure | 64; $62,474.39 | 3 |
| Potential magnitude of the credits | $260,457.72 | 3 |
| Significant deficiencies; material weaknesses | 2; 0 | 4 |
| Clean results | 8 | 5 |

> **Instructor notes, Requirement 8 (provisional ratings that rest on the records and on compensating controls not yet tested; reasoned alternatives accepted):** D1 credit authority, above the recorded general limit (414; 2026 exposure 172,307.40, above performance materiality 168,885.42 and below materiality; all 2026 credits 260,457.72, above it, the potential magnitude). D2 segregation in customer service (receipts, applications, credits, clawbacks; 206 overlaps, 44 of them by the credit date): a design deficiency as the duties are recorded, to confirm against the access rights, mitigated, if they operate, by every credit tracing to a return recorded in the warehouse at invoice prices (the receiving record documents a return: authenticate it and obtain inspection evidence before concluding that the goods arrived, in the stated condition, or justified the credit), refunds approved outside customer service (in Administration), and the absence of any lapping or false-credit trace. D1 and D2 combined (172 credits in 2026, 197,278.32, each counted once; 188, 215,322.24, on the wider test of Requirement 4, an accepted extension): a SIGNIFICANT DEFICIENCY over credits and receivables (occurrence of credits, completeness of cash), provisionally not a material weakness: a material misstatement through credits would need a warehouse record that does not reflect a real return, or collusion between the warehouse and customer service, and the records show no sign of either; but the receiving and inspection records, the delegation of authority, and the access rights lie outside the database, and finding no error or trace does not show that the compensating controls operate. Evidence that would change the rating: no approved delegation, receiving records that do not support the returns, or access that lets customer service record returns. A student who rates it a material weakness from the potential magnitude and the untested evidence is accepted if the answer addresses likelihood and the compensating link. D3 refund authority (163; 2026 59 / 56,131.84), D4 refunds before payment (58 by application date, 51 by receipt date; 2026 19 / 24,893.21; cause: credits booked to 2060 on unpaid invoices), and D6 no preparer recorded, an evidence gap until the system's design shows whether a preparer is kept (a design deficiency if none is): a SIGNIFICANT DEFICIENCY over refunds (cash out, a fraud risk factor; 64 refunds in 2026, 62,474.39, each counted once, of 85,107.82 refunded), though the magnitude is well below materiality. D5 no offset and refund method: a follow-up: the records show the patterns, while the customer terms and any policy on an offset or the original instrument lie outside them; a refund that can reach an account the customer does not control is a risk a control should address whether or not a policy exists, so verify the terms and the policy, offset eligible open balances where they require or permit it, and accept a student who calls it a design deficiency. D7 the Accounting Manager's concentration (commission rates, accruals, and payments; the largest refund; all payroll approvals in Chapters 12 and 16): a deficiency in this cycle, which may combine entity-wide into a significant deficiency unless an independent review is found to operate. D8 damaged goods restocked at standard cost: a valuation follow-up (the restocked cost is a flow, not the inventory still held, and 17 return lines of less than one unit sit below standard). No material weakness identified on the records; each rating stays provisional until the cause, the policy, and any compensating review are known. Clean: the reconciliations, clawbacks, the substantive tests, and the lapping tests.

## What a strong answer says

- **The matrix is live:** thresholds are named cells, exposures link to the Tests sheet, and each pattern says design or operation.
- **Likelihood, magnitude and compensating controls decide the rating,** and the compensating controls are named with the evidence they would need.
- **Deficiencies on the same account are assessed together,** and each document is counted once.
- **Every classification says what would change it,** and the ratings are called provisional.
- **The clean results sit beside the exceptions,** each with its test.

A weak answer ranks by count, rates from magnitude alone, or leaves out the clean results.

## Common mistakes and how to respond

- **Three-year exposure in the band.** *Symptom:* "at or above materiality" for $421,606.55. *Response:* ask which year materiality was set on.
- **Adding overlapping exposures.** *Symptom:* $240,822.22. *Response:* ask how many credits fail both tests.
- **Rating by count.** *Symptom:* the method mismatch ranked above the refunds before payment. *Response:* ask what a misstatement through each would need.
- **A material weakness from magnitude alone.** *Symptom:* no mention of the warehouse receipt. *Response:* ask what would have to fail for a misstatement.
- **A compensating control assumed to operate.** *Symptom:* "the warehouse receipt covers it". *Response:* ask what it shows and what it does not.
- **The ledger's creator read as the preparer.** *Symptom:* 834 credits and refunds "self-approved". *Response:* ask what the column says on the sales invoices.
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
