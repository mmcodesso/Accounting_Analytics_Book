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

Requirement 2 asked whether the surge hours were worked; this one asks what they bought and what they cost, on three calendars that must not be mixed: hours by work date, output by completion date, cost by pay date. It also teaches the difference between a bridge, which sums to the ledger, and measures, which explain a line and may overlap. The analytics type is diagnostic.

Students can:

- compare hours with output by year and week, with a window frame, and state the limits (Steps 1 and 2);
- measure capacity used and cost the overtime two ways (Steps 3 and 4);
- bridge a ledger account into lines that sum to the change (Step 5);
- explain a line with measures on stated calendars, and say why they overlap (Step 6).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Reporting and Control (cost accounting) and Business Acumen and Operations (operational knowledge); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql with SurgeDays and PlantEntries (Requirement 1). It builds on Chapter 10's measure of the plant (Tutorial 10.3), Chapter 11's frames and Tutorial 12.3's test H5. Tutorial 11.3's view MonthlyLaborEfficiency, from the chapter or from Setup_Part3_Views.sql with **Write Changes**; without it the December query fails with "{{ g.err }}".
- **Data conditions.** Time records end on {{ cutoff }}; completions run to the year-end and fall on weekends; payroll posts on pay dates, so the first fiscal year charged {{ lf.paydates }} payrolls to 1090 and the last {{ lc.paydates }}. Closes must be excluded, and GLEntry.AccountID is not the account number.
- **Verify first.** The bridge returns {{ g.n.bridge }} row, and the unexplained column of the ledger query is zero in every year.

## How to run it

Pairs, about 150 minutes: 30 for output against hours and the weekly view, 20 for capacity and cost, 40 for the ledger view and bridge, 35 for the three measures, 25 for the explanation. The routine: type the two comment lines and the query, select it, click **Execute all/selected SQL**, read the message pane. Hold back the frame until a pair has seen the weeks one at a time, and the measures until the bridge sums. **Collect** the script and the bridge.

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

**Check:**{% for y in ys %} {{ y.year }}, {{ y.hours|num }} hours against {{ y.std|num }} standard, {{ y.ratio|num(3) }}{{ ";" if not loop.last else "." }}{% endfor %} Surge overtime rises from {{ ys[0].surge.overtime|num }} to {{ ys[-1].surge.overtime|num }} hours: output flat, surge overtime {{ grew }}. The December values of the view agree to two decimals. **Watch for:** without the cut-off the last year reads {{ g.no_cut[2]|num }} standard hours and {{ g.no_cut[3]|num(3) }}.

**Step 2. Build the weekly view, group the weeks by surge days, and state the limits.** PlantWeeks holds each Monday week's clocked hours, surge days and standard hours, with the average output of the six weeks that follow in a window frame.

```sql
    AVG(COALESCE(o.StandardHours, 0)) OVER (
        ORDER BY h.WeekStart
        ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING
    ) AS NextSixWeeks
```

**Check:** in the last year {{ other.n }} weeks without surge days average {{ other.hours|num }} hours and {{ other.std|num }} standard hours ({{ other.ratio|num(2) }}); the {{ surge.n }} weeks with surge days {{ surge.hours|num }} and {{ surge.std|num }} ({{ surge.ratio|num(2) }}). The six weeks after a surge week average {{ surge.next|num }} standard hours, against {{ other.next|num }}, which looks like work pulled forward rather than more work. The limits: completions lag the work (about {{ lead|num }} days from release to completion) and {{ g.limits[1]|count }} of {{ g.limits[2]|count }} completions fall on weekends, so a week's hours and completions are not the same work. **Watch for:** two wrong frames.

- `ROWS UNBOUNDED PRECEDING` averages the earlier weeks, and every group reads about the same ({{ g.cum_next|min|num }} to {{ g.cum_next|max|num }}).
- `CURRENT ROW AND 5 FOLLOWING` mixes the week's own output into its follow-on ({{ g.own_next|map('num')|join(', ') }} against {{ g.groups|map(attribute=5)|map('num')|join(', ') }}).

### Part 2: Capacity and cost

**Step 3. Measure the capacity the ordinary days used.** Average the hours clocked on ordinary entries, and total the straight-time hours left unused on entries under eight regular hours.

```sql
    ROUND(SUM(CASE WHEN DayType = 'Ordinary' AND RegularHours < 8
        THEN 8 - RegularHours ELSE 0 END), 0)
        AS UnusedStraightTime,
```

**Check:** unused straight time falls from {{ g.capacity[0][2]|num }} to {{ g.capacity[-1][2]|num }} hours while surge overtime rises from {{ g.capacity[0][3]|num }} to {{ g.capacity[-1][3]|num }}; in the last year the unused hours are {{ (g.capacity[-1][2] / g.capacity[-1][3])|num(1) }} times the surge overtime, at {{ g.capacity[-1][1]|num(2) }} hours an ordinary entry.

**Step 4. Cost the surge overtime two ways, with the employer's taxes and benefits.** The premium is half the base rate, if the hours were needed and could have been worked at straight time; the full cost is one and a half times, if they were not needed. The burden is the Manufacturing registers' taxes and benefits over gross pay, by pay year.

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

**Check:** 5080 grew {{ g.bridge[0]|money }}: payroll charged to 1090 +{{ g.bridge[1]|money }}, journal entries -{{ (g.bridge[2]|abs)|money }}, standard cost released +{{ g.bridge[3]|money }}, change in 1090 -{{ (g.bridge[4]|abs)|money }}, material variance -{{ (g.bridge[5]|abs)|money }}, direct postings -{{ (g.bridge[6]|abs)|money }}. The direct postings are the first year's {{ pay_month }} payroll ({{ pay_amount|money }}) and {{ je }} ({{ je_amount|money }}). **Watch for:** with the closes left in, 5080 nets to zero in every year, because each close credits it with the year's total; and `AccountID IN (1090, 5080)` returns {{ g.by_id }} rows, since no AccountID is that large.

### Part 4: The payroll line

**Step 6. Explain the payroll line with three measures, and say why they overlap.** The calendar: the extra pay dates at the first year's average payroll. The hours beyond the work: the last year's hours less the first year's hours per standard hour times its output, priced at the last year's rate with burden. The growth of the surge premium, with burden.

```sql
        (lc.PayDates - lf.PayDates) * lf.Payroll / lf.PayDates
            AS Calendar,
        hc.ClockedHours
            - hf.ClockedHours / ofy.StandardHours * oc.StandardHours
            AS HoursBeyond,
```

**Check:** payroll line +{{ bridge.payroll|money }}; calendar {{ calendar|money }} ({{ extra }} more pay dates); hours beyond {{ hours_beyond|num }}, {{ beyond_cost|num }} at {{ rate|num(2) }} with burden; premium growth {{ premium_growth|num }}. Together {{ together|num }}, {{ excess|num }} above the line. The bridge's lines are ledger amounts and sum exactly; the measures overlap and use different calendars: hours by work date to {{ last_day }}, payroll by pay date, and a calendar measure at the first year's average payroll, which includes its start-up month. **Watch for:** counting the last year's output to its year-end gives {{ g.m_cut[2]|num }} hours and an excess of only {{ g.m_cut[6]|num }}, which looks better and is worse; the calendar at the last year's average reads {{ g.m_cal[1]|money }}.

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

- **Output and hours.** Output flat, hours up; surge weeks complete more but not in proportion, and the weeks after complete less. The weekly comparison only suggests, and the answer says so.
- **Capacity and cost.** The ordinary days left more straight time unused than the surge overtime used, so the overtime was not needed for capacity; its cost is the premium if the work was needed and the full amount if it was not.
- **The bridge.** Six ledger lines sum to the change; almost all of it is payroll charged to 1090.
- **The measures.** Three explanations of the payroll line, on stated calendars, with the reason they overlap.

## Common mistakes and how to respond

- **Output to the year-end.** *Symptom:* {{ g.no_cut[3]|num(3) }} for the last year. *Response:* ask which day the time records end.
- **A frame that averages the past or the week itself.** *Symptom:* follow-on averages that look alike, or mix the week's output. *Response:* ask which weeks the frame includes.
- **Closes left in, or AccountID read as the number.** *Symptom:* 5080 at zero, or an empty view. *Response:* ask what a close does and which column holds the number.
- **The measures called a bridge.** *Symptom:* a forced fit to the payroll line. *Response:* ask which ones are ledger lines.
- **A confident week-by-week conclusion.** *Symptom:* "surge weeks produce more". *Response:* ask what a completion date measures.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Output against hours | 15 | By year, cut off at the last time record, matches the view | No cut-off |
| Weekly comparison and limits | 20 | View, frame, groups, limits stated | Frame wrong, or no limits |
| Capacity and cost | 25 | Unused straight time; two costs with the plant's burden | One cost, or burden from every center |
| Bridge | 25 | Closes excluded; lines sum to the change; direct postings named | Lines that do not sum |
| Three measures and explanation | 15 | Calendars stated; overlap explained | Measures without the reason |

## Extensions and discussion questions

- Rerun Step 5 for the middle year and say whether the bridge pattern holds.
- Test the frame at two and at eight weeks and say how sensitive the conclusion is.
- Discuss: if the overtime was needed, which of the two costs is the right one, and why does the capacity test say otherwise?
- Discuss: could any single calendar serve all three measures?
