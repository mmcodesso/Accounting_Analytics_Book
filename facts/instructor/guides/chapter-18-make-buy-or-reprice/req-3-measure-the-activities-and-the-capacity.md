---
note: ch18.r3
uses: [ch18.g3]
title: Measure the activities and the capacity (Chapters 10 and 11)
kind: requirement
number: '3'
unit: '18'
perspective: managerial
tool: mixed
minutes: 90
solution: "Chapter18-capstone-sql.zip: MakeBuy.sql, the queries headed Requirement 3 (Q15 to Q20); Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Activities"
figures:
  - id: IF-18-3-A
    kind: sql-mock
    purpose: The capacity query with its six-row result, the table every later requirement reads.
    shows: "The tab MakeBuy.sql at Q20, scrolled to its last CTE and the final SELECT; the grid, scrolled one column to the right to fit the frame, shows one row for each work center and a Plant row, with the available, practical and routing hours and the two shares, the Plant row outlined; the message pane reports six rows."
    data: Query Q20, run read-only on the capstone copy.
  - id: IF-18-3-B
    kind: chart
    purpose: Where the plant's hours go, work center by work center.
    shows: "A clustered bar chart with one group for each of the five work centers and three bars in each: available hours, practical capacity and routing time used. A reference note marks that the Quality Assurance bar for routing time is a small fraction of its practical bar. Hours on the axis, no value labels beyond the Plant total."
    data: The result of Q20 (the five work-center rows).
---
{% set g = ch18_g3 %}
# Requirement 3: Measure the activities and the capacity (Chapters 10 and 11)

{{ header() }}

## Purpose and learning outcomes

What a family uses of the plant comes from the routings, multiplied by what was made; what the plant had comes from its calendar. Both are joins and sums over the year's work orders, which SQL handles directly, and the result is the capacity table that Requirements 4 to 7 read. Routing time, not the time recorded, is the measure, because Part III found that recorded direct time moved toward Packing and Quality Assurance and was often recorded after the operation had ended. The analytics type is descriptive.

Students can:

- measure each family's work orders, units, batch, run and setup hours and material issue lines without counting a fact twice (Part 1);
- measure each work center's available and practical hours, routing time used and its shares (Part 2);
- say why routing time is the right measure of use and what it leaves out (Part 3).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting) and Core S1 M8 (data analysis); IMA Strategic Cost Management and Operational Knowledge; IFAC IES 2 (b); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** MakeBuy.sql on CharlesRiver_Capstone.sqlite; Make Buy Reprice.xlsx with its Assumptions sheet, where the practical share sits.
- **Data conditions.** RoutingOperation holds the setup hours of a work order and the run hours of a unit at each work center. A work order can complete in parts. WorkCenterCalendar holds the available hours of {{ g.n_plant|count }} work centers. Recorded direct time is unreliable here: the direct hours recorded at {{ g.rec_top.name }} exceed its practical capacity.
- **Verify first.** In Q20 the run hours equal the standard labor hours completed, {{ run|num(2) }}, and the plant's routing time is {{ total|num(1) }}.

## How to run it

Pairs, about 90 minutes: 35 for the activity view, 10 for the per-thousand tables, 25 for the capacity table, 20 for the explanation. Routine for each query: type it, select it, **Execute all/selected SQL**, read the pane. Hold back that a work order can complete in parts until the setup hours come out too high. **Collect** the script and the Activities sheet (the Activity and Calendar Tables pasted with **Copy with Headers**, and the capacity table).

## Step-by-step solution

### Part 1: Each family's activities

**Step 1. Build the activity view at the grain of the work order.** Completions are summed to the work order first (`Done`), the routing is attached to it once (`Orders`), and the issue lines are counted for the work order (`Issues`). The families then sum those, and `Hours` multiplies run hours per unit by the units and adds each work order's setup once. The model saves the result as the view FamilyActivity (Q15). The block is a fragment, the first three CTEs, and the complete statement is Q15 in MakeBuy.sql.

```sql
Done AS (
    SELECT pc.WorkOrderID, SUM(pcl.QuantityCompleted) AS Units
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
    WHERE pc.CompletionDate BETWEEN '2026-01-01' AND '2026-12-31'
    GROUP BY pc.WorkOrderID
),
Orders AS (
    SELECT dn.WorkOrderID, dn.Units, wo.RoutingID,
        SUBSTR(i.ItemCode, 1, 7) AS Family, i.ItemGroup
    FROM Done AS dn
        INNER JOIN WorkOrder AS wo ON wo.WorkOrderID = dn.WorkOrderID
        INNER JOIN Item AS i ON i.ItemID = wo.ItemID
),
Issues AS (
    SELECT mi.WorkOrderID, COUNT(*) AS IssueLines
    FROM MaterialIssueLine AS mil
        INNER JOIN MaterialIssue AS mi
            ON mi.MaterialIssueID = mil.MaterialIssueID
    WHERE mi.WorkOrderID IN (SELECT WorkOrderID FROM Done)
    GROUP BY mi.WorkOrderID
),
```

**Check:** Q16 returns {{ g.n_q16|count }} rows; the run hours equal the standard hours completed and the setup hours total {{ g.setup_right|num(2) }}. **Watch for:**

- Setup counted once for every completion: {{ g.setup_wrong|num(2) }} hours instead of {{ g.setup_right|num(2) }}, because {{ g.n_completions|count }} completions belong to {{ g.n_orders|count }} work orders.
- Issue lines joined through the completions: {{ g.issues_wrong|count }} lines instead of {{ g.issues_true|count }}.
- A completion counted as a work order: the batch of Furniture falls to {{ g.furn_batch_wrong|num(1) }} units from {{ g.furn_batch|num(1) }}.

**Step 2. Express the activities per thousand units.** Setup hours and issue lines per thousand units make the families comparable.

```sql
-- Requirement 3, Q17: setup hours and material issue lines per thousand units, by family
-- Population: the view FamilyActivity; expected: small batches carry more setup per unit
SELECT Family, ItemGroup, WorkOrders, UnitsCompleted,
    ROUND(UnitsCompleted / WorkOrders, 1) AS AverageBatch,
    ROUND((COALESCE(CuttingSetup, 0)
        + COALESCE(AssemblySetup, 0)
        + COALESCE(FinishingSetup, 0)
        + COALESCE(PackingSetup, 0)
        + COALESCE(QASetup, 0))
        / UnitsCompleted * 1000, 1) AS SetupHoursPerThousand,
    ROUND(IssueLines / UnitsCompleted * 1000, 1)
        AS IssueLinesPerThousand
FROM FamilyActivity
ORDER BY Family;
```

**Check:** {{ g.n_q17|count }} rows. Q18 repeats it by item group: {{ small }}'s small batches carry about twice the setup per unit of the others (the Expected results).

### Part 2: What the plant had

**Step 3. Return the hours available.** Q19 sums WorkCenterCalendar's AvailableHours by work center for the year. **Check:** {{ g.n_q19|count }} rows, one for each work center.

**Step 4. Set the routing time beside the capacity.** The practical capacity is the assumed share of the available hours (`0.80` typed in the `Centers` CTE; the workbook reads it from the Assumptions sheet), the routing time is run plus setup, and a plant row adds the centers. The block is a fragment of Q20, its `Centers` and `Rows` CTEs and the final SELECT (the `Available` and `Used` CTEs above them are in MakeBuy.sql); run the complete query.

```sql
Centers AS (
    SELECT wc.WorkCenterID, wc.WorkCenterName, av.AvailableHours,
        av.AvailableHours * 0.80 AS PracticalHours,
        COALESCE(u.RunHours, 0) AS RunHours,
        COALESCE(u.SetupHours, 0) AS SetupHours
    FROM WorkCenter AS wc
        INNER JOIN Available AS av ON av.WorkCenterID = wc.WorkCenterID
        LEFT JOIN Used AS u ON u.WorkCenterID = wc.WorkCenterID
),
Rows AS (
    SELECT WorkCenterID, WorkCenterName, AvailableHours,
        PracticalHours, RunHours, SetupHours
    FROM Centers
    UNION ALL
    SELECT NULL, 'Plant', SUM(AvailableHours), SUM(PracticalHours),
        SUM(RunHours), SUM(SetupHours)
    FROM Centers
)
SELECT WorkCenterID, WorkCenterName,
    ROUND(AvailableHours, 2) AS AvailableHours,
    ROUND(PracticalHours, 2) AS PracticalHours,
    ROUND(RunHours, 2) AS RunHours, ROUND(SetupHours, 2) AS SetupHours,
    ROUND(RunHours + SetupHours, 1) AS RoutingHours,
    ROUND((RunHours + SetupHours) / AvailableHours, 3)
        AS ShareOfAvailable,
    ROUND((RunHours + SetupHours) / PracticalHours, 3)
        AS ShareOfPractical
FROM Rows
ORDER BY COALESCE(WorkCenterID, 99)
```

**Check:** the plant row: available {{ avail|num(2) }}, practical {{ pract|num(2) }}, routing time {{ used|num(1) }}, {{ of_avail|pct(1) }} of the available hours and {{ of_pract|pct(1) }} of the practical. Paste Q16 and Q19 into the Activities sheet as the Tables Activity and Calendar, and compute the shares there with formulas over the Assumptions share. **Watch for:** the direct hours recorded at {{ g.rec_top.name }}, {{ g.rec_top.hours|num(1) }}, as a measure of use: {{ g.rec_top.times|num(1) }} times its practical capacity and above its available hours, which cannot be use. Routing time never exceeds a center's capacity here.

{{ figure('IF-18-3-A') }}

### Part 3: Say what routing time measures

**Step 5. Write the two sentences.** Routing time is the right measure because it is what the products should take, measured independently of the time recorded, which drifted toward Packing and Quality Assurance and was often recorded after the operation ended. It leaves out the indirect activity routings do not list (maintenance, training, rework, scheduling) and the hours recorded above the routings that Part III found, and it takes the routings as right. So the unused capacity of Requirement 4 is an estimate from standard times, not a finding that those hours went unworked. It is the practical hours supplied less the run and setup hours the routings call for. It does not show that every indirect hour was idle or that a position can be removed, because normal support, maintenance, training and coverage need separate evaluation, and the practical share already allows for some normal nonproductive time.

{{ figure('IF-18-3-B') }}

## Expected results

| Group | Units completed | Work orders | Average batch | Setup hours per thousand units | Issue lines per thousand units |
|---|---:|---:|---:|---:|---:|
{% for a in acts %}
| {{ a.name }} | {{ a.units|num(1) }} | {{ a.wos|count }} | {{ a.batch|num(1) }} | {{ a.setup|num(1) }} | {{ a.issues|num(1) }} |
{% endfor %}

| Work center | Available | Practical | Routing time | Of available | Of practical |
|---|---:|---:|---:|---:|---:|
{% for c in centers %}
| {{ c.name }} | {{ c.avail|num(2) }} | {{ c.pract|num(2) }} | {{ c.used|num(1) }} | {{ c.of_avail|pct(1) }} | {{ c.of_pract|pct(1) }} |
{% endfor %}

{{ expected() }}

## What a strong answer says

- **Routing time is the measure of use.** It is what the products should take at the standard routings, independent of recorded time; the plant used {{ of_pract|pct(1) }} of its practical capacity.
- **What it leaves out.** Indirect activity the routings do not list and the hours recorded above them, which Requirement 4's unused capacity holds as an estimate, and any difference between the routing and the work. The practical share is the case's assumption, which Requirement 4's Data Table tests.
- **The activity differences.** {{ small }}'s small batches carry about twice the setup per unit, and more issue lines per unit.
- **Practical, not theoretical.** The controller's table sets practical capacity at a share of the available hours; reporting use on the available hours understates it.

A weak answer takes use from the time records, or reports a share without saying of which capacity.

## Common mistakes and how to respond

- **Setup per completion.** *Symptom:* {{ g.setup_wrong|num(2) }} setup hours. *Response:* ask how often a work order is set up.
- **Issue lines through completions.** *Symptom:* {{ g.issues_wrong|count }} lines. *Response:* ask which table holds the work order's issues.
- **A completion as a work order.** *Symptom:* a Furniture batch of {{ g.furn_batch_wrong|num(1) }}. *Response:* count the distinct work orders.
- **Recorded time as use.** *Symptom:* {{ g.rec_top.name }} above its capacity. *Response:* ask what Part III found about where time was recorded.
- **Use on the available hours.** *Symptom:* {{ of_avail|pct(1) }} called the use. *Response:* ask which capacity the assumptions table defines.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Activities by family | 35 | Work orders, units, batch, run and setup hours, issue lines; no fact counted twice | Totals that count setup or issues per completion |
| Capacity table | 30 | Available, practical, routing time and both shares for each center and the plant | Shares on one capacity only |
| Why routing time | 25 | Both sentences: why it measures use, and what it leaves out | Only the first |
| Workbook and documentation | 10 | Tables pasted, shares by formula over the Assumptions share | Typed shares |

## Extensions and discussion questions

- Repeat Q15 by item and list the five items with the most setup per unit.
- Rerun Q20 for each quarter and say whether the plant's use is steady.
- Discuss: Quality Assurance is used only a small share of its practical capacity. Does that make its cost idle?
- Discuss: what would the family costs of Requirement 4 look like on the recorded time?
