---
note: ch05.ex5
uses: [ch05.g5]
title: Testing for Related-Party Suppliers
kind: exercise
number: '5.5'
unit: '5'
perspective: auditing
tool: excel
minutes: 75
solution: "Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheets Ex 5.5, Ex 5.5 Supplier, Ex 5.5 Employee and Ex 5.5 DisbursementPayment"
figures:
  - id: IF-05-5-A
    kind: excel-mock
    purpose: The Supplier Table with its match key and the matched employee, filtered to the suppliers that match.
    shows: "The right-hand columns of the Supplier Table, in two strips of the same rows because the Table is wider than the window: MatchKey, EmployeeMatches and MatchedEmployeeID, then MatchedEmployee, MatchedJobTitle, PaymentCount and PaymentTotal, with the filter buttons on and the Table filtered to the rows where EmployeeMatches is greater than zero. Each match key reads in capitals as the address, a comma and a space, and the city. The formula bar shows the match key formula. Below the Table, on the Ex 5.5 worksheet, a result block lists the matched suppliers with the employee and job title for each."
    data: Supplier, Employee and DisbursementPayment (the Expected results table).
---
{% set g = ch05_g5 %}
# Exercise 5.5: Testing for Related-Party Suppliers

{{ header() }}

## Purpose and learning outcomes

Two lists share no key, and the question is whether they overlap. The exercise teaches the answer the chapter names in its lookups section: build a match key from the fields the lists do share, standardize it, and look it up. It ends in the audit habit of the unit: a match is a lead, not a conclusion. It practices Power Query loading, TRIM and UPPER, text joining, COUNTIFS and XLOOKUP, and SUMIFS across a large Table. The analytics type is descriptive, with a diagnostic purpose.

By the end, students can:

- build and standardize a match key from two columns, and explain why the key includes the city (outcome 2);
- find the rows of one Table that have a match in another, and carry the matched attributes across (outcome 4);
- total the payments to each matched supplier from a Table of about forty thousand rows (outcomes 4 and 5);
- write up a match as a lead, with the procedures that would follow it (outcome 1).

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance); IMA Data Analysis, and Internal Control; IFAC IES 2 (f), audit, and IES 4 (a), professional skepticism and professional judgment; AACSB A5 part 5.1.

## Before you assign

- **Files and software.** CharlesRiver.xlsx and a new workbook, as the exercise says. The model answer keeps all six exercises in one file, so its worksheets Ex 5.5, Ex 5.5 Supplier, Ex 5.5 Employee and Ex 5.5 DisbursementPayment stand for that new workbook, and its Supplier Table is the one Exercise 5.6 extends. Either layout works. Tell students which to use, because Exercise 5.6 says "the workbook of Exercise 5.5".
- **Load time.** The DisbursementPayment Table holds {{ g.n_payments|count }} rows. Load it to a worksheet with **Close & Load To**, and expect a pause on the load and on each SUMIFS.
- **Data conditions.** {{ g.n_suppliers|count }} suppliers and {{ g.n_employees|count }} employees. No address or city has a stray space, so TRIM changes nothing, and the as-recorded match finds the same {{ g.raw|count }} suppliers as the standardized key. The address alone finds the same suppliers too, so the effect of including the city cannot be shown in this data. The explanation in requirement (2) is an argument, and students should give it as one.
- **Who the matches are.** All {{ g.n_match|count }} matched suppliers are approved and rated Low risk. The matched employees have {{ g.n_titles|count }} different job titles, none in purchasing.

## How to run it

Pairs or individual, about 75 minutes: 15 on loading (requirement 1), 10 on the key (2), 15 on the match and the lookups (3), 10 on the payments (4) and 25 on the memo (5). Hold back the hint about XLOOKUP's not-found result until a student sees #N/A. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): Load the Tables

**Step 1. Import Supplier, Employee and DisbursementPayment.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx and click **Import**.
b. In the **Navigator**, select the **Select multiple items** check box, select **T31_Supplier**, **T74_Employee** and **T39_DisbursementPayment**, and click **Transform Data**.
c. Rename the queries `Supplier`, `Employee` and `DisbursementPayment`. Keep every column of Supplier ({{ g.supplier_columns|count }} columns). In Employee choose **Home > Choose Columns** and keep EmployeeID, EmployeeName, JobTitle, Address and City.
d. Choose **Home > Close & Load > Close & Load To**, select **Table** and **New worksheet**, and rename the worksheets `Ex 5.5 Supplier`, `Ex 5.5 Employee` and `Ex 5.5 DisbursementPayment`.

**Check:** Supplier {{ g.n_suppliers|count }} rows, Employee {{ g.n_employees|count }} with five columns, and DisbursementPayment {{ g.n_payments|count }}. **Watch for:** a plain **Close & Load**, which with Excel's default load settings sends the Tables to the Data Model and leaves no worksheets.

### Requirement (2): The match key

**Step 2. Build the key on both Tables.** In the first empty cell right of the last header of each Table, type `MatchKey` and enter the same formula:

```
=UPPER(TRIM([@Address])&", "&TRIM([@City]))
```

**Check:** the key reads in capitals as the address, a comma, a space and the city. **Watch for:** a key built on only one Table, or a different separator on each. Both sides must be built by the same formula.

**Step 3. Explain the city.** A street address is not unique on its own, so a key on the address alone can match a supplier with an unrelated employee in another town; the city makes the key identify one place. TRIM and UPPER keep spacing and case from hiding a match. The model answer adds that in this data the addresses match as recorded, so standardizing changes nothing, which belongs in the workpapers.

### Requirement (3): The matches

**Step 4. Count and carry across.** In the Supplier Table add `EmployeeMatches`, then the matched employee's name and job title. Wrap the lookup in a test on the count, so the {{ (g.n_suppliers - g.n_match)|count }} suppliers with no match return blanks instead of #N/A:

```
=COUNTIFS(Employee[MatchKey],[@MatchKey])
=IF([@EmployeeMatches]>0,XLOOKUP([@MatchKey],Employee[MatchKey],Employee[EmployeeName]),"")
```

Repeat the second formula for EmployeeID and JobTitle. Count the suppliers with a match: `=COUNTIF(Supplier[EmployeeMatches],">0")`.

**Check:** {{ n }} suppliers, each with exactly one matching employee. **Watch for:** XLOOKUP without the test. It returns #N/A for every other supplier, and a student who wraps it in IFERROR hides real errors too. A lookup returns only the first match, so the count of one is what shows nothing was skipped.

### Requirement (4): The payments

**Step 5. Total the payments.** Add `PaymentTotal` to the Supplier Table, for the matched suppliers only, and, as the model answer does, `PaymentCount` beside it:

```
=IF([@EmployeeMatches]>0,SUMIFS(DisbursementPayment[Amount],DisbursementPayment[SupplierID],[@SupplierID]),"")
=IF([@EmployeeMatches]>0,COUNTIFS(DisbursementPayment[SupplierID],[@SupplierID]),"")
```

Then state the range of payment dates the totals cover, for example with MINIFS and MAXIFS on PaymentDate for each matched supplier.

**Check:** {{ g.n_pay|count }} payments, ${{ g.paid|money }}, dated {{ g.pay_first }} to {{ g.pay_last }}. **Watch for:** a total read as one fiscal year's. The totals include {{ g.late_n|count }} payments, ${{ g.late_paid|money }}, dated after {{ g.year_end }}, so the requirement asks for the date range. A student who audits one fiscal year adds a PaymentDate criterion to both formulas and labels that total separately. Summing on the supplier name gives the same totals here, because the supplier names are unique, but SupplierID is the key that stays right when a name repeats.

### Requirement (5): The memo

**Step 6. Write the half page.** The outline: the test and its key; the {{ n }} matches, with the employee and job title for each; the payments and the dates they cover; the statement that a shared address is a recognized red flag and not proof of a related party or a fictitious vendor; the observation that the employees' roles are not in purchasing, so each relationship needs an explanation; the observation that all {{ n }} suppliers are approved and rated Low risk, so the master file's own rating does not flag them; and the next procedures: confirm ownership (registrations, the tax identification number, an inquiry of the employee), review who approved each supplier's setup and its invoices, compare prices with other suppliers of the same items, and test a sample of the payments for evidence that the goods or services were received.

**Check:** the memo names the {{ n }} suppliers and calls the match a lead.

## Expected results

| Supplier | Employee | Job title | Payments | Amount paid |
|---|---|---|---:|---:|
{% for m in matches %}
| {{ m.id }} {{ m.name }} | {{ m.emp }} {{ m.emp_name }} | {{ m.title }} | {{ m.payments|count }} | ${{ m.paid|money }} |
{% endfor %}
| All {{ g.n_match|count }} suppliers | | | {{ g.n_pay|count }} | ${{ g.paid|money }} |
| Matches as recorded, without TRIM and UPPER; on the address alone | {{ g.raw|count }}; {{ g.by_address|count }} | | | |

{{ figure('IF-05-5-A') }}

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The key joins two fields because one is not unique, and standardizes because the match should not depend on how an address was typed. A strong answer says that the standardizing changed nothing here.
- **Requirement (4).** Totals by SupplierID and the dates they cover. A plus: a count of payments beside each total, and a fiscal-year total labeled apart from the whole extract.
- **Requirement (5).** The {{ n }} suppliers, the employees and the payments; "a lead, not proof"; the roles; the next procedures in order of strength of evidence (ownership first).

A weak answer calls the matches fraud, or lists them without next procedures.

## Common mistakes and how to respond

- **A key on one Table.** *Symptom:* an error, or zero matches for every supplier. *Response:* open both MatchKey formulas and compare them.
- **#N/A in the lookup.** *Response:* test the count first.
- **A match on the address only.** *Symptom:* the same {{ g.by_address|count }} suppliers, so no visible error. *Response:* ask what the key would do if two towns had a street of the same name.
- **Totals by name.** *Symptom:* none in this data, because the names are unique. *Response:* ask what would happen with two suppliers of the same name, and use SupplierID.
- **A named fraud.** *Response:* ask what a shared address could also mean.
- **Plain Close & Load.** *Response:* **Load To** from **Queries & Connections**.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: loading | 15 | Three Tables as worksheets, Employee reduced to five columns | Loaded to the Data Model |
| Requirement 2: the key | 20 | The same formula on both Tables, with a reason for the city | A key without TRIM and UPPER, or no reason |
| Requirement 3: the matches | 20 | The count, the lookups with no #N/A, the six suppliers | Lookups that return errors |
| Requirement 4: payments | 15 | SUMIFS on SupplierID for each match, with the range of payment dates stated | Totals from a filter, or no date range |
| Requirement 5: the memo | 30 | Matches, payments, a lead not proof, next procedures | A list without procedures |

## Extensions and discussion questions

- Load PurchaseOrder and add each matched supplier's order count and total next to the payments, then compare the two.
- Add a fuzzy match with Power Query's Merge Queries and discuss what it would find that this key cannot.
- Discuss: Exercise 5.6 lists the suppliers a risk rating flags. Compare that list with the six matched here.
- Discuss: Chapter 8 tests purchasing further. Which of these six would you sample first, and why?
