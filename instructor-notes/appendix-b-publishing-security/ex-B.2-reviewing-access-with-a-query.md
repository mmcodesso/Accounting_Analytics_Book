# Exercise B.2: Reviewing Access with a Query

| | |
|---|---|
| Unit | Appendix B: Publishing, Securing, and Sharing Reports |
| Item | Exercise B.2 |
| Perspective | Auditing |
| Tools | Power BI Desktop |
| Time | About 75 minutes |
| Solution file | AppendixB-exercises-pbi.zip: Appendix B Exercises - Solutions.pbip, page Ex B.2, the DAX query tab Ex B.2, and the query AccessEmployees |
| Release | First edition, dataset release v2026.1 (fiscal 2024–2026) |

## Purpose and learning outcomes

Tutorial B.1 Step 4 checked the security table by eye. Internal audit wants the check as a query it can run each quarter, so that every change to the table is tested against the employee records. The exercise is a small continuous-monitoring test in the style of Chapter 16: a list of authorizations compared with the master data, with exceptions flagged. The analytics type is diagnostic, and the last requirement is prescriptive: what to do about the table that the review itself added to the file.

Students can:

- import a table that stays unrelated on purpose (Requirement 1);
- find the cost centers a security table leaves out, and the users it maps twice (Requirements 2 and 3);
- match each user to an employee with `LOOKUPVALUE` and flag three failures (Requirement 4);
- show what a role leaves visible in a table that no relationship reaches (Requirement 5);
- report what the review found, how often to run it, and what to do before publishing (Requirement 6).

**Competencies practiced.** Appendix D maps this exercise to tests of internal controls, logical access and change management (CPA Evolution ISC M2) and information security (ISC M5); to the IMA competencies for securing data and for internal control; to IFAC IES 2 (i) on judging the adequacy of information and communications technology controls and IES 2 (g) on governance, risk management and internal control; and to AACSB A5 part 5.1.

## Before you assign

- **Files.** The copy of Charles River Reports after Tutorial B.1, with its roles and its Security table. The model answer is the DAX query tab Ex B.2, the page Ex B.2 and the query AccessEmployees of AppendixB-exercises-pbi.zip.
- **Data conditions.** Every employee has a distinct Email, so `LOOKUPVALUE` on Email finds one row. Of the 120 employees, 13 are terminated, with a TerminationDate. Security is hidden but can be queried in DAX query view, and it has no relationship to any table.
- **Verify first.** Security holds nine rows in the order of the tutorial, and Model view shows no relationship line to AccessEmployees. A relationship to CostCenter or Employee would let the role's rules filter the table, and Requirement (5) would show a false pass.

## How to run it

Pairs, about 75 minutes: 5 for Requirement (1), 10 for (2), 5 for (3), 20 for (4), 15 for (5), 15 for (6), 5 spare. Hold back the flag's logic until the pair has the three-layer shape. Hint 1, after 10 minutes on (2): "Security is not related to CostCenter. Which function asks whether any row of Security has this cost center?" Hint 2, for (4): "Build it in three layers: the matched EmployeeID, the looked-up columns, the flag." Collect the query tab, the page and the note.

## Step-by-step solution

### Requirement (1): The unrelated table

**Step 1. Import the employees.**

a. Choose **Home > Get data > Excel workbook**, select **T74_Employee**, and click **Transform Data**.
b. Rename the query `AccessEmployees`, and use **Choose Columns** to keep EmployeeID, EmployeeName, Email, JobTitle, CostCenterID, EmploymentStatus and TerminationDate.
c. Type TerminationDate as a date, and choose **Home > Close & Apply**.
d. Open **Model view** and confirm that no relationship line touches AccessEmployees.

**Check:** 120 rows in **Table view**, and an isolated table in Model view. **Watch for:** a relationship the file created on its own. Delete it.

### Requirement (2): The cost center with no row

**Step 2. List the cost centers that Security leaves out.**

a. In DAX query view, add a query tab and rename it `Ex B.2`.
b. Enter the first query of the model answer, comment line included.

```dax
// Exercise B.2 (2): cost centers with no row in the security table
EVALUATE
SELECTCOLUMNS (
    FILTER ( CostCenter, ISEMPTY ( FILTER ( Security, Security[CostCenterID] = CostCenter[CostCenterID] ) ) ),
    "CostCenterID", CostCenter[CostCenterID],
    "CostCenterName", CostCenter[CostCenterName]
)
```

c. Choose **Run**.

**Check:** one row, 8, Research and Development. Its manager of record is Melinda Murphy, a product analyst, and it has 4 employees. **Watch for:** `RELATEDTABLE`, which needs a relationship that Security does not have. An `EXCEPT` of the two lists of IDs also finds it and is accepted.

### Requirement (3): Users mapped twice

**Step 3. List the users with more than one cost center.**

a. Add the second query below the first, and run it.

```dax
// (3): users mapped to more than one cost center
EVALUATE
FILTER ( ADDCOLUMNS ( VALUES ( Security[UserPrincipalName] ), "CostCenters", CALCULATE ( DISTINCTCOUNT ( Security[CostCenterID] ) ) ), [CostCenters] > 1 )
```

**Check:** no rows, because the table has nine users and nine cost centers. **Watch for:** an empty result that is empty because the query is wrong. In a copy of the Security table, add a second row for one user with another cost center, and the query lists that user with 2. A row that repeats an existing mapping exactly is not listed, because the query counts each user's distinct cost centers, not rows.

### Requirement (4): The matching and the flag

**Step 4. Build the review in three layers.**

a. Add the third query below the second.
b. Read it from the inside out. Users lists each user once, with the cost centers mapped to the user and the EmployeeID whose Email matches, Matched looks up five more columns by that ID, and the last layer adds the flag, which marks a user if any of those cost centers is not the employee's own.
c. Choose **Run**.

```dax
// (4): one row per user, the employee whose Email matches, and a flag
EVALUATE
VAR Users =
    ADDCOLUMNS (
        VALUES ( Security[UserPrincipalName] ),
        "CostCenterIDs", CALCULATE ( CONCATENATEX ( VALUES ( Security[CostCenterID] ), Security[CostCenterID], ", ", Security[CostCenterID], ASC ) ),
        "EmployeeID", LOOKUPVALUE ( AccessEmployees[EmployeeID], AccessEmployees[Email], Security[UserPrincipalName] )
    )
VAR Matched =
    ADDCOLUMNS (
        Users,
        "EmployeeName", LOOKUPVALUE ( AccessEmployees[EmployeeName], AccessEmployees[EmployeeID], [EmployeeID] ),
        "JobTitle", LOOKUPVALUE ( AccessEmployees[JobTitle], AccessEmployees[EmployeeID], [EmployeeID] ),
        "EmploymentStatus", LOOKUPVALUE ( AccessEmployees[EmploymentStatus], AccessEmployees[EmployeeID], [EmployeeID] ),
        "TerminationDate", LOOKUPVALUE ( AccessEmployees[TerminationDate], AccessEmployees[EmployeeID], [EmployeeID] ),
        "OwnCostCenterID", LOOKUPVALUE ( AccessEmployees[CostCenterID], AccessEmployees[EmployeeID], [EmployeeID] )
    )
RETURN
    ADDCOLUMNS (
        Matched,
        "Flag",
            VAR ThisUser = Security[UserPrincipalName]
            VAR OwnCenter = [OwnCostCenterID]
            VAR OtherCenters =
                COUNTROWS ( FILTER ( Security, Security[UserPrincipalName] = ThisUser && Security[CostCenterID] <> OwnCenter ) )
            RETURN
                SWITCH (
                    TRUE (),
                    ISBLANK ( [EmployeeID] ), "No matching employee",
                    [EmploymentStatus] <> "Active" || NOT ISBLANK ( [TerminationDate] ), "Terminated",
                    OtherCenters > 0, "Mapped to another cost center",
                    BLANK ()
                )
    )
```

![A mock of the result of query (4), the review a student runs every quarter, so an instructor sees what a clean review looks like.](../figures/appendix-b-publishing-security/IF-AB-2-A.pdf)

**Check:** nine rows, the Flag blank in every row. The matched employees are 1 (Chief Executive Officer), 6 (Sales Manager), 7 (Warehouse Manager), 4 (Production Manager), 10 (Purchasing Manager), 5 (Accounting Manager), 11 (Customer Service Manager), 12 (Marketing Manager), 14 (Design Services Manager). Each is in the cost center the table gives. **Watch for:** a flag that passes here and fails elsewhere. Every user is clean on this data, so a flag with a missing or misordered test also reads blank. Test it with three rows added to a copy of Security:

| Row added | Expected flag | Why |
|---|---|---|
| `employee083@charlesriver.example` on cost center 2 | Terminated | Cassandra Cardenas, sales representative, terminated 2024-06-21 |
| `employee007@charlesriver.example` on cost center 2 | Mapped to another cost center | Robert Fisher, warehouse manager, own cost center 3 |
| `employee06@charlesriver.example` on cost center 2 | No matching employee | no Email matches |

The order of the SWITCH matters: with the Terminated test first, the row that matches no employee reads Terminated, because a blank status is not "Active". A security table typed with the cost centers in sequence is caught the same way: 2 users read Mapped to another cost center, and Requirement (2) names Design Services as the cost center left out.

### Requirement (5): What a manager can see

**Step 5. View as the Sales Manager.**

a. Add a page named `Ex B.2` with a **Table** visual of EmployeeName, JobTitle, EmploymentStatus and TerminationDate from AccessEmployees, titled "AccessEmployees, as any role member sees it".
b. Choose **Modeling > View as**, select **Other user**, type `employee006@charlesriver.example`, select **Cost Center Managers**, and click **OK**.
c. Read the table, then choose **Stop viewing**.

![A mock of the page Ex B.2 viewed as the Sales Manager, the leak that requirement (5) asks students to find.](../figures/appendix-b-publishing-security/IF-AB-2-B.pdf)

**Check:** all 120 employees appear, with their termination dates, while Employee itself shows only the 8 of the Sales cost center. No rule filters a table that no relationship reaches. In **Manage roles**, a rule of `FALSE ()` on AccessEmployees for Cost Center Managers empties it for the role, though its name and columns stay visible, which object-level security would hide too. Keeping the table out of the published file removes it. **Watch for:** the review run under a manager's role. It sees one cost center and one row of Security, so Requirement (2) returns nothing and the gap disappears. Run the review as the file's author.

### Requirement (6): The note

**Step 6. Report.** Mark the note against "What a strong answer says".

**Instructor check.** In DAX query view, run this and compare it with the Expected results.

```dax
EVALUATE ROW ( "Unmapped", CONCATENATEX ( FILTER ( CostCenter, ISEMPTY ( FILTER ( Security, Security[CostCenterID] = CostCenter[CostCenterID] ) ) ), CostCenter[CostCenterName], ", " ), "Users matched", COUNTROWS ( FILTER ( Security, NOT ISBLANK ( LOOKUPVALUE ( AccessEmployees[EmployeeID], AccessEmployees[Email], Security[UserPrincipalName], AccessEmployees[EmploymentStatus], "Active" ) ) ) ), "AccessEmployees rows", COUNTROWS ( AccessEmployees ) )
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Cost center with no row in the security table | 8 Research and Development | 2 |
| Its manager of record; its employees | Melinda Murphy, Product Analyst; 4 | 2 |
| Users mapped to more than one cost center | none | 3 |
| Users in the table; matched to an active employee | 9; 9 | 4 |
| Users flagged | 0 | 4 |
| Test row `employee083@charlesriver.example` | Terminated | 4 |
| Test row `employee007@charlesriver.example` | Mapped to another cost center | 4 |
| Test row `employee06@charlesriver.example` | No matching employee | 4 |
| Typed in sequence: users flagged; cost center left out | 2; Design Services | 4 |
| AccessEmployees rows a manager sees; terminated among them | 120; 13 | 5 |
| Employee rows the Sales Manager sees | 8 | 5 |

> **Instructor notes, Exercise B.2 (SQL twins; the CR16 reference model):** (2) one cost center, Research and Development (8), whose manager of record is a Product Analyst. Security is unrelated, so RELATEDTABLE cannot be used; EXCEPT ( VALUES ( CostCenter\[CostCenterID\] ), VALUES ( Security\[CostCenterID\] ) ), or a FILTER on CostCenter with a COUNTROWS ( FILTER ( Security, ... ) ) = 0 test, finds it. (3) none: nine users, nine cost centers. Counting each user's distinct cost centers keeps a mapping typed twice from reading as two. (4) all nine names match the Email of an active employee (1 Chief Executive Officer, 6 Sales Manager, 7 Warehouse Manager, 4 Production Manager, 10 Purchasing Manager, 5 Accounting Manager, 11 Customer Service Manager, 12 Marketing Manager, 14 Design Services Manager), each in the cost center the table gives them, so no user is flagged. One row per user starts from VALUES ( Security\[UserPrincipalName\] ), with LOOKUPVALUE ( AccessEmployees\[EmployeeID\], AccessEmployees\[Email\], Security\[UserPrincipalName\] ) inside ADDCOLUMNS, and flags a user when any of their cost centers is not their own. (5) every row of AccessEmployees, all 120 employees with their addresses and termination dates, because no rule filters an unrelated table (the same reason the Customer table still lists every customer for a user missing from the security table). A rule of FALSE () on the table for Cost Center Managers empties it for the role, though its name and columns stay visible (object-level security hides them too), and keeping the table out of the published file removes it. Run the review whenever the table changes and at least quarterly, with the controller's approval recorded.

## What a strong answer says

- **(2) to (4)** The review found one cost center without a user, Research and Development, which agrees with Tutorial B.1, where no department manager sees it until the controller names its manager. It found no user mapped twice and no user who is unmatched, terminated or in another cost center.
- **(5)** A manager sees every row of AccessEmployees, including the e-mail addresses and termination dates of 120 employees, because no rule or relationship filters it. The fix is leaving the table out of the published file, or a rule of `FALSE ()` for the role, which empties the table but leaves its name and columns visible.
- **(6)** Run the review whenever the security table changes and at least quarterly, with the controller's approval recorded, and by someone other than the person who maintains the table.
- The limits: the review tests status and cost center on the day it runs, and Email stands in for the sign-in name, which the service may spell differently.

A strong answer reports a clean review without calling it proof, and ties the frequency to the events that change the table. A weak one lists the query results and stops.

## Common mistakes and how to respond

- **`RELATEDTABLE`.** *Symptom:* the query fails. *Response:* ask whether Security is related to CostCenter.
- **A flag nobody tested.** *Symptom:* "zero flagged, so it works". *Response:* ask for the test rows and their flags.
- **The wrong order.** *Symptom:* the unmatched test row reads Terminated. *Response:* ask what a missing employee's status is.
- **Rows counted, not cost centers.** *Symptom:* a user whose mapping was typed twice is listed in (3), or appears twice in (4). *Response:* ask what (3) and (4) ask about, a cost center or a row.
- **An auto-created relationship.** *Symptom:* the Sales Manager sees 8 employees of the 120, and the student reports no leak. *Response:* ask Model view what reaches the table.
- **The review run under a role.** *Symptom:* an empty list of unmapped cost centers. *Response:* ask which rows the role hides.
- **Findings ignored.** *Symptom:* a table typed in sequence, 2 users flagged, and a note that says all is well. *Response:* ask who sees what.
- **A one-time review.** *Symptom:* a note with no frequency. *Response:* ask when the table next changes.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Requirement 1 | 10 | Seven columns, typed, unrelated | A related table |
| Requirement 2 | 15 | The cost center left out, by name | The ID only |
| Requirement 3 | 10 | The query, and its empty result explained | The query without a test |
| Requirement 4 | 25 | One row per user, the lookups, a flag with the three tests in order | A flag with fewer tests |
| Requirement 5 | 15 | All employees seen, the reason, a fix | The leak found without a fix |
| Requirement 6 | 25 | Findings, a frequency with a trigger, the fix before publishing | One of the three |

## Extensions and discussion questions

- Add a measure that counts the flagged users, so the review has a number of record, and place it on a page of Audit Monitoring as a rule test of Chapter 16.
- Add the job title to the flag: it reads "not a manager" when the title does not end in Manager. Say what the test finds on the access review of Tutorial B.1.
- Discuss: who should run the review, the person who maintains the table, the person who approves it, or internal audit?
- Discuss: Email stands in for the sign-in name. What does the review miss if the two differ?
