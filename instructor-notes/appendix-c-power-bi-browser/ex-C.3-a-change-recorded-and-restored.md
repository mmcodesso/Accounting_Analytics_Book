# Exercise C.3: A Change, Recorded and Restored

| | |
|---|---|
| Unit | Appendix C: Power BI in the Browser |
| Item | Exercise C.3 |
| Perspective | Auditing |
| Tools | The Power BI service in a browser (the model editor, DAX query view and version history) |
| Time | About 45 minutes |
| Solution file | No solution file, because the projects open only in Desktop. The model answer is Steps 1 to 5 of this guide, built from Guided Tutorial C.3 (the Revenue measure and its test in Tests.dax) and the Checks tab of Chapter13-exercises-pbi.zip for the fiscal totals. Version history cannot be run outside a Pro account, so its dialog is described in general terms |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Internal audit wants evidence that a model built in the browser can be returned to a known state after a mistake. The service saves every change as it is made, with no undo, so the only way back is a saved version or a formula typed again. The exercise makes one controlled change to the Revenue measure and shows what detects it. The test in Tests.dax changes, and the report's cards do not, because they read columns and not the measure. A change log then records what happened. The analytics type is diagnostic, with a control point at the end: version history compared with a project under version control.

Students can:

- save a version before a change, so there is a state to return to (Requirement 1);
- run the same test before, during and after a change and compare (Requirements 2 to 4);
- restore a model and show by the test that it is restored (Requirement 4);
- write a change log entry and say what version history records and leaves out (Requirement 5).

**Competencies practiced.** Appendix D maps this exercise to CPA Evolution Core S2 M4 (information technology and IT controls) and ISC M2 (tests of internal controls, logical access and change management); to the IMA competencies for internal control and data governance; to IFAC IES 2 (g) on governance, risk management and internal control and (i); and to AACSB A5 parts 5.1 to 5.3.

## Before you assign

- **Files and software.** A browser and the student's model after Tutorial C.3, in Editing mode, with Tests.dax saved. A Pro license is needed for version history. Without one, students do Requirements (2), (3) and (5), and for (4) retype the formula and run the third test.
- **Data conditions.** ListAmount, Quantity times BaseListPrice, exceeds LineTotal in every fiscal year, so the changed test is higher in all three rows.
- **Verify first, in a live tenant.** The author's test read the two commands, **Save to version history** and **Version history**, on the **File** menu of a Pro account, but not their windows. Check that a description box exists, what the restore control is called, and what a free account's **File** menu shows.
- **Order.** Do this exercise after C.1 and C.2: it changes the Revenue measure that C.1's query reads.

## How to run it

Individual, about 45 minutes: 5 for (1), 5 for (2), 10 for (3), 10 for (4), 15 for (5). Hold back the comparison with Chapter 16 until the log is drafted. Hint 1, after 10 minutes on (3): "Which pages use the measure?" Hint 2, for (5): "Who changed it, and why? Does the version tell you?" Collect the three results and the log entry.

## Step-by-step solution

### Requirement (1): Save a version

**Step 1. Save the model's current state.**

a. In the model editor, choose **File > Save to version history**.
b. If the window offers a description, type `Before Exercise C.3`.
c. Choose **File > Version history** and confirm that a version is listed.

**Check:** a version dated now. **Watch for:** a student who saves after the change, or not at all: the model then has no earlier state to return to, and the formula must be retyped.

### Requirement (2): The test before the change

**Step 2. Run the test.**

a. Select **DAX query view** and paste the test from Tests.dax.
b. Click **Run**, and record the fiscal 2026 row.

```dax
EVALUATE
SUMMARIZECOLUMNS (
    SalesInvoice[FiscalYear],
    "Revenue", ROUND ( [Revenue], 2 )
)
ORDER BY SalesInvoice[FiscalYear]
```

**Check:** fiscal 2026 reads $29,756,420.08. The instructor check ignores the measure:

```dax
EVALUATE
ROW ( "Line total, current fiscal year", ROUND ( CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ), SalesInvoice[FiscalYear] = 2026 ), 2 ) )
```

### Requirement (3): The change and what it shows

**Step 3. Change the measure and run the test again.**

a. In the **Data** pane, select Revenue in Key Measures.
b. In the formula bar, replace LineTotal with ListAmount and press Enter.
c. Return to DAX query view and click **Run**.

```dax
Revenue = SUM ( SalesInvoiceLine[ListAmount] )
```

**Check:** every row now equals its list amount: fiscal 2026 reads $33,589,137.45, higher by $3,832,717.37, the price reductions and discounts. Open the Sales and Discounts page: its cards still read the old revenue, because they sum the columns. The test is the only place the change shows. **Watch for:** a result that has not moved, which usually means the formula was not committed with Enter; look at the formula bar.

![The three runs of the test, and what the pages did and did not show.](../figures/appendix-c-power-bi-browser/IF-AC-3-A.pdf)

### Requirement (4): The restore

**Step 4. Restore the model and prove it.**

a. Choose **File > Version history**.
b. Select the version of Requirement (1) and restore it. The labels of the version history window were not read in the author's test.
c. Run the test a third time.

Without a Pro license, retype the formula in the formula bar and press Enter:

```dax
Revenue = SUM ( SalesInvoiceLine[LineTotal] )
```

**Check:** the third run equals the first, $29,756,420.08. **Watch for:** a version saved after the change, which restores the changed model, and a restore that is never tested: only the third run is evidence.

### Requirement (5): The change log

**Step 5. Write the entry and the comparison.** The model entry has five rows: what changed (the Revenue measure, from LineTotal to ListAmount), when (the student's date and time), the results ($29,756,420.08, $33,589,137.45, $29,756,420.08), how it was restored, and by whom.

**Check:** the comparison says that version history records the model as it stood at each saved version, keeps only the last five, names only the last person to change each, and needs a Pro license. It does not record what changed or why, and nothing reviews a change before it takes effect. A Power BI project under version control, Chapter 16's change control, records every change with its author and message and can be reviewed before it is merged.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Test, fiscal 2026, before the change | $29,756,420.08 | 2 |
| Test after the change | $33,589,137.45 | 3 |
| Difference | $3,832,717.37 | 3 |
| Test after the restore | $29,756,420.08 | 4 |
| Test after the change, each year | 2024: $30,596,029.91; 2025: $33,030,575.85; 2026: $33,589,137.45 | 3 |

> **Instructor notes, Exercise C.3:** the test's fiscal 2026 revenue is 29,756,420.08 before the change, 33,589,137.45 with ListAmount (higher by 3,832,717.37, the price reductions and discounts), and 29,756,420.08 again after the restore. Version history records the model's state, not who changed it or why, keeps only the last few versions, and needs a Pro license; a Power BI project under version control (Chapter 16) records every change with its author and message and can be reviewed before it is merged.

## What a strong answer says

- **(1), (2)** A version before the change and a baseline result.
- **(3)** The test moved in all three years and the pages did not, with the reason: the cards read columns. A strong answer adds that a report built on the measure would have changed on every page at once.
- **(4)** The restore proved by the third run, not by the version history window.
- **(5)** A complete entry, and a comparison that names what version history leaves out: what and why, review, and more than five versions.

## Common mistakes and how to respond

- **No version before the change.** *Symptom:* nothing to restore. *Response:* ask what the model's last known state was.
- **The page checked, not the test.** *Symptom:* "nothing changed". *Response:* ask which visuals read the measure.
- **The restore untested.** *Symptom:* a log that says restored with no third result. *Response:* ask what shows it.
- **Version history credited with the reason.** *Symptom:* a log that cites the version as evidence of who and why. *Response:* ask what the version records.
- **A lost test.** *Symptom:* an empty query tab after the model is reopened. *Response:* the tab is discarded on close; paste it back from Tests.dax.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 10 | A version saved before the change | Saved after |
| Requirement 2 | 15 | Baseline result recorded | Result without the query |
| Requirement 3 | 25 | Result, difference and why the pages did not change | Result only |
| Requirement 4 | 20 | Restored and proved by a third run | Restored, not proved |
| Requirement 5 | 30 | Complete log and a correct comparison | Log without the comparison |

## Extensions and discussion questions

- Rerun the query of Exercise C.1 after the change. Which of its columns move?
- Point a card at the Revenue measure and repeat the exercise. What do the pages show now?
- Discuss: version history keeps five versions. Is it a control or a convenience?
- Discuss: three people edit one model in Editing mode. What rules would you set?
