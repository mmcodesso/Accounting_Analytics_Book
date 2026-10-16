# Requirement 7: Build the note schedules from the records (Chapters 6, 10, 11, and 14)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 7 |
| Perspective | Financial accounting |
| Tools | More than one tool |
| Time | About 150 minutes |
| Solution file | Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 7 (the register and its depreciation, disposals, notes, maturities, revenue, contract balances, services, components); Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheets Notes (the schedules and the text of the notes) and Fixed Assets |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A note is a schedule that the records can produce and that must agree with a line of the statements. Rebuilding a register, a debt schedule or revenue by product line joins documents to the ledger, which suits SQL; the workbook formats each schedule beside its statement and holds the text. The case allows Chapter 14's sales model for the revenue note if it is reconciled to the ledger and the cutoff, so students choose and say why. The analytics type is descriptive.

Students can roll property and equipment forward and reconcile it (Part 1), state the notes' terms, maturities and current portion (Part 2), disaggregate revenue on the adjusted basis (Part 3), break accrued liabilities and inventories into components (Part 4), and write the notes (Part 5).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 and BAR M10 (advanced data analytics: data models and joins); IMA Reporting and Control (financial statement preparation); IFAC IES 2 (a); AACSB A5 part 5.1 (technology integration: Excel and SQL).

## Before you assign

- **Files.** `LenderPackage.sql`, the workbook with Requirements 1 to 6 done, and CharlesRiver.xlsx for the Fixed Assets Table.
- **Data conditions.** FixedAsset holds no residual values; each note links to its asset through DebtAgreement.FixedAssetID, and no column records a security interest; design services and freight billed each have their own revenue account; `2070` is unused; every billable service hour is billed.
- **Verify first.** The register, at monthly amounts rounded to the cent, reproduces the ledger's depreciation.

## How to run it

Pairs, about 150 minutes: 35 for property and equipment, 20 for the notes payable, 35 for revenue, 20 for accrued liabilities and inventories, 30 for the text, 10 to check. Give the dates rule (the month after service through the month before disposal) only when the register and the ledger differ. **Collect** the Notes worksheet.

## Step-by-step solution

### Part 1: Property and equipment

**Step 1. Rebuild the register's depreciation.** In Excel load FixedAsset with its account numbers and add a first month, a last month and a monthly amount; the SQL does the same in the Register CTE of the first two Requirement 7 queries. The model's last month ends at the life or the month before disposal:

```
=LET(e,YEAR([@InServiceDate])*12+MONTH([@InServiceDate])-1+[@UsefulLifeMonths],IF(ISNUMBER([@DisposalDate]),MIN(e,YEAR([@DisposalDate])*12+MONTH([@DisposalDate])-2),e))
```

**Check:** the register's depreciation equals the ledger's Depreciation entries, $542,423.80 in 2025 and $576,245.19 in 2026, on lives of 48 to 120 months and no residual value. **Watch for:** counting the month of disposal, one more month for each disposed asset: the register exceeds the ledger by $2,000.00 in 2025 and $2,500.00 in 2026.

**Step 2. Roll cost and accumulated depreciation forward by class.** Four classes; for each year the opening balance, additions, disposals and closing balance, with the opening and closing taken from WorkingTB, disposals from the credits of the Asset Disposal entries, and a check column against the register.

**Check:** cost $4,027,000.00, $4,284,000.00, $4,354,000.00; accumulated depreciation $1,359,087.47, $1,803,511.27, $2,262,256.46. Disposals: WH-0001 (loss $42,000.00, proceeds $28,000.00) and MFG-0004 (loss $92,500.00, no proceeds); the 2026 addition, MFG-0007, was financed by a note, a noncash event. Of $576,245.19, $303,666.63 went to `1090`, not to an expense. **Watch for:** summing the register's cost without removing disposed assets: $4,732,000.00, $378,000.00 above the ledger.

### Part 2: Notes payable

**Step 3. State each note's terms, maturities and current portion.** The script's notes payable query joins DebtAgreement to FixedAsset and sums DebtScheduleLine's principal after each year-end, with the ledger's `2110` beside it as a check; a second query sums the principal due by year, and the first year is the current portion that Requirement 5 reclassified.

**Check:** note 1, $360,000.00 at 6.75%, finances MFG-0006; note 2, $280,000.00 at 6.4%, finances MFG-0007. Balances $154,181.62 and $235,123.06, $389,304.68 in all, equal to `2110`. Principal due: 2027 $147,503.76; 2028 $114,200.83; 2029 $59,133.22; 2030 $63,030.74; 2031 $5,436.13. Interest paid $28,946.47. **Watch for:** two slips. Summing scheduled payments instead of principal gives $430,805.53 over five years, $41,500.85 above the balance, and a current portion of $168,532.44, not $147,503.76. Calling a note secured by its asset claims what the records do not show.

### Part 3: Revenue

**Step 4. Disaggregate revenue on the adjusted basis.** Adjusted revenue is the ledger's revenue by account plus Requirement 4's cutoff items by year of delivery. The model's query builds the items in a CTE:

```sql
Cutoff AS (
    SELECT ItemGroup, DeliveryYear AS FiscalYear, LineTotal AS Amount
    FROM Late
    UNION ALL
    SELECT ItemGroup, PostingYear, -LineTotal
    FROM Late
    UNION ALL
    SELECT i.ItemGroup,
        CAST(strftime('%Y', s.DeliveryDate) AS INTEGER),
        ROUND(sl.QuantityShipped * sol.UnitPrice
            * (1 - sol.Discount), 2)
    FROM ShipmentLine AS sl
        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
        INNER JOIN SalesOrderLine AS sol
            ON sol.SalesOrderLineID = sl.SalesOrderLineID
        INNER JOIN Item AS i ON i.ItemID = sl.ItemID
        INNER JOIN SalesOrder AS so ON so.SalesOrderID = s.SalesOrderID
        INNER JOIN Customer AS c ON c.CustomerID = so.CustomerID
        LEFT JOIN SalesInvoiceLine AS sil
            ON sil.ShipmentLineID = sl.ShipmentLineID
    WHERE sil.SalesInvoiceLineID IS NULL
),
```

The workbook reads the adjusted trial balance by revenue account and, for the segments, adds the cutoff to the invoice lines by posting year:

```
=-SUMIFS(WorkingTB[Adjusted2026],WorkingTB[AccountNumber],4010)
```

**Check:** by product line, design services, freight and the five segments, the amounts of the instructor note below; at a point in time $28,785,418.73 and over time $1,213,344.00 in 2026. 2025's product revenue, $28,040,804.94, equals Exercise 14.2's revenue by ship date. **Watch for:** the ledger's revenue without the cutoff: $24,940.25 below the adjusted income statement in 2026 and $70,598.07 above it in 2025.

**Step 5. Show the contract balances and test the services.** Receivables are $4,755,337.09 and $4,843,285.43, each including the opening line that no document supports; no contract asset or liability is recorded; customer credits awaiting refund (`2060`) are $1,008.67 and $3,413.46, three Issued credit memos at the last year-end. The services query compares hours worked with hours billed, engagement by engagement.

**Check:** all 19,627.49 billable hours were billed, so the records show no recorded service work left unbilled. They cannot show that every hour worked was recorded. **Watch for:** reading engagement 209's planned hours less its billed hours as unbilled work: 17.05 hours that were never worked.

### Part 4: Accrued liabilities and inventories

**Step 6. Break each line into its components.** Accrued liabilities: payroll and related, commissions, accrued expenses after A3 and interest; inventories: finished goods as recorded (purchased goods at receipt cost, manufactured goods at standard), materials and packaging at purchase-order cost (price variances go to cost of goods sold) and work in process net of the `1090` credit. Each total must equal its balance sheet line.

**Check:** accrued liabilities $852,116.20, of which payroll $478,044.82; inventories $23,935,720.45, of which materials $11,751,653.92. **Watch for:** showing only the wages owed, $383,044.82. The total misses the balance sheet by the $95,000.00 opening line.

### Part 5: The text of the notes

**Step 7. Write the notes.** Five notes, each tied to a statement line.

| Note | It must say | Ties to |
|---|---|---|
| Property and equipment | Method and lives; additions, disposals, the noncash acquisition | The roll-forward |
| Notes payable | Terms, linked asset, maturities, current portion, interest paid | `2110` |
| Revenue | Timing and its assumption; disaggregation; contract balances; no recorded service work unbilled | The income statement |
| Accrued liabilities | Components, the opening line named | The balance sheet |
| Correction of 2025 | What changed; effect on opening equity and income; none on cash | The equity statement |

Notes still to be written (policies, inventories, Requirement 9's matters) go on the memo's list.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Cost at the three year-ends | $4,027,000.00; $4,284,000.00; $4,354,000.00 | 2 |
| Notes payable at the last year-end | $389,304.68 | 3 |
| Operating revenue as adjusted, 2026 | $28,785,418.73 at a point in time; $1,213,344.00 over time | 4 |
| Accrued liabilities; inventories, 2026 | $852,116.20; $23,935,720.45 | 6 |

> **Instructor notes, Requirement 7:** property and equipment, cost 4,027,000 at January 1, 2025; 2025 additions 425,000 (1120 360,000, WH-0005 and WH-0006; 1130 65,000, OFF-0005) and disposal of WH-0001 (cost 168,000, accumulated depreciation 98,000, proceeds 28,000, loss 42,000), 4,284,000; 2026 addition of MFG-0007, 280,000 by note (noncash), and disposal of MFG-0004 (cost 210,000, accumulated depreciation 117,500, no proceeds, loss 92,500), 4,354,000. Depreciation 2025 / 2026 by class: furniture and fixtures 52,500.00 / 52,500.00; warehouse 88,090.51 / 101,828.64; office 106,333.29 / 118,249.92; manufacturing 295,500.00 / 303,666.63; total 542,423.80 / 576,245.19 (to 6130 246,923.80 / 272,578.56, to 1090 295,500.00 / 303,666.63). Accumulated depreciation 1,359,087.47 -\> 1,803,511.27 -\> 2,262,256.46; net book value at 2026 by class 157,500.00 / 501,680.85 / 109,479.32 / 1,323,083.37. Straight line, lives of 48 to 120 months, no residual value, from the month after the asset is placed in service through the month before disposal; the register reproduces the ledger within monthly rounding. Notes: note 1, 360,000 at 6.75%, 48 payments of 8,578.95 from August 2024, linked to MFG-0006, 154,181.62 at 2026 (243,425.23 at 2025); note 2, 280,000 at 6.4%, 60 payments of 5,465.42 from February 2026, linked to MFG-0007, 235,123.06; total 389,304.68. Principal due 2027 147,503.76; 2028 114,200.83; 2029 59,133.22; 2030 63,030.74; 2031 5,436.13. The records link each note to the asset it financed; they do not show a security interest, so do not claim one. Revenue on the adjusted basis, 2026 / 2025: Furniture 17,420,791.79 / 17,418,046.62; Lighting 5,998,016.11 / 5,498,446.55; Textiles 3,279,920.95 / 3,177,119.95; Accessories 1,873,869.85 / 1,947,191.82; design services 1,213,344.00 / 1,261,365.95; freight 212,820.03 / 213,499.96. By segment, products and services: Wholesale 15,288,355.75 / 14,349,172.31; Strategic 9,008,553.51 / 9,245,320.80; Design Trade 3,035,208.44 / 3,251,824.91; Small Business 1,240,481.00 / 1,194,486.92; Design Services 1,213,344.00 / 1,261,365.95. Timing: at a point in time (goods and freight) 28,785,418.73 / 28,254,304.90; over time (services) 1,213,344.00 / 1,261,365.95, on the case's assumption, for the contracts to confirm, of an enforceable right to payment for the work completed to date. Cross-checks: 2025 product revenue, 28,040,804.94, equals Exercise 14.2's revenue by ship date; 2026's equals 28,528,117.59 plus the 44,481.11 never invoiced. An entity that is not a public business entity, as the case treats Charles River, may limit the disaggregation to the timing of transfer with qualitative information; the controller and the lender still ask for product lines. Contract balances: receivables 5,080,182.83 (January 1, 2025, adjusted) / 4,755,337.09 / 4,843,285.43, each including the unsupported 380,000.00 and, from the cutoff adjustment, deliveries not yet invoiced, shown as receivables on the case's assumption that payment then depends only on time; no contract asset or contract liability is recorded (2070 unused) and the records show no unbilled service hours, which the contracts would confirm; customer credits awaiting refund in 2060 3,105.75 / 1,008.67 / 3,413.46, at 2026 three Issued credit memos. Services: every billable hour in ServiceTimeEntry (19,627.49) is billed, December's work was billed on December 31, and engagement 209 (In Progress, ended 2026-10-31) billed all 125.64 hours worked through October 23; its 142.69 planned hours were never all recorded, so the records show no recorded work left unbilled, though they cannot show that every hour worked was recorded. Inventories 2026 / 2025: finished goods as recorded (purchased goods at receipt cost, manufactured goods at standard, an opening balance without item detail) 12,169,701.74 / 10,829,820.22; materials and packaging at purchase-order cost (price variance to cost of goods sold) 11,751,653.92 / 4,334,722.56; work in process net of the 1090 credit 14,364.79 / 14,290.16; total 23,935,720.45 / 15,178,832.94. Accrued liabilities 2026 / 2025: payroll and related, with the opening 95,000.00, 478,044.82 / 460,921.19; commissions (2034) 48,858.55 / 48,071.71; accrued expenses 323,205.57 / 300,939.13; interest 2,007.26 / 1,369.27; total 852,116.20 / 811,301.30.

## What a strong answer says

- **Property and equipment and notes.** Method, lives, both disposals, the noncash acquisition; the asset each note financed, with no security interest claimed.
- **Revenue.** The adjusted basis, with the assumptions stated that control of the goods passes on delivery and that the service contracts support recognition over time.
- **Accrued liabilities and the correction.** The opening line named; no effect on cash.

A weak answer lists balances without reconciling them to the statements.

## Common mistakes and how to respond

- **Disposal month counted.** *Symptom:* register $2,500.00 above the ledger. *Response:* ask the month the asset left.
- **All assets' cost.** *Symptom:* cost $378,000.00 high. *Response:* ask which assets the company still owns.
- **Payments as principal.** *Symptom:* maturities $41,500.85 above the balance. *Response:* ask what the payment includes.
- **Ledger revenue.** *Symptom:* $24,940.25 short of the income statement. *Response:* ask which year the delivery belongs to.
- **Planned hours.** *Symptom:* 17.05 hours unbilled. *Response:* ask what the time records show.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Property and equipment | 25 | Roll-forward by class, register reconciled, disposals and method | Balances without reconciliation |
| Notes payable | 15 | Terms, asset, maturities, current portion, interest | Balance only |
| Revenue and contract balances | 25 | Three disaggregations on the adjusted basis, contract balances, services test | Ledger basis |
| Accrued liabilities and inventories | 15 | Components equal the lines | Totals only |
| Text of the notes | 20 | Five notes, accurate, tied to the statements | Missing the correction note |

## Extensions and discussion questions

- Produce the revenue disaggregation from Chapter 14's sales model and reconcile it to the ledger and the cutoff.
- Disclose the interest the next five years will cost.
- Discuss: why claim no security interest when the records link each note to an asset?
