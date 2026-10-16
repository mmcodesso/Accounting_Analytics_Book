# Exercise 8.3: Customer Credit Exposure

| | |
|---|---|
| Unit | Chapter 8: Audit Analytics in Excel |
| Item | Exercise 8.3 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter08-exercises.zip: Chapter 8 Exercises - Solutions.xlsx, sheet Ex 8.3, with the PivotTable PivotEx83 and the edited Customers and OpenInvoices queries |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The credit manager wants three answers from the aging: who owes the most, who is over a limit, and how concentrated the receivables are. The exercise turns Tutorial 8.2's invoice-level detail into a customer-level view, and its useful surprise is that the customers over their limits have nothing past due. It practices editing a tutorial query in the copy, a PivotTable with Max, a ratio beside it, LARGE with SEQUENCE and SUMIFS by group. The analytics type is descriptive, with a recommendation.

By the end, students can:

- carry two more columns through a chain of queries and a PivotTable (outcome 3);
- compare a balance with a limit and separate an excess from a past-due amount (outcome 3);
- measure concentration with the share of the largest customers and summarize by segment and terms (outcome 3);
- recommend credit actions that the evidence supports (outcome 3).

**Competencies practiced.** CPA Evolution BAR M9 (financial statement analysis and working capital) and Core S1 M4 (financial statement analysis and performance measures); IMA Reporting and Control (financial statement analysis) and Strategy, Planning and Performance (performance management); IFAC IES 2 (b) and (g); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of AuditAnalytics.xlsx made after Tutorial 8.3, with the Customers and OpenInvoices queries of Tutorial 8.2. The exercise edits them in the copy only.
- **Data conditions.** The customers with an open balance number 203, across 1,079 invoices, so a customer has several open invoices on average. CreditLimit, PaymentTerms and CustomerSegment are columns of Customer. Two different customers share a name, so grouping by name alone gives 202 rows instead of 203. Every invoice's due date follows its customer's PaymentTerms.
- **Verify first.** Tutorial 8.2's aging total (Aging!C9) should equal the open balance of $4,418,804.32.

## How to run it

Individual, about 75 minutes: 20 for the queries and the PivotTable (1), 20 for the limit comparison (2), 15 for concentration and the groups (3) and 20 for the memo (4). Hold back the hint about past-due balances until a student has the list of customers over their limits. Collect the worksheet and the memo.

## Step-by-step solution

### Requirement (1): The customer ranking

**Step 1. Carry the two columns through.**

a. Choose **Data > Get Data > Launch Power Query Editor**. In Customers, reopen the step that keeps columns (**Choose Columns**) and add CustomerSegment and PaymentTerms.
b. In OpenInvoices, reopen the step that expands Customers and tick the two new columns, without the prefix.
c. Choose **Close & Load** and **Data > Refresh All**.

**Step 2. Build the PivotTable.** Select a cell in the OpenInvoices Table, choose **Insert > PivotTable** and place it on a new worksheet `Ex 8.3`. Put CustomerID and CustomerName in the **Rows** area, show them as two columns without subtotals (the tabular report layout), put the Sum of OpenBalance in the **Values** area, and sort the customers from the largest balance to the smallest.

**Check:** 203 rows, the first Wright PLC with $251,470.60. **Watch for:** the PivotTable left in its default order (customer 1 first), a grouping by name alone (202 rows), and the new fields missing, which means the OpenInvoices step was not edited or the PivotTable not refreshed.

### Requirement (2): The credit limits

**Step 3. Compare each balance with its limit.**

a. Add CreditLimit to the **Values** area and set it to **Max**. Every invoice of a customer carries the same limit.
b. In the column beside the PivotTable, calculate the balance as a share of the limit, and copy it down the customer rows.
c. List the customers whose share is above 100 percent. The model answer spills them with one LET and FILTER formula; students may filter the new column instead.
d. For each, total the invoices that are past due.

```
=IF(D4>0,C4/D4,"")
=SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[CustomerID],G4,OpenInvoices[DaysPastDue],">0")
```

**Check:** five customers are over their limits (see the Expected results), and none has a past-due balance. **Watch for:** **Sum** of CreditLimit, which multiplies the limit by the customer's number of open invoices (about 5.3 on average), so that almost nobody appears to be over.

### Requirement (3): Concentration and groups

**Step 4. Measure concentration.** In one cell sum the five largest balances, and in another the ten largest, then divide each by the total. Use the customer rows only, not the Grand Total row.

```
=SUM(LARGE(C4:C206,SEQUENCE(5)))
```

**Check:** the five largest hold 15.7% and the ten largest 24.7% of $4,418,804.32. All five of the largest are Strategic customers.

**Step 5. Summarize by segment and by terms.** For each CustomerSegment and each PaymentTerms value, total the open balance and the past-due balance with SUMIFS, and compute the past-due share. The model answer adds a count of distinct customers with UNIQUE and FILTER.

```
=SUMIFS(OpenInvoices[OpenBalance],OpenInvoices[PaymentTerms],G27,OpenInvoices[DaysPastDue],">0")
```

**Check:** the groups in the Expected results below. The past-due share falls as the terms lengthen.

### Requirement (4): The memo

**Step 6. Outline the memo.** To the credit manager. Concentration: the receivables are spread out, with the largest customer Wright PLC at 5.7%. Customers over their limits, each with the limit and the balance, and the fact that the excess is current billing. Past due by terms. Recommendations with reasons: review the limits and the approvals of the customers over them before stopping shipments, make the system route an order that would exceed a limit for approval, focus collection on the shorter terms, and watch the largest balances.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Customers with an open balance, and the open balance | 203; $4,418,804.32 | 2 |
| The five largest customers, and the ten largest | 15.7%; 24.7% | 4 |
| Past-due balance, and its share of the open balance | $762,832.82; 17.3% | 5 |
| Miller-Hernandez (Strategic, Net 60): balance and limit | $143,506.09; $125,394.78 | 3 |
| Sanchez, Lee and Jones (Wholesale, Net 45): balance and limit | $82,088.52; $58,146.44 | 3 |
| James, Gill and Campbell (Design Trade, Net 90): balance and limit | $34,917.32; $34,690.20 | 3 |
| Jenkins Ltd (Small Business, Net 60): balance and limit | $14,833.81; $11,873.67 | 3 |
| Santos-Salazar (Small Business, Net 60): balance and limit | $12,815.16; $11,868.51 | 3 |
| Wholesale: open, past due, share, customers | $2,270,774.32; $435,793.53; 19.2%; 79 | 5 |
| Strategic: open, past due, share, customers | $1,323,927.91; $206,756.50; 15.6%; 21 | 5 |
| Design Trade: open, past due, share, customers | $381,811.50; $67,357.17; 17.6%; 41 | 5 |
| Design Services: open, past due, share, customers | $252,933.36; $33,371.49; 13.2%; 16 | 5 |
| Small Business: open, past due, share, customers | $189,357.23; $19,554.13; 10.3%; 46 | 5 |
| Net 30: open, past due, share, customers | $1,394,279.02; $280,641.33; 20.1%; 88 | 5 |
| Net 45: open, past due, share, customers | $1,402,433.58; $270,357.98; 19.3%; 60 | 5 |
| Net 60: open, past due, share, customers | $1,265,864.14; $193,277.93; 15.3%; 48 | 5 |
| Net 90: open, past due, share, customers | $356,227.58; $18,555.58; 5.2%; 7 | 5 |

> **Instructor notes, Exercise 8.3:** 203 customers have open balances at 2026-12-31. Five exceed their credit limit, and none of them has any past-due balance: Miller-Hernandez 143,506.09 against 125,394.78 (Strategic, Net 60), Sanchez, Lee and Jones 82,088.52 against 58,146.44 (Wholesale, Net 45), James, Gill and Campbell 34,917.32 against 34,690.20 (Design Trade, Net 90), Jenkins Ltd 14,833.81 against 11,873.67 (Small Business, Net 60), Santos-Salazar 12,815.16 against 11,868.51 (Small Business, Net 60). None of their balance is past due at this date, so the excess comes from current billing rather than overdue amounts; that argues for reviewing the limits and how the excess was approved, rather than stopping shipments, and it says nothing about how they paid in the past. Largest balances: Wright PLC 251,470.60, Miller-Hernandez, Eaton, Robertson and Grant 105,369.89, Willis and Sons 97,530.65, Sanchez LLC 96,886.09, all Strategic. Top 5 hold 15.7% and top 10 24.7% of the open balance. By segment: Wholesale 2,270,774.32, Strategic 1,323,927.91, Design Trade 381,811.50, Design Services 252,933.36, Small Business 189,357.23. By terms (open, past due, customers): Net 30 1,394,279.02, 280,641.33, 88; Net 45 1,402,433.58, 270,357.98, 60; Net 60 1,265,864.14, 193,277.93, 48; Net 90 356,227.58, 18,555.58, 7. Every invoice's due date matches its customer's PaymentTerms.

## What a strong answer says

- **Requirement (2).** The customers over their limits, the limit and the balance of each, and the observation that nothing is past due: the excess comes from current billing, so the question is who approved the orders and whether the limits are right, not collection.
- **Requirement (4).** Concentration described by the observed shares and judged against the risk the company accepts, with the largest customer's share, the segments and terms with the most past due, and recommendations that follow from the evidence: review limits before stopping shipments, make the system enforce limits, concentrate collection effort where past-due shares are highest. It notes that a snapshot says nothing about how customers have paid in the past.

A weak answer recommends stopping shipments to the customers over their limits, or reads concentration from the number of customers and not the dollars.

## Common mistakes and how to respond

- **Sum of CreditLimit.** *Symptom:* a share of the limit far below the true one, and no customer over a limit. *Response:* ask how many invoices each customer has.
- **The default sort.** *Symptom:* the first customer is not the largest. *Response:* ask which field the PivotTable sorts by.
- **Grouping by name.** *Symptom:* one fewer row, and one customer with a balance twice the others. *Response:* ask which key identifies a customer.
- **New columns missing.** *Symptom:* PaymentTerms is not in the field list. *Response:* ask where the OpenInvoices query expands Customers.
- **A grand total inside the ranges.** *Symptom:* the largest "customer" is the total. *Response:* ask which rows are customers.
- **Excess read as overdue.** *Symptom:* "these customers do not pay". *Response:* ask what their past-due balance is.
- **A memo with no reasons.** *Symptom:* a list of actions. *Response:* ask which number supports each.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: queries and ranking | 25 | New columns reach the PivotTable, sorted by balance | Sorted by ID |
| Requirement 2: limits and past due | 25 | Max used, list of customers, past-due total for each | List without past due |
| Requirement 3: concentration and groups | 20 | Top five and ten, both group summaries | One group summary |
| Requirement 4: memo | 30 | Concentration, limits, past due, reasoned actions | Actions without reasons |

## Extensions and discussion questions

- Measure how the five customers over their limits have paid in the past: receipts against due dates from CashReceiptApplication. Does the history support a higher limit?
- Chart the share of limit used for all customers. How many are above half of their limit?
- Discuss: five customers exceed their limits with no approved exception in the data. Is that a credit problem or a control problem?
- Discuss: a low concentration is reassuring for one failing customer. What does it not protect against?
