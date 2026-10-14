# Exercise 4.4: Freight Billed Versus Freight Incurred

| | |
|---|---|
| Unit | Chapter 4: Excel Essentials for Accounting Analytics |
| Item | Exercise 4.4 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheets Ex 4.4, Ex 4.4 Shipment and Ex 4.4 SalesOrder |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The exercise brings a second Table into the workbook, joins it with a lookup and answers a managerial question: does billed freight cover freight paid to carriers? It practices Power Query loading, a calculated column from XLOOKUP, a formula rule, a mixed-reference grid whose columns are not adjacent, and a slicer with SUBTOTAL. The finding is a distinction: freight absorbed by design on one set of terms, and a small shortfall on the other. The analytics type is descriptive.

By the end, students can:

- load two Tables with Power Query as worksheets and bring one column across with a lookup (outcome 2);
- write a rule and a count that agree (outcomes 4 and 5);
- fill a grid with mixed references and a locked Table column, and notice when columns are not adjacent (outcome 3);
- compare groups with a slicer and SUBTOTAL, and interpret the result (outcomes 4 and 1).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S1 M8 T3 to T4 (data mining and analysis); IMA Data Analysis, and Strategic Cost Management; IFAC IES 2 (b), management accounting, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of Charles River Furniture Analysis.xlsx, with CharlesRiver.xlsx where the queries point. XLOOKUP needs Excel for Microsoft 365 or a recent perpetual version; check students' versions.
- **Data conditions.** The FreightTerms values are Prepaid and Prepaid and Add. Every shipment's sales order is found, so no lookup fails. Prepaid shipments bill no freight, and Prepaid and Add shipments bill most but not all of what the carrier charged. Shipments and sales orders are 9,707 and 5,819 rows.
- **The Table order matters.** In the Shipment Table FreightCost is column J, BillableFreightAmount K, then the two new columns FreightTerms (L) and FreightMargin (M). The grid's amounts are not adjacent, so a fill across fails in one column.
- **Load choice.** Both Tables load as worksheets. A plain Close & Load sends them to the Data Model.

## How to run it

Individual or pairs, about 75 minutes: 15 on loading (requirement 1), 10 on the columns (2), 10 on the rule and counts (3), 15 on the grid (4), 10 on the slicer (5) and 15 on the interpretation (6). Hold back the hint about the grid's columns until a student reads a zero in the last column. Collect the workbook and the paragraph.

## Step-by-step solution

### Requirement (1): Load the Tables

**Step 1. Import Shipment and SalesOrder.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx and click **Import**.
b. In the **Navigator**, select the **Select multiple items** check box, select **T14_Shipment** and **T9_SalesOrder**, and click **Transform Data**.
c. In the **Queries** pane rename the queries `Shipment` and `SalesOrder`.
d. Choose **Home > Close & Load > Close & Load To**, select **Table** and **New worksheet**, and click **OK**.
e. Rename the two worksheets `Ex 4.4 Shipment` and `Ex 4.4 SalesOrder`.

**Check:** the **Table Name** box shows Shipment with 9,707 rows, and SalesOrder with 5,819. **Watch for:** a plain **Close & Load**. No worksheets appear, and the student must use **Data > Queries & Connections**, right-click each query and choose **Load To**.

### Requirement (2): Two calculated columns

**Step 2. Bring FreightTerms across.** In the first empty cell right of the Shipment Table (column L) type `FreightTerms` and press Enter. In the first data cell enter:

```
=XLOOKUP([@SalesOrderID],SalesOrder[SalesOrderID],SalesOrder[FreightTerms])
```

**Step 3. Add FreightMargin.** In the next column type `FreightMargin` and enter `=[@BillableFreightAmount]-[@FreightCost]`. Format it with two decimals.

**Check:** no #N/A appears in FreightTerms, and a Prepaid shipment's FreightMargin is minus its FreightCost.

### Requirement (3): Highlight and count the shortfalls

**Step 4. Add the rule and the counts.**

a. Select the shipment data cells with the first data cell active, and choose **Home > Conditional Formatting > New Rule**.
b. Select **Use a formula to determine which cells to format** and enter `=$M2<0`. Choose a fill.
c. On `Ex 4.4` enter `=COUNTIFS(Shipment[FreightMargin],"<0")` and, beside it, `=SUMIFS(Shipment[FreightMargin],Shipment[FreightMargin],"<0")`.

**Check:** 7,632 shipments, with a total FreightMargin of -$868,490.27. **Watch for:** the rule written with a structured reference, which a rule cannot use, and confusion with the grid's overall FreightMargin, which is smaller because shipments above cost offset some.

### Requirement (4): The grid by FreightTerms

**Step 5. Build the grid with mixed references.**

a. In A9 to E9 type `FreightTerms`, `Shipments`, `FreightCost`, `BillableFreightAmount` and `FreightMargin`, and in A10 and A11 type the two terms exactly as the Table spells them.
b. In B10 enter the count below. In C10 enter the SUMIFS below, then copy it, paste it into D10 and E10, and change the sum column by hand to BillableFreightAmount and FreightMargin:

```
=COUNTIFS(Shipment[[FreightTerms]:[FreightTerms]],$A10)
=SUMIFS(Shipment[FreightCost],Shipment[[FreightTerms]:[FreightTerms]],$A10)
```

c. Copy B10:E10 down to row 11. Add a Total row, an Entire Shipment Table row (`=ROWS(Shipment[ShipmentID])` and `=SUM(Shipment[FreightCost])`, and so on) and a Difference row that rounds the first less the second.

**Check:** the Difference row is zero in all four columns, and the grid reads as in the Expected results. **Watch for:** a fill across from FreightCost. It moves to BillableFreightAmount, then to FreightTerms, a text column, so the last column shows 0.

### Requirement (5): The slicer and SUBTOTAL

**Step 6. Compare the average cost under each term.**

a. Choose **Table Design > Insert Slicer** on the Shipment Table and select **FreightTerms**.
b. Enter `=SUBTOTAL(103,Shipment[ShipmentID])` and `=SUBTOTAL(101,Shipment[FreightCost])`. Function 101 averages the rows in view.
c. Click each term in turn, record the two results, and click **Clear Filter**. An AVERAGEIFS beside the recorded values gives the same averages without the slicer.

**Check:** each term gives the shipments and the average cost in the Expected results.

### Requirement (6): The interpretation

**Step 7. Write four or five sentences.** A model answer: of the 9,707 shipments, 5,024 are on Prepaid terms and bill nothing, so a FreightMargin of -$849,739.09 is freight absorbed by design, 99.3% of the total. The 4,683 Prepaid and Add shipments bill freight, which covers 99.0% of their carrier cost in total, a shortfall of $6,391.63, spread across 2,608 shipments billed below cost and 2,070 above it. The conversation about freight terms should start with which orders get Prepaid terms.

**Check:** the answer separates absorbed freight from shortfall, and does not call the Prepaid margin an error.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Prepaid: shipments; FreightCost; BillableFreightAmount; FreightMargin | 5,024; $849,739.09; $0.00; -$849,739.09 | Step 5 |
| Prepaid and Add: shipments; FreightCost; BillableFreightAmount; FreightMargin | 4,683; $627,658.97; $621,267.34; -$6,391.63 | Step 5 |
| Total FreightMargin | -$856,130.72 | Step 5 |
| Shipments below zero; their total | 7,632; -$868,490.27 | Step 4 |
| Average FreightCost under each term | $169.14; $134.03 | Step 6 |
| Prepaid and Add: above cost; below cost; at cost | 2,070; 2,608; 5 | Step 4 |
| Prepaid and Add: billed over cost, in total; average of the shipments' ratios | 99.0%; 95.7% | Step 7 |

![A mock of the freight grid on Ex 4.4 with its total, entire-Table and difference rows, and the FreightTerms slicer beside the SUBTOTAL cells.](../figures/chapter-04-excel-essentials/IF-04-4-A.pdf)

> **Instructor notes, Exercise 4.4:** 9,707 shipments. FreightTerms values are Prepaid (5,024 shipments) and Prepaid and Add (4,683). Every Prepaid shipment has BillableFreightAmount 0, so all are negative by design: FreightMargin -849,739.09 (average FreightCost 169.14). Prepaid and Add shipments bill freight: 2,070 above cost, 2,608 below, 5 equal; FreightMargin -6,391.63 (average FreightCost 134.03; billed freight totals about 99 percent of cost, while the shipments' ratios average about 96 percent). Total FreightMargin -856,130.72; 7,632 negative shipments. FreightCost ranges from 23.24 to 873.95. The finding: freight is absorbed by design on Prepaid orders, and freight billed under Prepaid and Add recovers most but not all of the carrier cost.

## What a strong answer says

- **Requirement (3).** The count and the rule agree, and the student says which shipments the rule marks.
- **Requirement (4).** A grid that ties to the entire Table, with a lock on FreightTerms.
- **Requirement (6).** Two findings, not one: freight absorbed by design on Prepaid, and a small shortfall on Prepaid and Add. The totals' coverage and the average of the shipments' ratios are different measures and can differ.

A weak answer reports a loss on 7,632 shipments without separating the two terms.

## Common mistakes and how to respond

- **Both Tables in the Data Model.** *Symptom:* no worksheets. *Response:* **Load To** from **Queries & Connections**.
- **A lookup on the wrong key.** *Symptom:* #N/A or terms in the wrong rows. *Response:* the key is SalesOrderID in both Tables.
- **A rule that does not match the count.** *Cause:* a wrong active cell or column letter. *Response:* click a shaded row and read the rule in **Manage Rules**.
- **A zero in the last grid column.** *Cause:* a fill across through a text column. *Response:* read the formula bar of E10.
- **A loss reported for all shipments.** *Response:* ask what terms mean on Prepaid orders.
- **Two recovery rates read as an error.** *Response:* one divides totals, the other averages the shipments' own ratios.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: loading | 10 | Both Tables as worksheets, named Shipment and SalesOrder | Loaded to the Data Model |
| Requirement 2: columns | 15 | A lookup with no errors and the margin formula | Values pasted |
| Requirement 3: rule and counts | 15 | A rule on the margin column and counts that agree with it | Rule without counts |
| Requirement 4: grid | 20 | Mixed references, locked FreightTerms, totals tied to the Table | Hand-edited, or no tie-out |
| Requirement 5: slicer | 15 | SUBTOTAL average for each term, recorded | One term only |
| Requirement 6: interpretation | 25 | Absorbed by design versus shortfall, with the numbers | A single conclusion |

## Extensions and discussion questions

- Add the carrier or warehouse from the Shipment Table to the grid and see where the shortfall concentrates.
- Replace the hand-edited sum columns with a formula that reads its column from the header, and say what you gained.
- Discuss: why might a company offer Prepaid terms knowing it absorbs the freight?
- Discuss: Chapter 5 combines tables with Power Query merges. What would a merge have done that XLOOKUP did here?
