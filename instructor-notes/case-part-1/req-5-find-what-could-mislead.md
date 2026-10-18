# Requirement 5: Find what could mislead (Auditing)

| | |
|---|---|
| Unit | Case Part 1: Getting the Data Ready for the Furniture Margin Question |
| Item | Requirement 5 |
| Perspective | Auditing |
| Tools | Workbook browsing and written work |
| Time | About 45 minutes |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 5 is the case's audit moment. The data ties to the ledger, the quarters are right, and the margin can still be wrong, because the quarter ends on the day the books are closed. The lesson is not about one entry. It is the habit of reading the totals behind a percentage before believing it, and of tracing an odd total to its source document type and its entry type.

By the end, students can:

- compute a margin from all rows of two ledger accounts, and notice when the totals behind it make no sense;
- trace an odd total to a source document type, a voucher and an EntryType;
- explain why the entry does not belong in a quarterly measure, exclude it by a rule, and recompute the margins.

**Competencies practiced.** CPA Evolution Core S1 M8 T3 to T4 (data mining and analysis of financial data); IMA Data Literacy and Data Analysis within Data Analytics and Insights; IFAC IES 4 (a), professional skepticism and professional judgment; AACSB A5 part 5.2. The analytics type is descriptive, applied with an auditor's skepticism.

## Before you assign

- Students need Requirement 4's PivotTable skills, Tutorial 2.2 (Step 6, the last fiscal year's rows by source document type), Tutorial 3.2 (the trace) and the controller's reminder in the case about the quarter's end.
- The requirement relies on these conditions: the third quarter has no journal entry on either Furniture account; the fourth has one close that debits revenue and credits cost by the year's balances; each fiscal year has two closes, only one of which touches the Furniture accounts; and the closes are the only journal entries on those accounts.
- Do not tell students what the entry is. They find it. If they ask for a hint, point them at the source document types in the fourth quarter.

## How to run it

Individual work, 45 minutes: 10 for the all-rows margin, 15 for finding the entry, 10 for the exclusion and the recompute and 10 for the statement. In Plan A it is debriefed live (see the case note); show the PivotTable of Step 2 on the projector and ask what a negative revenue means before anyone says what the entry is. **Collect** the all-rows table, the name and EntryType of the entry, and the corrected margins.

## Step-by-step solution

### Phase 1: The margin from all rows

**Step 1. Total the two accounts with no filter on source document type.** Build the GLEntry PivotTable of Requirement 4 for AccountID 42 and then 50, for the three periods of each quarter, with Sum of Debit and Sum of Credit in **Values** and no filter on SourceDocumentType. Revenue is credits less debits; cost is debits less credits. The margin is:

```
=(Revenue - COGS) / Revenue
```

| Quarter | Revenue (4010) | Cost of goods sold (5010) | Margin |
|---|---:|---:|---:|
| 2026 Q3 | $4,283,322.86 | $2,427,252.91 | 43.3% |
| 2026 Q4 | -$13,241,499.72 | -$7,496,777.60 | 43.4% |

**Check:** the margin of 2026 Q4 is almost identical to the margin of 2026 Q3, so the ratio shows no decline. The totals behind it are negative in 2026 Q4: a revenue below zero is not a quarter's sales. **Watch for:** students who stop at the percentage, and who reverse the signs so that revenue reads positive and the trap disappears.

### Phase 2: Find the entry

**Step 2. Open up the fourth quarter.** In the revenue PivotTable for 2026 Q4, put SourceDocumentType in **Rows**. Two rows appear.

![A mock of the PivotTable that shows what sits behind the naive fourth-quarter revenue.](../figures/case-part-1/IF-C1-5-A.pdf)

| Source document type | Rows | Debit | Credit |
|---|---:|---:|---:|
| JournalEntry | 1 | $17,398,287.56 | $0.00 |
| SalesInvoice | 864 | $0.00 | $4,156,787.84 |

**Check:** SalesInvoice holds the quarter's sales, and a single JournalEntry row holds a debit of $17,398,287.56, several times the quarter's invoicing. The cost account shows the same pattern, with a credit of $9,946,838.67.

**Step 3. Name the entry.** Add VoucherNumber under JournalEntry: the voucher is JE-2026-000296. Its two Furniture rows read:

- 4010: Close Sales Revenue - Furniture, debit $17,398,287.56, credit $0.00
- 5010: Close COGS - Furniture, debit $0.00, credit $9,946,838.67

Then open the JournalEntry worksheet and filter EntryNumber for JE-2026-000296.

**Check:** the EntryType is "Year-End Close - P&L to Income Summary", posted on 2026-12-31, the last day of the fiscal year. **Watch for:** students who report the other close, which has a similar number and an EntryType that begins the same way. Its EntryType is the second of the year's two, and it posts to the income summary and retained earnings, not to a Furniture account.

### Phase 3: Explain it, exclude it, recompute

**Step 4. Explain why it does not belong.** A year-end close transfers the year's revenue and expense balances to an income summary so that the accounts start the next year at zero. It is not a sale or a cost. Here it debits 4010 by $17,398,287.56, which is the account's whole balance for fiscal 2026 before the close, and credits 5010 by $9,946,838.67, the cost's whole balance. Both are a year's totals, not a quarter's, and they sit in the last quarter because the entry is dated on its last day. The close is a legitimate entry; it is the quarterly measure that must leave it out. The fiscal years of the extract each have two:

| Entry | Posted | EntryType |
|---|---|---|
| JE-2024-000265 | 2024-12-31 | Year-End Close - P&L to Income Summary |
| JE-2024-000266 | 2024-12-31 | Year-End Close - Income Summary to Retained Earnings |
| JE-2025-000287 | 2025-12-31 | Year-End Close - P&L to Income Summary |
| JE-2025-000288 | 2025-12-31 | Year-End Close - Income Summary to Retained Earnings |
| JE-2026-000296 | 2026-12-31 | Year-End Close - P&L to Income Summary |
| JE-2026-000297 | 2026-12-31 | Year-End Close - Income Summary to Retained Earnings |

**Step 5. Exclude it by a rule.** In the PivotTable, clear JournalEntry in the SourceDocumentType filter, or exclude the voucher JE-2026-000296. The principled rule is by entry type: leave out entries whose EntryType begins "Year-End Close". Here either gives the same rows, because the closes are the only journal entries on the two Furniture accounts. A ledger with adjusting entries would need the EntryType rule, and the model answer says so.

**Step 6. Recompute both margins.**

| Quarter | Revenue (invoices) | Cost (shipments less returns) | Margin |
|---|---:|---:|---:|
| 2026 Q3 | $4,283,322.86 | $2,427,252.91 | 43.33% |
| 2026 Q4 | $4,156,787.84 | $2,450,061.07 | 41.06% |

A cross-check from the sub-ledger at standard cost: add a helper column in SalesInvoiceLine (the first free column after Requirement 4's, S) with the line's cost, and total it as in Requirement 4.

```
=SalesInvoiceLine!G2*XLOOKUP(F2, Item!A:A, Item!F:F)
```

The margin at standard cost is 42.26% in 2026 Q3 and 40.78% in 2026 Q4.

![The naive and the corrected Furniture margin for the two quarters, side by side.](../figures/case-part-1/IF-C1-5-B.pdf)

**Step 7. State what the margins show.** On this measure the Furniture margin fell from 43.33% to 41.06%, a drop of 2.27 points. Revenue fell 3.0% from 2026 Q3 to 2026 Q4 while cost rose 0.9%. The measure takes revenue before customer credits, which post to a shared account, and cost after the returned goods, so it overstates the margin, and a model answer says so. The cross-check at standard cost also falls, by 1.48 points, but it is a separate measure (the invoice lines before returns), so it supports the direction of the change, not the level. For reference, the invoice lines at standard cost come to $2,473,065.77 in 2026 Q3 and $2,461,576.82 in 2026 Q4, against posted shipment cost net of cost returns of $2,427,252.91 and $2,450,061.07. The gaps, $45,812.86 and $11,515.75, are differences between the two definitions (invoice and shipment timing, unmatched shipments, returns), not errors in the four tie-outs. That is the descriptive answer. Why it fell is the Part II question.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Naive revenue and cost, 2026 Q4 | -$13,241,499.72; -$7,496,777.60 | Step 1 |
| Naive margin, 2026 Q4; 2026 Q3 | 43.4%; 43.3% | Step 1 |
| The entry; its EntryType; its posting date | JE-2026-000296; Year-End Close - P&L to Income Summary; 2026-12-31 | Step 3 |
| Close: debit to 4010; credit to 5010 | $17,398,287.56; $9,946,838.67 | Step 3 |
| Corrected revenue and cost, 2026 Q4 | $4,156,787.84; $2,450,061.07 | Step 6 |
| Corrected margin, 2026 Q3; 2026 Q4 | 43.3%; 41.1% | Step 6 |
| Margin at standard cost, 2026 Q3; 2026 Q4 | 42.3%; 40.8% | Step 6 |

> **Instructor notes, Requirement 5:** using all rows, Q4 Furniture revenue is -\$13,241,499.72 and COGS is -\$7,496,777.60, because year-end close JE-2026-000296 (EntryType "Year-End Close - P&L to Income Summary", posted 2026-12-31) debits 4010 by \$17,398,287.56 and credits 5010 by \$9,946,838.67. The naive margin percentage is 43.4%, almost identical to Q3's 43.3%, so the ratio alone hides both the nonsense totals and the decline. Excluding the closing entry (SourceDocumentType JournalEntry with a Year-End Close EntryType), Q4 revenue is \$4,156,787.84 and COGS \$2,450,061.07 (shipments less returns), and the margin falls from 43.3% in Q3 to 41.1% in Q4. This measure takes revenue before customer credits (the shared returns account) and cost net of the returned goods, so it overstates the Furniture margin. Taking the Furniture credit memo lines, traced through SourceLineID, off revenue gives 42.6% and 40.5%, and the fall remains. A separate measure from the invoice lines at standard cost (invoiced quantity x Item.StandardCost, before returns) also falls, from 42.3% to 40.8%. Its population differs, so it supports the direction of the change, not the level.

## What a strong answer says

- **The trap.** Using all rows gives a 2026 Q4 margin of 43.4%, almost identical to the 2026 Q3 figure, on negative totals; the percentage hides both the nonsense and the decline.
- **The entry.** JE-2026-000296, a journal entry of EntryType "Year-End Close - P&L to Income Summary", posted on the last day of the year, debiting revenue and crediting cost by the year's balances.
- **The reason.** It is a bookkeeping transfer, not a transaction of the quarter, so it must be excluded from a quarterly margin; the exclusion rule is stated.
- **The result.** 43.3% to 41.1%, a fall on the stated basis (revenue before customer credits, cost after returned goods). The invoice-line view at standard cost falls too.

A weak answer reports the naive percentage as the result, removes one side of the close only, or drops the entry without saying why.

## Common mistakes and how to respond

- **Stopping at the ratio.** *Symptom:* "the margin rose slightly". *Response:* ask them to read the revenue and cost totals aloud.
- **Sign reversed.** *Symptom:* a 2026 Q4 revenue of $13,241,499.72, positive, because the signs were flipped. *Response:* ask which side of the ledger revenue sits on.
- **Only one side of the close removed.** *Symptom:* a margin far from either quarter. *Response:* ask whether the close posts to one account or two.
- **The wrong close.** *Symptom:* the second close of the year named. *Response:* ask which of the two posts to a Furniture account.
- **A blanket exclusion.** *Symptom:* "drop all journal entries". *Response:* ask what would happen to an accrual or an adjusting entry on the same account.
- **A fix of the ledger.** *Symptom:* "correct the entry". *Response:* the entry is right; the measure is what needs the exclusion.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| The all-rows margins and the totals behind them | 25 | Both percentages, the negative totals and a comment on them | Percentages only |
| The entry and its EntryType | 25 | The voucher, the source document type, the EntryType and the date | The entry without its EntryType |
| Why it is excluded | 20 | A bookkeeping transfer of the year's balances, not an operating transaction; a stated rule | "It is too large" |
| The corrected margins and what they show | 30 | Both margins, the decline in points and the descriptive statement | Margins without the statement, or an error of one side |

## Extensions and discussion questions

- Net the revenue side of returns. The Furniture credit memo lines were $55,437.94 in 2026 Q3 and $39,719.44 in 2026 Q4. The margin is then 42.59% and 40.49%. Does the fall survive?
- As a hypothetical sensitivity only, add the order-price amount of the Furniture shipment lines of 2026 Q4 with no invoice line ($34,792.96) to 2026 Q4 revenue, leaving their recorded cost as it is. The margin would be 41.55%, still below 2026 Q3. The calculation does not establish whether the revenue belongs in 2026 Q4. What order, shipment, delivery and billing evidence would you obtain to tell a timing difference from an omission or an item to correct?
- Discuss: which test of Chapter 2's checklist, if any, would have flagged this before the margin was computed?
