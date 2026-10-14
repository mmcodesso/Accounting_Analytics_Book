# Requirement 6: Write the data readiness memo

| | |
|---|---|
| Unit | Case Part 1: Getting the Data Ready for the Furniture Margin Question |
| Item | Requirement 6 |
| Tools | Workbook browsing and written work |
| Time | About 60 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Requirement 6 is where the case becomes a deliverable. The analysis of Requirements 2 to 5 is invisible to the controller until it is written for a reader who has little time. The memo has to do what the case title says: say whether the data is ready for the Furniture margin question, what it can and cannot support, and what to do next. It is also the one piece of professional writing in Part I, so it is graded as writing and as accounting.

By the end, students can:

- report readiness by perspective (financial reporting, managerial accounting, auditing) in one to two pages;
- state a margin measure precisely enough that someone else could reproduce it, and give what it shows;
- say what the evidence supports, name the limits, and end with a recommendation the controller can act on.

**Competencies practiced.** CPA Evolution Core S1 M8 T5 to T6 (visualization and communicating results); IMA Communication Skills within Leadership; IFAC IES 3 (b), interpersonal and communication skills; AACSB A5 part 5.2. The memo is written at the last stage of the workflow, for the readiness findings.

## Before you assign

- Students need the results of Requirements 2 to 5: the data map, the choice of quarters, the reconciliation table and the margins. Students who skipped one should not start the memo.
- The requirement relies on one condition that earlier steps established and that a student might forget to mention: the Furniture margin falls from the third to the fourth quarter of fiscal 2026 whichever way it is measured (from the ledger, or at standard cost from the invoice lines).
- Decide the length rule in advance. Two pages of 11-point text hold about 800 to 900 words with the header, so the model budget below keeps to about 700.

## How to run it

Individual work, 60 minutes: 10 to plan from the outline below, 35 to draft, 10 for the appendix and 5 to check against the slide "Before you submit". Hold back the outline until students have a first draft of the opening paragraph, then hand it out. Peer review works well: swap memos and read only the first paragraph, then say what you would do next. If you cannot say, the memo has failed its job. **Collect** the memo and the one-page appendix.

## Step-by-step solution

The model memo follows a fixed order, and its parts take these words:

| Part | Words | Draws on |
|---|---:|---|
| Header and opening paragraph (bottom line first) | 60 to 90 | Requirements 3, 5 |
| Financial reporting | 150 to 200 | Requirements 3, 4 |
| Managerial accounting | 150 to 220 | Requirements 2, 5 |
| Auditing | 150 to 220 | Requirements 2 to 5 |
| Recommendation | 60 to 100 | All |
| Appendix (one page) | A map and a table | Requirements 2, 4 |

### Phase 1: The opening

**Step 1. Write the bottom line first.** One paragraph. A model: the data can support a comparison of the Furniture gross margin of 2026 Q3 and 2026 Q4 once the year-end close (JE-2026-000296) is excluded; on that basis the margin fell from 43.33% to 41.06%, 2.27 points; the main limits are the revenue side of returns and the year-end cutoff; the recommendation is a diagnostic analysis in Part II.

**Check:** the paragraph answers "can I use this data, and for what?" before any detail. **Watch for:** an opening that says what the student did ("I examined the data") instead of what the controller needs.

![A page layout of the model memo and its appendix, with the word budget of each part.](../figures/case-part-1/IF-C1-6-A.pdf)

### Phase 2: Financial reporting

**Step 2. Report the reconciliation and the cutoff findings.** Model content:

- The Furniture invoice lines ($4,283,322.86 in 2026 Q3 and $4,156,787.84 in 2026 Q4) equal the sales invoice credits to account 4010 ($4,283,322.86 and $4,156,787.84), and the standard cost on the shipment lines equals the shipment postings to account 5010 in both quarters, to the cent.
- Agreement shows that the documents reached the ledger in full. It does not show that every sale was invoiced: 4 Furniture shipment lines of 2026 Q4 have no invoice line, $18,453.55 at standard cost.
- Of the 9 invoices dated before their first shipment, 3 hold Furniture lines; none is dated, shipped or posted in either quarter, so they do not touch this comparison. They matter for annual revenue and the year-end cutoff.

**Check:** a number is always followed by what it means for this quarter. **Watch for:** "the totals agree, so the data is reliable", and the cutoff finding presented as a defect of the margin.

### Phase 3: Managerial accounting

**Step 3. State the measure and what it shows.** Model content:

- The measure is revenue less cost of goods sold, over revenue, from the ledger: credits less debits on account 4010 and debits less credits on account 5010, including the postings of invoices, shipments and returns and excluding the year-end close; the quarters are 2026 Q3 and 2026 Q4, the latest two complete ones.
- It shows 43.33% falling to 41.06%. Revenue fell 3.0% while cost rose 0.9%. At standard cost, from the invoice lines, the margin falls from 42.26% to 40.78%, so the two views agree.
- For the diagnosis, the invoice lines already hold the fields it needs: ItemID, Quantity, BaseListPrice, UnitPrice, Discount, PromotionID, LineTotal, and the item master holds ItemCode, StandardCost, ListPrice.

**Check:** another analyst could reproduce the number from the memo's definition. **Watch for:** a margin given with no accounts, no quarters or no statement about the closing entry.

### Phase 4: Auditing

**Step 4. Give the evidence, the closing-entry problem and the limits.** Model content:

- Evidence for reliance: both reconciliations agree; every account number the ledger refers to exists in the chart; every posting names its document, so a number can be traced from the ledger back to its source.
- The closing-entry problem: all rows give a 2026 Q4 margin of 43.4%, a plausible percentage on negative totals, because JE-2026-000296 debits revenue and credits cost by the year's balances. The measure excludes it by entry type, so a later quarter-end that is also a year-end is handled the same way.
- Limits: the revenue side of returns posts to a shared account, so the margin is before it; the traced Furniture credit memo lines were $55,437.94 in 2026 Q3 and $39,719.44 in 2026 Q4, and netting them leaves the fall in place. The unbilled shipments are a cutoff question. A blank tracking number weakens the evidence that a shipment took place.

**Check:** the memo says what the data can support and what it cannot. **Watch for:** a limitation list with no consequence for the controller's decision.

### Phase 5: The recommendation and the appendix

**Step 5. End with the next analysis.** A model: perform the diagnostic analysis in Part II, decomposing the change between 2026 Q3 and 2026 Q4 into volume, mix, price and cost effects by product, from the invoice lines and the item master, using the measure above. First agree two treatments: whether to net the revenue side of returns, and whether to count the unbilled shipments. State the decision the controller needs to make.

**Step 6. Assemble the one-page appendix.** The data map of Requirement 2 and the reconciliation table of Requirement 4, on one page, readable on their own.

**Check:** the map names every key and cardinality; the table shows both sides and the difference for each quarter.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Margin, 2026 Q3; 2026 Q4 | 43.3%; 41.1% | Steps 1 and 3 |
| Fall in points | 2.27 | Step 1 |
| Margin at standard cost | 42.3%; 40.8% | Step 3 |
| Reconciliation differences | Zero in every cell | Step 2 |
| Furniture shipment lines with no invoice line, 2026 Q4 | 4 | Step 2 |
| Cutoff invoices; with Furniture lines | 9; 3 | Step 2 |

For the instructor only: what the Part II diagnosis will find, in outline. Units of Furniture invoiced barely change (7,091.2300000000005 to 7,122.12, 0.4%); the standard cost per unit is about the same ($348.75 to $345.62); the average price falls from $604.03 to $583.64 per unit (-3.4%), and the promotional discounts on Furniture lines more than double. A good memo does not claim this; it recommends the analysis that will.

## What a strong answer says

- **The opening.** The bottom line first: usable for this question, on the corrected measure, with the margin and its fall.
- **Financial reporting.** Reconciliation to the cent, what agreement does and does not show, and the cutoff findings with their meaning for this quarter.
- **Managerial accounting.** A measure defined by accounts, rows, exclusions and quarters; what it shows; and the data for Part II.
- **Auditing.** The evidence for reliance, the closing-entry problem and how it is avoided, and the limits, each with its consequence.
- **The recommendation.** The analysis to do next, the decisions to take first, and no claim about the cause.

A weak memo lists numbers without meaning, claims a cause, buries the closing entry, or runs past two pages.

## Common mistakes and how to respond

- **Too long.** *Symptom:* three pages, with working-paper detail. *Response:* move the tables to the appendix and keep one sentence per finding.
- **A cause claimed.** *Symptom:* "the margin fell because of promotions". *Response:* ask what evidence in the case supports it; the case has not decomposed the change.
- **Agreement as proof.** *Symptom:* "reliable" with no limit. *Response:* ask what an unbilled shipment does to the tie-out.
- **The closing entry in a footnote.** *Symptom:* mentioned last. *Response:* ask what the controller would have concluded from the naive margin.
- **IDs for numbers.** *Symptom:* AccountIDs in the memo. *Response:* the controller reads account numbers.
- **A vague recommendation.** *Symptom:* "analyze further". *Response:* ask who does what, with which data, to answer which question.
- **A missing appendix or map.** *Symptom:* a memo with no evidence page. *Response:* the appendix is part of the deliverable; ask where a reviewer finds a number's source.
- **Writing for the instructor.** *Symptom:* a tour of the steps. *Response:* ask what the reader needs to decide.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Structure and length | 15 | Bottom line first, three labeled sections, a recommendation, within two pages | Missing a section or over length |
| Accuracy and traceability | 20 | Numbers agree with the tables and can be traced to a filter or PivotTable | Numbers right but not traceable, or one error |
| Financial reporting section | 15 | Reconciliation, what agreement shows, and the cutoff meaning for this quarter | Reconciliation without interpretation |
| Managerial accounting section | 15 | A reproducible measure, what it shows, the product-level data for Part II | A margin without its definition |
| Auditing section | 15 | Evidence, the closing-entry problem and avoidance, and limits with consequences | Limits named without consequences |
| Recommendation | 10 | A specific next analysis with the decisions to take first | "Analyze further" |
| Appendix | 10 | Data map and reconciliation table, legible and complete | One of the two, or illegible |

## Extensions and discussion questions

- Write the memo's Auditing section as a table of limitations with a consequence and an action for each.
- Discuss: the case says the memo should recommend an analysis. How would the recommendation change if the margin had not fallen?
- Discuss: Part II will find a cause. How would you decide, from the memo alone, whether the controller is likely to find it believable?
