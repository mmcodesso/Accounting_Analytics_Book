---
note: ch04.ex5
uses: [ch04.g5]
title: A Refreshable Shipment Exception Report
kind: exercise
number: '4.5'
unit: '4'
perspective: auditing
tool: excel
minutes: 90
solution: "Chapter04-exercises.zip: Chapter 4 Exercises - Solutions.xlsx, sheets Ex 4.5 Parameters, Ex 4.5 Analysis and Ex 4.5 Shipment"
figures:
  - id: IF-04-5-A
    kind: excel-mock
    purpose: The shipment exception report with its two highlight colors, the counts and the Status slicer set to In Transit.
    shows: "Two panes of one window. The left pane shows the top of the Shipment Table (ShipmentID, TrackingNumber, Status and DeliveryDate) with amber rows for a blank TrackingNumber and coral rows for In Transit shipments with a DeliveryDate before the review date, and the Status filter set to In Transit. The right pane shows the Analysis worksheet with the review date, the three exception counts, the blank tracking numbers by Status, the In Transit shipments by year, and the SUBTOTAL cells beside a Status slicer with In Transit selected."
    data: Shipment at the review date, the year-end under review and the last shipment date (the Expected results table).
---
{% set g = ch04_g5 %}
# Exercise 4.5: A Refreshable Shipment Exception Report

{{ header() }}

## Purpose and learning outcomes

Tutorial 2.1 found shipments with no tracking number and shipments still In Transit after their delivery date, with one-off filters. This exercise rebuilds those two tests as a report that refreshes, with a review date held in a validated, named cell. The central point is the fixed review date. The test finds the records marked In Transit whose recorded DeliveryDate is before that date, which belongs to the extract, not to today. The analytics type is descriptive, with an auditing purpose.

By the end, students can:

- load a Table with Power Query and set its date columns to the Date type (outcome 2);
- hold a review date in a named, validated cell and justify a fixed date over TODAY (outcomes 3, 5 and 1);
- write two formula rules that use a named cell, and count the exceptions with COUNTIFS (outcomes 4 and 5);
- confirm counts with a slicer and SUBTOTAL, and explain a difference (outcome 4);
- write the exceptions up as an auditor would (outcome 6).

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (extracting and transforming financial data) and Core S2 M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Tools and Techniques, and Internal Control; IFAC IES 2 (f), audit, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **A new workbook.** Students start a new workbook, so their names are Shipment, Parameters and Analysis. The solution file already holds Exercise 4.4's Shipment query, so its names differ: the query is ShipmentReview, and the sheets are Ex 4.5 Parameters, Ex 4.5 Analysis and Ex 4.5 Shipment. The steps below use a student's names.
- **Date types.** Power Query may read ShipmentDate and DeliveryDate as date and time, and the exercise has students set the Date type with **Replace current**, as Tutorial 4.1, Step 6 does.
- **Data conditions.** The extract has {{ shipments|count }} shipments. {{ blank|count }} have no TrackingNumber ({{ blank_delivered|count }} Delivered and {{ blank_transit|count }} In Transit). {{ transit|count }} are In Transit, from every year of the data, and {{ late|count }} have a DeliveryDate before the review date, {{ review }}. No ShipmentDate or DeliveryDate is blank.
- **What the test shows.** It finds records currently marked In Transit whose recorded DeliveryDate is earlier than ReviewDate. The extract does not say whether DeliveryDate is the actual delivery or an expected one, and that decides how to read the exception, so students establish it before calling a shipment delivered, overdue or recorded incorrectly.
- **Software.** Desktop Excel with Power Query. Excel for the web limits the size of the workbooks it opens and the features it offers.

## How to run it

Individual, about 90 minutes: 15 loading (requirement 1), 15 the review date (2), 15 the rules (3), 15 the counts (4), 15 the slicer and the second date (5) and 15 the memo (6). Hold back the TODAY discussion until each student has written their own reason. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): Load the Shipment Table

**Step 1. Import and type the dates.**

a. In a new workbook, choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx and click **Import**.
b. In the **Navigator** select **T14_Shipment** and click **Transform Data**.
c. Rename the query `Shipment`. Click the type icon on the header of ShipmentDate, choose **Date**, and click **Replace current**. Do the same for DeliveryDate.
d. Choose **Home > Close & Load > Close & Load To**, select **Table** and **New worksheet**.

**Check:** a Table named Shipment with {{ shipments|count }} rows, and both dates show without a time. Blank tracking numbers are empty cells.

### Requirement (2): The review date

**Step 2. Create ReviewDate.**

a. Insert a worksheet named `Parameters`. In A4 type `ReviewDate` and in B4 enter {{ review }} as a date. Name B4 `ReviewDate` in the **Name Box** and set its font to blue.
b. Choose **Data > Data Validation**, allow a **Date** with only a lower bound (the model answer uses `=DATE(1900,1,1)`, so any date passes), add an input message, and choose the **Stop** style.
c. In C4 write why the report uses a fixed date and not `TODAY()`.

**Check:** text typed into B4 is refused. A model note: the review date is the year-end under review, which is also the last shipment date in the extract, so the counts are the same every time the report is refreshed or re-performed, while `TODAY()` changes the result daily and, long after the extract, flags every In Transit shipment. The date is changed when the next extract arrives.

### Requirement (3): Two highlight rules

**Step 3. Add the rules.**

a. On the Shipment worksheet, select the data cells with A2 active, and choose **Home > Conditional Formatting > New Rule**.
b. Select **Use a formula to determine which cells to format**, enter `=${{ g.letters.TrackingNumber }}2=""` and choose an amber fill.
c. Add a second rule, with a coral fill:

   ```jinja
   =AND(${{ g.letters.Status }}2="In Transit",${{ g.letters.DeliveryDate }}2<ReviewDate)
   ```

d. With a cell of the Table selected, choose **Home > Conditional Formatting > Manage Rules**. Excel puts a new rule at the top, so the coral rule comes first, and a shipment in both categories shows coral. The model answer and the figure in Expected results have the amber rule on top, so select it and click **Move Up** to match them.

**Check:** both colors appear when you scroll, and a shipment in both categories shows the color of the rule on top. Either order is right if the memo says which color wins. **Watch for:** a rule written with structured references, which a rule cannot use, and a rule applied to one column only. One fill cannot show both categories, which is one reason the counts and the overlap are made with COUNTIFS.

### Requirement (4): The counts

**Step 4. Count each category.** On a worksheet named `Analysis` enter these, with labels in column A:

```
=COUNTIFS(Shipment[TrackingNumber],"")
=COUNTIFS(Shipment[Status],"In Transit",Shipment[DeliveryDate],"<"&ReviewDate)
=COUNTIFS(Shipment[TrackingNumber],"",Shipment[Status],"In Transit",Shipment[DeliveryDate],"<"&ReviewDate)
```

Below them list Delivered and In Transit in A12 and A13 and count the blank tracking numbers for each, filled down:

```
=COUNTIFS(Shipment[TrackingNumber],"",Shipment[Status],$A12)
```

**Check:** {{ blank|count }} blank tracking numbers ({{ blank_delivered|count }} Delivered, {{ blank_transit|count }} In Transit), {{ late|count }} In Transit shipments with a recorded DeliveryDate before the review date, and {{ blank_transit|count }} in both. The In Transit shipments by year are {% for y, n in transit_by_year %}{{ y }}: {{ n|count }}{{ '; ' if not loop.last else '' }}{% endfor %}.

### Requirement (5): The slicer and a second review date

**Step 5. Confirm the blanks by Status with a slicer.**

a. Choose **Table Design > Insert Slicer** on the Shipment Table and select **Status**.
b. Enter the shipments in view and, below it, the tracking numbers in view. SUBTOTAL has no count of blanks, so the blanks in view are the first less the second.

   ```
   =SUBTOTAL(103,Shipment[ShipmentID])
   =SUBTOTAL(103,Shipment[TrackingNumber])
   ```
c. Click Delivered, then In Transit, and record the results. Click **Clear Filter**.

**Check:** Delivered shows {{ g.delivered|count }} shipments and {{ blank_delivered|count }} blanks, and In Transit shows {{ g.in_transit|count }} and {{ blank_transit|count }}. These agree with Step 4.

**Step 6. Explain the difference, then move the date.**

a. Compare the In Transit shipments in view, {{ g.in_transit|count }}, with the count of those whose recorded DeliveryDate is before the review date, {{ late|count }}. The slicer filters on Status only, so its count also includes the In Transit shipments with a DeliveryDate on or after the review date ({% if after_review == 0 %}{{ others|count }}, on {{ review }} itself{% elif on_review == 0 %}{{ others|count }}, all after it{% else %}{{ on_review|count }} on {{ review }} itself and {{ after_review|count }} after it{% endif %}). It confirms the count only together with a filter on DeliveryDate.
b. Change ReviewDate to {{ g.review2_long }}. The count falls to {{ late2|count }}, a change of -{{ g.drop }}, because the {{ g.drop }} In Transit shipments with a DeliveryDate from {{ g.window }} drop out. This is a sensitivity of the count to the review date on the same extract. The Status column is the extract's, so the run does not show which shipments were In Transit on {{ g.review2_long }}. Reconstructing that needs the status history or an earlier extract.
c. Set ReviewDate back to {{ g.review_long }}.

**Check:** the count returns to {{ late|count }}. **Watch for:** a student who leaves the date at the second value, or concludes that the slicer count is wrong.

### Requirement (6): The memo

**Step 7. Outline the half page.** Each exception gets what it is, the likely cause and the evidence to request. Blank tracking number: a completeness problem; the cause may be manual entry or pickups; ask for carrier documents and proof of delivery for a sample. In Transit with a recorded DeliveryDate before the review date: first establish whether DeliveryDate records the delivery or an expected date. If it records the delivery, the two fields conflict, a consistency and timeliness problem (Chapter 2), and either the status or the date is wrong. If it is an expected date, the records show the shipments past it. Either way, ask for carrier tracking and the status history before concluding that a delivery occurred, was late or was recorded incorrectly. Both: the {{ blank_transit|count }} In Transit shipments with no tracking number also have a DeliveryDate before the review date, so they are the first to confirm with customers. Neither exception proves that goods were lost.

**Check:** the memo does not call either exception fraud or a misstatement.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Shipments | {{ shipments|count }} | Step 1 |
| Blank TrackingNumber; Delivered; In Transit | {{ blank|count }}; {{ blank_delivered|count }}; {{ blank_transit|count }} | Step 4 |
| In Transit; with a recorded DeliveryDate before {{ review }} | {{ transit|count }}; {{ late|count }} | Steps 4 and 6 |
| In both categories | {{ blank_transit|count }} | Step 4 |
| In Transit by year shipped | {% for y, n in transit_by_year %}{{ y }}: {{ n|count }}{{ '; ' if not loop.last else '' }}{% endfor %} | Step 4 |
| Recorded DeliveryDate before {{ review2 }} (a sensitivity); change | {{ late2|count }}; -{{ g.drop }} | Step 6 |

{{ figure('IF-04-5-A') }}

{{ expected() }}

## What a strong answer says

- **Requirement (2).** A reason tied to the data. The report reads the records at the end of the extract and must give the same answer when it is performed again.
- **Requirement (5).** The slicer count and the date test differ for a stated reason, and the second date moves the count by the shipments whose DeliveryDate falls between the two dates, a sensitivity of the same extract rather than the status on the earlier date.
- **Requirement (6).** Each exception with a cause and a request for evidence, the question whether DeliveryDate is actual or expected, an honest statement of what the data cannot show, and the overlap between the two.

A weak answer lists counts without evidence requests, or treats a stale status as proof of loss.

## Common mistakes and how to respond

- **TODAY() as the review date.** *Symptom:* a count that changes between sessions. *Response:* ask what the report said last week.
- **A text date.** *Symptom:* a count of every In Transit shipment. *Response:* test the cell with `=ISNUMBER(ReviewDate)` and check the validation. Right alignment is only a clue.
- **Counting by color.** *Symptom:* a total that misses the shipments in both categories. *Response:* use COUNTIFS.
- **Reading blanks from SUBTOTAL(103).** *Symptom:* the count of tracking numbers reported as blanks. *Response:* subtract from the rows in view.
- **A difference called an error.** *Response:* ask which In Transit shipments have a DeliveryDate on or after the review date.
- **The date left at the second value.** *Response:* ask them to read B8 against the memo.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: loading | 10 | Date types set with Replace current | Text dates |
| Requirement 2: review date | 15 | Named, validated cell and a reasoned note | No reason, or TODAY() |
| Requirement 3: rules | 20 | Two rules in two colors, one using ReviewDate, in either order | One rule, or the wrong columns |
| Requirement 4: counts | 20 | COUNTIFS for each category and the overlap | Counts by filtering |
| Requirement 5: slicer and date | 20 | Blanks confirmed, the difference explained, the date restored | No explanation |
| Requirement 6: memo | 15 | Cause and evidence for each exception, with limits | Counts only |

## Extensions and discussion questions

- Add the days from the recorded DeliveryDate to ReviewDate for each flagged shipment as a calculated column, and a top-ten list.
- Make the review date a formula that takes the largest DeliveryDate, and discuss when a typed date is safer.
- Discuss: which of the two exceptions would you raise with management first, and why?
- Discuss: Chapter 8 builds a whole audit workbook. What from this report would you reuse?
