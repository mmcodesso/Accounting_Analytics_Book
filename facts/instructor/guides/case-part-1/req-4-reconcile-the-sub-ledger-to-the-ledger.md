---
note: case1.r4
uses: [case1.g4]
title: Reconcile the sub-ledger to the ledger (Chapters 2 and 3)
kind: requirement
number: '4'
unit: case1
perspective: general
tool: conceptual
minutes: 60
solution: ''
figures:
  - id: IF-C1-4-A
    kind: excel-mock
    purpose: The reconciliation table of the appendix, as a student's worksheet would show it.
    shows: A worksheet named Reconciliation with two blocks. The revenue block has a row for each of the two quarters and the columns Invoice lines, Sum of LineTotal, Ledger credits to the Furniture revenue account from SalesInvoice, and Difference. The cost block has the columns Shipment lines, Standard cost, Ledger debits to the Furniture cost account from Shipment, and Difference. Every Difference cell shows zero and is outlined. A note row beneath names the other source document types that post to the cost account.
    data: The Expected results of this requirement (sub-ledger and ledger totals of the two quarters).
---
{% set g = case1_g4 %}
# Requirement 4: Reconcile the sub-ledger to the ledger (Chapters 2 and 3)

{{ header() }}

## Purpose and learning outcomes

Requirement 4 is the case's tie-out. The question is whether the totals of the documents students will analyze (invoice lines and shipment lines) agree with the ledger the controller reports from. It is also the first time students need the whole map of Requirement 2 at once: lookups across worksheets, a PivotTable on the document side and another on the ledger side, and a comparison to the cent. The harder half is interpretive: what agreement does and does not show.

By the end, students can:

- total a product line's revenue and standard cost from document lines by quarter, using lookups for the date and the item group;
- total the matching ledger postings by account, source document type and quarter, and compare to the cent;
- explain what agreement shows, what it leaves open, and which source document types post to the cost account.

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Financial Recordkeeping; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (f), audit; AACSB A5 part 5.1. The analytics type is descriptive.

## Before you assign

- Students need the Requirement 2 map, Tutorial 2.2 (PivotTables on GLEntry) and Tutorial 3.2 (the trace), and the lookups of Tutorials 2.1 and 2.2.
- The requirement relies on these conditions: every invoice line has an invoice date and an item, and every shipment line a shipment date through its shipment; the invoices posted to the Furniture revenue account in a quarter are the invoices dated in it; and the only journal entries on the two Furniture accounts are year-end closes. Item.StandardCost is not used: the standard cost is on the shipment line itself (ExtendedStandardCost).
- The sheets are large ({{ g.lines_rows|count }} invoice lines and {{ g.ship_rows|count }} shipment lines). Helper columns on those two are fine; do not allow helper columns on GLEntry.

## How to run it

Individual work, 60 minutes: 20 on the revenue side, 20 on the cost side, 10 on the table and 10 on the interpretation. It is the longest requirement of the first four, so in a lab (Plan B) hand out the helper-column formulas of Steps 1 and 4. **Hints to hold back.** Say "a PivotTable ignores the worksheet's filter" only if students report Furniture totals that equal all groups. Say "which source document types are in the account?" only when students stop at agreement. **Collect** the reconciliation table; it is a part of the appendix.

## Step-by-step solution

### Phase 1: Furniture revenue, invoice lines against the ledger

**Step 1. Add three helper columns to SalesInvoiceLine.** The first empty column is {{ g.cols.h1 }}. Type the headers InvoiceDate, ItemGroup and Quarter in {{ g.cols.h1 }}1, {{ g.cols.h2 }}1 and {{ g.cols.h3 }}1 and fill the formulas down to the last row:

```jinja
=XLOOKUP({{ g.cols.line_invoice }}2, SalesInvoice!{{ g.cols.inv_id }}:{{ g.cols.inv_id }}, SalesInvoice!{{ g.cols.inv_date }}:{{ g.cols.inv_date }})
=XLOOKUP({{ g.cols.line_item }}2, Item!{{ g.cols.item_id }}:{{ g.cols.item_id }}, Item!{{ g.cols.item_group }}:{{ g.cols.item_group }})
=YEAR({{ g.cols.h1 }}2)&"-Q"&ROUNDUP(MONTH({{ g.cols.h1 }}2)/3,0)
```

**Check:** the lookups return no errors, and the Quarter column reads, for example, {{ g.year }}-Q3. **Watch for:** the helper filled only to the visible rows, which makes the totals short.

**Step 2. Total the Furniture lines by quarter.** Insert a PivotTable from SalesInvoiceLine: ItemGroup in **Filters** (set to Furniture), Quarter in **Rows**, Sum of LineTotal in **Values**. The item group must be in the PivotTable itself, because a PivotTable ignores the worksheet's filters. A formula cross-check for one cell:

```jinja
=SUMIFS(SalesInvoiceLine!{{ g.cols.line_total }}:{{ g.cols.line_total }}, SalesInvoiceLine!{{ g.cols.h2 }}:{{ g.cols.h2 }}, "Furniture", SalesInvoiceLine!{{ g.cols.h3 }}:{{ g.cols.h3 }}, "{{ g.year }}-Q3")
```

**Check:** the totals are {{ g.recon[0].label }} ${{ q3.lines|money }} on {{ g.recon[0].invoice_lines }} lines; {{ g.recon[1].label }} ${{ q4.lines|money }} on {{ g.recon[1].invoice_lines }} lines.

**Step 3. Total the ledger side.** Insert a PivotTable from GLEntry (no formulas on its rows): AccountID in **Filters** set to {{ revenue.id }} (account {{ revenue.number }}), FiscalYear in **Filters** set to {{ g.year }}, FiscalPeriod in **Filters** with the quarter's three periods selected, SourceDocumentType in **Rows**, and Sum of Debit and Sum of Credit in **Values**. Do it once for periods {{ g.periods3 }} and once for periods {{ g.periods4 }}. Fiscal periods equal calendar months, so the periods are the quarters.

**Check:** in {{ g.recon[0].label }}, one row: SalesInvoice, credits ${{ g.recon[0].ledger_revenue|money }}. In {{ g.recon[1].label }}, SalesInvoice credits ${{ g.recon[1].ledger_revenue|money }}, and a second row for JournalEntry, the year-end close, which Requirement 5 takes up. Compare only the SalesInvoice row with Step 2. The differences are ${{ g.recon[0].revenue_gap|money }} and ${{ g.recon[1].revenue_gap|money }}.

### Phase 2: Furniture cost, shipment lines against the ledger

**Step 4. Add helper columns to ShipmentLine.** The first empty column is {{ g.cols.k1 }}: ShipmentDate, ItemGroup and Quarter.

```jinja
=XLOOKUP({{ g.cols.sl_ship }}2, Shipment!{{ g.cols.ship_id }}:{{ g.cols.ship_id }}, Shipment!{{ g.cols.ship_date }}:{{ g.cols.ship_date }})
=XLOOKUP({{ g.cols.sl_item }}2, Item!{{ g.cols.item_id }}:{{ g.cols.item_id }}, Item!{{ g.cols.item_group }}:{{ g.cols.item_group }})
=YEAR({{ g.cols.k1 }}2)&"-Q"&ROUNDUP(MONTH({{ g.cols.k1 }}2)/3,0)
```

**Step 5. Total the standard cost.** PivotTable from ShipmentLine: ItemGroup in **Filters** (Furniture), Quarter in **Rows**, Sum of ExtendedStandardCost in **Values**.

**Check:** the totals are {{ g.recon[0].label }} ${{ q3.shipped|money }} on {{ g.recon[0].shipment_lines }} lines; {{ g.recon[1].label }} ${{ q4.shipped|money }} on {{ g.recon[1].shipment_lines }} lines.

**Step 6. Total the ledger side.** The same GLEntry PivotTable with AccountID set to {{ cogs.id }} (account {{ cogs.number }}). The Shipment row's debits are the cost of the shipments; compare it with Step 5.

**Check:** the Shipment debits are ${{ g.recon[0].ledger_cogs|money }} and ${{ g.recon[1].ledger_cogs|money }}, and the differences ${{ g.recon[0].cogs_gap|money }} and ${{ g.recon[1].cogs_gap|money }}. The same PivotTable shows other rows, which Step 8 explains.

### Phase 3: The table and what it means

**Step 7. Build the reconciliation table.** A model table for the appendix:

| Quarter | Invoice lines | Sum of LineTotal | Ledger credits, {{ revenue.number }} from SalesInvoice | Difference |
|---|---:|---:|---:|---:|
{% for r in g.recon %}
| {{ r.label }} | {{ r.invoice_lines }} | ${{ r.lines|money }} | ${{ r.ledger_revenue|money }} | ${{ r.revenue_gap|money }} |
{% endfor %}

| Quarter | Shipment lines | Standard cost | Ledger debits, {{ cogs.number }} from Shipment | Difference |
|---|---:|---:|---:|---:|
{% for r in g.recon %}
| {{ r.label }} | {{ r.shipment_lines }} | ${{ r.shipped|money }} | ${{ r.ledger_cogs|money }} | ${{ r.cogs_gap|money }} |
{% endfor %}

{{ figure('IF-C1-4-A') }}

**Step 8. Say what agreement shows, and what it does not.** The selected totals agree to the cent for each quarter and source document type. That supports the consistency of these recorded populations, but agreement of totals does not show by itself that every line posted exactly once, because an omission and a duplicate of the same amount would offset. A line-by-line match through SourceLineID, which every posting of the two kinds carries, would support a stronger conclusion, and the case does not ask for it. Three more things stay open:

a. Whether every Furniture sale was invoiced. In {{ g.recon[0].label }} every Furniture shipment line has an invoice line. In {{ g.recon[1].label }}, {{ g.recon[1].uninvoiced.lines }} lines shipped in its last month have none. Their standard cost of ${{ g.recon[1].uninvoiced.cost|money }} sits in the cost account without revenue, and at their order prices they would bill ${{ g.recon[1].uninvoiced.at_order_price|money }}. The extract cannot show whether they were billed later, so they need follow-up.
b. Whether the documents are right, in their prices, dates and quantities. Requirement 3's findings are the kind of evidence needed.
c. Whether revenue and cost fall in the same quarter. Revenue follows the invoice date and cost the shipment date. In {{ g.recon[0].label }}, {{ g.recon[0].shifted.lines }} of the lines invoiced (${{ g.recon[0].shifted.revenue|money }}) shipped in an earlier quarter, and in {{ g.recon[1].label }}, {{ g.recon[1].shifted.lines }} (${{ g.recon[1].shifted.revenue|money }}) did.

**Step 9. Name the other source document types on the cost account.** Remove the filters on year and period and read the SourceDocumentType rows of account {{ cogs.number }}:

| Source document type | Ledger rows | Direction | Meaning |
|---|---:|---|---|
{% for s in g.sources %}
| {{ s.source }} | {{ s.rows|count }} | {{ 'Debits' if s.debits else 'Credits' }} | {{ 'Cost of goods shipped' if s.source == 'Shipment' else 'Cost relieved when goods come back' if s.source == 'SalesReturn' else 'The year-end closes, one a fiscal year' }} |
{% endfor %}

**Check:** the case's reconciliation covers shipments only, so a margin built from the ledger must decide about the other two types. Returns reduce the cost in {{ g.ql3 }} by ${{ g.recon[0].returns|money }} and in {{ g.ql4 }} by ${{ g.recon[1].returns|money }}; the close is a Requirement 5 matter. **Watch for:** a student who stops at "the totals agree" and does not name the other two types.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Furniture invoice lines, {{ g.ql3 }}; {{ g.ql4 }} | ${{ q3.lines|money }}; ${{ q4.lines|money }} | Step 2 |
| Ledger credits to {{ revenue.number }} from SalesInvoice | ${{ g.recon[0].ledger_revenue|money }}; ${{ g.recon[1].ledger_revenue|money }} | Step 3 |
| Furniture shipment lines at standard cost | ${{ q3.shipped|money }}; ${{ q4.shipped|money }} | Step 5 |
| Ledger debits to {{ cogs.number }} from Shipment | ${{ g.recon[0].ledger_cogs|money }}; ${{ g.recon[1].ledger_cogs|money }} | Step 6 |
| Differences, revenue and cost | Zero in every cell | Steps 3 and 6 |
| Return credits to {{ cogs.number }} | ${{ g.recon[0].returns|money }}; ${{ g.recon[1].returns|money }} | Step 9 |
| Furniture shipment lines with no invoice line | {{ g.recon[0].uninvoiced.lines }}; {{ g.recon[1].uninvoiced.lines }} | Step 8 |

{{ expected() }}

## What a strong answer says

- **The tie-out.** Both sides, both quarters, to the cent, in a table, with the differences shown.
- **What agreement shows.** The selected totals agree for both quarters, which supports the consistency of the recorded populations, not the posting of every line.
- **What it does not show.** That each line posted once, that every sale was invoiced, that the documents are right, and that revenue and cost match in time. The best answers name the unbilled Q4 shipments.
- **Other sources.** Shipment, SalesReturn and JournalEntry on the cost account, with the direction of each.

A weak answer reports totals without a comparison, calls agreement proof of reliability, or names only the Shipment type.

## Common mistakes and how to respond

- **Totals for every item group.** *Symptom:* a revenue far above the ledger's account. *Response:* ask where ItemGroup is in the PivotTable.
- **Helper formulas not filled down.** *Symptom:* totals short by a sliver. *Response:* have them count the rows of the helper column against the sheet.
- **The close in the comparison.** *Symptom:* a Q4 ledger total of a different sign. *Response:* have them compare only the SalesInvoice row, then see Requirement 5.
- **Net instead of gross.** *Symptom:* credits less debits compared with invoice lines. *Response:* ask which source document type the invoice lines belong to.
- **Agreement as proof.** *Symptom:* "so the data is reliable". *Response:* ask what an unbilled shipment would do to the tie-out.
- **A date mix-up.** *Symptom:* shipment dates used for the invoice lines. *Response:* ask which date drives each document's posting.
- **Rounding.** *Symptom:* a difference of a few cents after multiplying quantity by price. *Response:* the line totals are already rounded per line; sum LineTotal, not the products.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Revenue reconciliation | 30 | Both quarters, both sides, differences shown | One quarter, or a mismatch left unexplained |
| Cost reconciliation | 30 | Both quarters, both sides, differences shown | One quarter, or the wrong cost source |
| What agreement shows | 20 | Agreement of the selected totals, not proof that each line posted, and at least two things left open | "Reliable" with no limit |
| Other sources on the cost account | 10 | Shipment, SalesReturn and JournalEntry with their direction | One or two named |
| The table | 10 | A clean table fit for the appendix | Totals scattered in the workbook |

## Extensions and discussion questions

- Find the Furniture shipment lines of {{ g.ql4 }} with no invoice line, and say what you would ask the sales department.
- Discuss: the sub-ledger and the ledger come from the same system. What independent evidence would make the tie-out stronger?
- Discuss: Requirement 5 uses the ledger alone. What does the reconciliation let the student say about using it?
