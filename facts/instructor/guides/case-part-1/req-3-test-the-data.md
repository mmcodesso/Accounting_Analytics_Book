---
note: case1.r3
uses: [case1.g3]
title: Test the data (Chapter 2)
kind: requirement
number: '3'
unit: case1
perspective: general
tool: conceptual
minutes: 40
solution: ''
figures: []
---
{% set g = case1_g3 %}
# Requirement 3: Test the data (Chapter 2)

{{ header() }}

## Purpose and learning outcomes

Requirement 3 turns Chapter 2's checklist into a decision. Students already found several data quality problems in Tutorials 2.1 and 2.2. The case asks a harder question of each: could it distort this comparison? The answer depends on the population, the period and the measure, and that dependence is the lesson. The requirement also fixes the two quarters that the rest of the case uses.

By the end, students can:

- find the edges of an extract and name the latest complete quarter, with the reason the latest rows of the ledger are not it;
- judge, for each earlier finding, whether it touches the Furniture margin of the two quarters, and give the reason;
- say which findings would matter for a different question or period, so that "not relevant here" is not read as "not a problem".

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (extraction, transformation and cleansing of financial data); IMA Data Literacy and Data Governance; IFAC IES 2 (i), using information and communications technologies to analyze data; AACSB A5 part 5.1 (technology integration, here Excel). The analytics type is descriptive, at the stage of preparing and testing the data.

## Before you assign

- Students need their Tutorial 2.1 and 2.2 notes (or the tutorials to rerun) and the data quality checklist of Chapter 2. Exercises 2.1 and 2.2 are the closest practice.
- The requirement relies on these conditions: the ledger's rows after {{ g.last_invoice }} are all of one source document type ({{ g.late_types }}); the ledger's monthly row counts in the last six periods are similar, so the fourth quarter is not partial; {{ g.n_nine }} invoices are dated before the first shipment of their order, and only {{ g.n_furniture }} of them hold Furniture lines; some customers share a name; and the blank list prices belong to items the company buys.
- Verify that students kept their working copy unchanged, since a helper column from Tutorial 2.1 (Min Date and Check in SalesInvoice) is reused here. If they did not keep it, the first step of Phase 2 rebuilds it in five minutes.

## How to run it

Individual or pairs, 40 minutes: 15 on the edges of the extract and 25 on the findings. **Hints to hold back.** For the first part, ask "what is in the ledger after the last invoice?" and let students find the answer in the PivotTable. For the second, ask "which table and column does the Furniture margin use?" before each finding. **Collect** the quarter choice with its reason, and a table of the findings with a verdict and a reason for each.

## Step-by-step solution

### Phase 1: Find the most recent complete quarter

**Step 1. Read both edges of the extract.** As in Tutorial 2.2 Step 6, build a PivotTable from GLEntry with FiscalYear and FiscalPeriod in **Rows** and a count of GLEntryID in **Values**, and put SourceDocumentType in **Columns** or filter by the latest fiscal year. Then read the earliest and latest dates of PostingDate, InvoiceDate (SalesInvoice) and ShipmentDate (Shipment) by sorting each column.

a. The ledger runs from {{ g.first_post }} to {{ g.last_post }}.
b. The last invoice and the last shipment are both dated {{ g.last_invoice }}.
c. Fiscal {{ g.next_year }} holds {{ g.late_rows }} rows, all {{ g.late_types }}.
d. The periods of {{ g.year }} from 7 to 12 hold similar numbers of rows:
{% for p in g.periods %}
   - period {{ p[0] }}: {{ p[1]|count }}
{% endfor %}

**Check:** the sales documents stop on the last day of fiscal {{ g.year }}, so the fourth quarter is complete for sales and shipments; the ledger's later rows are payments of prior-year supplier invoices, with no sales and no shipments, so no margin can come from them. The latest complete quarter is {{ g.ql4 }}, compared with {{ g.ql3 }}. A student who also looked at the start finds {{ g.jan_invoices }} invoices in the first month of the extract against {{ g.feb_invoices }} in the second: a partial first month that does not touch these quarters, which is the other edge.

**Watch for:** "the latest quarter is {{ g.next_year }} Q1" because those rows are the latest, and "the latest quarter is complete because it has ledger rows". Ask what kind of rows.

### Phase 2: Judge the findings

**Step 2. Invoices dated before their first shipment.** Rebuild the helper columns of Tutorial 2.1 in the SalesInvoice worksheet (the first empty column is {{ g.cols.next_free }}) and filter the check column for Check.

```jinja
=MINIFS(Shipment!{{ g.cols.date_in_shipment }}:{{ g.cols.date_in_shipment }}, Shipment!{{ g.cols.order_in_shipment }}:{{ g.cols.order_in_shipment }}, {{ g.cols.order_in_invoice }}2)
```

```
=IF(M2=0, "No shipment", IF(C2<M2, "Check", "OK"))
```

The filter lists {{ g.n_nine }} invoices. To see which hold Furniture lines, filter SalesInvoiceLine by each invoice's SalesInvoiceID and read the ItemID in Item, or use the item group helper column of Requirement 4. The model answer:

| Invoice | Dated | First shipment | Posted | Furniture lines | Posted in another year |
|---|---|---|---|---:|---|
{% for r in g.nine %}
| {{ r.number }} | {{ r.dated }} | {{ r.shipped }} | {{ r.posted }} | {{ r.lines }} | {{ 'Yes' if r.moved else 'No' }} |
{% endfor %}

**Check:** of the {{ g.n_nine }} invoices, {{ g.n_furniture }} hold Furniture lines, and none is dated, shipped or posted in {{ g.ql3 }} or {{ g.ql4 }}, so none can distort this comparison. A model answer adds that {{ crossing_word }} of them cross a year-end ({% for c in crossing %}{{ c.number }}, dated {{ c.dated }}, shipped {{ c.shipped }} and posted {{ c.posted }}{{ ', and ' if loop.first else '' }}{% endfor %}), so they would matter for an annual Furniture revenue figure or a year-end cutoff test. **Watch for:** "no effect, so no problem". The finding is out of scope for this comparison, not harmless.

**Step 3. Customers that share a name.** Sort the Customer worksheet by CustomerName and scan. There are {{ g.pairs }} pairs among {{ g.customers }} customers. **Check:** the margin is computed by item group, and a customer's name is not in the selection or the measure, so the pairs do not touch it. They would distort a customer count or a ranking of customers by revenue, unless the analysis groups by CustomerID.

**Step 4. List prices that are blank by design.** Filter the Item worksheet's ListPrice column for blanks: {{ g.blank_items }} items, all in {{ g.blank_groups }}. **Check:** no Furniture item has a blank list price, and no invoice line is for an item with one, so the Furniture lines are untouched. The blanks are items the company buys, not products it sells.

**Step 5. The other findings of Tutorial 2.1 (not named in the case).** A strong student also considers blank tracking numbers and "In Transit" shipments whose delivery date has passed. For the Furniture shipments of the two quarters:

| Quarter | Furniture shipments | With a blank TrackingNumber | Lines | Standard cost | Still "In Transit" with a past delivery date |
|---|---:|---:|---:|---:|---:|
| {{ g.ql3 }} | {{ g.other.q3.shipments }} | {{ g.other.q3.blank }} | {{ g.other.q3.blank_lines }} | ${{ g.other.q3.blank_cost|money }} | {{ g.other.q3.stale }} |
| {{ g.ql4 }} | {{ g.other.q4.shipments }} | {{ g.other.q4.blank }} | {{ g.other.q4.blank_lines }} | ${{ g.other.q4.blank_cost|money }} | {{ g.other.q4.stale }} |

**Check:** a shipment's cost posts on its ShipmentDate whatever its tracking number or status says, so neither changes the margin arithmetic. They weaken the evidence that the goods left, which matters for the auditing view in Requirement 6.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Last invoice date; last ledger posting date | {{ last_invoice }}; {{ last_gl }} | Step 1 |
| Rows of fiscal {{ g.next_year }}, all {{ g.late_types }} | {{ g.late_rows }} | Step 1 |
| Latest complete quarter, and its comparison quarter | {{ g.ql4 }}, {{ g.ql3 }} | Step 1 |
| Invoices dated before their first shipment; with Furniture lines | {{ invoices }}; {{ furniture|length }} | Step 2 |
| Of those, dated, shipped or posted in either quarter | None | Step 2 |
| Same-name customer pairs | {{ g.pairs }} | Step 3 |
| Items with a blank list price; Furniture among them | {{ g.blank_items }}; none | Step 4 |

{{ expected() }}

## What a strong answer says

- **The quarter.** {{ g.ql4 }} against {{ g.ql3 }}, chosen because sales and shipments end on the last day of fiscal {{ g.year }} and the ledger's later rows are only supplier payments.
- **The cutoff finding.** It holds Furniture lines on {{ furniture|length }} invoices, none in either quarter, so no effect here; it matters for year-end and annual views.
- **Same-name customers and blank list prices.** Neither touches a Furniture margin by item group, with the reason given: the first is about customers, the second about items the company buys.
- **Scope.** The verdicts are for this question; the answer says which findings would matter for another.

A weak answer names the findings without a verdict, calls all of them threats, or dismisses them without a reason.

## Common mistakes and how to respond

- **The wrong latest quarter.** *Symptom:* a comparison with {{ g.next_year }} rows. *Response:* ask what source document type those rows come from.
- **Every finding a threat.** *Symptom:* "all of these could distort the margin". *Response:* ask which table and column each finding lives in and whether the margin uses it.
- **Every finding dismissed.** *Symptom:* "not relevant" with no reason. *Response:* ask what would make it relevant.
- **Relevance confused with importance.** *Symptom:* "no effect, so no problem". *Response:* ask what the controller would conclude if the question were annual revenue.
- **A population error.** *Symptom:* all nine invoices called Furniture. *Response:* ask how many hold Furniture lines.
- **Dates mixed up.** *Symptom:* an invoice date and a posting date used as the same thing. *Response:* have them read the two columns side by side in the table of Step 2.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Latest complete quarter | 40 | {{ g.ql4 }} against {{ g.ql3 }}, with the edge reasoning and the ledger's tail identified | The right quarter without the reason, or the reason without the evidence |
| Cutoff finding | 15 | Furniture lines identified, none in the quarters, and the broader relevance named | Verdict without the population check |
| Same-name customers | 10 | Not relevant to an item-group margin, with the reason, and relevant elsewhere | Verdict with no reason |
| Blank list prices | 10 | By design, not in Furniture, no effect | Verdict with no reason |
| Quality of the reasoning | 15 | Each verdict tied to the table, column and period of the measure | Verdicts that restate the finding |
| Evidence and presentation | 10 | A table of findings with verdicts, and the PivotTable of the edges | Prose only |

## Extensions and discussion questions

- Add the tracking-number and "In Transit" findings to the table, and say which kind of assertion they weaken (the shipment's occurrence) and which they leave alone (its measurement).
- Rerun the Furniture comparison for the previous fiscal year's last two quarters. Which findings of the nine invoices now matter?
- Discuss: the case's findings were found by one analyst for another question. What should a data readiness memo do with findings that do not matter this time?
- Discuss: Requirement 4 tests whether the documents reached the ledger. Which finding of this requirement would most weaken that test if it mattered?
