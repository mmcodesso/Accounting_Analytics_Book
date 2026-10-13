# Exercise 5.6: Reviewing the Supplier and Item Master Files

| | |
|---|---|
| Unit | Chapter 5: Data Preparation and Cleaning in Excel |
| Item | Exercise 5.6 |
| Perspective | Auditing |
| Tools | Excel |
| Time | About 100 minutes |
| Solution file | Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheets Ex 5.6, Ex 5.6 PurchaseOrder and Ex 5.6 ItemMaster (the supplier columns are on Ex 5.5 Supplier, the line columns on SalesInvoiceLine) |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

This is the chapter's longest exercise and its sharpest test of judgment. Two master files are tested before an audit relies on them, and most tests come back clean or odd in a way the data cannot explain. The exercise makes four points: standardizing a consistent field damages it, a clean duplicate test shows less than it seems, a zero count needs a control, and master-file fields that disagree with the transactions are findings, not noise. It practices PROPER and EXACT, exact-match counting, COUNTIFS across Tables, MAXIFS and a lookup into the item master. The analytics type is descriptive.

By the end, students can:

- show that PROPER would damage a field that is already consistent, using EXACT because an ordinary comparison ignores case (outcomes 2 and 6);
- test identifiers for duplicates with a method that is safe for masked values, and say what a clean result does not show (outcomes 2 and 6);
- count each supplier's orders and payments across Tables, and check a zero against a control (outcomes 4 and 6);
- test an item master against the transactions that used it, and write the findings with their limits (outcomes 3, 4 and 1).

**Competencies practiced.** CPA Evolution ISC M4 (use and management of data) and Core S2 M8 (audit evidence and tests of controls); IMA Data Governance, and Internal Control; IFAC IES 2 (g), governance, risk management and internal control, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The Supplier Table from Exercise 5.5 with every column, and a copy of the analysis workbook for the item tests. The model answer keeps them in one file. XLOOKUP, COUNTIFS and MAXIFS are used throughout; the model answer's lists also use FILTER and HSTACK, which need Microsoft 365.
- **Load time.** PurchaseOrder holds 18,832 rows. Load it to a worksheet.
- **Data conditions.** 110 suppliers; 266 items, of which 43 have no list price and are not in the analysis workbook's Item Table. The Discontinued items that are still active, and the items sold before launch, all have a list price, so the filtered Item Table would find them too; the exercise loads the full item master so that the test does not depend on that filter.
- **Where the new columns go.** On SalesInvoiceLine the lookup columns of Tutorial 5.2 end at column W, so LaunchDate is in X and BeforeLaunch in Y.
- **The supplier lists.** The unapproved suppliers have consecutive IDs, and one High-risk supplier is also unapproved.

## How to run it

Individual, about 100 minutes, best in two sittings: 10 on PROPER (requirement 1), 10 on duplicates (2), 5 on the lists (3), 15 on orders and payments (4), 40 on the item master (5) and 20 on the memo (6). Hold back the hint about EXACT until a student reports that PROPER changes nothing. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): PROPER and the names it changes

**Step 1. Test the effect.** In the Supplier Table add `ProperName` with `=PROPER([@SupplierName])` and `NameChanged` with `=NOT(EXACT([@SupplierName],[@ProperName]))`. Count with `=COUNTIF(Supplier[NameChanged],TRUE)`.

**Check:** 62 of 110 names change: 45 because of the connecting word and 17 because of a capitalized abbreviation. For example "Watson, Mitchell and Chen" becomes "Watson, Mitchell And Chen" and "Donaldson LLC" becomes "Donaldson Llc". **Watch for:** `<>` in place of EXACT. Excel compares text without regard to case, so every name looks unchanged, the count is zero and the student concludes that PROPER is harmless.

### Requirement (2): Duplicate identifiers

**Step 2. Count equal values.** Add `TaxIDCount` and `BankAccountCount`, then count the suppliers above one:

```
=SUM(--(Supplier[TaxID]=[@TaxID]))
=SUM(--(Supplier[BankAccount]=[@BankAccount]))
=COUNTIF(Supplier[BankAccountCount],">1")
```

**Check:** no TaxID and no BankAccount is shared. **Watch for:** COUNTIF on the masked BankAccount. Its asterisks are wildcards, so the method is unsafe, but the result agrees here (0 shared), because the last four characters differ for every supplier. Grade the method, not the count. The clean result shows that no two records carry the same identifier. It does not show that there are no duplicate suppliers: a supplier entered twice with a different or missing identifier is not caught, and both fields are partly masked.

### Requirement (3): The lists

**Step 3. List the unapproved and the High-risk suppliers.** Filter the Supplier Table on IsApproved 0 and on SupplierRiskRating High, or spill them with FILTER.

**Check:** Seven unapproved suppliers, IDs 104 to 110, and seven High-risk suppliers, IDs 11, 24, 40, 55, 57, 80, and 104. Supplier 104 is on both lists.

### Requirement (4): Orders and payments

**Step 4. Load PurchaseOrder and count.** Load PurchaseOrder to a worksheet as in Exercise 5.5. For each supplier on the lists enter:

```
=COUNTIFS(PurchaseOrder[SupplierID],[@SupplierID])
=COUNTIFS(DisbursementPayment[SupplierID],[@SupplierID])
```

**Check:** every unapproved supplier has no purchase order and no payment. **Watch for:** a zero read as proof. Run the same two formulas on an approved supplier, for example the approved High-risk supplier 11, which has 60 orders and 116 payments. A control that returns a count shows the formula and the Table work. The finding is consistent with an approval control that keeps these suppliers from receiving business, and the extract alone cannot show how the control operates.

### Requirement (5): The item master

**Step 5. Load the full item master.** Load the Item Table again as a query named `ItemMaster` with every column, to a worksheet. Add the two columns below and a count of lines before launch:

```
=COUNTIFS(SalesInvoiceLine[ItemID],[@ItemID])
=IF([@InvoiceLineCount]>0,MAXIFS(SalesInvoiceLine[InvoiceDate],SalesInvoiceLine[ItemID],[@ItemID]),"")
```

Name them `InvoiceLineCount` and `LatestInvoiceDate`. On SalesInvoiceLine add `LaunchDate` with an XLOOKUP into ItemMaster, and `BeforeLaunch` with `=[@InvoiceDate]<[@LaunchDate]`. Then add `PrelaunchLines` to ItemMaster with COUNTIFS on ItemID and BeforeLaunch TRUE.

**Step 6. List the three findings.** Filter ItemMaster for LifecycleStatus Discontinued with IsActive 1; for IsActive 0 with InvoiceLineCount above zero; and for PrelaunchLines above zero.

**Check:** see the Expected results. **Watch for:** MAXIFS on an item with no lines. It returns 0, which Excel shows as a meaningless date, and 12 of the 15 inactive items were never invoiced; the IF guard prevents it. Compare dates as dates: the lookup returns the item's LaunchDate, and a blank would compare as zero.

### Requirement (6): The memo

**Step 7. Write the half page.** The model memo covers the supplier master (the names are consistently cased and PROPER would damage 62 of 110, so they stay as they are; no shared identifiers; the unapproved suppliers with no business), the High-risk suppliers, and the item master. It recommends that the purchasing tests focus on the six approved High-risk suppliers and on the suppliers that share an address with an employee (Exercise 5.5). For the items, the memo says that the status and launch fields conflict with each other and with the sales recorded, so they are not evidence that sales of inactive or unlaunched items are blocked, and that whether an item was already inactive when it was sold needs its status history.

**Check:** the memo gives each finding its limit.

## Expected results

| Quantity | Value | Where |
|---|---|---|
| Names PROPER changes | 62 of 110 | Step 1 |
| Suppliers sharing a TaxID; a BankAccount | 0; 0 | Step 2 |
| Unapproved suppliers; their purchase orders and payments | Seven, IDs 104 to 110; 0 and 0 | Steps 3 and 4 |
| High-risk supplier 11 (Thomas, Robinson and Cunningham): approved; orders; payments | yes; 60; 116 | Step 4 |
| High-risk supplier 24 (Barrett Inc): approved; orders; payments | yes; 42; 78 | Step 4 |
| High-risk supplier 40 (Yang-Sandoval): approved; orders; payments | yes; 53; 88 | Step 4 |
| High-risk supplier 55 (Donaldson LLC): approved; orders; payments | yes; 66; 120 | Step 4 |
| High-risk supplier 57 (Lopez, Sheppard and Ramirez): approved; orders; payments | yes; 52; 82 | Step 4 |
| High-risk supplier 80 (Gordon and Sons): approved; orders; payments | yes; 51; 91 | Step 4 |
| High-risk supplier 104 (Clay, Hunt and Anderson): approved; orders; payments | no; 0; 0 | Step 4 |
| Items Discontinued but IsActive 1 | ACC-MIR-0001, LGT-TBL-0001, TXT-THR-0001 | Step 6 |
| ACC-MIR-0001: invoice lines | 119 | Step 6 |
| LGT-TBL-0001: invoice lines | 90 | Step 6 |
| TXT-THR-0001: invoice lines | 293 | Step 6 |
| Inactive, still invoiced: ACC-PLN-0002 | 132 lines, latest invoice 2026-12-31 | Step 6 |
| Inactive, still invoiced: LGT-PND-0002 | 68 lines, latest invoice 2026-12-31 | Step 6 |
| Inactive, still invoiced: FUR-SDB-0002 | 216 lines, latest invoice 2026-12-31 | Step 6 |
| Invoiced before launch: LGT-CHD-0019 | 58 lines from 2024-02-11 to 2026-01-15; launch 2026-01-21 | Step 6 |
| Invoiced before launch: ACC-ART-0020 | 54 lines from 2024-01-11 to 2025-01-31; launch 2025-02-05 | Step 6 |
| Lines invoiced before launch; their line total | 112; $206,424.41 | Step 6 |

> **Instructor notes, Exercise 5.6:** PROPER changes 62 of 110 supplier names, for example "Watson, Mitchell and Chen" to "Watson, Mitchell And Chen" and "Donaldson LLC" to "Donaldson Llc": the names are already consistently cased, so standardizing damages them. No TaxID or BankAccount is shared: no duplicate suppliers on these keys, although duplicates with different identifiers would not be caught. Seven suppliers are unapproved (IDs 104 to 110), and none has a purchase order or a payment in the extract, which is consistent with an approval control that keeps them from receiving business (the extract alone cannot show how the control operates). Seven suppliers are rated High risk (IDs 11, 24, 40, 55, 57, 80, and 104), six of them approved and receiving business. The six suppliers of Exercise 5.5 that share an address with an employee are also worth focusing on. Item master: three items are Discontinued but IsActive 1 (IDs 1, 2, 6: ACC-MIR-0001, LGT-TBL-0001, TXT-THR-0001), a status conflict. Three Discontinued items with IsActive 0 were still invoiced in every year through 2026-12-31: ACC-PLN-0002 (132 lines), LGT-PND-0002 (68), and FUR-SDB-0002 (216), the sideboard used as an example in the chapter. Two items were invoiced before their LaunchDate: LGT-CHD-0019 (launch 2026-01-21; 58 lines from 2024-02-11 to 2026-01-15) and ACC-ART-0020 (launch 2025-02-05; 54 lines from 2024-01-11 to 2025-01-31), 112 lines and 206,424.41 in all. These are the AnomalyLog's item\_status\_alignment\_conflict, discontinued\_item\_in\_new\_activity, and prelaunch\_item\_in\_new\_activity items; the log also names item 228, but no line of item 228 is dated before its launch. The master holds only current values, so whether an item was already inactive when it was sold needs its status history; as they stand, the status and launch fields conflict with each other and with the sales recorded, so they are not evidence that sales of inactive or unlaunched items are blocked.

The generator's anomaly log also lists item 228 as invoiced before launch, but no invoice line of that item is dated before its launch, so it does not appear in the lists.

## What a strong answer says

- **Requirement (1).** The names are already consistently cased; PROPER lowers "and" and abbreviations; so the right step is to leave the field alone and record that it was checked.
- **Requirement (2).** A clean result with its limit: identifiers are unique, which does not rule out a duplicate entered under a different identifier.
- **Requirement (4).** The zero is checked against a control, and the finding is stated as consistent with a control, not as proof of one.
- **Requirement (6).** Each item finding is a conflict between fields, and the memo says the master holds only current values, so history is needed. The recommendation names where the purchasing tests should go.

A weak answer applies PROPER anyway, reads the clean duplicate test as "no duplicates", or calls the item findings sales controls that failed.

## Common mistakes and how to respond

- **`<>` for EXACT.** *Symptom:* zero names changed. *Response:* ask whether `"And"<>"and"` is TRUE in Excel.
- **COUNTIF on masked accounts.** *Symptom:* none here. *Response:* ask what an asterisk means to COUNTIF, and mark the method.
- **A zero without a control.** *Response:* run the formula on a supplier that has orders.
- **MAXIFS dates in the year `1900`.** *Cause:* items with no invoice lines. *Response:* guard with the count.
- **The filtered Item Table.** *Symptom:* none here. *Response:* the full master is the population; ask what the filter could have removed.
- **A memo that names a control failure.** *Response:* ask what the extract shows and what it cannot.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: PROPER | 15 | EXACT, the count, the reason PROPER would damage the names | A count without the reason |
| Requirement 2: duplicates | 15 | An exact comparison, a stated result and its limit | COUNTIF with no limit |
| Requirement 3: lists | 5 | Both lists, the overlap noticed | One list |
| Requirement 4: orders and payments | 15 | COUNTIFS on both Tables, a control run | No control |
| Requirement 5: item master | 30 | The three tests with counts and the guarded MAXIFS | Two of three |
| Requirement 6: memo | 20 | Both reviews, each finding with its limit, a focus recommendation | Findings without limits |

## Extensions and discussion questions

- Add each High-risk supplier's purchase order total and payment total to its row, and compare the approved ones with a sample of suppliers rated Low risk.
- For each item that was invoiced, calculate the days between its LaunchDate and its first InvoiceDate, and describe the distribution.
- Discuss: the item master holds only current values. What history would you request, and from whom?
- Discuss: Chapter 8 tests supplier invoices and payments in depth. Which of this exercise's findings would you carry into that work?
