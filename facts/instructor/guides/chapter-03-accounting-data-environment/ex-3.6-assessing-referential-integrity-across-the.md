---
note: ch03.ex6
title: Assessing Referential Integrity Across the Charles River Database
kind: exercise
number: '3.6'
unit: '3'
perspective: auditing
tool: conceptual
minutes: 90
solution: ''
figures:
  - id: IF-03-6-A
    kind: excel-mock
    purpose: The test log of a finished answer, one row for each relationship, with the counts that the memo reports.
    shows: A worksheet named Integrity Tests with the columns Child table, Foreign key, Parent table, Primary key, Rows, Blank, Orphans, Blank allowed because, and Verdict, and one row for each relationship of the Step 4 log. The Orphans column shows no orphans and the Verdict column reads Maintained. Rows with a blank count have a short reason in the Blank allowed because column. Beside the table sits a small PivotTable of the distinct AccountID values of the ledger, with a column that shows the lookup result for each, all ok. The formula bar shows the COUNTIFS lookup of the helper column.
    data: The relationships of this guide's Step 4 log, with their counts, and the distinct accounts of the ledger.
---
# Exercise 3.6: Assessing Referential Integrity Across the Charles River Database

{{ header() }}

## Purpose and learning outcomes

The chapter says that the Charles River file declares no foreign keys, so the relationships have to be tested. This exercise makes students do it. They list relationships from the diagrams, test them with lookups in the workbook, separate blanks from orphans, and write a memo. The result is clean everywhere, and that is the lesson: the clean result comes from the tests and not from the database, so the memo must say what was tested, how and what it does not show. The exercise also trains a method for large tables, a PivotTable of distinct values tested against the parent's list. The analytics type is descriptive.

By the end, students can:

- state a foreign key as child table, column, parent table and key, and say which links cross table groups (chapter outcome 2);
- test a relationship in Excel and report its orphans, counting blanks separately;
- decide for each blank whether the relationship allows it;
- use a PivotTable of distinct values to test a foreign key in a table of hundreds of thousands of rows;
- write a memo that says why a clean result comes from testing, and what it leaves open (outcome 6).

**Competencies practiced.** CPA Evolution Core S2 M4 (information technology and IT controls) and ISC M4 (use and management of data); IMA Data Governance, and Reporting and Control, Internal Control; IFAC IES 2 (i), judging the adequacy of information technology processes and controls, and IES 4 (a), professional skepticism and judgment; AACSB A5 part 5.1.

## Before you assign

- Students need CharlesRiver_Work.xlsx, Tutorial 2.2's Step 5 (the PivotTable of AccountID tested against the chart) and the chapter's sections on keys.
- The exercise relies on these conditions. The file declares no foreign keys. Every filled-in key of the {{ n_tests }} relationships of the model answer finds its parent ({{ n_orphans }} orphans). {{ n_blank }} of them have blanks by design, and each blank has a reason. GLEntry has {{ gl_rows|count }} rows.
- The large tables are the practical problem. A lookup in every row of GLEntry makes Excel unresponsive, so the PivotTable method is required there. It also works for any foreign key with a few hundred distinct values at most: {{ pivot['SalesOrder.CustomerID'] }} customers in SalesOrder, {{ pivot['SalesOrderLine.ItemID'] }} items in SalesOrderLine, {{ pivot['GLEntry.AccountID'] }} accounts and {{ pivot['GLEntry.CostCenterID'] }} cost centers in GLEntry. A key that is nearly distinct in every row, such as the shipment line on an invoice line, is not shortened by a PivotTable, and a whole-column lookup takes minutes. Tell students to choose their six relationships with that in mind, and to let Excel finish.
- Hold the trace until the extension. The relationship between GLEntry and its source documents is not a foreign key, and it is the one place where this data holds an orphan.

## How to run it

Individual work. For about 90 minutes: 15 listing the relationships (requirement 1), 40 testing (requirement 2), 10 on the three named relationships (requirement 3) and 25 on the memo (requirement 4).

**Hints.** If a student reports many orphans, ask which column they tested against. If a blank is counted as an orphan, ask what the formula does with an empty cell. Give the formula pattern of Step 2 only after the first attempt. **Collect** the test log and the memo.

## Step-by-step solution

### Requirement (1): List the relationships

**Step 1. Write each foreign key from the diagrams.** Use Figures 3.7 and 3.9, and write child table, foreign key, parent table and primary key. The model list has {{ n_tests }}, of which {{ n_cross }} cross table groups: SalesOrderLine.ItemID to Item, GLEntry.AccountID to Account and GLEntry.CostCenterID to CostCenter.

| Child.column | Parent.column | Where it sits |
|---|---|---|
{% for t in tests %}
| {{ t.child }}.{{ t.fk }} | {{ t.parent }}.{{ t.pk }} | {{ t.group }} |
{% endfor %}

**Check:** at least six relationships, each with the four parts, and one that crosses groups. **Watch for:** a student who lists a relationship with two column names that do not exist, and for the account link written as AccountID to AccountNumber.

### Requirement (2): Test each relationship

**Step 2. Test a small or medium table with a helper column.** On the child worksheet, in the first free column, look each filled-in key up in the parent and label the row. For SalesOrder, whose first free column is {{ tests[0].free_col }}:

```text jinja
{{ tests[0].formula }}
```

Copy it down, then count the labels:

```text jinja
{{ tests[0].count_formula }}
```

**Check:** the labels are ok, blank or orphan, and the count of orphans is {{ tests[0].orphans }}. **Watch for:** a formula with no test for an empty cell. COUNTIFS treats an empty criterion cell as zero, which matches no ID, so every blank would be labeled an orphan. The first test of the formula is what separates them.

**Step 3. Test the large table with a PivotTable.** For GLEntry, do not copy a formula down {{ gl_rows|count }} rows.

a. Insert a PivotTable from **GLEntry** with AccountID in **Rows**. It lists {{ used }} distinct accounts, where the chart holds {{ accounts }}.
b. Next to the PivotTable, look each listed AccountID up in the AccountID column of **Account** (XLOOKUP or COUNTIFS).
c. Count the misses.

**Check:** the result is {{ tests[9].orphans }} orphans. Repeat for CostCenterID: the PivotTable lists {{ pivot['GLEntry.CostCenterID'] }} cost centers and a (blank) row for the {{ tests[10].blank|count }} ledger rows with none, which is the optional relationship of Exercise 2.4. **Watch for:** testing AccountID against the AccountNumber column. AccountID and AccountNumber are different numbers, and the test flags all {{ wrong }} accounts the ledger uses. The pair to match is the key in both tables.

{{ figure('IF-03-6-A') }}

**Step 4. Decide whether each blank is allowed.** The model log, with the reason for each blank:

| Child.column | Rows | Blank | Orphans | Blank allowed because |
|---|---:|---:|---:|---|
{% for t in tests %}
| {{ t.child }}.{{ t.fk }} | {{ t.rows|count }} | {{ t.blank|count }} | {{ t.orphans|count }} | {{ t.reason if t.reason else 'never blank' }} |
{% endfor %}

**Check:** each relationship has a count of rows, blanks and orphans and a verdict, and each blank has a reason. A blank is allowed where the relationship is optional: an invoice line for a design service has no shipment line, a receipt names its own invoice only for a minority of receipts (the application table holds the link), a ledger row without a cost center is mostly a balance sheet row, and a top-level account has no parent.

### Requirement (3): The three named relationships

**Step 5. Report SalesOrder to Customer, SalesOrderLine to Item and GLEntry to Account.** The three have {{ tests[0].orphans + tests[1].orphans + tests[9].orphans }} orphans between them, so there are no key values or record counts to list, and the log says so in words. The parents with no children are a different matter and not an orphan: {{ tests[0].childless|count }} customers have no orders, {{ tests[1].childless|count }} items appear on no order line, and {{ tests[9].childless|count }} accounts have no ledger rows, among them the header accounts.

**Check:** the student does not report the childless parents as violations. **Watch for:** the reverse test, which looks up the parent's keys in the child and reports the misses.

### Requirement (4): Write the memo

**Step 6. Outline one page.** A model memo has five parts: the purpose and scope (the relationships and why they were chosen); the method (a lookup with blanks separated, and a PivotTable of distinct values for the ledger); the results table of Step 4; the conclusion, that integrity was maintained in all {{ n_tests }} relationships tested; and the limits.

What a clean result tells the audit team: every key that is filled in finds its parent, so a join on these keys will not lose rows to an orphan and the totals built on them rest on a complete link. Why the assurance comes from the tests: the file declares no foreign keys, so nothing in it enforces the links. The same file could have held an orphan, and only the test would have found it. The limits: a valid key can still be the wrong one (a customer ID that exists and is not the customer who ordered), the tests cover only the listed relationships, and they say nothing about the source-document trace, which is not a foreign key.

**Check:** the memo says that the database did not give the assurance, and that the result is as of the extract's date.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Relationships tested; crossing table groups | {{ n_tests }}; {{ n_cross }} | Step 1 |
| Orphaned keys among them | {{ n_orphans }} | Step 4 |
| Relationships with blanks | {{ n_blank }} | Step 4 |
| Distinct accounts in the ledger; in the chart | {{ used }}; {{ accounts }} | Step 3 |
| Accounts flagged if tested against AccountNumber | {{ wrong }} | Step 3 |
| Ledger rows with no cost center | {{ tests[10].blank|count }} | Step 3 |

## What a strong answer says

- **Requirement (1).** At least six complete relationships, with a cross-group one.
- **Requirement (2).** Counts of rows, blanks and orphans for each, blanks reasoned, the PivotTable method for the ledger.
- **Requirement (3).** The three relationships reported as clean, with childless parents distinguished from orphans.
- **Requirement (4).** A conclusion that integrity was maintained, and an explanation that the tests, not the file, give the assurance, with limits.

A weak answer reports violations that are blanks or childless parents, reports only the conclusion, or says that the database ensures integrity.

## Common mistakes and how to respond

- **Testing AccountID against AccountNumber.** *Symptom:* every account an orphan. *Response:* ask which column of Account holds the key.
- **A blank counted as an orphan.** *Symptom:* thousands of orphans on an optional key. *Cause:* COUNTIFS treats an empty criterion cell as zero. *Response:* ask what the formula does with an empty cell.
- **The test run backwards.** *Symptom:* customers with no orders reported as violations. *Response:* ask which table holds the foreign key.
- **A lookup in every ledger row.** *Symptom:* a frozen workbook. *Response:* send them to the PivotTable method of Tutorial 2.2.
- **The pivot's (blank) row looked up.** *Symptom:* one spurious miss. *Response:* ask what the blank row stands for.
- **The memo says the database ensures integrity.** *Response:* ask what the file declares.
- **A formula copied only to the visible rows.** *Symptom:* labels missing in a filtered range. *Response:* clear the filter first.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the relationships | 15 | At least six, each with four parts, one cross-group | Fewer, or incomplete |
| Requirement 2: the tests | 35 | Counts of rows, blanks and orphans, blanks reasoned, the PivotTable for the ledger | Orphans without blanks, or no method for the ledger |
| Requirement 3: the three named | 15 | Reported clean, with childless parents set apart | Reported without the distinction |
| Requirement 4: the memo | 35 | Results, conclusion, why testing gives the assurance, and the limits | Results without the explanation |

## Extensions and discussion questions

- Test the source-document trace. For each source type that names a table, check that every SourceDocumentID exists in it. {{ n_trace }} types name a table; the one exception is {{ bad.orphans }} of the {{ bad.rows|count }} ledger rows typed {{ bad.source }}, whose payments do not exist. The type PayrollSummary names no table, because its key is a code between {{ summary_low|count }} and {{ summary_high|count }}.
- Plant an orphan in a copy of one worksheet, and show that your test finds it. Why is that a better test of the test than a clean result?
- Test one relationship the diagrams do not show, such as the order line key on an invoice line.
- Discuss: if the file declared and enforced its foreign keys, what would you still test? (Part III returns to this with the trace.)
- Discuss: what does a clean result tell you about the accuracy of the data? (Chapter 2's four dimensions help: this test speaks to consistency, not accuracy.)
