# Requirement 6: Sample what the database cannot show (Chapter 8)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 6 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 150 minutes |
| Solution file | Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Sample (attributes, parameters, key items, the rule, the frozen selection, D1 and A3) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This is the one requirement where sampling is the right tool, and the point is to know why. The records cannot show whether a customer asked in writing for a refund, whether someone independent checked the payee, or whether anyone inspected goods returned damaged. Those are documents, examined one at a time. Students plan the sample, take the key items in full, draw and freeze the rest, and write the rule before testing. On the one attribute the data can test, they see that a query of the whole population finds what a sample can only estimate. The analytics type is statistical inference: the upper deviation limit says what the population could be, not what will happen.

Students can size an attribute sample from the case's table, take key items in full, draw and freeze the rest, write the rule first (Parts 1 to 4), and compare a sample with the population test (Part 5), while refusing to report results the database cannot hold (Part 6).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls); IMA Data Analytics and Insights (statistical analysis); IFAC IES 2 (f); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Credits Audit.xlsx with the Refunds Table of Requirement 4, including its BeforePayment flag, and the Credits and ReturnLines Tables. Excel for Microsoft 365: the draw needs RANDARRAY and SORTBY, the rule BETA.INV; the model also uses LET, FILTER, HSTACK, TAKE and XLOOKUP.
- **Data conditions.** No table holds a request, a payee check or an inspection record. The reason for a return is SalesReturn.ReasonCode, which is what defines the third attribute's population. Students' draws differ from the model's, so grade the plan, not the count.
- **Verify first.** The size cell reads 59 with 95% confidence, a 5% tolerable rate and no expected deviations, and the key items and the remainder read 7 and 215.

## How to run it

Individual or pairs, about 150 minutes: 25 for the attributes, 15 for the parameters and size, 25 for the key items, 25 for the draw and freeze, 15 for the rule, 25 for D1 and the comparison, 20 for A3 and the write-up. Hold back the third attribute's own population until students have a draw, and the comparison with Requirement 4 until the rule is frozen. **Collect** the workbook with the frozen selection, its date and parameters, and the rule dated before the count.

## Step-by-step solution

### Part 1: Define three attributes that need outside evidence

**Step 1. Name each attribute and its deviation.** On the Sample sheet, list A1 (a written request, dated before the refund and for its amount), A2 (a payee checked against the customer master by someone independent) and A3 (an inspection record, for refunds of returns coded Damaged only), each with the evidence and what counts as a deviation. Add D1, the data attribute: the refund dated before the last application of the customer's payments, as Requirement 4 defined it.

**Check:** A1 and A2 apply to all 222 refunds, A3 to 50 of them (2 key items and 48 in the remainder). **Watch for:** A3 sampled like the others. A draw of 59 from the remainder expects about 13.2 Damaged refunds, so the other refunds of the draw are not tests of an inspection.

### Part 2: Choose the parameters and read the size

**Step 2. Enter the parameters and take the size from the table.** Enter the confidence, the tolerable rate and the expected rate in cells, and name them as the model does (SampleConfidence, TolerableRate, ExpectedRate, SampleSize). The model reads the size and the deviations the plan allows from the case's table by the two-way lookup below; typing the value is acceptable.

```
=INDEX($E$15:$H$17,MATCH(ExpectedRate,$D$15:$D$17,0),MATCH(1,($E$13:$H$13=SampleConfidence)*($E$14:$H$14=TolerableRate),0))
```

**Check:** 59 refunds, no deviation allowed. **Watch for:** a size from the wrong column. For a plan at 95% and 5%, a size of 29 (the next column) has an upper limit of 9.8% at no deviation, and 45 (the 90% confidence column) has 6.4%. Both are above the tolerable rate, so the plan fails before any test.

### Part 3: Take the key items in full and draw the rest

**Step 3. List the key items.** Name the thresholds in cells (KeyAmount and KeyCustomerTotal) and spill the key items with one formula, which reads each refund's amount and its customer's three-year total.

```
=LET(c,Refunds[CustomerID],a,Refunds[Amount],t,SUMIFS(Refunds[Amount],Refunds[CustomerID],c),k,(a>=KeyAmount)+(t>KeyCustomerTotal)>0,SORT(FILTER(HSTACK(Refunds[RefundNumber],Refunds[RefundDate],c,a,t,IF((a>=KeyAmount)*(t>KeyCustomerTotal),"Amount and customer",IF(a>=KeyAmount,"Amount","Customer total")),Refunds[BeforePayment]),k)))
```

**Check:** 7 key items ($31,628.48): 6 from customer 128, whose refunds total $26,315.10, and the rest by amount. The remainder is 215 refunds ($185,089.94). **Watch for:** a test on the refund's own amount, which finds 2, or the refund threshold applied to the customer total, which finds 45.

**Step 4. Draw the remainder and freeze it.** The model draws once, in a single cell that spills.

```
=LET(c,Refunds[CustomerID],a,Refunds[Amount],t,SUMIFS(Refunds[Amount],Refunds[CustomerID],c),rest,FILTER(Refunds[RefundNumber],(a<KeyAmount)*(t<=KeyCustomerTotal)),TAKE(SORTBY(rest,RANDARRAY(ROWS(rest))),SampleSize))
```

a. Enter the formula below the header of the selection and confirm it spills 59 rows.
b. Copy the spill and choose **Home > Paste > Paste Values** without moving the selection.
c. Record the date, the parameters and the method next to the selection.

**Check:** 59 distinct refunds, none of them a key item, 27.4% of the remainder. **Watch for:** two errors. An unfrozen draw changes at every recalculation, and with it the count of deviations (10 to 19 in 93% of draws). A draw from all 222 refunds holds about 1.9 key items, and about one draw in nine holds none, so the error hides itself.

### Part 4: Write the rule before the test

**Step 5. Tabulate the upper deviation limit for zero to three deviations.** Three is the case's minimum; a plan that allows more deviations extends the rule to one more than it allows.

```
=BETA.INV(SampleConfidence,A44+1,SampleSize-A44)
```

**Check:** 4.95%, 7.79%, 10.29% and 12.62%. Only no deviation supports reliance at the tolerable rate. **Watch for:** a rule written after the count, which ends at the count it found. Date it before the draw is frozen. BETA.INV fails when every item deviates; the model guards it with an IF.

![A mock of the plan a student hands in before testing anything.](../figures/chapter-19-customer-credits-audit/IF-19-6-A.pdf)

### Part 5: Apply D1 to the sample and compare it with the population

**Step 6. Count D1's deviations in the draw, then in the remainder.** A column of the frozen selection looks up each refund's flag; the count and the limit follow.

```
=COUNTIF(K53:K111,"Deviation")
=IF(B115>=SampleSize,1,BETA.INV(SampleConfidence,B115+1,SampleSize-B115))
```

**Check:** the model's draw holds 16 deviations (27.1%), an upper limit of 38.2%: no reliance. The population test finds 52 of the 215 (24.2%) and 6 of the 7 key items, the same conclusion. A draw holds 10 to 19 deviations in 93% of cases, with limits from 27% to 44%, and a draw with no deviation has probability 3.1e-09.

**Watch for:** the draw's rate offered as the population's, or the limit as a forecast. Where the data hold the evidence, the query replaces the sample.

![Why almost any draw gives the same answer.](../figures/chapter-19-customer-credits-audit/IF-19-6-B.pdf)

### Part 6: Plan A3 on its own population, and deliver no results

**Step 7. Size A3 on the Damaged refunds.** Count them, split the key items from the remainder, and see what the draw holds.

```
=SUM(--(XLOOKUP(XLOOKUP(Refunds[CreditMemoID],Credits[CreditMemoID],Credits[SalesReturnID]),ReturnLines[SalesReturnID],ReturnLines[ReasonCode])="Damaged"))
```

**Check:** 50 refunds, 2 key and 48 in the remainder. The model's draw holds 11, and even if all of them passed the limit would be 23.84%, so examine all 50: with no sample, no sampling risk. **Watch for:** the whole draw counted as inspected, which gives 4.95% and a false pass.

**Step 8. Mark what is not tested.** Fill the attribute columns of the draw with the words the model uses (Not tested: no document in the database; Not applicable for A3 on a refund of another return). The deliverable is the plan, the frozen selection and the rule.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Sample size; deviations the plan allows | 59; 0 | 2 |
| Key items; amount | 7; $31,628.48 | 3 |
| Remainder; amount | 215; $185,089.94 | 3 |
| Upper limit at zero to three deviations | 4.95%; 7.79%; 10.29%; 12.62% | 5 |
| D1 in the remainder; in the key items | 52 of 215; 6 of 7 | 6 |
| Model draw: deviations; limit; Damaged refunds | 16; 38.2%; 11 | 6, 7 |
| Damaged refunds: all; in the remainder | 50; 48 | 7 |

> **Instructor notes, Requirement 6:** key items 7 refunds, 31,628.48 (RF-2025-000097, -000109, -000113, -000120, -000134, RF-2026-000158, -000218), examined in full and evaluated apart from the sample; remainder 215 (185,089.94). Expected parameters 95% / 5% / 0%, so n = 59 (27% of 215; the large-population table is conservative). Upper limits at n = 59: 0 deviations 4.95%, 1 7.79%, 2 10.29%, 3 12.62%; only zero deviations supports reliance at 5%, and the rule must reach at least one more deviation than the plan allows (BETA.INV holds for fewer deviations than items; every item deviating gives 100%). A1 and A2 apply to every refund; A3 applies only to refunds of Damaged returns: 50 in all (2 key items, 48 in the remainder), so a draw of 59 expects about 13.2 of them, and 13 inspected with no deviation give an upper limit of 20.58%, far above 5%: plan A3 on its own population, best by examining all 50 (no sampling risk) or by a sample sized for the 48, and record the other refunds as not applicable, never as passes. The draw covers fiscal 2024 to 2026, so it supports a conclusion on the three years together (81 of the 215 remainder refunds are dated in 2026); a conclusion as at the end of 2026 also needs evidence that the controls did not change. Data attribute (Requirement 4's definition): 52 of the 215 deviate (24.2%), and 6 of the 7 key items (by receipt date 45 and 6, the same conclusion); a sample of 59 expects 14.3, and about 93% of draws give 10 to 19 (P(X \<= 9) = 0.041, P(X \<= 19) = 0.967), with upper limits of about 27% at 10, 35% at 14, and 44% at 19: every plausible draw concludes the control is ineffective, as the population did (a draw with no deviation at all has a probability of about 3.1e-09). Point: where the data allow, a population test replaces the sample; sampling remains for evidence outside the database. No document results exist, so the deliverable is the plan, the frozen selection, and the decision rule; do not invent results.

## What a strong answer says

- **Each attribute states its evidence and its deviation,** and the third has its own population.
- **The parameters come first,** the size from the table, the key items in full, the draw frozen with its date.
- **The rule is written and dated before the test,** and no result is invented: the plan, the selection and the rule are the deliverable.
- **D1 shows the point:** the sample and the population agree, and the population is the better evidence.

A weak answer samples A3 across all refunds, or reports passes for documents nobody has seen.

## Common mistakes and how to respond

- **The wrong table column.** *Symptom:* a size of 29. *Response:* ask what the limit at no deviation is, and compare it with the tolerable rate.
- **Key items by amount only.** *Symptom:* 2 key items. *Response:* ask which customer's refunds the rule was written for.
- **The customer threshold at the refund's.** *Symptom:* 45 key items. *Response:* ask the two thresholds apart.
- **An unfrozen draw.** *Symptom:* a count that moves on recalculation. *Response:* ask where the selection is recorded.
- **A3 across the draw.** *Symptom:* 59 refunds inspected, none deviating. *Response:* ask how many were of Damaged returns.
- **Invented results.** *Symptom:* "No deviation" under A1 to A3. *Response:* ask for the document.
- **A rule written after the count.** *Symptom:* rows that stop at the count found. *Response:* ask when the rule was dated.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Three attributes, A3 on its own population | 20 | Evidence, deviation and population for each | A3 sampled across all refunds |
| Parameters and size | 15 | Named cells, size from the table | Size without parameters |
| Key items in full | 15 | Both thresholds, 7 items | The amount threshold only |
| Frozen selection | 15 | Distinct, not key, dated, with parameters | Live formula |
| Rule written first | 15 | Zero to three deviations, dated | Rule after the count |
| D1 on the sample and the population | 10 | Both, compared | Sample only |
| No invented results | 10 | Tested columns marked as such | Passes reported |

## Extensions and discussion questions

- A sample of 59 is 27% of the remainder. Explain why a finite-population correction would allow a smaller one, and why the table's size at a `2%` expected rate, 181, is 84% of it and calls for examining all.
- Discuss: when would you still sample an attribute the data can test?
- Discuss: the sample's limit is 38.2%. What can the committee do with it, and what can it not?
