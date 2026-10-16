# Exercise 4.6: Reviewing Price Override Approvals

| | |
|---|---|
| Unit | Chapter 4: Excel Essentials for Accounting Analytics |
| Item | Exercise 4.6 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheets Ex 4.6, Ex 4.6 PriceOverrideApproval and Ex 4.6 Employee |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise is a preliminary test of a control: a manager must approve a price below the price list before it is used. Students load the approvals, compute a discount, flag two exceptions, build a grid by requester and write the memo. The traps are in the counting: COUNTIFS cannot compare two columns of a row, and a blank approver is not an approval by someone else. The analytics type is descriptive, with a control test as the purpose.

By the end, students can:

- load a Table with Power Query and add a calculated ratio (outcome 2);
- build a helper column when a function cannot compare two columns, and count with it (outcomes 2 and 3);
- highlight two exceptions in two colors and confirm them with a slicer (outcomes 4 and 5);
- count approvals by requester without counting an empty approver as an approval (outcome 3);
- describe a control exception and propose follow-up procedures (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls) and ISC M2 (tests of internal controls); IMA Internal Control; IFAC IES 2 (f), audit, and IES 2 (g), governance, risk management and internal control; AACSB A5 part 5.1.

## Before you assign

- **A new workbook.** Students start a new workbook, so the Table is PriceOverrideApproval. In the solution file the sheets are Ex 4.6, Ex 4.6 PriceOverrideApproval and Ex 4.6 Employee, and the Employee query keeps three columns of T74_Employee. A student may instead look the names up in CharlesRiver.xlsx, as the exercise says.
- **Data conditions.** There are 412 requests: 409 Approved and 3 Pending. Every approval was made by one employee, the Sales Manager (EmployeeID 6), who is also a requester. The Pending requests have no approver and no approval date, and the same employee made all of them.
- **Dates.** RequestDate and ApprovedDate are set to the Date type with Replace current, as in Tutorial 4.1, Step 6.
- **Hint.** Make sure students know a Pending request still has an ApprovedUnitPrice. It is a requested price, not an approved one.

## How to run it

Individual, about 90 minutes: 10 loading (requirement 1), 10 the discount (2), 20 the exceptions (3), 20 the grid (4), 10 the sort (5) and 20 the memo (6). Hold back the "approved by someone else" hint until a student's grid shows an approval that does not exist. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): Load the approvals

**Step 1. Import and type the dates.**

a. In a new workbook choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx and click **Import**.
b. In the **Navigator** select **T8_PriceOverrideApproval** (and T74_Employee if you load the names) and click **Transform Data**.
c. Rename the queries `PriceOverrideApproval` and `Employee`. For RequestDate and ApprovedDate, click the type icon, choose **Date** and click **Replace current**.
d. Choose **Home > Close & Load > Close & Load To**, select **Table** and **New worksheet**.

**Check:** a Table named PriceOverrideApproval with 412 rows, and 3 empty ApprovedByEmployeeID cells.

### Requirement (2): The discount from the reference price

**Step 2. Add DiscountFromReference.** In the first empty cell right of the Table (column N) type `DiscountFromReference`. In the first data cell enter `=1-[@ApprovedUnitPrice]/[@ReferenceUnitPrice]` and format the column as a percentage.

**Check:** the column is filled to the last row and reads as a percentage. **Watch for:** a decimal fraction where a percentage should be, which means the format was skipped.

### Requirement (3): Two exceptions

**Step 3. Add the helper column.** In the next column (O) type `SelfApproved` and enter `=[@RequestedByEmployeeID]=[@ApprovedByEmployeeID]`. COUNTIFS cannot compare two columns of a row, so this column carries the comparison as TRUE or FALSE.

**Step 4. Highlight and count.**

a. Select the data cells with A2 active and add a rule with **Home > Conditional Formatting > New Rule**, **Use a formula to determine which cells to format**: `=$F2=""`, with an amber fill.
b. Add a second rule, `=$E2=$F2`, with a coral fill.
c. On `Ex 4.6` enter `=COUNTIFS(PriceOverrideApproval[ApprovedByEmployeeID],"")` and `=COUNTIFS(PriceOverrideApproval[SelfApproved],TRUE)`.
d. Choose **Table Design > Insert Slicer**, select **Status**, and enter `=SUBTOTAL(103,PriceOverrideApproval[PriceOverrideApprovalID])` and the same on ApprovedByEmployeeID. Click each status and record the results, then **Clear Filter**.

**Check:** 3 blank approvers, all Pending; 106 requests approved by the requester, all Approved. The slicer shows 409 requests with an approver on Approved, and 3 with none on Pending. The two groups do not overlap, because a blank approver never equals the requester.

### Requirement (4): The grid by requester

**Step 5. Build the grid.**

a. In a header row type `RequestedByEmployeeID`, `EmployeeName`, `JobTitle`, `Requests`, `Approved by someone else`, `Approved by the requester` and `Pending`. List the requesters' IDs below the first (6, 82, 84, 107, 108, 120), and look up their names and, in the next column, their job titles:

```
=XLOOKUP($A24,Employee[EmployeeID],Employee[EmployeeName])
```

b. In the next columns enter the four counts for the row (here the requester is in $A24):

```
=COUNTIFS(PriceOverrideApproval[RequestedByEmployeeID],$A24)
=COUNTIFS(PriceOverrideApproval[RequestedByEmployeeID],$A24,PriceOverrideApproval[Status],"Approved",PriceOverrideApproval[ApprovedByEmployeeID],"<>"&$A24,PriceOverrideApproval[ApprovedByEmployeeID],"<>")
=COUNTIFS(PriceOverrideApproval[RequestedByEmployeeID],$A24,PriceOverrideApproval[Status],"Approved",PriceOverrideApproval[ApprovedByEmployeeID],$A24)
=COUNTIFS(PriceOverrideApproval[RequestedByEmployeeID],$A24,PriceOverrideApproval[Status],"Pending")
```

c. Add a Total row. Paste the formulas down, not across.

**Check:** the grid matches the Expected results, and its total equals 412. **Watch for:** the someone-else formula without the Status test. A blank approver differs from the requester, so the requester 6 shows 3 approvals by someone else, when the answer is 0.

### Requirement (5): Sort and range

**Step 6. Sort and read the range.** Choose **Data > Sort** and sort DiscountFromReference **Largest to Smallest**. Enter the range on the Approved requests only:

```
=MINIFS(PriceOverrideApproval[DiscountFromReference],PriceOverrideApproval[Status],"Approved")
```

and a MAXIFS the same way.

**Check:** the approved discounts run from 5.7% to 10.6%, and the largest is on request 196. **Watch for:** reading the first and last rows of the sorted Table without the Status test.
The Pending requests' prices fall inside the approved range here, so the error would not change the numbers; ask for the method.

### Requirement (6): The memo

**Step 7. Find out whether the pending requests were used.** On the SalesInvoiceLine Table, filter SalesOrderLineID on the lines of the pending requests and compare UnitPrice with the ApprovedUnitPrice.

**Check:** request 2 (order line 147): 1 invoice line, 1 at the pending price; request 165 (order line 8038): 2 invoice lines, 2 at the pending price; request 294 (order line 15033): 1 invoice line, 1 at the pending price. All are billed under Segment Price List pricing, not an override.

**Step 8. Outline the half page.** Exception 1: the Sales Manager approved 106 of their own 109 requests, and no other approver appears in the records, so they show no independent review of those requests. Exception 2: requests 2, 165, and 294 are Pending, with no approver, and were all requested by the same person; the 4 lines were invoiced at the pending prices. Why it matters: a control whose only recorded approver is also a requester gives no independent check of that person's prices, and the records show no step that kept an unapproved price off an invoice. Whether the policy requires another approval, or another review compensates, is the first thing to ask. Follow-up: obtain the pricing policy and authority matrix; inspect the reasons and customer agreements for a sample of self-approved overrides; confirm the pending prices on the invoice lines; recommend an independent approver and a system block on unapproved prices.

**Check:** the memo describes exceptions, not misconduct.

## Expected results

| Requester | Name and job title | Requests | Approved by someone else | Approved by the requester | Pending |
|---|---|---:|---:|---:|---:|
| 6 | Carrie Schultz, Sales Manager | 109 | 0 | 106 | 3 |
| 82 | Rachel Schmidt, Account Executive | 44 | 44 | 0 | 0 |
| 84 | Connie Freeman, Sales Representative | 76 | 76 | 0 | 0 |
| 107 | Molly Lara, Account Executive | 80 | 80 | 0 | 0 |
| 108 | Jeremiah Mooney, Sales Representative | 31 | 31 | 0 | 0 |
| 120 | John Crosby, Account Executive | 72 | 72 | 0 | 0 |
| Requests; Approved; Pending | 412; 409; 3 | | | | |
| Blank approver; self-approved | 3; 106 | | | | |
| Approved discounts, smallest to largest | 5.7% to 10.6% | | | | |

![A mock of the requester grid on Ex 4.6, with the Status slicer and the SUBTOTAL cells that show the Pending requests have no approver.](../figures/chapter-04-excel-essentials/IF-04-6-A.pdf)

> **Instructor notes, Exercise 4.6:** 412 requests; 409 Approved, 3 Pending. All 409 approvals were made by EmployeeID 6 (Carrie Schultz, Sales Manager). Requests by requester: EmployeeID 6 109, 82 44, 84 76, 107 80, 108 31, 120 72. The Sales Manager approved 106 of her own 109 requests; her other 3 requests are the 3 Pending ones (IDs 2, 165, and 294), which have no approver or approval date. These three are the AnomalyLog's missing\_price\_override\_approval items. On the Approved requests, DiscountFromReference ranges from about 5.7% to 10.6%, and the Pending requests' discounts fall inside that range. In the requester grid, a request counts as approved by someone else only when its Status is Approved and its approver is not the requester: a COUNTIFS that tests only ApprovedByEmployeeID against the requester's ID also counts the 3 Pending requests, whose approver is blank, as approvals by someone else. Follow-up for the pending requests: their SalesOrderLineIDs (147, 8038, 15033) were invoiced at the pending ApprovedUnitPrice under a price-list PricingMethod (AnomalyLog sale\_below\_price\_floor\_without\_approval), which students can find by filtering SalesInvoiceLine on SalesOrderLineID; the full test is part of the audit analytics later in Part II. The self-approval pattern is a design question for the authorization policy, because the only approver in the records is also a requester.

## What a strong answer says

- **Requirement (3).** The two exceptions are different: a blank approver is a missing approval, and a self-approval is an approval without independence.
- **Requirement (4).** A grid whose someone-else column tests the Status, and the observation that every requester but one was approved by the Sales Manager.
- **Requirement (6).** The design weakness, the pending prices on the invoices, and a follow-up that names evidence, with no accusation.

A weak answer concludes that the control worked because every approved request has an approver.

## Common mistakes and how to respond

- **COUNTIFS across two columns.** *Symptom:* an error or a count of one column. *Response:* build the helper column.
- **Pending counted as approved by someone else.** *Symptom:* 3 in that column for requester 6. *Response:* ask what Status means.
- **Rules that overlap or drift.** *Cause:* a missing dollar sign or the wrong active cell. *Response:* read the rule in **Manage Rules**.
- **A range read from the sorted Table.** *Response:* use MINIFS and MAXIFS with the Status test.
- **A memo that accuses.** *Response:* ask what the data cannot show about the reason for each approval.
- **Names left as IDs.** *Response:* ask who the reader of the memo would call.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: loading | 10 | Table with Date types set | Dates left as date and time |
| Requirement 2: the discount | 10 | A correct formula, formatted | Wrong denominator |
| Requirement 3: exceptions | 20 | Helper column, two rules, counts, slicer check | One exception |
| Requirement 4: grid | 25 | All four counts with the Status test, names and titles | The pending approvals counted |
| Requirement 5: range | 10 | Approved requests only | The whole Table |
| Requirement 6: memo | 25 | Both exceptions, the design reason, and the follow-up | Findings without follow-up |

## Extensions and discussion questions

- Add the customer and item of each request and see whether any customer concentrates the overrides.
- Compare the discount of each requester's approved requests, and say what a difference would and would not show.
- Discuss: who should approve the Sales Manager's own requests, and what should the system do with a Pending price?
- Discuss: Chapter 8 tests the same control with price lists and approvals together. What would you add?
