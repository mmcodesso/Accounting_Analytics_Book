---
note: ch05.ex6
uses: [ch05.g6]
title: Reviewing the Supplier and Item Master Files
kind: exercise
number: '5.6'
unit: '5'
perspective: auditing
tool: excel
minutes: 100
solution: "Chapter05-exercises.zip: Chapter 5 Exercises - Solutions.xlsx, sheets Ex 5.6, Ex 5.6 PurchaseOrder and Ex 5.6 ItemMaster (the supplier columns are on Ex 5.5 Supplier, the line columns on SalesInvoiceLine)"
figures: []
---
{% set g = ch05_g6 %}
# Exercise 5.6: Reviewing the Supplier and Item Master Files

{{ header() }}

## Purpose and learning outcomes

This is the chapter's longest exercise and its sharpest test of judgment. Two master files are tested before an audit relies on them, and most tests come back clean or odd in a way the data cannot explain. The exercise makes four points: standardizing a consistent field damages it, a clean duplicate test shows less than it seems, a zero count needs a control, and master-file fields that disagree with the transactions are findings, not noise. It practices PROPER and EXACT, exact-match counting, COUNTIFS across Tables, MAXIFS and a lookup into the item master. The analytics type is descriptive.

By the end, students can:

- show that PROPER would damage a field that is already consistent, using EXACT because an ordinary comparison ignores case (outcomes 2 and 6);
- test identifiers for duplicates with a method that is safe for masked values, and say what a clean result does not show (outcomes 2 and 6);
- count each supplier's orders and payments across Tables, and check a zero against a control (outcomes 4 and 6);
- test an item master against the transactions that used it, and write the findings with their limits (outcomes 3, 4 and 1).

**Competencies practiced.** CPA Evolution ISC M4 (use and management of data) and Core S2 M8 (audit evidence and tests of controls); IMA Data Governance, and Internal Control; IFAC IES 2 (g), governance, risk management and internal control, and IES 2 (i); AACSB A5 part 5.1.

## Before you assign

- **Files and software.** The workbook of Exercise 5.5, whose Supplier Table keeps every column, for requirements (1) to (4), and a copy of the analysis workbook for the item tests of requirement (5). The model answer keeps them in one file, so its supplier columns sit on Ex 5.5 Supplier, its purchase orders on Ex 5.6 PurchaseOrder, its item master on Ex 5.6 ItemMaster, and the results of both reviews on Ex 5.6. XLOOKUP, COUNTIFS and MAXIFS are used throughout. The model answer's lists also use FILTER and HSTACK, and HSTACK needs a newer Excel than XLOOKUP does, as the chapter note says.
- **Load time.** PurchaseOrder holds {{ g.n_po|count }} rows. Load it to a worksheet.
- **Data conditions.** {{ g.n_names|count }} suppliers; {{ g.n_items|count }} items, of which {{ g.n_blank_price|count }} have no list price and are not in the analysis workbook's Item Table. The Discontinued items that are still active, and the items sold before launch, all have a list price, so the filtered Item Table would find them too; the exercise loads the full item master so that the test does not depend on that filter.
- **Where the new columns go.** On SalesInvoiceLine the lookup columns of Tutorial 5.2 end at column {{ g.letters.ProductType }}, so LaunchDate is in {{ g.letters.LaunchDate }} and BeforeLaunch in {{ g.letters.BeforeLaunch }}.
- **The supplier lists.** The unapproved suppliers have consecutive IDs, and one High-risk supplier is also unapproved.

## How to run it

Individual, about 100 minutes, best in two sittings: 10 on PROPER (requirement 1), 10 on duplicates (2), 5 on the lists (3), 15 on orders and payments (4), 40 on the item master (5) and 20 on the memo (6). Hold back the hint about EXACT until a student reports that PROPER changes nothing. Collect the workbook and the memo.

## Step-by-step solution

### Requirement (1): PROPER and the names it changes

**Step 1. Test the effect.** In the Supplier Table add `ProperName` with `=PROPER([@SupplierName])` and `NameChanged` with `=NOT(EXACT([@SupplierName],[@ProperName]))`. Count with `=COUNTIF(Supplier[NameChanged],TRUE)`.

**Check:** {{ g.n_changed|count }} of {{ g.n_names|count }} names change: {{ g.only_and|count }} because of the connecting word and {{ g.only_abbr|count }} because of a capitalized abbreviation. For example {% for a, b in examples %}"{{ a }}" becomes "{{ b }}"{{ ' and ' if not loop.last else '' }}{% endfor %}. **Watch for:** `<>` in place of EXACT. Excel compares text without regard to case, so every name looks unchanged, the count is zero and the student concludes that PROPER is harmless.

### Requirement (2): Duplicate identifiers

**Step 2. Count equal values.** Add `TaxIDCount` and `BankAccountCount`, then count the suppliers above one:

```
=SUM(--(Supplier[TaxID]=[@TaxID]))
=SUM(--(Supplier[BankAccount]=[@BankAccount]))
=COUNTIF(Supplier[BankAccountCount],">1")
```

**Check:** no TaxID and no BankAccount is shared. **Watch for:** COUNTIF on the masked BankAccount. Its asterisks are wildcards, so the method is unsafe, but the result agrees here ({{ g.wildcard_shared|count }} shared), because the last four characters differ for every supplier. Grade the method, not the count. The clean result shows that no two records carry the same identifier. It does not show that there are no duplicate suppliers: a supplier entered twice with a different or missing identifier is not caught, and both fields are partly masked.

### Requirement (3): The lists

**Step 3. List the unapproved and the High-risk suppliers.** Filter the Supplier Table on IsApproved 0 and on SupplierRiskRating High, or spill them with FILTER.

**Check:** {{ w_unapproved }} unapproved suppliers, IDs {{ unapproved_first }} to {{ unapproved_last }}, and {{ w_high|lower }} High-risk suppliers, IDs {{ high }}. Supplier {{ g.both }} is on both lists.

### Requirement (4): Orders and payments

**Step 4. Load PurchaseOrder and count.** Load PurchaseOrder to a worksheet as in Exercise 5.5. For each supplier on the lists enter:

```
=COUNTIFS(PurchaseOrder[SupplierID],[@SupplierID])
=COUNTIFS(DisbursementPayment[SupplierID],[@SupplierID])
```

**Check:** every unapproved supplier has no purchase order and no payment. **Watch for:** a zero read as proof. Run the same two formulas on an approved supplier, for example the approved High-risk supplier {{ g.high[0].id }}, which has {{ g.high[0].po|count }} orders and {{ g.high[0].pay|count }} payments. A control that returns a count shows the formula and the Table work. The finding is consistent with an approval control that keeps these suppliers from receiving business, and the extract alone cannot show how the control operates.

### Requirement (5): The item master

**Step 5. Load the full item master.** Load the Item Table again as a query named `ItemMaster` with every column, to a worksheet. Add the two columns below and a count of lines before launch:

```
=COUNTIFS(SalesInvoiceLine[ItemID],[@ItemID])
=IF([@InvoiceLineCount]>0,MAXIFS(SalesInvoiceLine[InvoiceDate],SalesInvoiceLine[ItemID],[@ItemID]),"")
```

Name them `InvoiceLineCount` and `LatestInvoiceDate`. On SalesInvoiceLine add `LaunchDate` with an XLOOKUP into ItemMaster, and `BeforeLaunch` with `=[@InvoiceDate]<[@LaunchDate]`. Then add `PrelaunchLines` to ItemMaster with COUNTIFS on ItemID and BeforeLaunch TRUE.

**Step 6. List the three findings.** Filter ItemMaster for LifecycleStatus Discontinued with IsActive 1; for IsActive 0 with InvoiceLineCount above zero; and for PrelaunchLines above zero.

**Check:** see the Expected results. **Watch for:** MAXIFS on an item with no lines. It returns 0, which Excel shows as a meaningless date, and {{ g.inactive_unsold|count }} of the {{ g.inactive_all|count }} inactive items were never invoiced; the IF guard prevents it. Compare dates as dates: the lookup returns the item's LaunchDate, and a blank would compare as zero.

### Requirement (6): The memo

**Step 7. Write the half page.** The model memo covers the supplier master (the names are consistently cased and PROPER would damage {{ g.n_changed|count }} of {{ g.n_names|count }}, so they stay as they are; no shared identifiers; the unapproved suppliers with no business), the High-risk suppliers, and the item master. It recommends that the purchasing tests focus on the {{ w_high_approved }} approved High-risk suppliers and on the suppliers that share an address with an employee (Exercise 5.5). For the items, the memo says that the status and launch fields conflict with each other and with the sales recorded, so they are not evidence that sales of inactive or unlaunched items are blocked, and that whether an item was already inactive when it was sold needs its status history.

**Check:** the memo gives each finding its limit.

## Expected results

| Quantity | Value | Where |
|---|---|---|
| Names PROPER changes | {{ changed|count }} of {{ suppliers|count }} | Step 1 |
| Suppliers sharing a TaxID; a BankAccount | 0; 0 | Step 2 |
| Unapproved suppliers; their purchase orders and payments | {{ w_unapproved }}, IDs {{ unapproved_first }} to {{ unapproved_last }}; 0 and 0 | Steps 3 and 4 |
{% for h in g.high %}
| High-risk supplier {{ h.id }} ({{ h.name }}): approved; orders; payments | {{ 'yes' if h.approved else 'no' }}; {{ h.po|count }}; {{ h.pay|count }} | Step 4 |
{% endfor %}
| Items Discontinued but IsActive 1 | {{ conflict_codes }} | Step 6 |
{% for c, n in g.conflict_lines %}
| {{ c }}: invoice lines | {{ n|count }} | Step 6 |
{% endfor %}
{% for code, n in inactive %}
| Inactive, still invoiced: {{ code }} | {{ n|count }} lines, latest invoice {{ latest }} | Step 6 |
{% endfor %}
{% for p in prelaunch %}
| Invoiced before launch: {{ p.code }} | {{ p.lines|count }} lines from {{ p.first }} to {{ p.last }}; launch {{ p.launch }} | Step 6 |
{% endfor %}
| Lines invoiced before launch; their line total | {{ prelaunch_lines|count }}; ${{ prelaunch_amount|money }} | Step 6 |

{{ expected() }}

The generator's anomaly log also lists {{ 'item' if n_extra == 1 else 'items' }} {{ extra }} as invoiced before launch, but no invoice line of {{ 'that item' if n_extra == 1 else 'those items' }} is dated before {{ 'its' if n_extra == 1 else 'their' }} launch, so {{ 'it does' if n_extra == 1 else 'they do' }} not appear in the lists.

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
