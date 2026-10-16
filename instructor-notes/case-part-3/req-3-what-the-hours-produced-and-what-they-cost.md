# Requirement 3: What the hours produced and what they cost (Chapters 10 and 11; managerial accounting)

| | |
|---|---|
| Unit | Case Part 3: Planning the Plant's Hours for 2027 |
| Item | Requirement 3 |
| Perspective | Managerial accounting |
| Tools | SQL (DB Browser for SQLite) |
| Time | About 150 minutes |
| Solution file | PartIII-case-sql.zip: Case.sql, the queries labeled Requirement 3 (the hours against output, the view PlantWeeks, the capacity and cost queries, the view PlantLedger, the bridge and the three measures), and the Requirement 3 model answer in its closing comments |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This requirement asks what the surge hours bought and what they cost, on three calendars that must not be mixed. It also teaches the difference between a bridge, which sums to the ledger, and measures, which explain a line and may overlap. The analytics type is diagnostic.

Students can:

- compare hours with output by year and week, with a window frame, and state the limits (Steps 1 and 2);
- measure capacity used and cost the overtime two ways (Steps 3 and 4);
- bridge a ledger account into lines that sum to the change (Step 5);
- explain a line with measures on stated calendars, and say why they overlap (Step 6).

**Competencies practiced.** CPA Evolution BAR M5 (cost accounting and variance analysis); IMA Reporting and Control (cost accounting) and Business Acumen and Operations (operational knowledge); IFAC IES 2 (b), management accounting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Case.sql with SurgeDays and PlantEntries (Requirement 1). It builds on Chapter 10's measure of the plant (Tutorial 10.3), Chapter 11's frames and Tutorial 12.3's test H5. Tutorial 11.3's view MonthlyLaborEfficiency, from the chapter or from Setup_Part3_Views.sql with **Write Changes**; without it the December query fails with "no such table: MonthlyLaborEfficiency".
- **Data conditions.** Time records end on 2026-12-11; completions run to the year-end; the first fiscal year charged 24 payrolls to 1090 and the last 26. GLEntry.AccountID is not the account number.
- **Verify first.** The bridge returns 1 row, and the unexplained column of the ledger query is zero in every year.

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

**Check:** 2024, 83,628 hours against 70,871 standard, 1.180; 2025, 93,391 hours against 66,109 standard, 1.413; 2026, 101,237 hours against 66,998 standard, 1.511. Surge overtime rises from 3,456 to 14,112 hours: output flat, surge overtime quadrupled. The December values of the view agree to two decimals, but the view is no coverage test. Its indirect time ends on 2026-12-04, so its last row is provisional, and counted to that day on both sides the last year's direct ratio is somewhat lower and the indirect a little higher (Chapter 10). **Watch for:** without the cut-off the last year reads 68,913 standard hours and 1.469.

**Step 2. Build the weekly view, group the weeks by surge days, and state the limits.** PlantWeeks holds each Monday week's clocked hours, surge days and standard hours completed up to 2026-12-11, with the average output of up to six following weeks in a window frame and the number of weeks the frame holds.

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

**Check:** in the last year 37 weeks without surge days average 1,555 hours and 1,087 standard hours (0.70); the 12 weeks with surge days 3,622 and 1,984 (0.55). The following weeks average 1,138 standard hours after a surge week, against 1,385. The last 6 frames of the year hold fewer than six weeks and the last week stops on the cut-off, and over six complete following weeks the figures are 1,126 after 10 surge weeks against 1,372 after 32. That is consistent with output timing, including work brought forward, but cannot show which hours produced the output: work orders closed in the last year took about 40 days from release to completion, and 1,674 of 5,314 completions fall on weekends. **Watch for:** three wrong versions.

- Without the cut-off in the view's Output CTE the last week takes in 249.2 standard hours completed after 2026-12-11, and surge weeks read 2,005.

- `ROWS UNBOUNDED PRECEDING` averages the earlier weeks, and every group reads about the same (1,332 to 1,342).
- `CURRENT ROW AND 5 FOLLOWING` mixes the week's own output into its follow-on (1,330, 1,267, 1,197, 1,561 against 1,385, 1,128, 1,154, 1,112).

### Part 2: Capacity and cost

**Step 3. Measure the capacity the ordinary days used.** Sum each employee's entries by work date first, because a few employee-days carry two entries, then average the ordinary employee-days and total the straight-time hours left unused on days under eight regular hours.

```sql
    ROUND(SUM(CASE WHEN DayType = 'Ordinary' AND RegularHours < 8
        THEN 8 - RegularHours ELSE 0 END), 0)
        AS UnusedStraightTime,
```

**Check:** unused straight time falls from 52,597 to 38,403 hours while surge overtime rises from 3,456 to 14,112; in the last year the unused hours are 2.7 times the surge overtime, at 5.26 hours an ordinary employee-day. That is a total, not a schedule, so only a dated plan by work center and skill could show the work could move.

**Step 4. Cost the surge overtime two ways, with the employer's taxes and benefits.** The premium is half the base rate, if the hours were needed; the full cost is one and a half times, if they were not. The burden comes from the Manufacturing registers, by pay year.

```sql
    ROUND(s.StraightTimeCost * 0.5, 2) AS Premium,
    ROUND(s.StraightTimeCost * 0.5 * (1 + b.BurdenRate), 2)
        AS PremiumWithBurden,
    ROUND(s.StraightTimeCost * 1.5, 2) AS FullCost,
```

**Check:** premium 46,055.52, 122,814.72, 188,060.04 (214,651.73 with the 14.14% burden in the last year); full cost 138,166.56, 368,444.16, 564,180.12 (643,955.19 with burden). **Watch for:** a burden from every cost center gives 214,087.55, a little low.

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

![The bridge of account 5080 from the first fiscal year to the last, the exhibit that carries the cost story into the memo.](../figures/case-part-3/IF-C3-3-A.pdf)

**Check:** 5080 grew 947,709.56: payroll charged to 1090 +966,846.03, journal entries -8,473.29, standard cost released +91,787.08, change in 1090 -72,196.35, material variance -9,378.15, direct postings -20,875.76. The direct postings are the first year's January payroll (11,520.94) and JE-2024-000005 (9,354.82). **Watch for:** with the closes left in, 5080 nets to zero in every year; and `AccountID IN (1090, 5080)` returns 0 rows, since no AccountID is that large.

### Part 4: The payroll line

**Step 6. Explain the payroll line with three measures, and say why they overlap.** The calendar: the extra payrolls charged to 1090 at the first year's average, one an added pay date and the other the first year's payroll that posted to 5080. The hours beyond the work: the last year's hours less the first year's hours per standard hour times its output, priced at the last year's rate with burden. The growth of the surge premium, with burden.

```sql
        (lc.PayDates - lf.PayDates) * lf.Payroll / lf.PayDates
            AS Calendar,
        hc.ClockedHours
            - hf.ClockedHours / ofy.StandardHours * oc.StandardHours
            AS HoursBeyond,
```

**Check:** payroll line +966,846.03; calendar 237,379.26 (two more payrolls charged to 1090); hours beyond 22,180, 673,995 at 26.62 with burden; premium growth 162,084. Together 1,073,459, 106,612 above the line. The bridge's lines are ledger amounts and sum exactly. The measures are diagnostics, not a second bridge, because they overlap and use different calendars and populations (the note spells them out). **Watch for:** counting the last year's output to its year-end gives 19,920 hours and an excess of only 37,948, which looks better and is worse; the calendar at the last year's average reads 293,492.09.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Hours per standard hour, by year | 1.180, 1.413, 1.511 | 1 |
| Standard per clocked hour, surge weeks and other weeks | 0.55; 0.70 | 2 |
| Surge overtime cost, premium and full, with burden | 214,651.73; 643,955.19 | 4 |
| Growth of 5080 | 947,709.56 | 5 |
| Three measures against the payroll line | 1,073,459 against 966,846 | 6 |

> **Instructor notes, Requirement 3:** by year (work dates, output to 2026-12-11): hours 83,628, 93,391, 101,237 against standard hours 70,871, 66,109, 66,998 (1.180, 1.413, 1.511 hours per standard hour); surge-day overtime 3,456, 9,216, 14,112 hours, other overtime 6,273, 6,426, 5,918. Output was flat while surge overtime quadrupled. Weekly (Monday weeks, date(WorkDate, '-6 days', 'weekday 1')), 2026: 37 weeks without surge days averaged 1,555 clocked hours and 1,087 standard hours completed (0.70), and the 12 weeks with surge days 3,622 and 1,984 (0.55), in detail 3 surge days 2 weeks (3,130 and 1,762), 4 surge days 7 weeks (3,601 and 1,447), 5 surge days 3 weeks (4,000 and 3,385); the following weeks (up to six) after a week with surge days averaged 1,138 standard hours, against 1,385 after other weeks, and counted only over six complete following weeks 1,126 after 10 surge weeks against 1,372 after 32 others. Output is counted to 2026-12-11, so the last week is partial and leaves out 249.2 standard hours completed after that day. June 2024 onward: 102 weeks without surge days, 1,500 and 1,108 (0.74). Surge weeks complete more but not in proportion to the hours, and the weeks after them complete less. That is consistent with output timing, including work brought forward, but completion dates cannot show which hours produced the output: work orders closed in 2026 took about 40 days from release to completion, and completions post on weekends. Capacity on ordinary days, by employee and work date (a few employee-days carry two clock entries): 4.93, 4.79, and 5.26 clocked hours per employee-day; unused straight-time hours (8 less regular hours, on employee-days with fewer than 8) 52,597, 51,942, and 38,403, against surge overtime of 3,456, 9,216, and 14,112, so in total the 2026 unused straight time was more than twice the surge overtime. Whether the work could have moved there needs a dated plan by work center and skill. Cost at base rates: premium 46,055.52, 122,814.72, 188,060.04 (214,651.73 with the 14.14% burden in 2026); full overtime 138,166.56, 368,444.16, 564,180.12 (643,955.19 with burden in 2026). Bridge (ledger, closes excluded): 5080 rose from 1,317,927.32 to 2,265,636.88, +947,709.56 = payroll to 1090 +966,846.03 (2,848,551.11 to 3,815,397.14) + journal entries -8,473.29 (1,621,008.98 to 1,612,535.69) + standard cost released +91,787.08 (3,358,209.62 to 3,266,422.54, released less) + change in 1090 -72,196.35 (the account fell by 69,824.09 in 2024 and rose by 2,372.26 in 2026) + material variance -9,378.15 (115,877.00 to 106,498.85) + direct postings -20,875.76 (2024's January payroll, 11,520.94, and JE-2024-000005, 9,354.82). The payroll line, with three diagnostics that are not a second bridge: two more payrolls charged to 1090 at 2024's average, 237,379.26, one of them a pay date the calendar added (Manufacturing had 25 pay dates in 2024 and 26 in 2026) and the other because 2024's first payroll posted to 5080 (a direct posting of the bridge); hours beyond 2024's 1.18 hours per standard hour, 22,180 hours at the 2026 straight-time rate of 26.62 with burden, 673,995; growth of the surge premium with burden, 162,084; together 1,073,459, which exceeds the payroll line by 106,612 because the measures overlap and use different calendars and populations: the hours follow work dates through December 11 and describe the hourly staff, the payroll follows pay dates and includes the salaried staff, and the calendar measure uses 2024's average payroll, which includes the start-up month. The six ledger lines are the exact bridge.

## What a strong answer says

- **Output and hours.** Output flat, hours up, and a weekly comparison read as a suggestion, with its tail stated.
- **Capacity and cost.** Unused straight time above the surge overtime in total, to be confirmed by a dated check; two costs, not a sum.
- **The bridge and the measures.** Six ledger lines that sum to the change, and three overlapping diagnostics of the payroll line on stated calendars.

## Common mistakes and how to respond

- **Output to the year-end.** *Symptom:* 1.469 for the last year. *Response:* ask which day the time records end.
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
