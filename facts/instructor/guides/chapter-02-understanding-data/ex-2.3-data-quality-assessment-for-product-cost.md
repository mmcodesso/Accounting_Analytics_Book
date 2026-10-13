---
note: ch02.ex3
uses: [ch02.t1]
title: Data Quality Assessment for Product Cost Analysis
kind: exercise
number: '2.3'
unit: '2'
perspective: managerial
tool: conceptual
minutes: 60
solution: ''
figures:
  - id: IF-02-3-A
    kind: excel-mock
    purpose: The WorkOrder worksheet with the Operations helper column of Step 5, filtered to zero.
    shows: The WorkOrder Table with WorkOrderNumber, ItemID, ReleasedDate, ClosedDate and Status visible (other columns hidden) and a helper column headed Operations at the right, filtered to show only the value 0. Three rows remain, with the row numbers in blue because the Table is filtered, each with the status Closed. The formula bar shows the COUNTIFS formula and the status bar shows how many records match the filter.
    data: WorkOrder and WorkOrderOperation, with the COUNTIFS formula of Step 5.
---
# Exercise 2.3: Data Quality Assessment for Product Cost Analysis

{{ header() }}

## Purpose and learning outcomes

A cost analysis stands on three things: a standard cost for each item, a reliable identity for each item, and a complete record of each work order. The exercise tests each in turn. Its main lesson is that a zero, a repeat and a gap each need a reason before they are called errors, and that the reason differs. The tests are descriptive.

By the end, students can:

- explain why a zero standard cost is legitimate for one kind of item and a problem for another (chapter outcome 5);
- decide whether items that share a name are duplicates or distinct, and say what grouping by name would do to a cost figure (outcomes 3 and 5);
- count the child rows of a parent with COUNTIFS and name what a parent with none breaks (outcome 4);
- write a short readiness assessment for product costing.

**Competencies practiced.** CPA Evolution Core S1 M8 T2 and BAR M5 (cost accounting and variance analysis); IMA Data Literacy and Cost Accounting; IFAC IES 2 (b), management accounting, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx and Tutorial 2.1, whose Step 8 introduced the blank ListPrice.
- The exercise relies on these conditions: Item.StandardCost is never blank; a few items have a StandardCost of 0; some Item names appear on more than one item; and a few WorkOrder rows have no WorkOrderOperation rows. WorkOrder has {{ work_orders|count }} rows and WorkOrderOperation {{ operations|count }}, so the COUNTIFS runs without trouble.
- "Appears unreasonable" in requirement (1) is a judgment. Decide before class what you accept: a comparison within the item group and the unit of measure is the model.
- The work orders in requirement (3) are the data's own gap. Students may find the same three that you do, and no others.

## How to run it

Individual work with a pair comparison of requirement (2). For about 60 minutes: 15 on requirement 1, 15 on requirement 2, 15 on requirement 3 and 15 on the assessment.

**Hints.** If a student wants to delete the zero-cost items, ask what Charles River sells them for. If nobody finds the work orders, give the COUNTIFS pattern of Tutorial 2.1 Step 6 and ask which table is the child.

## Step-by-step solution

### Requirement (1): Zero, blank or unreasonable standard costs

**Step 1. Filter StandardCost for zero and for blank.** On **Item**, filter the StandardCost column for 0, then for blank cells.

**Check:** no blank cost, and {{ n_zero }} items at 0:

| ItemCode | ItemName | ItemGroup | ListPrice | Unit |
|---|---|---|---:|---|
{% for r in zero %}
| {{ r[0] }} | {{ r[1] }} | {{ r[2] }} | ${{ r[3]|money }} | {{ r[4] }} |
{% endfor %}

All are Services items sold by the hour, so the zero is by design: Charles River does not carry the consultants' time as an item cost. A margin at standard cost would be the whole price, which a cost analysis must not read as profit. Chapter 6 shows where the cost of the design staff appears.

**Step 2. Compare the costs within their group and unit.** Sort StandardCost from largest to smallest and look at the group of each large value.

| ItemGroup | Items | Lowest cost | Highest cost |
|---|---:|---:|---:|
{% for r in by_group %}
| {{ r[0] }} | {{ r[1] }} | ${{ r[2]|money }} | ${{ r[3]|money }} |
{% endfor %}

**Check:** the largest costs belong to the Services items that are bought by the month (insurance, marketing, research) and to the equipment in the Capex group, where costs in the thousands are expected. The finished goods cost far less than either, and no priced item is priced below its cost. **Watch for:** students who flag the big numbers without asking what the item is.

### Requirement (2): Blank list prices and shared names

**Step 3. Sort the blank list prices by group.** Filter **Item** for a blank ListPrice and read ItemGroup, as in Tutorial 2.1 Step 8.

**Check:** {{ ch02_t1.sizes }}. The {{ ch02_t1.sellable|count }} remaining items are sold. The four design services have a price per hour, and the other items are bought: raw materials, packaging, equipment and operating services.

**Step 4. Find the names shared by more than one item.**

a. In the first free column of **Item**, count the rows with the same name: `=COUNTIFS(C:C,C2)`.
b. Filter the column for values above 1, then sort by ItemName.
c. Compare ItemCode, StandardCost and the lifecycle of the items that share each name.

**Check:** the table holds {{ n_names }} shared names, on {{ n_shared_items }} items. Every pair or group has different codes and different standard costs, so these are distinct items, not duplicate records. For {{ lifecycle }} of the names the items also differ in lifecycle status, so one item may be the successor of another; ask the owner of the item master. For example, {{ widest.name }} appears on {{ widest.codes|length }} items with costs from ${{ widest.low|money }} to ${{ widest.high|money }}.

| ItemCode | StandardCost | Lifecycle |
|---|---:|---|
{% for r in widest.codes %}
| {{ r[0] }} | ${{ r[1]|money }} | {{ r[2] }} |
{% endfor %}

A cost analysis that groups by ItemName averages items that cost up to {{ widest.ratio|num(1) }} times as much as each other, and merges them on the invoice lines of the {{ sold }} shared names that are sold. The key is ItemCode or ItemID. None of the shared names is made on a work order.

### Requirement (3): Work orders with no operation

**Step 5. Count the operations of every work order.**

a. On **WorkOrder**, in the first free column, enter `=COUNTIFS(WorkOrderOperation!B:B,A2)` and copy it down.
b. Filter the column for 0.

**Check:** among {{ work_orders|count }} work orders, {{ n_none }} have none.

| WorkOrderNumber | Status | ReleasedDate | Item |
|---|---|---|---|
{% for w in no_ops %}
| {{ w.number }} | {{ w.status }} | {{ w.released }} | {{ w.item }} |
{% endfor %}

All are Closed, and each is the first work order numbered in its year. The others have three or four operations.

{{ figure('IF-02-3-A') }}

**Step 6. Say why this makes the cost figures unreliable.** A model answer: the operations give the planned hours, the work center and the sequence against which actual labor and overhead are compared. Without them, a standard labor and overhead cost cannot be assigned step by step, and the labor recorded cannot be tied to a work center. The data confirms it: these work orders have {{ labor.n }} labor entries for {{ labor.hours|num(2) }} hours, none of which is tied to an operation that exists, and each has a close that posted a variance, ${{ closes.total|money }} in all.

**Check:** the answer names what the operations provide and what the gap breaks. **Watch for:** "no operations means no cost", which is wrong: the close posted a cost, but it cannot be traced to a step.

### Requirement (4): Write the assessment

**Step 7. Outline half a page to a page.** A strong assessment has a conclusion up front (the data supports product costing for the items with a positive cost and a routing); a short list of problems with the table, column and count; the conditions it sets (treat the design services separately, key by ItemCode, resolve the three work orders before the variance work); and what is not known (whether a shared name is a successor).

**Check:** each problem has a count and a decision.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Items with a blank StandardCost | 0 | Step 1 |
| Items with a StandardCost of 0; their group | {{ n_zero }}; Services | Step 1 |
| Items with a blank ListPrice; items sold | {{ ch02_t1.blank_items }}; {{ ch02_t1.sellable|count }} | Step 3 |
| Names shared by more than one item; items involved | {{ n_names }}; {{ n_shared_items }} | Step 4 |
| Shared names that appear on invoice lines; made on work orders | {{ sold }}; {{ made }} | Step 4 |
| Work orders; with no operation | {{ work_orders|count }}; {{ n_none }} | Step 5 |
| Labor entries on those work orders; hours | {{ labor.n }}; {{ labor.hours|num(2) }} | Step 6 |

## What a strong answer says

- **Requirement (1).** The zero-cost items named as the hourly design services, the reason, and a comparison of costs within a group and a unit of measure.
- **Requirement (2).** The blank list prices sorted into bought items, the shared names treated as distinct items on the evidence of the codes and costs, and the effect of grouping by name.
- **Requirement (3).** The work orders listed, and what the missing operations break.
- **Requirement (4).** A conclusion, conditions and open questions.

A weak answer calls the zero costs errors, treats the shared names as duplicates to delete, or finds the work orders and stops at the count.

## Common mistakes and how to respond

- **Zero cost called an error.** *Symptom:* "fix the costs of the design services". *Response:* ask how the business prices and costs an hour of consultant time.
- **Shared names called duplicates.** *Symptom:* "delete one of each pair". *Response:* ask what differs in the rest of the record.
- **Big numbers called outliers.** *Symptom:* the monthly services and equipment flagged. *Response:* ask what unit the cost is in.
- **Names as the key.** *Symptom:* a cost table grouped by ItemName. *Response:* ask what happens when two items share a name.
- **COUNTIFS pointed at the wrong table.** *Symptom:* every work order shows 1 or 0 for the wrong reason. *Response:* ask which table holds the children.
- **Count without consequence.** *Symptom:* "three work orders have no operations" and nothing more. *Response:* ask what the cost analysis cannot do for them.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: standard costs | 25 | Zero-cost items identified with the reason, costs compared within group and unit | Zero costs listed without a reason |
| Requirement 2: blank prices and shared names | 30 | Blank prices sorted by group, shared names judged distinct on evidence, effect on grouping explained | Shared names found without a judgment |
| Requirement 3: work orders | 25 | The work orders found with a formula and the consequence explained | Found without the consequence |
| Requirement 4: assessment | 20 | Conclusion, conditions and open questions, half a page to a page | A list of findings only |

## Extensions and discussion questions

- Count the manufactured items that have no routing ({{ unrouted.blank }} of {{ unrouted.manufactured }}) and test whether any of them was put on a work order; none was.
- Test whether any item with a list price is priced below its standard cost, and say what the result shows.
- Discuss: when is a missing operation a data problem and when is it a business decision?
- Discuss: how would the answer change if the design services were a large share of revenue? (Chapter 6 measures the margin at standard cost.)
