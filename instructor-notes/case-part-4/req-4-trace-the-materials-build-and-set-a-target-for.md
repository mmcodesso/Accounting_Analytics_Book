# Requirement 4: Trace the materials build and set a target for 2027 (Chapters 13 to 15; managerial accounting)

| | |
|---|---|
| Unit | Case Part 4: Finding the Cash Behind the Profit |
| Item | Requirement 4 |
| Perspective | Managerial accounting |
| Tools | Power BI Desktop |
| Time | About 150 minutes |
| Solution file | PartIV-case.zip: Charles River Cash Case.pbip, pages Materials Build and Materials Target, the queries IssuedByPair and ShortfallPairs, the what-if table Target Days, the display folder Materials and the Requirement 4 rows of the Checks tab |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Profit went into inventories, and this requirement says which inventory, through which channel, on whose approval, and what a return to the company's own targets would release. It joins documents the earlier chapters kept apart (receipts, order lines, requisitions, issues) with a text key and ends with a what-if that sizes the cash and states what the estimate leaves out. The analytics type is diagnostic, with a prescriptive end.

Students can:

- chart receipts by channel against issues, and the build by item (Step 1);
- group requisitions by the work order and item they name, and compare them with what was issued (Steps 2 and 3);
- show who approved each channel (Step 4);
- build a what-if for the target days and compare the excess with the fall in cash (Step 5);
- state what the estimate assumes, what it leaves out and how fast cash returns (Step 6).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis) and Core S1 M4; IMA Strategy, Planning, and Performance (strategic cost management) and Business Acumen and Operations (operational knowledge); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Requirements 1 to 3 done. The model answer is in PartIV-case.zip: the two pages, the queries and the table above.
- **From earlier work.** Tutorial 16.2's document key, Exercise 15.4's what-if, Exercise 15.3's field parameter and Chapter 13's combo chart.
- **Data conditions.** Shortfall justifications name one work order and one item; the opening materials of $3,587,025.70 carry no item detail; every inventory policy ends at the current year-end.
- **Verify first.** The 92 Requirement 4 rows of the Checks tab agree.

## How to run it

Pairs, about 150 minutes: 30 for the chart, 50 for the groups and approvals, 35 for the what-if, 25 for the assumptions, 10 spare. Hold back the approval matrix until the groups are built. **Collect** the .pbix and half a page on the target.

## Step-by-step solution

The Checks tab proves every value; the combo chart, the slider and the matrices are visible only in Desktop.

### Part 1: The build by channel and item

**Step 1. Chart the build.**

a. Add a **Line and clustered column chart** with YearMonth on the **X-axis**, the two channel receipts on **Column y-axis** and Materials Issued on **Line y-axis**, titled "Materials received by channel (columns) and issued (line), by month".
b. Add a **Matrix** with ItemGroup and ItemCode on **Rows** and Materials Build in **Values**, filtered to the current year, sorted descending and titled "The build of fiscal 2026 by item group and item".

```dax
Materials Build = [Materials Received] - [Materials Issued]

Supply Plan Receipts = CALCULATE ( [Materials Received], Receipts[Channel] = "Supply plan" )

Shortfall Receipts = CALCULATE ( [Materials Received], Receipts[Channel] = "Work-order shortfall" )
```

**Check:** receipts of the supply plan and the shortfall channel by year are $5,681,207.72 and $2,141,872.90; $7,017,928.00 and $6,472,674.93; $6,358,142.79 and $11,219,993.21, while issues stay near $10,161,204.64. The build of 2026 is $7,416,931.36, 96% of it six raw materials, led by RAW-CTN-0010 at $2,959,318.29. **Watch for:** a stock by item. The opening materials carry no item detail, so only a flow can be shown by item.

![A mock of the Materials Build page of the model answer, which shows the channel and the items that carry the build.](../figures/case-part-4/IF-C4-4-A.pdf)

### Part 2: The groups, the key and the approvals

**Step 2. Group the requisitions and build the key.**

a. Choose **Reference** on Requisitions, name it `ShortfallPairs`, and keep the shortfall channel.
b. Use **Group By** (**Advanced**) on Justification, WorkOrderNumber and ItemID with the count, the quantity and estimated value (sums), the first and last request dates, and the due and completed dates. Relate ShortfallPairs[ItemID] to Item, many to one, **Single** direction.
c. In Issues itself, name the column `PairKey`, choose **Add Column > Custom Column**, enter only the expression below and set the type to Text. Choose **Reference** on Issues, name it `IssuedByPair`, group it by PairKey with the issued quantity and cost, and clear **Enable load**. Merge it into ShortfallPairs with **Home > Merge Queries** (**Left Outer**) on Justification and PairKey. Issues keeps one row for each issue line.

```m
"WO-COMPONENT-SHORTFALL | WO=" & Text.From([WorkOrderID]) & " | ITEM=" & Text.From([ItemID])
```

**Check:** 10,365 pairs, 9,605 matched to issues and 760 with nothing issued. **Watch for:** two wrong versions. Grouping by work order alone gives 6,288 groups and a maximum of 39, against 18 for a pair. An inner join drops the 760 unmatched pairs, so the groups hold 9,605 pairs in place of 10,365, and the rolls requisitioned read 489,701.2 in place of 545,948.0.

**Step 3. Compare and count.** Add cards titled "Shortfall requisitions by work order and item" and a table titled "The pairs requisitioned most often" sorted by the count.

**Check:** 5,702 pairs were requisitioned more than once, holding 16,774 requisitions. By unit of measure, 545,948.0 rolls were requisitioned against 251,235.0 issued and 1,242.8 boxes were requisitioned against 1,139.2 issued to the same pairs, and in value the requisitions' estimate of $20,623,419.07 sits beside $8,925,946.87 issued at standard, two different bases. **Watch for:** a card that adds rolls and boxes into one total of 547,190.8 units. The model answer shows the units in a table by unit of measure, and its unit measures are blank across units. The pair with the most is WO-2025-008090 and RAW-CTN-0010: 18 requisitions, one or two a month from 2025-08-13 to 2026-11-01, for a work order due 2025-08-17 and completed 2026-12-01.

**Step 4. Show the approvals.** Add a **Matrix** titled "Who approved the requisitions of each channel" with Channel and ApproverTitle on **Rows** and the requisition count and `Self-requested` in **Values**.

**Check:** the Production Manager approved all 21,437 shortfall requisitions, 351 of them requested by the same employee; production staff requested the rest. The CFO approved 3,915 supply-plan requisitions and 6 have no approver.

### Part 3: The target

**Step 5. Add the what-if.**

a. Choose **Modeling > New parameter > Numeric range**, **Whole number**, named `Target Days`, with Minimum 7, Maximum 120 and Increment 1. Keep **Add slicer to this page**.
b. Add the measures below, with the largest materials target (28 days, raw materials) as the default, a benchmark for the whole balance. Select it in the slicer, save, close and reopen the report, and check that the slicer and `Target Days Value` both show it.
c. Add a **Table** titled "Targets tested at the end of fiscal 2026" filtered to 28, 60 and 90 days, and set the slider's **Edit interactions** to **None** toward it, so the tested targets stay independent of the slider.

```dax
Target Days Value = SELECTEDVALUE ( 'Target Days'[Target Days], 28 )

Allowed Materials = DIVIDE ( [Issues TTM], 365 ) * [Target Days Value]

Excess Materials = [Materials] - [Allowed Materials]

Months of Issues in Excess = DIVIDE ( [Excess Materials], DIVIDE ( [Issues TTM], 12 ) )
```

**Check:** at the year's issues the target allows $779,489.67, $1,670,335.01, $2,505,502.51 and the excess is $10,972,164.25, $10,081,318.91, $9,246,151.41, or 12.96, 11.91, 10.92 months of issues. Even at 90 days the excess is about ten times the year's fall in cash. **Watch for:** the excess measured on all the inventories, which reads $23,202,961.33 at 28 days because finished goods and work in process are in it, and a slider left at the series' first value of 7 days, which reads $11,556,781.50. Each class at its own target (packaging at 24 days) allows $774,303.26 and leaves $10,977,350.66, an accepted alternative when its definition is stated.

![The excess at each target next to the year's fall in cash, the comparison the requirement asks for.](../figures/case-part-4/IF-C4-4-B.pdf)

### Part 4: What the estimate leaves out

**Step 6. State the limits.** Add cards titled "What the estimate leaves out" for the finished goods, the open requisitions and the open order lines.

**Check:** finished goods at the target would be $1,213,408.82 against $12,169,701.74; 522 approved requisitions are unordered ($510,445.06); 486 order lines are not fully received ($617,265.16, $408,584.88 of it materials); every policy ends at the year-end. The cash comes back only as purchases fall below use, over 2027 and after, and only if the stock can be used.

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax
EVALUATE
ROW (
    "Pairs", [Pairs],
    "Repeated pairs", [Repeated Pairs],
    "Pairs with issues", [Pairs with Issues],
    "Excess at 28 days", ROUND ( CALCULATE ( [Excess Materials], 'Date'[Year] = 2026, 'Target Days'[Target Days] = 28 ), 2 ),
    "Open requisitions", [Open Requisitions]
)
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Receipts, 2026: supply plan; shortfall | $6,358,142.79; $11,219,993.21 | 1 |
| Build of 2026; packaging | $7,416,931.36; -$5,594.49 | 1 |
| Pairs; matched; repeated; most for one pair | 10,365; 9,605; 5,702; 18 | 2, 3 |
| Excess at 28, 60, 90 days | $10,972,164.25; $10,081,318.91; $9,246,151.41 | 5 |

> **Instructor notes, Requirement 4:** materials receipts by channel (supply plan / work-order shortfall): 2024 5,681,207.72 (336 lines) / 2,141,872.90 (3,094 lines); 2025 7,017,928.00 (390) / 6,472,674.93 (8,077); 2026 6,358,142.79 (363) / 11,219,993.21 (12,615); issues stayed near 10 million (2026: raw materials 9,687,944.26, packaging 473,260.38). The supply plan's receipts stay below production's use, which holds steady; the shortfall channel carries the build. 2026 build 7,416,931.36, of which six raw materials make up about 96%: RAW-CTN-0010 Cotton Fabric Roll +2,959,318.29, RAW-LED-0005 LED Module Pack +1,153,243.40, RAW-LIN-0008 +1,134,217.41, RAW-LIN-0002 +797,202.63, RAW-LIN-0006 +549,623.46, RAW-LIN-0004 +521,297.17 (Linen Fabric Rolls); packaging nets -5,594.49. Stock by item cannot be rebuilt, because the opening materials of 3,587,025.70 carry no item detail, so the build by item is a flow, not each item's stock. Shortfall requisitions: 3,180 / 7,304 / 10,953 a year, estimated at 2,466,594.50 / 6,813,074.37 / 11,343,750.21; 10,365 work order and item pairs, of which 5,702 were requisitioned more than once, holding 16,774 requisitions; at most 18 for one pair, WO-2025-008090 and RAW-CTN-0010, every month from 2025-08-13 to 2026-11-01, one or two a month (the work order was due 2025-08-17 and completed 2026-12-01). Merge key "WO-COMPONENT-SHORTFALL \| WO=" & Text.From ( \[WorkOrderID\] ) & " \| ITEM=" & Text.From ( \[ItemID\] ): 9,605 pairs matched, 760 with nothing issued. Quantities add only within a unit of measure, so the model answer shows 545,948.0 rolls requisitioned against 251,235.0 issued and 1,242.8 boxes requisitioned against 1,139.2 issued to the same pairs. In value, the requisitions were estimated at 20,623,419.07 at their own unit costs, against 8,925,946.87 issued at standard, two different bases. Approvals: every shortfall requisition (21,437) was approved by employee 4, the Production Manager, who also requested 351 of them; production staff requested the rest (Assemblers 7,631, Machine Operators 7,111, Quality Technicians 5,706, Production Planners 324, Production Supervisors 314); the CFO approved 3,915 supply-plan requisitions, 6 have no approver; the six capital requests were approved by the CFO (4) and the Purchasing Manager (2). What-if (twelve-month issues 10,161,204.64): 28 days allows 779,489.67, an excess of 10,972,164.25, 12.96 months of issues; 60 days 1,670,335.01, 10,081,318.91, 11.91 months; 90 days 2,505,502.51, 9,246,151.41, 10.92 months; even at 90 days the excess is about ten times the year's fall in cash. The default is the largest materials target, a benchmark for the whole balance. Each class at its own target (raw materials 28, packaging 24) allows 774,303.26 and leaves 10,977,350.66, an accepted alternative when its definition is stated. 522 approved, unordered shortfall requisitions (510,445.06). Optional: shortfall requisitions dated after their work order's due date numbered 137, 2,178, and 5,039 a year (estimated 69,032.98, 2,186,214.31, and 5,372,871.72). Engine-checked.

## What a strong answer says

- **Channel and items.** The supply plan's receipts stay below use; the shortfall channel carries the build; six raw materials make up most of it.
- **Requisitions.** Repeated for one work order and item, long after the order was due, and approved by one manager, while the records do not show whether stock on hand or open orders were checked. The wording describes the records, not a person.
- **Target.** A stated benchmark (the largest materials target, or each class at its own) reached by buying less than production uses, an interim target for the committee, the controller's approval because the policies have ended, and the excess several times the fall in cash even at the longest target.
- **Limits.** Issues continue at the year's rate, the stock is usable at standard, finished goods and open orders are left out, and the policies need approval.

## Common mistakes and how to respond

- **Channel through the header.** *Symptom:* blank channels on most receipt lines. *Response:* ask which table names the requisition for each line.
- **Group by work order alone.** *Symptom:* a maximum of 39. *Response:* ask what the justification names besides the work order.
- **Inner join.** *Symptom:* 9,605 pairs, or 489,701.2 rolls requisitioned. *Response:* ask which pairs have no issue.
- **Rolls and boxes added.** *Symptom:* a card of 547,190.8 units. *Response:* ask what one unit is.
- **Excess on all inventories.** *Symptom:* $23,202,961.33. *Response:* ask which balance the target covers.
- **Default left at the first value.** *Symptom:* cards at 7 days. *Response:* ask what the policy target is.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Build by channel and item | 25 | Chart and matrix; channel and items named | Chart without the explanation |
| Groups, key and approvals | 35 | Pairs, key, comparison, repeated count, approvals; neutral wording | Groups without the comparison |
| Target | 25 | Parameter with default; three targets; excess against the fall in cash | One target |
| Limits | 15 | Assumptions, omissions and timing stated | Limits named, not sized |

## Extensions and discussion questions

- Add the shortfall requisitions dated after their work order's due date, by year, and say what they suggest.
- Rebuild the excess for packaging at its own target.
- Discuss: one manager runs production and approves its purchases. What control would you add, and what would it cost?
- Discuss: should the committee approve the 2027 targets, and on what evidence?
