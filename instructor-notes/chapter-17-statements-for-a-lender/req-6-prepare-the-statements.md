# Requirement 6: Prepare the statements (Chapter 6)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 6 |
| Perspective | Financial accounting |
| Tools | More than one tool |
| Time | About 180 minutes |
| Solution file | Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheet Statements, built from the Tables WorkingTB and AdjustmentLines; Chapter17-capstone-pbi.zip: Charles River Lender Review, page Package Tests and the Tests 3 to 5 and Checks tabs; Chapter17-capstone-sql.zip: LenderPackage.sql, the two queries headed Requirement 6 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This requirement turns Requirement 5's schedule into the four statements the bank reads and shows that the package agrees with itself. The cash flow statement is where a reviewer looks hardest: no adjustment moves cash or changes how a cash flow is classified, so they may change lines of the reconciliation but no total. The workbook builds the statements; the Review file tests them by recomputing the balances from the ledger. The analytics type is descriptive, with a diagnostic test.

Students can prepare classified balance sheets and statements of income from the adjusted balances (Part 1), roll equity forward with the corrected year labeled restated (Part 2), prepare cash flows by the indirect method while disclosing what moved no cash (Part 3), and test the package against the ledger in a second tool (Part 4).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts, and transactions); IMA Reporting and Control (financial statement preparation); IFAC IES 2 (a); AACSB A5 part 5.1 (technology integration: Excel and Power BI).

## Before you assign

- **Files.** The workbook with Requirements 1 to 5 done (WorkingTB, the AdjustmentLines Table), the Review project of Requirement 2, `LenderPackage.sql` and CharlesRiver.xlsx.
- **Data conditions.** No income tax account exists and no distribution was posted (`3040` is unused); depreciation is charged partly to `1090`, so it never reaches an expense line; in the two years presented, equipment financed by a note and a disposal with no proceeds occur only in 2026.
- **Verify first.** Every entry balances and none touches `1010`. The AdjustmentLines Table holds 111 lines in 17 entries, with a totals row below.

## How to run it

Pairs, about 180 minutes: 50 for the balance sheets and income statements, 15 for equity, 50 for cash flows, 45 for the Review file, 20 for checks. Hold back the noncash entries until a student's sections fail to add up to the change in cash. **Collect** the Statements worksheet and the Review project.

## Step-by-step solution

### Part 1: Balance sheets and statements of income

**Step 1. Build the adjusted balance sheets.** On a worksheet named **Statements** give each year-end a column: 2026, 2025 (restated) and, as the model does, 2024 (restated), the opening balances of 2025, which as a classified column also needs R1's current portion at that year-end. Each line adds what WorkingTB records under its StatementLine to what the adjustment lines add at that year-end; liabilities and equity take the opposite sign. The model's formula for cash:

```
=(SUMIFS(WorkingTB[Recorded2026],WorkingTB[StatementLine],"Cash")+SUMIFS(AdjustmentLines[Amount],AdjustmentLines[StatementLine],"Cash",AdjustmentLines[YearEnd],YE_2026))
```

**Check:** total assets $39,373,005.22 and $31,858,224.86, equal to total liabilities and equity, so each check row is zero. **Watch for:** a retained earnings line without the year's net income, which the ledger has not closed. The check row then reads the income, $4,572,087.08 for 2026.

**Step 2. Build the statements of income by function.** Lay out operating revenue to net income by function, with the loss on disposals and an income taxes line marked not determined and shown as zero. Net income equals income before income taxes only if the tax expense is determined to be zero, so it is provisional.

**Check:** income before income taxes $4,572,087.08 and $5,057,894.81, the recorded income plus the schedule's effect. **Watch for:** the loss on a disposal, a debit on a revenue-type account. Adding it instead of subtracting it overstates income by $185,000.00 in 2026.

### Part 2: Changes in stockholders' equity

**Step 3. Roll equity forward from January 1, 2025.** Columns for common stock, retained earnings and total. Start from retained earnings as previously reported: the 2024 trial balance leaves out its own close, so that is `3030` plus 2024 net income. Add the correction, then each year's net income and distributions (none). The model's first row:

```
=RecRE_2024+RecNI_2024
```

**Check:** $15,294,129.73 as reported, -$175,240.12 of correction, $15,118,889.61 as restated; the year-end balances equal the balance sheets' ($20,176,784.42 and $24,748,871.50). **Watch for:** a roll-forward without the correction. Retained earnings then differ from the balance sheets by $175,240.12 at both year-ends.

### Part 3: Statements of cash flows

**Step 4. Build the indirect statement from the adjusted balances.** Start from adjusted net income, add back depreciation and the loss on disposals, and take the change in each working-capital line from the two adjusted balance sheets (receivables, inventories with `1090`, payables with goods received not invoiced, sales tax payable, accrued and other items). Add a column for each year as recorded. The model's depreciation line adds the expense account's depreciation to the Depreciation entries' debits to `1090`:

```
=SUMIFS(WorkingTB[Recorded2026],WorkingTB[AccountNumber],6130)+SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],1090,LedgerSummary[EntryType],"Depreciation",LedgerSummary[Year],2026)
```

Purchases paid in cash are additions less equipment financed by a note. The script's first Requirement 6 query gives the change in cash and interest paid by year, an independent check.

![A mock of the statement of cash flows, where the adjustments must change no total.](../figures/chapter-17-statements-for-a-lender/IF-17-6-A.pdf)

**Check:** 2026 operating -$807,189.75, investing $0.00, financing -$134,120.55, change in cash -$941,310.30; 2025 $3,975,026.14, -$397,000.00, -$83,434.28, $3,494,591.86. Adjusted and recorded operating totals agree, as offsetting cash lines would too, so Step 8's test of the lines on `1010` is the proof that no adjustment moves cash. **Watch for:** three slips, each caught by the check row. Starting from recorded income leaves the sections $68,475.84 short in 2026; adding back only the expense account's depreciation, $303,666.63 short; leaving out the loss, $92,500.00 short.

**Step 5. Disclose what moved no cash.** The script's second Requirement 6 query lists the investing events by FixedAssetEvent.FinancingType; read it by that column. In 2026 a $280,000.00 acquisition was financed by a note and one disposal brought no proceeds, so neither is a cash flow; the 2025 disposal had proceeds, which belong to investing; the 2024 row falls before the years presented. Add interest paid, income taxes paid (none recorded) and the noncash equipment below the statement.

**Check:** interest paid $28,946.47 and $19,513.12; 2025 purchases paid in cash $425,000.00, proceeds $28,000.00; no purchase in 2026. **Watch for:** two errors. Reporting the note-financed equipment as a purchase puts $280,000.00 in investing, and balancing it with a financing inflow reports cash that never arrived. Interest paid taken from the adjusted expense, $29,584.46, is $637.99 too high: the interest accrual.

### Part 4: The Review file's tests

**Step 6. Load the adjustment lines beside the ledger.** In the Review file choose **Home > Get data > Excel workbook**, select the package workbook, choose the AdjustmentLines Table and **Transform Data**. Keep the columns the file reads, filter out the totals row, type YearEnd as a date and **Close & Apply**. In **Model view** relate AdjustmentLines[Account] to Account[AccountNumber] and AdjustmentLines[YearEnd] to Date[Date], Many to one, **Single**.

**Check:** 111 lines. **Watch for:** the totals row, which Power Query reads as one more row. The count reads 112 and an entry named Total appears in the matrix, while debits and credits, each $1,993,762.48 higher, still agree.

**Step 7. Add the measures and the Package Tests page.** Under **Modeling > New measure**:

```
Adjustment Amount = SUM ( AdjustmentLines[Amount] )

Adjusted P&L Amount = [P&L Amount] - [Adjustment Amount]

Adjusted Net Income = CALCULATE ( [Adjusted P&L Amount], Account[AccountType] IN { "Revenue", "Expense" } )
```

The page holds a card visual titled "The adjustment lines of the package workbook", a matrix of debits and credits by entry, two tables comparing adjusted income and total assets with the workbook, and an adjusted income matrix. Use **Format > Edit interactions** so that no visual filters another.

**Check:** the difference between adjusted income and the workbook's is zero for 2025 and 2026. **Watch for:** without the relationship to Account the adjusted income is the ledger's, and the difference equals the effect on income, $68,475.84 in 2026; with the adjustment added instead of subtracted it is $136,951.68.

**Step 8. Run Tests 3 to 5 and the Checks tab.** In **DAX query view** type Tests 3 to 5 at the end of the Tests tab and choose **Run** for each. Test 3 lists each entry's debits, credits and difference, and Test 5 sets adjusted income and total assets by year against the workbook. Test 4, on the measures of the Key Measures table's Package folder, reads:

```dax
// Test 4: no adjustment touches cash, and no entry is out of balance
EVALUATE
ROW (
    "Lines on Cash", [Lines on Cash],
    "Entries", [Entries],
    "Entries out of Balance", [Entries out of Balance],
    "Lines with Inconsistent Amounts", [Lines with Inconsistent Amounts]
)
```

**Check:** each entry nets to zero, no line is on cash, and adjusted income and total assets agree with the workbook; the 43 Checks rows of this requirement all agree. The project tests these numbers; how the page renders is visible only in Desktop.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Income before income taxes, 2025; 2026 | $5,057,894.81; $4,572,087.08 | 2 |
| Retained earnings, January 1, 2025, restated | $15,118,889.61 | 3 |
| Operating cash flow, 2025; 2026 | $3,975,026.14; -$807,189.75 | 4 |

> **Instructor notes, Requirement 6:** balance sheets, 2026 / 2025: cash 8,442,255.80 / 9,383,566.10; receivables 4,843,285.43 / 4,755,337.09; inventories 23,935,720.45 / 15,178,832.94; prepaid 60,000.00 / 60,000.00; current assets 37,281,261.68 / 29,377,736.13; property and equipment, net 2,091,743.54 / 2,480,488.73; total assets 39,373,005.22 / 31,858,224.86; accounts payable 6,237,466.66 / 5,467,809.52; goods received not invoiced 1,020,992.06 / 969,574.35; accrued liabilities 852,116.20 / 811,301.30; sales tax payable 5,620,840.66 / 3,688,321.37; customer credits (2060) 3,413.46 / 1,008.67; current portion of notes 147,503.76 / 89,243.61; current liabilities 13,882,332.80 / 11,027,258.82; notes payable less current portion 241,800.92 / 154,181.62; total liabilities 14,124,133.72 / 11,181,440.44; common stock 500,000.00; retained earnings 24,748,871.50 / 20,176,784.42; total equity 25,248,871.50 / 20,676,784.42. Working capital 23,398,928.88 / 18,350,477.31; current ratio 2.69 / 2.66; quick ratio (cash and receivables) 0.957 / 1.28; cash net of sales tax 2,821,415.14. Income, 2025 / 2026: operating revenue 29,515,670.85 / 29,998,762.73; returns 201,104.38 / 242,764.56; net revenue 29,314,566.47 / 29,755,998.17; cost of goods sold 17,881,630.40 / 18,651,599.17; gross margin 11,432,936.07 / 11,104,399.00; operating expense 6,313,997.45 / 6,410,227.46; operating income 5,118,938.62 / 4,694,171.54; interest 19,043.81 / 29,584.46; loss on disposal 42,000.00 / 92,500.00; income before income taxes 5,057,894.81 / 4,572,087.08 (net income only if the current and deferred income tax expense is determined to be zero, which Requirement 9 leaves to the CFO, so the net income that the statements of equity and cash flows start from is provisional until then). With the old accruals kept (A3 held for evidence), 2026 / 2025: accrued liabilities 1,009,462.99 / 907,350.88; current liabilities 14,039,679.59 / 11,123,308.40; retained earnings 24,591,524.71 / 20,080,734.84; current ratio 2.66 / 2.64; quick ratio 0.946 / 1.27; income before income taxes 5,000,873.66 (2025) / 4,510,789.87 (2026); retained earnings at January 1, 2025, as restated 15,079,861.18; total assets and the cash flow totals as above. Retained earnings: January 1, 2025, as previously reported 15,294,129.73, correction -175,240.12, as restated 15,118,889.61; plus 2025 net income, 20,176,784.42; plus 2026, 24,748,871.50; no distributions. Cash flows, 2026 / 2025: net income 4,572,087.08 / 5,057,894.81; depreciation 576,245.19 / 542,423.80; loss on disposal 92,500.00 / 42,000.00; receivables -87,948.34 / +324,845.74; inventories, with 1090, -8,756,887.51 / -5,043,043.30; payables (2010, 2020) +821,074.85 / +1,087,218.19; sales tax +1,932,519.29 / +1,910,036.22; accrued and other +43,219.69 / +53,650.68; operating -807,189.75 / 3,975,026.14; investing 0.00 / -397,000.00 (425,000.00 paid, 28,000.00 of proceeds); financing -134,120.55 / -83,434.28; change in cash -941,310.30 / +3,494,591.86, which none of these adjustments changes, since none moves cash. Interest paid 28,946.47 / 19,513.12; income taxes paid: none recorded (a matter for the CFO); noncash: 280,000.00 of equipment financed by a note in 2026. Review tests: every entry nets to zero, none posts to 1010, adjusted net income equals the workbook's, and recorded total assets equal Requirement 1's.

## What a strong answer says

- **Statements.** Four statements that agree with one another, the corrected year labeled restated.
- **Cash flows.** Operating cash flow of -$807,189.75 in 2026, as the ledger gives it, because no adjustment moves cash; the noncash equipment and the disposal without proceeds disclosed, not reported.
- **Review file.** Tests that fail loudly, and a stated limit: two accounts off by equal and opposite amounts leave a total unchanged.

A weak answer plugs the cash flow sections or skips the tests.

## Common mistakes and how to respond

- **Recorded income in the cash flows.** *Symptom:* sections $68,475.84 short. *Response:* ask which income the adjusted balances produce.
- **Note-financed equipment as a purchase.** *Symptom:* investing of -$280,000.00. *Response:* ask what cash left the company.
- **No correction in the equity roll-forward.** *Symptom:* retained earnings $175,240.12 off the balance sheets. *Response:* ask which balance the shareholders were given.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Balance sheets and income statements | 25 | Both years, classified, balanced, income equal to the schedule | One year, or a plug |
| Equity statement | 15 | Correction shown, restated labels, ties to the balance sheets | No correction |
| Cash flows | 30 | Sections add to the change in cash; adjusted equals recorded | Plugged sections |
| Noncash items and supplemental information | 10 | Disclosed and excluded | Reported as cash |
| Review file tests | 20 | Lines, relationships, measures, Tests 3 to 5, Checks agree | Page without tests |

## Extensions and discussion questions

- Rebuild the statements for the retained-liability answer to A3 (current ratio 2.66 against 2.69) and compare the two presentations.
- Discuss: income of $4,572,087.08 against operating cash flow of -$807,189.75. What does each tell the bank?
