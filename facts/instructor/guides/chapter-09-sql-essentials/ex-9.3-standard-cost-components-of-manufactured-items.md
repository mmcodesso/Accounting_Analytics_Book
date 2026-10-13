---
note: ch09.ex3
uses: [ch09.g3]
title: Standard Cost Components of Manufactured Items
kind: exercise
number: '9.3'
unit: '9'
perspective: managerial
tool: sql
minutes: 60
solution: "Chapter09-exercises-sql.zip: Ex 9.3.sql"
figures: []
---
{% set g = ch09_g3 %}
# Exercise 9.3: Standard Cost Components of Manufactured Items

{{ header() }}

## Purpose and learning outcomes

The manufacturing variance compares actual cost with standard cost, so the controller wants the standards understood before the variance is analyzed. The exercise is a tour of one table, Item, in three moves: filter to the items Charles River makes, calculate what the table does not store (material cost and the labor rate per hour), and test whether the standard's parts add up. Its lesson in method is that an empty result proves a test clean only when the test could have found something. The analytics type is descriptive.

By the end, students can:

- filter on a text column and calculate rounded columns with aliases (outcome 2);
- write a check that should return no rows, and a companion check for missing values (outcomes 4 and 6);
- sort by a calculated column and rank with LIMIT (outcome 5);
- describe how a standard cost is built from material, labor and overhead (outcome 6).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Reporting and Control (cost accounting) and Data Analytics and Insights (data tools); IFAC IES 2 (b) and (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** CharlesRiver_Work.sqlite and a script `Ex 9.3.sql`. Standard costs are explained in the chapter's section Standard Costs in Brief.
- **Data conditions.** Item holds {{ g.n_all }} rows, of which {{ g.made }} have SupplyMode Manufactured, written exactly so. The other {{ g.bought }} items are bought and have zero standard labor hours, so a division by hours gives NULL, not an error, for them. Every standard component of a manufactured item is filled.
- **Verify first.** A query with the SupplyMode filter returns {{ n }} rows.

## How to run it

Individual, about 60 minutes: 15 for requirements (1) and (2), 15 for (3), 15 for (4) and 15 for (5) and the description. The routine of Exercise 9.1 applies: type the comment lines and query at the end of the script, select it, click **Execute all/selected SQL** and read the message pane. Hold back ROUND for requirement (3) until a student's check returns rows, then ask them to read two of the rows. Collect the script and the description.

## Step-by-step solution

### Requirement (1): The manufactured items

**Step 1. List the items Charles River makes.**

```sql
-- Requirement (1): the manufactured items and their standards
-- Population: Item, SupplyMode Manufactured; expected: 88 items (Furniture 56, Lighting 26, Textiles 5, Accessories 1)
SELECT ItemCode, ItemName, ItemGroup, StandardCost,
    StandardLaborHoursPerUnit, StandardDirectLaborCost,
    StandardVariableOverheadCost, StandardFixedOverheadCost,
    StandardConversionCost
FROM Item
WHERE SupplyMode = 'Manufactured'
ORDER BY ItemCode;
```

**Check:** {{ n }} rows, in the groups of the Expected results. **Watch for:** no filter returns {{ g.n_all }} rows; `'manufactured'` in small letters returns none.

### Requirement (2): The material cost

**Step 2. Add the standard material cost.** Material cost is what is left of StandardCost after the conversion cost.

```sql
-- Requirement (2): the same list with the standard material cost
-- Population: as (1); expected: material cost from 10.43 to 558.40
SELECT ItemCode, ItemName, ItemGroup, StandardCost,
    StandardLaborHoursPerUnit, StandardDirectLaborCost,
    StandardVariableOverheadCost, StandardFixedOverheadCost,
    StandardConversionCost,
    ROUND(StandardCost - StandardConversionCost, 2)
        AS StandardMaterialCost
FROM Item
WHERE SupplyMode = 'Manufactured'
ORDER BY ItemCode;
```

**Check:** {{ n }} rows and a new column that runs from ${{ material_low|money }} to ${{ material_high|money }}; sort on it to see the ends. **Watch for:** the ROUND does not change what you read here. It matters for the next step.

### Requirement (3): Do the components add up?

**Step 3. Test the conversion cost.**

```sql
-- Requirement (3): items whose conversion components do not add up
-- Population: Item, SupplyMode Manufactured; expected: no rows
SELECT ItemCode, ItemName, StandardDirectLaborCost,
    StandardVariableOverheadCost, StandardFixedOverheadCost,
    StandardConversionCost
FROM Item
WHERE SupplyMode = 'Manufactured'
    AND ROUND(StandardDirectLaborCost
        + StandardVariableOverheadCost
        + StandardFixedOverheadCost, 2)
        <> ROUND(StandardConversionCost, 2);
```

**Check:** 0 rows. **Watch for:** without the two ROUNDs the test returns {{ g.unrounded }} items whose parts look equal to their total on screen, because SQLite compares the stored binary values. A student who stops there reports a defect that does not exist.

**Step 4. Look for a missing component.** An empty Step 3 means little unless this step is empty too. The exercise does not ask for this query; the model answer adds it, so give it as a hint or as credit.

```sql
-- Requirement (3): items with a missing component, which the comparison would pass over
-- Population: Item, SupplyMode Manufactured; expected: no rows
SELECT ItemCode, ItemName
FROM Item
WHERE SupplyMode = 'Manufactured'
    AND (StandardDirectLaborCost IS NULL
        OR StandardVariableOverheadCost IS NULL
        OR StandardFixedOverheadCost IS NULL
        OR StandardConversionCost IS NULL);
```

**Check:** 0 rows. A NULL makes the Step 3 comparison unknown, so such an item would have been skipped without a message.

### Requirement (4): The labor rate

**Step 5. Divide labor cost by labor hours and sort.**

```sql
-- Requirement (4): the list with the labor rate per standard hour, sorted by it
-- Population: as (1); expected: rates from 23.27 to 31.82
SELECT ItemCode, ItemName, ItemGroup, StandardCost,
    StandardLaborHoursPerUnit, StandardDirectLaborCost,
    StandardVariableOverheadCost, StandardFixedOverheadCost,
    StandardConversionCost,
    ROUND(StandardCost - StandardConversionCost, 2)
        AS StandardMaterialCost,
    ROUND(StandardDirectLaborCost / StandardLaborHoursPerUnit, 2)
        AS LaborRatePerHour
FROM Item
WHERE SupplyMode = 'Manufactured'
ORDER BY LaborRatePerHour, ItemCode;
```

**Check:** {{ n }} rows from ${{ rate_low|money }} ({{ g.rate_low_item }}) to ${{ rate_high|money }} ({{ g.rate_high_item }}), {{ g.distinct_rates }} different rates. The rate belongs to the item: Furniture alone runs from ${{ g.furniture_low|money }} to ${{ g.furniture_high|money }}. **Watch for:** without the SupplyMode filter, {{ g.no_filter_null }} bought items show a NULL rate and sort first.

### Requirement (5): The highest conversion costs

**Step 6. Rank by conversion cost.**

```sql
-- Requirement (5): the ten items with the highest standard conversion cost
-- Population: Item, SupplyMode Manufactured; expected: FUR-TBL-0017 first (112.43), all Furniture
SELECT ItemCode, ItemName, ItemGroup, StandardConversionCost
FROM Item
WHERE SupplyMode = 'Manufactured'
ORDER BY StandardConversionCost DESC
LIMIT 10;
```

**Check:** 10 rows, {{ top[0].code }} first at ${{ top[0].cost|money }}, then {{ top[1].code }} and {{ top[2].code }}, all in {{ top_group }}. **Watch for:** ascending order returns items of {{ g.asc_groups }}, the cheapest to convert.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Manufactured items, and by group | {{ n }}; {% for k in groups %}{{ k[0] }} {{ k[1] }}{{ ", " if not loop.last else "" }}{% endfor %} | 1 |
| Standard material cost, lowest and highest | ${{ material_low|money }}; ${{ material_high|money }} | 2 |
| Items whose components differ from the conversion cost, and items with a missing component | 0; 0 | 3, 4 |
| Labor rate per standard hour, lowest and highest | ${{ rate_low|money }}; ${{ rate_high|money }} | 5 |
| The three highest conversion costs | {% for t in top %}{{ t.code }} ${{ t.cost|money }}{{ "; " if not loop.last else "" }}{% endfor %} | 6 |

{{ expected() }}

## What a strong answer says

- **Requirement (3).** The three parts add up to the conversion cost on every item, and no part is missing, so the standards are internally consistent. A strong answer adds that consistent is not the same as right: whether the standards fit how the plant works is a question for Chapters 10 to 12.
- **Requirement (4).** Rates differ by item, with no single plant rate, and they do not follow the item group. The labor cost of a unit is hours times an item's own rate.
- **The description.** A standard cost is material plus conversion cost, and conversion is direct labor plus variable and fixed overhead. The highest conversion costs are all {{ top_group }}, the group with the most manufactured items.

A weak answer reads the {{ g.unrounded }} unrounded differences as errors in the standards, or lists numbers without saying how the parts fit.

## Common mistakes and how to respond

- **No SupplyMode filter.** *Symptom:* {{ g.n_all }} rows, and NULL rates. *Response:* ask which items the requirement means.
- **A check without ROUND.** *Symptom:* {{ g.unrounded }} "defects". *Response:* ask the student to add the parts of one row by hand.
- **No companion check for NULL.** *Symptom:* "no rows, so no problem". *Response:* ask what the comparison does with a missing value.
- **The rate upside down.** *Symptom:* values near `{{ g.inverted }}` or below. *Response:* ask what a rate per hour divides by.
- **An ascending ranking.** *Symptom:* the top ten are {{ g.asc_groups }}. *Response:* ask which direction puts the largest first.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the filtered list | 10 | Correct filter and columns | No filter |
| Requirement 2: material cost | 15 | Rounded calculation with an alias | Unrounded or no alias |
| Requirement 3: the component test | 25 | Rounded test and the finding reported, with the check for a missing component or the reason it is needed | Rounded test and the finding only |
| Requirement 4: labor rate | 20 | Rate, sorted, range described | Rate without the description |
| Requirement 5: highest conversion cost | 15 | DESC and LIMIT, group named | Unlimited list |
| The description | 15 | Material, labor and overhead and what the checks show | Numbers without the structure |

## Extensions and discussion questions

- In Chapter 10, compare the labor rates with the base hourly rates in the Employee table. Do they agree?
- Discuss: why would a per-unit standard include a share of fixed overhead, and what does that do to the variance when volume changes?
- Discuss: the standards add up on every item. What else would you test before you trust them?
