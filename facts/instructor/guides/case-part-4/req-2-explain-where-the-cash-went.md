---
note: case4.r2
uses: [case4.g2]
title: Explain where the cash went (Chapters 14 and 15; financial reporting)
kind: requirement
number: '2'
unit: case4
perspective: financial
tool: powerbi
minutes: 180
solution: "PartIV-case.zip: Charles River Cash Case.pbip, pages Balance Sheet, Cash Bridge and Bridge Detail (the hidden drill-through page), Test 3 of the Tests tab and the Requirement 2 rows of the Checks tab"
figures:
  - id: IF-C4-2-A
    kind: pbi-mock
    purpose: The Cash Bridge page of the model answer, the exhibit that answers the committee's first question.
    shows: "Report view, page Cash Bridge. A tile slicer of the fiscal years; a waterfall of ten steps from Net income to Debt and equity, the Inventories step far below the others; a matrix of the bridge by year; and a matrix of the sections by activity with As recorded and Restated Cash Flow."
    data: The Expected results quantities (the bridge steps by year and the sections as recorded and restated), read-only.
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = case4_g2 %}
# Requirement 2: Explain where the cash went (Chapters 14 and 15; financial reporting)

{{ header() }}

## Purpose and learning outcomes

The income statement cannot say where the cash went, so the requirement bridges net income to the change in cash, finds the entries that moved no cash and restates the sections as the indirect method requires (ASC Topic 230 leaves investing and financing activities that move no cash out of the statement's amounts and discloses them apart, while the indirect method adjusts net income for noncash items such as depreciation and losses; paragraphs 230-10-45-28 and 230-10-50-3 to 50-6, to read before quoting). Its technical lessons are KEEPFILTERS and the difference between a flow and a difference of balances. The analytics type is descriptive, with diagnostic work in the drill-through.

Students can:

- show balance sheets and ratios and say what each hides (Step 1);
- assign accounts to bridge steps and measure each step from the year's postings (Steps 2 and 3);
- chart the year as a waterfall and explain why the first year reads differently (Step 4);
- drill through to the entries that moved no cash and restate the sections (Steps 5 and 6);
- measure cash net of the recorded sales tax payable and the notes due within a year (Step 7).

**Competencies practiced.** CPA Evolution BAR M9 (financial statement analysis and working capital) and Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Reporting and Control (financial statement analysis); IFAC IES 2 (a), financial accounting and reporting; AACSB A5 part 5.1.

## Before you assign

- **Files.** Requirement 1's file. The model answer is in PartIV-case.zip: the pages above and Test 3.
- **Data conditions.** The opening entry {{ entry }} is a {{ d.F }} posting; one equipment invoice moved to notes payable in {{ d.C }}; {{ d.P }} and {{ d.C }} each have one asset disposal; the notes sit in account `2110`; the debt schedule runs past the Date table.
- **Verify first.** Test 3 agrees for {{ d.P }} and {{ d.C }}, and so do the {{ g.n_checks }} Requirement 2 rows of the Checks tab.

## How to run it

Pairs, about 180 minutes: 25 for the balance sheet, 45 for the columns and measure, 30 for the waterfall, 50 for the drill-through and restatement, 30 for tax and notes. **Collect** the .pbix.

## Step-by-step solution

The Checks tab proves every value; colors, order and the drill-through button are visible only in Desktop.

### Part 1: The balance sheet and the ratios

**Step 1. Show the year-ends.** Add a **Matrix** with AccountType and AccountSubType on **Rows**, Year on **Columns** and `Statement Balance` in **Values**, titled "{{ g.t_matrix }}", and a **Table** titled "{{ g.t_ratios }}" with the working capital, current ratio and quick ratio.

**Check:** `Statement Balance` reverses the sign of liabilities and equity. Working capital {% for v in ye %}${{ v.wc|money }}{{ ", " if not loop.last else "" }}{% endfor %}; current ratio {% for v in ye %}{{ v.current|num(2) }}{{ ", " if not loop.last else "" }}{% endfor %}; quick ratio {% for v in ye %}{{ v.quick|num(2) }}{{ ", " if not loop.last else "" }}{% endfor %}. The current ratio hides the change, and the quick ratio, cash and receivables over current liabilities, falls. Inventories are {{ inv_share|pct(0) }} of {{ d.C }} current assets.

### Part 2: The bridge columns and the measure

**Step 2. Add Step and Activity to Account.** In Power Query, choose **Add Column > Custom Column**. Name the column `Step`, enter only the first expression below, an if-then-else chain on account numbers first and subtypes after, and set the type to Text. Add `Activity` from the second, and a whole-number `StepOrder` that numbers the steps from Net income to Debt and equity. After **Close & Apply**, select Account[Step] and choose **Column tools > Sort by column > StepOrder**, as Tutorial 15.1 sorted its Steps table.

```m jinja
{{ g.e_step }}
```

```m jinja
{{ g.e_activity }}
```

**Check:** `1030` falls in Receivables, `1090` and `8020` in Other current assets, `2110` in Debt and equity by default. **Watch for:** cash among the steps. They then sum to zero, because every entry balances: the other accounts' effects add up to the change in cash, and the cash step is its opposite.

**Step 3. Write the measures.** Choose **Modeling > New measure** for each.

```dax jinja
{{ g.d_cash }}
```

**Check:** Test 3 shows the steps ending at the change in cash for {{ d.P }} and {{ d.C }}. **Watch for:** two wrong versions. Without KEEPFILTERS every step reads {{ sm(g.kf_value) }}, the change in cash. A bridge from differences of Balance gives a net income step of {{ sm(g.diff_ni) }}, {{ d.C }}'s less {{ d.P }}'s, and a debt and equity step of {{ sm(g.diff_fin) }}, because the {{ d.P }} close sits in retained earnings.

### Part 3: The waterfall and the first year

**Step 4. Chart the year.** Add a **Waterfall chart** with Step on **Category** and Cash Effect on **Y-axis**, titled "{{ g.t_waterfall }}", and a **Slicer** (**Tile**, **Single select**) on Year. Filter out the Cash step in **Filters on this visual**, sort the steps in their order, and add a **Matrix** of the bridge by year titled "{{ g.t_bridge }}". Limit Year on both the slicer and the waterfall to the complete years of the window, save the latest as the selection, and keep the note on {{ d.F }} beside the chart. {{ d.N }} stays out, because its postings are a few supplier payments and not a year.

**Check:** {{ d.C }}: net income {{ sm(cur.net_income) }}, inventories {{ sm(cur.inventories) }}, change in cash {{ sm(cur.cash) }}, from ${{ cash_from|money }} to ${{ cash_to|money }}. {{ d.P }}: inventories {{ sm(pri.inventories) }} and cash up {{ sm(pri.cash) }}. **Watch for:** reading {{ d.F }} like {{ d.P }}. The opening entry is a {{ d.F }} posting, so the bridge starts from zero cash, shows {{ sm(first.cash) }} and puts {{ sm(first.financing) }} in financing; without it the change is {{ sm(first_x.cash) }} from an opening cash line of ${{ open_cash|money }}.

{{ figure('IF-C4-2-A') }}

### Part 4: The entries that moved no cash

**Step 5. Drill through.** Add a hidden **Bridge Detail** page with Step in the **Drillthrough** well and a **Table** of postings titled "{{ g.t_postings }}". Right-click Fixed assets and Debt and equity in the matrix and choose **Drillthrough > Bridge Detail**.

**Check:** the postings hold {{ gr }} (${{ financed|money }} of equipment debited to `{{ gr_account }}`), {{ reclass }} (invoice {{ reclass_invoice }} moved to notes) and the disposal {{ disp.entry }} (loss ${{ disp.loss|money }}, no proceeds).

**Step 6. Restate the sections.** Add measures for the disposal and the financed equipment, the restated measure below, and a **Matrix** titled "{{ g.t_restated }}".

```dax jinja
{{ g.d_restated }}
```

**Check:** {{ d.C }} restated: operating {{ sm(rc.operating) }}, investing {{ sm(rc.investing) }}, financing {{ sm(rc.financing) }}, with ${{ rc.notes_financed|money }} of equipment acquired by a note disclosed. **Watch for:** sections left as recorded. Financing reads {{ sm(g.fin_rec) }} where the restated one is {{ sm(g.fin_res) }}, and investing {{ sm(g.inv_rec) }} where it is zero. The depreciation step ({{ sm(g.dep_step) }}) is net of the write-off; the entries were ${{ g.dep_entries|money }}.

### Part 5: Cash net of tax and the notes

**Step 7. Measure what the cash is worth.** Add `Cash Net of Sales Tax`, `Sales Tax Payable` and `Principal Due within a Year` as cards titled "{{ g.t_cards }}".

**Check:** cash net of the recorded tax payable (${{ tax_c|money }}) is ${{ net[-1]|money }}, a liquidity sensitivity (tax billed, not all collected). The notes are ${{ outstanding|money }}, and ${{ due_next|money }} falls due in {{ d.N }} yet sits in `2110`. The principal measures clear the filter on Date and count payments after the as-of date on the notes originated by it (the origination date comes from the debt agreements). **Watch for:** the schedule filtered through Date, which drops {{ g.beyond_lines }} payments past the table's end and reads ${{ g.inside|money }}, or on PaymentDate alone, which at an earlier year-end counts a note not yet originated.

**Instructor check.** In **DAX query view**, compare this with the Expected results.

```dax jinja
{{ g.dax_check }}
```

## Expected results

| Quantity ({{ d.C }}) | Value | Step |
|---|---|---|
| Net income; inventories; change in cash | {{ sm(cur.net_income) }}; {{ sm(cur.inventories) }}; {{ sm(cur.cash) }} | 4 |
| Restated operating; investing; financing | {{ sm(rc.operating) }}; {{ sm(rc.investing) }}; {{ sm(rc.financing) }} | 6 |
| Operating, tax increase paid (a sensitivity) | {{ sm(without_tax) }} | 6 |
| Cash net of tax; principal due next year | ${{ net[-1]|money }}; ${{ due_next|money }} | 7 |

{{ expected() }}

## What a strong answer says

- **Balance sheet.** The current ratio barely moves; the quick ratio falls below one, because inventories are most of current assets.
- **Bridge.** The recorded profit went into inventories, the growth of the recorded tax payable and of payables held cash up, and the steps end at the change in cash. The opening entry makes {{ d.F }} start from zero cash.
- **Sections.** The entries that moved no cash named, the sections restated, the note disclosed.
- **Cash and notes.** Net of the recorded tax payable, cash is far smaller, a sensitivity. The notes' current portion belongs in current liabilities.

## Common mistakes and how to respond

- **Cash among the steps.** *Symptom:* steps sum to zero. *Response:* ask what a balanced entry guarantees about the sum of every account.
- **Bridge from balances.** *Symptom:* net income of {{ sm(g.diff_ni) }}. *Response:* ask where the {{ d.P }} close went.
- **Sections as recorded.** *Symptom:* financing of {{ sm(g.fin_rec) }}. *Response:* ask which entries moved no cash.
- **Schedule through Date, or without origination.** *Symptom:* notes of ${{ g.inside|money }}, or ${{ debt_hist[1].all|money }} at the end of {{ d.P }}. *Response:* ask which dates the table covers and when each note began.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Balance sheet and ratios | 15 | Signed by type; both ratios; what each hides | Ratios without the reading |
| Bridge columns and measures | 25 | Step and Activity; KEEPFILTERS; steps end at the change in cash | Right values, no KEEPFILTERS |
| Waterfall and years | 15 | Sorted; {{ d.P }} compared; first year explained | No reason for the first year |
| Drill-through and restatement | 30 | Entries found; sections restated; note disclosed | Entries found, not restated |
| Cash net of tax and notes | 15 | Both measured; balance sheet effects stated | One measured |

## Extensions and discussion questions

- Rebuild {{ d.F }} with `Cash Effect without Opening` and say what it can show.
- Discuss: no remittance of the sales tax is recorded. What would the committee need before it counts that cash as its own?
