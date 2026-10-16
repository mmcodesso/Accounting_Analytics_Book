# Exercise 5.3: The Furniture Product Mix

| | |
|---|---|
| Unit | Chapter 5: Data Preparation and Cleaning in Excel |
| Item | Exercise 5.3 |
| Perspective | Managerial accounting |
| Tools | Excel |
| Time | About 75 minutes |
| Solution file | Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheet Ex 5.3 |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Before the controller measures what moved the Furniture margin, the first question is whether the product mix moved. The exercise uses the product type that Tutorial 5.1 extracted from the item code and the InvoiceLines table of Tutorial 5.3. It practices SUMIFS with three criteria, shares and changes in share, a conditional formatting rule, and a judgment about which measure of mix to trust. The result is modest, and the exercise is also about writing that down. The analytics type is descriptive.

By the end, students can:

- build a grid of SUMIFS with an item group, a product type and a period as criteria, and tie it to an earlier total (outcomes 2 and 4);
- calculate shares and changes in share, and read a change in percentage points correctly (outcome 1);
- write a formula rule that tests the size of a change in either direction (outcome 2);
- explain why fractional quantities make revenue shares the safer measure of mix (outcome 6).

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis of financial data); IMA Data Analysis, and Performance Management; IFAC IES 2 (b), management accounting, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The analysis workbook after Tutorial 5.3: the grid reads InvoiceLines, so students who skipped that tutorial need the end file.
- **Data conditions.** The eight Furniture product types are the codes of Tutorial 5.1's table. The code `TBL` is also used by another item group (Lighting), which is why the exercise asks for ItemGroup as a criterion. Most Furniture lines of the two quarters carry a fractional quantity.
- **Alignment with Exercise 5.1.** The Furniture totals of the two quarters must equal the billed revenue of Exercise 5.1 and Tutorial 5.2, so a student can tie the grid to earlier work.

## How to run it

Individual, about 75 minutes: 20 on the grid (requirement 1), 10 on shares (2), 15 on the rule and its test (3) and 20 on the interpretation (4), with 10 for ties and formatting. Hold back the hint about testing the rule until a student reports that nothing is highlighted and is satisfied. Collect the workbook and the paragraph.

## Step-by-step solution

### Requirement (1): The grid

**Step 1. Lay out the grid.** On `Ex 5.3` type the two period labels as text in C2 and E2 (`2026-Q3` and `2026-Q4`). In row 3 type `Code`, `Product type` and the revenue and quantity headings of each period. In A4 to A11 type the eight codes and in B4 to B11 their names from the chapter's table of product types.

**Step 2. Fill the formulas.** In C4 and D4 enter the first two formulas below, and in E4 and F4 the same two with `$E$2`. Fill down by copy and paste. Put a Total row in row 12 with SUM.

```
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],"Furniture",InvoiceLines[ProductType],$A4,InvoiceLines[Period],$C$2)
=SUMIFS(InvoiceLines[Quantity],InvoiceLines[ItemGroup],"Furniture",InvoiceLines[ProductType],$A4,InvoiceLines[Period],$C$2)
```

**Check:** the Total row equals $4,283,322.86 and $4,156,787.84, the Furniture revenue of Exercise 5.1. **Watch for:** the ItemGroup criterion left out. The code TBL then also picks up the Lighting table lamps, which adds $253,326.44 to the third quarter and $234,294.32 to the fourth, and the total no longer ties. A total that ties is the check, not the sight of eight plausible rows.

### Requirement (2): Shares and changes

**Step 3. Add the shares.** In G4 enter `=C4/C$12`, in H4 `=E4/E$12` and in I4 `=H4-G4`. Fill down and total. Format G to I as percentages.

**Check:** the shares add to 100 percent and the changes to zero. **Watch for:** a reading of column I as a percent of a percent. A value of 1.1% is 1.1 percentage points of the Furniture total.

### Requirement (3): The highlight rule

**Step 4. Write the rule.**

a. Put the threshold in a cell, B14, as `0.02` and format it as a percentage, so a student can change it.
b. Select A4 to I11 with A4 active, then choose **Home > Conditional Formatting > New Rule**.
c. Select **Use a formula to determine which cells to format**, enter `=ABS($I4)>$B$14` and choose a fill.
d. In B15 count the product types over the threshold: `=SUMPRODUCT(--(ABS(I4:I11)>B14))`.

**Check:** nothing is highlighted and B15 reads 0. **Watch for:** a rule that passes this check and is wrong. No change in share exceeds two points in either direction, so a rule without ABS, or one that compares with `2` instead of `0.02`, also highlights nothing. Test the rule by typing `0.01` in B14: B15 then reads 4, and the rows of BKC, CON, NGT, SDB light up, the rises and the falls alike. Put `0.02` back.

### Requirement (4): The interpretation

**Step 5. Write three or four sentences.** A model answer: Furniture revenue fell by $126,535.02 between the two quarters. Nightstands and sideboards lost the most revenue (4 of the eight types fell) and consoles and bookcases gained the most, with benches and dining tables also gaining. The largest changes in share are NGT -1.8, SDB -1.3, CON +1.5, BKC +1.1 points, so no type passes two points and the mix moved only modestly. Quantities need care: 95% of these Furniture lines carry a fractional quantity, even for items sold by the unit, so quantities are not counts of whole products. Revenue shares do not depend on the quantity field, though they measure dollars, which prices and discounts move as well as volume.

**Check:** the note says the shift is modest, uses shares, and names the quantity limitation.

## Expected results

| Code and type | Q3 revenue | Q4 revenue | Q3 quantity | Q4 quantity | Change in share |
|---|---:|---:|---:|---:|---:|
| BKC Bookcase | $259,617.77 | $297,121.44 | 475.61 | 517.59 | +1.1 points |
| BNH Bench | $234,227.64 | $239,562.62 | 374.62 | 422.79 | +0.3 points |
| CON Console table | $454,136.92 | $504,299.85 | 636.04 | 667.36 | +1.5 points |
| CTB Coffee table | $732,861.82 | $690,150.36 | 1,296.08 | 1,240.95 | -0.5 points |
| DSK Desk | $768,977.89 | $751,338.42 | 1,050.73 | 1,195.45 | +0.1 points |
| NGT Nightstand | $457,540.67 | $369,972.92 | 905.06 | 734.14 | -1.8 points |
| SDB Sideboard | $633,110.81 | $558,717.15 | 1,072.57 | 958.22 | -1.3 points |
| TBL Dining table | $742,849.34 | $745,625.08 | 1,280.52 | 1,385.62 | +0.6 points |
| Total | $4,283,322.86 | $4,156,787.84 | 7,091.23 | 7,122.12 | 0.0 |
| Product types over two points; over one point | 0; 4 | | | | |
| Furniture lines in the two quarters; with a fractional quantity | 1,732; 1,652 | | | | |

![A mock of the product mix grid with the highlight threshold lowered to one percentage point, which shows that the rule works.](../figures/chapter-05-data-preparation/IF-05-3-A.pdf)

> **Instructor notes, Exercise 5.3:** Furniture revenue by product type, Q3 / Q4 (quantity Q3 / Q4): BKC 259,617.77 / 297,121.44 (475.61 / 517.59); BNH 234,227.64 / 239,562.62 (374.62 / 422.79); CON 454,136.92 / 504,299.85 (636.04 / 667.36); CTB 732,861.82 / 690,150.36 (1,296.08 / 1,240.95); DSK 768,977.89 / 751,338.42 (1,050.73 / 1,195.45); NGT 457,540.67 / 369,972.92 (905.06 / 734.14); SDB 633,110.81 / 558,717.15 (1,072.57 / 958.22); TBL 742,849.34 / 745,625.08 (1,280.52 / 1,385.62). Totals 4,283,322.86 / 4,156,787.84. Nightstands and sideboards lost the most revenue; consoles and bookcases gained the most, and benches and dining tables also gained. Largest share changes: NGT -1.8 pts, SDB -1.3 pts, CON +1.5 pts, BKC +1.1 pts; the two-point threshold highlights none, a useful result: the mix shift is modest. Quantities are fractional on most lines (the validity finding), so unit counts are not whole products; revenue shares avoid the issue.

## What a strong answer says

- **Requirement (1).** A grid that ties to the Furniture total, with the item group as a criterion and a reason for it.
- **Requirement (3).** A rule with ABS and an active cell stated, tested by lowering the threshold.
- **Requirement (4).** Which types gained and lost, the size of the largest shifts, the conclusion that the mix moved modestly, and two reasons to prefer shares: the quantity field is not whole units, and shares do not need it. A strong student adds that shares of dollars still mix price and volume, which Chapter 6's bridge separates.

A weak answer reads the unit counts as volume, or calls the mix shift large without a threshold.

## Common mistakes and how to respond

- **No ItemGroup criterion.** *Symptom:* the totals do not tie, and TBL is too high. *Response:* ask which other group uses the code, and tie the total to Exercise 5.1.
- **A rule on the wrong cell.** *Symptom:* shading in the wrong rows. *Cause:* a different active cell. *Response:* open **Manage Rules** and read the rule for the first row.
- **A rule that cannot fire.** *Symptom:* nothing highlighted, student satisfied. *Response:* lower the threshold and see whether anything lights up.
- **A threshold of 2.** *Response:* ask what a change of two percentage points looks like as a decimal in column I.
- **Shares of the wrong total.** *Symptom:* shares that do not add to 100 percent. *Response:* check the dollar signs on the total row.
- **Quantities as units.** *Response:* ask how many sideboards a quantity with decimals sold.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the grid | 30 | SUMIFS with three criteria, a Total that ties | A grid without the ItemGroup criterion, or typed |
| Requirement 2: shares | 20 | Shares and change in points, locked total row | Relative total row |
| Requirement 3: the rule | 25 | Formula rule with ABS, tested | A rule that is not tested |
| Requirement 4: the interpretation | 25 | Direction, size, modest shift, the quantity limit | Direction only |

## Extensions and discussion questions

- Chart the change in share with a bar chart, and decide whether the chart helps more than the shading.
- Repeat the grid for Lighting, and say what the code TBL does to a grid without ItemGroup there.
- Discuss: shares of revenue move when prices move. What would you need to separate price from mix? Chapter 6 builds that bridge.
- Discuss: a rule is tested by the case it should catch. Which other tests in this chapter would you test the same way?
