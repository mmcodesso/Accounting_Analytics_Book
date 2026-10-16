# Requirement 1: Build and validate the case workbook (Chapters 4 and 5)

| | |
|---|---|
| Unit | Case Part 2: Deciding on the 2027 Promotion Calendar |
| Item | Requirement 1 |
| Tools | Excel |
| Time | About 90 minutes |
| Solution file | PartII-case.zip: Charles River Promotion Case.xlsx, sheets Documentation, Parameters, SourceCounts and the query sheets (Promotions, Orders, Items, Customers, OrderLines, BilledLines, Accounts, RevenuePostings, LedgerActivity, BudgetPrices, Overrides, Employees) |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 1 builds the workbook that every later requirement reads, and it is graded as much on what it checks as on what it builds. Students have imported Tables with Power Query since Chapter 4, but here they choose the queries, document them and show with control totals that no merge lost or doubled a row. A mistyped Discount column or an inner join would flow silently into Requirements 2 to 5, so this requirement is the quality gate of the case. The analytics type is descriptive: it prepares the data and states its limits.

By the end, students can:

- build named queries from several Tables with merges, calculated columns and a filtered import of the large ledger Table;
- keep the inputs of an analysis in named, colored cells;
- compare each query with its source and say what each filter keeps;
- record sources, steps, checks and open questions on a Documentation sheet.

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (extraction, transformation and cleansing of financial data); IMA Data Analytics and Insights (data tools and techniques); IFAC IES 2 (i), using information and communications technology to analyze data; AACSB A5 part 5.1 (technology integration).

## Before you assign

- **Files and software.** CharlesRiver.xlsx in a folder every student can reach and Excel for Microsoft 365 with Power Query. There is no start file: the case builds a new workbook next to CharlesRiver.xlsx, so the workbooks of Chapters 4 to 8 stay as they were. Students need the commission rate from Tutorial 7.3 (their value, or 1.903%).
- **The type trap.** None of the first 200 rows of SalesOrderLine or SalesInvoiceLine carries a discount or a promotion: the first promotion lines are SalesOrderLineID 1249 and SalesInvoiceLineID 1548. Power Query types Discount from those rows as a whole number and leaves PromotionID untyped (Any), so the rates would round to 0. Tutorial 4.1 Step 6 taught the fix, **Replace current** in the Changed Type step.
- **The ledger Table.** T3_GLEntry has 815,921 rows, so it is imported with **Transform Data** and filtered before anything loads.
- **Verify first.** Build the queries once, or refresh the solution workbook: its queries read C:\CharlesRiver\CharlesRiver.xlsx, and **Data > Get Data > Data Source Settings > Change Source** points them at your copy.

## How to run it

Individual work, about 90 minutes: 10 on the Documentation and Parameters sheets, 45 on the queries, 25 on the checks and 10 on documenting the result. In a lab, give the case's Watch out (the three duplicate column names) at the start, because it costs the most time. Hold back the row-count hint until a count is far too small, the symptom of an inner join. **Collect** the workbook; the checks live on its Documentation sheet.

![A mock of the completeness checks of the Documentation sheet, as a student's workbook shows them after a refresh.](../figures/case-part-2/IF-C2-1-A.pdf)

## Step-by-step solution

### Phase 1: Documentation and Parameters

**Step 1. Start the Documentation sheet.** Create `Charles River Promotion Case.xlsx` next to CharlesRiver.xlsx. Add a worksheet named `Documentation` as in Tutorial 4.3 and drag it to the far left. Column A holds the labels Purpose, Source, Query steps, Last refreshed, Parameters, Calculated columns, Worksheets, Conventions, Prepared by, Reviewed by and Open questions, and column B the entries. Leave the entries until the end, and put the checks of Steps 7 and 8 below them.

**Check:** the sheet opens first and has the eleven labels. The model answer adds a Recommendation row once the memo is written.

**Step 2. Add the Parameters sheet.**

a. Add a worksheet named `Parameters` with the columns Parameter, Value, Name and Description.
b. Type `0.08`, `0.1` and `0.12` as the proposal's rates, format them as percentages and color them blue.
c. Name the three cells `HarborRate`, `FurnitureRate` and `DesignTradeRate` with the Name Box.
d. Add `CommissionRate`. Typing Tutorial 7.3's value is enough. The model answer recomputes it so a refresh keeps it current: the report year's commission expense (a `LedgerActivity` query of the ledger grouped by account, year and source, with `ReportYear` a named input cell) divided by the year's invoice-line revenue.

```
=SUMIFS(LedgerActivity[Debit],LedgerActivity[AccountNumber],6290,LedgerActivity[FiscalYear],ReportYear,LedgerActivity[SourceDocumentType],"<>JournalEntry")-SUMIFS(LedgerActivity[Credit],LedgerActivity[AccountNumber],6290,LedgerActivity[FiscalYear],ReportYear,LedgerActivity[SourceDocumentType],"<>JournalEntry")
=SUMIFS(BilledLines[LineTotal],BilledLines[InvoiceYear],ReportYear)
```

**Check:** CommissionRate reads 1.903%: commission expense of $566,347.93 over invoice-line revenue of $29,756,420.08, leaving out the year-end close JE-2026-000296. The formula leaves out every journal entry to the account, and in the report year the close is the only one, which the note checks. A year with an adjusting entry to commissions would need the close left out by its voucher number instead. **Watch for:** the close left in. It brings the account to zero for the year, and the rate collapses.

### Phase 2: The queries

**Step 3. Import the lookup Tables.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx, select the Table in the Navigator and choose **Transform Data**. Repeat for T7_PromotionProgram (`Promotions`), T9_SalesOrder (`Orders`), T16_SalesInvoice (`Invoices`), T44_Item (`Items`), T4_Customer (`Customers`), T1_Account (`Accounts`) and T74_Employee (`Employees`).
b. In `Promotions` rename ItemGroup, CollectionName and CustomerSegment to `PromoItemGroup`, `PromoCollection` and `PromoSegment`.
c. In every query check the Changed Type step: date columns as Date, and FreightAmount in `Invoices` as **Decimal Number** with **Replace current**.

**Step 4. Build OrderLines.**

a. Import T10_SalesOrderLine as `OrderLines`. In its Changed Type step set Discount to **Decimal Number** and PromotionID to **Whole Number**, each with **Replace current**.
b. Choose **Home > Merge Queries**, merge with `Orders` on SalesOrderID, and expand OrderDate and CustomerID with "Use original column name as prefix" cleared.
c. Merge `Items` on ItemID and expand ItemCode, ItemName, ItemGroup, CollectionName and StandardCost; merge `Customers` on CustomerID and expand CustomerSegment; merge `Promotions` on PromotionID and expand ScopeType, the three Promo columns, DiscountPct, EffectiveStartDate and EffectiveEndDate.
d. Choose **Add Column > Custom Column** five times: `OrderYear` as `Date.Year([OrderDate])`, `OrderMonth` as `Date.Month([OrderDate])`, `ListAmount` as `[Quantity] * [BaseListPrice]`, `GrossAmount` as `[Quantity] * [UnitPrice]` and `DiscountAmount` as `[GrossAmount] * [Discount]`.

**Check:** 22,269 rows, one for each source row. **Watch for:** an inner join, which keeps only the 1,650 promotion lines; and the Discount type, which leaves the DiscountAmount total at zero.

**Step 5. Build BilledLines.** Import T17_SalesInvoiceLine with the same two type corrections. Merge `Invoices` and expand InvoiceNumber and InvoiceDate, merge `Items` and expand ItemGroup and StandardCost, and add `InvoiceYear` as `Date.Year([InvoiceDate])`, `InvoiceQuarter` as `Date.QuarterOfYear([InvoiceDate])` and the same three amounts.

**Check:** 27,933 rows and a LineTotal of $86,446,845.84.

**Step 6. Build the ledger, budget and override queries, then load.**

a. Import T3_GLEntry with **Transform Data**. Filter SourceDocumentType to SalesInvoice and PostingDate to the report year, merge `Accounts` for AccountNumber, choose **Transform > Group By**, select **Advanced**, and group by AccountNumber with the sum of Credit and the sum of Debit. Name it `RevenuePostings`.
b. Import T77_BudgetLine, filter BudgetCategory to Revenue, merge `Items` (ItemCode, ItemGroup, CollectionName, ListPrice) and add `ListAmount` as `[Quantity] * [ListPrice]`. Name it `BudgetPrices`.
c. Import T8_PriceOverrideApproval as `Overrides` and merge `Employees` twice, once on RequestedByEmployeeID and once on ApprovedByEmployeeID, renaming the expanded columns for the requester and the approver.
d. Choose **Home > Close & Load > Close & Load To**. A query that only feeds others, here `Invoices`, is loaded with **Only Create Connection**; load the rest as Tables on new worksheets and rename each worksheet after its query. The dialog's choice applies to every query loaded at once, so load the connection-only queries separately.

**Check:** `RevenuePostings` has 8 rows, one for each account the report year's sales invoices post to: 1020, 2050, 4010, 4020, 4030, 4040, 4050, 4080. `BudgetPrices` has 9,616 of the 31,426 budget rows.

### Phase 3: The completeness checks

**Step 7. Compare each query with its source.** Build `SourceCounts` from the workbook's own list of Tables (the Name and Data columns the Navigator is built from), filtered to the Tables above, with a custom column `Rows` as `Table.RowCount([Data])`. Beside each loaded query on the Documentation sheet put:

```
=ROWS(OrderLines[SalesOrderLineID])
=XLOOKUP("T10_SalesOrderLine",SourceCounts[Name],SourceCounts[Rows])
```

and a final column that tests whether the two agree. For `BudgetPrices` compare with the source's Revenue rows, which `SourceCounts` also counts, and for `RevenuePostings` state what the filter keeps instead.

**Check:** Promotions 9; Orders 5,819; Items 266; Customers 220; OrderLines 22,269; BilledLines 27,933; Accounts 104; Overrides 412; Employees 120. A student who selects a key column of each source Table and reads the Count in the status bar gets the same answers, but loses the refresh.

**Step 8. Tie the totals.** Record these checks:

```
=SUM(OrderLines[LineTotal])      against      =SUM(Orders[OrderTotal])
=COUNTIF(Orders[LinesAgree],FALSE)
=COUNTIFS(OrderLines[PromotionID],"",OrderLines[Discount],"<>0")
=COUNTIFS(BilledLines[PromotionID],"",BilledLines[Discount],"<>0")
=SUM(RevenuePostings[Debit])      against      =SUM(RevenuePostings[Credit])
```

`LinesAgree` is a calculated column in `Orders`: `=ABS([@OrderTotal]-[@LinesTotal])<0.005`, with `LinesTotal` a SUMIFS of the order's lines.

**Check:** the order lines total $87,500,091.56 and equal the orders' total, with no order disagreeing with its lines. No line without a promotion carries a discount, in 22,269 order lines or 27,933 billed lines. The distinct Discount values in `OrderLines` are 0, 0.08, 0.1, 0.12. The postings' debits and credits are both $31,924,034.93. **Watch for:** the no-discount checks run before the type correction. They pass trivially, because every rate has already become 0; the list of distinct rates is the check that catches the type trap. The 20,619 lines with no promotion are the population those checks test.

**Step 9. Finish the Documentation sheet.** Fill each entry: the Tables and their query names, the type corrections and why, the renamed columns, the unrounded amounts, the filters of `RevenuePostings` and `BudgetPrices`, the checks and their result, and the Last refreshed date. Under Open questions list the three data issues students will meet later, in general terms: end dates that cannot be right, a CustomerSince that does not match the orders, and fractional quantities on items sold by the unit.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Rows in each of the nine source queries | as in Step 7 | 7 |
| `BudgetPrices` rows, Revenue only | 9,616 | 6 |
| `RevenuePostings` rows | 8 | 6 |
| LineTotal of `OrderLines`, equal to the orders' OrderTotal | $87,500,091.56 | 8 |
| Order lines with a PromotionID; their DiscountAmount | 1,650; $728,878.86 | 8 |
| LineTotal of `BilledLines` | $86,446,845.84 | 5 |
| CommissionRate | 1.903% | 2 |

> **Instructor notes, Requirement 1:** OrderLines has 22,269 rows and a LineTotal of 87,500,091.56, equal to the OrderTotal of the 5,819 orders (every order agrees with its own lines). 1,650 order lines carry a PromotionID (DiscountAmount 728,878.86), and no other line has a nonzero Discount. BilledLines has 27,933 rows and a LineTotal of 86,446,845.84. Items 266 rows, Customers 220, Promotions 9, Overrides 412, Employees 120; BudgetPrices keeps the 9,616 Revenue rows. CommissionRate is 1.903%: 2026 postings to account 6290 of 566,347.93, excluding closing entry JE-2026-000296, divided by 2026 invoice-line revenue of 29,756,420.08 (Tutorial 7.3). M formulas: OrderYear = Date.Year(\[OrderDate\]), OrderMonth = Date.Month(\[OrderDate\]), InvoiceQuarter = Date.QuarterOfYear(\[InvoiceDate\]). RevenuePostings: T3\_GLEntry filtered with Transform Data to SourceDocumentType SalesInvoice and PostingDate in 2026, merged with Accounts, and grouped by AccountNumber with Advanced (sum of Credit, sum of Debit).

## What a strong answer says

- **The queries.** Every query has the case's name, merges keep all rows, and the three amounts are unrounded.
- **The checks.** Each query is compared with its source, each filter says what it keeps, and the totals agree to the cent, on the Documentation sheet.
- **The documentation.** Sources, steps, type corrections, checks and open questions, so another person could refresh and follow the workbook.

A weak answer builds the queries and reports no checks, records a check without saying what agreement shows, or leaves the type correction undocumented.

## Common mistakes and how to respond

- **The type trap.** *Symptom:* DiscountAmount totals zero, and the distinct rates show only 0. *Cause:* Discount typed as a whole number from the first 200 rows. *Response:* ask what the Changed Type step did to 0.1, and send the student to **Replace current**.
- **An inner join.** *Symptom:* `OrderLines` has about 1,650 rows. *Response:* ask what the row-count check shows and which join kind keeps every row of the left query.
- **Duplicate column names.** *Symptom:* the expand step reports a column that already exists. *Response:* point to the Watch out and the Promo renames.
- **The ledger loaded whole.** *Symptom:* a slow load and a workbook far larger than the others. *Response:* ask where the filter belongs, and send the student back to **Transform Data**.
- **Checks without a source.** *Symptom:* row counts typed from memory. *Response:* ask what would happen to the check after a refresh.
- **Everything loaded.** *Symptom:* a sheet for `Invoices`, which only feeds `BilledLines`. *Response:* ask which queries a reader needs to see.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Documentation and Parameters | 15 | All entries, named blue inputs, the commission rate | Entries missing or inputs unnamed |
| OrderLines and BilledLines | 30 | All columns and amounts, types corrected, no rows lost | Right rows, an amount or type missing |
| The other queries | 15 | Filtered ledger import, budget and override queries | One query missing or loaded unfiltered |
| Completeness checks | 30 | Counts and totals against sources, filters explained | Totals without row counts, or no explanation |
| Documentation of the result | 10 | Checks and open questions recorded | Checks not recorded |

## Extensions and discussion questions

- Add a check that the invoice lines' total equals the invoices' SubTotal total, and say what it adds.
- Discuss: the checks passed. What could still be wrong that none of them tests?
- Discuss: how would you hand this workbook to a colleague whose copy of CharlesRiver.xlsx is in another folder?
