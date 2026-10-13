---
note: ch09.ex5
uses: [ch09.g5]
title: Shipments That Need Follow-Up
kind: exercise
number: '9.5'
unit: '9'
perspective: auditing
tool: sql
minutes: 45
solution: "Chapter09-exercises-sql.zip: Ex 9.5.sql"
figures: []
---
{% set g = ch09_g5 %}
# Exercise 9.5: Shipments That Need Follow-Up

{{ header() }}

## Purpose and learning outcomes

Students already ran two shipment tests with Excel filters in Tutorial 2.1. The audit senior wants the same tests in SQL so that they can be saved and run again at the next year-end. The exercise is short on purpose: its point is the habit of writing a completeness test and a consistency test as conditions that a reviewer can read, and of naming the data quality dimension each one addresses. The analytics type is descriptive.

By the end, students can:

- use DISTINCT to learn the values of a status and a carrier column (outcome 2);
- write a completeness test with IS NULL and a consistency test that combines a status with a date (outcomes 3 and 4);
- explain why a saved SQL test is easier to rerun and review than an Excel filter (outcome 6);
- name the data quality dimension of each test and the question to put to the process owner (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M9 (audit procedures and audit data analytics) and ISC M4; IMA Data Analytics and Insights (data literacy) and Reporting and Control (internal control); IFAC IES 2 (f) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** CharlesRiver_Work.sqlite, a script `Ex 9.5.sql`, and each student's notes from Tutorial 2.1.
- **Data conditions.** Shipment.TrackingNumber is NULL, not empty text, where it is blank. Status holds two values. DeliveryDate is filled on every shipment and, like every date, is text in year-month-day form. The last shipment date of the data is {{ g.end }}.
- **Verify first.** Students' counts from Tutorial 2.1 are the numbers to reach again.

## How to run it

Individual, about 45 minutes: 10 for requirement (1), 10 for (2), 10 for (3), 15 for (4) and (5). The routine of Exercise 9.1 applies: type the comment lines and query at the end of the script, select it, click **Execute all/selected SQL** and read the message pane. Hold back the boundary hint until a student's count in (3) differs from the Excel filter. Collect the script and the comparison.

## Step-by-step solution

### Requirement (1): The values of Status and ShippedBy

**Step 1. List the statuses.**

```sql
-- Requirement (1): the values of Status
-- Population: Shipment; expected: Delivered and In Transit
SELECT DISTINCT Status
FROM Shipment
ORDER BY Status;
```

**Check:** {{ status|length }} rows: {{ status[0][0] }} and {{ status[1][0] }}. The next step counts them.

**Step 2. Count each status.** The message pane gives each count.

```sql
-- Requirement (1): the shipments with Status Delivered (count in the message pane)
-- Population: Shipment; expected: 8,967 shipments
SELECT ShipmentID, ShipmentNumber, ShipmentDate, Status
FROM Shipment
WHERE Status = 'Delivered';
```

```sql
-- Requirement (1): the shipments with Status In Transit (count in the message pane)
-- Population: Shipment; expected: 740 shipments
SELECT ShipmentID, ShipmentNumber, ShipmentDate, Status
FROM Shipment
WHERE Status = 'In Transit';
```

**Check:** {{ status[0][1]|count }} {{ status[0][0] }} rows and {{ status[1][1]|count }} {{ status[1][0] }} rows. **Watch for:** `'In transit'` with a small t returns no rows.

**Step 3. List the carriers.**

```sql
-- Requirement (1): the values of ShippedBy
-- Population: Shipment; expected: 4 carriers
SELECT DISTINCT ShippedBy
FROM Shipment
ORDER BY ShippedBy;
```

**Check:** {{ carriers|length }} rows: {{ carriers|join(", ") }}.

### Requirement (2): No tracking number

**Step 4. Find the shipments with a blank TrackingNumber.**

```sql
-- Requirement (2): shipments with no tracking number
-- Population: Shipment, TrackingNumber NULL; expected: 392 shipments, 2024-01-16 to 2026-12-31
SELECT ShipmentNumber, ShipmentDate, ShippedBy, Status
FROM Shipment
WHERE TrackingNumber IS NULL
ORDER BY ShipmentDate;
```

**Check:** {{ n }} rows; the first row is dated {{ low }} and the last {{ high }}, so the blanks span the whole period. **Watch for:** `= NULL` returns {{ g.eq_null }} rows and `= ''` returns {{ g.eq_empty }}, because the blanks are NULL, not empty text. The blanks are spread over every carrier, {{ g.carrier_low }} to {{ g.carrier_high }} each, so it is not one carrier's habit.

### Requirement (3): In Transit past the delivery date

**Step 5. Combine the status with the date.**

```sql
-- Requirement (3): shipments In Transit with a DeliveryDate before 2026-12-31
-- Population: Shipment, Status In Transit; expected: 739 shipments, oldest 2024-01-10
SELECT ShipmentNumber, ShipmentDate, DeliveryDate, ShippedBy,
    TrackingNumber, Status
FROM Shipment
WHERE Status = 'In Transit' AND DeliveryDate < '2026-12-31'
ORDER BY DeliveryDate;
```

**Check:** {{ transit }} rows, the oldest delivery date {{ oldest }} in the first row. **Watch for:** `<=` returns {{ g.le }}, adding {{ g.last_number }}, shipped on the last day of the data with a DeliveryDate of the same day, which cannot yet be late. Without the Status condition the date test keeps {{ g.no_status|count }} rows, almost every shipment.

**Step 6. Look at the one that is left.** The exercise does not ask for this query; the model answer uses it to account for every In Transit shipment.

```sql
-- Requirement (3): the other In Transit shipments, delivered on or after 2026-12-31
-- Population: Shipment, Status In Transit; expected: 1 shipment
SELECT ShipmentNumber, ShipmentDate, DeliveryDate, Status
FROM Shipment
WHERE Status = 'In Transit' AND DeliveryDate >= '2026-12-31';
```

**Check:** {{ later_word }} row, {{ g.last_number }}. The two tests together account for every In Transit shipment, {{ status[1][1]|count }} in all.

### Requirement (4): The comparison with Tutorial 2.1

**Step 7. Compare the counts and the method.** The counts should equal the Excel results; the answer is about why the SQL version reruns more easily. See "What a strong answer says".

### Requirement (5): Dimensions and questions

**Step 8. Name the dimension and the question for each test.** See "What a strong answer says".

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Shipments by status | {{ status[0][0] }} {{ status[0][1]|count }}; {{ status[1][0] }} {{ status[1][1]|count }} | 2 |
| Carriers | {{ carriers|length }} | 3 |
| No tracking number, and the dates | {{ n }}; {{ low }} to {{ high }} | 4 |
| In Transit before the last day, and the oldest | {{ transit }}; {{ oldest }} | 5 |
| In Transit on or after the last day | {{ later }} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirement (4).** The SQL counts equal the Excel filters of Tutorial 2.1. Both tests are written as conditions that a reviewer reads in plain text, so the same script runs on a later extract once its cutoff date is changed, and the results are checked again. An Excel filter stays with its workbook too, but its conditions sit in each column's filter menu and apply to whatever rows the sheet holds.
- **Requirement (5).** The blank tracking number is a completeness test: ask why the number was not recorded and whether the carrier's records hold it. The status after the delivery date is a consistency, or timeliness, test: ask who updates the status on delivery, whether DeliveryDate records the delivery or the date expected, and what evidence of delivery exists. A DeliveryDate does not prove delivery.

A weak answer calls the blanks inaccurate, or gives a test but no question for the process owner.

## Common mistakes and how to respond

- **`= NULL` or `= ''`.** *Symptom:* no rows for a test that must find rows. *Response:* ask how the blank is stored.
- **A status typed from memory.** *Symptom:* no rows. *Response:* run DISTINCT first, as in Step 1.
- **`<=` on the cutoff.** *Symptom:* {{ g.le }} rows against Tutorial 2.1's {{ transit }}. *Response:* ask which shipments can already be late on the last day.
- **No status condition.** *Symptom:* {{ g.no_status|count }} rows. *Response:* ask what the test is meant to find.
- **A cutoff typed in two places without a note.** *Symptom:* a rerun that changes one date and not the other. *Response:* record the date in the header comment.
- **The wrong dimension.** *Symptom:* "accuracy" for a missing value. *Response:* ask whether the value is wrong or absent.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: values and counts | 15 | DISTINCT for both columns, counts from the pane | Values without counts |
| Requirement 2: no tracking number | 20 | IS NULL, sorted, count and date range reported | Count only |
| Requirement 3: In Transit past due | 25 | Both conditions, the right boundary, count and oldest date | Boundary off by one |
| Requirement 4: comparison | 20 | Counts agree with Tutorial 2.1 and the reason SQL reruns more easily | Counts without the reason |
| Requirement 5: dimensions and questions | 20 | Right dimension and a useful question for each test | One test |

## Extensions and discussion questions

- Combine the two tests with AND. {{ g.transit_no_track }} In Transit shipments have no tracking number; are they the first ones to chase?
- Move the cutoff date and rerun the script. Which parts of the work had to change?
- Discuss: which test would you run every month, and with what cutoff date?
- Discuss: Chapter 12 turns tests like these into a library. What would each test need to carry so a stranger could run it?
