---
note: ch05.ex1
uses: [ch05.g1]
title: Net Furniture Revenue by Quarter
kind: exercise
number: '5.1'
unit: '5'
perspective: financial
tool: excel
minutes: 75
solution: "Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheets Ex 5.1, Ex 5.1 CreditMemo and Ex 5.1 CreditMemoLine"
figures:
  - id: IF-05-1-A
    kind: excel-mock
    purpose: The quarterly grid of Exercise 5.1 with its check row and the earlier-year credits beneath it.
    shows: "Rows labeled Furniture revenue billed, Furniture credit memo lines and Net Furniture revenue, with the four period labels of the fiscal year in the header row and a Total column. Below the three rows sit a count of credit memo lines, the credits as a share of revenue billed, and a cell for credit memo lines not matched that reads zero. Under a second heading sit the count of credit memos for invoices of earlier years, the Furniture credits they carry, and the net revenue with those credits moved to their invoice's year. The net revenue row is bold."
    data: InvoiceLines, CreditMemoLine and CreditMemo (the Expected results table).
---
{% set g = ch05_g1 %}
# Exercise 5.1: Net Furniture Revenue by Quarter

{{ header() }}

## Purpose and learning outcomes

The chapter prepared the invoice lines and left a gap: they show what was billed, not what was kept. This exercise brings in a second source of the same shape, the credit memo lines, and asks students to prepare it with the same lookups before comparing the two. It practices loading Tables with Power Query, lookups with a "No match" check, SUMIFS on a period label, and a judgment about timing. The analytics type is descriptive.

By the end, students can:

- load two related Tables with Power Query and bring a date and an item group onto the child Table by lookup (outcomes 5 and 4);
- build a period label with a date function and use it as a SUMIFS criterion (outcome 3);
- reconcile a net figure to the gross figure it starts from, say what the difference is, and state which period a credit belongs to (outcome 1).

**Competencies practiced.** CPA Evolution Core S1 M8 T2 (financial data: extraction, transformation and cleansing) and Core S1 M1 to M3 (financial statements, accounts and transactions); IMA Data Tools and Techniques, and Financial Recordkeeping; IFAC IES 2 (a) and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The copy of Charles River Furniture Analysis.xlsx made after Tutorial 5.3, so that InvoiceLines, the Item Table and SalesInvoice exist. XLOOKUP is in every desktop Excel that Microsoft still supports.
- **Data conditions.** The CreditMemo and CreditMemoLine Tables hold {{ g.memos_all|count }} memos and {{ g.lines_all|count }} lines, all years. Every credit memo line is for an item the workbook's Item Table keeps, so no lookup fails. Some memos hold lines of Furniture and of another item group, which matters for the header-total shortcut below.
- **Check the Tutorial 5.3 workbook first.** The grid reads the Period and ItemGroup columns of InvoiceLines. A student who skipped Tutorial 5.3 needs the start or end file in Chapter05-companion.zip.
- **Where the new columns go.** CreditMemoLine has its database columns first. The three new columns are CreditMemoDate in column {{ g.letters.CreditMemoDate }}, Period in {{ g.letters.Period }} and ItemGroup in {{ g.letters.ItemGroup }}.

## How to run it

Individual, about 75 minutes: 10 on loading (requirement 1), 20 on the three columns (2), 15 on the grid (3), 20 on the earlier-year credits (4) and 10 on the note. Hold back the hint about the period label until a student sees zero credits. Collect the workbook and the note.

## Step-by-step solution

### Requirement (1): Load the credit memos

**Step 1. Import the two Tables.**

a. Choose **Data > Get Data > From File > From Excel Workbook**, select CharlesRiver.xlsx and click **Import**.
b. In the **Navigator**, select the **Select multiple items** check box, select **T23_CreditMemo** and **T24_CreditMemoLine**, and click **Transform Data**.
c. Rename the queries `CreditMemo` and `CreditMemoLine`. In CreditMemo, check the icon of CreditMemoDate; if it shows a time, set the type to **Date** and choose **Replace current**.
d. Choose **Home > Close & Load > Close & Load To**, select **Table** and **New worksheet**, and rename the worksheets `Ex 5.1 CreditMemo` and `Ex 5.1 CreditMemoLine`.

**Check:** the Table Name box shows CreditMemo with {{ g.memos_all|count }} rows and CreditMemoLine with {{ g.lines_all|count }}. **Watch for:** a plain **Close & Load**. No worksheets appear, because Excel loads several queries to the Data Model. Use **Data > Queries & Connections**, right-click each query and choose **Load To**.

### Requirement (2): Date, period and group on each credit line

**Step 2. Bring CreditMemoDate onto the lines.** In the first empty cell right of the last header of CreditMemoLine, type `CreditMemoDate`, enter the formula below and format the column as a date:

```
=XLOOKUP([@CreditMemoID],CreditMemo[CreditMemoID],CreditMemo[CreditMemoDate],"No match")
```

**Step 3. Add the period and the item group.** Add `Period` with `=YEAR([@CreditMemoDate])&"-Q"&ROUNDUP(MONTH([@CreditMemoDate])/3,0)`, and `ItemGroup` with:

```
=XLOOKUP([@ItemID],Item[ItemID],Item[ItemGroup],"No match")
```

**Step 4. Count the failures.** On `Ex 5.1` enter `=COUNTIF(CreditMemoLine[[CreditMemoDate]:[ItemGroup]],"No match")`.

**Check:** zero, and the first period labels read like `{{ g.periods[0] }}`. **Watch for:** a lookup on CreditMemoLineID instead of CreditMemoID. The two ID ranges overlap, so most lines get a plausible date from the wrong memo and {{ g.wrong_key|count }} lines read "No match". A small nonzero count is a symptom, not noise.

### Requirement (3): The quarterly grid

**Step 5. Build the grid.**

a. On `Ex 5.1` put the fiscal year ({{ g.y }}) in B2, in blue as an input, and type the four period labels in B4 to E4 as text.
b. Enter the first formula below in B5 and the second in B6, fill both across by copy and paste, and enter `=B5-B6` in B7. Add a Total column with SUM.

```
=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],"Furniture",InvoiceLines[Period],B$4)
=SUMIFS(CreditMemoLine[LineTotal],CreditMemoLine[ItemGroup],"Furniture",CreditMemoLine[Period],B$4)
```

c. In row 9 count the Furniture credit lines with COUNTIFS on the same two criteria.

**Check:** the Expected results table. Billed revenue for the third and fourth quarters equals the Part I case and Tutorial 5.2's grid. **Watch for:** credits added instead of subtracted. The credit lines carry positive LineTotal values, so net revenue above billed revenue is the symptom. Also watch for a period label built differently on the two sides (`2026Q1` against `2026-Q1`): SUMIFS then returns zero credits in every quarter and no error.

### Requirement (4): Credits for invoices of earlier years

**Step 6. Find the invoice behind each credit.** In the CreditMemo Table add `OriginalInvoiceDate` with the first formula below and `EarlierYearInvoice` with the second.

```
=XLOOKUP([@OriginalSalesInvoiceID],SalesInvoice[SalesInvoiceID],SalesInvoice[InvoiceDate],"No match")
=AND(YEAR([@CreditMemoDate])='Ex 5.1'!$B$2,YEAR([@OriginalInvoiceDate])<'Ex 5.1'!$B$2)
```

Bring the flag to CreditMemoLine with an XLOOKUP on CreditMemoID, then count the flagged memos with COUNTIF and sum the Furniture credits with SUMIFS on the flag.

**Check:** {{ g.early_memos|count }} memos dated {{ g.early_first }} to {{ g.early_last }}, for invoices dated {{ g.inv_first }} to {{ g.inv_last }}; {{ g.early_furn_lines|count }} of their lines are Furniture, ${{ g.early_furn|money }}, all in {{ g.periods[0] }}.

**Step 7. Write the note.** Two or three sentences. The model answer assigns each credit to the quarter of its credit memo, because the ledger records it on that date and the schedule is one of recorded activity. It names the alternative, the quarter of the original invoice, which answers a different question, the net result of each quarter's sales, and belongs in a separate schedule, labeled and reconciled to this one. It says that neither choice changes the ledger and that the choice moves only ${{ g.early_furn|money }} out of {{ g.periods[0] }}. It adds that the credits are small and do not explain the change between the third and fourth quarters.

**Check:** the note states which assignment the schedule uses.

## Expected results

| Period | Billed | Credit lines | Credits | Net |
|---|---:|---:|---:|---:|
{% for c in credits %}
| {{ g.periods[loop.index0] }} | ${{ gross[loop.index0]|money }} | {{ c.lines|count }} | ${{ c.amount|money }} | ${{ net[loop.index0]|money }} |
{% endfor %}
| Credit lines in the year; credits | | {{ credit_lines|count }} | ${{ credit_total|money }} | |
| Lookups not matched | | | | 0 |
| Credit memos of the year for invoices of earlier years; Furniture credits | | {{ g.early_memos|count }} | ${{ g.early_furn|money }} | |
| Net revenue of the third and fourth quarters with each credit assigned to its invoice's quarter | | | ${{ g.alt3|money }}; ${{ g.alt4|money }} | |

{{ figure('IF-05-1-A') }}

{{ expected() }}

## What a strong answer says

- **Requirement (3).** The grid ties: billed revenue agrees with the earlier tutorial, credits are summed by credit memo date, and net is billed less credits.
- **Requirement (4).** A stated choice with its reason. The ledger records a credit on the credit memo's date, so the credit memo's quarter suits a schedule of recorded activity. The invoice's quarter answers a different question, the net result of each quarter's sales, and goes in a separate schedule, labeled and reconciled to this one. Neither changes the ledger, and an adjustment to an earlier period would need accounting and transaction evidence, not a choice of schedule.
- **The comparison.** Credits are at most {{ g.max_share|pct }} of billed revenue in any quarter, and net revenue still falls from the third to the fourth quarter under either assignment. The credits are not the story of the quarter, and the note should say so.

A weak answer chooses an assignment without a reason, or concludes that the credits explain the fall.

## Common mistakes and how to respond

- **Both Tables in the Data Model.** *Symptom:* no worksheets. *Response:* **Load To** from **Queries & Connections**.
- **The wrong lookup key.** *Symptom:* {{ g.wrong_key|count }} lines read "No match" and the rest carry dates from other memos. *Response:* ask which column of CreditMemo each line belongs to, and compare a line's date with its memo's.
- **A header total for the Furniture credit.** *Symptom:* credits above the line total, by ${{ g.header_over|money }} in the year. *Cause:* {{ g.mixed|count }} memos hold Furniture and other lines, so a memo's SubTotal is not Furniture. *Response:* sum the lines.
- **Credits added to revenue.** *Response:* ask whether a credit memo increases or decreases revenue.
- **Mismatched labels.** *Symptom:* zero credits, no error. *Response:* click one Period cell and one header label and compare them character by character.
- **A bare assertion about timing.** *Response:* ask which question each assignment answers, and which one this schedule is for.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: loading | 15 | Both Tables loaded as worksheets, date typed | Loaded to the Data Model |
| Requirement 2: columns | 25 | Three lookups on the right keys and a count of "No match" | Values pasted, or no count |
| Requirement 3: the grid | 30 | SUMIFS with the period label, net by subtraction, ties to the earlier tutorial | Typed labels that miss, or credits added |
| Requirement 4: earlier years | 30 | Flag by lookup, the memos counted, a stated assignment with a reason | Count without the reason |

## Extensions and discussion questions

- Assign each credit to the quarter of its original invoice and compare: the net revenue of the third and fourth quarters becomes ${{ g.alt3|money }} and ${{ g.alt4|money }}.
- Redo requirement (2) with Power Query merges instead of lookups, and compare the row counts before and after.
- Discuss: Chapter 6 bridges the Furniture margin from billed revenue. Would net revenue change the bridge, and which credits would belong in it?
- Discuss: every credit for an earlier year's invoice is dated in January. What would you ask the people who process returns?
