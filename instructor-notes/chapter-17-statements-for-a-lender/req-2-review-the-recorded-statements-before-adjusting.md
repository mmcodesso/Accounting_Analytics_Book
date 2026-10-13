# Requirement 2: Review the recorded statements before adjusting them (Chapters 14 and 15)

| | |
|---|---|
| Unit | Chapter 17: Financial Statements for a Lender |
| Item | Requirement 2 |
| Perspective | Financial accounting |
| Tools | Power BI Desktop |
| Time | About 150 minutes |
| Solution file | Chapter17-capstone-pbi.zip: Charles River Lender Review.pbip, pages Review, Postings (the hidden drill-through), Sources, Questions and Validation, the Tests tab (Tests 1 and 2) and the Requirement 2 rows of the Checks tab; Chapter17-capstone-excel.zip: worksheet Review, which keeps the same results for the package |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

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
- **Data conditions.** GLEntry holds 815,921 rows, so the first refresh is slow. The 6 closes post 134 rows. The opening entry has 18 lines. The ledger runs past the last year-end, because supplier payments follow it.
- **Verify first.** After a refresh, the 72 Requirement 2 rows of the Checks tab in DAX query view all agree.

## How to run it

Individual or pairs, about 150 minutes: 45 for the model, 30 for Balance and the matrix, 25 for the threshold and flags, 20 for the drill-through, 20 for the sources, 10 for the questions. Hold back the Sources page until the Review page works. **Collect** the .pbix.

> **[Figure placeholder IF-17-2-A]** The Review page the model answer ends Part 2 with, the picture of a correct flagged list.
> Kind: pbi-mock · Shows: Report view, page Review. A slicer titled Threshold (what-if) at the top left, a card titled Threshold and materiality, a matrix of statement lines and accounts with the three year-end balances, the change from the prior year to the current one and a Flag column, and a table of the changes above the threshold sorted by size. The flagged rows of the matrix read Above threshold. · Data: The Expected results quantities (materiality, the flagged accounts and their changes), read-only. · Status: planned

## Step-by-step solution

### Part 1: The ledger model and the Balance measure

**Step 1. Load the ledger star and flag the closes.** As in Tutorial 14.3:

a. Choose **Home > Get data > Excel workbook**, select the Tables for the ledger, the chart, the cost centers and the journal entries, and choose **Transform Data**.
b. In GLEntry, merge JournalEntry on VoucherNumber and EntryNumber (**Home > Merge Queries**) and expand EntryType.
c. Add IsYearEndClose with **Add Column > Custom Column**, then clear **Enable load** on JournalEntry.
d. Add the Date table of Tutorial 14.1, choose **Close & Apply**, and relate the Tables in **Model view**, many to one, **Single** direction.

```
    #"Merged Queries" = Table.NestedJoin(#"Changed Type1", {"VoucherNumber"}, JournalEntry, {"EntryNumber"}, "JournalEntry", JoinKind.LeftOuter)
    #"Expanded JournalEntry" = Table.ExpandTableColumn(#"Merged Queries", "JournalEntry", {"EntryType"}, {"EntryType"})
    #"Added Custom" = Table.AddColumn(#"Expanded JournalEntry", "IsYearEndClose", each [EntryType] <> null and Text.StartsWith([EntryType], "Year-End Close"))
```

**Check:** GLEntry has 815,921 rows and 134 are flagged, the 6 closes of Requirement 1.

**Step 2. Write Balance and test it against Requirement 1.** Choose **Modeling > New measure** and type the definition. A card or a matrix by year then reproduces each trial balance.

```dax
Balance =
VAR AsOf = MAX ( 'Date'[Date] )
RETURN
    CALCULATE (
        SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ),
        REMOVEFILTERS ( 'Date' ),
        'Date'[Date] <= AsOf,
        NOT ( GLEntry[IsYearEndClose] && GLEntry[PostingDate] = AsOf )
    )
```

**Check:** a table by year shows 71 accounts with postings at the last year-end and debit and credit balances of $67,107,722.36, Requirement 1's figures. **Watch for:** a measure that leaves out every close (Tutorial 14.3's GL Amount). Balance sheet accounts other than retained earnings are right, but retained earnings lacks the earlier years' income and every revenue and expense account carries three years.

### Part 2: Flag the large changes

**Step 3. Bring in the statement lines.** Load the Working TB Table of the package workbook as a second source, filter out its totals row, and relate its account number to the chart's.

```
    Source = Excel.Workbook(File.Contents("C:\CharlesRiver\Charles River Lender Package.xlsx"), null, true)
    WorkingTB_Table = Source{[Item="WorkingTB",Kind="Table"]}[Data]
    #"Filtered Rows" = Table.SelectRows(#"Removed Other Columns", each [AccountNumber] <> null)
```

**Check:** the matrix can group accounts by statement line. **Watch for:** the totals row. Power Query reads a Table's totals row as data, so a blank account number sits on the one side of the relationship and Desktop rejects it.

**Step 4. Measure the change and set the threshold.** Choose **Modeling > New parameter > Numeric range** for the threshold (the model's series is `GENERATESERIES ( 0, 1000000, 25000 )`, with **Add slicer to this page**), and write the measures.

```dax
Balance 2026 = CALCULATE ( [Balance], REMOVEFILTERS ( 'Date' ), 'Date'[Date] = DATE ( 2026, 12, 31 ) )

Change 2025 to 2026 = [Balance 2026] - [Balance 2025]

Absolute Change = ABS ( [Change 2025 to 2026] )

Materiality = ROUND ( 0.05 * [Net Income], 2 )

Materiality 2026 = CALCULATE ( [Materiality], REMOVEFILTERS (), 'Date'[Year] = 2026 )

Threshold Value = SELECTEDVALUE ( 'Threshold'[Threshold], [Materiality 2026] )

Is Above Threshold = IF ( [Absolute Change] > [Threshold Value], 1, 0 )

Flag = IF ( [Absolute Change] > [Threshold Value], "Above threshold" )
```

**Check:** the card titled "Threshold and materiality" shows materiality of $225,180.56 for 2026 and $256,717.74 for 2025, and the threshold reads the 2026 figure until the slider moves.

**Step 5. Build the matrix and the flagged list.** On the Review page add the slicer ("Threshold (what-if)", set to **Single select**), the matrix ("Statement lines and accounts: year-end balances (debits less credits) and the change from 2025 to 2026") with the year-end balances, the change and Flag, and a table ("Changes above the threshold (right-click > Drill through > Postings)") filtered to the measure `Is Above Threshold` with its filter card, sorted by absolute change.

**Check:** the report flags 8 accounts and retained earnings: 1045 Inventory - Materials and Packaging +$7,416,931.36; 2050 Sales Tax Payable -$1,932,519.29; 1040 Inventory - Finished Goods +$1,339,881.52; 1010 Cash and Cash Equivalents -$941,310.30; 2010 Accounts Payable -$769,657.14; 4020 Sales Revenue - Lighting -$498,432.37; 5080 Manufacturing Variance +$403,686.80; 5020 COGS - Lighting +$246,456.24. Retained earnings moves by $5,134,354.71, the 2025 net income closed into it. **Watch for:** four wrong versions.

- Leaving out every close flags 30 accounts besides retained earnings: each revenue and expense account's change becomes the whole year's activity.
- Leaving every close in drops 4020 Sales Revenue - Lighting, 5080 Manufacturing Variance, 5020 COGS - Lighting, and the list has 5 accounts: every revenue and expense account is zero at both year-ends.
- Testing the signed change against the threshold flags only 1045 Inventory - Materials and Packaging, 1040 Inventory - Finished Goods, 5080 Manufacturing Variance, 5020 COGS - Lighting, and misses 2050 Sales Tax Payable, 1010 Cash and Cash Equivalents, 2010 Accounts Payable, 4020 Sales Revenue - Lighting. Use the absolute change.
- A balance at the ledger's last date is not a year-end balance: cash reads $8,170,928.63 against $8,442,255.80, and accounts payable $5,966,139.49 against $6,237,466.66, because supplier payments of $271,327.17 follow the year.

### Part 3: Drill through and the sources

**Step 6. Drill through to the postings.** Add a page Postings with the account label as its drill-through field (the **Drillthrough** section of the **Visualizations** pane), cards for the balances, a matrix of activity by SourceDocumentType and year ("Activity by source document, 2025 and 2026 (closes left out)"), and a table of the postings of 2026 ("Postings in fiscal 2026"). Right-click a flagged account and choose **Drillthrough** > **Postings**.

**Check:** from the largest change, the postings show the source documents behind it and each posting's voucher number. Put a unique key in the posting table, or identical postings merge into one row.

**Step 7. Find the balances that rest on the opening entry.** Add a Sources page with a matrix of the balance sheet accounts by SourceDocumentType ("Balance-sheet accounts at the end of fiscal 2026, by source document"), a table of the opening entry's lines ("The opening entry's lines (debits less credits)") and a list of the accounts posted by journal entries alone ("Balance-sheet accounts posted by journal entries alone").

```dax
Opening Entry Amount = CALCULATE ( SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ), GLEntry[EntryType] = "Opening" )

Postings after Opening = CALCULATE ( COUNTROWS ( GLEntry ), REMOVEFILTERS ( 'Date' ), GLEntry[EntryType] <> "Opening" || ISBLANK ( GLEntry[EntryType] ) ) + 0

Moved since Opening = [Balance 2026] - CALCULATE ( [Opening Entry Amount], REMOVEFILTERS ( 'Date' ) )

Document Postings = CALCULATE ( COUNTROWS ( GLEntry ), REMOVEFILTERS ( 'Date' ), GLEntry[SourceDocumentType] <> "JournalEntry" ) + 0

Journal Entries Only = IF ( [Postings] > 0 && [Document Postings] = 0, 1, 0 )
```

**Check:** the opening entry has 18 lines. Balances unchanged since it: 1050 Prepaid Expenses, 1110 Furniture and Fixtures, 2030 Accrued Payroll, 3010 Common Stock; all but the payroll account carry a single posting. Accounts posted by journal entries alone: 1050 Prepaid Expenses, 1110 Furniture and Fixtures, 1150 Accumulated Depreciation - Furniture and Fixtures, 1160 Accumulated Depreciation - Warehouse Equipment, 1170 Accumulated Depreciation - Office Equipment, 1186 Accumulated Depreciation - Manufacturing Equipment, 2110 Notes Payable, 3010 Common Stock, 3030 Retained Earnings, 8010 Income Summary; the property and debt records support the equipment and the notes. **Watch for:** counting postings. The payroll account has 8,968 postings, yet none moved the balance, because every payroll posting to it nets to zero.

### Part 4: The Questions table

**Step 8. Record the questions.** Use **Home > Enter data** for a Questions table (number, question, accounts, requirement) and show it on a Questions page.

**Check:** 12 questions, each naming the later requirement that answers it (one for Requirement 3, three for Requirement 4, three for Requirement 5, five for Requirement 9).

**Instructor check.** In **DAX query view**, run this and compare it with the Expected results.

```dax
EVALUATE
ROW (
    "Materiality 2026", [Materiality 2026],
    "Threshold", [Threshold Value],
    "Accounts flagged", COUNTROWS ( FILTER ( VALUES ( Account[AccountNumber] ), [Is Above Threshold] = 1 ) ),
    "1045 change", CALCULATE ( [Change 2025 to 2026], Account[AccountNumber] = 1045 )
)
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Materiality, 2026; 2025 | $225,180.56; $256,717.74 | 4 |
| Accounts flagged, retained earnings included | 9 | 5 |
| Largest change, 1045 | $7,416,931.36 | 5 |
| Cash at the last year-end; at the ledger's last date | $8,442,255.80; $8,170,928.63 | 5 |
| Opening entry; its lines | JE-2024-000001; 18 | 7 |
| Opening lines with no document: prepaid; payroll; payables | $60,000.00; $95,000.00; $2,096,371.12 | 7 |
| Growth of the accrued expenses account in 2026 | $83,563.65 | 8 |

> **Instructor notes, Requirement 2:** materiality, 5% of recorded income before income taxes: 225,180.56 (2026) and 256,717.74 (2025). At a year-end the Balance measure shows a revenue or expense account's activity for that year, because the prior close zeroed it, so the change for those accounts is this year's activity less last year's. Changes from 2025 to 2026 above 225,180.56: 1045 +7,416,931.36; 2050 +1,932,519.29 (credit); 1040 +1,339,881.52; 1010 -941,310.30; 2010 +769,657.14 (credit); 4020 +498,432.37 (credit); 5080 +403,686.80; 5020 +246,456.24; retained earnings moves by 2025's net income, closed into it. Next largest: 1186 186,166.63 and 2110 145,879.45. Balances resting on the opening entry (JE-2024-000001, 18 lines): 1050 Prepaid Expenses 60,000.00, its only posting; 2030 Accrued Payroll 95,000.00, because every payroll posting to it nets to zero; and parts of 1020 (380,000.00), 2010 (2,096,371.12, equal to opening cash to the cent), and 2040 (85,000.00), none with a document. 1110 also has a single posting, but the FixedAsset register supports it (OFF-0001, 420,000). Questions to expect: why 2040 grew (by 83,563.65; Requirement 3); cutoff, payroll, and interest at each year-end (Requirement 4); a credit balance in 1090 inside current assets (Requirement 5); 1030 unused (Requirement 5); 2050 has no debits except credit memos, 2120 Lease Liability is unused while rent is paid monthly, there is no tax account, and 7010 shows no interest income on more than 8 million of cash (Requirement 9).

## What a strong answer says

- **The flags.** Materiality as the controller set it, an absolute test, and the flagged accounts read as questions: inventories and sales tax, cash, payables and the movement in cost of goods sold and its variance.
- **The sources.** Which balances rest on journal entries alone, which have not moved since the opening entry, and which opening lines have no document.
- **The questions.** Each tied to the requirement that will answer it, including those the ledger cannot settle.

A weak answer lists the flagged accounts and stops, or records questions with no requirement.

## Common mistakes and how to respond

- **Every close left out.** *Symptom:* 30 accounts flagged. *Response:* ask what a revenue account's change means after the prior close.
- **Closes left in.** *Symptom:* only 5 accounts flagged and none from the income statement. *Response:* ask what the close does on the as-of date itself.
- **The signed change.** *Symptom:* cash and the credit-balance accounts missing. *Response:* ask which direction a fall in cash and a rise in a liability take in debits less credits.
- **The ledger's last date.** *Symptom:* cash of $8,170,928.63. *Response:* ask what posts after the year-end.
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

- Move the slider to the largest step below the change in account `1186`, $186,166.63, and say which account enters the list.
- Add a card that counts the accounts whose balance moved only by journal entries in the year, and say what such a measure would catch in another company.
- Discuss: the review flagged retained earnings. Is that a question or an explanation?
- Discuss: why does the case build the Review file before any adjustment, not after?
