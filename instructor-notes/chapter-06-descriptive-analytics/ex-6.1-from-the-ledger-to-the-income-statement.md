# Exercise 6.1: From the Ledger to the Income Statement

| | |
|---|---|
| Unit | Chapter 6: Descriptive and Diagnostic Analytics in Excel |
| Item | Exercise 6.1 |
| Perspective | Financial accounting |
| Tools | Excel |
| Time | About 120 minutes |
| Solution file | Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheets TrialBalance, IncomeStatement, JournalEntries and Ex 6.1 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This exercise starts from the other record of revenue, the general ledger, and asks students to build the statements the controller reads and reconcile them to the invoice lines. It practices Group By, calculated columns, SUMIFS by account subtype, two independent checks and a judgment about which date decides a period. The analytics type is descriptive.

By the end, students can:

- build a pre-closing trial balance from GLEntry, with a date filter, the closing entries left out and Group By, and show that its debit and credit balances agree (outcome 6);
- turn it into a common-size income statement with SUMIFS by AccountSubType, and tie net income to the closing entry and the balance sheet to equity (outcomes 6 and 2);
- reconcile the ledger's product revenue to InvoiceLines, identify the invoices behind the differences and say which date should decide their period (outcome 5).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Reporting and Control: Financial Statement Preparation; IFAC IES 2 (a) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 6.3, with InvoiceLines and the SalesInvoice Table of Tutorial 5.1. Requirement 5 reads shipment dates from the ShipmentLine and Shipment worksheets of CharlesRiver_Work.xlsx. The model answer uses FILTER, CHOOSECOLS and HSTACK (Microsoft 365 or Excel 2024).
- **Data conditions.** T3_GLEntry holds 815,921 rows. 526 of them are dated after 2026-12-31, all supplier payments, and 45 belong to the two closing entries JE-2026-000296 and JE-2026-000297. The earlier closes (JE-2024-000265 and JE-2024-000266; JE-2025-000287 and JE-2025-000288) zeroed the revenue and expense accounts of the earlier years, so those accounts show only fiscal 2026. The chart of accounts has 104 accounts and 71 have postings.
- **Column letters.** The loaded TrialBalance Table runs from AccountID in column A through AccountSubType in G, with the three calculated columns in H, I and J.

## How to run it

Individual, or pairs for the reconciliation, about 120 minutes: 35 on the query (requirement 1), 15 on the columns and Total Row (2), 20 on the statement (3), 15 on the checks (4), 20 on the reconciliation (5) and 15 on the memo (6). Before students follow the shipment path that requirement 5 prints, ask them to name the two dates that could decide the period. Collect the workbook and memo.

## Step-by-step solution

### Requirement (1): Build the trial balance query

**Step 1. Import the two Tables.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx, and in the **Navigator** check **Select multiple items** and select **T3_GLEntry** and **T1_Account**.
b. Click **Transform Data**, not **Load**, and rename the queries `TrialBalance` and `ChartOfAccounts`.

**Step 2. Filter before you group.** In TrialBalance, check that PostingDate has the Date type, and filter it to dates before `2027-01-01` with the column's date filters. Then filter VoucherNumber with the text filter that excludes a value, once for JE-2026-000296 and once for JE-2026-000297, as two filters or one filter joined by **And**. Joined by **Or**, it keeps every row.

**Step 3. Group by account.** Choose **Transform > Group By** and **Advanced**, group by AccountID, and add two aggregations: `Debit`, the sum of Debit, and `Credit`, the sum of Credit.

**Check:** 71 rows, one for each account with postings. **Watch for:** a missing date filter. The extract still balances, because the later supplier payments debit payables and credit cash, so equal totals cannot reveal it. Cash would read $8,170,928.63 instead of $8,442,255.80.

**Step 4. Merge the chart of accounts.**

a. In ChartOfAccounts, use **Home > Choose Columns** to keep AccountID, AccountNumber, AccountName, AccountType and AccountSubType.
b. In TrialBalance choose **Home > Merge Queries**, match AccountID with AccountID and expand the four other columns, clearing **Use original column name as prefix**.
c. Sort by AccountNumber.

![A mock of the Power Query Editor with the applied steps of the TrialBalance query after Step 4.](../figures/chapter-06-descriptive-analytics/IF-06-1-A.pdf)

**Step 5. Load the result.**

a. Choose **Home > Close & Load > Close & Load To**, select **Only Create Connection** and click **OK**. The choice applies to both queries.
b. Open **Data > Queries & Connections**, right-click **TrialBalance**, choose **Load To**, and load it as a **Table** on a **New worksheet** named `TrialBalance`.

Check on **Table Design** that the Table is named `TrialBalance`, as the formulas expect.

**Check:** the Table has 71 rows. **Watch for:** a plain **Close & Load**, which with Excel's default load settings sends both queries to the Data Model.

### Requirement (2): Balances and the Total Row

**Step 6. Add the three columns.** In the first empty cell right of AccountSubType, type each header and its formula, so that the Table fills the column:

```
Balance        =[@Debit]-[@Credit]
DebitBalance   =MAX(0,[@Balance])
CreditBalance  =MAX(0,-[@Balance])
```

**Step 7. Turn on the Total Row.** Choose **Table Design > Total Row** and set the sum for DebitBalance and CreditBalance.

**Check:** both totals read $67,107,722.36 and 4 accounts (2031, 2032, 2033, and 8010) have a zero balance. **Watch for:** comparing the two totals with `=`. Summing so many rows leaves differences far below a cent, so a check cell needs `ROUND(...,2)`.

For the written part, the query includes every year, but the earlier closes (JE-2024-000265 and JE-2024-000266; JE-2025-000287 and JE-2025-000288) zeroed the revenue and expense accounts, so only fiscal 2026 remains in them.

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

**Check:** the Expected results table. **Watch for:** other income and expense typed as one subtype. Account 7020 is typed Revenue with the subtype Other Income or Expense, and account 7030 is Other Expense, so the line needs both.

### Requirement (4): Two checks

**Step 9. Check net income against the closing entry.** Import **T2_JournalEntry** as a query named `JournalEntries` (or read the entry on the JournalEntry worksheet of CharlesRiver.xlsx). Look up the TotalAmount of JE-2026-000297 and subtract it from B10.

**Step 10. Check the balance sheet.** Enter this formula for the assets, the same with `"Liability"` and `"Equity"` for the other two with the sign reversed, add B10 to equity, and compute the difference with `ROUND`.

```
=SUMIFS(TrialBalance[Balance],TrialBalance[AccountType],"Asset")
```

**Check:** net income less the closing entry is zero, and assets ($39,328,524.11) equal liabilities ($13,896,428.43) plus equity ($20,928,484.44) plus net income.

### Requirement (5): Reconcile the revenue accounts

**Step 11. Compare the accounts with InvoiceLines.** On `Ex 6.1`, from row 5, list accounts 4010, 4020, 4030, 4040 and 4080 beside their item groups. For each, take the account's balance with the sign reversed and subtract the group's revenue for fiscal 2026.

```
=-SUMIFS(TrialBalance[Balance],TrialBalance[AccountNumber],$A5)
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$B5,InvoiceLines[FiscalYear],2026)
```

**Check:** differences of $3,233.18, $1,112.23, none for Textiles, $236.96 and none for Services.

**Step 12. Find the invoices and the dates.** Filter SalesInvoice to fiscal 2025 with an invoice number that starts `SI-2026`: 3 invoices, which Exercise 5.2 found. Sum their lines by item group and match each to a difference. For each, read ShipmentLineID on InvoiceLines and follow it through ShipmentLine to Shipment for the delivery date.

![A mock of the reconciliation of Requirement 5 on the worksheet Ex 6.1.](../figures/chapter-06-descriptive-analytics/IF-06-1-B.pdf)

**Check:** each difference equals one invoice, and the ledger posted all of them on 2026-01-01. The shipment records give SI-2026-013741, shipped 2026-01-01 and delivered 2026-01-04; SI-2026-013742, shipped 2025-12-06 and delivered 2025-12-10; SI-2026-013743, shipped 2026-01-01 and delivered 2026-01-05. SI-2026-013742 was delivered in fiscal 2025, so its $3,233.18 is a cutoff error. The other two were delivered in fiscal 2026, so only their dates are wrong. **Watch for:** the invoice number, or the shipment date, taken as the evidence. Delivery decides, because control passes then.

### Requirement (6): The memo

Outline: the statement and its basis, the two checks, the cost structure, then the reconciling items. The memo labels the statement and the reconciliation as recorded, before any correction of the errors found, and says the closing-entry check tests consistency, not recognition. Correcting the cutoff error would also reach the related receivable, sales tax and cost entries. Freight revenue is net of freight credits ($214,616.66 billed less $1,796.63), and the credit memos' subtotals post to sales returns, so the credits are not deducted twice. Net revenue is $29,731,057.92; cost of goods sold takes 62.68%, so gross margin is 37.32%; operating expenses take 21.77%, so operating income is 15.56% and net income 15.15%.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Accounts in the trial balance; with a zero balance | 71; 4 | 3, 7 |
| Debit and credit balances | $67,107,722.36 each | 7 |
| Operating revenue | $29,973,822.48 | 8 |
| Sales returns and allowances | -$242,764.56 | 8 |
| Net revenue | $29,731,057.92 | 8 |
| Cost of goods sold | -$18,634,303.63 | 8 |
| Gross margin | $11,096,754.29 | 8 |
| Operating expenses | -$6,471,696.58 | 8 |
| Operating income | $4,625,057.71 | 8 |
| Other income and expense | -$121,446.47 | 8 |
| Net income, equal to JE-2026-000297 | $4,503,611.24 | 9 |
| Assets | $39,328,524.11 | 10 |
| Account 4010 less Furniture revenue | $3,233.18 | 11 |
| Account 4020 less Lighting revenue | $1,112.23 | 11 |
| Account 4030 less Textiles revenue | $0.00 | 11 |
| Account 4040 less Accessories revenue | $236.96 | 11 |
| Account 4080 less Services revenue | $0.00 | 11 |
| Freight revenue (account 4050, net of freight credits, no invoice line) | $212,820.03 | 12 |

> **Instructor notes, Exercise 6.1:** the pre-closing trial balance at 2026-12-31 (GLEntry with PostingDate before 2027-01-01, without the 45 GL rows of the closes JE-2026-000296 and JE-2026-000297) has 71 accounts, 4 of them with a zero balance; debit and credit balances are both 67,107,722.36. Revenue and expense accounts show only fiscal 2026 because the 2024 and 2025 closing entries zeroed them. Income statement: operating revenue 29,973,822.48 (100.82% of net revenue); sales returns and allowances -242,764.56 (4060); net revenue 29,731,057.92; cost of goods sold -18,634,303.63 (62.68%; includes freight-out 5050, purchase price variance 5060, and manufacturing variance 5080); gross margin 11,096,754.29 (37.32%); operating expenses -6,471,696.58 (21.77%); operating income 4,625,057.71 (15.56%); other income and expense -121,446.47 (loss on asset disposal 7020 of 92,500.00, an account typed Revenue with subtype Other Income or Expense, and interest expense 7030 of 28,946.47); net income 4,503,611.24 (15.15%), equal to JE-2026-000297. Balance sheet: assets 39,328,524.11 = liabilities 13,896,428.43 + equity 20,928,484.44 + net income 4,503,611.24. The balances include the unsupported opening balances found in Chapter 8. Revenue reconciliation, account balance vs InvoiceLines 2026: 4010 17,398,287.56 vs Furniture 17,395,054.38 (+3,233.18); 4020 5,998,649.16 vs Lighting 5,997,536.93 (+1,112.23); 4030 3,278,211.11 vs Textiles, equal; 4040 1,872,510.62 vs Accessories 1,872,273.66 (+236.96); 4080 1,213,344.00 vs Services, equal. The differences are SI-2026-013742 (Furniture, dated 2025-12-04), SI-2026-013741 (Lighting, 2025-11-29), and SI-2026-013743 (Accessories, 2025-12-03), dated in 2025 with the next year's number and posted 2026-01-01. InvoiceLines assigns them to fiscal 2025 by their invoice dates, the ledger to fiscal 2026. On the basis the book uses, control of the goods passes on delivery, so the delivery date, not the invoice date or number, determines the period (every shipment is delivered in the year it ships); students who name transfer of control, with delivery as its evidence, have the right idea. Only SI-2026-013742 shipped in 2025 (on 2025-12-06), so its 3,233.18 is a revenue cutoff error; the other two shipped on 2026-01-01, so on that basis the ledger's period is right and their invoice dates are wrong. Tutorial 12.1 tests cutoff by delivery date for every invoice. Freight revenue (4050, 212,820.03) has no invoice line.

## What a strong answer says

- **Requirement (2).** The earlier closes zeroed the revenue and expense accounts, the balance sheet accounts carry forward, and the 2026 closes are left out so the statement can be prepared.
- **Requirement (5).** Three invoices numbered for fiscal 2026, dated in fiscal 2025, posted in 2026. Delivery decides the period, and the shipment records show one cutoff error and two wrong dates. Freight revenue, net of freight credits, has no invoice line.
- **Requirement (6).** Every ratio ties to the statement, which is labeled as recorded, before correction of the cutoff error, and cost of goods sold includes freight-out and the two variances, which is why the gross margin is below the margin at standard cost.

A weak memo lists the statement without reading it, or calls the cutoff differences "errors" without saying which ones.

## Common mistakes and how to respond

- **The two closes left in.** *Symptom:* revenue and expense accounts at zero and net income of zero. *Response:* ask what the closing entry did to those accounts.
- **No date filter.** *Symptom:* balances still agree, but cash and payables are off. *Response:* ask which rows exist after the year-end and which check would have caught them.
- **Revenue with the wrong sign.** *Symptom:* negative revenue. *Response:* ask what a credit balance means.
- **One subtype for other items.** *Symptom:* other income and expense of $92,500.00 or $28,946.47 only. *Response:* list the accounts in each subtype.
- **Trusting the invoice number or date.** *Symptom:* all three invoices called errors, or none. *Response:* ask what evidence shows when the goods were delivered.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the query | 25 | Filters before the Group By, merge without prefix, loaded as a Table | Closes or date filter missing, or loaded to the Data Model |
| Requirement 2: columns and Total Row | 15 | Three columns, equal totals, written explanation | Totals without the explanation |
| Requirement 3: the statement | 20 | SUMIFS by subtype, signs, both other-item subtypes, percentages | Typed values, or one subtype missing |
| Requirement 4: the checks | 15 | Both checks made and their results stated | One check |
| Requirement 5: reconciliation | 15 | Three invoices, delivery date, one cutoff error | Invoices found without the period argument |
| Requirement 6: the memo | 10 | Cost structure, checks and reconciling items, labeled as recorded | Descriptive only |

## Extensions and discussion questions

- Find the closing entries by EntryType and posting date instead of typing their numbers.
- Discuss: the ledger balances with and without the later supplier payments. What would a completeness test look like?
