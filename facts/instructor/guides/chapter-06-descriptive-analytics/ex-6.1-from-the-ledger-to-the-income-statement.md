---
note: ch06.ex1
uses: [ch06.g1]
title: From the Ledger to the Income Statement
kind: exercise
number: '6.1'
unit: '6'
perspective: financial
tool: excel
minutes: 120
solution: "Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheets TrialBalance, IncomeStatement, JournalEntries and Ex 6.1"
figures:
  - id: IF-06-1-A
    kind: excel-mock
    purpose: The Power Query Editor with the applied steps of the TrialBalance query after Step 4.
    shows: "The Power Query Editor with TrialBalance selected. Applied Steps: Source, Navigation, Filtered Rows, Filtered Rows1, Grouped Rows, Merged Queries, Expanded ChartOfAccounts, Sorted Rows. The preview grid shows the first accounts with their debit, credit, number, name, type and subtype."
    data: The first rows of the trial balance and the applied steps (the Expected results of this exercise).
  - id: IF-06-1-B
    kind: excel-mock
    purpose: The reconciliation of Requirement 5 on the worksheet Ex 6.1.
    shows: "A grid with columns Account, Item group, Account balance, InvoiceLines of the report year, Difference, Explained and Unexplained, five rows for the product revenue accounts and a Total row; the three rows with a difference are outlined. Below it, the three invoices numbered in the report year but dated in the year before, with number, date, item group and line total."
    data: The reconciliation and invoice rows of the Expected results.
---
{% set g = ch06_g1 %}
# Exercise 6.1: From the Ledger to the Income Statement

{{ header() }}

## Purpose and learning outcomes

This exercise starts from the other record of revenue, the general ledger, and asks students to build the statements the controller reads and reconcile them to the invoice lines. It practices Group By, calculated columns, SUMIFS by account subtype, two independent checks and a judgment about which date decides a period. The analytics type is descriptive.

By the end, students can:

- build a pre-closing trial balance from GLEntry, with a date filter, the closing entries left out and Group By, and show that its debit and credit balances agree (chapter outcome 6);
- turn it into a common-size income statement with SUMIFS by AccountSubType, and tie net income to the closing entry and the balance sheet to equity (outcomes 6 and 2);
- reconcile the ledger's product revenue to InvoiceLines, identify the invoices behind the differences and say which date should decide their period (outcome 5).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Reporting and Control: Financial Statement Preparation; IFAC IES 2 (a) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 6.3, with InvoiceLines and the SalesInvoice Table of Tutorial 5.1. Requirement 5 reads shipment dates from the ShipmentLine and Shipment worksheets of CharlesRiver_Work.xlsx. The model answer uses FILTER, CHOOSECOLS and HSTACK (Microsoft 365 or Excel 2024). Run the Group By yourself first: the ledger is large.
- **Data conditions.** T3_GLEntry holds {{ g.rows_all|count }} rows. {{ g.rows_next|count }} of them are dated after {{ asof }}, all supplier payments, and {{ g.rows_close|count }} belong to the two closing entries {{ g.c1 }} and {{ g.c2 }}. The earlier closes ({{ g.earlier_close_f }}; {{ g.earlier_close_p }}) zeroed the revenue and expense accounts of the earlier years, so those accounts show only fiscal {{ d.C }}. The chart of accounts has {{ g.n_accounts_all|count }} accounts and {{ accounts }} have postings.
- **Column letters.** The loaded TrialBalance Table runs from AccountID in column {{ g.letters.AccountID }} through AccountSubType in {{ g.letters.AccountSubType }}, with the three calculated columns in {{ g.letters.Balance }}, {{ g.letters.DebitBalance }} and {{ g.letters.CreditBalance }}.

## How to run it

Individual, or pairs for the reconciliation, about 120 minutes: 35 on the query (requirement 1), 15 on the columns and Total Row (2), 20 on the statement (3), 15 on the checks (4), 20 on the reconciliation (5) and 15 on the memo (6). Hold back the shipment path of requirement 5 until students have named the two dates that could decide the period. Collect the workbook and memo.

## Step-by-step solution

### Requirement (1): Build the trial balance query

**Step 1. Import the two Tables.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx, and in the **Navigator** select **T3_GLEntry** and **T1_Account**.
b. Click **Transform Data**, not **Load**, and rename the queries `TrialBalance` and `ChartOfAccounts`.

**Step 2. Filter before you group.** In TrialBalance, filter PostingDate to dates before `2027-01-01` with the column's date filters. Then filter VoucherNumber with the text filter that excludes a value, once for {{ g.c1 }} and once for {{ g.c2 }}.

**Step 3. Group by account.** Choose **Transform > Group By** and **Advanced**, group by AccountID, and add two aggregations: `Debit`, the sum of Debit, and `Credit`, the sum of Credit.

**Check:** {{ accounts }} rows, one for each account with postings. **Watch for:** a missing date filter. The extract still balances, because the later supplier payments debit payables and credit cash, so equal totals cannot reveal it. Cash would read ${{ g.cash_all|money }} instead of ${{ g.cash|money }}.

**Step 4. Merge the chart of accounts.**

a. In ChartOfAccounts, use **Home > Choose Columns** to keep AccountID, AccountNumber, AccountName, AccountType and AccountSubType.
b. In TrialBalance choose **Home > Merge Queries**, match AccountID with AccountID and expand the four other columns, clearing **Use original column name as prefix**.
c. Sort by AccountNumber.

{{ figure('IF-06-1-A') }}

**Step 5. Load the result.**

a. Choose **Home > Close & Load > Close & Load To**, select **Only Create Connection** and click **OK**. The choice applies to both queries.
b. Open **Data > Queries & Connections**, right-click **TrialBalance**, choose **Load To**, and load it as a **Table** on a **New worksheet** named `TrialBalance`.

**Check:** the Table has {{ accounts }} rows. **Watch for:** a plain **Close & Load**, which sends both queries to the Data Model.

### Requirement (2): Balances and the Total Row

**Step 6. Add the three columns.** In the first empty cell right of AccountSubType, type each header and its formula, so that the Table fills the column:

```
Balance        =[@Debit]-[@Credit]
DebitBalance   =MAX(0,[@Balance])
CreditBalance  =MAX(0,-[@Balance])
```

**Step 7. Turn on the Total Row.** Choose **Table Design > Total Row** and set the sum for DebitBalance and CreditBalance.

**Check:** both totals read ${{ debits|money }} and {{ zero }} accounts ({{ g.zero_accounts }}) have a zero balance. **Watch for:** comparing the two totals with `=`. Summing so many rows leaves differences far below a cent, so a check cell needs `ROUND(...,2)`.

For the written part, the query includes every year, but the earlier closes ({{ g.earlier_close_f }}; {{ g.earlier_close_p }}) zeroed the revenue and expense accounts, so only fiscal {{ d.C }} remains in them.

### Requirement (3): The income statement

**Step 8. Build the statement.** On `IncomeStatement`, label A2 to A10 with the lines of Figure 6.7 and enter the formulas below in B2 to B10, then `=B2/$B$4` in C2, filled down.

```
B2   =-SUMIFS(TrialBalance[Balance],TrialBalance[AccountSubType],"Operating Revenue")
B3   =-SUMIFS(TrialBalance[Balance],TrialBalance[AccountSubType],"Contra Revenue")
B4   =B2+B3
B5   =-SUMIFS(TrialBalance[Balance],TrialBalance[AccountSubType],"COGS")
B6   =B4+B5
B7   =-SUMIFS(TrialBalance[Balance],TrialBalance[AccountSubType],"Operating Expense")
B8   =B6+B7
B9   =-SUMIFS(TrialBalance[Balance],TrialBalance[AccountSubType],"Other Income or Expense")-SUMIFS(TrialBalance[Balance],TrialBalance[AccountSubType],"Other Expense")
B10  =B8+B9
```

**Check:** the Expected results table. **Watch for:** other income and expense typed as one subtype. Account {{ g.acct.loss }} is typed Revenue with the subtype Other Income or Expense, and account {{ g.acct.interest }} is Other Expense, so the line needs both.

### Requirement (4): Two checks

**Step 9. Check net income against the closing entry.** Import **T2_JournalEntry** as a query named `JournalEntries` (or read the entry on the JournalEntry worksheet of CharlesRiver.xlsx). Look up the TotalAmount of {{ g.c2 }} and subtract it from B10.

**Step 10. Check the balance sheet.** Enter `=SUMIFS(TrialBalance[Balance],TrialBalance[AccountType],"Asset")` for the assets, the same with `"Liability"` and `"Equity"` for the other two with the sign reversed, add B10 to equity, and compute the difference with `ROUND`.

**Check:** net income less the closing entry is zero, and assets (${{ assets|money }}) equal liabilities (${{ liabilities|money }}) plus equity (${{ equity|money }}) plus net income.

### Requirement (5): Reconcile the revenue accounts

**Step 11. Compare the accounts with InvoiceLines.** On `Ex 6.1`, from row 5, list accounts {{ recon[0].account }}, {{ recon[1].account }}, {{ recon[2].account }}, {{ recon[3].account }} and {{ recon[4].account }} beside their item groups. For each, take the account's balance with the sign reversed and subtract the group's revenue for fiscal {{ d.C }}.

```jinja
=-SUMIFS(TrialBalance[Balance],TrialBalance[AccountNumber],$A5)
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$B5,InvoiceLines[FiscalYear],{{ d.C }})
```

**Check:** differences of ${{ recon[0].diff|money }}, ${{ recon[1].diff|money }}, none for Textiles, ${{ recon[3].diff|money }} and none for Services.

**Step 12. Find the invoices and the dates.** Filter SalesInvoice to fiscal {{ d.P }} with an invoice number that starts `SI-{{ d.C }}`: {{ invoices|length }} invoices, which Exercise 5.2 found. Sum their lines by item group and match each to a difference. For each, read ShipmentLineID on InvoiceLines and follow it through ShipmentLine to Shipment for the delivery date.

{{ figure('IF-06-1-B') }}

**Check:** each difference equals one invoice, and the ledger posted all of them on {{ posted }}. {{ early.number }} shipped on {{ early.shipped }}, in fiscal {{ d.P }}, so its ${{ early.amount|money }} is a cutoff error. The other {{ others }} shipped {{ others_shipped }}, so only their dates are wrong. **Watch for:** the invoice number taken as evidence. Delivery decides, because control passes then.

### Requirement (6): The memo

Outline: the statement and its basis, the two checks, the cost structure, then the reconciling items. Net revenue is ${{ net_rev|money }}; cost of goods sold takes {{ (-cogs / net_rev)|pct(2) }}, so gross margin is {{ (gm / net_rev)|pct(2) }}; operating expenses take {{ (-opex / net_rev)|pct(2) }}, so operating income is {{ (oi / net_rev)|pct(2) }} and net income {{ (ni / net_rev)|pct(2) }}.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Accounts in the trial balance; with a zero balance | {{ accounts }}; {{ zero }} | 3, 7 |
| Debit and credit balances | ${{ debits|money }} each | 7 |
| Operating revenue | ${{ opr|money }} | 8 |
| Sales returns and allowances | -${{ (contra|abs)|money }} | 8 |
| Net revenue | ${{ net_rev|money }} | 8 |
| Cost of goods sold | -${{ (cogs|abs)|money }} | 8 |
| Gross margin | ${{ gm|money }} | 8 |
| Operating expenses | -${{ (opex|abs)|money }} | 8 |
| Operating income | ${{ oi|money }} | 8 |
| Other income and expense | -${{ (other|abs)|money }} | 8 |
| Net income, equal to {{ g.c2 }} | ${{ ni|money }} | 9 |
| Assets | ${{ assets|money }} | 10 |
{% for r in recon %}
| Account {{ r.account }} less {{ r.group }} revenue | ${{ r.diff|money }} | 11 |
{% endfor %}
| Freight revenue (account {{ g.acct.freight }}, no invoice line) | ${{ freight|money }} | 12 |

{{ expected() }}

## What a strong answer says

- **Requirement (2).** The earlier closes zeroed the revenue and expense accounts, the balance sheet accounts carry forward, and the {{ d.C }} closes are left out so the statement can be prepared.
- **Requirement (5).** Three invoices numbered for fiscal {{ d.C }}, dated in fiscal {{ d.P }}, posted in {{ d.C }}. Delivery decides the period, and the shipment records show one cutoff error and two wrong dates. Freight revenue has no invoice line.
- **Requirement (6).** Every ratio ties to the statement, the checks are called tests of arithmetic and not of completeness, and cost of goods sold includes freight-out and the two variances, which is why the gross margin is below the margin at standard cost.

A weak memo lists the statement without reading it, or calls the cutoff differences "errors" without saying which ones.

## Common mistakes and how to respond

- **The two closes left in.** *Symptom:* revenue and expense accounts at zero and net income of zero. *Response:* ask what the closing entry did to those accounts.
- **No date filter.** *Symptom:* balances still agree, but cash and payables are off. *Response:* ask which rows exist after the year-end and which check would have caught them.
- **Revenue with the wrong sign.** *Symptom:* negative revenue. *Response:* ask what a credit balance means.
- **One subtype for other items.** *Symptom:* other income and expense of ${{ loss|money }} or ${{ interest|money }} only. *Response:* list the accounts in each subtype.
- **Trusting the invoice number or date.** *Symptom:* all three invoices called errors, or none. *Response:* ask what evidence shows when the goods were delivered.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the query | 25 | Filters before the Group By, merge without prefix, loaded as a Table | Closes or date filter missing, or loaded to the Data Model |
| Requirement 2: columns and Total Row | 15 | Three columns, equal totals, written explanation | Totals without the explanation |
| Requirement 3: the statement | 20 | SUMIFS by subtype, signs, both other-item subtypes, percentages | Typed values, or one subtype missing |
| Requirement 4: the checks | 15 | Both checks, rounded, stated as arithmetic only | One check |
| Requirement 5: reconciliation | 15 | Three invoices, delivery date, one cutoff error | Invoices found without the period argument |
| Requirement 6: the memo | 10 | Cost structure, checks and reconciling items | Descriptive only |

## Extensions and discussion questions

- Find the closing entries by EntryType and posting date instead of typing their numbers.
- Discuss: the ledger balances with and without the later supplier payments. What would a completeness test look like?
- Discuss: Tutorial 12.1 tests the cutoff for every invoice. What would you ask the shipping department?
