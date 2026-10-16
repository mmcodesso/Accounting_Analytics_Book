---
note: ch19.r5
uses: [ch19.g5]
title: Explain the returns and rank the refunds (Chapters 13 to 15)
kind: requirement
number: '5'
unit: '19'
perspective: auditing
tool: powerbi
minutes: 180
solution: "Chapter19-capstone-pbi.zip: Credits Analytics/Credits Analytics.pbip (pages About, Returns, Timing, Concentration, Refund Ranking, Refund Detail, Validation and Notes; the Tests and Checks tabs in DAX query view) and RefundFlags.csv, the export of test T10 of Credits.sql"
figures:
  - id: IF-19-5-A
    kind: pbi-mock
    purpose: The Timing page, the page that shows why the last months and the first year mislead.
    shows: "The Timing page: a line chart by month with two lines, the return rate by the month of the credit and by the month of the shipment, the second falling toward zero in the last month; a table of the rate by year on both bases; a table of the last fiscal year by month of the shipment; a row of cards with the days after shipment and the lines returned in a later year."
    data: The Credits Analytics model on the pinned dataset, all three years.
  - id: IF-19-5-B
    kind: pbi-mock
    purpose: The Refund Ranking page a reviewer starts from.
    shows: "The Refund Ranking page: a bar chart of the refunds at each score from 0 to 5, a matrix of refunds and amounts by flag and year, a matrix of the refunds by approver's job title and year, two cards for the refunds scoring 4 or 5 and their amount, and the table of every refund with its five flags and score sorted from the highest score, one row selected."
    data: The refunds with their flags (RefundFlags.csv) and scores.
---
{% set g = ch19_g5 %}
# Requirement 5: Explain the returns and rank the refunds (Chapters 13 to 15)

{{ header() }}

## Purpose and learning outcomes

The committee will want to see where returns grow, which refunds deserve a second look, and the documents behind each. That is a report, not a workbook: a model with explicit relationships, a Date table that the facts read by their own dates and, through inactive relationships, by the shipment date (Chapter 14), measures that switch, a drill-through page (Chapter 15), and a Validation page and Tests tab that tie it out. The query of Requirement 4 decides which refunds are flagged; the report lets the committee see and drill into the decision. The analytics type is descriptive and diagnostic.

Students can load the cycle's tables and the flags and relate each fact to Date twice (Part 1), write rate and score measures (Part 2), and build the pages, the drill-through and the tie-out (Part 3).

**Competencies practiced.** CPA Evolution Core S1 M8 (data mining and analysis of financial data; visualization and communicating results); IMA Data Analytics and Insights (data analysis, data visualization); IFAC IES 2 (f) and (i); AACSB A5 part 5.1 (Power BI).

## Before you assign

- **Files.** Power BI Desktop (Windows only), CharlesRiver.xlsx and RefundFlags.csv from Requirement 4. The solution reads both from `C:\CharlesRiver\`; students point the queries at their copies with **Change Source**.
- **Data conditions.** {{ g.n_noship|count }} invoice lines (the design services) have no shipment, so revenue by ship date leaves them out. Returns come {{ lag.lo }} to {{ lag.hi }} days after shipment. The data stop a few days before the last year-end, and the first year had no earlier sales to return.
- **Verify first.** In DAX query view, run the Checks tab: {{ g.n_checks }} rows of Requirement 5, {{ g.n_flags }} of the flags and {{ g.n_ms }} of Milestone 2 all agree.

## How to run it

Pairs, about 180 minutes: 40 for the model, 30 for the measures, 70 for the pages and the drill-through, 25 for Validation and Tests, 15 for About. Hold back USERELATIONSHIP until the Timing page looks wrong, and the drill-through until the ranking exists. **Collect** the .pbix and a screenshot of the Tests tab.

## Step-by-step solution

### Part 1: The model

**Step 1. Load the tables.** Choose **Home > Get data > Excel workbook** and load the credit lines and credits, the refunds, the invoice lines, the receipt applications, Item and Customer, GLEntry and Account; choose **Home > Get data** again for the CSV. The shipment, warehouse, return, invoice, receipt and employee queries only feed merges, so clear **Enable load**. The credit lines take their credit, return and shipment by merges:

```jinja
{{ g.m_lines }}
{{ g.m_ship }}
```

GLEntry is filtered first, so only the three posting types the Tests tab needs are loaded:

```jinja
{{ g.m_gl }}
```

**Check:** {{ g.n_lines|count }} credit lines, {{ g.n_cm }} credits, {{ g.n_rf }} refunds, {{ g.n_il|count }} invoice lines and {{ g.n_gl|count }} ledger rows. **Watch for:** the CSV merged into a workbook query, which combines two data sources and risks a privacy-level error; relate it instead.

**Step 2. Relate the tables.** In **Model view**, relate each fact to Date by its own date ({{ g.rel_active }} active relationships) and the credit lines and invoice lines also by ShipmentDate ({{ g.rel_inactive }} inactive, with **Make this relationship active** cleared); relate the facts to Item and Customer, the refunds to RefundFlags on RefundNumber, and GLEntry to Account. The receipt applications stay unrelated and are read by TREATAS in Step 7. **Check:** the Date table carries the active and inactive relationships above.

### Part 2: The measures

**Step 3. Write the rate measures.** The rate by the month of the credit divides each fact by its own date; by the month of the shipment both sides switch to the shipment date.

```jinja
{{ g.d_rate }}

{{ g.d_ship }}
```

**Check:** by year of the credit the rates are {{ g.rate_year[0]|pct(3) }}, {{ g.rate_year[1]|pct(3) }} and {{ g.rate_year[2]|pct(3) }}; by year of the shipment {{ by_ship_year[0]|pct(3) }}, {{ by_ship_year[1]|pct(3) }} and {{ by_ship_year[2]|pct(3) }}. **Watch for:**

- The overall rate by ship date reads {{ g.rate_ship|pct(3) }} against {{ g.rate_all|pct(3) }} by credit date: the lines that never ship are out of its revenue, on purpose.
- Credits taken from the credit memo total, not the lines: it exceeds the lines by ${{ g.tot_diff|money }} (freight and tax), and the Tests tab shows a difference. Counting lines as credits gives {{ g.n_lines|count }} for {{ g.n_cm }}.

**Step 4. Score the refunds.** Enter the five flag names with **Home > Enter data** (the Flags table, disconnected, sorted by an Order column); add the score as a calculated column over the related flags, and switch the flag measures on the selected name.

```jinja
{{ g.d_score }}

{{ g.d_flags }}

{{ g.d_high }}
```

**Check:** scores 0 to 5 count {{ scores|join(', ') }} refunds; {{ hi }} score 4 or 5 (${{ hi_amt|money }}). **Watch for:** a past-due flag on any balance instead of one at least the refund: {{ g.any_hi }} refunds score 4 or 5.

### Part 3: The pages

**Step 5. Build Returns and Timing.** Returns shows credits and the rate by year, item group, reason, segment and the largest group's families: {{ top }} grows from ${{ by_group[0][1][0]|money }} to ${{ by_group[0][1][2]|money }} ({{ top_rates[0]|pct(3) }} to {{ top_rates[2]|pct(3) }} of its revenue), damaged returns from ${{ damaged[0]|money }} to ${{ damaged[2]|money }}. On Timing, the line chart "{{ g.t.timing }}" puts both rates by YearMonth.

{{ figure('IF-19-5-A') }}

**Check:** the last month by shipment month reads {{ dec|pct(2) }} against {{ mlo|pct(2) }} to {{ mhi|pct(2) }} for the other months of that year; the first month by credit month reads {{ g.first_rate|pct(2) }}. **Watch for:** reading either as good news. The last shipments' returns arrive after the data end, and the first year had nothing earlier to return; compare over complete windows.

**Step 6. Build Concentration.** Credit lines by carrier and reason, by warehouse, and a customer table "{{ g.t.concentration }}" sorted by return rate with a visual filter on credits above zero. **Check:** customer {{ focus }} ({{ seg }}, {{ terms }}) has ${{ focus_cred|money }} of credits on sales of ${{ focus_sales|money }}, {{ rate|pct(2) }} against {{ overall|pct(3) }} for all customers; it is first by dollars and number {{ g.rank_rate }} by rate, with customers {{ higher[0][0] }}, {{ higher[1][0] }} and {{ higher[2][0] }} above it, {{ n_small }} on sales under a tenth of its. Carrier and warehouse counts compare only when volumes match; as shares of shipped revenue the carriers run {{ car_rlo|pct(2) }} to {{ car_rhi|pct(2) }}.

**Step 7. Build Refund Ranking and the drill-through.** The ranking page holds the score chart, the flags by year, the approvers and the table "{{ g.t.ranking }}". On Refund Detail, drop RefundNumber in the **Drillthrough filters** well of the Visualizations pane; a reviewer right-clicks a refund and chooses **Drillthrough** and the page, and sees the refund, its flags, its credit, its invoice and the receipts applied to it, read without a relationship:

```jinja
{{ g.d_paid }}
```

{{ figure('IF-19-5-B') }}

**Check:** the largest refund, {{ big }}, scores {{ big_score }}, so it is not at the top of the list although it is the largest.

**Step 8. Add Validation and Tests.** Validation shows credits less `4060` and refunds against `1010` by year, and the cards that compare the score, date and amount with the export. The Tests tab holds {{ g.n_tests }} tests; this instructor check repeats the core of the third:

```jinja
EVALUATE
ROW (
    "Refunds flagged", {{ g.c_flags }},
    "Scores different", {{ g.c_scores }},
    "Exports different", {{ g.c_exports }}
)
```

**Check:** {{ g.n_rf }}, zero and zero. The Checks tab tests the values and the tie to the export; the layout, the drill-through menu and the slicer state show only in Desktop.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Credit lines; credits; refunds | {{ g.n_lines|count }}; {{ g.n_cm }}; {{ g.n_rf }} | 1 |
| Rate by year of the credit | {{ g.rate_year[0]|pct(3) }}; {{ g.rate_year[1]|pct(3) }}; {{ g.rate_year[2]|pct(3) }} | 3 |
| Refunds scoring 4 or 5; their amount | {{ hi }}; ${{ hi_amt|money }} | 4 |
| Customer {{ focus }}: credits; rate | ${{ focus_cred|money }}; {{ rate|pct(2) }} | 6 |
| Checks that agree | {{ g.n_checks }}; {{ g.n_flags }}; {{ g.n_ms }} | 8 |

{{ expected() }}

## What a strong answer says

- **Each fact is read by its own date and by the shipment date,** and the report says which basis each rate uses.
- **Timing is allowed for:** the last months and the first year are explained, not presented as trends.
- **Concentration is a share of each customer's sales,** and the customer to follow up is found by both dollars and rate.
- **The ranking is traceable:** a reviewer drills from the score to the refund, its credit and its invoice, and Validation ties the report to the ledger and the export.

A weak answer shows counts without rates, ranks customers by dollars, or leaves the report with no tie-out.

## Common mistakes and how to respond

- **Revenue by ship date with the unshipped lines.** *Symptom:* a rate that differs from the overall card. *Response:* ask which lines have no shipment.
- **The last month as good news.** *Symptom:* a rate of {{ dec|pct(2) }}. *Response:* ask when those returns will arrive.
- **The first year's first months.** *Symptom:* {{ g.first_rate|pct(2) }}. *Response:* ask how many earlier sales it had.
- **Customers ranked by dollars.** *Symptom:* customer {{ focus }} alone. *Response:* ask the rate on its sales.
- **Credit memo total on the Tests tab.** *Symptom:* a difference of ${{ g.tot_diff|money }}. *Response:* ask what the total adds to the lines.
- **Lines counted as credits.** *Symptom:* {{ g.n_lines|count }} for {{ g.n_cm }}. *Response:* ask what one credit is.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Model and relationships | 25 | All tables and flags, each fact related twice, the CSV related not merged | Relationships without the shipment dates |
| Measures | 25 | Rates by both dates, the score and the flag measures | One basis only |
| Pages and drill-through | 30 | Returns, Timing, Concentration, Ranking and a working drill-through | Pages without the timing explanation |
| Validation and Tests | 20 | Ties to the ledger and the export | Validation without a test |

## Extensions and discussion questions

- Add a by-ship-month table of the last year that leaves out the censored month, and say what it shows.
- Discuss: should the committee see the score or the five flags?
- Discuss: which page would you open the meeting with, and what would you say it cannot show?
