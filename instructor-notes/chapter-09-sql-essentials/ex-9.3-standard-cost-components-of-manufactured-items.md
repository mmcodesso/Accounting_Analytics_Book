# Exercise 9.3: Standard Cost Components of Manufactured Items

| | |
|---|---|
| Unit | Chapter 9: SQL Essentials for Accounting Analytics |
| Item | Exercise 9.3 |
| Perspective | Managerial accounting |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 60 minutes |
| Solution file | Chapter09-exercises-sql.zip: Ex 9.3.sql |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

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
- **Data conditions.** Item holds 266 rows, of which 88 have SupplyMode Manufactured, written exactly so. The other 178 items are bought and have zero standard labor hours, so a division by hours gives NULL, not an error, for them. Every standard component of a manufactured item is filled.
- **Verify first.** A query with the SupplyMode filter returns 88 rows.

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

**Check:** 88 rows, in the groups of the Expected results. **Watch for:** no filter returns 266 rows; `'manufactured'` in small letters returns none.

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

**Check:** 88 rows and a new column that runs from $10.43 to $558.40; sort on it to see the ends. **Watch for:** the ROUND does not change what you read here. It matters for the next step.

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

**Check:** 0 rows. **Watch for:** without the two ROUNDs the test returns 30 items whose parts look equal to their total on screen, because SQLite compares the stored binary values. A student who stops there reports a defect that does not exist.

**Step 4. Look for a missing component.** An empty Step 3 means little unless this step is empty too. The exercise does not ask for this query. The model answer adds it, so give it as a hint, or count it as a plus, never as a condition for full credit. Keep the point for the class discussion.

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

**Check:** 88 rows from $23.27 (TXT-CRT-0011) to $31.82 (FUR-BNH-0048), 81 different rates. The rate belongs to the item: Furniture alone runs from $26.01 to $31.82. **Watch for:** without the SupplyMode filter, 178 bought items show a NULL rate and sort first.

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

**Check:** 10 rows, FUR-TBL-0017 first at $112.43, then FUR-CON-0077 and FUR-CTB-0014, all in Furniture. **Watch for:** ascending order returns items of Accessories, Lighting, and Textiles, the cheapest to convert.

## Expected results

| Quantity | Value | Step |
|---|---:|---|
| Manufactured items, and by group | 88; Furniture 56, Lighting 26, Textiles 5, Accessories 1 | 1 |
| Standard material cost, lowest and highest | $10.43; $558.40 | 2 |
| Items whose components differ from the conversion cost, and items with a missing component | 0; 0 | 3, 4 |
| Labor rate per standard hour, lowest and highest | $23.27; $31.82 | 5 |
| The three highest conversion costs | FUR-TBL-0017 $112.43; FUR-CON-0077 $106.38; FUR-CTB-0014 $105.58 | 6 |

> **Instructor notes, Exercise 9.3:** 88 manufactured items (Furniture 56, Lighting 26, Textiles 5, Accessories 1). Material cost = StandardCost - StandardConversionCost, from 10.43 to 558.40. The component check returns no rows: labor + variable overhead + fixed overhead = conversion for every item, and no component is NULL, so no item escapes the test (a NULL would make the comparison unknown, not true). Labor rate per standard hour ranges from 23.27 to 31.82, so rates are item-specific, not one plant rate. Highest conversion cost: FUR-TBL-0017 Mason Dining Table Ash Natural 84 in (112.43), FUR-CON-0077 (106.38), FUR-CTB-0014 (105.58); the top ten are Furniture.

## What a strong answer says

- **Requirement (3).** The three parts add up to the conversion cost on every item, so the standards are internally consistent. The check for a missing component of Step 4, which shows that no part is missing and so that the comparison skipped no item, is a plus. A strong answer adds that consistent is not the same as right: whether the standards fit how the plant works is a question for Chapters 10 to 12.
- **Requirement (4).** Rates differ by item, with no single plant rate, and they do not follow the item group. The labor cost of a unit is hours times an item's own rate.
- **The description.** A standard cost is material plus conversion cost, and conversion is direct labor plus variable and fixed overhead. The highest conversion costs are all Furniture, the group with the most manufactured items.

A weak answer reads the 30 unrounded differences as errors in the standards, or lists numbers without saying how the parts fit.

## Common mistakes and how to respond

- **No SupplyMode filter.** *Symptom:* 266 rows, and NULL rates. *Response:* ask which items the requirement means.
- **A check without ROUND.** *Symptom:* 30 "defects". *Response:* ask the student to add the parts of one row by hand.
- **No companion check for NULL.** *Symptom:* "no rows, so no problem". *Response:* this is not a mistake against the requirement. Ask, as a point for discussion, what the comparison does with a missing value.
- **The rate upside down.** *Symptom:* values near `0.04` or below. *Response:* ask what a rate per hour divides by.
- **An ascending ranking.** *Symptom:* the top ten are Accessories, Lighting, and Textiles. *Response:* ask which direction puts the largest first.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the filtered list | 10 | Correct filter and columns | No filter |
| Requirement 2: material cost | 15 | Rounded calculation with an alias | Unrounded or no alias |
| Requirement 3: the component test | 25 | The manufactured items, the rounded comparison and the result reported | Unrounded test, the wrong population, or no result reported |
| Requirement 4: labor rate | 20 | Rate, sorted, range described | Rate without the description |
| Requirement 5: highest conversion cost | 15 | DESC and LIMIT, group named | Unlimited list |
| The description | 15 | Material, labor and overhead and what the checks show | Numbers without the structure |

## Extensions and discussion questions

- In Chapter 10, compare the labor rates with the base hourly rates in the Employee table. Do they agree?
- Discuss: why would a per-unit standard include a share of fixed overhead, and what does that do to the variance when volume changes?
- Discuss: the standards add up on every item. What else would you test before you trust them?
