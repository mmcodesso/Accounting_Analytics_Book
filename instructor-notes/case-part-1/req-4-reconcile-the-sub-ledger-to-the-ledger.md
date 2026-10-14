# Requirement 4: Reconcile the sub-ledger to the ledger (Chapters 2 and 3)

| | |
|---|---|
| Unit | Case Part 1: Getting the Data Ready for the Furniture Margin Question |
| Item | Requirement 4 |
| Tools | Workbook browsing and written work |
| Time | About 60 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 4 is the case's tie-out. The question is whether the documents students will analyze (invoice lines and shipment lines) are the same thing as the ledger the controller reports from. It is also the first time students need the whole map of Requirement 2 at once: lookups across worksheets, a PivotTable on the document side and another on the ledger side, and a comparison to the cent. The harder half is interpretive: what agreement does and does not show.

By the end, students can:

- total a product line's revenue and standard cost from document lines by quarter, using lookups for the date and the item group;
- total the matching ledger postings by account, source document type and quarter, and compare to the cent;
- explain what agreement shows, what it leaves open, and which source document types post to the cost account.

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 (financial statements, accounts and transactions) and Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Financial Recordkeeping and Financial Statement Preparation; IFAC IES 2 (a), financial accounting and reporting, and IES 2 (f), audit; AACSB A5 part 5.1. The analytics type is descriptive.

## Before you assign

- Students need the Requirement 2 map, Tutorial 2.2 (PivotTables on GLEntry) and Tutorial 3.2 (the trace), and the lookups of Tutorials 2.1 and 2.2.
- The requirement relies on these conditions: every invoice line has an invoice date and an item, and every shipment line a shipment date through its shipment; the invoices posted to the Furniture revenue account in a quarter are the invoices dated in it; and the only journal entries on the two Furniture accounts are year-end closes. Item.StandardCost is not used: the standard cost is on the shipment line itself (ExtendedStandardCost).
- The sheets are large (27,933 invoice lines and 27,503 shipment lines). Helper columns on those two are fine; do not allow helper columns on GLEntry.

## How to run it

Individual work, 60 minutes: 20 on the revenue side, 20 on the cost side, 10 on the table and 10 on the interpretation. It is the longest requirement of the first four, so in a lab (Plan B) hand out the helper-column formulas of Steps 1 and 4. **Hints to hold back.** Say "a PivotTable ignores the worksheet's filter" only if students report Furniture totals that equal all groups. Say "which source document types are in the account?" only when students stop at agreement. **Collect** the reconciliation table; it is a part of the appendix.

## Step-by-step solution

### Phase 1: Furniture revenue, invoice lines against the ledger

**Step 1. Add three helper columns to SalesInvoiceLine.** The first empty column is P. Type the headers InvoiceDate, ItemGroup and Quarter in P1, Q1 and R1 and fill the formulas down to the last row:

```
=XLOOKUP(B2, SalesInvoice!A:A, SalesInvoice!C:C)
=XLOOKUP(F2, Item!A:A, Item!D:D)
=YEAR(P2)&"-Q"&ROUNDUP(MONTH(P2)/3,0)
```

**Check:** the lookups return no errors, and the Quarter column reads, for example, 2026-Q3. **Watch for:** the helper filled only to the visible rows, which makes the totals short.

**Step 2. Total the Furniture lines by quarter.** Insert a PivotTable from SalesInvoiceLine: ItemGroup in **Filters** (set to Furniture), Quarter in **Rows**, Sum of LineTotal in **Values**. The item group must be in the PivotTable itself, because a PivotTable ignores the worksheet's filters. A formula cross-check for one cell:

```
=SUMIFS(SalesInvoiceLine!K:K, SalesInvoiceLine!Q:Q, "Furniture", SalesInvoiceLine!R:R, "2026-Q3")
```

**Check:** the totals are 2026 Q3 $4,283,322.86 on 868 lines; 2026 Q4 $4,156,787.84 on 864 lines.

**Step 3. Total the ledger side.** Insert a PivotTable from GLEntry (no formulas on its rows): AccountID in **Filters** set to 42 (account 4010), FiscalYear in **Filters** set to 2026, FiscalPeriod in **Filters** with the quarter's three periods selected, SourceDocumentType in **Rows**, and Sum of Debit and Sum of Credit in **Values**. Do it once for periods 7, 8 and 9 and once for periods 10, 11 and 12. Fiscal periods equal calendar months, so the periods are the quarters.

**Check:** in 2026 Q3, one row: SalesInvoice, credits $4,283,322.86. In 2026 Q4, SalesInvoice credits $4,156,787.84, and a second row for JournalEntry, the year-end close, which Requirement 5 takes up. Compare only the SalesInvoice row with Step 2. The differences are $0.00 and $0.00.

### Phase 2: Furniture cost, shipment lines against the ledger

**Step 4. Add helper columns to ShipmentLine.** The first empty column is H: ShipmentDate, ItemGroup and Quarter.

```
=XLOOKUP(B2, Shipment!A:A, Shipment!D:D)
=XLOOKUP(E2, Item!A:A, Item!D:D)
=YEAR(H2)&"-Q"&ROUNDUP(MONTH(H2)/3,0)
```

**Step 5. Total the standard cost.** PivotTable from ShipmentLine: ItemGroup in **Filters** (Furniture), Quarter in **Rows**, Sum of ExtendedStandardCost in **Values**.

**Check:** the totals are 2026 Q3 $2,459,120.72 on 864 lines; 2026 Q4 $2,475,813.68 on 866 lines.

**Step 6. Total the ledger side.** The same GLEntry PivotTable with AccountID set to 50 (account 5010). The Shipment row's debits are the cost of the shipments; compare it with Step 5.

**Check:** the Shipment debits are $2,459,120.72 and $2,475,813.68, and the differences $0.00 and $0.00. The same PivotTable shows other rows, which Step 8 explains.

### Phase 3: The table and what it means

**Step 7. Build the reconciliation table.** A model table for the appendix:

| Quarter | Invoice lines | Sum of LineTotal | Ledger credits, 4010 from SalesInvoice | Difference |
|---|---:|---:|---:|---:|
| 2026 Q3 | 868 | $4,283,322.86 | $4,283,322.86 | $0.00 |
| 2026 Q4 | 864 | $4,156,787.84 | $4,156,787.84 | $0.00 |

| Quarter | Shipment lines | Standard cost | Ledger debits, 5010 from Shipment | Difference |
|---|---:|---:|---:|---:|
| 2026 Q3 | 864 | $2,459,120.72 | $2,459,120.72 | $0.00 |
| 2026 Q4 | 866 | $2,475,813.68 | $2,475,813.68 | $0.00 |

![A mock of the reconciliation table of the appendix, as a student's worksheet would show it.](../figures/case-part-1/IF-C1-4-A.pdf)

**Step 8. Say what agreement shows, and what it does not.** Agreement to the cent shows that the Furniture invoice lines and shipment lines reached the ledger in full in both quarters, at the same amounts, so either source can support the analysis. It leaves three things open:

a. Whether every Furniture sale was invoiced. In 2026 Q3 every Furniture shipment line has an invoice line. In 2026 Q4, 4 lines shipped in its last month have none: their standard cost of $18,453.55 sits in the cost account without revenue, and at their order prices they would bill $34,792.96.
b. Whether the documents are right: the prices, the dates and the quantities. Requirement 3's findings are the kind of evidence needed.
c. Whether revenue and cost fall in the same quarter. Revenue follows the invoice date and cost the shipment date. In 2026 Q3, 6 of the lines invoiced ($32,647.50) shipped in an earlier quarter; in 2026 Q4, 2 ($6,640.61).

**Step 9. Name the other source document types on the cost account.** Remove the filters on year and period and read the SourceDocumentType rows of account 5010:

| Source document type | Ledger rows | Direction | Meaning |
|---|---:|---|---|
| Shipment | 10,200 | Debits | Cost of goods shipped |
| SalesReturn | 244 | Credits | Cost relieved when goods come back |
| JournalEntry | 3 | Credits | The year-end closes, one a fiscal year |

**Check:** the case's reconciliation covers shipments only, so a margin built from the ledger must decide about the other two types. Returns reduce the cost in 2026 Q3 by $31,867.81 and in 2026 Q4 by $25,752.61; the close is a Requirement 5 matter. **Watch for:** a student who stops at "the totals agree" and does not name the other two types.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Furniture invoice lines, 2026 Q3; 2026 Q4 | $4,283,322.86; $4,156,787.84 | Step 2 |
| Ledger credits to 4010 from SalesInvoice | $4,283,322.86; $4,156,787.84 | Step 3 |
| Furniture shipment lines at standard cost | $2,459,120.72; $2,475,813.68 | Step 5 |
| Ledger debits to 5010 from Shipment | $2,459,120.72; $2,475,813.68 | Step 6 |
| Differences, revenue and cost | Zero in every cell | Steps 3 and 6 |
| Return credits to 5010 | $31,867.81; $25,752.61 | Step 9 |
| Furniture shipment lines with no invoice line | 0; 4 | Step 8 |

> **Instructor notes, Requirement 4:** Furniture invoice lines total \$4,283,322.86 in 2026 Q3 and \$4,156,787.84 in 2026 Q4; SalesInvoice postings to AccountID 42 (4010) match exactly in both quarters. Furniture shipment lines at standard cost total \$2,459,120.72 in Q3 and \$2,475,813.68 in Q4; Shipment postings to AccountID 50 (5010) match exactly. Other sources posting to 5010: SalesReturn (Q3 -\$31,867.81, Q4 -\$25,752.61) and, at year-end, JournalEntry (the closing entry). Agreement shows that the Furniture invoice lines and shipments reached the ledger in full in both quarters, so either source can support the analysis; it does not show that every Furniture sale was invoiced or that the documents themselves are right.

## What a strong answer says

- **The tie-out.** Both sides, both quarters, to the cent, in a table, with the differences shown.
- **What agreement shows.** The documents reached the ledger in full and at the same amounts; either source can support the analysis.
- **What it does not show.** That every sale was invoiced, that the documents are right, and that revenue and cost match in time; the best answers name the unbilled Q4 shipments.
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
| What agreement shows | 20 | Shows delivery to the ledger; names at least two things left open | "Reliable" with no limit |
| Other sources on the cost account | 10 | Shipment, SalesReturn and JournalEntry with their direction | One or two named |
| The table | 10 | A clean table fit for the appendix | Totals scattered in the workbook |

## Extensions and discussion questions

- Find the Furniture shipment lines of 2026 Q4 with no invoice line, and say what you would ask the sales department.
- Discuss: the sub-ledger and the ledger come from the same system. What independent evidence would make the tie-out stronger?
- Discuss: Requirement 5 uses the ledger alone. What does the reconciliation let the student say about using it?
