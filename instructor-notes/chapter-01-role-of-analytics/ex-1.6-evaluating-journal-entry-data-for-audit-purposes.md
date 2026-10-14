# Exercise 1.6: Evaluating Journal Entry Data for Audit Purposes

| | |
|---|---|
| Unit | Chapter 1: The Role of Analytics in Accounting |
| Item | Exercise 1.6 |
| Perspective | Auditing |
| Tools | Workbook browsing and written work |
| Time | About 50 minutes |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Before an auditor writes a query for management override of controls, the auditor asks whether the data can support the test. This exercise asks that question of the journal entry data in three common fraud risk indicators. The honest answer is different for each: one test is possible as it stands, one needs a table from outside the Accounting Core, and one has a field that looks right but carries almost no information. Students practice professional skepticism about the data itself. The tests are descriptive screens, and the exercise is the best preview in Part I of the audit chapters.

By the end, students can:

- list the columns of JournalEntry and GLEntry and say where the entry's lines are (chapter outcome 6);
- choose the columns that bear on who posted an entry, when, how much and what kind;
- judge, for each indicator, whether the data are sufficient, and name what is missing when they are not;
- sketch how ReversesJournalEntryID could support a test for window dressing at period end, and say what the data actually show.

**Competencies practiced.** CPA Evolution Core S2 M5 (risk of fraud and noncompliance) and M9 (audit procedures, analytical procedures and audit data analytics); IMA Data Literacy and Internal Control; IFAC IES 2 (f), audit, and IES 4 (a), professional skepticism and judgment; AACSB A5 part 5.2.

## Before you assign

- Students need CharlesRiver.xlsx. Exercise 1.5 (the source columns) is a good lead-in but not required.
- The exercise relies on these conditions, which you can see on the worksheets: JournalEntry has no lines, which are the GLEntry rows of type JournalEntry; JournalEntry.CreatedDate carries a time of day, and the times vary very little; amounts are in TotalAmount, and the approver's limit is not in JournalEntry but in Employee (MaxApprovalAmount); and ReversesJournalEntryID is filled for only one kind of entry.
- Do requirement 3 yourself on the worksheets before class. If you scan the time part of CreatedDate, you will see why the first indicator is not simple.
- Do not ask for queries or calculations. This exercise is a data assessment.

## How to run it

Individual work, with a short class discussion of requirement 3, which has the widest range of answers. For about 50 minutes: 10 minutes listing columns (requirement 1), 10 choosing them (requirement 2), 20 for the assessment (requirement 3) and 10 for the paragraph (requirement 4).

**Hints.** For requirement 3, if a student judges the after-hours indicator by whether CreatedDate exists, ask them to read the time of ten entries. For requirement 4, if the paragraph only defines reversals, ask what the auditor would select and compare.

**Collect** the written assessment and the paragraph.

## Step-by-step solution

### Requirement (1): List the columns

**Step 1. Open JournalEntry and GLEntry and read row 1.**

a. Click the **JournalEntry** worksheet tab. It has 11 columns: JournalEntryID, EntryNumber, PostingDate, EntryType, Description, TotalAmount, CreatedByEmployeeID, CreatedDate, ApprovedByEmployeeID, ApprovedDate and ReversesJournalEntryID.
b. Click the **GLEntry** worksheet tab. It has 16 columns: GLEntryID, PostingDate, AccountID, Debit, Credit, VoucherType, VoucherNumber, SourceDocumentType, SourceDocumentID, SourceLineID, CostCenterID, Description, CreatedByEmployeeID, CreatedDate, FiscalYear and FiscalPeriod.

**Check:** the lists are complete, and the student notes that JournalEntry has one row for each of 851 entries and no lines. The debits and credits are in GLEntry, in the 2,821 rows whose SourceDocumentType is JournalEntry. **Watch for:** a student who evaluates JournalEntry alone and never reaches the lines.

### Requirement (2): Choose the useful columns

**Step 2. Group the columns by the question they answer.**

| Question | Columns | What to look at |
|---|---|---|
| Who? | CreatedByEmployeeID, ApprovedByEmployeeID (and Employee for roles and limits) | The same person creating and approving; an approver without the authority |
| When? | CreatedDate, PostingDate, ApprovedDate | Weekend or after-hours creation; posting before or after creation |
| How much? | TotalAmount in JournalEntry; Debit and Credit in GLEntry | Round amounts; amounts just below a limit |
| What? | EntryType, Description | The kind of entry, and an unusual or vague description |

**Check:** each column named exists, and the answer explains how to use it. **Watch for:** GLEntry's own CreatedByEmployeeID and CreatedDate. For the rows of a journal entry they repeat the entry's creator, but for the rows of other types they are system values, so they say little about who prepared the posting.

### Requirement (3): Assess the three indicators

**Step 3. Take the indicators one at a time.** A model assessment in three to five sentences covers these points.

**Outside normal business hours.** CreatedDate carries a time of day, so the field exists. In this dataset the times barely vary: 845 entries at 08:00:00, and 6 entries at 10:00:00. No entry is created before 08:00 or after 17:00, so a time-of-day test with those hours would flag 0. PostingDate has no time. The date part of CreatedDate still gives the day of the week, and 17 entries were created on a weekend (Chapter 8 tests that). What would be needed for a real after-hours test: the system's entry log with true timestamps.

**Round-dollar amounts.** TotalAmount, and Debit and Credit on the lines, are enough. How many entries are round depends on the definition: 17 entries have a whole-dollar amount, and 4 are exact multiples of 1,000.

**Just below an approval threshold.** JournalEntry holds no threshold. The limit sits in Employee, by approver, so the test needs ApprovedByEmployeeID joined to MaxApprovalAmount. With that, 9 entries are above their approver's limit and 2 are within ten percent below it, and the near ones are ordinary rent entries. The data are sufficient once Employee is added, and the written authority policy should be confirmed.

![A mock of What the CreatedDate and ReversesJournalEntryID columns look like in JournalEntry, the evidence for requirements 3 and 4.](../figures/chapter-01-role-of-analytics/IF-01-6-A.pdf)

The approvers and their limits:

| Approver | Limit | Entries approved |
|---|---:|---:|
| Controller | 250,000 | 802 |
| Chief Financial Officer | 250,000 | 43 |
| Accounting Manager | 25,000 | 6 |

**Check:** each indicator gets its own verdict, with a reason and, where needed, a named missing item. **Watch for:** a blanket "yes, sufficient" or "no, insufficient". The strongest answers separate the three.

### Requirement (4): Write the window dressing paragraph

**Step 4. Explain how ReversesJournalEntryID could support the test.** A model paragraph: the column links an entry that reverses or corrects another entry to the original. Window dressing books an entry in the last days of a period that improves the reported result and reverses it just after the period closes. The test selects entries posted in the last days of a quarter or a year, uses ReversesJournalEntryID to find the entries that reverse them, and flags pairs that reverse within days after period end, especially when the amounts match or are large, and then reads the descriptions and the approvals.

What the data show, which students need not find: the column is filled for only 149 entries. Each is an Accrual Adjustment that settles or partly cleans up the residual of an earlier accrual, none equals its original in amount, the gap is 15 to 94 days, and 15 fall in the year after the original. In this dataset the column marks routine accrual cleanup, so a test would find pairs that the descriptions explain. A good student paragraph does not need to say this, but a student who checks the data and says so has gone further than required.

**Check:** the paragraph says what to select, what to compare and what would be a flag. It does not stop at defining a reversal.

## Expected results

| Quantity | Value | Where |
|---|---:|---|
| Columns in JournalEntry; in GLEntry | 11; 16 | Step 1 |
| Journal entries; GLEntry rows of type JournalEntry | 851; 2,821 | Step 1 |
| Clock times in CreatedDate | 2 | Step 3 |
| Entries created outside 08:00 to 17:00 | 0 | Step 3 |
| Entries created on a weekend | 17 | Step 3 |
| Whole-dollar entries; exact multiples of 1,000 | 17; 4 | Step 3 |
| Entries above their approver's limit | 9 | Step 3 |
| Entries within ten percent below the limit | 2 | Step 3 |
| Entries that reverse another; gap in days | 149; 15 to 94 | Step 4 |

The entries that are exact multiples of 1,000:

- JE-2024-000103: 360,000.00
- JE-2025-000028: 168,000.00
- JE-2026-000001: 280,000.00
- JE-2026-000115: 210,000.00

## What a strong answer says

- **Requirement (1).** Complete column lists, and the observation that the lines are in GLEntry.
- **Requirement (2).** Columns grouped by who, when, how much and what, each with a use.
- **Requirement (3).** A verdict for each indicator: after-hours has the field but little variation, round amounts are testable, and the threshold needs the approver's limit from Employee. Missing items are named.
- **Requirement (4).** A test design: what to select, what to compare, what to flag, and a limit.

A weak answer says that the data are sufficient because the columns exist, never opens the time part of CreatedDate, or defines reversals without a test.

## Common mistakes and how to respond

- **Judging a field by its name.** *Symptom:* "CreatedDate has time, so after-hours is testable". *Response:* ask them to read the times.
- **PostingDate treated as the only date.** *Symptom:* "no time, so after-hours is impossible". *Response:* point to CreatedDate.
- **No approval limit.** *Symptom:* "the threshold is not in the data". *Cause:* Employee is not opened. *Response:* ask where an approver's authority would be recorded.
- **Round defined as no cents.** *Symptom:* a different count from a classmate. *Response:* discuss the definition, and ask which one the policy would use.
- **Window dressing paragraph with no test.** *Symptom:* a definition of reversals. *Response:* ask what the auditor selects first.
- **The wrong end of the link.** *Symptom:* the reversed entry is flagged instead of the reversing one. *Response:* ask which row holds the column.
- **GLEntry's creator as the preparer.** *Response:* ask what it shows for a sales invoice.
- **An assessment of eight sentences.** *Response:* ask for the three verdicts first.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1: the columns | 20 | Both lists, and the lines in GLEntry | A list with columns missing |
| Requirement 2: the useful columns | 25 | Grouped by who, when, how much and what, each with a use | Names without uses |
| Requirement 3: the three verdicts | 35 | A verdict for each, with reasons and the missing item named | A blanket verdict, or one indicator missing |
| Requirement 4: the paragraph | 20 | Select, compare, flag, and a limit | A definition only |

## Extensions and discussion questions

- Name two further indicators of management override that the Accounting Core could support, and the columns for each.
- Choose the indicator that the data support worst, and write the data request that would fix it.
- Discuss: an entry that passes all three screens can still be improper. What would you read next? (Chapter 8 builds a score from several tests.)
- Discuss: how would the answer change for the other types in GLEntry, such as sales invoices?
- Discuss: should an auditor rely on a field that varies so little, and what would you ask the owner of the system?
