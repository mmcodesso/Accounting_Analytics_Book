# Requirement 3: Measure how fast working capital turns (Chapters 14 and 15; managerial accounting)

| | |
|---|---|
| Unit | Case Part 4: Finding the Cash Behind the Profit |
| Item | Requirement 3 |
| Perspective | Managerial accounting |
| Tools | Power BI Desktop |
| Time | About 180 minutes |
| Solution file | PartIV-case.zip: Charles River Cash Case.pbip, page Working Capital and its hidden tooltip page WC Tooltip, the field parameter table WC Measure, the display folders Working capital, Working capital (average balance) and Policy targets, and the Requirement 3 rows of the Checks tab |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Balances say how much cash is tied up; days say how long it stays. The requirement writes four measures of days, each a quarter-end balance over its own flow for the twelve months before, with a guard for the months that do not exist. Its lessons are that every ratio needs a stated definition, that each balance needs its own flow, and that an opening entry can hide what 2024 shows. The analytics type is diagnostic, with a predictive edge in the targets.

Students can:

- write the four measures and the cycle with a guard that blanks incomplete windows (Steps 1 and 2);
- add days of supply for materials and finished goods and compare them with the policy targets (Step 3);
- build a field-parameter page with a tooltip and icons (Step 4);
- compare versions with and without the opening entry and on the average balance, and say which the committee should see (Step 5).

**Competencies practiced.** CPA Evolution BAR M9 (financial statement analysis and working capital) and Core S1 M4 (financial statement analysis and performance measures); IMA Reporting and Control (financial statement analysis) and Strategy, Planning, and Performance (performance management); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Requirements 1 and 2 done, with Data Through. The model answer is in PartIV-case.zip: the page and tooltip above.
- **From earlier work.** Tutorial 15.3's twelve-month guard, Exercise 15.3's field parameter, Tutorial 15.1's tooltip and Chapter 15's conditional formatting.
- **Data conditions.** Cost of goods sold includes freight-out and the variances, and the closes credit it; each policy target is one number for raw materials and one for packaging; every policy ends at the year-end of the current fiscal year; the Date table runs past Data Through.
- **Verify first.** The 127 Requirement 3 rows of the Checks tab agree.

## How to run it

Pairs, about 180 minutes: 40 for the measures, 25 for days of supply, 55 for the page, 40 for the comparison and discussion, 20 spare. Hold back the opening-entry question until the first quarter is on the chart. **Collect** the .pbix and a half page on which version to show.

## Step-by-step solution

The Checks tab proves every value; the icons, the tooltip and the parameter slicer are visible only in Desktop.

### Part 1: The measures

**Step 1. Write the window and the flows.** Choose **Modeling > New measure** for each. Every flow reads the twelve months that end on the last date in the filter context.

```dax
Full Twelve Months =
VAR Window =
    DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -12, MONTH )
VAR MonthsInWindow =
    COUNTROWS ( CALCULATETABLE ( VALUES ( 'Date'[YearMonth] ), Window ) )
RETURN
    MonthsInWindow = 12 && MAX ( 'Date'[Date] ) <= [Data Through]

Billing TTM =
CALCULATE (
    SUM ( GLEntry[Debit] ),
    Account[AccountNumber] = 1020,
    GLEntry[SourceDocumentType] = "SalesInvoice",
    DATESINPERIOD ( 'Date'[Date], MAX ( 'Date'[Date] ), -12, MONTH )
)
```

**Check:** the guard is true only when twelve months exist and end by Data Through, so 2024-Q4 is the first quarter with a value. **Watch for:** a quarter's flow in place of the year's, which makes DSO 224.1 against 54.9 in 2026-Q4; revenue in place of billing, 59.1, because receivables carry tax and freight; and a cost of goods sold that keeps the closes. Debits less credits reads 10,296.6 days of DIO in 2026-Q3, where a window holds an old close, and nothing at all in 2026-Q4, where the window holds its own.

**Step 2. Write the days and the cycle.**

```dax
DSO = IF ( [Full Twelve Months], DIVIDE ( [Receivables], [Billing TTM] ) * 365 )

DIO = IF ( [Full Twelve Months], DIVIDE ( [Inventories], [COGS TTM] ) * 365 )

DPO = IF ( [Full Twelve Months], DIVIDE ( [Payables], [Supplier Invoices TTM] ) * 365 )

Cash Conversion Cycle = IF ( [Full Twelve Months], [DSO] + [DIO] - [DPO] )

Materials Days = IF ( [Full Twelve Months], DIVIDE ( [Materials], [Issues TTM] ) * 365 )
```

**Check:** from 2024-Q4 to 2026-Q4 DSO runs 62.2 to 54.9, DIO 229.9 to 469.8, DPO 118.4 to 98.9 and the cycle 173.7 to 425.7. **Watch for:** one flow for every balance. Materials against cost of goods sold read 230.2 days in 2026-Q4 where the right flow gives 422.1, and payables against it read 122.2 against 98.9.

### Part 2: Days of supply

**Step 3. Compare with the targets.** Add the target measures and their ratios to the days of supply, then read raw materials at 28 days, packaging at 24, and finished goods at 12 to 16 (manufactured) and 24 to 28 (purchased).

**Check:** materials stand at 422.1 days in 2026-Q4, against 29.3 in 2024-Q4, and finished goods at 280.8 against 235.5. The model answer's target measures take the largest target of each class, a benchmark for the company-level days, which cannot show whether each item meets its own policy. Every policy ends at the current year-end, so targets for the next year need approval.

### Part 3: The page

**Step 4. Build the page.**

a. Choose **Modeling > New parameter > Fields**, name it `WC Measure`, and add the six measures in order; keep the slicer.
b. Add a **Line chart** with YearQuarter on the **X-axis** and the parameter on the **Y-axis**, titled "The measure chosen, at each quarter-end (hover for the balances and flows)".
c. Add a tooltip page: **Canvas settings** Type Tooltip, **Page information** **Tooltip** on, and a table of each balance beside its flow. In the line chart's **Format visual > General > Tooltips**, choose that page.
d. Add a **Matrix** titled "The measures at each quarter-end (icons: days of supply against the largest item target)", with **Conditional formatting > Icons** (**Format style** **Rules**) on the days of supply: up from 1.25 times the target, down at 0.8 or below.

```dax
{
    ("DSO", NAMEOF ( 'Key Measures'[DSO] ), 0),
    ("DIO", NAMEOF ( 'Key Measures'[DIO] ), 1),
    ("DPO", NAMEOF ( 'Key Measures'[DPO] ), 2),
    ("Cash Conversion Cycle", NAMEOF ( 'Key Measures'[Cash Conversion Cycle] ), 3),
    ("Materials Days", NAMEOF ( 'Key Measures'[Materials Days] ), 4),
    ("Finished Goods Days", NAMEOF ( 'Key Measures'[Finished Goods Days] ), 5)
}
```

**Check:** the slicer, titled "Measure", changes the line; hovering shows a balance and its flow. **Watch for:** a missing guard. 2024-Q1 then reads 253.7 days of DSO, with under a year of billing behind it, and 2027-Q1, which lies after Data Through, reads 73.5 where the model answer is blank. Test 5 of Requirement 5 finds the second.

![A mock of the Working Capital page of the model answer, the exhibit with the measures at each quarter-end.](../figures/case-part-4/IF-C4-3-A.pdf)

### Part 4: The comparison

**Step 5. Test the opening entry and the average.** Add the measures that leave out the lines of JE-2024-000001 and the average-balance versions, and a **Table** titled "Year-end measures against the versions on the year's average balance".

```dax
DSO without Opening =
IF (
    [Full Twelve Months],
    DIVIDE ( CALCULATE ( [Receivables], GLEntry[VoucherNumber] <> "JE-2024-000001" ), [Billing TTM] ) * 365
)

DSO on Average Balance =
IF (
    HASONEVALUE ( 'Date'[Year] ) && MAX ( 'Date'[Date] ) <= [Data Through],
    DIVIDE ( CALCULATE ( [Average Balance], Account[AccountNumber] = 1020 ), CALCULATE ( SUM ( GLEntry[Debit] ), Account[AccountNumber] = 1020, GLEntry[SourceDocumentType] = "SalesInvoice" ) ) * 365
)
```

**Check:** without the opening line DSO runs 57.4 to 50.5 and DPO 66.2 to 65.7. The cycle moves 252.0 days as recorded and 233.4 without the opening line; DIO moves 239.9, DSO -7.3 and DPO -19.5. The average-balance materials days are 76.7 in 2024 and 288.9 in 2026.

![Which component moved the cycle, so students see that receivables and payables are flat beside inventory.](../figures/case-part-4/IF-C4-3-B.pdf)

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax
EVALUATE
ROW (
    "DSO 2026-Q4", ROUND ( CALCULATE ( [DSO], 'Date'[YearQuarter] = "2026-Q4" ), 1 ),
    "Cycle 2026-Q4", ROUND ( CALCULATE ( [Cash Conversion Cycle], 'Date'[YearQuarter] = "2026-Q4" ), 1 ),
    "DSO 2024-Q1", CALCULATE ( [DSO], 'Date'[YearQuarter] = "2024-Q1" ),
    "DSO 2027-Q1", CALCULATE ( [DSO], 'Date'[YearQuarter] = "2027-Q1" ),
    "Materials target", CALCULATE ( [Materials Target Days], 'Date'[Year] = 2026 )
)
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| DSO, DIO, DPO, cycle in 2026-Q4 | 54.9; 469.8; 98.9; 425.7 | 2 |
| Materials days; finished goods days | 422.1; 280.8 | 3 |
| Cycle without the opening line, 2024-Q4 and 2026-Q4 | 221.2; 454.6 | 5 |
| Average-balance DSO, DIO, materials, DPO, 2026 | 54.5; 384.0; 288.9; 92.8 | 5 |

> **Instructor notes, Requirement 3:** definitions: billing = SalesInvoice debits to 1020; cost of goods sold = GL Amount on AccountSubType "COGS" (the close JE-2026-000296 credits COGS by 18.63 million, so a window that includes a close reads zero without GL Amount; COGS here includes freight-out, purchase price variance, and manufacturing variance); supplier invoices = PurchaseInvoice credits to 2010; materials flow = MaterialIssue credits to 1045; finished goods flow = Shipment credits to 1040. Window = DATESINPERIOD ( 'Date'\[Date\], MAX ( 'Date'\[Date\] ), -12, MONTH ), with the twelve-month count of Tutorial 15.3 and MAX ( 'Date'\[Date\] ) \<= \[Data Through\]; 2024-Q1 to Q3 and every 2027 quarter are blank (checked in the engine). Quarter-ends 2024-Q4 to 2026-Q4: DSO 62.2, 61.1, 58.8, 56.7, 54.9, 59.2, 58.5, 55.4, 54.9; DIO 229.9, 237.6, 249.8, 269.4, 311.7, 338.3, 372.8, 414.7, 469.8; materials days 29.3, 69.7, 93.8, 126.3, 158.1, 229.9, 282.8, 351.0, 422.1; finished goods days 235.5, 222.7, 228.5, 228.4, 255.8, 245.5, 253.5, 258.1, 280.8; DPO 118.4, 107.6, 109.1, 110.0, 106.2, 101.8, 103.2, 96.8, 98.9; cycle 173.7, 191.2, 199.5, 216.1, 260.4, 295.7, 328.1, 373.2, 425.7. Without JE-2024-000001: DSO 57.4, 56.6, 54.4, 52.4, 50.5, 54.9, 54.1, 51.1, 50.5; DPO 66.2, 62.9, 62.8, 66.3, 65.5, 63.5, 67.4, 62.0, 65.7; cycle 221.2 at 2024-Q4, 296.7 at 2025-Q4, 454.6 at 2026-Q4. Average-balance versions by year (beginning balance of 2024 = the opening entry): DSO 33.5 / 56.3 / 54.5; DIO 201.6 / 260.3 / 384.0; materials 76.7 / 94.6 / 288.9; DPO 85.3 / 99.2 / 92.8; they lag a fast build (289 against 422 days in 2026) and in 2024 rest on the opening entry, so materials look like 77 days when the year-end stock stood at 29. Policy targets: raw materials 28 days and packaging 24; finished goods 12-16 (manufactured, lot-for-lot) and 24-28 (purchased); every policy ends 2026-12-31. The company-level icons use the largest target of each class (28 days for materials, 28 for finished goods), labeled as a benchmark, which cannot show whether each item meets its own policy. Value-weighted payment terms: customers about 44 days, suppliers about 40, so receivables, without the opening line, run about a week beyond terms (11 days as recorded) and payables, without it, almost four weeks beyond. Conclusion: receivables and payables barely moved, and the cycle grew mainly through inventory, materials above all (without the opening lines, DIO rose by more than the cycle). The apparent fall of DPO from 118 to 99 days as recorded is the constant 2.1 million of unsupported opening payables diluted by growing purchases.

## What a strong answer says

- **Definitions.** Each flow named: billing with tax and freight, cost of goods sold without the closes, issues, shipments, supplier invoices.
- **Movement.** Receivables and payables barely move, and the cycle grows mainly through inventory, materials above all, far beyond the benchmarks. The apparent fall of DPO is the unsupported opening payables diluted by purchases.
- **Which version.** The quarter-end versions on full windows, without the opening lines where they distort; 2024 shows only its last quarter, and the average lags a fast build.

A weak answer reports the numbers without saying which flow each uses.

## Common mistakes and how to respond

- **A quarter's flow.** *Symptom:* DSO of 224.1. *Response:* ask how many quarters the balance is compared with.
- **Closes in the cost of goods sold.** *Symptom:* DIO of 10,296.6 or blank. *Response:* ask what a close does to the account.
- **One flow for every balance.** *Symptom:* materials of 230.2 days. *Response:* ask what consumes materials.
- **No guard.** *Symptom:* 253.7 days in 2024-Q1. *Response:* ask how much billing the window holds.
- **Average balance on the first year.** *Symptom:* materials days of 76.7 for a year-end of 29.3. *Response:* ask what the beginning balance stands for.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Measures and guard | 30 | Four days and the cycle; own flows; guard blanks early and late quarters | Right values, no guard |
| Days of supply and targets | 15 | Both days of supply; targets compared | Days without targets |
| Page | 25 | Parameter, tooltip, matrix with icons, titled | Chart without tooltip or icons |
| Comparison and explanation | 30 | Both versions; component named; version chosen with reasons | Versions without the choice |

## Extensions and discussion questions

- Add finished goods at the target as a measure and say what it leaves out.
- Remove the guard from one measure, rerun Test 5 of Requirement 5 and report what it shows.
- Discuss: customers pay in about 44 days by terms and suppliers are paid in about 40. What does it mean that both run beyond terms?
- Discuss: why is a day count a better measure for a committee than a balance?
