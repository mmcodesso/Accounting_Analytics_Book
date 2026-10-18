---
note: ch07.ex5
uses: [ch07.g5]
title: Regression-Based Expectations for Revenue and Commissions
kind: exercise
number: '7.5'
unit: '7'
perspective: auditing
tool: excel
minutes: 90
solution: "Chapter07-exercises.zip: Chapter 7 Exercises - Solutions.xlsx, sheets Ex 7.5, Ex 7.5 Revenue36, Ex 7.5 Revenue35 and Ex 7.5 Commission, with the queries GLCommission, SalesCommissionAccrual and AccrualDates"
figures:
  - id: IF-07-5-A
    kind: chart
    purpose: The 2026 commission differences against the senior's threshold, to show the offsetting pair and the quiet months.
    shows: "A column chart of the twelve months of the report year. Each column is the difference between recorded commission expense and the expectation, as a percentage of the expectation, with two horizontal lines at plus and minus 3 percent. The columns beyond the lines are coral, the others gray, and the two consecutive flagged months of opposite sign are bracketed. The axis includes zero."
    data: The Difference % column of the Ex 7.5 sheet for the report year (the Expected results).
---
{% set g = ch07_g5 %}
# Exercise 7.5: Regression-Based Expectations for Revenue and Commissions

{{ header() }}

## Purpose and learning outcomes

Chapter 1 described a regression-based expectation as a substantive analytical procedure. This exercise compares an imprecise revenue expectation with a more closely fitted commission expectation. A threshold set in advance identifies differences for follow-up, but a high R Square or an unflagged month does not by itself establish sufficient evidence. The reliability of the data, the precision required and corroborating records must also be assessed. It practices a monthly series, a regression with and without an influential month, a threshold set in advance and a follow-up that goes to the records. The analytics type is predictive, in the auditor's use.

By the end, students can:

- judge an expectation by its standard error against the misstatement it must detect, not by its R Square alone (outcomes 1 and 6);
- set a regression-based expectation from earlier years and flag the months that differ by more than a stated threshold (outcome 6);
- follow up a flagged pair of months to the records and reconcile an expense to its source documents (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures and audit data analytics) and BAR M10; IMA Statistical Analysis, Applied Forecasting, and Predictive & Prescriptive Analytics; IFAC IES 2 (f) and IES 4 (a); AACSB A5 parts 5.1 and 5.2.

## Before you assign

- **Files and software.** The analysis workbook at the end of Chapter 7's tutorials, with InvoiceLines and the SalesInvoice Table, and the Analysis ToolPak. The model answer uses live RSQ, STEYX and SLOPE formulas beside the ToolPak's output.
- **Data conditions.** GLOpex holds only the report year, so students import the ledger again, with **Transform Data**, and filter to the commission account (AccountID {{ g.account_id }}) and away from the JournalEntry source, whose only rows on this account are the {{ g.closes }} year-end closes. The commission postings come from SalesCommissionAccrual and SalesCommissionAdjustment documents. The accruals carry {{ g.n_segments }} commission rates, one for each customer segment, from {{ low|pct(1) }} to {{ high|pct(1) }}.
- **Verify first.** Run requirement 4 once, and read the signs of the flagged months before class: the follow-up depends on them.

## How to run it

Individual, about 90 minutes: 20 for the monthly table (requirement 1), 20 for the revenue regressions (2), 10 for the commission expectation (3), 20 for the flags and the follow-up (4), 10 for the reconciliation (5) and 10 for the memo. Hold back the idea of looking at the signs of consecutive months until students have the flags. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): The monthly table

**Step 1. Import the commission postings.** Choose **Data > Get Data > From File > From Excel Workbook**, select T3_GLEntry and click **Transform Data**. Name the query `GLCommission`, filter AccountID to {{ g.account_id }} and SourceDocumentType to exclude JournalEntry, add the column `Amount` as `[Debit] - [Credit]`, and load it.

**Step 2. Build the table on a worksheet named `Ex 7.5`.** Use columns A to D for `Month`, `Revenue`, `InvoiceCount` and `CommissionExpense`. In A4 `=DATE({{ d.F }},1,1)`, below it `=EDATE(A4,1)` to row 39, then in B4, C4 and D4, filled down to row 39:

```
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[InvoiceDate],">="&$A4,InvoiceLines[InvoiceDate],"<"&EDATE($A4,1))
=COUNTIFS(SalesInvoice[InvoiceDate],">="&$A4,SalesInvoice[InvoiceDate],"<"&EDATE($A4,1))
=SUMIFS(GLCommission[Amount],GLCommission[PostingDate],">="&$A4,GLCommission[PostingDate],"<"&EDATE($A4,1))
```

Add the control totals in row 40 against the Tables, with money rounded to the cent so that a binary residue of a fraction of a cent does not show as a difference, and counts compared exactly:

```
B40  =ROUND(SUM(B4:B39)-SUM(InvoiceLines[LineTotal]),2)
C40  =SUM(C4:C39)-ROWS(SalesInvoice[SalesInvoiceID])
D40  =ROUND(SUM(D4:D39)-SUM(GLCommission[Amount]),2)
```

The controls are in the model answer and are a plus in grading.

**Check:** {{ g.n_months }} months, the controls at zero, {{ g.invoices_all|count }} invoices in all, {{ g.gl_rows|count }} commission postings. **Watch for:** the closing entries left in. They credit the account at each year-end, so December looks wrong.

### Requirement (2): Revenue on invoices

**Step 3. Regress.** Run the ToolPak's **Regression** twice, with revenue as Y and invoices as X: once on all months (rows 4 to 39) and once without the first month (rows 5 to 39), with **Labels** cleared both times because the ranges leave out the headings. The model answer also keeps live formulas beside them: `=RSQ(B4:B39,C4:C39)`, `=STEYX(B4:B39,C4:C39)` and `=SLOPE(B5:B39,C5:C39)`.

**Check:** R Square {{ r2_with|num(3) }} with the first month and {{ r2_without|num(3) }} without; the slope without it is ${{ slope|num(0) }} per invoice; the standard error is ${{ g.se_all|num(0) }} with the first month and about ${{ se|num(0) }} without it, {{ se_share|pct(1) }} of the average month (${{ average|money }}). Five percent of the average month is ${{ g.five|num(0) }}, below one standard error: the expectation could not reliably detect that misstatement. **Watch for:** a student who reads the R Square and stops.

### Requirement (3): The commission expectation

**Step 4. Fit the earlier years and project the report year.** Regress commission expense (D4:D27) on revenue (B4:B27), the {{ g.observations }} months of {{ d.F }} and {{ d.P }}. Label J18 `Intercept` and J19 `Slope`, enter `=INTERCEPT(D4:D27,B4:B27)` in K18 and `=SLOPE(D4:D27,B4:B27)` in K19, and compare them with the ToolPak's coefficients. In E28:E39 enter `=$K$18+$K$19*B28`, which uses the unrounded coefficients.

**Check:** intercept ${{ a|num(2) }}, slope {{ b|num(5) }} (a commission rate of that many dollars per dollar of revenue), R Square {{ r2|num(3) }}.

### Requirement (4): Flags and follow-up

**Step 5. Flag the differences.** In F `=D28-E28`, in G `=F28/E28`, and in H `=IF(ABS(G28)>0.03,"Investigate","")`.

**Check:** {{ flagged|length }} months are flagged:{% for r in flagged %} {{ r.month }} {% if r.diff < 0 %}-${{ (r.diff|abs)|money }}{% else %}+${{ r.diff|money }}{% endif %} ({{ r.pct|spct(1) }}){% if not loop.last %};{% endif %}{% endfor %}. Every other month is within {{ within }}. **Watch for:** the percentage divided by the recorded amount, not the expectation.

{{ figure('IF-07-5-A') }}

**Step 6. Follow up the flags.** Import and load T27_SalesCommissionAccrual as `SalesCommissionAccrual` first (**Close & Load To**, **Table**, new worksheet), because the follow-up reads it. {{ pair[0] }} and {{ pair[1] }} are consecutive months with opposite signs that nearly offset. A shift between the two months is one hypothesis to test, and the offsetting signs do not establish it. {{ g.singles|map(attribute='name')|join(' and ') }} has no offsetting partner and needs the same evidence.

a. Compare each accrual's date with its invoice's date. In a reference query of SalesCommissionAccrual, merge SalesInvoice on SalesInvoiceID with a left outer join, expand InvoiceDate, check that the row count is unchanged and no key is unmatched, and add one column that compares AccrualDate with InvoiceDate and one that compares their month starts. {{ misdated|count }} of {{ accrual_rows|count }} accruals differ, {{ other_month|count }} of them across a month-end: timing does not explain the pair.
b. Compute the accrual rate and the lowest-rate segment's share of the commission base by month (SUMIFS on CommissionAmount and CommissionBaseAmount by AccrualDate), the weighted rate being total commission over total base. The lowest-rate segment is {{ g.low_segment }}.
c. Compare each flagged month's accruals with the signed SalesCommissionAdjustment postings in GLCommission.

**Check:** {{ g.low_segment }} was {{ share[0]|pct(0) }} of {{ pair[0] }}'s commission base against {{ share[1]|pct(0) }} of {{ pair[1] }}'s ({{ share_year|pct(0) }} for the year), so the accrual rate was {{ rate[0]|pct(2) }} against {{ rate[1]|pct(2) }}. A regression on total revenue cannot see the mix.{% for s in g.singles %} In {{ s.name }} the share was {{ s.share|pct(0) }} and the rate {{ s.rate|pct(2) }}, the direction that a month above the expectation needs.{% endfor %} The signed adjustments posted in the flagged months are {% for f in g.flags %}-${{ (f.adj_amount|abs)|money }} in {{ f.name }} ({{ f.adj_rows|count }} rows){{ ', ' if not loop.last }}{% endfor %}, each well under a quarter of that month's difference, so they do not explain the flags either. The mix is consistent with the signs, and recomputing a sample of accruals would test it.

### Requirement (5): The reconciliation

**Step 7. Reconcile the accruals to the ledger.** In a block beside the table, total the accruals dated in the report year (SalesCommissionAccrual, loaded in Step 6) and the ledger's postings by source document type:

```jinja
=SUMIFS(SalesCommissionAccrual[CommissionAmount],SalesCommissionAccrual[AccrualDate],">="&DATE({{ d.C }},1,1),SalesCommissionAccrual[AccrualDate],"<"&DATE({{ d.N }},1,1))
=SUMIFS(GLCommission[Amount],GLCommission[FiscalYear],{{ d.C }},GLCommission[SourceDocumentType],"SalesCommissionAdjustment")
```

**Check:** accruals ${{ accruals|money }} plus the {{ adj_rows|count }} signed SalesCommissionAdjustment postings (-${{ adj_amount|money }}) equal the ledger's ${{ gl|money }}. The postings are already negative, so they are added, not subtracted. The source document type that explains the difference is SalesCommissionAdjustment, which reverses commissions on credit memos.

### Memo

**Step 8. Write it.** An outline: the revenue expectation and why it is not precise enough; the commission expectation and its fit; the flagged months and the evidence for each; the reconciliation.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| R Square, revenue on invoices: with and without the first month | {{ r2_with|num(3) }}; {{ r2_without|num(3) }} | 3 |
| Slope without the first month | ${{ slope|num(0) }} | 3 |
| Standard error without the first month; share of the average month | ${{ se|num(0) }}; {{ se_share|pct(1) }} | 3 |
| Commission on revenue: intercept; slope; R Square | ${{ a|num(2) }}; {{ b|num(5) }}; {{ r2|num(3) }} | 4 |
{% for r in flagged %}
| {{ r.month }}: difference; percent | {% if r.diff < 0 %}-${{ (r.diff|abs)|money }}{% else %}+${{ r.diff|money }}{% endif %}; {{ r.pct|spct(1) }} | 5 |
{% endfor %}
| Accruals dated in {{ d.C }}; adjustments; ledger | ${{ accruals|money }}; ${{ adj_amount|money }}; ${{ gl|money }} | 7 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The fit looks good with the first month and much worse without it. The standard error is larger than five percent of an average month, so differences of that size are lost in the scatter. The expectation is not precise enough for a substantive procedure at that level.
- **Requirement (4).** The commission expectation fits closely, so a three percent threshold flags few months. For each flagged month the evidence is the accrual dates, the rates applied (the customer mix) and the credit-memo adjustments. The accrual dates do not explain the offsetting pair, the customer mix is consistent with it and with the third flagged month, and recomputing a sample of accruals would test that. A stronger expectation would multiply each segment's revenue by its rate.
- **The memo.** It reports flags as items to follow up, not as misstatements, and says how the reconciliation to the source documents closes.

A weak answer calls the offsetting pair "timing" without looking at the dates, or concludes that the commission is misstated because {{ flagged|length }} months are flagged.

## Common mistakes and how to respond

- **R Square as precision.** *Symptom:* "R Square {{ r2_with|num(2) }}, so the expectation is good". *Response:* ask what a five percent misstatement looks like next to the standard error.
- **The fit includes the report year.** *Symptom:* few flags. *Cause:* the expectation is not independent of the data it tests. *Response:* ask which months the line is allowed to see.
- **Closing entries left in.** *Symptom:* December commission far off in every year. *Response:* ask what the year-end entry does to the account.
- **Percent on the recorded amount.** *Symptom:* slightly different percentages. *Response:* ask what the expectation is.
- **Timing assumed.** *Symptom:* "the months offset, so it is timing". *Response:* ask which dates you compared.
- **A reconciliation that stops at the total.** *Symptom:* a difference with no source named. *Response:* ask for the ledger rows by source document type.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: monthly table | 15 | Three series, closing entries excluded | A series missing, or the closes left in |
| Requirement 2: revenue regressions | 20 | Both fits, standard error compared with five percent | R Square only |
| Requirement 3: expectation | 15 | Fitted to the earlier years, applied to the report year | Fitted to all months |
| Requirement 4: flags and follow-up | 25 | Flags correct, signs noticed, specific evidence | Generic evidence |
| Requirement 5: reconciliation | 10 | Accruals, adjustments and ledger agree | Source type unnamed |
| Memo | 15 | Conclusions bounded, evidence named | Overstated conclusion |

## Extensions and discussion questions

- Build the expectation by segment: each segment's revenue times its rate. How many months are still flagged?
- Change the threshold to two percent. What changes in the follow-up?
- Discuss: the standard on substantive analytical procedures asks for expectations precise enough to identify material misstatements and prefers monthly amounts to annual ones. Does this exercise show why?
- Discuss: which of the flagged months would you test with documents, and how would you choose?
