# Exercise 8.1: Estimating the Allowance for Credit Losses

| | |
|---|---|
| Unit | Chapter 8: Audit Analytics in Excel |
| Item | Exercise 8.1 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheet Ex 8.1, with the LossRate column of the Buckets Table and column E of the Aging worksheet |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial 8.2 ended with two findings: a receivables balance with no invoice detail, and no allowance anywhere in the ledger. This exercise has students act on the second without mishandling the first. An estimate from loss rates is arithmetic; deciding what belongs in the base is the accounting. The analytics type is predictive (an expected loss) on a descriptive aging.

By the end, students can:

- apply a loss rate to each aging bucket with a lookup and total the expected credit loss (outcome 3);
- explain why a balance with no customer detail cannot be aged, and what evidence would settle its status (outcomes 3 and 6);
- draft the adjusting entry and say how the credit loss standard bears on the rates (outcome 3);
- write a one-page memo that separates what the data support from what they do not (outcome 6).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S2 M9 (audit procedures, analytical procedures and data analytics); IMA Reporting and Control (financial recordkeeping, statement preparation and statement analysis); IFAC IES 2 (a) and (f); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3 (End of Chapter 8 in Chapter08-companion.zip), with the Aging worksheet, the Buckets Table in F3:G8 and the OpenInvoices and LedgerAR queries. The chapter's tutorials already need XLOOKUP, so older versions of Excel will not do.
- **Data conditions.** GLEntry has no rows for AccountID 4 (1030) or AccountID 74 (6170). Account 1020 exceeds the 1,079 open invoices by the opening line of JE-2024-000001. Of the open invoices, 10 have balances under $10: 9 are 61 or more days past due, and SI-2026-020608 ($5.20) is not yet due.
- **Verify first.** Tutorial 8.2's checkpoint should hold: Aging!C9 equals the sum of the OpenBalance column and Aging!C13 equals the opening balance. The loss rates are the credit department's assumption, not Charles River's experience.

## How to run it

Individual, about 90 minutes: 25 on requirement (1), 15 on (2), 15 on (3), 15 on (4) and 20 on the memo (5). Hold back the point of requirement (2) until a student has the larger allowance, then ask who the customer is. Give the write-off sequencing hint for (4) only after students post the entry. Collect the workbook and the memo.

> **[Figure placeholder IF-08-1-A]** The Aging worksheet after requirement 1, with the expected credit loss beside the aging and the loss rates in the Buckets Table.
> Kind: excel-mock · Shows: The Aging worksheet: columns A to D as in Tutorial 8.2, then column E, Expected credit loss, with an amount for each bucket and the total outlined, and the E4 formula in the formula bar. To the right, the Buckets Table with its LossRate column as percentages. · Data: The aging of the open invoices at the as-of date and the five proposed rates (the Expected results table). · Status: planned

## Step-by-step solution

### Requirement (1): Loss rates and expected loss

**Step 1. Add the LossRate column.**

a. On the Aging worksheet, click the cell to the right of the last header of the Buckets Table (H3) and type `LossRate`. Excel adds the column to the Table.
b. Type the five rates in the order of the Bucket column: `0.005`, `0.02`, `0.05`, `0.15` and `0.4`.
c. Format the column as percentages.

**Check:** the Table holds five rates, and Over 90 days is 40 percent. **Watch for:** rates typed as whole numbers, so that 5 percent is `5`. The expected loss of a bucket then exceeds its balance.

**Step 2. Calculate the expected loss of each bucket.**

a. In E3 type `Expected credit loss`.
b. In E4 enter the formula below and copy it to E8.
c. In E9 total E4:E8 with SUM.

```
=ROUND(C4*XLOOKUP(A4,Buckets[Bucket],Buckets[LossRate]),2)
```

**Check:** E9 is $34,106.25, 0.77% of the open balance of $4,418,804.32. The current and 1-30 days buckets carry almost all of it, because almost all of the balance is current or recent.

### Requirement (2): The opening balance

**Step 3. Price the unsupported balance.** On a worksheet named `Ex 8.1`, in B9, B10 and B11, enter the three formulas below, and in B12 add the allowance of Step 2 (B5 holds `=Aging!E9`).

```
=SUMIFS(LedgerAR[Amount],LedgerAR[AccountID],3,LedgerAR[SourceDocumentType],"JournalEntry")
=XLOOKUP("Over 90 days",Buckets[Bucket],Buckets[LossRate])
=ROUND(B9*B10,2)
```

**Check:** $380,000.00 from JE-2024-000001, a loss of $152,000.00 and a combined allowance of $186,106.25. **Watch for:** $186,106.25 given as the answer. It is a sensitivity, and the requirement asks why it cannot be the estimate.

**Step 4. Say what the data cannot tell.** The model answer makes four points. The entry posted the balance as one line on the conversion date, with no customer, invoice, invoice date or due date, so there is nothing to age. Every receipt in the extract is applied to an invoice, so nothing has reduced it. A balance that cannot be tied to a customer cannot be confirmed or collected, so the question is whether it belongs in receivables at all. The controller should obtain the customer detail from the conversion date and age that; a correction is for management and the auditor to decide.

### Requirement (3): Small balances

**Step 5. Count and total them.** In B18 and B19 enter these two formulas.

```
=COUNTIF(OpenInvoices[OpenBalance],"<10")
=SUMIF(OpenInvoices[OpenBalance],"<10")
```

To list the invoices without disturbing the Table, the model answer spills them, oldest first, with one formula. Students may copy a filtered view instead.

```
=LET(k,OpenInvoices[OpenBalance]<10,SORTBY(FILTER(HSTACK(OpenInvoices[InvoiceNumber],OpenInvoices[CustomerName],OpenInvoices[DueDate],OpenInvoices[DaysPastDue],OpenInvoices[Bucket],OpenInvoices[OpenBalance]),k),FILTER(OpenInvoices[DaysPastDue],k),-1))
```

**Check:** 10 invoices totaling $23.58. One is current; the other 9 are 61 or more days past due, from $0.03 to $9.98.

**Step 6. Show the aging without them.** Build a second table below the list with the columns Bucket, Invoices, Open balance, Written off, Invoices after, Balance after, Loss rate and Expected loss after. In the model answer these are in A35:H40, and the three working formulas for the Current row are below. Adjust the cell references to your layout.

```
=COUNTIFS(OpenInvoices[Bucket],A35,OpenInvoices[OpenBalance],"<10")
=C35-SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[Bucket],A35,OpenInvoices[OpenBalance],"<10")
=ROUND(F35*G35,2)
```

**Check:** writing off all 10 lowers the expected loss from $34,106.25 to $34,103.35, and the two oldest buckets fall from 13 invoices to 4. **Watch for:** the current invoice written off with the rest. It is a whole invoice not yet due, so a small-balance policy would keep it.

### Requirement (4): The entry and the standard

**Step 7. Draft the entry.** Dated 2026-12-31: debit 6170 Bad Debt Expense and credit 1030 Allowance for Doubtful Accounts for $34,106.25. Add a check that debits equal credits and a count of the GL rows in the two accounts.

**Check:** the count is 0, so this would be the first allowance in the extract. If the 9 old balances are then written off under a small-balance policy, the write-off is charged to the allowance (debit 1030, credit 1020, $18.38), which leaves $34,087.87. The invoices that remain need $34,103.38, so $15.51 more is debited to 6170. Accept either order if the ending allowance is right.

**Step 8. Tie the rates to the standard.** The FASB standard (2016) accepts an aging schedule and requires the estimate to reflect the risk of loss even when it is remote. Its illustration starts from historical loss rates for each bucket and adjusts them for current conditions and reasonable and supportable forecasts. The data hold no write-off history, so the proposed rates are not Charles River's own experience: they should be documented, raised if customers' conditions or the forecast worsen, lowered only with evidence, and revisited at each reporting date.

### Requirement (5): The memo

**Step 9. Outline the memo.** To the controller. First paragraph: the estimate (the total, its share of the open balance, where it comes from) and the recommended entry. Second: the opening balance, why it is not reserved as if it were an aged receivable, and the request for the conversion-date detail. Third: the small balances, the write-off of the old ones and the effect on the allowance.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Current: invoices, balance, rate, expected loss | 780; $3,655,971.50; 0.5%; $18,279.86 | 2 |
| 1-30 days: invoices, balance, rate, expected loss | 258; $745,674.84; 2.0%; $14,913.50 | 2 |
| 31-60 days: invoices, balance, rate, expected loss | 28; $16,711.26; 5.0%; $835.56 | 2 |
| 61-90 days: invoices, balance, rate, expected loss | 10; $405.41; 15.0%; $60.81 | 2 |
| Over 90 days: invoices, balance, rate, expected loss | 3; $41.31; 40.0%; $16.52 | 2 |
| Allowance from the aging | $34,106.25 | 2 |
| Opening balance, loss at 40 percent, combined allowance | $380,000.00; $152,000.00; $186,106.25 | 3 |
| Open invoices under $10, and their total | 10; $23.58 | 5 |
| Old balances written off, and the expected loss after all ten go | $18.38; $34,103.35 | 6 |
| Allowance left after charging the old balances, and the top-up | $34,087.87; $15.51 | 7 |

> **Instructor notes, Exercise 8.1:** at 2026-12-31, aging by due date (OpenBalance \> 0 after cash applications and credit memos dated on or before the as-of date): Current 780 invoices, 3,655,971.50; 1-30 days 258, 745,674.84; 31-60 days 28, 16,711.26; 61-90 days 10, 405.41; over 90 days 3, 41.31; total 1,079 invoices, 4,418,804.32. Expected losses at the given rates: 18,279.86 + 14,913.50 + 835.56 + 60.81 + 16.52 = 34,106.25. With the 380,000.00 opening balance (JE-2024-000001, account 1020) at 40%: 186,106.25. The opening balance has no invoice detail and no cash application in the extract, so its age and collectability are unknown; the honest answer is that it must be supported (conversion-date customer detail) before it can be aged or valued, and that a correction, if the evidence shows it is not a receivable, is a decision for management and the auditor, not a write-off made from the extract alone. Balances under \$10: 10 invoices totalling 23.58 (SI-2026-020608 5.20 is current; the others are 61+ days past due, from 0.03 to 9.98). Entry: Dr 6170 Bad Debt Expense, Cr 1030 Allowance for Doubtful Accounts. Neither account has any GL rows. A student who also writes off the small balances must sequence the entries: the write-off is charged to the allowance, which then needs topping up to the estimate on the invoices that remain; accept either order if the ending allowance is right. ASC 326-20-30-3 accepts aging-schedule methods and 326-20-30-10 requires the estimate to reflect risk even when remote; Example 5 (326-20-55-37 to 55-40) adjusts historical bucket rates for current conditions and forecasts.

## What a strong answer says

- **Requirement (2).** The larger allowance as a sensitivity, the reasons the balance cannot be aged (no customer, no dates, no receipt applied to it), the request for the conversion-date detail, and a statement that any correction is a decision for management and the auditor.
- **Requirement (4).** The entry with its accounts and amount, the statement that the rates are an assumption without Charles River's history behind them, and a reason to adjust them (current conditions, forecasts).
- **Requirement (5).** A recommendation in the first paragraph, an estimate that is not padded with the unsupported balance, and a limit on what the extract can show.

A weak answer books the larger allowance, calls the balance uncollectible, or leaves the memo with no recommendation.

## Common mistakes and how to respond

- **Rates as whole numbers.** *Symptom:* an expected loss larger than its bucket. *Response:* ask what 5 percent is as a number in Excel.
- **The opening balance aged and reserved.** *Symptom:* the entry or memo uses the larger allowance. *Response:* ask which customer owes it.
- **A rate range outside the Table.** *Symptom:* the structured reference does not resolve. *Response:* ask where the Buckets Table ends.
- **The entry reversed.** *Symptom:* a credit to expense. *Response:* ask which account the estimate reduces.
- **All 10 small balances written off.** *Symptom:* the current invoice vanishes from the aging. *Response:* ask whether it is a residual or an invoice.
- **No sequencing.** *Symptom:* a write-off to expense and an unchanged allowance. *Response:* ask what the allowance is for.
- **A memo that restates the tutorial.** *Symptom:* no recommendation. *Response:* ask what you want the controller to do.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: loss rates and expected loss | 25 | LossRate in the Buckets Table, lookup formula, correct total | Right total with typed values |
| Requirement 2: the opening balance | 25 | Sensitivity computed, reasons given, detail requested | Computed but aged as a receivable |
| Requirement 3: small balances | 15 | List, total and the aging after write-off | List without the aging |
| Requirement 4: the entry and the standard | 15 | Accounts and amount right, rates tied to the standard | Entry without the standard |
| Requirement 5: memo | 20 | Recommendation, estimate, opening balance, small balances | One topic missing |

## Extensions and discussion questions

- Build a data table of the allowance against the 1-30 days rate and the over 90 days rate, as in Tutorial 7.3. Which rate does the answer depend on?
- Aged by segment, is the allowance more concentrated in some customers than in others? Use the CustomerBalances query.
- Discuss: who should own the loss rates, the credit department that proposes them or the controller who signs the estimate?
- Discuss: Exercise 8.2 finds the same pattern in payables. Why is an unsupported liability a different kind of risk from an unsupported asset?
