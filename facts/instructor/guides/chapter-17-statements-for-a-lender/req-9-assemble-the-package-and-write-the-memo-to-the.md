---
note: ch17.r9
uses: [ch17.g9]
title: Assemble the package and write the memo to the CFO (Chapter 8)
kind: requirement
number: '9'
unit: '17'
perspective: general
tool: excel
minutes: 120
solution: "Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheet Memo (the matters with live numbers and the model memo) and the Statements and Notes worksheets that the PDF prints; Chapter17-capstone-sql.zip: LenderPackage.sql, the three queries headed Requirement 9"
figures:
  - id: IF-17-9-A
    kind: diagram
    purpose: The memo and its appendix at a glance, so students see what goes where before they write.
    shows: "Two page outlines and an appendix strip. Page one: header, an opening that holds the recommendation, and a table of the four required matters with four columns. Page two: the other matters, the passed items, the close changes and the closing recommendation. Under them, three exhibits of one page each: the schedule of adjustments, the matters' numbers and the going-concern conditions."
    data: none; the layout follows the requirement's page limits and its outline.
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = ch17_g9 %}
# Requirement 9: Assemble the package and write the memo to the CFO (Chapter 8)

{{ header() }}

## Purpose and learning outcomes

This requirement decides whether the work is usable. The memo is what the CFO reads before choosing whether the package leaves the company, so it must measure only what the ledger supports, describe rather than accuse, and end in a recommendation. The PDF is the product of the earlier requirements; the Memo worksheet keeps every number in the memo live. The analytics type is prescriptive, resting on descriptive evidence.

Students can assemble the package as a PDF from the workbook (Part 1), tabulate each open matter with what the records show, the evidence that would settle it, its possible effect and the treatment (Part 2), write a two-page memo with a three-page appendix that ends in a recommendation (Part 3), and screen it for wording and length (Part 4).

**Competencies practiced.** CPA Evolution Core S1 M8 T5 to T6 (visualization and communicating results); IMA Leadership (communication skills); IFAC IES 3 (b) (interpersonal and communication skills); AACSB A5 part 5.2 (technology judgment, interpretation, and communication).

## Before you assign

- **Files.** The workbook with Requirements 1 to 8 done and `LenderPackage.sql`. The Review file's Questions table holds {{ g.questions|length }} questions that this requirement answers (the tax status, the leases, the sales tax, the interest income and the opening balances).
- **Data conditions.** No income tax account exists; rent is paid straight from cash on the first weekday of each month while `2120` and `1140` are unused; `2050` is credited only by invoices and debited only by credit memos; the opening entry's lines to `1020`, `1050`, `2010`, `2030` and `2040` have not moved, and its inventory lines (`1040`, `1045`) have no item detail; `7010` is unused.
- **Verify first.** The Requirement 9 Checks agree, so the Memo worksheet's numbers can be trusted.

## How to run it

Individual work, because the memo is one voice; pairs can build the matters table together. About 120 minutes: 20 for the PDF, 25 for the matters table, 55 for the memo, 10 for the appendix, 10 to edit. Plan C of the case notes drafts from the Requirement 9 outline in Part 3 and swaps drafts against the Requirement 9 grading guide below. Hold back the four-part table until students have a first draft of their own. **Collect** the PDF, the memo with its appendix and the Memo worksheet.

{{ figure('IF-17-9-A') }}

## Step-by-step solution

### Part 1: Assemble the package as a PDF

**Step 1. Print the statements and notes from the workbook.** Order the pages: the four statements, then the notes on property and equipment, notes payable, revenue and accrued liabilities, and the note on the correction of {{ d.P }}. Put the date through which the data run (from the Documentation worksheet) and the word Draft on the first page. On each worksheet that prints, select the statement or note block and choose **Page Layout > Print Area > Set Print Area**, set the orientation, scale it to fit one page wide, and set **Print Titles** for a block that runs over a page. Then use **File > Export > Create PDF/XPS** and read every page for clipped text, print too small to read, a missing draft mark or tax warning, and blank pages. The model workbook sets no print areas and the solution holds no PDF, so compare a student's PDF with the Statements and Notes worksheets.

**Check:** the figures in the PDF equal the Statements and Notes worksheets, and every check cell of Requirements 6 and 7 is zero at the moment of printing. **Watch for:** a PDF printed from a stale refresh, or without the date and the draft mark: the package is a draft until the CFO releases it.

### Part 2: The matters table

**Step 2. Build the Memo worksheet's table.** One row for each measurable matter, with the value read from the workbook, not typed. The model's formulas for the tax screen, the credit memos' debits to `2050` and the equity effect of the opening balances:

```jinja
{{ g.f.provision }}
{{ g.f.memo_debits }}
{{ g.f.equity }}
```

**Check:** a tax screen of about ${{ provision|num(0) }}, {{ g.multiple|num(1) }} times materiality; rent paid from cash of ${{ rent[0]|money }}, ${{ rent[1]|money }} and ${{ rent[2]|money }}; sales tax payable ${{ stax|money }}, with debits only from credit memos (${{ memo_debits|money }}) and none from a remittance; opening balances that would lower assets by ${{ assets|money }} and liabilities by ${{ liabilities|money }}, raising equity by ${{ equity|money }}. **Watch for:** counting the payables alone as the equity effect: it is ${{ g.payables_only|money }} too high, because the opening assets and the other opening liabilities also fall.

### Part 3: The Requirement 9 outline

**Step 3. Write the memo in the order of the CFO's questions.** Open with what the package required and the recommendation: four adjustments and two reclassifications, income before income taxes of ${{ adj_ni|money }} for {{ d.C }}, {{ d.P }} presented as restated, no effect on cash. Then the four required matters, each in four parts:

| Matter | What the records show | Evidence that would settle it | Possible effect and treatment |
|---|---|---|---|
| Tax status | No income tax account; no tax recorded in {{ years }} years; equity is common stock with no distributions | Legal form or tax election, returns, payments | A screen of about ${{ provision|num(0) }} at the federal rate; state it, record no number; once settled, the note follows ASU 2023-09 |
| Leases | Rent paid from cash; `2120` and `1140` unused; no lessor among the suppliers | The agreements: term, options, escalation, discount rate | Right-of-use assets and lease liabilities would move the ratios; state it |
| Sales tax | ${{ stax|money }} payable, tax billed rather than collected; no remittance recorded | Returns, bank statements, the tax authority's account | Paid outside the ledger: liability and cash both overstated; unpaid: penalties and interest; do not conclude |
| Opening balances | Five lines, unchanged for {{ years }} years, payables equal to the opening cash | Suppliers' statements, confirmations, agreements | Equity ${{ equity|money }} higher if none of the five is real, a sensitivity and not an entry; keep them until evidence |

Then the other matters the records point to, briefly: cash (no interest income and no bank reconciliation: confirm the balance with the bank), inventories (a count and a net realizable value review; the opening inventories of ${{ o_inv|money }} with no item detail, evidence to request and not a write-off; standards unchanged since {{ d.F }}, so a cost study, with a rebuilt standard raising manufactured finished goods by about ${{ reval_c|num(0) }} at the end of {{ d.C }} and ${{ reval_p|num(0) }} a year earlier, a sensitivity and no entry), and Requirement 8's later events and going concern. Add the passed items for approval (two estimates and an exposure, a combined screen of ${{ g.passed|abs|money }}, {{ g.passed_share|pct(0) }} of materiality, not a measured misstatement), the changes to the year-end close (accrue payroll for days worked, review open accruals monthly, cut revenue off by delivery date, accrue interest monthly) and the recommendation: record A1, A2, A4, R1 and R2, A3 once the suppliers' evidence supports it and its period, and hold the package until every matter that could be material is settled or supported by a documented conclusion, with the notes completed and the CFO's approval.

**Check:** the opening and the recommendation can be read alone; each matter has four parts. The appendix of three pages holds the schedule of adjustments with the passed items, the matters' numbers and the going-concern conditions.

### Part 4: Screen the wording and the length

**Step 4. Read the draft as the CFO would.** Search it for words that assign intent, such as hidden, unpaid, kept and fraud, and rewrite each as what the records show. Count the pages: two for the memo, three for the appendix. The model memo runs {{ g.memo_words }} words in {{ g.memo_paragraphs }} paragraphs.

**Check:** every number traces to the Memo worksheet or a requirement's result. No new adjustment is booked for a matter the ledger cannot settle, and the recorded balances it cannot support stay as recorded, named in the memo and held for evidence.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Tax screen; as a multiple of materiality | about ${{ provision|num(0) }}; {{ g.multiple|num(1) }} | 2 |
| Sales tax payable; debits from remittances | ${{ stax|money }}; none | 2 |
| Equity effect if no opening balance is real | ${{ equity|money }} | 2 |
| Candidates to pass, their combined screen | {{ sm(g.passed) }} | 3 |

{{ expected() }}

## What a strong answer says

- **Opening.** What the package required, the effect on income and on {{ d.P }}, the fact that no adjustment moves cash, and the recommendation, in a paragraph.
- **Each matter.** What the records show, the evidence outside the database, the possible effect only where the ledger measures it, and a proposed treatment.
- **Wording.** "The records show no remittance" and never what anyone did with the money.
- **Ending.** Passed items for approval, the close changes, and a recommendation the CFO can act on: record some, hold one, do not release yet.

A weak answer opens with method, books a number for a matter the evidence cannot settle, or recommends release.

## Common mistakes and how to respond

- **A tax provision in the statements.** *Symptom:* income lower by about ${{ provision|num(0) }}, {{ g.multiple|num(1) }} times materiality. *Response:* ask what evidence the number rests on.
- **Payables alone as the equity effect.** *Symptom:* ${{ g.payables_only|money }} too high. *Response:* ask which opening lines are assets.
- **Intent in the wording.** *Symptom:* "the company kept the ${{ stax|money }}". *Response:* ask what the records show and what they cannot.
- **The revaluation as an entry.** *Symptom:* about ${{ reval_c|num(0) }} added to inventories. *Response:* ask what shows the old standards were an error.
- **Passed items left out.** *Symptom:* no list for approval. *Response:* ask how the CFO approves what is not listed.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Opening and recommendation | 20 | Readable alone, actionable, states the effect and the hold | Recommendation without reasons |
| The four required matters | 30 | Records, evidence, effect and treatment for each | Records only |
| Accuracy of numbers | 15 | Every number traces to the workbook | Numbers typed, one wrong |
| Wording | 10 | Describes, never accuses; no number for what cannot be measured | Intent implied |
| Passed items and close changes | 10 | Listed for approval; four close changes | One of the two |
| Package PDF, appendix and length | 15 | Dated draft, a memo of no more than two pages and an appendix of no more than three, the exhibits in the appendix | Over length |

## Extensions and discussion questions

- Rewrite the opening for the bank's relationship manager and list what must not appear in it.
- Add credit losses as a fifth matter, using the passed allowance.
- Discuss: when should a memo give a number for a matter the evidence cannot settle?
- Discuss: which matter would the bank want settled first, and why?
