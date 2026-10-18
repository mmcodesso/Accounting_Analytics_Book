---
note: ch03.ex3
title: Mapping the Charles River Manufacturing Group
kind: exercise
number: '3.3'
unit: '3'
perspective: managerial
tool: conceptual
minutes: 75
solution: ''
figures:
  - id: IF-03-3-A
    kind: diagram
    purpose: The path from a finished product to its components, with the Item table at both ends.
    shows: On the left an Item box holding the model product (its code and name) with ItemID. An arrow labeled ParentItemID leads to a BillOfMaterial box, an arrow labeled BOMID leads to a BillOfMaterialLine box listing the model product's component lines, and an arrow labeled ComponentItemID leads back to a second Item box on the right that lists the component items with their standard costs. The two Item boxes are drawn identically, joined by a dotted line and a note that they are one table in two roles. Under the lines, a small table works out quantity per unit times one plus the scrap factor times the component cost for each line, and a strip adds the lines up to the material cost and then to the standard cost with the conversion cost.
    data: The model product of this guide, its bill, its component lines and the roll-up of Step 3.
---
# Exercise 3.3: Mapping the Charles River Manufacturing Group

{{ header() }}

## Purpose and learning outcomes

A cost analyst asks three questions of the manufacturing data: what goes into a product, what was made, and what the difference between plan and result cost. The exercise has students answer each from the diagram and the workbook, and then judge whether the data can support a product cost project. The surprises are useful: one table plays two roles in the bill of material, the planned and the completed quantities always agree, and the variance has to be read as cost and not as output. The analytics type is descriptive.

By the end, students can:

- name the production tables and say what a row of each records (outcome 3);
- follow ParentItemID, BOMID and ComponentItemID from a product to its components, and explain why Item sits at both ends (outcome 5);
- say what the data allow a cost analyst to compare, and which table holds the variance;
- state which tables and columns give the variance of one product, and what the data do not store;
- write a one-page suitability memo.

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S2 M4 (information technology and IT controls); IMA Data Literacy, and Operational Knowledge; IFAC IES 2 (b), management accounting, and IES 3 (a), evaluating data from several sources; AACSB A5 part 5.2.

## Before you assign

- Students need Figure 3.8, the workbook, and Tutorial 3.1's reading skills. Chapter 1 introduced the group, and its Exercise 1.3 evaluated it for cost analysis, so tell students to build on that and not to repeat it.
- The exercise relies on these conditions. There are {{ manufactured }} manufactured items, and {{ with_bom }} have a bill of material, one each; the other {{ no_bom }} are discontinued and were never made. Components are {{ components }}, and no component is itself a parent, so every bill has one level. A work order has a close exactly when its status is Closed, so {{ open_orders|count }} work orders have no close yet. The quantity completed equals the planned quantity on every closed work order.
- Do Step 3 yourself first: the roll-up needs the scrap factor. A student who omits it finds a material cost that is too low, and this is the exercise's best check.

## How to run it

Individual work, or pairs for requirements (2) and (4). For about 75 minutes: 15 on the tables (requirement 1), 20 on the bill (requirement 2), 15 on production and closes (requirement 3), 10 on the variance (requirement 4) and 15 on the memo (requirement 5).

**Hints.** For requirement (2), if a student cannot see why Item appears twice, ask which column of BillOfMaterialLine holds the component, and which table holds its name. For requirement (4), ask which table has a variance in dollars. **Collect** the memo. A numerical roll-up is an optional extension (Step 3 shows it).

## Step-by-step solution

### Requirement (1): Name the production tables

**Step 1. List the tables of Figure 3.8 and say what one row records.**

| Table | One row records | Rows |
|---|---|---:|
| BillOfMaterial | The recipe of one manufactured item: version, status | {{ rows.BillOfMaterial|count }} |
| BillOfMaterialLine | One component of a recipe, with quantity per unit and scrap factor | {{ rows.BillOfMaterialLine|count }} |
| WorkOrder | An order to make an item: planned quantity, dates, status, cost center | {{ rows.WorkOrder|count }} |
| WorkOrderOperation | One step of a work order, with its work center and planned hours | {{ rows.WorkOrderOperation|count }} |
| MaterialIssue and its lines | Components taken from stock to a work order, valued at standard cost | {{ rows.MaterialIssue|count }}; {{ rows.MaterialIssueLine|count }} |
| ProductionCompletion and its lines | Finished units received, valued at standard material and conversion cost | {{ rows.ProductionCompletion|count }}; {{ rows.ProductionCompletionLine|count }} |
| WorkOrderClose | The variances posted when a work order closes | {{ rows.WorkOrderClose|count }} |

**Check:** each description ties the table to cost analysis (the recipe, the cost of materials, the output, the variance). The requirement then asks for the Manufacturing tables that the focused diagram leaves out. They are {{ omitted }}, which hold the routes, the work centers and their capacity. A strong student adds that LaborTimeEntry, in the Payroll and Time group, holds the actual hours by work order.

### Requirement (2): Follow the path from product to components

**Step 2. Start at the Item table and follow the keys.** The model product is {{ item.code }}, {{ item.name }}, in the {{ item.group }} group.

a. On **BillOfMaterial**, filter ParentItemID for {{ item.id }}. There is one row: BOMID {{ item.bom }}, version {{ item.version }}, status {{ item.status }}.
b. On **BillOfMaterialLine**, filter BOMID for {{ item.bom }}.
c. For each line, look up ComponentItemID in **Item**.

| Line | Component | Group | StandardCost | QuantityPerUnit | ScrapFactorPct |
|---:|---|---|---:|---:|---:|
{% for x in lines %}
| {{ x.line }} | {{ x.code }} {{ x.name }} | {{ x.group }} | ${{ x.cost|money }} | {{ x.quantity|num(2) }} | {{ x.scrap|num(4) }} |
{% endfor %}

{{ figure('IF-03-3-A') }}

**Check:** the same Item table appears at both ends. ParentItemID and ComponentItemID are two foreign keys to ItemID, so a product and its components are rows of one table, and the bill says which row is made of which. **Watch for:** a student who looks for a Component table.

**Step 3. Roll up the material cost.** For each line multiply QuantityPerUnit by one plus ScrapFactorPct and by the component's StandardCost, and add the lines. The model product comes to ${{ material|num(2) }}. The product's StandardCost is ${{ item.cost|money }} and its StandardConversionCost ${{ item.conversion|money }}, so StandardCost less conversion is ${{ (item.cost - item.conversion)|num(2) }}.

**Check:** the roll-up equals the material part of the standard cost within a cent or two. On the completion records, the sum of ExtendedStandardMaterialCost over the sum of QuantityCompleted comes to the same, ${{ per_unit|num(2) }}, though a single completion line's ratio can differ, because each extended amount is rounded to the cent (most for a line of a fraction of a unit). The same holds for all {{ n_roll }} manufactured items that have a bill. Without the scrap factor the model product comes to ${{ noscrap|num(2) }}, which does not reproduce it. A cost analyst uses the path to calculate the material cost of any product, and to see which components drive it. **Watch for:** the roll-up without the scrap factor.

### Requirement (3): Read the production records

**Step 4. Look at the tables that record what happened.**

a. On **WorkOrder**, count the rows by Status.
b. On **ProductionCompletion**, count the completions for one work order.
c. On **WorkOrderClose**, read the variance columns of one row.

| Status | Work orders | With a close |
|---|---:|---:|
{% for s in statuses %}
| {{ s[0] }} | {{ s[1]|count }} | {{ s[2]|count }} |
{% endfor %}

**Check:** a close exists exactly for the Closed work orders. A work order can be completed in several parts, so ProductionCompletion has more rows than there are work orders that were produced: {{ one_completion|count }} work orders have one completion, others have up to several, and {{ no_completion|count }} have none yet. Each completion has exactly one line. The planned quantity of a closed work order equals the quantity completed, so the quantity comparison finds nothing; the information for comparing plan and result is in dollars. The completion lines hold the standard cost released (material, labor, overhead, conversion, total), and the close holds the variance: MaterialVarianceAmount, DirectLaborVarianceAmount, OverheadVarianceAmount, ConversionVarianceAmount and TotalVarianceAmount. **Watch for:** the conclusion that no variance exists because the quantities agree.

### Requirement (4): Find the variance of a product

**Step 5. Join the close to the product.** The path is WorkOrderClose to WorkOrder through WorkOrderID, and WorkOrder to Item through ItemID. Sum the variance columns by product.

For the model product, the {{ v.closes }} closes total ${{ v.total|money }}: material {{ sm(v.material) }}, direct labor {{ sm(v.labor) }} and overhead {{ sm(v.overhead) }}, with conversion {{ sm(v.conversion) }}. A negative amount is a favorable variance. The completions behind them are {{ v.units|num(2) }} units, so the variance is ${{ v.per_unit|num(2) }} a unit, against a standard cost of ${{ item.cost|money }}.

**Check:** a positive amount is an unfavorable variance, because a close's total is the net debit that it posts to the manufacturing variance account. The total is the material part plus the conversion part, and the conversion part is labor plus overhead, on every close. The material variance is the material issued at standard cost less the standard material of the units completed, so it measures usage and not price. The data do not store an actual cost per unit. The close gives the differences from standard for materials used, labor and overhead; price differences on purchased materials are posted separately, so an actual cost per unit has to be assembled from them. The hours behind the labor variance are in LaborTimeEntry (the model product's work orders have {{ labor_entries|count }} entries), joined by WorkOrderID, a bridge key to the Payroll and Time group. **Watch for:** the conversion variance added to the labor and overhead variances, which counts them twice.

### Requirement (5): Write the memo

**Step 6. Outline one page.** A model memo has four parts: what the group holds (the recipe, the work, the completions, the closes), what a product cost project can do with it (reconcile standard cost to the bill, rank variances by product and by cause), what limits it, and a recommendation. The limits are that {{ open_orders|count }} work orders have no close, so recent production has no variance yet; that the variance is recorded per work order and not per component price; that actual hours live in another group; and that routings and work centers are outside the diagram.

**Check:** the memo gives a verdict on suitability (suitable for standard-cost and variance analysis, with named limits) and names the tables.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Manufactured items; with a bill of material | {{ manufactured }}; {{ with_bom }} | Step 2 |
| Model product's material roll-up; with no scrap factor | ${{ material|num(2) }}; ${{ noscrap|num(2) }} | Step 3 |
| Model product's StandardCost; StandardConversionCost | ${{ item.cost|money }}; ${{ item.conversion|money }} | Step 3 |
| Work orders; closed work orders | {{ rows.WorkOrder|count }}; {{ closes|count }} | Step 4 |
| Work orders with no close yet | {{ open_orders|count }} | Step 4 |
| Model product: closes; total variance | {{ v.closes }}; ${{ v.total|money }} | Step 5 |
| Model product: material; labor; overhead variance | {{ sm(v.material) }}; {{ sm(v.labor) }}; {{ sm(v.overhead) }} | Step 5 |

## What a strong answer says

- **Requirement (1).** Each table of the diagram with what a row records, the {{ n_omitted }} Manufacturing tables the diagram leaves out, and LaborTimeEntry for the actual hours.
- **Requirement (2).** The path in order, the calculation explained with the scrap factor, and Item named as a parent and a component. A numerical roll-up that reconciles to the standard cost is a plus.
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
| Requirement 2: the path | 25 | The keys in order, a correct explanation of the calculation (QuantityPerUnit times one plus ScrapFactorPct times the component's StandardCost), and Item at both ends explained | The path with an incomplete explanation of the calculation or of Item's two roles |
| Requirement 3: the records | 20 | Plan and result tables, partial completions, the variance columns | Tables without the comparison |
| Requirement 4: the variance | 25 | The join, the sign, and what is derived | The variance without the path |
| Requirement 5: the memo | 15 | A verdict, named tables and limits | A summary with no verdict |

## Extensions and discussion questions

- Find the manufactured items with no bill of material and say why none has a work order.
- Rank the products by total variance. Is the largest the one with the most work orders?
- Discuss: variances are posted at the close. What does that mean for the variance of the work orders still open at a year-end? (Chapters 9 and 10 take up the account.)
- Discuss: the material variance is a usage variance, not a price variance. Where would a purchase price variance live? (Exercise 3.1 found it in the purchase postings.)
