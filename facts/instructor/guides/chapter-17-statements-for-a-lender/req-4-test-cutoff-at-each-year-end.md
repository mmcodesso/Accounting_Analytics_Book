---
note: ch17.r4
uses: [ch17.g4]
title: Test cutoff at each year-end (Chapters 6 and 12)
kind: requirement
number: '4'
unit: '17'
perspective: auditing
tool: mixed
minutes: 150
solution: "Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 4 (tests L5 to L8 rerun, the revenue accounts, the payroll owed and the interest); Chapter17-capstone-excel.zip: worksheet Cutoff, with the proration in formulas, and the pasted results on SQL Results"
figures:
  - id: IF-17-4-A
    kind: excel-mock
    purpose: The payroll block of the Cutoff worksheet, where the proration is visible to a reviewer.
    shows: "The Cutoff worksheet scrolled to its payroll block, with one column for each year-end. Rows give the pay period paid in the next year, the period that crosses the year-end with its working days and its working days within the year, the share within the year, the cost from the registers, and the payroll owed with its gross pay, employer taxes, benefits, manufacturing and other parts. The last year-end column shows the eight processed periods, their cost per working day and the working days left."
    data: The payroll owed at each year-end and its parts (the Expected results).
---
{% set g = ch17_g4 %}
# Requirement 4: Test cutoff at each year-end (Chapters 6 and 12)

{{ header() }}

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
- **Verify first.** The unbilled-lines query returns {{ cc.n_lines }} rows, and the pay-period query returns {{ g.l7 }}.

## How to run it

Pairs, about 150 minutes: 40 for revenue, 60 for payroll, 25 for interest, 25 for the entries' effects. The routine for every query: type it at the end of the script, select it, choose **Execute all/selected SQL**, read the message pane. Hold back the one-method rule until students meet the last year-end's missing registers. **Collect** the queries and the Cutoff worksheet.

{{ figure('IF-17-4-A') }}

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

The block holds the query's two CTEs only, a fragment. The complete query, with its main SELECT, is in LenderPackage.sql under the heading `{{ g.h.l5 }}`.

**Check:** {{ cf.n }} invoices for {{ d.F }} deliveries (${{ cf.total|money }}), {{ cp.n }} for {{ d.P }} (${{ cp.total|money }}) and {{ cc.n }} for {{ d.C }}; sales tax of ${{ cf.tax|money }} and ${{ cp.tax|money }} on them is not adjusted. **Watch for:** dating the test by the invoice date. It finds {{ g.n_date[d.P] }} invoices (${{ g.s_date[d.P]|money }}) for {{ d.P }} and {{ g.n_date[d.C] }} (${{ g.s_date[d.C]|money }}) for {{ d.C }}: the lists mix invoices dated before their shipment, which the ledger posted in the right year, with real errors, and miss the invoice dated in the year of delivery and posted in the next.

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

**Check:** {{ cc.n_lines }} lines, ${{ cc.total|money }}, all shipped in December {{ d.C }}; their standard cost, ${{ cc.std|money }}, is already in cost of goods sold. **Watch for:** two errors. Testing only invoices finds nothing at the last year-end and turns its revenue effect to -${{ (g.no_unbilled|abs)|money }}, against +${{ g.a2.C|money }}. Valuing the lines at standard cost records a cost as revenue.

**Step 3. Put the totals on the Cutoff worksheet by item group.** Paste the L5 and L6 results, and total by year, customer segment and item group. The account each group is credited to comes from the ledger's invoice postings.

**Check:** revenue that belongs to the year, ${{ cf.total|money }}, ${{ cp.total|money }} and ${{ cc.total|money }}.

### Part 2: Payroll

**Step 4. Find the pay periods that cross each year-end and test account `2030`.** Test L7 lists the periods whose start and pay date fall in different years: {{ g.l7 }} rows, four with registers and two with none. Test L8 sums `2030` by source document: the opening line alone, the payroll postings netting to zero, so no year-end has accrued wages.

**Step 5. Measure the earlier year-ends from the registers.** The period paid in the next year in full, plus the share of the crossing period that falls in the year, by working days from WorkCenterCalendar. The model's formulas give the working days within the year, the share, and the total. They read the Tables the workbook loads (WorkingDays, PayrollCost, PayrollPeriods), the year-end names such as `YE_{{ d.F }}`, and the cells of the payroll block that the figure shows, so build that block first (**Formulas > Name Manager** lists the names):

```jinja
{{ g.f.days_in }}
{{ g.f.share }}
{{ g.f.owed }}
```

**Check:** {{ d.F }}: ${{ pf.full.cost|money }} plus {{ pf.cross.inside }} of {{ pf.cross.days }} working days of the next period, ${{ pf.cross.share|money }}, is ${{ pf.total|money }}. {{ d.P }}: ${{ pp.full.cost|money }} plus {{ pp.cross.inside }} of {{ pp.cross.days }}, ${{ pp.cross.share|money }}, is ${{ pp.total|money }}. **Watch for:** prorating by calendar days. The crossing period then counts a fraction of two weeks, and the totals read ${{ g.cal[0]|money }} and ${{ g.cal[1]|money }}, short by ${{ g.cal_short[0]|money }} and ${{ g.cal_short[1]|money }}.

**Step 6. Estimate the last year-end from the processed periods.** The last two periods have no registers, so multiply the cost per working day of the last eight processed periods by the working days left. The model's formulas list the periods, count their working days, count the days left, and accrue:

```jinja
{{ g.f.eight }}
{{ g.f.d_days }}
{{ g.f.d_left }}
{{ g.f.d_owed }}
```

**Check:** {{ pc.p.wd }} working days, ${{ pc.p.cost|money }}, ${{ pc.p.daily|num(2) }} a day, {{ pc.p.left }} days left: ${{ pc.total|money }}, of which gross pay ${{ pc.gross|money }}, employer taxes ${{ pc.tax|money }} and benefits ${{ pc.ben|money }}. Manufacturing, ${{ pc.mfg|money }}, would have gone to `1090`. Under the case's standard-cost close it ends in `5080` and cost of goods sold, because standard cost leaves `1090` only through completions. An answer that traces the December work to its work orders and assigns part of it to work in process or finished goods is acceptable. The rest goes to the cost centers' salary accounts and `6060`. **Watch for:** two errors. An accrual from the registers alone is zero, and the last year's effect becomes +${{ g.open_none|money }}, the reversal of the year before with nothing new. One period's cost per day gives ${{ g.single|money }}, ${{ g.single_over|money }} too high.

### Part 3: Interest

**Step 7. Accrue each note's interest from its schedule.** Each payment's interest covers the days since the one before it, so the year-end owes the next payment's interest for the days to the year-end, counted inclusive. State the convention.

```jinja
{{ g.f.accrued }}
```

**Check:** ${{ ints[0].total|money }}, ${{ ints[1].total|money }} and ${{ ints[2].total|money }}; at the last year-end the second note's payment of {{ ints[2]['items'][1]['date'] }} covers {{ ints[2]['items'][1]['span'] }} days and {{ ints[2]['items'][1]['elapsed'] }} are owed. Leaving out the day of the previous payment gives ${{ ints[2].alt|money }}; either is acceptable if stated. **Watch for:** accruing the whole next payment, ${{ g.full_next[2]|money }}.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Invoices posted late; their subtotal, {{ d.F }}, {{ d.P }} | {{ cf.n }}, {{ cp.n }}; ${{ cf.total|money }}, ${{ cp.total|money }} | 1 |
| Lines never invoiced; at order price less discount | {{ cc.n_lines }}; ${{ cc.total|money }} | 2 |
| Payroll owed, {{ d.F }}, {{ d.P }}, {{ d.C }} | ${{ pf.total|money }}; ${{ pp.total|money }}; ${{ pc.total|money }} | 5, 6 |
| Interest accrued, {{ d.F }}, {{ d.P }}, {{ d.C }} | ${{ ints[0].total|money }}; ${{ ints[1].total|money }}; ${{ ints[2].total|money }} | 7 |

{{ expected() }}

## What a strong answer says

- **Revenue.** Recognized in the year of delivery; the invoices and the unbilled lines both found; the entry at each year-end.
- **Payroll.** One working-day method at every year-end, manufacturing separated and explained, the last year's estimate stated as an estimate.
- **Interest.** The convention named; either day count is accepted when it is stated.

A weak answer finds the invoices and forgets the unbilled lines, or uses one method for one year and another for the next.

## Common mistakes and how to respond

- **Dating by invoice.** *Symptom:* {{ g.n_date[d.C] }} invoices for {{ d.C }}. *Response:* ask which date the ledger used to post them.
- **Invoices only.** *Symptom:* no adjustment at the last year-end. *Response:* ask what a shipment with no invoice line is.
- **Calendar days.** *Symptom:* payroll ${{ g.cal_short[1]|money }} short. *Response:* ask how many days of the period people worked.
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
