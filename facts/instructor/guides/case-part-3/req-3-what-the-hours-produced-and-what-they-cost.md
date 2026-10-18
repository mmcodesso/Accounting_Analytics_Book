---
note: case3.r3
uses: [case3.g3]
title: What the hours produced and what they cost (Chapters 10 and 11; managerial accounting)
kind: requirement
number: '3'
unit: case3
perspective: managerial
tool: sql
minutes: 150
solution: "PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 3 (the hours against output, the view PlantWeeks, the capacity and cost queries, the view PlantLedger, the bridge and the three measures), and the Requirement 3 model answer in its closing comments"
figures:
  - id: IF-C3-3-A
    kind: chart
    purpose: The bridge of account 5080 from the first fiscal year to the last, the exhibit that carries the cost story into the memo.
    shows: "A waterfall. The first bar is 5080 in the first year, then one step for each ledger line (payroll charged to 1090, journal entries, standard cost released, change in 1090, material variance, direct postings), signed and labeled, and a last bar for 5080 in the last year. Increases and decreases differ in fill and in the sign of the label."
    data: The bridge query of Step 5, run read-only.
---
{% set g = case3_g3 %}
# Requirement 3: What the hours produced and what they cost (Chapters 10 and 11; managerial accounting)

{{ header() }}

## Purpose and learning outcomes

This requirement asks what the surge hours bought and what they cost, on three calendars that must not be mixed. It also teaches the difference between a bridge, which sums to the ledger, and measures, which explain a line and may overlap. The analytics type is diagnostic.

Students can:

- compare hours with output by year and week, with a window frame, and state the limits (Steps 1 and 2);
- measure capacity used and cost the overtime two ways (Steps 3 and 4);
- bridge a ledger account into lines that sum to the change (Step 5);
- explain a line with measures on stated calendars, and say why they overlap (Step 6).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Reporting and Control (cost accounting) and Business Acumen and Operations (operational knowledge); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql with SurgeDays and PlantEntries (Requirement 1). It builds on Chapter 10's measure of the plant (Tutorial 10.3), Chapter 11's frames and Tutorial 12.3's test H5. Tutorial 11.3's view MonthlyLaborEfficiency, from the chapter or from Setup_Part3_Views.sql with **Write Changes**; without it the December query fails with "{{ g.err }}".
- **Data conditions.** Time records end on {{ cutoff }}; completions run to the year-end; the first fiscal year charged {{ lf.paydates }} payrolls to 1090 and the last {{ lc.paydates }}. GLEntry.AccountID is not the account number.
- **Verify first.** The bridge returns {{ g.n.bridge }} row, and the unexplained column of the ledger query is zero in every year.

## How to run it

Pairs, about 150 minutes: 30 for output against hours and the weekly view, 20 for capacity and cost, 40 for the ledger view and bridge, 35 for the three measures, 25 for the explanation. Hold back the measures until the bridge sums. **Collect** the script and the bridge.

## Step-by-step solution

### Part 1: Output against hours

**Step 1. Compare hours with output by year.** An Output CTE sums the standard hours of completions up to the last day with time records, an Hours CTE sums clocked hours and overtime by day type, and the query divides.

```sql
WITH Output AS (
    SELECT strftime('%Y', pc.CompletionDate) AS WorkYear,
        SUM(pcl.QuantityCompleted * i.StandardLaborHoursPerUnit)
            AS StandardHours
    FROM ProductionCompletionLine AS pcl
        INNER JOIN ProductionCompletion AS pc
            ON pc.ProductionCompletionID = pcl.ProductionCompletionID
        INNER JOIN Item AS i ON i.ItemID = pcl.ItemID
    WHERE pc.CompletionDate <= (SELECT MAX(WorkDate) FROM TimeClockEntry)
    GROUP BY WorkYear
),
```

**Check:**{% for y in ys %} {{ y.year }}, {{ y.hours|num }} hours against {{ y.std|num }} standard, {{ y.ratio|num(3) }}{{ ";" if not loop.last else "." }}{% endfor %} Surge overtime rises from {{ ys[0].surge.overtime|num }} to {{ ys[-1].surge.overtime|num }} hours: output flat, surge overtime {{ grew }}. The December values of the view agree to two decimals, but the view is no coverage test. Its indirect time ends on {{ g.ind_end }}, so its last row is provisional, and counted to that day on both sides the last year's direct ratio is somewhat lower and the indirect a little higher (Chapter 10). **Watch for:** without the cut-off the last year reads {{ g.no_cut[2]|num }} standard hours and {{ g.no_cut[3]|num(3) }}.

**Step 2. Build the weekly view, group the weeks by surge days, and state the limits.** PlantWeeks holds each Monday week's clocked hours, surge days and standard hours completed up to {{ cutoff }}, with the average output of up to six following weeks in a window frame and the number of weeks the frame holds.

```sql
    AVG(COALESCE(o.StandardHours, 0)) OVER (
        ORDER BY h.WeekStart
        ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING
    ) AS NextSixWeeks,
    COUNT(*) OVER (
        ORDER BY h.WeekStart
        ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING
    ) AS FollowingWeeks
```

**Check:** in the last year {{ other.n }} weeks without surge days average {{ other.hours|num }} hours and {{ other.std|num }} standard hours ({{ other.ratio|num(2) }}); the {{ surge.n }} weeks with surge days {{ surge.hours|num }} and {{ surge.std|num }} ({{ surge.ratio|num(2) }}). The following weeks average {{ surge.next|num }} standard hours after a surge week, against {{ other.next|num }}. The last {{ g.short }} frames of the year hold fewer than six weeks and the last week stops on the cut-off, and over six complete following weeks (the sensitivity query of the model script, which drops the final partial week) the figures are {{ g.six.Surge[2]|num(2) }} after {{ g.six.Surge[1] }} surge weeks against {{ g.six.Ordinary[2]|num(2) }} after {{ g.six.Ordinary[1] }}. `FollowingWeeks = 6` alone adds {{ g.six_open.Surge[1] - g.six.Surge[1] }} surge week whose frame holds the partial week. The comparison reads {{ d.C }}, while PlantWeeks keeps every year. That is consistent with output timing, including work brought forward, but cannot show which hours produced the output: work orders closed in the last year took about {{ lead|num }} days from release to completion, and {{ g.limits[1]|count }} of {{ g.limits[2]|count }} completions fall on weekends. **Watch for:** three wrong versions.

- Without the cut-off in the view's Output CTE the last week takes in {{ tail.hours|num(1) }} standard hours completed after {{ cutoff }}, and surge weeks read {{ g.surge_no_cut[4]|num }}.

- `ROWS UNBOUNDED PRECEDING` averages the earlier weeks, and every group reads about the same ({{ g.cum_next|min|num }} to {{ g.cum_next|max|num }}).
- `CURRENT ROW AND 5 FOLLOWING` mixes the week's own output into its follow-on ({{ g.own_next|map('num')|join(', ') }} against {{ g.groups|map(attribute=5)|map('num')|join(', ') }}).

### Part 2: Capacity and cost

**Step 3. Measure the capacity the ordinary days used.** Sum each employee's entries by work date first, because a few employee-days carry two entries, then average the ordinary employee-days and total the straight-time hours left unused on days under eight regular hours.

```sql
    ROUND(SUM(CASE WHEN DayType = 'Ordinary' AND RegularHours < 8
        THEN 8 - RegularHours ELSE 0 END), 0)
        AS UnusedStraightTime,
```

**Check:** unused straight time falls from {{ g.capacity[0][2]|num }} to {{ g.capacity[-1][2]|num }} hours while surge overtime rises from {{ g.capacity[0][3]|num }} to {{ g.capacity[-1][3]|num }}; in the last year the unused hours are {{ (g.capacity[-1][2] / g.capacity[-1][3])|num(1) }} times the surge overtime, at {{ g.capacity[-1][1]|num(2) }} hours an ordinary employee-day. That is a total, not a schedule, so only a dated plan by work center and skill could show the work could move.

**Step 4. Cost the surge overtime two ways, with the employer's taxes and benefits.** The premium is half the base rate, if the hours were needed; the full cost is one and a half times, if they were not. The burden comes from the Manufacturing registers, by pay year.

```sql
    ROUND(s.StraightTimeCost * 0.5, 2) AS Premium,
    ROUND(s.StraightTimeCost * 0.5 * (1 + b.BurdenRate), 2)
        AS PremiumWithBurden,
    ROUND(s.StraightTimeCost * 1.5, 2) AS FullCost,
```

**Check:** premium {{ ys|map(attribute='surge_premium')|map('money')|join(', ') }} ({{ g.cost[-1][4]|money }} with the {{ burden|pct(2) }} burden in the last year); full cost {{ ys|map(attribute='surge_full')|map('money')|join(', ') }} ({{ g.cost[-1][6]|money }} with burden). **Watch for:** a burden from every cost center gives {{ g.all_centers[-1][4]|money }}, a little low.

### Part 3: The bridge

**Step 5. Save PlantLedger and bridge account 5080.** The view sums accounts 1090 and 5080 by fiscal year and source document type, closes excluded; WorkOrderClose supplies the material variance.

```sql
    WHERE a.AccountNumber IN (1090, 5080)
        AND gl.VoucherNumber NOT IN (
            SELECT EntryNumber
            FROM JournalEntry
            WHERE EntryType LIKE 'Year-End Close%')
    GROUP BY gl.FiscalYear
```

{{ figure('IF-C3-3-A') }}

**Check:** 5080 grew {{ g.bridge[0]|money }}: payroll charged to 1090 +{{ g.bridge[1]|money }}, journal entries -{{ (g.bridge[2]|abs)|money }}, standard cost released +{{ g.bridge[3]|money }}, change in 1090 -{{ (g.bridge[4]|abs)|money }}, material variance -{{ (g.bridge[5]|abs)|money }}, direct postings -{{ (g.bridge[6]|abs)|money }}. The direct postings are the first year's {{ pay_month }} payroll ({{ pay_amount|money }}) and {{ je }} ({{ je_amount|money }}). **Watch for:** with the closes left in, 5080 nets to zero in every year; and `AccountID IN (1090, 5080)` returns {{ g.by_id }} rows, since no AccountID is that large.

### Part 4: The payroll line

**Step 6. Explain the payroll line with three measures, and say why they overlap.** The calendar: the extra payrolls charged to 1090 at the first year's average, {{ added_dates }} an added pay date and the other the first year's payroll that posted to 5080. The hours beyond the work: the last year's hours less the first year's hours per standard hour times its output, priced at the last year's rate with burden. The growth of the surge premium, with burden.

```sql
        (lc.PayDates - lf.PayDates) * lf.Payroll / lf.PayDates
            AS Calendar,
        hc.ClockedHours
            - hf.ClockedHours / ofy.StandardHours * oc.StandardHours
            AS HoursBeyond,
```

**Check:** payroll line +{{ bridge.payroll|money }}; calendar {{ calendar|money }} ({{ extra }} more payrolls charged to 1090); hours beyond {{ hours_beyond|num }}, {{ beyond_cost|num }} at {{ rate|num(2) }} with burden; premium growth {{ premium_growth|num }}. Together {{ together|num }}, {{ excess|num }} above the line. The bridge's lines are ledger amounts and sum exactly. The measures are diagnostics, not a second bridge, because they overlap and use different calendars and populations (the note spells them out). **Watch for:** counting the last year's output to its year-end gives {{ g.m_cut[2]|num }} hours and an excess of only {{ g.m_cut[6]|num }}, which looks better and is worse; the calendar at the last year's average reads {{ g.m_cal[1]|money }}.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Hours per standard hour, by year | {% for y in ys %}{{ y.ratio|num(3) }}{{ ", " if not loop.last else "" }}{% endfor %} | 1 |
| Standard per clocked hour, surge weeks and other weeks | {{ surge.ratio|num(2) }}; {{ other.ratio|num(2) }} | 2 |
| Surge overtime cost, premium and full, with burden | {{ g.cost[-1][4]|money }}; {{ g.cost[-1][6]|money }} | 4 |
| Growth of 5080 | {{ g.bridge[0]|money }} | 5 |
| Three measures against the payroll line | {{ together|num }} against {{ bridge.payroll|num }} | 6 |

{{ expected() }}

## What a strong answer says

- **Output and hours.** Output flat, hours up, and a weekly comparison read as a suggestion, with its tail stated.
- **Capacity and cost.** Unused straight time above the surge overtime in total, to be confirmed by a dated check; two costs, not a sum.
- **The bridge and the measures.** Six ledger lines that sum to the change, and three overlapping diagnostics of the payroll line on stated calendars.

## Common mistakes and how to respond

- **Output to the year-end.** *Symptom:* {{ g.no_cut[3]|num(3) }} for the last year. *Response:* ask which day the time records end.
- **A frame that averages the past or the week itself.** *Symptom:* follow-on averages that look alike, or mix the week's output. *Response:* ask which weeks the frame includes.
- **Closes left in, or AccountID read as the number.** *Symptom:* 5080 at zero, or an empty view. *Response:* ask what a close does and which column holds the number.
- **The measures called a bridge.** *Symptom:* a forced fit to the payroll line. *Response:* ask which ones are ledger lines.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Output against hours | 15 | By year, cut off at the last time record, matches the view | No cut-off |
| Weekly comparison and limits | 20 | View, frame, groups, limits stated | Frame wrong, or no limits |
| Capacity and cost | 25 | Unused straight time; two costs with the plant's burden | One cost, or burden from every center |
| Bridge | 25 | Closes excluded; lines sum to the change; direct postings named | Lines that do not sum |
| Three measures and explanation | 15 | Calendars stated; overlap explained | Measures without the reason |

## Extensions and discussion questions

- Test the frame at two and at eight weeks and say how sensitive the conclusion is.
- Discuss: if the overtime was needed, which of the two costs is the right one?
- Discuss: could any single calendar serve all three measures?
