---
note: ch02.ex5
uses: [ch02.t1, ch02.t2, ch02.ex1]
title: Data Quality Evaluation for Audit Planning
kind: exercise
number: '2.5'
unit: '2'
perspective: auditing
tool: conceptual
minutes: 75
solution: ''
figures: []
---
# Exercise 2.5: Data Quality Evaluation for Audit Planning

{{ header() }}

## Purpose and learning outcomes

An auditor decides which data can support analytics before running any. The exercise asks for that decision across four table groups, using the tests of both tutorials plus one new test, and for a classification of every problem by dimension and by what it does to an audit procedure. Students also meet a finding that is a missing-evidence problem and a possible authorization exception at once. The tests are descriptive and prepare the audit analytics of Chapters 8 and 12.

By the end, students can:

- apply the dimension tests to four table groups and report each result with a count (outcomes 2 and 4);
- classify a finding by dimension and by its effect on an audit procedure, such as revenue cutoff (outcome 3);
- separate a finding about the data from a finding about a control (outcome 5);
- recommend which tables are suitable for audit analytics and on what conditions.

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (cleansing financial data) and ISC M4 (use and management of data); IMA Data Governance and Data Literacy; IFAC IES 2 (f), audit, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.1. The analytics type is descriptive.

## Before you assign

- Students need CharlesRiver_Work.xlsx and both tutorials. Requirements (1) to (3) repeat tests they have run, so let them reuse their findings and spend the time on requirements (4) and (5).
- The exercise relies on these conditions: SalesOrder has no blank required fields; a few invoices are dated before the first shipment on their order; blank ListPrice values are by design; the ledger balances, references only existing accounts, and has a few rows with no amount; the last fiscal year holds only supplier payments; and PurchaseRequisition has rows with no approver.
- Requirement (4) is a control finding and a data finding at once. Decide how you want it classified, and read the model answer in Step 8.
- This is the longest exercise of the chapter. Consider assigning requirements (1) to (3) as a table of results and grading the memo.

## How to run it

Individual work, then a swap of memos. For about 75 minutes: 15 on requirement 1, 5 on requirement 2, 20 on requirement 3, 10 on requirement 4 and 25 on requirement 5. In the swap, each student marks the other memo against the grading table.

**Hints.** If a student wants to treat the blank approvers as a missing-value problem only, ask what the approval is for. Hold back the dimension labels until the tests are done.

## Step-by-step solution

### Requirement (1): Order-to-Cash

**Step 1. Test the required fields of SalesOrder.** Filter OrderDate, CustomerID and Status for blanks, as in Exercise 2.1.

**Check:** no blank OrderDate, CustomerID or Status ({{ ch02_ex1.required.OrderDate }}, {{ ch02_ex1.required.CustomerID }} and {{ ch02_ex1.required.Status }}).

**Step 2. Test the invoice dates against the first shipment.** Use Tutorial 2.1 Steps 6 and 7 (MINIFS, then the Check column) and filter for "Check".

**Check:** {{ ch02_t1.n_before }} invoices are dated before the first shipment on their order; {{ ch02_t1.no_ship|count }} show "No shipment" because they bill design services.

| Invoice | InvoiceDate | First shipment |
|---|---|---|
{% for r in ch02_t1.before %}
| {{ r.number }} | {{ r.date }} | {{ r.first }} |
{% endfor %}

### Requirement (2): Master Data

**Step 3. Filter Item for a blank ListPrice and read the groups.**

**Check:** {{ ch02_t1.blank_items }} blanks, in {{ ch02_t1.sizes }}. All are expected, because Charles River buys these items and does not sell them. {{ ch02_t1.sellable|count }} items have a price.

### Requirement (3): Accounting Core

**Step 4. Total the ledger.** Sum Debit and Credit (Tutorial 2.2 Step 4) and round the difference.

**Check:** ${{ ch02_t2.debit|money }} on each side, difference ${{ ch02_t2.difference|money }}.

**Step 5. Test the references to Account.** Build the distinct list of AccountID with a PivotTable and look each up in **Account**.

**Check:** {{ ch02_t2.used }} distinct accounts, {{ ch02_t2.orphans }} not found.

**Step 6. Find the rows with no amount.** Filter Debit and Credit for 0.

**Check:** {{ ch02_t2.zero[1] }} rows, all {{ ch02_t2.zero[0] }}, on one posting date, {{ ch02_t2.zero[3] }}.

**Step 7. Read the source types and the periods.** PivotTable by SourceDocumentType, then by FiscalYear and FiscalPeriod.

**Check:** {{ ch02_t2.n_source }} source types, the six that Exercise 2.2 names among them. The first period and the last two are small, and the last fiscal year ({{ ch02_t2.last_year }}) holds only supplier payments.

### Requirement (4): Procure-to-Pay

**Step 8. Filter the requisitions with no approver.**

a. On **PurchaseRequisition**, filter ApprovedByEmployeeID for blank cells.
b. Read the status bar, then read the Status, RequestDate, Quantity and EstimatedUnitCost of the rows.
c. Compute each value as Quantity times EstimatedUnitCost.

**Check:** {{ n_reqs }} of {{ total|count }} requisitions have no approver, and every one has the status Converted to PO.

| Requisition | RequestDate | Estimated value |
|---|---|---:|
{% for r in reqs %}
| {{ r.number }} | {{ r.date }} | ${{ r.value|money }} |
{% endfor %}

The values lie between ${{ low|money }} and ${{ high|money }}, just under ${{ threshold|count }}, which is the approval limit of some roles, and every one is dated January 1. A purchase order cites each of them, which is stronger evidence of the conversion than the status. A requisition converted with no approver recorded is a possible authorization failure, so the finding is a control matter as well as a blank field. Before concluding that no one approved it, ask for the approval log or a policy that allows the exception, because an approval can sit outside the extract. A field test finds it, and Chapter 8 follows it. The other requisitions show the status Approved or Converted to PO, and each of those has an approver.

**Watch for:** a memo that calls these a "missing value" and stops. The missing value is the symptom, and the approval is the point.

### Requirement (5): Classify and write the memo

**Step 9. Classify each problem.** A model table:

| Finding | Dimension | Effect on audit procedures |
|---|---|---|
| Invoices dated before the first shipment ({{ ch02_t1.n_before }}) | Accuracy | Revenue cutoff: a timing exception to investigate (the terms, the shipment and delivery evidence, the recognition policy). None crosses a year from its first shipment, and the order-level screen can miss lines shipped later |
| Blank list prices ({{ ch02_t1.blank_items }}) | By design | None; limit price tests to the items sold |
| Debits equal credits; no unmatched AccountID | Consistency (clean) | The ledger can be totalled and joined to the chart |
| Rows with no amount ({{ ch02_t2.zero[1] }}) | Accuracy and consistency | Exclude or explain; they change no total but should not be read as payments |
| First period and last two small | Timeliness | The first is the extract's first month and stays in the period; the last two are payments after year-end, out of the annual totals but used for settlement work |
| Requisitions with no approver ({{ n_reqs }}) | Completeness, and a control matter | Approval testing: follow up as an exception |

**Step 10. Outline the memo.** A strong memo has a header and the purpose; a conclusion up front (which tables are suitable and on what conditions); a table by group and dimension, as above; the tests that found nothing; and a recommendation for each table: Order-to-Cash usable with the dates noted, Master Data usable for the items sold, the Accounting Core usable for the years under review with the payments after year-end kept out of their totals, and Procure-to-Pay usable with the requisition exceptions reported separately.

**Check:** the memo fits a page and gives a verdict for each group.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Blanks in OrderDate, CustomerID, Status | {{ ch02_ex1.required.OrderDate }}, {{ ch02_ex1.required.CustomerID }}, {{ ch02_ex1.required.Status }} | Step 1 |
| Invoices dated before the first shipment; with no shipment | {{ ch02_t1.n_before }}; {{ ch02_t1.no_ship|count }} | Step 2 |
| Blank list prices | {{ ch02_t1.blank_items }} | Step 3 |
| Total debits; total credits | ${{ ch02_t2.debit|money }}; ${{ ch02_t2.credit|money }} | Step 4 |
| Unmatched AccountIDs | {{ ch02_t2.orphans }} | Step 5 |
| Rows with no amount | {{ ch02_t2.zero[1] }} | Step 6 |
| Source types | {{ ch02_t2.n_source }} | Step 7 |
| Requisitions with no approver; converted to purchase orders | {{ n_reqs }}; {{ n_reqs }} | Step 8 |

## What a strong answer says

- **Requirements (1) to (3).** Each test with its result and count, including the tests that found nothing.
- **Requirement (4).** The six requisitions, their status and the reading that this is a control exception.
- **Requirement (5).** Each problem classified, tied to an audit procedure, and a verdict for each table group.

A weak answer lists counts with no classification, treats every finding as an error, or declares the whole dataset reliable.

## Common mistakes and how to respond

- **Counts without dimensions.** *Symptom:* a table of results. *Response:* ask which dimension each test examines.
- **Every blank called an error.** *Symptom:* blank list prices in the problems. *Response:* ask who sells these items.
- **The requisitions called a missing value.** *Symptom:* "fill in the approver". *Response:* ask what the approval controls.
- **Impact missing.** *Symptom:* "accuracy problem" and nothing more. *Response:* ask which procedure the problem would distort.
- **A clean result left out.** *Symptom:* no mention of the totals or the references. *Response:* ask what the senior learns from them.
- **No verdict.** *Symptom:* findings without a recommendation by table. *Response:* ask which tables the senior could use tomorrow.
- **The edges misread.** *Symptom:* the payments after year-end counted in annual totals, or the first month dropped. *Response:* ask what the rows in each small period are and which year they belong to.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirements 1 to 3: tests with counts | 30 | Every test run, with a count and the clean results reported | One group missing, or counts missing |
| Requirement 4: the requisitions | 15 | Found, counted, status read, control reading stated | Found without the reading |
| Requirement 5: classification and impact | 30 | Each problem classified by dimension and tied to a procedure | Dimension without an impact |
| Requirement 5: memo and verdicts | 25 | One page, conclusion first, a verdict for each group, conditions | A list with no verdicts |

## Extensions and discussion questions

- Test whether any of the requisitions with no approver has a purchase order, and say what that adds. (It does, for each.)
- Add a fifth group, Payroll and Time, and name two tests you would run before using its data.
- Discuss: should a control exception found while cleaning data be reported in the data quality memo, the audit file, or both?
- Discuss: which of the groups would you start analytics on first, and why? (Chapter 8 starts with receivables, payables, journal entries and payments.)
