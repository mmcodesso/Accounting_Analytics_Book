# Requirement 3: Test the data (Chapter 2)

| | |
|---|---|
| Unit | Case Part 1: Getting the Data Ready for the Furniture Margin Question |
| Item | Requirement 3 |
| Tools | Workbook browsing and written work |
| Time | About 40 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 3 turns Chapter 2's checklist into a decision. Students already found several data quality problems in Tutorials 2.1 and 2.2. The case asks a harder question of each: could it distort this comparison? The answer depends on the population, the period and the measure, and that dependence is the lesson. The requirement also fixes the two quarters that the rest of the case uses.

By the end, students can:

- find the edges of an extract and name the latest complete quarter, with the reason the latest rows of the ledger are not it;
- judge, for each earlier finding, whether it touches the Furniture margin of the two quarters, and give the reason;
- say which findings would matter for a different question or period, so that "not relevant here" is not read as "not a problem".

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (extraction, transformation and cleansing of financial data); IMA Data Literacy and Data Governance; IFAC IES 2 (i), using information and communications technologies to analyze data; AACSB A5 part 5.1 (technology integration, here Excel). The analytics type is descriptive, at the stage of preparing and testing the data.

## Before you assign

- Students need their Tutorial 2.1 and 2.2 notes (or the tutorials to rerun) and the data quality checklist of Chapter 2. Exercises 2.1 and 2.2 are the closest practice.
- The requirement relies on these conditions: the ledger's rows after 2026-12-31 are all of one source document type (DisbursementPayment); the ledger's monthly row counts in the last six periods are similar, so the fourth quarter is not partial; 9 invoices are dated before the first shipment of their order, and only 3 of them hold Furniture lines; some customers share a name; and the blank list prices belong to items the company buys.
- Verify that students kept their working copy unchanged, since a helper column from Tutorial 2.1 (Min Date and Check in SalesInvoice) is reused here. If they did not keep it, the first step of Phase 2 rebuilds it in five minutes.

## How to run it

Individual or pairs, 40 minutes: 15 on the edges of the extract and 25 on the findings. **Hints to hold back.** For the first part, ask "what is in the ledger after the last invoice?" and let students find the answer in the PivotTable. For the second, ask "which table and column does the Furniture margin use?" before each finding. **Collect** the quarter choice with its reason, and a table of the findings with a verdict and a reason for each.

## Step-by-step solution

### Phase 1: Find the most recent complete quarter

**Step 1. Read both edges of the extract.** As in Tutorial 2.2 Step 6, build a PivotTable from GLEntry with FiscalYear and FiscalPeriod in **Rows** and a count of GLEntryID in **Values**, and put SourceDocumentType in **Columns** or filter by the latest fiscal year. Then read the earliest and latest dates of PostingDate, InvoiceDate (SalesInvoice) and ShipmentDate (Shipment) by sorting each column.

a. The ledger runs from 2024-01-01 to 2027-02-23.
b. The last invoice and the last shipment are both dated 2026-12-31.
c. Fiscal 2027 holds 526 rows, all DisbursementPayment.
d. The periods of 2026 from 7 to 12 hold similar numbers of rows:
   - period 7: 26,113
   - period 8: 25,742
   - period 9: 27,585
   - period 10: 27,269
   - period 11: 28,605
   - period 12: 27,211

**Check:** the sales documents stop on the last day of fiscal 2026, so the fourth quarter is complete for sales and shipments; the ledger's later rows are payments of prior-year supplier invoices, with no sales and no shipments, so no margin can come from them. The latest complete quarter is 2026 Q4, compared with 2026 Q3. A student who also looked at the start finds 279 invoices in the first month of the extract against 512 in the second: a partial first month that does not touch these quarters, which is the other edge.

**Watch for:** "the latest quarter is 2027 Q1" because those rows are the latest, and "the latest quarter is complete because it has ledger rows". Ask what kind of rows.

### Phase 2: Judge the findings

**Step 2. Invoices dated before their first shipment.** Rebuild the helper columns of Tutorial 2.1 in the SalesInvoice worksheet (the first empty column is M) and filter the check column for Check.

```
=MINIFS(Shipment!D:D, Shipment!C:C, E2)
```

```
=IF(M2=0, "No shipment", IF(C2<M2, "Check", "OK"))
```

The filter lists 9 invoices. To see which hold Furniture lines, filter SalesInvoiceLine by each invoice's SalesInvoiceID and read the ItemID in Item, or use the item group helper column of Requirement 4. The model answer:

| Invoice | Dated | First shipment | Posted | Furniture lines | Posted in another year |
|---|---|---|---|---:|---|
| SI-2024-000001 | 2024-01-01 | 2024-01-03 | 2024-01-03 | 0 | No |
| SI-2024-000002 | 2024-01-02 | 2024-01-04 | 2024-01-04 | 0 | No |
| SI-2024-000003 | 2024-01-01 | 2024-01-03 | 2024-01-06 | 1 | No |
| SI-2025-006733 | 2024-11-23 | 2024-11-25 | 2025-01-01 | 0 | Yes |
| SI-2025-006734 | 2024-12-05 | 2024-12-07 | 2025-01-01 | 0 | Yes |
| SI-2025-006735 | 2024-12-15 | 2024-12-17 | 2025-01-01 | 1 | Yes |
| SI-2026-013741 | 2025-11-29 | 2025-12-01 | 2026-01-01 | 0 | Yes |
| SI-2026-013742 | 2025-12-04 | 2025-12-06 | 2026-01-01 | 1 | Yes |
| SI-2026-013743 | 2025-12-03 | 2025-12-05 | 2026-01-01 | 0 | Yes |

**Check:** of the 9 invoices, 3 hold Furniture lines, and none is dated, shipped or posted in 2026 Q3 or 2026 Q4, so none can distort this comparison. A model answer adds that two of them cross a year-end (SI-2025-006735, dated 2024-12-15, shipped 2024-12-17 and posted 2025-01-01, and SI-2026-013742, dated 2025-12-04, shipped 2025-12-06 and posted 2026-01-01), so they would matter for an annual Furniture revenue figure or a year-end cutoff test. **Watch for:** "no effect, so no problem". The finding is out of scope for this comparison, not harmless.

**Step 3. Customers that share a name.** Sort the Customer worksheet by CustomerName and scan. There are 2 pairs among 220 customers. **Check:** the margin is computed by item group, and a customer's name is not in the selection or the measure, so the pairs do not touch it. They would distort a customer count or a ranking of customers by revenue, unless the analysis groups by CustomerID.

**Step 4. List prices that are blank by design.** Filter the Item worksheet's ListPrice column for blanks: 43 items, all in Capex, Packaging, Raw Materials, and Services. **Check:** no Furniture item has a blank list price, and no invoice line is for an item with one, so the Furniture lines are untouched. The blanks are items the company buys, not products it sells.

**Step 5. The other findings of Tutorial 2.1 (not named in the case).** A strong student also considers blank tracking numbers and "In Transit" shipments whose delivery date has passed. For the Furniture shipments of the two quarters:

| Quarter | Furniture shipments | With a blank TrackingNumber | Lines | Standard cost | Still "In Transit" with a past delivery date |
|---|---:|---:|---:|---:|---:|
| 2026 Q3 | 531 | 16 | 28 | $82,731.53 | 38 |
| 2026 Q4 | 530 | 28 | 46 | $122,218.45 | 46 |

**Check:** a shipment's cost posts on its ShipmentDate whatever its tracking number or status says, so neither changes the margin arithmetic. They weaken the evidence that the goods left, which matters for the auditing view in Requirement 6.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Last invoice date; last ledger posting date | 2026-12-31; 2027-02-23 | Step 1 |
| Rows of fiscal 2027, all DisbursementPayment | 526 | Step 1 |
| Latest complete quarter, and its comparison quarter | 2026 Q4, 2026 Q3 | Step 1 |
| Invoices dated before their first shipment; with Furniture lines | 9; 3 | Step 2 |
| Of those, dated, shipped or posted in either quarter | None | Step 2 |
| Same-name customer pairs | 2 | Step 3 |
| Items with a blank list price; Furniture among them | 43; none | Step 4 |

> **Instructor notes, Requirement 3:** invoices run through 2026-12-31, and the GL continues to 2027-02-23 with only DisbursementPayment rows (supplier payments for prior-year invoices), so the latest complete quarter is 2026 Q4 (compared with 2026 Q3). Of the 9 invoices dated before their order's first shipment, 3 contain Furniture lines (SI-2024-000003, SI-2025-006735, SI-2026-013742), and none is dated, shipped, or posted in 2026 Q3 or Q4, so they do not affect this comparison. They matter for revenue cutoff in general, because two of them cross a year-end. SI-2025-006735 is dated 2024-12-15, shipped 2024-12-17 and posted 2025-01-01. SI-2026-013742 is dated 2025-12-04, shipped 2025-12-06 and posted 2026-01-01. Same-name customers do not affect a product-line margin. Blank list prices belong to purchased items and services, not to Furniture products.

## What a strong answer says

- **The quarter.** 2026 Q4 against 2026 Q3, chosen because sales and shipments end on the last day of fiscal 2026 and the ledger's later rows are only supplier payments.
- **The cutoff finding.** It holds Furniture lines on 3 invoices, none in either quarter, so no effect here; it matters for year-end and annual views.
- **Same-name customers and blank list prices.** Neither touches a Furniture margin by item group, with the reason given: the first is about customers, the second about items the company buys.
- **Scope.** The verdicts are for this question; the answer says which findings would matter for another.

A weak answer names the findings without a verdict, calls all of them threats, or dismisses them without a reason.

## Common mistakes and how to respond

- **The wrong latest quarter.** *Symptom:* a comparison with 2027 rows. *Response:* ask what source document type those rows come from.
- **Every finding a threat.** *Symptom:* "all of these could distort the margin". *Response:* ask which table and column each finding lives in and whether the margin uses it.
- **Every finding dismissed.** *Symptom:* "not relevant" with no reason. *Response:* ask what would make it relevant.
- **Relevance confused with importance.** *Symptom:* "no effect, so no problem". *Response:* ask what the controller would conclude if the question were annual revenue.
- **A population error.** *Symptom:* all nine invoices called Furniture. *Response:* ask how many hold Furniture lines.
- **Dates mixed up.** *Symptom:* an invoice date and a posting date used as the same thing. *Response:* have them read the two columns side by side in the table of Step 2.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Latest complete quarter | 40 | 2026 Q4 against 2026 Q3, with the edge reasoning and the ledger's tail identified | The right quarter without the reason, or the reason without the evidence |
| Cutoff finding | 15 | Furniture lines identified, none in the quarters, and the broader relevance named | Verdict without the population check |
| Same-name customers | 10 | Not relevant to an item-group margin, with the reason, and relevant elsewhere | Verdict with no reason |
| Blank list prices | 10 | By design, not in Furniture, no effect | Verdict with no reason |
| Quality of the reasoning | 15 | Each verdict tied to the table, column and period of the measure | Verdicts that restate the finding |
| Evidence and presentation | 10 | A table of findings with verdicts, and the PivotTable of the edges | Prose only |

## Extensions and discussion questions

- Add the tracking-number and "In Transit" findings to the table, and say which kind of assertion they weaken (the shipment's occurrence) and which they leave alone (its measurement).
- Rerun the Furniture comparison for the previous fiscal year's last two quarters. Which findings of the nine invoices now matter?
- Discuss: the case's findings were found by one analyst for another question. What should a data readiness memo do with findings that do not matter this time?
- Discuss: Requirement 4 tests whether the documents' totals agree with the ledger. Which finding of this requirement would most weaken that test if it mattered?
