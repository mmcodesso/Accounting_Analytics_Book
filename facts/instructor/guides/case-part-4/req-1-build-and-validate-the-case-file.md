---
note: case4.r1
uses: [case4.g1]
title: Build and validate the case file (Chapters 13, 14, and 16)
kind: requirement
number: '1'
unit: case4
perspective: general
tool: powerbi
minutes: 150
solution: "PartIV-case.zip: Charles River Cash Case.pbip, pages About and Validation, the Tests tab (Tests 1 and 2) and the Requirement 1 rows of the Checks tab"
figures:
  - id: IF-C4-1-A
    kind: pbi-mock
    purpose: The Validation page the model answer ends Requirement 1 with, the evidence a student must reproduce before Requirement 2.
    shows: "Report view, page Validation. A table titled Control totals by fiscal year with one row for each fiscal year and seven columns: Year, Net Income, Total Assets, Materials Received, Receipts to 1045, Materials Issued and Issues from 1045; each materials pair, Materials Received with Receipts to 1045 and Materials Issued with Issues from 1045, is outlined because it agrees. Below it a row of five cards titled Links tested: Receipt Lines, Receipts without a Requisition, Issue Lines, Issues without a Work Order and Requisition Count. The two link cards that count exceptions read zero and are outlined."
    data: The Expected results quantities (net income, total assets, materials received and issued by fiscal year; the link counts), read-only.
---
{% set g = case4_g1 %}
# Requirement 1: Build and validate the case file (Chapters 13, 14, and 16)

{{ header() }}

## Purpose and learning outcomes

Everything the committee will read rests on this file, so students prove it first: queries that follow the Part IV conventions, profiles on the whole data set, links tested, control totals that agree with what they trust, and a date for how far the data run. The analytics type is descriptive, with a diagnostic edge in the link tests.

Students can:

- build the queries and the ledger star, flag the closing entries and describe every measure (Part 1);
- profile the new Tables on the entire data set and test the links later requirements rely on (Part 2);
- tie the new tables to account `1045` on a Validation page and in a Tests tab (Part 3);
- define Data Through and say why the last posting date in the ledger is the wrong answer (Part 4).

**Competencies practiced.** CPA Evolution BAR M10 (advanced data analytics) and Core S1 M8 T2 (financial data: extraction, transformation and cleansing); IMA Data Analytics and Insights (data tools and techniques); IFAC IES 2 (i), using information and communications technology to analyze data; AACSB A5 part 5.1 (technology integration, Power BI).

## Before you assign

- **Files.** CharlesRiver.xlsx in the folder where students save Charles River Cash Case.pbix, and Power BI Desktop at the release the Part IV chapters use. The model answer is the project in PartIV-case.zip; open it as Opening a Companion File on the Downloads page describes (copy the .pbip and its two folders, open the .pbip, **Change Source**, refresh).
- **Data conditions.** PurchaseRequisition.Justification names the channel; the order header's RequisitionID is blank on many orders; InventoryPolicy has one row for each item and warehouse; the ledger's last posting date is not Data Through, and Data Through itself is a bound observed in the extract, not proof that the data are complete.
- **Verify first.** After a refresh, the {{ g.n_checks }} Requirement 1 rows of the Checks tab all agree.

## How to run it

Individual or pairs, about 150 minutes: 50 for the queries and model, 30 for profiles and links, 40 for Validation and the Tests tab, 30 for Data Through and the About page. Hold back the header-link explanation until a pair sees blank channels. **Collect** the .pbix.

## Step-by-step solution

The project encodes the model and the structure of each page, and its Checks tab proves every value below. How a page looks is visible only in Desktop. The M blocks of a Custom Column are the expression alone, which the dialog takes under the column's name and type. Power Query shows the same step in the formula bar and the Advanced Editor as a `Table.AddColumn` assignment, which is not pasted into the dialog.

### Part 1: The queries and the model

**Step 1. Load the ledger star and flag the closes.**

a. Save Charles River Cash Case.pbix and turn off Auto date/time and Autodetect new relationships under Current File, as Tutorial 13.1 did.
b. Choose **Home > Get data > Excel workbook**, select GLEntry, Account and JournalEntry, and choose **Transform Data**.
c. In GLEntry, choose **Home > Choose Columns**, keep only what the model needs and filter no rows. Merge JournalEntry on VoucherNumber and EntryNumber with **Home > Merge Queries** and expand EntryType.
d. Name the column `IsYearEndClose`, choose **Add Column > Custom Column** (Tutorial 14.3), enter only the expression below, set the type to True/False, and clear **Enable load** on JournalEntry.

```m jinja
{{ g.e_close }}
```

**Check:** GLEntry has all {{ gl_rows|count }} rows and {{ close_rows }} are flagged: the {{ n_closes }} closes ({{ closes|join('; ') }}). **Watch for:** closes left unflagged. Net income nets to zero in every year, because each close moves a year's revenue and expenses to retained earnings.

**Step 2. Carry the channel into Receipts.**

a. In Requisitions, choose **Add Column > Custom Column**, name the column `Channel`, enter only the first expression below and set the type to Text. Add `WorkOrderID` from the second expression, as a Whole number. Merge WorkOrder and Employee (requester and approver).
b. In Receipts, merge OrderLines on POLineID, then Requisitions on RequisitionID, and expand Channel.

```m jinja
{{ g.e_channel }}
```

```m jinja
{{ g.e_workorder }}
```

**Check:** {{ shortfall|count }} work-order shortfall requisitions, {{ supply|count }} supply plan and {{ n_other }} other. Receipts goes through the order line because the order header names no requisition on {{ blank_header|count }} orders. **Watch for:** a merge through the header. {{ g.hdr_lines|count }} of {{ g.receipt_lines|count }} receipt lines then have no channel, and the materials among them, {{ g.hdr_mat_lines|count }} lines worth ${{ g.hdr_mat_value|money }}, drop out of Requirement 4's channel columns.

**Step 3. Build Issues and Item, relate and describe.**

a. In Issues, merge the issue's date and work order. In InventoryPolicy, choose **Group By** (**Advanced**) on ItemID with the largest target and the latest end date, then merge it into Item. Clear **Enable load** on the queries that only feed others.
b. In **Model view**, relate each fact table to its dimensions and to Date, many to one, **Single** direction, and hide the keys.
c. Choose **Modeling > New measure** for each measure and type its definition in **Properties**.

```m jinja
{{ g.m_policy }}
```

**Check:** Item has {{ g.n_items|count }} rows. **Watch for:** the policy merged before it is grouped. The {{ g.two_policy|count }} items with a policy at both warehouses appear twice, so Item has {{ g.ungrouped|count }} rows, ItemID is no longer unique and the relationship cannot be one to many. The Group By step is shown as the formula bar reads it.

### Part 2: Profiles and links

**Step 4. Profile on the entire data set.**

a. In Power Query, choose **View > Column quality**, **Column distribution** and **Column profile**.
b. Click **{{ g.label_top }}** in the status bar and choose **Column profiling based on entire data set**.
c. Read Justification, Status and ApprovedByEmployeeID in Requisitions.
d. Profile every other new Table the same way (Receipts, Issues, InventoryPolicy, the invoice, payment and credit Tables, DebtSchedule) and record its grain, row count, missing and duplicate keys, date range, errors and disposition. Check that each merge keeps its fact table's row count.

**Check:** {{ requisitions|count }} requisitions, Justification never empty, {{ no_approver }} without an approver and {{ g.all_approved|count }} Approved. **Watch for:** the default profile. The first {{ g.top_n|count }} rows are all converted to orders, so no Approved requisition shows, only {{ g.top_no_app }} of the {{ g.all_no_app }} blank approvers do, and the shortfall channel is {{ g.top['Shortfall'][0] }} rows of the thousand when it is most of the data set.

**Step 5. Test the links.** Add `Receipts without a Requisition`, `Issues without a Work Order` and the row counts to Key Measures, and show them as cards titled "{{ g.t_links }}".

**Check:** all {{ receipt_lines|count }} receipt lines find their order line, each of the {{ po_lines|count }} order lines names one requisition, and {{ issue_lines|count }} issue lines sit on {{ issues_with_lines|count }} issues that all find their work order. Issue headers with no lines number {{ empty_issues }} (Chapter 12): record them and move on.

### Part 3: Validation and the Tests tab

**Step 6. Reproduce the control totals.** Add a **Table** titled "{{ g.t_control }}" with Year from Date and the measures `Net Income`, `Total Assets`, `Materials Received`, `Receipts to 1045`, `Materials Issued` and `Issues from 1045`, filtered to the years of the window in **Filters on this visual**. The `1045` measures filter AccountNumber.

**Check:** net income and total assets are Tutorial 14.3's and Exercise 14.1's, and each materials pair agrees. **Watch for:** two silent errors. A filter on AccountID `1045` finds no account, and receipts of every item read ${{ g.by_year[-1][1]|money }} in {{ d.C }} against ${{ g.by_year[-1][2]|money }} of materials.

{{ figure('IF-C4-1-A') }}

**Step 7. Write the Tests tab.** In **DAX query view**, type each test under a comment and choose **Run**. Test 1 is the table above in `SUMMARIZECOLUMNS`; Test 2 returns Data Through, the last ledger posting and what follows it. Requirements 2 and 5 add Tests 3 to 5.

### Part 4: Data Through and the About page

**Step 8. Write Data Through and the About page.** Choose **Modeling > New measure**, enter the formula, and add a card titled "{{ g.t_data }}" to the About page with Data Through and the ledger's last posting, and a text box that states the purpose, sources, period, definitions and why Data Through is not the last posting.

```dax jinja
{{ g.d_through }}
```

**Check:** Data Through reads {{ g.through }} under any slicer, because `REMOVEFILTERS ()` clears every filter. The ledger runs to {{ g.last }} only because {{ n_pay|count }} supplier payments of {{ d.C }} invoices (${{ pay_amount|money }}, {{ rows_after|count }} rows) follow the year. **Watch for:** two wrong answers. The last posting date puts cash at ${{ cash_last|money }}, and a bridge for {{ d.N }} shows a fall of ${{ fall|money }} that only means the data stop. Adding payroll puts Data Through at {{ g.pay_end }}, and the last quarter goes blank, because the last {{ n_open }} pay periods are marked Open in the data and are scheduled to pay in {{ open_pay_year }}. The About page states what Data Through does not show, that no document before it is missing.

**Instructor check.** In **DAX query view**, run this and compare it with the Expected results.

```dax jinja
{{ g.dax_check }}
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| GLEntry rows; flagged closing rows | {{ gl_rows|count }}; {{ close_rows }} | 1 |
| Shortfall; supply plan; other requisitions | {{ shortfall|count }}; {{ supply|count }}; {{ n_other }} | 2 |
| Item rows; approved and unordered requisitions | {{ g.n_items|count }}; {{ unordered|count }} | 3, 4 |
| Net income {{ d.F }}, {{ d.P }}, {{ d.C }} | ${{ ni[0]|money }}; ${{ ni[1]|money }}; ${{ ni[2]|money }} | 6 |
| Total assets {{ d.F }}, {{ d.P }}, {{ d.C }} | ${{ assets[0]|money }}; ${{ assets[1]|money }}; ${{ assets[2]|money }} | 6 |
| Materials received and issued, {{ d.C }} | ${{ received[2]|money }}; ${{ issued[2]|money }} | 6 |
| Data Through; last posting; rows after | {{ g.through }}; {{ g.last }}; {{ rows_after|count }} | 8 |

{{ expected() }}

## What a strong answer says

- **Model.** Closes flagged and left out of every flow, the channel carried through the order line, the policy grouped before it is merged, every measure defined.
- **Profiles and links.** Entire data set, each link tested, isolated exceptions recorded.
- **Validation.** Totals that agree with Tutorial 14.3 and Exercise 14.1, and the new tables tied to account `1045` in a Tests tab.
- **Data Through.** The earliest of the last posting dates of the documents behind the working-capital accounts, with the reason (supplier payments follow the year, and payroll ends before it) and the limit, a bound observed in the extract rather than proof of completeness.

A weak submission says the totals "look right" and has no Tests tab.

## Common mistakes and how to respond

- **Closes left in.** *Symptom:* net income reads zero in every year. *Response:* ask what a close does to a year's revenue and expenses.
- **Merge through the header.** *Symptom:* {{ g.hdr_lines|count }} receipt lines with no channel. *Response:* ask which table names the requisition for each line.
- **Policy not grouped.** *Symptom:* {{ g.ungrouped|count }} item rows. *Response:* ask how many policy rows an item has, and which items have two.
- **Profile of the first rows.** *Symptom:* no Approved requisition in the profile. *Response:* ask which basis the status bar names.
- **Last posting as Data Through.** *Symptom:* {{ g.last }} on the About page. *Response:* ask what posts after the year.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Queries and model | 25 | Closes flagged; channel through the line; policy grouped; relationships; descriptions | One convention missing |
| Profiles and links | 20 | Entire data set; every link tested; exceptions recorded | First rows, or no links |
| Validation and Tests | 25 | Totals agree; materials tied to `1045`; Tests 1 and 2 | Totals without the tie |
| Data Through | 20 | Measure correct; payroll and last posting explained | Correct date, no reason |
| About page | 10 | Purpose, sources, period, definitions | Missing definitions |

## Extensions and discussion questions

- Add a test that every working-capital measure is blank before a full twelve months, and say where it belongs in the Tests tab.
- Extend Data Through to the payroll documents and say what the report would then hide.
