"""Appendix B Exercises - Solutions.pbip: the exercises of the appendix on publishing and security, built on a copy of
Charles River Reports at the end of Guided Tutorial B.1 (the reader's Save as copy).

Exercise B.1 adds object-level security to the role Cost Center Managers, as the TMDL view script the exercise
describes leaves it (the script is kept as a TMDL view tab), and its role checks run in the engine under the role: a
query that reads the secured column must fail, while the hours measures still evaluate. Exercise B.2 is an access
review in a DAX query tab; its checks reproduce the queries' results as scalars and run once more under the role.
"""

from __future__ import annotations

from pbibuild.model import MEASURES_TABLE, Measure, Query, query_table
from pbibuild.pbir import Page, Visual, col, meas, textbox
from pbibuild.project import Check
from pbibuild.reports import MONEY, Build, claim, keep, money, one, rows

from notes import appendix_b  # noqa: E402  (facts/ is on sys.path through pbibuild.reports)

KM = MEASURES_TABLE
M = lambda n: meas(KM, n)                 # noqa: E731
ROLE = "Cost Center Managers"
T = "\t"


def answer(name: str, x, y, w, h, lines: list, size: int = 10):
    return textbox(name, x, y, w, h, [("Model answer", True)] + lines, size=size)


def blank(expr: str) -> str:
    return f"IF ( ISBLANK ( {expr} ), \"blank\", \"not blank\" )"


# --- Exercise B.1 ----------------------------------------------------------------------------------------------------

def ex1(b: Build) -> None:
    y, m = b.year, b.model
    # (1) the measure and the page
    m.tables[KM].measures.append(Measure("Labor Cost", "SUM ( LaborTimeEntry[ExtendedLaborCost] )", MONEY,
                                         display_folder="Ex B.1"))
    page = b.report.add(Page("exb1", "Ex B.1"))
    page.add(Visual("laborByTitle", "tableEx", 20, 20, 700, 260, {"Values": [
        col("Employee", "JobTitle"), M("Manufacturing Hours"), M("Labor Cost")]}, title=f"Hours and labor cost by job "
        f"title, fiscal {y}", filters=[keep("lbtYear", col("Date", "Year"), [y])], sort=[(M("Labor Cost"), "Descending")]))
    # (2) the role scripted in TMDL view, its rules kept, the column's metadata permission set to none, applied
    role = next(r for r in m.roles if r.name == ROLE)
    role.columns = {"LaborTimeEntry": {"ExtendedLaborCost": "none"}}
    script = role.tmdl().rstrip("\n").split("\n")
    b.project.tmdl_scripts["Ex B.1"] = "createOrReplace\n\n" + "\n".join(T + line if line else "" for line in script) + "\n"
    titles = rows("SELECT e.JobTitle, SUM(CASE WHEN l.LaborType <> 'NonManufacturing' THEN l.RegularHours + l.OvertimeHours END), "
                  "SUM(l.ExtendedLaborCost) FROM LaborTimeEntry l JOIN Employee e ON e.EmployeeID = l.EmployeeID "
                  "WHERE substr(l.WorkDate, 1, 4) = ? GROUP BY 1 ORDER BY 3 DESC", str(y))
    total = sum(r[2] for r in titles)
    page.add(answer("exa1Answer", 740, 20, 520, 690, [
        "(2) The role's script, as TMDL view's Apply leaves it, is the TMDL view tab Ex B.1: the role's tablePermission "
        "rules are kept, and LaborTimeEntry gets columnPermission ExtendedLaborCost with metadataPermission: none. A "
        "role written from scratch with createOrReplace would replace the role and lose its row filters.",
        f"(3) As the Production Manager (View as, Other user employee004@charlesriver.example, role {ROLE}), the table on "
        "this page fails: Labor Cost reads a column the role cannot see, and the engine answers that column "
        "'ExtendedLaborCost' in table 'LaborTimeEntry' cannot be found or may not be used in this expression, so the "
        "visual shows an error, while the Plant page's hours visuals still work, since no measure on it reads the cost. With "
        f"the Finance role the page shows every job title's cost ({money(total)} in fiscal {y}).",
        "(4) Performance analyzer durations vary by machine; expect slightly longer durations under View as, because "
        "every query carries the role's filters.",
        "(5) Row-level security restricts rows, not columns: the managers must see the plant's employees and their "
        "hours, so the rows stay and only the column is hidden. The controller should keep cost measures off the "
        "pages the managers read (or in a finance report), so that no visual a manager opens fails."]))
    page.add(Visual("laborCostCard", "cardVisual", 20, 300, 700, 120, {"Data": [M("Labor Cost")]},
                    filters=[keep("lccYear", col("Date", "Year"), [y])],
                    objects={"value": [{"properties": {"labelDisplayUnits": {"expr": {"Literal": {"Value": "1D"}}}},
                                        "selector": {"id": "default"}}]}))
    page.expect = ["JobTitle", "Labor Cost", titles[0][0], money(titles[0][2]), money(total), "Model answer"]

    t, cy = "Exercise B.1", f"'Date'[Year] = {y}"
    b.check(t, f"{y} Labor Cost (no role)", round(total, 2), f"CALCULATE ( [Labor Cost], {cy} )", 0.01)
    for title, hours, cost in titles[:3]:
        f = f"{cy}, Employee[JobTitle] = \"{title}\""
        b.check(t, f"{y} Labor Cost, {title}", round(cost, 2), f"CALCULATE ( [Labor Cost], {f} )", 0.01)
        b.check(t, f"{y} Manufacturing Hours, {title}", round(hours, 2), f"CALCULATE ( [Manufacturing Hours], {f} )", 0.01)
    b.check(t, "column permissions set to None (object-level security)", 1,
            "COUNTROWS ( FILTER ( INFO.COLUMNPERMISSIONS (), [MetadataPermission] = 1 ) )", 0)
    # Under the role, the engine treats the column as if it did not exist: the query fails to compile. The measures
    # that do not read it still evaluate (blank: the Windows sign-in is not in the security table).
    sec = [("Exercise B.1", c) for c in [Check("labor cost of the column (must fail)", 0,
                                               "SUM ( LaborTimeEntry[ExtendedLaborCost] )", 0)]]
    meas_ = [("Exercise B.1", c) for c in [Check("Labor Cost (must fail)", 0, "[Labor Cost]", 0)]]
    hours = [("Exercise B.1", c) for c in [
        Check(f"{y} Manufacturing Hours evaluates for the role (blank: no employee is visible)", "blank",
              blank(f"CALCULATE ( [Manufacturing Hours], {cy} )")),
        Check("LaborTimeEntry rows visible", 0, "COUNTROWS ( LaborTimeEntry )", 0)]]
    finance = [("Exercise B.1", c) for c in [Check(f"{y} Labor Cost for Finance", round(total, 2),
                                                   f"CALCULATE ( [Labor Cost], {cy} )", 0.01)]]
    b.role_checks.update({
        "Ex B.1: Cost Center Managers, the secured column": (ROLE, None, sec, "ExtendedLaborCost"),
        "Ex B.1: Cost Center Managers, the Labor Cost measure": (ROLE, None, meas_, "Labor Cost"),
        "Ex B.1: Cost Center Managers, the hours": (ROLE, None, hours),
        "Ex B.1: Finance": ("Finance", None, finance)})


# --- Exercise B.2 ----------------------------------------------------------------------------------------------------

def ex2(b: Build) -> None:
    ctx = appendix_b.ex2(b.data, claim)
    m = b.model
    # (1) the employees, unrelated
    q = (Query.navigator("AccessEmployees", b.xlsx, 74, "Employee")
         .select(["EmployeeID", "EmployeeName", "Email", "JobTitle", "CostCenterID", "EmploymentStatus", "TerminationDate"])
         .types({"TerminationDate": "type date"}))
    m.add(query_table(q, summarize={"EmployeeID": "none", "CostCenterID": "none"}))
    # (2) to (4) the review, in its own query tab
    unmapped = ("FILTER ( CostCenter, ISEMPTY ( FILTER ( Security, Security[CostCenterID] = CostCenter[CostCenterID] ) ) )")
    twice = ("FILTER ( ADDCOLUMNS ( VALUES ( Security[UserPrincipalName] ), \"CostCenters\", CALCULATE ( COUNTROWS ( "
             "Security ) ) ), [CostCenters] > 1 )")
    look = "LOOKUPVALUE ( AccessEmployees[{}], AccessEmployees[EmployeeID], [EmployeeID] )"
    review = (
        "VAR Users =\n    ADDCOLUMNS (\n        Security,\n        \"EmployeeID\", LOOKUPVALUE ( AccessEmployees[EmployeeID], "
        "AccessEmployees[Email], Security[UserPrincipalName] )\n    )\n"
        "VAR Matched =\n    ADDCOLUMNS (\n        Users,\n" + ",\n".join(
            f"        \"{n}\", {look.format(c)}" for n, c in [("EmployeeName", "EmployeeName"), ("JobTitle", "JobTitle"),
                                                             ("EmploymentStatus", "EmploymentStatus"),
                                                             ("TerminationDate", "TerminationDate"),
                                                             ("OwnCostCenterID", "CostCenterID")]) + "\n    )\n"
        "RETURN\n    ADDCOLUMNS (\n        Matched,\n        \"Flag\",\n            SWITCH (\n                TRUE (),\n"
        "                ISBLANK ( [EmployeeID] ), \"No matching employee\",\n"
        "                [EmploymentStatus] <> \"Active\" || NOT ISBLANK ( [TerminationDate] ), \"Terminated\",\n"
        "                [OwnCostCenterID] <> Security[CostCenterID], \"Mapped to another cost center\",\n"
        "                BLANK ()\n            )\n    )")
    b.project.queries["Ex B.2"] = (
        "// Exercise B.2 (2): cost centers with no row in the security table\nEVALUATE\nSELECTCOLUMNS (\n    "
        f"{unmapped},\n    \"CostCenterID\", CostCenter[CostCenterID],\n    \"CostCenterName\", CostCenter[CostCenterName]\n)\n\n"
        f"// (3): users mapped to more than one cost center\nEVALUATE\n{twice}\n\n"
        "// (4): each user, the employee whose Email matches, and a flag\nEVALUATE\n" + review + "\n")
    # (5) and (6): the page and the note
    page = b.report.add(Page("exb2", "Ex B.2"))
    page.add(Visual("accessEmployees", "tableEx", 20, 20, 700, 690, {"Values": [
        col("AccessEmployees", "EmployeeName"), col("AccessEmployees", "JobTitle"), col("AccessEmployees", "EmploymentStatus"),
        col("AccessEmployees", "TerminationDate")]}, title="AccessEmployees, as any role member sees it"))
    page.add(answer("exa2Answer", 740, 20, 520, 690, [
        f"(2) One cost center has no row in the security table: {ctx['center']} ({ctx['cc']}), whose manager of record is "
        f"{ctx['an']} {ctx['title']}.",
        f"(3) None: {ctx['users']} users, {ctx['ccs']} cost centers.",
        "(4) Every user name matches the Email of an active employee (" + ", ".join(f"{i} {t}" for i, t in ctx["matches"]) +
        "), each in the cost center the table gives them, so no user is flagged.",
        f"(5) Viewed as the Sales Manager, the page lists every row of AccessEmployees, all {ctx['n_employees']} "
        "employees with their e-mail addresses and termination dates: no rule filters an unrelated table (the same "
        "reason the Customer table lists every customer for a user missing from the security table).",
        f"(6) The review found the unmapped {ctx['center']} and nothing else. Internal audit should run it whenever the "
        "security table changes and at least quarterly, with the controller's approval recorded. Before the file is "
        f"published, give AccessEmployees a rule of FALSE () in {ROLE}, or keep the table out of the published file."]))
    first = one("SELECT MIN(EmployeeName) FROM Employee")          # the table's first row, sorted by name
    page.expect = ["EmployeeName", "EmploymentStatus", first, "Model answer"]

    t = "Exercise B.2"
    b.check(t, "AccessEmployees rows", ctx["n_employees"], "COUNTROWS ( AccessEmployees )", 0)
    b.check(t, "cost centers with no row in the security table", ctx["center"],
            f"CONCATENATEX ( {unmapped}, CostCenter[CostCenterName], \", \" )")
    b.check(t, "users mapped to more than one cost center", 0, f"COUNTROWS ( {twice} )", 0)
    flagged = review.replace("RETURN\n    ADDCOLUMNS (", "RETURN\n    COUNTROWS ( FILTER ( ADDCOLUMNS (")[:-1] + \
        "), NOT ISBLANK ( [Flag] ) ) )"
    b.check(t, "users flagged (no employee, terminated, or another cost center)", 0, flagged.replace("\n", " "), 0)
    matched = ("COUNTROWS ( FILTER ( Security, NOT ISBLANK ( LOOKUPVALUE ( AccessEmployees[EmployeeID], "
               "AccessEmployees[Email], Security[UserPrincipalName], AccessEmployees[EmploymentStatus], \"Active\" ) ) ) )")
    b.check(t, "users matching an active employee's Email", len(ctx["matches"]), matched, 0)
    b.check(t, "the matched employees", ", ".join(str(i) for i, _ in sorted(ctx["matches"])),
            "CONCATENATEX ( Security, LOOKUPVALUE ( AccessEmployees[EmployeeID], AccessEmployees[Email], "
            "Security[UserPrincipalName] ), \", \", LOOKUPVALUE ( AccessEmployees[EmployeeID], AccessEmployees[Email], "
            "Security[UserPrincipalName] ), ASC )")
    claim(all(i for i, _ in ctx["matches"]), "every user matched an employee")
    # (5) under the role: nothing of Employee, everything of the unrelated table
    b.role_checks["Ex B.2: Cost Center Managers, the unrelated table"] = (ROLE, None, [("Exercise B.2", c) for c in [
        Check("AccessEmployees rows visible (no rule filters it)", ctx["n_employees"], "COUNTROWS ( AccessEmployees )", 0),
        Check("Employee rows visible (filtered by the role)", 0, "COUNTROWS ( Employee )", 0)]])


EXERCISES = [("B.1", ex1), ("B.2", ex2)]
