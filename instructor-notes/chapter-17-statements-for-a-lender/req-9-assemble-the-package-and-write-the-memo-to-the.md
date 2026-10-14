# Requirement 9: Assemble the package and write the memo to the CFO (Chapter 8)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 9 |
| Tools | Excel |
| Time | About 120 minutes |
| Solution file | Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheet Memo (the matters with live numbers and the model memo) and the Statements and Notes worksheets that the PDF prints; Chapter17-capstone-sql.zip: LenderPackage.sql, the three queries headed Requirement 9 |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This requirement decides whether the work is usable. The memo is what the CFO reads before choosing whether the package leaves the company, so it must measure only what the ledger supports, describe rather than accuse, and end in a recommendation. The PDF is the product of the earlier requirements; the Memo worksheet keeps every number in the memo live. The analytics type is prescriptive, resting on descriptive evidence.

Students can assemble the package as a PDF from the workbook (Part 1), tabulate each open matter with what the records show, the evidence that would settle it, its possible effect and the treatment (Part 2), write a two-page memo with a three-page appendix that ends in a recommendation (Part 3), and screen it for wording and length (Part 4).

**Competencies practiced.** CPA Evolution Core S1 M8 T5 to T6 (visualization and communicating results); IMA Leadership (communication skills); IFAC IES 3 (b) (interpersonal and communication skills); AACSB A5 parts 5.2 and 5.3 (technology judgment, interpretation, and communication; learning to learn).

## Before you assign

- **Files.** The workbook with Requirements 1 to 8 done and `LenderPackage.sql`. The Review file's Questions table holds 5 questions that this requirement answers (the tax status, the leases, the sales tax, the interest income and the opening balances).
- **Data conditions.** No income tax account exists; rent is paid straight from cash on the first weekday of each month while `2120` and `1140` are unused; `2050` is credited only by invoices and debited only by credit memos; the opening entry's lines to `1020`, `1050`, `2010`, `2030` and `2040` have not moved; `7010` is unused.
- **Verify first.** The Requirement 9 Checks agree, so the Memo worksheet's numbers can be trusted.

## How to run it

Individual work, because the memo is one voice; pairs can build the matters table together. About 120 minutes: 20 for the PDF, 25 for the matters table, 55 for the memo, 10 for the appendix, 10 to edit. Plan C of the case notes drafts from the Requirement 9 outline in Part 3 and swaps drafts against the Requirement 9 grading guide below. Hold back the four-part table until students have a first draft of their own. **Collect** the PDF, the memo with its appendix and the Memo worksheet.

![The memo and its appendix at a glance, so students see what goes where before they write.](../figures/chapter-17-statements-for-a-lender/IF-17-9-A.pdf)

## Step-by-step solution

### Part 1: Assemble the package as a PDF

**Step 1. Print the statements and notes from the workbook.** Order the pages: the four statements, then the notes on property and equipment, notes payable, revenue and accrued liabilities, and the note on the correction of 2025. Put the date through which the data run (from the Documentation worksheet) and the word Draft on the first page, set the print areas and page breaks, and use Excel's own export to PDF.

**Check:** the figures in the PDF equal the Statements and Notes worksheets, and every check cell of Requirements 6 and 7 is zero at the moment of printing. **Watch for:** a PDF printed from a stale refresh, or without the date and the draft mark: the package is a draft until the CFO releases it.

### Part 2: The matters table

**Step 2. Build the Memo worksheet's table.** One row for each measurable matter, with the value read from the workbook, not typed. The model's formulas for the tax screen, the credit memos' debits to `2050` and the equity effect of the opening balances:

```
=ROUND(C5*0.21,-4)
=SUMIFS(LedgerSummary[Debit],LedgerSummary[AccountNumber],2050,LedgerSummary[SourceDocumentType],"CreditMemo",LedgerSummary[Year],"<="&2026)
=C22-C21
```

**Check:** a tax screen of about $960,000, 4.3 times materiality; rent paid from cash of $467,525.63, $484,969.91 and $504,245.32; sales tax payable $5,620,840.66, with debits only from credit memos ($38,587.80) and none from a remittance; opening balances that would lower assets by $440,000.00 and liabilities by $2,276,371.12, raising equity by $1,836,371.12. **Watch for:** counting the payables alone as the equity effect: it is $260,000.00 too high, because the opening assets and the other opening liabilities also fall.

### Part 3: The Requirement 9 outline

**Step 3. Write the memo in the order of the CFO's questions.** Open with what the package required and the recommendation: four adjustments and two reclassifications, income before income taxes of $4,572,087.08 for 2026, 2025 presented as restated, no effect on cash. Then the four required matters, each in four parts:

| Matter | What the records show | Evidence that would settle it | Possible effect and treatment |
|---|---|---|---|
| Tax status | No income tax account; no tax recorded in three years; equity is common stock with no distributions | Legal form or tax election, returns, payments | A screen of about $960,000 at the federal rate; state it, record no number |
| Leases | Rent paid from cash; `2120` and `1140` unused; no lessor among the suppliers | The agreements: term, options, escalation, discount rate | Right-of-use assets and lease liabilities would move the ratios; state it |
| Sales tax | $5,620,840.66 payable; no remittance recorded | Returns, bank statements, the tax authority's account | Paid outside the ledger: liability and cash both overstated; unpaid: penalties and interest; do not conclude |
| Opening balances | Five lines, unchanged for three years, payables equal to the opening cash | Suppliers' statements, confirmations, agreements | Equity $1,836,371.12 higher if none is real; keep them until evidence |

Then the other matters the records point to, briefly: cash (no interest income and no bank reconciliation: confirm the balance with the bank), inventories (a count and a net realizable value review; standards unchanged since 2024, so a cost study, with a rebuilt standard raising manufactured finished goods by about $471,000 at the end of 2026 and $370,000 a year earlier, a sensitivity and no entry), and Requirement 8's later events and going concern. Add the passed items for approval ($102,025.38 in aggregate, 45% of materiality), the changes to the year-end close (accrue payroll for days worked, review open accruals monthly, cut revenue off by delivery date, accrue interest monthly) and the recommendation: record A1, A2, A4, R1 and R2, A3 once the suppliers' evidence supports it, and do not release the package until the first four matters are settled.

**Check:** the opening and the recommendation can be read alone; each matter has four parts. The appendix of three pages holds the schedule of adjustments with the passed items, the matters' numbers and the going-concern conditions.

### Part 4: Screen the wording and the length

**Step 4. Read the draft as the CFO would.** Search it for words that assign intent, such as hidden, unpaid, kept and fraud, and rewrite each as what the records show. Count the pages: two for the memo, three for the appendix. The model memo runs 692 words in 10 paragraphs.

**Check:** every number traces to the Memo worksheet or a requirement's result; no matter the ledger cannot settle carries a number in the statements.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Tax screen; as a multiple of materiality | about $960,000; 4.3 | 2 |
| Sales tax payable; debits from remittances | $5,620,840.66; none | 2 |
| Equity effect if no opening balance is real | $1,836,371.12 | 2 |
| Passed items in aggregate | -$102,025.38 | 3 |

> **Instructor notes, Requirement 9:** (1) Tax status (ASC Topic 740): no tax account and no tax recorded in three years; equity is common stock with no distributions. Evidence: the entity's legal form or tax election, its returns, and its payments. If it is a C corporation, a provision could be several times materiality: 21% federal on 4,572,087.08, a magnitude screen that measures neither taxable income nor state or deferred taxes, is about 960,000 (950,000 with the old accruals kept), so state the matter and record no number. (2) Leases (ASC Topic 842): office and warehouse rent is paid on the first weekday of each month straight from cash (467,525.63 / 484,969.91 / 504,245.32), in amounts that vary slightly from month to month; 2120 Lease Liability is unused (1140 Leasehold Improvements, also unused, holds improvements to leased space, not a right-of-use asset) and no lessor appears among the suppliers. Evidence: the agreements (term, options, escalation, discount rate). Likely effect: right-of-use assets and lease liabilities, which would move the bank's ratios. (3) Sales tax: 5,620,840.66 recorded as payable on invoicing, with no remittance recorded (2050 credits only from invoices, debits only from credit memos, 38,587.80); whether it was collected is a question for the receipts. Evidence: the returns, the bank statements, the tax authority's account. If it was paid from company cash outside the ledger, the liability and cash are both overstated; if it was not paid, penalties and interest may be owed (ASC Topic 450); a payment by anyone else would need a different entry. (4) Opening balances: receivables 380,000.00, prepaid 60,000.00, payables 2,096,371.12 (equal to opening cash to the cent), accrued payroll 95,000.00, accrued expenses 85,000.00, all unchanged in three years; if none is real, equity rises by 1,836,371.12 (assets -440,000.00, liabilities -2,276,371.12); if the payables are real, the records show them unpaid for three years, and the suppliers' statements would give their terms and due dates. (5) Cash: no interest income and no bank reconciliation in the records; confirm the balance with the bank. (6) Inventories (ASC Topic 330): a physical count and a net realizable value review are needed; stock by item cannot be rebuilt because the opening inventory has no item detail. Whether standards unchanged since 2024 still approximate cost on normal capacity needs a cost study; at a standard rebuilt on normal capacity, manufactured finished goods would be about 471,000 higher at the end of 2026 and 370,000 higher at the end of 2025, so a strong memo names it and recommends the study. (7) Subsequent events and going concern, as in Requirement 8. (8) Passed items P1-P3, for approval. Recommendation: record A1, A2, A4, R1, and R2, record A3 once the suppliers' evidence supports it (or keep the old accruals), and do not release the package until items 1 to 4 are settled. Close-process changes: a year-end payroll accrual, a monthly review of open accruals that confirms with the supplier any past the invoicing window, revenue cutoff by delivery date, and an interest accrual.

## What a strong answer says

- **Opening.** What the package required, the effect on income and on 2025, the fact that no adjustment moves cash, and the recommendation, in a paragraph.
- **Each matter.** What the records show, the evidence outside the database, the possible effect only where the ledger measures it, and a proposed treatment.
- **Wording.** "The records show no remittance" and never what anyone did with the money.
- **Ending.** Passed items for approval, the close changes, and a recommendation the CFO can act on: record some, hold one, do not release yet.

A weak answer opens with method, books a number for a matter the evidence cannot settle, or recommends release.

## Common mistakes and how to respond

- **A tax provision in the statements.** *Symptom:* income lower by about $960,000, 4.3 times materiality. *Response:* ask what evidence the number rests on.
- **Payables alone as the equity effect.** *Symptom:* $260,000.00 too high. *Response:* ask which opening lines are assets.
- **Intent in the wording.** *Symptom:* "the company kept the $5,620,840.66". *Response:* ask what the records show and what they cannot.
- **The revaluation as an entry.** *Symptom:* about $471,000 added to inventories. *Response:* ask what shows the old standards were an error.
- **Passed items left out.** *Symptom:* no list for approval. *Response:* ask how the CFO approves what is not listed.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Opening and recommendation | 20 | Readable alone, actionable, states the effect and the hold | Recommendation without reasons |
| The four required matters | 30 | Records, evidence, effect and treatment for each | Records only |
| Accuracy of numbers | 15 | Every number traces to the workbook | Numbers typed, one wrong |
| Wording | 10 | Describes, never accuses; no number for what cannot be measured | Intent implied |
| Passed items and close changes | 10 | Listed for approval; four close changes | One of the two |
| Package PDF, appendix and length | 15 | Dated draft, two pages and three, appendix exhibits | Over length |

## Extensions and discussion questions

- Rewrite the opening for the bank's relationship manager and list what must not appear in it.
- Add credit losses as a fifth matter, using the passed allowance.
- Discuss: when should a memo give a number for a matter the evidence cannot settle?
- Discuss: which matter would the bank want settled first, and why?
