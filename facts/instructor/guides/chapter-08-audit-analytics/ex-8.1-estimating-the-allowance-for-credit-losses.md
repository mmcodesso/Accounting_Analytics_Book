---
note: ch08.ex1
uses: [ch08.g1]
title: Estimating the Allowance for Credit Losses
kind: exercise
number: '8.1'
unit: '8'
perspective: financial
tool: excel
minutes: 90
solution: "Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheet Ex 8.1, with the LossRate column of the Buckets Table and column E of the Aging worksheet"
figures:
  - id: IF-08-1-A
    kind: excel-mock
    purpose: The Aging worksheet after requirement 1, with the expected credit loss beside the aging and the loss rates in the Buckets Table.
    shows: "The Aging worksheet: columns A to D as in Tutorial 8.2, then column E, Expected credit loss, with an amount for each bucket and the total outlined, and the E4 formula in the formula bar. To the right, the Buckets Table with its LossRate column as percentages. Below the aging, the three reconciliation rows of Tutorial 8.2 show that the opening line is in neither the aging nor the estimate."
    data: The aging of the open invoices at the as-of date and the five proposed rates (the Expected results table).
---
{% set g = ch08_g1 %}
# Exercise 8.1: Estimating the Allowance for Credit Losses

{{ header() }}

## Purpose and learning outcomes

Tutorial 8.2 ended with two findings: a receivables balance with no invoice detail, and no allowance anywhere in the ledger. This exercise has students act on the second without mishandling the first. An estimate from loss rates is arithmetic; deciding what belongs in the base is the accounting. The analytics type is predictive (an expected loss) on a descriptive aging.

By the end, students can:

- apply a loss rate to each aging bucket with a lookup and total the expected credit loss (outcome 3);
- explain why a balance with no customer detail cannot be aged, and what evidence would settle its status (outcomes 3 and 6);
- draft the adjusting entry and say how the credit loss standard bears on the rates (outcome 3);
- write a one-page memo that separates what the data support from what they do not (outcome 6).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S2 M9 (audit procedures, analytical procedures and data analytics); IMA Reporting and Control (financial recordkeeping and statement analysis); IFAC IES 2 (a) and (f); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3 (End of Chapter 8 in Chapter08-companion.zip), with the Aging worksheet, the Buckets Table in F3:G8 and the OpenInvoices and LedgerAR queries. The chapter's tutorials already need XLOOKUP, so older versions of Excel will not do.
- **Data conditions.** GLEntry has no rows for AccountID {{ g.allowance_id }} (1030) or AccountID {{ g.bad_debt_id }} (6170). Account 1020 exceeds the {{ n|count }} open invoices by the opening line of {{ entry }}. Of the open invoices, {{ small|count }} have balances under $10: {{ g.n_old }} are 61 or more days past due, and {{ g.current.number }} (${{ g.current.balance|money }}) is not yet due. Requirement (3) asks for two cases, the write-off of all {{ small|count }} as a hypothetical and a recommended case, graded separately.
- **Verify first.** Tutorial 8.2's checkpoint should hold: Aging!C9 equals the sum of the OpenBalance column and Aging!C13 equals the opening balance.

## How to run it

Individual, about 90 minutes: 25 on requirement (1), 15 on (2), 15 on (3), 15 on (4) and 20 on the memo (5). Hold back the point of requirement (2) until a student has the larger allowance, then ask who the customer is. Give the write-off sequencing hint for (4) only after students post the entry.

{{ figure('IF-08-1-A') }}

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

**Check:** E9 is ${{ loss|money }}, {{ g.share|pct(2) }} of the open balance of ${{ total|money }}. The current and 1-30 days buckets carry almost all of it, because almost all of the balance is current or recent.

### Requirement (2): The opening balance

**Step 3. Price the unsupported balance.** On a worksheet named `Ex 8.1`, in B9, B10 and B11, enter the three formulas below, and in B12 add the allowance of Step 2 (B5 holds `=Aging!E9`).

```jinja
=SUMIFS(LedgerAR[Amount],LedgerAR[AccountID],{{ g.ar_id }},LedgerAR[SourceDocumentType],"JournalEntry")
=XLOOKUP("Over 90 days",Buckets[Bucket],Buckets[LossRate])
=ROUND(B9*B10,2)
```

**Check:** ${{ opening|money }} from {{ entry }}, a loss of ${{ g.opening_loss|money }} and a combined allowance of ${{ loss_with|money }}. **Watch for:** ${{ loss_with|money }} given as the answer. It is a sensitivity, and the requirement asks why it cannot be the estimate.

**Step 4. Say what the data cannot tell.** The model answer makes four points. The entry posted the balance as one line on the conversion date, with no customer, invoice, invoice date or due date, so there is nothing to age. Every receipt in the extract is applied to an invoice, so nothing has reduced it. A balance that cannot be tied to a customer cannot be confirmed or collected, so the question is whether it belongs in receivables at all. The controller should obtain the customer detail from the conversion date and age that; a correction is for management and the auditor to decide.

### Requirement (3): Small balances

**Step 5. Count and total them.** In B18 and B19 enter these two formulas.

```
=COUNTIF(OpenInvoices[OpenBalance],"<10")
=SUMIF(OpenInvoices[OpenBalance],"<10")
```

The model answer spills the list, oldest first, with one formula, and students may copy a filtered view instead.

```
=LET(k,OpenInvoices[OpenBalance]<10,SORTBY(FILTER(HSTACK(OpenInvoices[InvoiceNumber],OpenInvoices[CustomerName],OpenInvoices[DueDate],OpenInvoices[DaysPastDue],OpenInvoices[Bucket],OpenInvoices[OpenBalance]),k),FILTER(OpenInvoices[DaysPastDue],k),-1))
```

**Check:** {{ small|count }} invoices totaling ${{ small_total|money }}. One is current; the other {{ g.n_old }} are 61 or more days past due, from ${{ low|money }} to ${{ high|money }}.

**Step 6. Show the aging without them.** Below the list of Step 5, build a second table. In the model answer its headings are in A34:H34 (adjust the row numbers to your layout): Bucket, Invoices, Open balance, Write-off count, Invoices after, Balance after, Loss rate and Expected loss after. A35:C35 repeat Aging!A4:C4, E35 is `=B35-D35`, and the others are below. Copy row 35 through row 39, put `Total` in A40, add B35:F39 and H35:H39 by column, and leave G40 blank.

```
D35 =COUNTIFS(OpenInvoices[Bucket],A35,OpenInvoices[OpenBalance],"<10")
F35 =C35-SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[Bucket],A35,OpenInvoices[OpenBalance],"<10")
G35 =XLOOKUP(A35,Buckets[Bucket],Buckets[LossRate])
H35 =ROUND(F35*G35,2)
```

**Check:** writing off all {{ small|count }}, the required hypothetical, removes ${{ small_total|money }} and lowers the expected loss from ${{ loss|money }} to ${{ g.after_all|money }}. The two oldest buckets fall from {{ g.old_before }} invoices to {{ g.old_after }}.

For the recommended case, copy the table below it (A43:H49 in the model answer) and add the criterion `OpenInvoices[DaysPastDue],">=61"` to the COUNTIFS of D44 and the SUMIFS of F44.

```
D44 =COUNTIFS(OpenInvoices[Bucket],A44,OpenInvoices[OpenBalance],"<10",OpenInvoices[DaysPastDue],">=61")
F44 =C44-SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[Bucket],A44,OpenInvoices[OpenBalance],"<10",OpenInvoices[DaysPastDue],">=61")
```

**Check:** the {{ g.n_old }} old balances total ${{ g.old_total|money }}, the expected loss falls to ${{ g.after_old|money }} and the gross supported receivables are ${{ g.gross_after|money }}. {{ g.current.number }} (${{ g.current.balance|money }}) stays in the Current row. **Watch for:** the all-{{ small|count }} case given as the recommendation. A small-balance policy would keep a whole invoice not yet due, even though the two cases differ in the allowance by only ${{ g.case_diff|money }}.

### Requirement (4): The entry and the standard

**Step 7. Draft the entry.** Dated {{ asof }}: debit 6170 Bad Debt Expense and credit 1030 Allowance for Doubtful Accounts for ${{ loss|money }}. Add a check that debits equal credits and a count of the GL rows in the two accounts.

**Check:** the count is {{ g.gl_rows }}, so this would be the first allowance in the extract. If the {{ g.n_old }} old balances are then written off, the sequence matters. With the estimate recorded first, the write-off is charged to the allowance (debit 1030, credit 1020, ${{ g.old_total|money }}), which leaves ${{ g.remaining|money }}, and ${{ g.topup|money }} more is debited to 6170. With the write-off first, against a zero allowance, the later expense and allowance entry is ${{ g.seq_after|money }}. Both end with gross supported receivables of ${{ g.gross_after|money }} and an allowance of ${{ g.after_old|money }}.

**Step 8. Tie the rates to the standard.** The FASB standard (2016) accepts an aging schedule and requires the estimate to reflect the risk of loss even when it is remote, adjusting historical bucket rates for current conditions and reasonable and supportable forecasts. The data hold no write-off history, so the proposed rates are not Charles River's own experience: document them, raise them if conditions or forecasts worsen, lower them only with evidence, and revisit them at each reporting date. The practical expedient for current receivables (FASB, 2025) and the private-company election to consider later collections are not elected, as the exercise assumes.

### Requirement (5): The memo

**Step 9. Outline the memo.** To the controller. First paragraph: the estimate (the total, its share of the open balance, where it comes from) and the recommended entry. Second: the opening balance, why it is not reserved as if it were an aged receivable, and the request for the conversion-date detail. Third: the small balances, the write-off of the old ones and the effect on the allowance.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
{% for r in g.rows %}
| {{ r.label }}: invoices, balance, rate, expected loss | {{ r.n|count }}; ${{ r.amount|money }}; {{ r.rate|pct(1) }}; ${{ r.loss|money }} | 2 |
{% endfor %}
| Allowance from the aging | ${{ loss|money }} | 2 |
| Opening balance, loss at 40 percent, combined allowance | ${{ opening|money }}; ${{ g.opening_loss|money }}; ${{ loss_with|money }} | 3 |
| Count and total of the open invoices under $10 | {{ small|count }}; ${{ small_total|money }} | 5 |
| All {{ small|count }} written off: removed, expected loss after | ${{ small_total|money }}; ${{ g.after_all|money }} | 6 |
| The {{ g.n_old }} old ones written off: removed, expected loss after, gross receivables after | ${{ g.old_total|money }}; ${{ g.after_old|money }}; ${{ g.gross_after|money }} | 6 |
| Allowance left after the write-off, the top-up, the entry if the write-off is first | ${{ g.remaining|money }}; ${{ g.topup|money }}; ${{ g.seq_after|money }} | 7 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The larger allowance as a sensitivity, the reasons the balance cannot be aged (no customer, no dates, no receipt applied to it), the request for the conversion-date detail, and a statement that any correction is a decision for management and the auditor.
- **Requirement (3).** The all-{{ small|count }} calculation as the hypothetical, and a separate recommended case that keeps the current invoice and says why.
- **Requirement (4).** The entry with its accounts and amount, the statement that the rates are an assumption without Charles River's history behind them, and a reason to adjust them (current conditions, forecasts).
- **Requirement (5).** A recommendation in the first paragraph, an estimate that is not padded with the unsupported balance, and a limit on what the extract can show.

A weak answer books the larger allowance, calls the balance uncollectible, or leaves the memo with no recommendation.

## Common mistakes and how to respond

- **Rates as whole numbers.** *Symptom:* an expected loss larger than its bucket. *Response:* ask what 5 percent is as a number in Excel.
- **The opening balance aged and reserved.** *Symptom:* the entry or memo uses the larger allowance. *Response:* ask which customer owes it.
- **A rate range outside the Table.** *Symptom:* the structured reference does not resolve. *Response:* ask where the Buckets Table ends.
- **The entry reversed.** *Symptom:* a credit to expense. *Response:* ask which account the estimate reduces.
- **The all-{{ small|count }} case taken as the recommendation.** *Symptom:* the memo writes off the current invoice with the rest. *Response:* credit the hypothetical, then ask whether the current invoice is a residual or an invoice.
- **No sequencing.** *Symptom:* a write-off to expense and an unchanged allowance. *Response:* ask what the allowance is for.
- **A memo that restates the tutorial.** *Symptom:* no recommendation. *Response:* ask what you want the controller to do.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: loss rates and expected loss | 25 | LossRate in the Buckets Table, lookup formula, correct total | Right total with typed values |
| Requirement 2: the opening balance | 25 | Sensitivity computed, reasons given for why its age cannot be known | Computed but aged as a receivable |
| Requirement 3: small balances | 15 | List, total, the aging with all written off, and a separate recommended aging | List without the aging, or one case only |
| Requirement 4: the entry and the standard | 15 | Accounts and amount right, rates tied to the standard | Entry without the standard |
| Requirement 5: memo | 20 | Recommendation, estimate, opening balance, small balances | One topic missing |

## Extensions and discussion questions

- Build a data table of the allowance against the 1-30 days rate and the over 90 days rate, as in Tutorial 7.3. Which rate does the answer depend on?
- Aged by segment, is the allowance concentrated in some customers? Add CustomerSegment to OpenInvoices as in Exercise 8.3, apply the loss rates, and group the estimated losses by segment.
- Discuss: who should own the loss rates, the credit department that proposes them or the controller who signs the estimate?
- Discuss: Exercise 8.2 finds the same pattern in payables. Why is an unsupported liability a different kind of risk from an unsupported asset?
