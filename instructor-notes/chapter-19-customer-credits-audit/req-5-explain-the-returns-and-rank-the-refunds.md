# Requirement 5: Explain the returns and rank the refunds (Chapters 13 to 15)

| | |
|---|---|
| Unit | Chapter 19: Auditing the Customer Credits Cycle |
| Item | Requirement 5 |
| Perspective | Auditing |
| Tools | Power BI Desktop |
| Time | About 180 minutes |
| Solution file | Chapter19-capstone-pbi.zip: Credits Analytics/Credits Analytics.pbip (pages About, Returns, Timing, Concentration, Refund Ranking, Refund Detail, Validation and Notes; the Tests and Checks tabs in DAX query view) and RefundFlags.csv, the export of test T10 of Credits.sql |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The committee will want to see where returns grow, which refunds deserve a second look, and the documents behind each. That is a report, not a workbook: a model with explicit relationships, a Date table that the facts read by their own dates and, through inactive relationships, by the shipment date (Chapter 14), measures that switch, a drill-through page (Chapter 15), and a Validation page and Tests tab that tie it out. The query of Requirement 4 decides which refunds are flagged; the report lets the committee see and drill into the decision. The analytics type is descriptive and diagnostic.

Students can load the cycle's tables and the flags and relate the facts to Date (Part 1), write rate and score measures (Part 2), and build the pages, the drill-through and the tie-out (Part 3).

**Competencies practiced.** CPA Evolution Core S1 M8 (data mining and analysis of financial data; visualization and communicating results); IMA Data Analytics and Insights (data analysis, data visualization); IFAC IES 2 (f) and (i); AACSB A5 part 5.1 (Power BI).

## Before you assign

- **Files.** Power BI Desktop (Windows only), CharlesRiver.xlsx and RefundFlags.csv from Requirement 4. The solution reads both from `C:\CharlesRiver\`; students point the queries at their copies with **Change Source**.
- **Data conditions.** 439 invoice lines (the design services) have no shipment, so revenue by ship date leaves them out. Returns come 7 to 74 days after shipment. The data stop a few days before the last year-end, and the first year had no earlier sales to return.
- **Verify first.** In DAX query view, run the Checks tab: 181 rows of Requirement 5, 27 of the flags and 7 of Milestone 2 all agree.

## How to run it

Pairs, about 180 minutes: 40 for the model, 30 for the measures, 70 for the pages and the drill-through, 25 for Validation and Tests, 15 for About. Hold back USERELATIONSHIP until the Timing page looks wrong, and the drill-through until the ranking exists. **Collect** the .pbix and a screenshot of the Tests tab.

## Step-by-step solution

### Part 1: The model

**Step 1. Load the tables.** Choose **Home > Get data > Excel workbook** and load the credit lines and credits, the refunds, the invoice lines, the receipt applications, Item and Customer, GLEntry and Account; choose **Home > Get data** again for the CSV. The shipment, warehouse, return, invoice, receipt and employee queries only feed merges, so clear **Enable load**. The credit lines take their credit, return and shipment by merges:

```
    #"Merged Queries" = Table.NestedJoin(#"Removed Other Columns", {"CreditMemoID"}, CreditMemo, {"CreditMemoID"}, "CreditMemo", JoinKind.LeftOuter)
    #"Added Custom" = Table.AddColumn(#"Expanded ShipmentLine", "DaysAfterShipment", each Duration.Days([ReturnDate] - [ShipmentDate]))
    #"Merged Queries2" = Table.NestedJoin(#"Expanded SalesReturnLine", {"ShipmentLineID"}, ShipmentLine, {"ShipmentLineID"}, "ShipmentLine", JoinKind.LeftOuter)
    #"Expanded ShipmentLine" = Table.ExpandTableColumn(#"Merged Queries2", "ShipmentLine", {"ShipmentNumber", "ShipmentDate", "Carrier", "DeliveryDate", "Warehouse"}, {"ShipmentNumber", "ShipmentDate", "Carrier", "DeliveryDate", "Warehouse"})
```

GLEntry is filtered first, so only the three posting types the Tests tab needs are loaded:

```
    #"Filtered Rows" = Table.SelectRows(#"Changed Type", each [SourceDocumentType] = "CreditMemo" or [SourceDocumentType] = "CustomerRefund" or [SourceDocumentType] = "SalesInvoice")
```

**Check:** 637 credit lines, 612 credits, 222 refunds, 27,933 invoice lines and 76,875 ledger rows. **Watch for:** the CSV merged into a workbook query, which combines two data sources and risks a privacy-level error; relate it instead.

**Step 2. Relate the tables.** In **Model view**, relate the 5 dated fact tables (CreditMemoLine, CreditMemo, SalesInvoiceLine, CustomerRefund, GLEntry) to Date by their own dates, and add inactive ShipmentDate relationships only for CreditMemoLine and SalesInvoiceLine (**Make this relationship active** cleared); every relationship is many to one in a single direction. Relate the facts to Item and Customer, the refunds to RefundFlags on RefundNumber, and GLEntry to Account. The receipt applications stay unrelated and are read by TREATAS in Step 7. **Check:** the Date table carries the active and inactive relationships above.

### Part 2: The measures

**Step 3. Write the rate measures.** The rate by the month of the credit divides each fact by its own date; by the month of the shipment both sides switch to the shipment date.

```
Credits = SUM ( CreditMemoLine[LineTotal] )

Revenue = SUM ( SalesInvoiceLine[LineTotal] )

Return Rate = DIVIDE ( [Credits], [Revenue] )

Credits by Ship Date = CALCULATE ( [Credits], USERELATIONSHIP ( CreditMemoLine[ShipmentDate], 'Date'[Date] ) )

Revenue by Ship Date =
CALCULATE (
    [Revenue],
    USERELATIONSHIP ( SalesInvoiceLine[ShipmentDate], 'Date'[Date] ),
    NOT ISBLANK ( SalesInvoiceLine[ShipmentDate] )
)

Return Rate by Ship Date = DIVIDE ( [Credits by Ship Date], [Revenue by Ship Date] )
```

**Check:** by year of the credit the rates are 0.533%, 0.685% and 0.816%; by year of the shipment 0.606%, 0.726% and 0.794%. **Watch for:**

- The overall rate by ship date reads 0.711% against 0.682% by credit date: the lines that never ship are out of its revenue, on purpose.
- Credits taken from the credit memo total, not the lines: it exceeds the lines by $42,721.62 (freight and tax), and the Tests tab shows a difference. Counting lines as credits gives 637 for 612.

**Step 4. Score the refunds.** Enter the five flag names with **Home > Enter data** (the Flags table, disconnected, sorted by an Order column); add the score as a calculated column over the related flags, and switch the flag measures on the selected name.

```
Score = RELATED ( RefundFlags[AboveLimit] ) + RELATED ( RefundFlags[CreditAboveLimit] ) + RELATED ( RefundFlags[MethodMismatch] ) + RELATED ( RefundFlags[BeforePayment] ) + RELATED ( RefundFlags[PastDueAtLeastRefund] )

Flagged Refunds =
SWITCH (
    SELECTEDVALUE ( Flags[Flag] ),
    "Refund above authority", CALCULATE ( [Refunds], RefundFlags[AboveLimit] = 1 ),
    "Credit above authority", CALCULATE ( [Refunds], RefundFlags[CreditAboveLimit] = 1 ),
    "Method mismatch", CALCULATE ( [Refunds], RefundFlags[MethodMismatch] = 1 ),
    "Before the last application", CALCULATE ( [Refunds], RefundFlags[BeforePayment] = 1 ),
    "Past due at least the refund", CALCULATE ( [Refunds], RefundFlags[PastDueAtLeastRefund] = 1 )
)

High-Score Refunds = CALCULATE ( [Refunds], CustomerRefund[Score] >= 4 )
```

**Check:** scores 0 to 5 count 4, 18, 53, 83, 44, 20 refunds; 64 score 4 or 5 ($80,776.86). **Watch for:** a past-due flag on any balance instead of one at least the refund: 66 refunds score 4 or 5.

### Part 3: The pages

**Step 5. Build Returns and Timing.** Returns shows credits and the rate by year, item group, reason, segment and the largest group's families: Furniture grows from $73,312.97 to $161,086.15 (0.468% to 0.926% of its revenue), damaged returns from $22,547.39 to $73,617.40. On Timing, the line chart "Return rate by month of the credit and by month of the shipment" puts both rates by YearMonth.

![A mock of the Timing page, the page that shows why the last months and the first year mislead.](../figures/chapter-19-customer-credits-audit/IF-19-5-A.pdf)

**Check:** the last month by shipment month reads 0.05% against 0.51% to 1.35% for the other months of that year; the first month by credit month reads 0.04%. **Watch for:** reading either as good news. The first year had nothing earlier to return, and the last shipments' returns arrive after the data end. Compare cohorts with equal follow-up under a stated rule: the last return is dated 2026-12-24 and the longest lag is 74 days, so shipments after 2026-10-11 (7.1% of shipped revenue, the months from 2026-10 on) are immature and disclosed as excluded. Omitting December alone, or an unspecified month or two, does not establish maturity, and past lags do not prove that no later return can arrive.

**Step 6. Build Concentration.** Credit lines by carrier and reason, by warehouse, and a customer table "Customers by credits as a share of their sales (all three years)" sorted by return rate with a visual filter on credits above zero. **Check:** customer 128 (Strategic, Net 45) has $38,912.92 of credits on sales of $1,077,502.22, 3.61% against 0.682% for all customers; it is first by dollars and number 4 by rate, with customers 178, 35 and 73 above it, two on sales under a tenth of its. Carrier and warehouse counts compare only when volumes match; as shares of shipped revenue the carriers run 0.64% to 0.78%.

**Step 7. Build Refund Ranking and the drill-through.** The ranking page holds the score chart, the flags by year, the approvers and the table "Every refund, by score (right-click a refund: Drill through > Refund Detail)". On Refund Detail, drop RefundNumber in the **Drillthrough filters** well of the Visualizations pane; a reviewer right-clicks a refund and chooses **Drillthrough** and the page, and sees the refund, its flags, its credit, its invoice and the receipts applied to it, read without a relationship:

```
Applied to the Invoice =
CALCULATE (
    SUM ( CashReceiptApplication[AppliedAmount] ),
    TREATAS ( VALUES ( CustomerRefund[OriginalSalesInvoiceID] ), CashReceiptApplication[SalesInvoiceID] )
)
```

![A mock of the Refund Ranking page a reviewer starts from.](../figures/chapter-19-customer-credits-audit/IF-19-5-B.pdf)

**Check:** the largest refund, RF-2025-000097, scores 4, so it is not at the top of the list although it is the largest.

**Step 8. Add Validation and Tests.** Validation shows credits less `4060` and refunds against `1010` by year, and the cards that compare the score, date and amount with the export. The Tests tab holds 3 tests; this instructor check repeats the core of the third:

```
EVALUATE
ROW (
    "Refunds flagged", [Refunds Flagged],
    "Scores different", [Scores Different],
    "Exports different", [Exports Different]
)
```

**Check:** 222, zero and zero. The Checks tab tests the values and the tie to the export; the layout, the drill-through menu and the slicer state show only in Desktop.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Credit lines; credits; refunds | 637; 612; 222 | 1 |
| Rate by year of the credit | 0.533%; 0.685%; 0.816% | 3 |
| Refunds scoring 4 or 5; their amount | 64; $80,776.86 | 4 |
| Customer 128: credits; rate | $38,912.92; 3.61% | 6 |
| Checks that agree | 181; 27; 7 | 8 |

> **Instructor notes, Requirement 5:** credits by group 2024 / 2025 / 2026: Furniture 73,312.97 / 129,872.44 / 161,086.15 (0.468% / 0.743% / 0.926% of 4010); Lighting 33,062.08 / 32,578.56 / 48,813.77; Textiles 26,889.07 / 24,090.73 / 22,396.32; Accessories 12,391.23 / 14,562.65 / 10,468.32. Damaged 22,547.39 / 47,008.01 / 73,617.40 (Furniture Damaged 5,273.25 / 31,696.30 / 50,172.01). Furniture families 2026: TBL 36,350.42, DSK 31,186.47, SDB 22,766.37, CTB 20,790.93, NGT 19,797.66. Wholesale 82,477.55 / 90,614.46 / 148,224.44. Damaged lines spread evenly by carrier (25-33 each) and returned lines by warehouse (326 / 311), counts that compare rates only when volumes match; as a share of the revenue each shipped, carriers return 0.64%-0.78% and the warehouses 0.67% / 0.75%, so none stands out, before any adjustment for product mix. Returns come 7-74 days after shipment (mean 28.3; 3-72 after delivery). By shipment year 0.606% / 0.726% / 0.794%; December 2026 shipments 0.05% (immature, with less follow-up in the extract than the longest lag seen), other 2026 months 0.51-1.35%, though the months from 2026-10 on all hold shipments with less than 74 days of follow-up. A comparison of equal follow-up states its rule: the last return is dated 2026-12-24 and the longest lag observed is 74 days, so it includes shipments dated by 2026-10-11 and excludes, and discloses, the later ones (7.1% of shipped revenue); historical lags inform the window and do not prove that no later return can arrive, and the history before 2024 is missing; 27 return lines (30,304.99) fall in a later year than their shipment; 2024 has no 2023 carry-in. Credits on sales 0.682% overall; customer 128 (Strategic, Net 45) 3.61% (38,912.92 on 1,077,502.22), 16 credits (41,442.26; 13 approved by two representatives), 6 refunds (26,315.10), all dated before the last application of the customer's payments, 5 before any receipt; customers 178 (4.86% on sales of 76,595), 35 (4.15% on sales of 32,539), and 73 (3.70% on sales of 491,464) rank higher, two of them on sales under a tenth of 128's. Refund approvers by year: Accounting Manager 12 / 23 / 24, Administrative Specialists 23 / 38 / 23, Staff Accountants 20 / 23 / 36. Score from five flags (refund above authority, credit above authority, method mismatch, before payment, past due at least the refund), a triage count and not a probability of fraud or loss, so equal scores are ranked on the amounts and the evidence: 0-5 = 4, 18, 53, 83, 44, 20; 64 refunds score 4 or 5 (80,776.86); RF-2025-000097 scores 4 (its approver was within limit). Weekend dates are spread evenly (62 refunds, 179 credits) and are not a useful flag here.

## What a strong answer says

- **Each fact is read by its own date, the credit and invoice lines also by the shipment date,** and the report says which basis each rate uses.
- **Timing is allowed for:** the last months and the first year are explained, not presented as trends.
- **Concentration is a share of each customer's sales,** and the customer to follow up is found by both dollars and rate.
- **The ranking is traceable:** a reviewer drills from the score to the refund, its credit and its invoice, and Validation ties the report to the ledger and the export.

A weak answer shows counts without rates, ranks customers by dollars, or leaves the report with no tie-out.

## Common mistakes and how to respond

- **Revenue by ship date with the unshipped lines.** *Symptom:* a rate that differs from the overall card. *Response:* ask which lines have no shipment.
- **The last month as good news.** *Symptom:* a rate of 0.05%. *Response:* ask when those returns will arrive.
- **The first year's first months.** *Symptom:* 0.04%. *Response:* ask how many earlier sales it had.
- **Customers ranked by dollars.** *Symptom:* customer 128 alone. *Response:* ask the rate on its sales.
- **Credit memo total on the Tests tab.** *Symptom:* a difference of $42,721.62. *Response:* ask what the total adds to the lines.
- **Lines counted as credits.** *Symptom:* 637 for 612. *Response:* ask what one credit is.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Model and relationships | 25 | All tables and flags, the dated facts related to Date by their own dates and two also by ShipmentDate (inactive), the CSV related not merged | Relationships without the shipment dates |
| Measures | 25 | Rates by both dates, the score and the flag measures | One basis only |
| Pages and drill-through | 30 | Returns, Timing, Concentration, Ranking and a working drill-through | Pages without the timing explanation |
| Validation and Tests | 20 | Ties to the ledger and the export | Validation without a test |

## Extensions and discussion questions

- Add a by-ship-month table of the last year under an explicit cutoff rule (shipments dated by the cutoff, the later ones disclosed as excluded), and say what it shows.
- Discuss: should the committee see the score or the five flags?
- Discuss: which page would you open the meeting with, and what would you say it cannot show?
