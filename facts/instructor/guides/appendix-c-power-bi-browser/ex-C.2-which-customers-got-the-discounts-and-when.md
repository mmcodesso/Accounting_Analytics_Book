---
note: appendix_c.ex2
uses: [appC.g2]
title: Which Customers Got the Discounts, and When
kind: exercise
number: C.2
unit: appC
perspective: managerial
tool: powerbi
tool_label: The Power BI service in a browser (the report editor)
minutes: 45
solution: "No solution file, because the projects open only in Desktop. The model answer is Steps 1 to 6 of this guide, built from Guided Tutorial C.2 (the page, the slicer, the line chart and its sort), the Discounts measure of Exercise C.1, and the Checks tab of Chapter13-exercises-pbi.zip for the month and segment values"
figures:
  - id: IF-AC-2-A
    kind: pbi-mock
    purpose: The Ex C.2 page at its end state, where the Design Services row and the peaks can be read.
    shows: "The report editor of the Power BI service on the page Ex C.2: a tile slicer with the current year selected; a matrix of Discounts with five segment rows and the twelve months as columns, the Design Services row reading zero in every month and each other segment's largest month outlined; and a line chart of Discounts by month in month order with a legend of the five segments, the Design Services line flat along the axis. The Data pane, drawn as an inset because twelve months of amounts need the window's width, lists Key Measures first."
    data: Discounts by segment and month for the current year, as in the Expected results, read-only.
---
{% set g = appC_g2 %}
# Exercise C.2: Which Customers Got the Discounts, and When

{{ header() }}

## Purpose and learning outcomes

The sales manager works on a Mac and wants to see which segments received the promotions' discounts, and when, before the next calendar is planned. The exercise is the page-building practice of the appendix: a slicer as tiles, a matrix, and a line chart whose months must be in order. The reading is the lesson. A segment promotion reaches one segment, an item-group promotion reaches every segment that buys the group, and one segment never appears because of what it buys. The analytics type is descriptive.

Students can:

- build a page with a tile slicer, a matrix and a legend chart in the report editor (Requirements 2 and 3);
- keep a month axis in month order (Requirement 3);
- name each segment's peak month and the promotion behind it (Requirement 4);
- say why one segment has no discounts and what that implies for a calendar aimed at one segment (Requirement 5).

**Competencies practiced.** Appendix D maps this exercise to CPA Evolution Core S1 M8 T3 and T4 (data mining and analysis) and T5 and T6 (visualization and communication); to the IMA competencies for data analysis and data visualization; to IFAC IES 2 (b) on management accounting and (i); and to AACSB A5 part 5.1.

## Before you assign

- **Files and software.** A browser, and the student's model and report after Tutorial C.2, with the Discounts measure of Exercise C.1 (or the exercise's instruction to create it). There is no model file.
- **Data conditions.** Customer.CustomerSegment has {{ g.w_segs }} values. SalesInvoiceLine.PromotionID is empty on most lines. The {{ g.none }} segment buys only {{ g.services_only }} items, and no Services line carries a promotion.
- **Verify first.** The Sales and Discounts page's discounts card reads ${{ g.total|money }} for fiscal {{ g.y }}.
- **Not confirmed in the service.** The test did not build a matrix or a legend on a line chart. Build the page once before you assign it.

## How to run it

Pairs, about 45 minutes: 5 for (1), 15 for (2), 10 for (3), 10 for (4), 5 for (5). Hold back the promotion names until the peaks are read. Hint 1, after 10 minutes on (2): "Which table holds CustomerSegment, and which holds Month?" Hint 2, for (5): "Which items does this segment buy?" Collect the page and the written answers to (4) and (5).

## Step-by-step solution

### Requirement (1): The Discounts measure

**Step 1. Find or create the measure.** Open the model and look in **Key Measures**. If Discounts is missing, add it as Step 2 of Exercise C.1 does.

```dax jinja
{{ g.m_disc }}
```

**Check:** the measure sits in Key Measures. Dragging DiscountAmount into the matrix instead gives the same numbers under the name Sum of DiscountAmount.

### Requirement (2): The page, the slicer and the matrix

**Step 2. Add the page and the slicer.**

a. Open the **Charles River Reports** report, and choose **Edit** on the menu bar.
b. Click the plus sign beside the page tabs, double-click the new tab, and rename it `Ex C.2`.
c. Select **Slicer**, and select FiscalYear in the SalesInvoice table.
d. Under **Format visual > Visual > Slicer settings > Options**, set **Style** to **Tile**; under **Selection**, turn on **Single select** and click the current year.

**Step 3. Add the matrix.**

a. Select **Matrix**, and drag Discounts from Key Measures into **Values**.
b. Drag CustomerSegment from the Customer table into **Rows**, and Month from SalesInvoice into **Columns**.

**Check:** {{ g.w_segs }} segment rows and twelve month columns. The {{ g.none }} row reads zero in every month, not blank, because it has invoice lines every month and each has a discount of zero. **Watch for:** the slicer left unselected, which gives {{ g.n_months }} month columns, or left as **Between**, a range with two handles. The matrix computes each total from the unrounded amounts, so Wholesale's displayed months add to ${{ g.ws_cells|money }} against its row total of ${{ g.ws_total|money }}, and the displayed monthly totals add to ${{ g.months_cells|money }} against ${{ g.total|money }}. Those are display rounding, not errors.

{{ figure('IF-AC-2-A') }}

### Requirement (3): The line chart

**Step 4. Chart the months in order.**

a. Select **Line chart**. Drag Month into **X-axis**, Discounts into **Y-axis** and CustomerSegment into **Legend**.
b. Read the labels under the axis. If they are not in month order, open **More options** (**…**) and choose **Sort by > Month**, then **Sort by > Sort ascending**.

**Check:** the labels run from the first month to the last, and the {{ g.none }} line lies along the axis. **Watch for:** a chart sorted by its values. For the whole company it starts {{ g.ranked[:4]|join(", ") }} and ends {{ g.last_month }}, so the line falls and reads as a decline. The test saw this on a chart with no legend; check the axis of the one with a legend.

### Requirement (4): The peaks and their promotions

**Step 5. Read each segment's largest month.**

**Check:** {{ g.trade }}, a segment promotion, gives most of {{ trade_month }} for the segment it names (${{ trade_own|money }}), and the {{ autumn }}'s lines invoiced that month give the rest (${{ trade_rest|money }}). The other peaks fall in the months of {{ autumn }}, which ran in {{ autumn_months }}: the other segments peak in {{ others|map("last")|unique|join(" or ") }}. One cell is worth matching.

```dax jinja
EVALUATE
ROW ( "Design Trade, {{ trade_month }}", {{ g.dax_trade }} )
```

**Watch for:** attributing every peak to the segment promotion. Only {{ g.w_trade_segs }} segment received it, while the item-group promotion discounted {{ g.w_autumn_segs }}.

### Requirement (5): The segment with no discounts

**Step 6. Say which segment and why.** The {{ g.none }} segment received none: it buys only {{ g.services_only }}, and no promotion covers Services.

**Check:** two sentences. The first names the segment and the reason. The second says that an item-group promotion discounts every segment that buys the group, so Wholesale, the largest, holds {{ g.ws_share|pct(1) }} of the year's discounts, while a segment promotion reaches only its segment. A strong second sentence also says that the page shows the discounts by invoice month, not what the promotions did to sales, so a calendar aimed at one segment needs that segment's orders and margins as well.

## Expected results

| Quantity | Value | Step |
|---|---|---|
{% for s, month, peak, total in peaks %}
| {{ s }}: largest month; its discounts; the year's | {{ month }}; ${{ peak|money }}; ${{ total|money }} | 5 |
{% endfor %}
| {{ g.none }}: every month | zero | 3 |
| Months on the matrix with no year selected | {{ g.n_months }} | 3 |

{{ expected() }}

## What a strong answer says

- **(2), (3)** A page with the slicer on the current year, the matrix with five rows, and the line chart in month order, with a title.
- **(4)** {{ trade }} for most of Design Trade's {{ trade_month }}, with part of the autumn promotion's billing; for the others, the autumn promotion, with the remark that its orders of {{ autumn_months }} are invoiced into the next months.
- **(5)** The segment, the reason (it buys only Services), and the distinction between a segment and an item-group promotion.

## Common mistakes and how to respond

- **No year selected.** *Symptom:* {{ g.n_months }} columns, and Wholesale's largest month reads {{ g.all_ws }} (${{ g.all_ws_value|money }}), from a segment promotion of the prior year, instead of {{ g.ws_peak_month }} (${{ g.ws_peak_value|money }}). *Response:* ask which year the page is about.
- **A sorted line.** *Symptom:* a line that falls from the left. *Response:* ask them to read the axis labels aloud.
- **The zero row called missing.** *Symptom:* "no data for {{ g.none }}". *Response:* ask what a zero in every month says that a blank would not.
- **Revenue for discounts.** *Symptom:* the peaks fall in {{ g.rev_months }}, not in the autumn. *Response:* ask which measure is in **Values**.
- **One promotion for every peak.** *Symptom:* "the Design Trade promotion explains it all". *Response:* ask who else received it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 10 | The measure used, in Key Measures | Implicit sum |
| Requirement 2 | 25 | Tile slicer on one year, matrix with both wells | Matrix with the year unselected |
| Requirement 3 | 20 | Legend, months in order, a title | Months sorted by value |
| Requirement 4 | 25 | Every peak with its promotion | Peaks without promotions |
| Requirement 5 | 20 | Segment, reason, calendar implication | Segment only |

## Extensions and discussion questions

- Put CustomerSegment in **Small multiples** instead of **Legend**, and compare the two readings.
- Add a dropdown slicer for CustomerSegment, as Tutorial C.2 Step 7 does, and use it to isolate one segment.
- Discuss: the Part II case decides a promotion calendar. What does this page say about a segment promotion for Strategic?
- Discuss: should a segment that buys only Services be offered a promotion, and of what kind?
