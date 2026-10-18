# Exercise C.2: Which Customers Got the Discounts, and When

| | |
|---|---|
| Unit | Appendix C: Power BI in the Browser |
| Item | Exercise C.2 |
| Perspective | Managerial accounting |
| Tools | The Power BI service in a browser (the report editor) |
| Time | About 45 minutes |
| Solution file | No solution file, because the projects open only in Desktop. The model answer is Steps 1 to 6 of this guide, built from Guided Tutorial C.2 (the page, the slicer, the line chart and its sort), the Discounts measure of Exercise C.1, and the Checks tab of Chapter13-exercises-pbi.zip for the month and segment values |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

The sales manager works on a Mac and wants to see which segments received the promotions' discounts, and when, before the next calendar is planned. The exercise is the page-building practice of the appendix: a slicer as tiles, a matrix, and a line chart whose months must be in order. The reading is the lesson. A segment promotion reaches one segment, an item-group promotion reaches every segment that buys the group, and one segment never appears because of what it buys. The analytics type is descriptive.

Students can:

- build a page with a tile slicer, a matrix and a legend chart in the report editor (Requirements 2 and 3);
- keep a month axis in month order (Requirement 3);
- name each segment's peak month and the promotion behind it (Requirement 4);
- say why one segment has no discounts and what that implies for a calendar aimed at one segment (Requirement 5);
- title and describe the chart, save the page, and confirm it after reopening (Requirement 6).

**Competencies practiced.** Appendix D maps this exercise to CPA Evolution Core S1 M8 T3 and T4 (data mining and analysis) and T5 and T6 (visualization and communication); to the IMA competencies for data analysis and data visualization; to IFAC IES 2 (b) on management accounting and (i); and to AACSB A5 part 5.1.

## Before you assign

- **Files and software.** A browser, and the student's model and report after Tutorial C.3, including Key Measures, with the Discounts measure of Exercise C.1 used or created as Requirement 1 says. There is no model file.
- **Data conditions.** Customer.CustomerSegment has five values. SalesInvoiceLine.PromotionID is empty on most lines. The Design Services segment buys only Services items, and no Services line carries a promotion.
- **Verify first.** The Sales and Discounts page's discounts card reads $362,110.75 for fiscal 2026.
- **Not confirmed in the service.** The test did not build a matrix or a legend on a line chart. Build the page once before you assign it.

## How to run it

Pairs, about 45 minutes: 5 for (1), 10 for (2), 10 for (3), 10 for (4), 5 for (5), 5 for (6). Hold back the promotion names until the peaks are read. Hint 1, after 10 minutes on (2): "Which table holds CustomerSegment, and which holds Month?" Hint 2, for (5): "Which items does this segment buy?" Collect the saved page with its screenshot or table, and the written answers to (4) and (5).

## Step-by-step solution

### Requirement (1): The Discounts measure

**Step 1. Find or create the measure.** Open the model and look in **Key Measures**. If Discounts is missing, add it as Step 2 of Exercise C.1 does.

```dax
Discounts = SUM ( SalesInvoiceLine[DiscountAmount] )
```

**Check:** the measure sits in Key Measures, with a thousands separator and two decimal places, so the matrix shows amounts to the cent. Dragging DiscountAmount into the matrix instead gives the same numbers under the name Sum of DiscountAmount.

### Requirement (2): The page, the slicer and the matrix

**Step 2. Add the page and the slicer.**

a. Open the **Charles River Reports** report, and choose **Edit** on the menu bar.
b. Click the plus sign beside the page tabs, double-click the new tab, and rename it `Ex C.2`.
c. Select **Slicer**, and select FiscalYear in the SalesInvoice table.
d. Under **Format visual > Visual > Slicer settings > Options**, set **Style** to **Tile**; under **Selection**, turn on **Single select** and click 2026.

**Step 3. Add the matrix.**

a. Select **Matrix**, and drag Discounts from Key Measures into **Values**.
b. Drag CustomerSegment from the Customer table into **Rows**, and Month from SalesInvoice into **Columns**.

**Check:** five segment rows and twelve month columns. The Design Services row reads zero in every month, not blank, because it has invoice lines every month and each has a discount of zero. **Watch for:** the slicer left unselected, which gives 36 month columns, or left as **Between**, a range with two handles. The matrix computes each total from the unrounded amounts, so Wholesale's displayed months add to $184,926.13 against its row total of $184,926.14, and the displayed monthly totals add to $362,110.73 against $362,110.75. Those are display rounding, not errors.

![A mock of the Ex C.2 page at its end state, where the Design Services row and the peaks can be read.](../figures/appendix-c-power-bi-browser/IF-AC-2-A.pdf)

### Requirement (3): The line chart

**Step 4. Chart the months in order.**

a. Select **Line chart**. Drag Month into **X-axis**, Discounts into **Y-axis** and CustomerSegment into **Legend**.
b. Read the labels under the axis. If they are not in month order, open **More options** (**…**) and choose **Sort by > Month**, then **Sort by > Sort ascending**.

**Check:** the labels run from the first month to the last, and the Design Services line lies along the axis. **Watch for:** a chart sorted by its values. For the whole company it starts Oct, Sep, Nov, Dec and ends July, so the line falls and reads as a decline. The test saw this on a chart with no legend; check the axis of the one with a legend.

### Requirement (4): The peaks and their promotions

**Step 5. Read each segment's largest month.**

**Check:** accept the promotion names from Chapter 6 and Exercise 13.3, or from the instructor's lookup of PromotionID and PromotionName, which the student task allows, and no other table is needed (T7_PromotionProgram is an optional extension). Design Trade Customer Promotion, a segment promotion, gives most of November for the segment it names ($21,482.20), and the Furniture Seasonal Promotion's lines invoiced that month give the rest ($6,113.67). The other peaks fall in the months of Furniture Seasonal Promotion, which ran in September and October: the other segments peak in September or October. One cell is worth matching.

```dax
EVALUATE
ROW ( "Design Trade, November", CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SalesInvoice[Month] = "2026-11", Customer[CustomerSegment] = "Design Trade" ) )
```

**Watch for:** attributing every peak to the segment promotion. Only one segment received it, while the item-group promotion discounted four.

### Requirement (5): The segment with no discounts

**Step 6. Say which segment and why.** The Design Services segment received none: it buys only Services, and no promotion covers Services.

**Check:** two sentences. The first names the segment and the reason. The second says that an item-group promotion discounts every segment that buys the group, so Wholesale, the largest, holds 51.1% of the year's discounts, while a segment promotion reaches only its segment. A strong second sentence also says that the page shows the discounts by invoice month, not what the promotions did to sales, so a calendar aimed at one segment needs that segment's orders and margins as well.

### Requirement (6): The title, the alt text and the saved page

**Step 7. Finish the page and save it.**

a. Select the line chart, and in **Format visual > General > Title** replace the text with `Promotional discounts by customer segment fiscal 2026`.
b. Under **Format visual > General > Alt text**, describe the comparison between the segments and say which segment has no discounts.
c. Click **Save this report**.
d. Choose **Reading view** on the menu bar, and select the page `Ex C.2`.

An alt text that fits is: "A line chart of promotional discounts by month for fiscal 2026, with one line for each customer segment. Design Trade peaks in November, the other segments peak in September or October, and Design Services stays at zero in every month."

**Check:** fiscal 2026 is still selected on the tile slicer, the matrix has five segment rows and twelve month columns, and the chart runs from January to December of fiscal 2026 under the assigned title. **Watch for:** a page that was never saved, whose title and slicer are gone when the report is reopened. A saved slicer selection was not tested in a service, so if the page reopens with another selection, the student selects fiscal 2026 and saves again, and says so. The screenshot or table is the student's evidence, kept in the place you approve, and it needs to be readable: a table of the matrix's values serves a student who cannot attach an image.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Design Trade: largest month; its discounts; the year's | November; $27,595.87; $59,673.47 | 5 |
| Small Business: largest month; its discounts; the year's | September; $4,070.03; $13,279.03 | 5 |
| Strategic: largest month; its discounts; the year's | October; $46,330.25; $104,232.11 | 5 |
| Wholesale: largest month; its discounts; the year's | October; $74,453.77; $184,926.14 | 5 |
| Design Services: every month | zero | 3 |
| Months on the matrix with no year selected | 36 | 3 |

> **Instructor notes, Exercise C.2:** fiscal 2026 discounts by segment, with each segment's peak month: Design Trade peaks in November (27,595.87 of 59,673.47); Small Business peaks in September (4,070.03 of 13,279.03); Strategic peaks in October (46,330.25 of 104,232.11); Wholesale peaks in October (74,453.77 of 184,926.14). (4) Design Trade peaks in November, the month of the Design Trade Customer Promotion, which gives 21,482.20 of it, while 6,113.67 comes from the Furniture Seasonal Promotion's lines invoiced that month. Small Business peaks in September, Strategic peaks in October, Wholesale peaks in October, the months of the Furniture Seasonal Promotion (September and October). (5) Design Services received no discounts. The segment promotion reached one segment, while the item-group promotion reached every segment that bought the group. The pattern shows the discounts by invoice month, not what the promotions did to sales, so a calendar aimed at one segment also needs that segment's orders and margins. (6) The saved page reopens in Reading view with fiscal 2026 selected, the assigned chart title and the alt text.

## What a strong answer says

- **(2), (3), (6)** A saved page with the slicer on fiscal 2026, the matrix with five rows, and the line chart in month order under the assigned title, with an alt text that names the comparison and the segment with no discounts, confirmed again in Reading view and supported by the screenshot or table.
- **(4)** Design Trade Customer Promotion for most of Design Trade's November, with part of the autumn promotion's billing; for the others, the autumn promotion, with the remark that its orders of September and October are invoiced into the next months.
- **(5)** The segment, the reason (it buys only Services), and the distinction between a segment and an item-group promotion.

## Common mistakes and how to respond

- **No year selected.** *Symptom:* 36 columns, and Wholesale's largest month reads 2025-11 ($97,956.73), from a segment promotion of the prior year, instead of October ($74,453.77). *Response:* ask which year the page is about.
- **A sorted line.** *Symptom:* a line that falls from the left. *Response:* ask them to read the axis labels aloud.
- **The zero row called missing.** *Symptom:* "no data for Design Services". *Response:* ask what a zero in every month says that a blank would not.
- **Revenue for discounts.** *Symptom:* the peaks fall in January, February, and March, not in the autumn. *Response:* ask which measure is in **Values**.
- **A page that was not saved.** *Symptom:* the title or the selection is gone in Reading view. *Response:* ask which button saves a report in the editor.
- **One promotion for every peak.** *Symptom:* "the Design Trade promotion explains it all". *Response:* ask who else received it.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 10 | The measure used, in Key Measures | Implicit sum |
| Requirement 2 | 25 | Tile slicer on fiscal 2026, matrix with both wells | Matrix with the year unselected |
| Requirements 3 and 6 | 20 | Legend, months in order, the assigned title and an alt text, the saved page confirmed in Reading view with the screenshot or table | Months in order, title or evidence missing |
| Requirement 4 | 25 | Every peak with its promotion | Peaks without promotions |
| Requirement 5 | 20 | Segment, reason, calendar implication | Segment only |

## Extensions and discussion questions

- Put CustomerSegment in **Small multiples** instead of **Legend**, and compare the two readings.
- Add a dropdown slicer for CustomerSegment, as Tutorial C.2 Step 7 does, and use it to isolate one segment.
- Discuss: the Part II case decides a promotion calendar. What does this page say about a segment promotion for Strategic?
- Discuss: should a segment that buys only Services be offered a promotion, and of what kind?
