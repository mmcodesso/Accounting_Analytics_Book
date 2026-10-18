# Requirement 4: Test cutoff at each year-end (Chapters 6 and 12)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 4 |
| Perspective | Auditing |
| Tools | More than one tool |
| Time | About 150 minutes |
| Solution file | Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 4 (tests L5 to L8 rerun, the revenue accounts, the payroll owed and the interest); Chapter17-capstone-excel.zip: worksheet Cutoff, with the proration in formulas, and the pasted results on SQL Results |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A cutoff error is where the ledger and its documents disagree at a boundary, and it reverses in the next year, which is why the case asks for every year-end it presents and the one before. Queries find the populations. Prorating a pay period or an interest payment is a formula a reviewer should see, so it goes in the workbook. The analytics type is diagnostic, with a small predictive step: the last year-end's payroll is an estimate.

Students can:

- find the invoices posted in another year than the delivery they bill, and the shipments never invoiced (Part 1);
- measure the payroll owed at each year-end by one working-day method, split between manufacturing and the rest (Part 2);
- accrue the interest each note owes, stating the day count (Part 3).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures, analytical procedures, and audit data analytics); IMA Reporting and Control (financial recordkeeping); IFAC IES 2 (a) and 2 (f); AACSB A5 part 5.1 (technology integration: SQL and Excel).

## Before you assign

- **Files.** `LenderPackage.sql` and the workbook. Chapter 12's Audit.sql holds the tests L5 to L8 that students rerun.
- **Data conditions.** Shipments are delivered in the year they ship; SalesInvoiceLine.ShipmentLineID links an invoice line to its shipment; the last pay periods of the last year are Open and have no PayrollRegister rows; every work center has the same working days in WorkCenterCalendar; `2080` has never been used.
- **Verify first.** The unbilled-lines query returns 9 rows, and the pay-period query returns 6.

## How to run it

Pairs, about 150 minutes: 40 for revenue, 60 for payroll, 25 for interest, 25 for the entries' effects. The routine for every query: type it at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the one-method rule until students meet the last year-end's missing registers. **Collect** the queries and the Cutoff worksheet.

![A mock of the payroll block of the Cutoff worksheet, where the proration is visible to a reviewer.](../figures/chapter-17-statements-for-a-lender/IF-17-4-A.pdf)

## Step-by-step solution

### Part 1: Revenue by delivery

**Step 1. Find the invoices posted in another year than their delivery.** Two CTEs carry the test: the latest delivery date of each invoice's shipments, and the first posting date of each invoice. The main SELECT joins them to the invoice and keeps the rows where the two years differ. SQL fits: the population is exact, and it reruns for any year-end.

```sql
WITH Shipped AS (
    SELECT sil.SalesInvoiceID, MAX(s.DeliveryDate) AS DeliveryDate
    FROM SalesInvoiceLine AS sil
        INNER JOIN ShipmentLine AS sl
            ON sl.ShipmentLineID = sil.ShipmentLineID
        INNER JOIN Shipment AS s ON s.ShipmentID = sl.ShipmentID
    GROUP BY sil.SalesInvoiceID
),
Posted AS (
    SELECT SourceDocumentID AS SalesInvoiceID,
        MIN(PostingDate) AS PostingDate
    FROM GLEntry
    WHERE SourceDocumentType = 'SalesInvoice'
    GROUP BY SourceDocumentID
)
```

The block holds the query's two CTEs only, a fragment. The complete query, with its main SELECT, is in LenderPackage.sql under the heading `Requirement 4: test L5, invoices posted in another year than the latest delivery they bill (LateInvoices)`.

**Check:** 15 invoices for 2024 deliveries ($90,138.93), 8 for 2025 ($19,540.86) and 0 for 2026; sales tax of $5,859.04 and $1,270.17 on them is not adjusted. **Watch for:** dating the test by the invoice date. It finds 10 invoices ($16,956.73) for 2025 and 2 ($1,349.19) for 2026: the lists mix invoices dated before their shipment, which the ledger posted in the right year, with real errors, and miss the invoice dated in the year of delivery and posted in the next.

**Step 2. Find the shipments never invoiced.** A shipment line with no invoice line, valued at its order price less discount.

```sql
-- Requirement 4: test L6, shipment lines never invoiced, at order price less discount (UnbilledLines)
-- Population: every shipment line; expected: 9 lines shipped in December 2026, 44,481.11 at order price, standard cost 22,895.78
SELECT sl.ShipmentLineID, s.ShipmentNumber, s.ShipmentDate,
    s.DeliveryDate, i.ItemCode, i.ItemGroup, c.CustomerSegment,
    sl.QuantityShipped, sol.UnitPrice, sol.Discount,
    sl.ExtendedStandardCost,
    ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2)
        AS Value
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
ORDER BY sl.ShipmentLineID;
```

**Check:** 9 lines, $44,481.11, all shipped in December 2026; their standard cost, $22,895.78, is already in cost of goods sold. **Watch for:** two errors. Testing only invoices finds nothing at the last year-end and turns its revenue effect to -$19,540.86, against +$24,940.25. Valuing the lines at standard cost records a cost as revenue.

**Step 3. Put the totals on the Cutoff worksheet by item group.** Paste the L5 and L6 results, and total by year, customer segment and item group. The account each group is credited to comes from the ledger's invoice postings.

**Check:** revenue that belongs to the year, $90,138.93, $19,540.86 and $44,481.11.

### Part 2: Payroll

**Step 4. Find the pay periods that cross each year-end and test account `2030`.** Test L7 lists the periods whose start and pay date fall in different years: 6 rows, four with registers and two with none. Test L8 sums `2030` by source document: the opening line alone, the payroll postings netting to zero, so no year-end has accrued wages.

**Step 5. Measure the earlier year-ends from the registers.** The period paid in the next year in full, plus the share of the crossing period that falls in the year, by working days from WorkCenterCalendar. The model's formulas give the working days within the year, the share, and the total. They read the Tables the workbook loads (WorkingDays, PayrollCost, PayrollPeriods), the year-end names such as `YE_2024`, and the cells of the payroll block that the figure shows, so build that block first (**Formulas > Name Manager** lists the names):

```
=COUNTIFS(WorkingDays[CalendarDate],">="&B34,WorkingDays[CalendarDate],"<="&YE_2024,WorkingDays[IsWorkingDay],1)
=B37/B36
=ROUND(SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],B31)+SUMIFS(PayrollCost[Cost],PayrollCost[PayrollPeriodID],B33)*B38,2)
```

**Check:** 2024: $242,165.92 plus 2 of 9 working days of the next period, $60,402.98, is $302,568.90. 2025: $263,426.72 plus 3 of 9, $102,494.47, is $365,921.19. **Watch for:** prorating by calendar days. The crossing period then counts a fraction of two weeks, and the totals read $280,996.41 and $329,316.02, short by $21,572.49 and $36,605.17.

**Step 6. Estimate the last year-end from the processed periods.** The last two periods have no registers, so multiply the cost per working day of the last eight processed periods by the working days left. The model's formulas list the periods, count their working days, count the days left, and accrue:

```
=TAKE(SORTBY(FILTER(PayrollPeriods[PayrollPeriodID],PayrollPeriods[Status]="Processed"),FILTER(PayrollPeriods[PeriodEndDate],PayrollPeriods[Status]="Processed"),1),-8)
=COUNTIFS(WorkingDays[CalendarDate],">="&MIN(XLOOKUP(F31#,PayrollPeriods[PayrollPeriodID],PayrollPeriods[PeriodStartDate])),WorkingDays[CalendarDate],"<="&MAX(XLOOKUP(F31#,PayrollPeriods[PayrollPeriodID],PayrollPeriods[PeriodEndDate])),WorkingDays[IsWorkingDay],1)
=COUNTIFS(WorkingDays[CalendarDate],">="&MAX(XLOOKUP(F31#,PayrollPeriods[PayrollPeriodID],PayrollPeriods[PeriodEndDate]))+1,WorkingDays[CalendarDate],"<="&YE_2026,WorkingDays[IsWorkingDay],1)
=ROUND(D44/D43*D46,2)
```

**Check:** 78 working days, $2,298,268.90, $29,464.99 a day, 13 days left: $383,044.82, of which gross pay $336,456.34, employer taxes $25,738.93 and benefits $20,849.55. Manufacturing, $197,970.68, would have gone to `1090`. Under the case's standard-cost close it ends in `5080` and cost of goods sold, because standard cost leaves `1090` only through completions. An answer that traces the December work to its work orders and assigns part of it to work in process or finished goods is acceptable. The rest goes to the cost centers' salary accounts and `6060`. **Watch for:** two errors. An accrual from the registers alone is zero, and the last year's effect becomes +$365,921.19, the reversal of the year before with nothing new. One period's cost per day gives $416,471.68, $33,426.86 too high.

### Part 3: Interest

**Step 7. Accrue each note's interest from its schedule.** Each payment's interest covers the days since the one before it, so the year-end owes the next payment's interest for the days to the year-end, counted inclusive. State the convention.

```
=IF(C77,ROUND(H77*MIN(G77,F77)/F77,2),0)
```

**Check:** $1,838.58, $1,369.27 and $2,007.26; at the last year-end the second note's payment of 2027-01-04 covers 33 days and 30 are owed. Leaving out the day of the previous payment gives $1,969.26; either is acceptable if stated. **Watch for:** accruing the whole next payment, $2,121.26.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Invoices posted late; their subtotal, 2024, 2025 | 15, 8; $90,138.93, $19,540.86 | 1 |
| Lines never invoiced; at order price less discount | 9; $44,481.11 | 2 |
| Payroll owed, 2024, 2025, 2026 | $302,568.90; $365,921.19; $383,044.82 | 5, 6 |
| Interest accrued, 2024, 2025, 2026 | $1,838.58; $1,369.27; $2,007.26 | 7 |

> **Instructor notes, Requirement 4:** revenue, by the latest DeliveryDate of each invoice's shipments against the year of its posting (SubTotal; these invoices carry no freight): 15 invoices for 2024 deliveries posted in 2025, 90,138.93 (Strategic 35,325.32, Wholesale 54,813.61; Furniture 76,792.75, Lighting 4,836.07, Textiles 8,510.11; tax 5,859.04); 8 for 2025 deliveries posted in 2026, 19,540.86 (Strategic 13,241.85, Wholesale 6,299.01; Furniture 12,288.72, Lighting 3,065.83, Textiles 1,784.83, Accessories 2,401.48; tax 1,270.17; includes SI-2026-013742, dated in 2025); 9 shipment lines of December 2026 never invoiced, 44,481.11 at order price (Quantity shipped x UnitPrice x (1 - Discount); Strategic 20,022.95, Wholesale 24,458.16; Furniture 34,792.95, Lighting 2,432.78, Textiles 3,494.67, Accessories 3,760.71), whose standard cost (22,895.78) is already in cost of goods sold. Sales tax is recorded on invoicing and is not adjusted; the tax on the unbilled lines is not known. Payroll (PayrollRegister gross pay plus employer taxes and benefits; working days identical in every work center): end of 2024, period 26 (2024-12-16 to 12-29, paid 2025-01-03) in full, 242,165.92, plus 2 of the 9 working days of period 27, 60,402.98: 302,568.90 (gross 265,750.45, employer taxes 20,329.93, benefits 16,488.52; manufacturing 132,849.90, other 169,719.00). End of 2025: period 52 in full, 263,426.72, plus 3/9 of period 53, 102,494.47: 365,921.19 (gross 321,409.38, taxes 24,587.79, benefits 19,924.02; manufacturing 180,675.14, other 185,246.05). End of 2026: periods 70-77 cost 2,298,268.90 over 78 working days, 29,464.99 a day, times 13 working days: 383,044.82 (gross 336,456.34, taxes 25,738.93, benefits 20,849.55; manufacturing 197,970.68, other 185,074.14). The manufacturing part goes to 1090, and the model answer ends it in 5080 and cost of goods sold, following the case's standard-cost close: standard cost leaves 1090 only through completions, and the rest clears to 5080 when the work orders close. Assigning part of it to work in process or finished goods would need the production of those days traced to their work orders and a review of how 1090's variances are allocated, so a reasoned allocation to inventory with that trace is acceptable. The rest goes to the cost centers' salary accounts and 6060. Exercise 12.1 allocated hourly labor by the hours worked and got about 296,000 (2024) and 335,000 (2025); either method is acceptable if it is applied at every year-end and the 2026 estimate uses the same one. Interest (2080 has never been used; each payment's interest covers the month before it): end of 2024, note 1's payment of 2025-01-01, 1,838.58; end of 2025, note 1's payment of 2026-01-01, 1,369.27; end of 2026, note 1's payment of 2027-01-01, 867.27 plus 30 of the 33 days of note 2's 1,253.99 (2026-12-02 to 2027-01-04), 1,139.99, total 2,007.26 (29 days gives 1,969.26; accept either with the convention stated).

## What a strong answer says

- **Revenue.** Recognized in the year of delivery; the invoices and the unbilled lines both found; the entry at each year-end.
- **Payroll.** One working-day method at every year-end, manufacturing separated and explained, the last year's estimate stated as an estimate.
- **Interest.** The convention named; either day count is accepted when it is stated.

A weak answer finds the invoices and forgets the unbilled lines, or uses one method for one year and another for the next.

## Common mistakes and how to respond

- **Dating by invoice.** *Symptom:* 2 invoices for 2026. *Response:* ask which date the ledger used to post them.
- **Invoices only.** *Symptom:* no adjustment at the last year-end. *Response:* ask what a shipment with no invoice line is.
- **Calendar days.** *Symptom:* payroll $36,605.17 short. *Response:* ask how many days of the period people worked.
- **Registers only.** *Symptom:* a payroll accrual of zero. *Response:* ask why the last periods have no registers.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Revenue populations | 25 | Both tests, each year-end, valued at order price less discount | Invoices only |
| Payroll method | 30 | One working-day method; last year-end estimated; split | Method changes between years |
| Interest | 15 | Convention stated; each note | No convention |
| Entries and accounts | 20 | Each cutoff item with accounts and the year's effect | Totals without accounts |
| Evidence | 10 | Queries and formulas traceable | Totals typed |

## Extensions and discussion questions

- Recompute the last year-end's payroll with the last four processed periods and say how far the estimate moves.
- Allocate the payroll by the hours worked, as Exercise 12.1 did, and compare it with the working-day estimate.
- Discuss: why is revenue by delivery date an assumption, and what contract term would change it?
- Discuss: an error missed at one year-end reverses in the next year. What does that do to a trend in income?
