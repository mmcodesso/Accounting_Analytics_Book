---
note: case4.r4
uses: [case4.g4]
title: Trace the materials build and set a target for 2027 (Chapters 13 to 15; managerial accounting)
kind: requirement
number: '4'
unit: case4
perspective: managerial
tool: powerbi
minutes: 150
solution: "PartIV-case.zip: Charles River Cash Case.pbip, pages Materials Build and Materials Target, the queries IssuedByPair and ShortfallPairs, the what-if table Target Days, the display folder Materials and the Requirement 4 rows of the Checks tab"
figures:
  - id: IF-C4-4-A
    kind: pbi-mock
    purpose: The Materials Build page of the model answer, which shows the channel and the items that carry the build.
    shows: "Report view, page Materials Build. A line and clustered column chart by month with two columns for each month, supply plan receipts and work-order shortfall receipts, and a line for materials issued; a table of the yearly totals; a matrix by item group and item, expanded and sorted by the build, with six raw materials at the top; and a matrix of the approver titles for each channel."
    data: The Expected results quantities (receipts by channel and year, the build by item, the approvals), read-only.
  - id: IF-C4-4-B
    kind: chart
    purpose: The excess at each target next to the year's fall in cash, the comparison the requirement asks for.
    shows: "Four horizontal bars of dollars: the excess at 28 days, at 60 days and at 90 days, and the year's fall in cash. The three excess bars are each many times the length of the fall; labels give the months of issues the excess represents."
    data: The Expected results quantities (the excess at each target, the months of issues and the fall in cash), read-only.
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = case4_g4 %}
# Requirement 4: Trace the materials build and set a target for 2027 (Chapters 13 to 15; managerial accounting)

{{ header() }}

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
- **Data conditions.** Shortfall justifications name one work order and one item; the opening materials of ${{ opening_materials|money }} carry no item detail; every inventory policy ends at the current year-end.
- **Verify first.** The {{ g.n_checks }} Requirement 4 rows of the Checks tab agree.

## How to run it

Pairs, about 150 minutes: 30 for the chart, 50 for the groups and approvals, 35 for the what-if, 25 for the assumptions, 10 spare. Hold back the approval matrix until the groups are built. **Collect** the .pbix and half a page on the target.

## Step-by-step solution

The Checks tab proves every value; the combo chart, the slider and the matrices are visible only in Desktop.

### Part 1: The build by channel and item

**Step 1. Chart the build.**

a. Add a **Line and clustered column chart** with YearMonth on the **X-axis**, the two channel receipts on **Column y-axis** and Materials Issued on **Line y-axis**, titled "{{ g.t_receipts }}".
b. Add a **Matrix** with ItemGroup and ItemCode on **Rows** and Materials Build in **Values**, filtered to the current year, sorted descending and titled "{{ g.t_build }}".

```dax jinja
{{ g.d_build }}
```

**Check:** receipts of the supply plan and the shortfall channel by year are {% for r in by_year %}${{ r.plan[1]|money }} and ${{ r.short[1]|money }}{{ "; " if not loop.last else "" }}{% endfor %}, while issues stay near ${{ ttm|money }}. The build of {{ d.C }} is ${{ build|money }}, {{ share|pct(0) }} of it six raw materials, led by {{ top_items[0].code }} at ${{ top_items[0].amount|money }}. **Watch for:** a stock by item. The opening materials carry no item detail, so only a flow can be shown by item.

{{ figure('IF-C4-4-A') }}

### Part 2: The groups, the key and the approvals

**Step 2. Group the requisitions and build the key.**

a. Choose **Reference** on Requisitions, name it `ShortfallPairs`, and keep the shortfall channel.
b. Use **Group By** (**Advanced**) on Justification with the count, the quantity, the estimated value and the first and last dates.
c. In Issues, add `PairKey` with **Add Column > Custom Column**, group Issues by it as `IssuedByPair`, and merge the issued quantity into the groups with **Home > Merge Queries** (**Left Outer**).

```m jinja
{{ g.key_m }}
```

**Check:** {{ pairs|count }} pairs, {{ matched|count }} matched to issues and {{ unmatched }} with nothing issued. **Watch for:** two wrong versions. Grouping by work order alone gives {{ g.wo_groups|count }} groups and a maximum of {{ g.wo_most }}, against {{ most }} for a pair. An inner join drops the {{ unmatched }} unmatched pairs, so the groups hold {{ matched|count }} pairs in place of {{ pairs|count }}, and the {{ by_unit[0].plural }} requisitioned read {{ g.main_inner|num(1) }} in place of {{ by_unit[0].req|num(1) }}.

**Step 3. Compare and count.** Add cards titled "{{ g.t_cards }}" and a table titled "{{ g.t_pairs }}" sorted by the count.

**Check:** {{ repeated|count }} pairs were requisitioned more than once, holding {{ in_repeated|count }} requisitions. By unit of measure, {% for u in by_unit %}{{ u.req|num(1) }} {{ u.plural }} were requisitioned against {{ u.issued|num(1) }} issued{{ " and " if not loop.last else "" }}{% endfor %} to the same pairs, and in value the requisitions' estimate of ${{ estimated|money }} sits beside ${{ issued_cost|money }} issued at standard, two different bases. **Watch for:** a card that adds rolls and boxes into one total of {{ units|num(1) }} units. The model answer shows the units in a table by unit of measure, and its unit measures are blank across units. The pair with the most is {{ wo }} and {{ item }}: {{ most }} requisitions, one or two a month from {{ first_request }} to {{ last_request }}, for a work order due {{ due }} and completed {{ completed }}.

**Step 4. Show the approvals.** Add a **Matrix** titled "{{ g.t_approvals }}" with Channel and ApproverTitle on **Rows** and the requisition count and `Self-requested` in **Values**.

**Check:** the {{ approver_title }} approved all {{ n_short|count }} shortfall requisitions, {{ self_requested }} of them requested by the same employee; production staff requested the rest. The CFO approved {{ cfo_plan|count }} supply-plan requisitions and {{ no_plan }} have no approver.

### Part 3: The target

**Step 5. Add the what-if.**

a. Choose **Modeling > New parameter > Numeric range**, **Whole number**, named `Target Days`; keep **Add slicer to this page**.
b. Add the measures below, with the largest materials target ({{ g.raw_target }} days, raw materials) as the default, a benchmark for the whole balance.
c. Add a **Table** titled "{{ g.t_tested }}" filtered to {{ whatif[0].days }}, {{ whatif[1].days }} and {{ whatif[2].days }} days.

```dax jinja
{{ g.d_target }}
```

**Check:** at the year's issues the target allows {% for w in whatif %}${{ w.allowed|money }}{{ ", " if not loop.last else "" }}{% endfor %} and the excess is {% for w in whatif %}${{ w.excess|money }}{{ ", " if not loop.last else "" }}{% endfor %}, or {% for w in whatif %}{{ w.months|num(2) }}{{ ", " if not loop.last else "" }}{% endfor %} months of issues. Even at {{ whatif[2].days }} days the excess is about {{ multiple }} times the year's fall in cash. **Watch for:** the excess measured on all the inventories, which reads ${{ g.all_inv_excess|money }} at {{ whatif[0].days }} days because finished goods and work in process are in it, and a slider left at the series' first value of {{ g.low_days }} days, which reads ${{ g.low_excess|money }}. Each class at its own target (packaging at {{ g.pack_target }} days) allows ${{ policy_allowed|money }} and leaves ${{ policy_excess|money }}, an accepted alternative when its definition is stated.

{{ figure('IF-C4-4-B') }}

### Part 4: What the estimate leaves out

**Step 6. State the limits.** Add cards titled "{{ g.t_left }}" for the finished goods, the open requisitions and the open order lines.

**Check:** finished goods at the target would be ${{ fg_target|money }} against ${{ fg|money }}; {{ n_never }} approved requisitions are unordered (${{ never_value|money }}); {{ open_lines }} order lines are not fully received (${{ open_value|money }}, ${{ open_materials|money }} of it materials); every policy ends at the year-end. The cash comes back only as purchases fall below use, over {{ d.N }} and after, and only if the stock can be used.

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax jinja
{{ g.dax_check }}
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Receipts, {{ d.C }}: supply plan; shortfall | ${{ by_year[-1].plan[1]|money }}; ${{ by_year[-1].short[1]|money }} | 1 |
| Build of {{ d.C }}; packaging | ${{ build|money }}; {{ sm(packaging) }} | 1 |
| Pairs; matched; repeated; most for one pair | {{ pairs|count }}; {{ matched|count }}; {{ repeated|count }}; {{ most }} | 2, 3 |
| Excess at {{ whatif[0].days }}, {{ whatif[1].days }}, {{ whatif[2].days }} days | ${{ whatif[0].excess|money }}; ${{ whatif[1].excess|money }}; ${{ whatif[2].excess|money }} | 5 |

{{ expected() }}

## What a strong answer says

- **Channel and items.** The supply plan's receipts stay below use; the shortfall channel carries the build; six raw materials make up most of it.
- **Requisitions.** Repeated for one work order and item, long after the order was due, and approved by one manager, while the records do not show whether stock on hand or open orders were checked. The wording describes the records, not a person.
- **Target.** A stated benchmark (the largest materials target, or each class at its own) reached by buying less than production uses, an interim target for the committee, the controller's approval because the policies have ended, and the excess several times the fall in cash even at the longest target.
- **Limits.** Issues continue at the year's rate, the stock is usable at standard, finished goods and open orders are left out, and the policies need approval.

## Common mistakes and how to respond

- **Channel through the header.** *Symptom:* blank channels on most receipt lines. *Response:* ask which table names the requisition for each line.
- **Group by work order alone.** *Symptom:* a maximum of {{ g.wo_most }}. *Response:* ask what the justification names besides the work order.
- **Inner join.** *Symptom:* {{ matched|count }} pairs, or {{ g.main_inner|num(1) }} {{ by_unit[0].plural }} requisitioned. *Response:* ask which pairs have no issue.
- **Rolls and boxes added.** *Symptom:* a card of {{ units|num(1) }} units. *Response:* ask what one unit is.
- **Excess on all inventories.** *Symptom:* ${{ g.all_inv_excess|money }}. *Response:* ask which balance the target covers.
- **Default left at the first value.** *Symptom:* cards at {{ g.low_days }} days. *Response:* ask what the policy target is.

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
- Discuss: should the committee approve the {{ d.N }} targets, and on what evidence?
