# Exercise 3.3: Mapping the Charles River Manufacturing Group

| | |
|---|---|
| Unit | Chapter 3: The Accounting Data Environment |
| Item | Exercise 3.3 |
| Perspective | Managerial accounting |
| Tools | Workbook browsing and written work |
| Time | About 75 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

A cost analyst asks three questions of the manufacturing data: what goes into a product, what was made, and what the difference between plan and result cost. The exercise has students answer each from the diagram and the workbook, and then judge whether the data can support a product cost project. The surprises are useful: one table plays two roles in the bill of material, the planned and the completed quantities always agree, and the variance has to be read as cost and not as output. The analytics type is descriptive.

By the end, students can:

- name the production tables and say what a row of each records (chapter outcome 3);
- follow ParentItemID, BOMID and ComponentItemID from a product to its components, and explain why Item sits at both ends (outcome 5);
- say what the data allow a cost analyst to compare, and which table holds the variance;
- state which tables and columns give the variance of one product, and what the data do not store;
- write a one-page suitability memo.

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S2 M4 (information technology and IT controls); IMA Data Literacy, and Operational Knowledge; IFAC IES 2 (b), management accounting, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.2.

## Before you assign

- Students need Figure 3.8, the workbook, and Tutorial 3.1's reading skills. Chapter 1 introduced the group, and its Exercise 1.3 evaluated it for cost analysis, so tell students to build on that and not to repeat it.
- The exercise relies on these conditions. There are 88 manufactured items, and 83 have a bill of material, one each; the other 5 are discontinued and were never made. Components are packaging and raw materials, and no component is itself a parent, so every bill has one level. A work order has a close exactly when its status is Closed, so 670 work orders have no close yet. The quantity completed equals the planned quantity on every closed work order.
- Do Step 3 yourself first: the roll-up needs the scrap factor. A student who omits it finds a material cost that is too low, and this is the exercise's best check.

## How to run it

Individual work, or pairs for requirements (2) and (4). For about 75 minutes: 15 on the tables (requirement 1), 20 on the bill (requirement 2), 15 on production and closes (requirement 3), 10 on the variance (requirement 4) and 15 on the memo (requirement 5).

**Hints.** For requirement (2), if a student cannot see why Item appears twice, ask which column of BillOfMaterialLine holds the component, and which table holds its name. For requirement (4), ask which table has a variance in dollars. **Collect** the memo and the roll-up.

## Step-by-step solution

### Requirement (1): Name the production tables

**Step 1. List the tables of Figure 3.8 and say what one row records.**

| Table | One row records | Rows |
|---|---|---:|
| BillOfMaterial | The recipe of one manufactured item: version, status | 83 |
| BillOfMaterialLine | One component of a recipe, with quantity per unit and scrap factor | 300 |
| WorkOrder | An order to make an item: planned quantity, dates, status, cost center | 13,668 |
| WorkOrderOperation | One step of a work order, with its work center and planned hours | 50,969 |
| MaterialIssue and its lines | Components taken from stock to a work order, valued at standard cost | 19,240; 70,126 |
| ProductionCompletion and its lines | Finished units received, valued at standard material and conversion cost | 17,352; 17,352 |
| WorkOrderClose | The variances posted when a work order closes | 12,998 |

**Check:** each description ties the table to cost analysis (the recipe, the cost of materials, the output, the variance). The requirement then asks for the Manufacturing tables that the focused diagram leaves out. They are Routing, RoutingOperation, WorkCenter, WorkCenterCalendar, and WorkOrderOperationSchedule, which hold the routes, the work centers and their capacity. A strong student adds that LaborTimeEntry, in the Payroll and Time group, holds the actual hours by work order.

### Requirement (2): Follow the path from product to components

**Step 2. Start at the Item table and follow the keys.** The model product is FUR-BKC-0019, Harbor Bookcase Acacia Whitewash 60 in, in the Furniture group.

a. On **BillOfMaterial**, filter ParentItemID for 65. There is one row: BOMID 24, version 1, status active.
b. On **BillOfMaterialLine**, filter BOMID for 24.
c. For each line, look up ComponentItemID in **Item**.

| Line | Component | Group | StandardCost | QuantityPerUnit | ScrapFactorPct |
|---:|---|---|---:|---:|---:|
| 1 | RAW-LIN-0002 Linen Fabric Roll | Raw Materials | $50.32 | 2.76 | 0.0202 |
| 2 | RAW-CTN-0007 Cotton Fabric Roll | Raw Materials | $25.36 | 2.94 | 0.0032 |
| 3 | PKG-PLW-0004 Pallet Wrap Large | Packaging | $3.25 | 1.04 | 0.0033 |

![The path from a finished product to its components, with the Item table at both ends.](../figures/chapter-03-accounting-data-environment/IF-03-3-A.pdf)

**Check:** the same Item table appears at both ends. ParentItemID and ComponentItemID are two foreign keys to ItemID, so a product and its components are rows of one table, and the bill says which row is made of which. **Watch for:** a student who looks for a Component table.

**Step 3. Roll up the material cost.** For each line multiply QuantityPerUnit by one plus ScrapFactorPct and by the component's StandardCost, and add the lines. The model product comes to $219.88. The product's StandardCost is $300.15 and its StandardConversionCost $80.27, so StandardCost less conversion is $219.88.

**Check:** the roll-up equals the material part of the standard cost within a cent or two, and equals the standard material cost per unit on the product's completion lines ($219.88). The same holds for all 83 manufactured items that have a bill. Without the scrap factor the model product comes to $216.82, which does not reproduce it. A cost analyst uses the path to calculate the material cost of any product, and to see which components drive it. **Watch for:** the roll-up without the scrap factor.

### Requirement (3): Read the production records

**Step 4. Look at the tables that record what happened.**

a. On **WorkOrder**, count the rows by Status.
b. On **ProductionCompletion**, count the completions for one work order.
c. On **WorkOrderClose**, read the variance columns of one row.

| Status | Work orders | With a close |
|---|---:|---:|
| Closed | 12,998 | 12,998 |
| Released | 558 | 0 |
| Completed | 85 | 0 |
| In Progress | 27 | 0 |

**Check:** a close exists exactly for the Closed work orders. A work order can be completed in several parts, so ProductionCompletion has more rows than there are work orders that were produced: 9,270 work orders have one completion, others have up to several, and 558 have none yet. Each completion has exactly one line. The planned quantity of a closed work order equals the quantity completed, so the quantity comparison finds nothing; the information for comparing plan and result is in dollars. The completion lines hold the standard cost released (material, labor, overhead, conversion, total), and the close holds the variance: MaterialVarianceAmount, DirectLaborVarianceAmount, OverheadVarianceAmount, ConversionVarianceAmount and TotalVarianceAmount. **Watch for:** the conclusion that no variance exists because the quantities agree.

### Requirement (4): Find the variance of a product

**Step 5. Join the close to the product.** The path is WorkOrderClose to WorkOrder through WorkOrderID, and WorkOrder to Item through ItemID. Sum the variance columns by product.

For the model product, the 175 closes total $50,342.64: material $3,818.85, direct labor -$10,744.73 and overhead $57,268.52, with conversion $46,523.79. A negative amount is a favorable variance. The completions behind them are 1,490.56 units, so the variance is $33.77 a unit, against a standard cost of $300.15.

**Check:** a positive amount is an unfavorable variance, because a close's total is the net debit that it posts to the manufacturing variance account. The total is the material part plus the conversion part, and the conversion part is labor plus overhead, on every close. The material variance is the material issued at standard cost less the standard material of the units completed, so it measures usage and not price. The data do not store an actual cost per unit. The close gives the differences from standard for materials used, labor and overhead; price differences on purchased materials are posted separately, so an actual cost per unit has to be assembled from them. The hours behind the labor variance are in LaborTimeEntry (the model product's work orders have 714 entries), joined by WorkOrderID, a bridge key to the Payroll and Time group. **Watch for:** the conversion variance added to the labor and overhead variances, which counts them twice.

### Requirement (5): Write the memo

**Step 6. Outline one page.** A model memo has four parts: what the group holds (the recipe, the work, the completions, the closes), what a product cost project can do with it (reconcile standard cost to the bill, rank variances by product and by cause), what limits it, and a recommendation. The limits are that 670 work orders have no close, so recent production has no variance yet; that the variance is recorded per work order and not per component price; that actual hours live in another group; and that routings and work centers are outside the diagram.

**Check:** the memo gives a verdict on suitability (suitable for standard-cost and variance analysis, with named limits) and names the tables.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Manufactured items; with a bill of material | 88; 83 | Step 2 |
| Model product's material roll-up; with no scrap factor | $219.88; $216.82 | Step 3 |
| Model product's StandardCost; StandardConversionCost | $300.15; $80.27 | Step 3 |
| Work orders; closed work orders | 13,668; 12,998 | Step 4 |
| Work orders with no close yet | 670 | Step 4 |
| Model product: closes; total variance | 175; $50,342.64 | Step 5 |
| Model product: material; labor; overhead variance | $3,818.85; -$10,744.73; $57,268.52 | Step 5 |

## What a strong answer says

- **Requirement (1).** Each table of the diagram with what a row records, the 5 Manufacturing tables the diagram leaves out, and LaborTimeEntry for the actual hours.
- **Requirement (2).** The path in order, the bill reconciled to the standard cost with the scrap factor, and Item named as a parent and a component.
- **Requirement (3).** Planned and completed quantities that agree, completions in parts, and the variance columns of the close as the place where plan and result differ.
- **Requirement (4).** The join path, the sign convention, and what is derived and what is stored.
- **Requirement (5).** A verdict with limits.

A weak answer lists tables, looks for a component table, or says that the database has no variance because the quantities agree.

## Common mistakes and how to respond

- **The scrap factor left out.** *Symptom:* a material cost below the standard. *Response:* ask what a ScrapFactorPct column is for.
- **No second Item.** *Symptom:* "components are not in the database". *Response:* ask which table holds the name of a component.
- **Quantity read as the variance.** *Symptom:* "no variance, because completed equals planned". *Response:* ask where the dollars are.
- **Open work orders counted.** *Symptom:* a variance for a work order with no close. *Response:* ask what the Status column says.
- **A positive variance read as favorable.** *Response:* ask which account the close debits.
- **Standard cost read as actual.** *Response:* ask what the close adds to it.
- **Completions mistaken for work orders.** *Symptom:* a count that exceeds the work orders. *Response:* ask whether a work order can be completed in parts.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the tables | 15 | Every table of the diagram with what a row records, and the tables it leaves out | Names without roles |
| Requirement 2: the path | 25 | The keys in order, the roll-up with the scrap factor, and Item at both ends explained | The path without the roll-up |
| Requirement 3: the records | 20 | Plan and result tables, partial completions, the variance columns | Tables without the comparison |
| Requirement 4: the variance | 25 | The join, the sign, and what is derived | The variance without the path |
| Requirement 5: the memo | 15 | A verdict, named tables and limits | A summary with no verdict |

## Extensions and discussion questions

- Find the manufactured items with no bill of material and say why none has a work order.
- Rank the products by total variance. Is the largest the one with the most work orders?
- Discuss: variances are posted at the close. What does that mean for the variance of the work orders still open at a year-end? (Chapters 9 and 10 take up the account.)
- Discuss: the material variance is a usage variance, not a price variance. Where would a purchase price variance live? (Exercise 3.1 found it in the purchase postings.)
