---
note: ch17.r2
uses: [ch17.g2]
title: Review the recorded statements before adjusting them (Chapters 14 and 15)
kind: requirement
number: '2'
unit: '17'
perspective: financial
tool: powerbi
minutes: 150
solution: "Chapter17-capstone-pbi.zip: Charles River Lender Review.pbip, pages Review, Postings (the hidden drill-through), Sources, Questions and Validation, the Tests tab (Tests 1 and 2) and the Requirement 2 rows of the Checks tab; Chapter17-capstone-excel.zip: worksheet Review, which keeps the same results for the package"
figures:
  - id: IF-17-2-A
    kind: pbi-mock
    purpose: The Review page the model answer ends Part 2 with, the picture of a correct flagged list.
    shows: "Report view, page Review. A slicer titled Threshold (what-if) at the top left, a card titled Threshold and materiality, a matrix of statement lines and accounts with the three year-end balances, the change from the prior year to the current one and a Flag column, and a table of the changes above the threshold sorted by size. The flagged rows of the matrix read Above threshold."
    data: The Expected results quantities (materiality, the flagged accounts and their changes), read-only.
---
{% set g = ch17_g2 %}
# Requirement 2: Review the recorded statements before adjusting them (Chapters 14 and 15)

{{ header() }}

## Purpose and learning outcomes

The review turns the recorded statements into questions before any adjustment is made, and it fixes which later requirement answers each. A report with a ledger model suits it: the review moves from a statement line to its postings. The analytics types are descriptive (the balances and changes) and diagnostic (what rests on the opening entry).

Students can:

- build a ledger model and a Balance measure that leaves out only the closes dated on the as-of date (Part 1);
- flag the changes above the controller's materiality with a what-if parameter and drill through to their postings (Part 2);
- find the balances that rest on journal entries alone or have not moved since the opening entry (Part 3);
- record each question with the requirement that will answer it (Part 4).

**Competencies practiced.** CPA Evolution BAR M9 (financial statement analysis and working capital) and Core S1 M8 T5 to T6 (visualization and communicating results); IMA Reporting and Control (financial statement analysis); IFAC IES 2 (a) and IES 4 (a) (professional skepticism and professional judgment); AACSB A5 part 5.1 (technology integration: Power BI).

## Before you assign

- **Files.** Power BI Desktop at the release of Part IV (Windows only), CharlesRiver.xlsx, and the package workbook of Requirement 1, which the Review file reads for the statement lines. The model project's queries point at the folder the Downloads page names; students use Change Source, then refresh.
- **Data conditions.** GLEntry holds {{ g.gl_rows|count }} rows, so the first refresh is slow. The {{ g.n_closes }} closes post {{ g.close_rows }} rows. The opening entry has {{ g.opening_lines }} lines. The ledger runs past the last year-end, because supplier payments follow it.
- **Verify first.** After a refresh, the {{ g.n_checks }} Requirement 2 rows of the Checks tab in DAX query view all agree.

## How to run it

Individual or pairs, about 150 minutes: 45 for the model, 30 for Balance and the matrix, 25 for the threshold and flags, 20 for the drill-through, 20 for the sources, 10 for the questions. Hold back the Sources page until the Review page works. **Collect** the .pbix.

{{ figure('IF-17-2-A') }}

## Step-by-step solution

### Part 1: The ledger model and the Balance measure

**Step 1. Load the ledger star and flag the closes.** As in Tutorial 14.3:

a. Choose **Home > Get data > Excel workbook**, select the Tables for the ledger, the chart, the cost centers and the journal entries, and choose **Transform Data**.
b. In GLEntry, merge JournalEntry on VoucherNumber and EntryNumber (**Home > Merge Queries**) and expand EntryType.
c. Add IsYearEndClose with **Add Column > Custom Column**, then clear **Enable load** on JournalEntry.
d. Add the Date table of Tutorial 14.1, choose **Close & Apply**, and relate the Tables in **Model view**, many to one, **Single** direction.

```jinja
{{ g.m_gl }}
```

**Check:** GLEntry has {{ g.gl_rows|count }} rows and {{ g.close_rows }} are flagged, the {{ g.n_closes }} closes of Requirement 1.

**Step 2. Write Balance and test it against Requirement 1.** Choose **Modeling > New measure** and type the definition. A card or a matrix by year then reproduces each trial balance.

```dax jinja
{{ g.d_balance }}
```

**Check:** a table by year shows {{ g.rec_c.n }} accounts with postings at the last year-end and debit and credit balances of ${{ g.rec_c.debits|money }}, Requirement 1's figures. **Watch for:** a measure that leaves out every close (Tutorial 14.3's GL Amount). Balance sheet accounts other than retained earnings are right, but retained earnings lacks the earlier years' income and every revenue and expense account carries three years.

### Part 2: Flag the large changes

**Step 3. Bring in the statement lines.** Load the Working TB Table of the package workbook as a second source, filter out its totals row, and relate its account number to the chart's.

```jinja
{{ g.m_wt }}
```

**Check:** the matrix can group accounts by statement line. **Watch for:** the totals row. Power Query reads a Table's totals row as data, so a blank account number sits on the one side of the relationship and Desktop rejects it.

**Step 4. Measure the change and set the threshold.** Choose **Modeling > New parameter > Numeric range** for the threshold (the model's series is `{{ g.series }}`, with **Add slicer to this page**), and write the measures.

```dax jinja
{{ g.d_change }}

{{ g.d_mat }}

{{ g.d_flag }}
```

**Check:** the card titled "{{ g.t_card }}" shows materiality of ${{ mat_c|money }} for {{ d.C }} and ${{ mat_p|money }} for {{ d.P }}, and the threshold reads the {{ d.C }} figure until the slider moves.

**Step 5. Build the matrix and the flagged list.** On the Review page add the slicer ("{{ g.t_threshold }}", set to **Single select**), the matrix ("{{ g.t_matrix }}") with the year-end balances, the change and Flag, and a table ("{{ g.t_above }}") filtered to the measure `Is Above Threshold` with its filter card, sorted by absolute change.

**Check:** the report flags {{ g.n_right }} accounts and retained earnings: {{ g.flag_text }}. Retained earnings moves by ${{ g.re_change|money }}, the {{ d.P }} net income closed into it. **Watch for:** four wrong versions.

- Leaving out every close flags {{ g.n_every }} accounts besides retained earnings: each revenue and expense account's change becomes the whole year's activity.
- Leaving every close in drops {{ g.lost_text }}, and the list has {{ g.n_closed }} accounts: every revenue and expense account is zero at both year-ends.
- Testing the signed change against the threshold flags only {{ g.signed_text }}, and misses {{ g.missed_text }}. Use the absolute change.
- A balance at the ledger's last date is not a year-end balance: cash reads ${{ g.cash_last|money }} against ${{ g.cash_ye|money }}, and accounts payable ${{ g.ap_last|money }} against ${{ g.ap_ye|money }}, because supplier payments of ${{ g.after|money }} follow the year.

### Part 3: Drill through and the sources

**Step 6. Drill through to the postings.** Add a page Postings with the account label as its drill-through field (the **Drillthrough** section of the **Visualizations** pane), cards for the balances, a matrix of activity by SourceDocumentType and year ("{{ g.t_by_source }}"), and a table of the postings of {{ d.C }} ("{{ g.t_list }}"). Right-click a flagged account and choose **Drillthrough** > **Postings**.

**Check:** from the largest change, the postings show the source documents behind it and each posting's voucher number. Put a unique key in the posting table, or identical postings merge into one row.

**Step 7. Find the balances that rest on the opening entry.** Add a Sources page with a matrix of the balance sheet accounts by SourceDocumentType ("{{ g.t_source }}"), a table of the opening entry's lines ("{{ g.t_opening }}") and a list of the accounts posted by journal entries alone ("{{ g.t_journal }}").

```dax jinja
{{ g.d_open }}

{{ g.d_je }}
```

**Check:** the opening entry has {{ g.opening_lines }} lines. Balances unchanged since it: {{ g.unmoved_text }}; all but the payroll account carry a single posting. Accounts posted by journal entries alone: {{ g.only_je_text }}; the property and debt records support the equipment and the notes. **Watch for:** counting postings. The payroll account has {{ g.posts_2030|count }} postings, yet none moved the balance, because every payroll posting to it nets to zero.

### Part 4: The Questions table

**Step 8. Record the questions.** Use **Home > Enter data** for a Questions table (number, question, accounts, requirement) and show it on a Questions page.

**Check:** {{ g.n_questions }} questions, each naming the later requirement that answers it ({{ g.q_text }}).

**Instructor check.** In **DAX query view**, run this and compare it with the Expected results.

```dax jinja
{{ g.dax_check }}
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Materiality, {{ d.C }}; {{ d.P }} | ${{ mat_c|money }}; ${{ mat_p|money }} | 4 |
| Accounts flagged, retained earnings included | {{ g.n_right + 1 }} | 5 |
| Largest change, {{ above[0].n }} | ${{ above[0].v|money }} | 5 |
| Cash at the last year-end; at the ledger's last date | ${{ g.cash_ye|money }}; ${{ g.cash_last|money }} | 5 |
| Opening entry; its lines | {{ entry }}; {{ lines }} | 7 |
| Opening lines with no document: prepaid; payroll; payables | ${{ prepaid|money }}; ${{ payroll|money }}; ${{ payable|money }} | 7 |
| Growth of the accrued expenses account in {{ d.C }} | ${{ grew|money }} | 8 |

{{ expected() }}

## What a strong answer says

- **The flags.** Materiality as the controller set it, an absolute test, and the flagged accounts read as questions: inventories and sales tax, cash, payables and the movement in cost of goods sold and its variance.
- **The sources.** Which balances rest on journal entries alone, which have not moved since the opening entry, and which opening lines have no document.
- **The questions.** Each tied to the requirement that will answer it, including those the ledger cannot settle.

A weak answer lists the flagged accounts and stops, or records questions with no requirement.

## Common mistakes and how to respond

- **Every close left out.** *Symptom:* {{ g.n_every }} accounts flagged. *Response:* ask what a revenue account's change means after the prior close.
- **Closes left in.** *Symptom:* only {{ g.n_closed }} accounts flagged and none from the income statement. *Response:* ask what the close does on the as-of date itself.
- **The signed change.** *Symptom:* cash and the credit-balance accounts missing. *Response:* ask which direction a fall in cash and a rise in a liability take in debits less credits.
- **The ledger's last date.** *Symptom:* cash of ${{ g.cash_last|money }}. *Response:* ask what posts after the year-end.
- **Counting postings.** *Symptom:* the payroll account called a live balance. *Response:* ask what the postings added up to.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Model and Balance | 25 | Star, closes flagged, Balance leaves out only the close on the as-of date, totals agree with Requirement 1 | Model without a test against Requirement 1 |
| Review page | 25 | Matrix by line and account, what-if threshold at materiality, absolute flag, correct list | Fixed threshold, or signed test |
| Drill-through | 15 | Page reached from a flagged account, with sources and postings | Page not wired to the account |
| Sources analysis | 15 | Opening-entry lines, unmoved balances and journal-only accounts found | One list only |
| Questions table | 20 | All questions entered, each with its requirement | Questions without requirements |

## Extensions and discussion questions

- Move the slider to the largest step below the change in account `{{ following[0].n }}`, ${{ following[0].v|money }}, and say which account enters the list.
- Add a card that counts the accounts whose balance moved only by journal entries in the year, and say what such a measure would catch in another company.
- Discuss: the review flagged retained earnings. Is that a question or an explanation?
- Discuss: why does the case build the Review file before any adjustment, not after?
