# Requirement 3: Measure the activities and the capacity (Chapters 10 and 11)

| | |
|---|---|
| Unit | Chapter 18: Make, Buy, or Reprice |
| Item | Requirement 3 |
| Perspective | Managerial accounting |
| Tools | More than one tool |
| Time | About 90 minutes |
| Solution file | Chapter18-capstone-sql.zip: MakeBuy.sql, the queries headed Requirement 3 (Q15 to Q20); Chapter18-capstone-excel.zip: Make Buy Reprice.xlsx, worksheet Activities |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

What a family uses of the plant comes from the routings, multiplied by what was made; what the plant had comes from its calendar. Both are joins and sums over the year's work orders, which SQL handles directly, and the result is the capacity table that Requirements 4 to 7 read. Routing time, not the time recorded, is the measure, because Part III found that recorded direct time moved toward Packing and Quality Assurance and was often recorded after the operation had ended. The analytics type is descriptive.

Students can:

- measure each family's work orders, units, batch, run and setup hours and material issue lines without counting a fact twice (Part 1);
- measure each work center's available and practical hours, routing time used and its shares (Part 2);
- say why routing time is the right measure of use and what it leaves out (Part 3).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting) and Core S1 M8 (data analysis); IMA Strategic Cost Management and Operational Knowledge; IFAC IES 2 (b); AACSB A5 part 5.1 (SQL).

## Before you assign

- **Files.** MakeBuy.sql on CharlesRiver_Capstone.sqlite; Make Buy Reprice.xlsx with its Assumptions sheet, where the practical share sits.
- **Data conditions.** RoutingOperation holds the setup hours of a work order and the run hours of a unit at each work center. A work order can complete in parts. WorkCenterCalendar holds the available hours of 5 work centers. Recorded direct time is unreliable here: the direct hours recorded at Packing exceed its practical capacity.
- **Verify first.** In Q20 the run hours equal the standard labor hours completed, 68,912.79, and the plant's routing time is 73,822.9.

## How to run it

Pairs, about 90 minutes: 35 for the activity view, 10 for the per-thousand tables, 25 for the capacity table, 20 for the explanation. Routine for each query: type it, select it, **Execute all/selected SQL**, read the pane. Hold back that a work order can complete in parts until the setup hours come out too high. **Collect** the script and the Activities sheet (the Activity and Calendar Tables pasted with **Copy with Headers**, and the capacity table).

## Step-by-step solution

### Part 1: Each family's activities

**Step 1. Build the activity view at the grain of the work order.** Completions are summed to the work order first (`Done`), the routing is attached to it once (`Orders`), and the issue lines are counted for the work order (`Issues`). The families then sum those, and `Hours` multiplies run hours per unit by the units and adds each work order's setup once. The model saves the result as the view FamilyActivity (Q15).

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

**Check:** Q16 returns 16 rows; the run hours equal the standard hours completed and the setup hours total 4,910.11. **Watch for:**

- Setup counted once for every completion: 6,562.36 hours instead of 4,910.11, because 5,314 completions belong to 3,984 work orders.
- Issue lines joined through the completions: 30,658 lines instead of 21,276.
- A completion counted as a work order: the batch of Furniture falls to 8.1 units from 10.8.

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

**Check:** 16 rows. Q18 repeats it by item group: Furniture's small batches carry about twice the setup per unit of the others (the Expected results).

### Part 2: What the plant had

**Step 3. Return the hours available.** Q19 sums WorkCenterCalendar's AvailableHours by work center for the year. **Check:** 5 rows, one for each work center.

**Step 4. Set the routing time beside the capacity.** The practical capacity is the assumed share of the available hours (`0.80` typed in the `Centers` CTE; the workbook reads it from the Assumptions sheet), the routing time is run plus setup, and a plant row adds the centers.

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

**Check:** the plant row: available 128,833.25, practical 103,066.60, routing time 73,822.9, 57.3% of the available hours and 71.6% of the practical. Paste Q16 and Q19 into the Activities sheet as the Tables Activity and Calendar, and compute the shares there with formulas over the Assumptions share. **Watch for:** the direct hours recorded at Packing, 33,026.9, as a measure of use: 3.0 times its practical capacity and above its available hours, which cannot be use. Routing time never exceeds a center's capacity here.

![A mock of the capacity query with its six-row result, the table every later requirement reads.](../figures/chapter-18-make-buy-or-reprice/IF-18-3-A.pdf)

### Part 3: Say what routing time measures

**Step 5. Write the two sentences.** Routing time is the right measure because it is what the products should take, measured independently of the time recorded, which drifted toward Packing and Quality Assurance and was often recorded after the operation ended. It leaves out the indirect activity routings do not list (maintenance, training, rework, scheduling) and the hours recorded above the routings that Part III found, and it takes the routings as right. So the unused capacity of Requirement 4 is an estimate from standard times, not a finding that those hours went unworked.

![Where the plant's hours go, work center by work center.](../figures/chapter-18-make-buy-or-reprice/IF-18-3-B.pdf)

## Expected results

| Group | Units completed | Work orders | Average batch | Setup hours per thousand units | Issue lines per thousand units |
|---|---:|---:|---:|---:|---:|
| Furniture | 28,052.6 | 2,604 | 10.8 | 127.9 | 543.3 |
| Lighting | 18,865.1 | 1,160 | 16.3 | 57.8 | 257.0 |
| Textiles | 4,242.3 | 220 | 19.3 | 54.7 | 279.6 |

| Work center | Available | Practical | Routing time | Of available | Of practical |
|---|---:|---:|---:|---:|---:|
| Cutting | 25,655.58 | 20,524.46 | 12,313.7 | 48.0% | 60.0% |
| Assembly | 55,177.04 | 44,141.63 | 34,435.8 | 62.4% | 78.0% |
| Finishing and Test | 30,234.03 | 24,187.22 | 19,064.8 | 63.1% | 78.8% |
| Packing | 13,809.10 | 11,047.28 | 7,648.5 | 55.4% | 69.2% |
| Quality Assurance | 3,957.50 | 3,166.00 | 360.2 | 9.1% | 11.4% |

> **Instructor notes, Requirement 3:** 2026 completions by group (units / work orders / batch / setup hours per 1,000 units / issue lines per 1,000 units): Furniture 28,052.6 / 2,604 / 10.8 / 127.9 / 543.3; Lighting 18,865.1 / 1,160 / 16.3 / 57.8 / 257.0; Textiles 4,242.3 / 220 / 19.3 / 54.7 / 279.6. Furniture's small batches carry twice the setup per unit. Routing time on 2026 completions: run 68,912.79 hours (equal to the standard labor hours) plus setup 4,910.11 = 73,822.90. Work centers (available / practical at 80% / used / of available / of practical): Cutting 25,655.58 / 20,524.46 / 12,313.7 / 48.0% / 60.0%; Assembly 55,177.04 / 44,141.63 / 34,435.8 / 62.4% / 78.0%; Finishing and Test 30,234.03 / 24,187.22 / 19,064.8 / 63.1% / 78.8%; Packing 13,809.10 / 11,047.28 / 7,648.5 / 55.4% / 69.2%; Quality Assurance 3,957.50 / 3,166.00 / 360.2 / 9.1% / 11.4%; plant 128,833.25 / 103,066.60 / 73,822.9 / 57.3% / 71.6%. Routing time measures what the products should use at the standard routings. It leaves out the indirect activity routings do not list (maintenance, training, rework, scheduling) and the hours recorded above the routings that Part III found, so the unused capacity of Requirement 4 is an estimate from standard times on the case's practical share, not a finding that those hours went unworked.

## What a strong answer says

- **Routing time is the measure of use.** It is what the products should take at the standard routings, independent of recorded time; the plant used 71.6% of its practical capacity.
- **What it leaves out.** Indirect activity the routings do not list and the hours recorded above them, which Requirement 4's unused capacity holds as an estimate, and any difference between the routing and the work. The practical share is the case's assumption, which Requirement 4's Data Table tests.
- **The activity differences.** Furniture's small batches carry about twice the setup per unit, and more issue lines per unit.
- **Practical, not theoretical.** The controller's table sets practical capacity at a share of the available hours; reporting use on the available hours understates it.

A weak answer takes use from the time records, or reports a share without saying of which capacity.

## Common mistakes and how to respond

- **Setup per completion.** *Symptom:* 6,562.36 setup hours. *Response:* ask how often a work order is set up.
- **Issue lines through completions.** *Symptom:* 30,658 lines. *Response:* ask which table holds the work order's issues.
- **A completion as a work order.** *Symptom:* a Furniture batch of 8.1. *Response:* count the distinct work orders.
- **Recorded time as use.** *Symptom:* Packing above its capacity. *Response:* ask what Part III found about where time was recorded.
- **Use on the available hours.** *Symptom:* 57.3% called the use. *Response:* ask which capacity the assumptions table defines.

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
