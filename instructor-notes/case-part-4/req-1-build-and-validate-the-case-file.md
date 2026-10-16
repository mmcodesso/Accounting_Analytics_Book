# Requirement 1: Build and validate the case file (Chapters 13, 14, and 16)

| | |
|---|---|
| Unit | Case Part 4: Finding the Cash Behind the Profit |
| Item | Requirement 1 |
| Tools | Power BI Desktop |
| Time | About 150 minutes |
| Solution file | PartIV-case.zip: Charles River Cash Case.pbip, pages About and Validation, the Tests tab (Tests 1 and 2) and the Requirement 1 rows of the Checks tab |
| Release | First edition, dataset release v2027.1 (fiscal 2024–2026) |

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
- **Verify first.** After a refresh, the 58 Requirement 1 rows of the Checks tab all agree.

## How to run it

Individual or pairs, about 150 minutes: 50 for the queries and model, 30 for profiles and links, 40 for Validation and the Tests tab, 30 for Data Through and the About page. Hold back the header-link explanation until a pair sees blank channels. **Collect** the .pbix.

## Step-by-step solution

The project encodes the model and the structure of each page, and its Checks tab proves every value below. How a page looks is visible only in Desktop.

### Part 1: The queries and the model

**Step 1. Load the ledger star and flag the closes.**

a. Save Charles River Cash Case.pbix and turn off the two loading options of Tutorial 13.1.
b. Choose **Home > Get data > Excel workbook**, select GLEntry, Account and JournalEntry, and choose **Transform Data**.
c. In GLEntry, choose **Home > Choose Columns**, keep only what the model needs and filter no rows. Merge JournalEntry on VoucherNumber and EntryNumber with **Home > Merge Queries** and expand EntryType.
d. Add `IsYearEndClose` with **Add Column > Custom Column** (Tutorial 14.3) and clear **Enable load** on JournalEntry.

```m
    #"Added Custom" = Table.AddColumn(#"Expanded JournalEntry", "IsYearEndClose", each [EntryType] <> null and Text.StartsWith([EntryType], "Year-End Close"))
```

**Check:** GLEntry has all 815,921 rows and 134 are flagged: the six closes (JE-2024-000265 and -000266; JE-2025-000287 and -000288; JE-2026-000296 and -000297). **Watch for:** closes left unflagged. Net income nets to zero in every year, because each close moves a year's revenue and expenses to retained earnings.

**Step 2. Carry the channel into Receipts.**

a. In Requisitions, choose **Add Column > Custom Column** for the channel, from the justification, and again for the work order it names. Merge WorkOrder and Employee (requester and approver).
b. In Receipts, merge OrderLines on POLineID, then Requisitions on RequisitionID, and expand Channel.

```m
    #"Added Custom" = Table.AddColumn(#"Changed Type1", "Channel", each if Text.StartsWith([Justification], "WO-COMPONENT-SHORTFALL") then "Work-order shortfall"
        else if Text.StartsWith([Justification], "Supply plan") then "Supply plan" else "Other")
    #"Added Custom2" = Table.AddColumn(#"Changed Type3", "WorkOrderID", each if [Channel] = "Work-order shortfall" then Number.From(Text.BetweenDelimiters([Justification], "WO=", " |")) else null)
```

**Check:** 21,437 work-order shortfall requisitions, 3,921 supply plan and six other. Receipts goes through the order line because the order header names no requisition on 4,408 orders. **Watch for:** a merge through the header. 12,001 of 29,597 receipt lines then have no channel, and the materials among them, 11,524 lines worth $11,113,837.49, drop out of Requirement 4's channel columns.

**Step 3. Build Issues and Item, relate and describe.**

a. In Issues, merge the issue's date and work order. In InventoryPolicy, choose **Group By** (**Advanced**) on ItemID with the largest target and the latest end date, then merge it into Item. Clear **Enable load** on the queries that only feed others.
b. In **Model view**, relate each fact table to its dimensions and to Date, many to one, **Single** direction, and hide the keys.
c. Choose **Modeling > New measure** for each measure and type its definition in **Properties**.

```m
    #"Grouped Rows" = Table.Group(#"Changed Type1", {"ItemID"}, {{"TargetDaysSupply", each List.Max([TargetDaysSupply]), Int64.Type}, {"PolicyEnd", each List.Max([EffectiveEndDate]), type date}})
```

**Check:** Item has 266 rows. **Watch for:** the policy merged before it is grouped. Item then has 505 rows, so ItemID is no longer unique and the relationship cannot be one to many.

### Part 2: Profiles and links

**Step 4. Profile on the entire data set.**

a. In Power Query, choose **View > Column quality**, **Column distribution** and **Column profile**.
b. Click **Column profiling based on top 1000 rows** in the status bar and choose **Column profiling based on entire data set**.
c. Read Justification, Status and ApprovedByEmployeeID in Requisitions.

**Check:** 25,364 requisitions, Justification never empty, 6 without an approver and 522 Approved. **Watch for:** the default profile. The first 1,000 rows are all converted to orders, so no Approved requisition shows, only 2 of the 6 blank approvers do, and the shortfall channel is 161 rows of the thousand when it is most of the data set.

**Step 5. Test the links.** Add `Receipts without a Requisition`, `Issues without a Work Order` and the row counts to Key Measures, and show them as cards titled "Links tested".

**Check:** all 29,597 receipt lines find their order line, each of the 24,842 order lines names one requisition, and 70,126 issue lines sit on 19,234 issues that all find their work order. Issue headers with no lines number 6 (Chapter 12): record them and move on.

### Part 3: Validation and the Tests tab

**Step 6. Reproduce the control totals.** Add a **Table** titled "Control totals by fiscal year" with Year from Date and the measures `Net Income`, `Total Assets`, `Materials Received`, `Receipts to 1045`, `Materials Issued` and `Issues from 1045`, filtered to the years of the window in **Filters on this visual**. The `1045` measures filter AccountNumber.

**Check:** net income and total assets are Tutorial 14.3's and Exercise 14.1's, and each materials pair agrees. **Watch for:** two silent errors. A filter on AccountID `1045` finds no account, and receipts of every item read $21,554,113.46 in 2026 against $17,578,136.00 of materials.

![A mock of the Validation page the model answer ends Requirement 1 with, the evidence a student must reproduce before Requirement 2.](../figures/case-part-4/IF-C4-1-A.pdf)

**Step 7. Write the Tests tab.** In **DAX query view**, type each test under a comment and choose **Run**. Test 1 is the table above in `SUMMARIZECOLUMNS`; Test 2 returns Data Through, the last ledger posting and what follows it. Requirements 2 and 5 add Tests 3 to 5.

### Part 4: Data Through and the About page

**Step 8. Write Data Through and the About page.** Choose **Modeling > New measure**, enter the formula, and add a card titled "Data currency" to the About page with Data Through and the ledger's last posting, and a text box that states the purpose, sources, period, definitions and why Data Through is not the last posting.

```dax
Data Through =
CALCULATE (
    VAR LastDates =
        {
            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "SalesInvoice" ),
            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "CashReceiptApplication" ),
            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "PurchaseInvoice" ),
            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "DisbursementPayment" ),
            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "GoodsReceipt" ),
            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "MaterialIssue" ),
            CALCULATE ( MAX ( GLEntry[PostingDate] ), GLEntry[SourceDocumentType] = "Shipment" )
        }
    RETURN
        IF (
            COUNTROWS ( FILTER ( LastDates, ISBLANK ( [Value] ) ) ) > 0,
            BLANK (),
            MINX ( LastDates, [Value] )
        ),
    REMOVEFILTERS ()
)
```

**Check:** Data Through reads 2026-12-31 under any slicer, because `REMOVEFILTERS ()` clears every filter. The ledger runs to 2027-02-23 only because 263 supplier payments of 2026 invoices ($271,327.17, 526 rows) follow the year. **Watch for:** two wrong answers. The last posting date puts cash at $8,170,928.63, and a bridge for 2027 shows a fall of $271,327.17 that only means the data stop. Adding payroll puts Data Through at 2026-12-18, and the last quarter goes blank, because the last two pay periods are marked Open in the data and are scheduled to pay in 2027. The About page states what Data Through does not show, that no document before it is missing.

**Instructor check.** In **DAX query view**, run this and compare it with the Expected results.

```dax
EVALUATE
ROW (
    "Data Through", FORMAT ( [Data Through], "yyyy-mm-dd" ),
    "Net Income 2026", ROUND ( CALCULATE ( [Net Income], 'Date'[Year] = 2026 ), 2 ),
    "Total Assets 2026", ROUND ( CALCULATE ( [Total Assets], 'Date'[Year] = 2026 ), 2 ),
    "Received less 1045 2026", ROUND ( CALCULATE ( [Materials Received] - [Receipts to 1045], 'Date'[Year] = 2026 ), 2 ),
    "Receipts without a Requisition", [Receipts without a Requisition]
)
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| GLEntry rows; flagged closing rows | 815,921; 134 | 1 |
| Shortfall; supply plan; other requisitions | 21,437; 3,921; six | 2 |
| Item rows; approved and unordered requisitions | 266; 522 | 3, 4 |
| Net income 2024, 2025, 2026 | $5,110,308.27; $5,134,354.71; $4,503,611.24 | 6 |
| Total assets 2024, 2025, 2026 | $23,742,720.31; $31,838,684.00; $39,328,524.11 | 6 |
| Materials received and issued, 2026 | $17,578,136.00; $10,161,204.64 | 6 |
| Data Through; last posting; rows after | 2026-12-31; 2027-02-23; 526 | 8 |

> **Instructor notes, Requirement 1:** GLEntry has 815,921 rows; the six year-end closes (JE-2024-000265 and -000266, JE-2025-000287 and -000288, JE-2026-000296 and -000297) post 134 rows. Channel: Text.StartsWith on Justification, "WO-COMPONENT-SHORTFALL \| WO=\<id\> \| ITEM=\<id\>" for a work-order shortfall (21,437 requisitions; the ITEM in the text always equals ItemID), "Supply plan \<id\> - ..." for the supply plan (3,921; all but 3 carry a SupplyPlanRecommendationID), and six capital requests ("Other"). Receipts: 29,597 lines, every one with its order line, and every order line (24,842) with exactly one requisition; the purchase order header's RequisitionID is blank on 4,408 orders, which is why the merge goes through the line. Issues: 70,126 lines on 19,234 issues, every issue with its work order; 6 issue headers have no lines (Chapter 12). Requisitions: 25,364; 6 with no approver (Exercise 2.5); 522 Approved and never ordered, all work-order shortfall requisitions of December 2026. Validation (fiscal 2024 / 2025 / 2026): net income 5,110,308.27 / 5,134,354.71 / 4,503,611.24; total assets 23,742,720.31 / 31,838,684.00 / 39,328,524.11; materials received (receipt lines of Raw Materials and Packaging items) 7,823,080.62 / 13,490,602.93 / 17,578,136.00 and issued 10,560,905.25 / 10,005,081.44 / 10,161,204.64, equal to the GoodsReceipt debits and MaterialIssue credits to 1045 (AccountNumber, not AccountID). Data Through: the minimum of the last PostingDate of SalesInvoice, CashReceiptApplication, PurchaseInvoice, DisbursementPayment, GoodsReceipt, MaterialIssue, and Shipment postings, inside MINX over a table constructor and with the report's filters removed: 2026-12-31 (the model answer returns a blank if any of the seven has no posting, which MINX would skip). It is a bound observed in the extract, not proof that no document before it is missing, which the reconciliations of Requirement 5 and the source systems' own counts would show. The ledger's last posting is 2027-02-23: 263 supplier payments of 2026 invoices, 526 rows, 271,327.17 (Dr 2010, Cr 1010); a balance taken at that date shows cash 8,170,928.63 and payables 5,966,139.49, and a bridge for 2027 shows a fall of 271,327.17 that only means the data stop. Payroll summaries and payments end 2026-12-18, because the last two pay periods are marked Open in the data and are scheduled to pay in 2027 (Part III case), and the remittances of payroll liabilities run to 2026-12-30. Including them would make Data Through 2026-12-18 and blank the last quarter, so the About page should say why payroll is reported apart. Engine-checked on a reference model in Desktop 2.158.

## What a strong answer says

- **Model.** Closes flagged and left out of every flow, the channel carried through the order line, the policy grouped before it is merged, every measure defined.
- **Profiles and links.** Entire data set, each link tested, isolated exceptions recorded.
- **Validation.** Totals that agree with Tutorial 14.3 and Exercise 14.1, and the new tables tied to account `1045` in a Tests tab.
- **Data Through.** The earliest of the last posting dates of the documents behind the working-capital accounts, with the reason (supplier payments follow the year, and payroll ends before it) and the limit, a bound observed in the extract rather than proof of completeness.

A weak submission says the totals "look right" and has no Tests tab.

## Common mistakes and how to respond

- **Closes left in.** *Symptom:* net income reads zero in every year. *Response:* ask what a close does to a year's revenue and expenses.
- **Merge through the header.** *Symptom:* 12,001 receipt lines with no channel. *Response:* ask which table names the requisition for each line.
- **Policy not grouped.** *Symptom:* 505 item rows. *Response:* ask how many policy rows an item has.
- **Profile of the first rows.** *Symptom:* no Approved requisition in the profile. *Response:* ask which basis the status bar names.
- **Last posting as Data Through.** *Symptom:* 2027-02-23 on the About page. *Response:* ask what posts after the year.

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
