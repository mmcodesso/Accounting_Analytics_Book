# Requirement 2: Explain where the cash went (Chapters 14 and 15; financial reporting)

| | |
|---|---|
| Unit | Case Part 4: Finding the Cash Behind the Profit |
| Item | Requirement 2 |
| Perspective | Financial accounting |
| Tools | Power BI Desktop |
| Time | About 180 minutes |
| Solution file | PartIV-case.zip: Charles River Cash Case.pbip, pages Balance Sheet, Cash Bridge and Bridge Detail (the hidden drill-through page), Test 3 of the Tests tab and the Requirement 2 rows of the Checks tab |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The income statement cannot say where the cash went, so the requirement bridges net income to the change in cash, finds the entries that moved no cash and restates the sections as the indirect method requires (ASC Topic 230 reports only cash receipts and payments and discloses noncash activities apart). Its technical lessons are KEEPFILTERS and the difference between a flow and a difference of balances. The analytics type is descriptive, with diagnostic work in the drill-through.

Students can:

- show balance sheets and ratios and say what each hides (Step 1);
- assign accounts to bridge steps and measure each step from the year's postings (Steps 2 and 3);
- chart the year as a waterfall and explain why the first year reads differently (Step 4);
- drill through to the entries that moved no cash and restate the sections (Steps 5 and 6);
- measure cash net of the recorded sales tax payable and the notes due within a year (Step 7).

**Competencies practiced.** CPA Evolution BAR M9 (financial statement analysis and working capital) and Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Reporting and Control (financial statement analysis); IFAC IES 2 (a), financial accounting and reporting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Requirement 1's file. The model answer is in PartIV-case.zip: the pages above and Test 3.
- **Data conditions.** The opening entry JE-2024-000001 is a 2024 posting; one equipment invoice moved to notes payable in 2026; 2025 and 2026 each have one asset disposal; the notes sit in account `2110`; the debt schedule runs past the Date table.
- **Verify first.** Test 3 agrees for 2025 and 2026, and so do the 120 Requirement 2 rows of the Checks tab.

## How to run it

Pairs, about 180 minutes: 25 for the balance sheet, 45 for the columns and measure, 30 for the waterfall, 50 for the drill-through and restatement, 30 for tax and notes. **Collect** the .pbix.

## Step-by-step solution

The Checks tab proves every value; colors, order and the drill-through button are visible only in Desktop.

### Part 1: The balance sheet and the ratios

**Step 1. Show the year-ends.** Add a **Matrix** with AccountType and AccountSubType on **Rows**, Year on **Columns** and `Statement Balance` in **Values**, titled "Balances at each fiscal year-end, before that day's closing entries", and a **Table** titled "Working capital at each fiscal year-end" with the working capital, current ratio and quick ratio.

**Check:** `Statement Balance` reverses the sign of liabilities and equity. Working capital $13,453,076.71, $18,691,420.94, $23,729,656.82; current ratio 2.77, 2.75, 2.76; quick ratio 1.43, 1.32, 0.98. The current ratio hides the change, and the quick ratio, cash and receivables over current liabilities, falls. Inventories are 64% of 2026 current assets.

### Part 2: The bridge columns and the measure

**Step 2. Add Step and Activity to Account.** In Power Query, choose **Add Column > Custom Column** for `Step`, an if-then-else chain on account numbers first and subtypes after, and for `Activity`; sort Step by a step-order column, as Tutorial 15.1 sorted its Steps table.

```m
    #"Added Custom" = Table.AddColumn(#"Removed Other Columns", "Step", each if [AccountNumber] = 1010 then "Cash"
        else if [AccountType] = "Revenue" or [AccountType] = "Expense" then "Net income"
        else if [AccountSubType] = "Contra Fixed Asset" then "Depreciation"
        else if [AccountNumber] = 1020 or [AccountNumber] = 1030 then "Receivables"
        else if [AccountNumber] = 1040 or [AccountNumber] = 1045 or [AccountNumber] = 1046 then "Inventories"
        else if [AccountSubType] = "Current Asset" or [AccountSubType] = "Contra Current Asset" then "Other current assets"
        else if [AccountNumber] = 2010 or [AccountNumber] = 2020 then "Payables"
        else if [AccountNumber] = 2050 then "Sales tax"
        else if [AccountSubType] = "Current Liability" then "Other current liabilities"
        else if [AccountSubType] = "Fixed Asset" or [AccountSubType] = "Noncurrent Asset" then "Fixed assets" else "Debt and equity")
```

**Check:** `1030` falls in Receivables, `1090` and `8020` in Other current assets, `2110` in Debt and equity by default. **Watch for:** cash among the steps. They then sum to zero, because every entry balances: the other accounts' effects add up to the change in cash, and the cash step is its opposite.

**Step 3. Write the measures.** Choose **Modeling > New measure** for each.

```dax
Cash Effect = CALCULATE ( - [GL Amount], KEEPFILTERS ( Account[Step] <> "Cash" ) )

Change in Cash = CALCULATE ( [GL Amount], Account[Step] = "Cash" )
```

**Check:** Test 3 shows the steps ending at the change in cash for 2025 and 2026. **Watch for:** two wrong versions. Without KEEPFILTERS every step reads -$941,310.30, the change in cash. A bridge from differences of Balance gives a net income step of -$630,743.47, 2026's less 2025's, and a debt and equity step of $5,280,234.16, because the 2025 close sits in retained earnings.

### Part 3: The waterfall and the first year

**Step 4. Chart the year.** Add a **Waterfall chart** with Step on **Category** and Cash Effect on **Y-axis**, titled "From net income to the change in cash, in the year selected", and a **Slicer** (**Tile**, **Single select**) on Year. Filter out the Cash step in **Filters on this visual**, sort the steps in their order, and add a **Matrix** of the bridge by year titled "The bridge by year (drill through on a step to its postings)".

**Check:** 2026: net income $4,503,611.24, inventories -$8,754,515.25, change in cash -$941,310.30, from $9,383,566.10 to $8,442,255.80. 2025: inventories -$5,022,322.02 and cash up $3,494,591.86. **Watch for:** reading 2024 like 2025. The opening entry is a 2024 posting, so the bridge starts from zero cash, shows $5,888,974.24 and puts $11,010,680.97 in financing; without it the change is $3,792,603.12 from an opening cash line of $2,096,371.12.

![A mock of the Cash Bridge page of the model answer, the exhibit that answers the committee's first question.](../figures/case-part-4/IF-C4-2-A.pdf)

### Part 4: The entries that moved no cash

**Step 5. Drill through.** Add a hidden **Bridge Detail** page with Step in the **Drillthrough** well and a **Table** of postings titled "Postings behind the step drilled through". Right-click Fixed assets and Debt and equity in the matrix and choose **Drillthrough > Bridge Detail**.

**Check:** the postings hold GR-2026-015616 ($280,000.00 of equipment debited to `1185`), JE-2026-000001 (invoice 21692 moved to notes) and the disposal JE-2026-000115 (loss $92,500.00, no proceeds).

**Step 6. Restate the sections.** Add measures for the disposal and the financed equipment, the restated measure below, and a **Matrix** titled "Cash flows by activity, as recorded and restated by the indirect method".

```dax
Restated Cash Flow =
VAR Recorded = [Cash Effect]
RETURN
    SWITCH (
        SELECTEDVALUE ( Account[Activity] ),
        "Operating", Recorded + [Disposal Write-off] + [Disposal Loss],
        "Investing", Recorded + [Financed by Notes] - [Disposal Cost] + [Disposal Proceeds],
        "Financing", Recorded - [Financed by Notes],
        Recorded
    )
```

**Check:** 2026 restated: operating -$807,189.75, investing $0.00, financing -$134,120.55, with $280,000.00 of equipment acquired by a note disclosed. **Watch for:** sections left as recorded. Financing reads $145,879.45 where the restated one is -$134,120.55, and investing -$70,000.00 where it is zero. The depreciation step ($458,745.19) is net of the write-off; the entries were $576,245.19.

### Part 5: Cash net of tax and the notes

**Step 7. Measure what the cash is worth.** Add `Cash Net of Sales Tax`, `Sales Tax Payable` and `Principal Due within a Year` as cards titled "At the end of fiscal 2026".

**Check:** cash net of the recorded tax payable ($5,620,840.66) is $2,821,415.14, a liquidity sensitivity (tax billed, not all collected). The notes are $389,304.68, and $147,503.76 falls due in 2027 yet sits in `2110`. **Watch for:** the schedule filtered through Date, which drops 44 payments past the table's end and reads $147,503.76, or on PaymentDate alone, which at an earlier year-end counts a note not yet originated.

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax
EVALUATE
ROW (
    "Change in cash 2026", ROUND ( CALCULATE ( [Change in Cash], 'Date'[Year] = 2026 ), 2 ),
    "Sum of the steps", ROUND ( CALCULATE ( [Cash Effect], 'Date'[Year] = 2026 ), 2 ),
    "Restated financing", ROUND ( CALCULATE ( [Restated Cash Flow], 'Date'[Year] = 2026, Account[Activity] = "Financing" ), 2 )
)
```

## Expected results

| Quantity (2026) | Value | Step |
|---|---|---|
| Net income; inventories; change in cash | $4,503,611.24; -$8,754,515.25; -$941,310.30 | 4 |
| Restated operating; investing; financing | -$807,189.75; $0.00; -$134,120.55 | 6 |
| Operating, tax increase paid (a sensitivity) | -$2,739,709.04 | 6 |
| Cash net of tax; principal due next year | $2,821,415.14; $147,503.76 | 7 |

> **Instructor notes, Requirement 2:** year-end 2024 / 2025 / 2026: current assets 21,074,807.78 / 29,358,195.27 / 37,236,780.57; current liabilities 7,621,731.07 / 10,666,774.33 / 13,507,123.75; working capital 13,453,076.71 / 18,691,420.94 / 23,729,656.82; current ratio 2.77 / 2.75 / 2.76; quick ratio (cash 1010 and receivables 1020 over current liabilities, not current assets less inventories) 1.43 / 1.32 / 0.98; inventories are 64% of 2026 current assets, so the current ratio hides the change that the quick ratio shows. Steps: 1010 Cash (left out of the waterfall, or the steps sum to zero); Revenue and Expense accounts, net income; Contra Fixed Asset, depreciation; 1020 and 1030, receivables; 1040, 1045, 1046, inventories; other Current Asset and Contra Current Asset (including 1090 with a credit balance, 46,730.55, and 8020), other current assets; 2010 and 2020, payables; 2050, sales tax; other Current Liability, other current liabilities; Fixed Asset and Noncurrent Asset, fixed assets (investing); Long-Term Liability, Equity, and the rest, debt and equity (financing). The if-then-else chain of Tutorial 16.1 builds it. Cash Effect = CALCULATE ( - \[GL Amount\], KEEPFILTERS ( Account\[Step\] \<\> "Cash" ) ); without KEEPFILTERS every step shows the change in cash (checked in the engine). 2026: net income 4,503,611.24; depreciation +458,745.19; receivables -63,008.09; inventories -8,754,515.25; other current assets -2,372.26; payables +821,074.85; sales tax +1,932,519.29; other current liabilities +86,755.28; fixed assets -70,000.00; debt and equity +145,879.45; change in cash -941,310.30 (9,383,566.10 to 8,442,255.80). 2025: 5,134,354.71; +444,423.80; +254,247.67; -5,022,322.02; -20,721.28; +1,087,218.19; +1,910,036.22; +47,788.85; -257,000.00; -83,434.28; change +3,494,591.86. A bridge from differences of Balance at 2026-12-31 keeps the 2025 close in retained earnings, so its net income step becomes 2026's less 2025's. 2024: the opening entry (18 lines, JE-2024-000001) is a 2024 posting, so the bridge starts from zero cash and shows +5,888,974.24 with financing of 11,010,680.97; without it, +3,792,603.12 from the opening cash line of 2,096,371.12, with receivables -4,610,043.90 that only fill the ledger from the 380,000 opening line. As recorded, 2026 activities are operating -1,017,189.75, investing -70,000.00, and financing +145,879.45. Noncash entries: equipment of 280,000 received (GR-2026-015616, debit 1185) and financed by a note (JE-2026-000001 moves the invoice, PI 21692, from 2010 to 2110), and the disposal JE-2026-000115 (Cr 1185 210,000.00, Dr 1186 117,500.00, loss 92,500.00 in 7020, no proceeds). Depreciation entries were 576,245.19, so the step is depreciation net of the 117,500.00 written off. Restated 2026: operating -807,189.75 (net income, depreciation 576,245.19, the loss 92,500.00, and changes in working capital of -5,979,546.18), investing 0.00, financing -134,120.55 (23 principal payments), with 280,000.00 of equipment acquired by a note disclosed. Restated 2025: operating 3,975,026.14 (depreciation 542,423.80 and a loss of 42,000.00 on JE-2025-000028), investing -397,000.00 (425,000.00 of equipment paid in cash on PI 8865, 16416, and 18958, less proceeds of 28,000.00), financing -83,434.28. Cash net of sales tax payable: 8,442,255.80 - 5,620,840.66 = 2,821,415.14 (5,695,244.73 at 2025, 4,110,689.09 at 2024), a liquidity sensitivity. 2050 holds tax billed, not tax collected, and 866 taxable invoices unpaid at the year-end hold 232,384.17 of it. Its growth added 1,778,285.15, 1,910,036.22, and 1,932,519.29 a year. Had 2026's increase been paid in the year, operating cash flow would have been -2,739,709.04, a sensitivity. Notes: 389,304.68 outstanding, equal to the schedule (154,181.62 and 235,123.06); 147,503.76 of principal is due in 2027, yet all of it sits in 2110, a Long-Term Liability, so it should be reclassified to current, which lowers working capital. Counting only the notes originated by each date, the schedule gives 326,859.51 and 243,425.23 at the 2024 and 2025 year-ends, equal to 2110, and 89,243.61 due within a year at 2025. Without that filter it adds the 2026 note's 280,000.00 at both and puts 134,120.55 due at 2025. Engine-checked.

## What a strong answer says

- **Balance sheet.** The current ratio barely moves; the quick ratio falls below one, because inventories are most of current assets.
- **Bridge.** The recorded profit went into inventories, the growth of the recorded tax payable and of payables held cash up, and the steps end at the change in cash. The opening entry makes 2024 start from zero cash.
- **Sections.** The entries that moved no cash named, the sections restated, the note disclosed.
- **Cash and notes.** Net of the recorded tax payable, cash is far smaller, a sensitivity. The notes' current portion belongs in current liabilities.

## Common mistakes and how to respond

- **Cash among the steps.** *Symptom:* steps sum to zero. *Response:* ask what a balanced entry guarantees about the sum of every account.
- **Bridge from balances.** *Symptom:* net income of -$630,743.47. *Response:* ask where the 2025 close went.
- **Sections as recorded.** *Symptom:* financing of $145,879.45. *Response:* ask which entries moved no cash.
- **Schedule through Date, or without origination.** *Symptom:* notes of $147,503.76, or $523,425.23 at the end of 2025. *Response:* ask which dates the table covers and when each note began.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Balance sheet and ratios | 15 | Signed by type; both ratios; what each hides | Ratios without the reading |
| Bridge columns and measures | 25 | Step and Activity; KEEPFILTERS; steps end at the change in cash | Right values, no KEEPFILTERS |
| Waterfall and years | 15 | Sorted; 2025 compared; first year explained | No reason for the first year |
| Drill-through and restatement | 30 | Entries found; sections restated; note disclosed | Entries found, not restated |
| Cash net of tax and notes | 15 | Both measured; balance sheet effects stated | One measured |

## Extensions and discussion questions

- Rebuild 2024 with `Cash Effect without Opening` and say what it can show.
- Discuss: no remittance of the sales tax is recorded. What would the committee need before it counts that cash as its own?
