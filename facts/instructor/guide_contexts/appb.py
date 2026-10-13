"""Appendix B's instructor guides: the values the guides state, and the claims their wording makes.

The appendix on publishing, securing, and sharing reports has two guided tutorials (B.1 in Desktop, B.2 in the service) and two
exercises that extend the security model of Tutorial B.1: object-level security on a pay column (B.1) and an access review in
DAX query view (B.2). The contexts do the same four jobs as Chapters 13 to 16:

- they check, with claim(), every table and column the guides name and every statement about the data that another dataset could
  falsify, so a roll flags the wording instead of leaving it stale,
- they supply what each exercise's steps need beyond the registered notes (appendix_b.t1 for the tutorial, appendix_b.ex2 for
  Exercise B.2, which has the only registered exercise note): above all the symptom of each wrong version a guide names (a role
  written from scratch, a column hidden by a rule that was never applied, a security table typed with the cost centers in
  sequence, a review run under the role it tests), computed read-only on the dataset the way the model would show it,
- they quote the DAX, the TMDL script and the visual titles of the model answer from the solution project itself
  (outputs/companion/solutions/AppendixB-exercises-pbi), so a quoted step cannot drift from the file the instructor opens: a quote
  that is not found in the project is a failed claim,
- they supply the chapter note's counts (exercises, questions, tutorial steps, checks) from the appendix's own files.

Keys: appB.chapter (the chapter note), appB.g1 (Exercise B.1) and appB.g2 (Exercise B.2, used next to the registered note
appendix_b.ex2). The tutorials' values come from the registered note appendix_b.t1.

What the project proves and what only Desktop shows: the project encodes the model, the roles (TMDL), the Power Query steps and the
visual structure, and its Checks tab (DAX query view) runs without a role. A role row of the Checks tab ("as employee006 ...")
reproduces the role's three rules as CALCULATE filters with the user's name typed in, so it proves the rules' logic and the numbers;
the OLS row reads INFO.COLUMNPERMISSIONS, so it proves that the column permission is saved. What View as shows (the bar, the error
in a visual, the empty Plant page) is visible only in Desktop, or in the service for Test as role.
"""

from __future__ import annotations

import re
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import schema
from guide_contexts.ch09 import and_list
from guide_contexts.ch13 import _block, version
from notes import appendix_b as nb

REPO = Path(__file__).resolve().parents[3]
APPENDIX = REPO / "appendices" / "b-publishing-security"
PROJECT = REPO / "outputs" / "companion" / "solutions" / "AppendixB-exercises-pbi" / "Appendix B Exercises - Solutions"
MODEL = PROJECT / "Appendix B Exercises - Solutions.SemanticModel"
REPORT = PROJECT / "Appendix B Exercises - Solutions.Report"

SCHEMA = {
    "CostCenter": ["CostCenterID", "CostCenterName", "ManagerID"],
    "Employee": ["EmployeeID", "EmployeeName", "Email", "JobTitle", "CostCenterID", "EmploymentStatus", "TerminationDate"],
    "LaborTimeEntry": ["EmployeeID", "WorkDate", "LaborType", "RegularHours", "OvertimeHours", "ExtendedLaborCost"],
    "GLEntry": ["AccountID", "CostCenterID", "PostingDate", "Debit", "Credit"],
    "BudgetLine": ["AccountID", "CostCenterID", "FiscalYear", "BudgetAmount"],
    "SalesInvoice": ["SalesInvoiceID", "InvoiceDate"],
    "SalesInvoiceLine": ["SalesInvoiceID", "ItemID", "LineTotal"],
    "Item": ["ItemID", "ItemGroup", "ListPrice"],
    "Account": ["AccountID", "AccountNumber", "AccountType", "AccountSubType"],
}
ROLES = ["Cost Center Managers", "Finance"]
TYPO = "employee06@charlesriver.example"          # Exercise B.2's test row: a name that matches no employee's Email
PRODUCTION_CC = 4


# --- helpers ---------------------------------------------------------------------------------------------------------

def need(d, claim, *tables: str) -> None:
    """Claims that each table and the columns the guides name are in the database."""
    schema(d, claim, {t: SCHEMA[t] for t in (tables or SCHEMA)})


def _model_text(relative: str) -> str:
    return (MODEL / relative).read_text(encoding="utf-8")


def table_m(name: str) -> list[str]:
    """The M of a loaded table's partition in the solution project, one stripped line per step."""
    return _block(_model_text(f"definition/tables/{name}.tmdl"), "source =")


def measure_table() -> dict[str, str]:
    """Every measure of the project as the formula bar reads it: `Name = expression`, the body dedented."""
    out: dict[str, str] = {}
    for path in sorted((MODEL / "definition" / "tables").glob("*.tmdl")):
        lines = path.read_text(encoding="utf-8").split("\n")
        for i, line in enumerate(lines):
            m = re.match(r"^\tmeasure (?:'([^']+)'|(\S+)) =(.*)$", line)
            if not m:
                continue
            name, first = m.group(1) or m.group(2), m.group(3).strip()
            body, j = [], i + 1
            while j < len(lines) and lines[j].startswith("\t\t\t"):
                body.append(lines[j][3:].rstrip())
                j += 1
            out[name] = f"{name} = {first}" if first and not body else f"{name} =\n" + "\n".join(body)
    return out


def measure(claim, name: str) -> str:
    found = measure_table().get(name)
    claim(found is not None, f"the solution project has the measure {name}")
    return found or ""


def check_expr(claim, section: str, label: str) -> str:
    """The DAX expression of one row of the project's Checks tab (DAX query view), found by its section and label."""
    text = _model_text("DAXQueries/Checks.dax")
    m = re.search(r'"Section", "' + re.escape(section) + r'", "Check", "' + re.escape(label)
                  + r'", "Expected", .*?, "Actual", (.*?), "Agrees"', text)
    claim(m is not None, f"the Checks tab has the row {label!r} of {section}")
    return m.group(1) if m else ""


def lay_out(expr: str) -> str:
    """A Checks-tab expression (one line in the file) broken after its CALCULATE and before each FILTER, nothing else changed."""
    out = expr.strip().replace("CALCULATE ( ", "CALCULATE (\n    ", 1)
    out = re.sub(r", FILTER \(", ",\n    FILTER (", out)
    return re.sub(r" \)$", "\n)", out)


def check_count(section_prefix: str, label_prefix: str = "") -> int:
    text = _model_text("DAXQueries/Checks.dax")
    return len(re.findall(r'"Section", "' + re.escape(section_prefix) + r'[^"]*", "Check", "' + re.escape(label_prefix), text))


def visual_title(claim, page: str, name: str) -> str:
    """The title of a visual of the solution project's report page, as Desktop shows it."""
    import json
    try:
        data = json.loads((REPORT / "definition" / "pages" / page / "visuals" / name / "visual.json").read_text(encoding="utf-8"))
        title = data["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
        title = title.strip("'").replace("''", "'")
    except (OSError, KeyError, IndexError, ValueError):
        title = ""
    claim(title != "", f"the visual {name} of page {page} in the solution project has a title")
    return title


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (APPENDIX / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise [A-Z]\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def step_count(n: int) -> int:
    text = (APPENDIX / f"_tutorial-0{n}.qmd").read_text(encoding="utf-8")
    return len(re.findall(r"^\*\*Step \d+\.", text, re.M))


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import package
    import source
    text = (APPENDIX / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("appendices/b-publishing-security/_multiple-choice.qmd", "mcq", r"<!--\s*Answer key, (?:Chapter|Appendix) B\b")
    letters, _ = package.answer_key(comment)
    key = {i: a for i, a in enumerate(letters, 1)}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def labor_by_title(d, year: int, centers: list[int] | None = None) -> list[dict]:
    """Exercise B.1 (1): Manufacturing Hours (direct and indirect time) and Labor Cost (all time) by job title of the year's
    work dates, largest cost first; hours are None for a title with no manufacturing time. `centers` limits it to the employees
    of those cost centers, which is what a role that filters Employee shows."""
    where = f"AND e.CostCenterID IN ({','.join(map(str, centers))})" if centers else ""
    return [dict(title=t, hours=h, cost=c) for t, h, c in d.q(
        "SELECT e.JobTitle, SUM(CASE WHEN l.LaborType <> 'NonManufacturing' THEN l.RegularHours + l.OvertimeHours END), "
        "SUM(l.ExtendedLaborCost) FROM LaborTimeEntry l JOIN Employee e ON e.EmployeeID = l.EmployeeID "
        f"WHERE substr(l.WorkDate, 1, 4) = ? {where} GROUP BY 1 ORDER BY 3 DESC", str(year))]


def flag(emp, cc: int) -> str | None:
    """Exercise B.2 (4)'s flag, in the order of the model answer's SWITCH."""
    if emp is None:
        return "No matching employee"
    if emp["status"] != "Active" or emp["terminated"]:
        return "Terminated"
    if emp["cc"] != cc:
        return "Mapped to another cost center"
    return None


def query_blocks(claim) -> dict[str, str]:
    """The three queries of the model answer's DAX query tab Ex B.2, keyed by requirement number, comment lines included."""
    text = _model_text("DAXQueries/Ex B.2.dax").strip()
    parts = re.split(r"\n\n(?=// )", text)
    claim(len(parts) == 3, "the DAX query tab Ex B.2 of the solution project holds the three queries of requirements (2) to (4)")
    return {k: p.strip() for k, p in zip(("2", "3", "4"), parts)}


# --- the chapter note ------------------------------------------------------------------------------------------------

@context("appB.chapter")
def chapter(d, claim):
    need(d, claim)
    ex = exercise_counts()
    claim(ex == {"managerial": 1, "auditing": 1}, "the appendix has one managerial and one auditing exercise")
    n_q, longest = mcq_facts()
    claim(n_q == 8, "the appendix has eight multiple-choice questions (the key's rationales and the note's plans use their numbers)")
    claim(version() != "", "Tutorial 13.1 names the Power BI Desktop version")
    claim(MODEL.is_dir(), "the solution project of Appendix B is in outputs/companion/solutions")
    roles = sorted(p.stem for p in (MODEL / "definition" / "roles").glob("*.tmdl"))
    claim(roles == sorted(ROLES), "the solution project has the roles Cost Center Managers and Finance")
    claim(step_count(1) == 11 and step_count(2) == 5, "Tutorial B.1 has eleven steps and Tutorial B.2 has five")
    review = nb.access_review(d)
    emails = nb.by_email(d)
    claim(len(review["terminated"]) == 3, "three of the ten managers of record are terminated")
    claim(len(review["flagged"]) == 4, "four cost centers have a flagged manager of record (three terminated, one an analyst)")
    claim(nb.FORMER in emails, "the terminated employee recorded as manager of Sales has an Email")
    s = nb.view_as(d, nb.SALES)
    p = nb.view_as(d, nb.PRODUCTION)
    company = nb.company_net_income(d)
    claim(s["ni"] > 2 * company, "the Sales Manager's net income is more than twice the company's")
    unmapped = [cc for cc in nb.centers(d) if cc not in {c for _, c in nb.SECURITY}]
    claim(len(unmapped) == 1, "one cost center is left out of the security table")
    # The Item rule is the only rule that restricts sales: no relationship joins the invoice lines to CostCenter or Employee,
    # so without it a person added to the role by mistake sees every sale.
    rel = _model_text("definition/relationships.tmdl")
    claim("SalesInvoiceLine.CostCenterID" not in rel and "SalesInvoiceLine.EmployeeID" not in rel
          and "toColumn: CostCenter" not in "".join(l for l in rel.split("relationship ") if "fromColumn: SalesInvoiceLine" in l),
          "the invoice lines are not related to CostCenter or Employee, so only the rule on Item restricts sales")
    hours_all = d.one("SELECT SUM(RegularHours + OvertimeHours) FROM LaborTimeEntry WHERE LaborType <> 'NonManufacturing' "
                      "AND substr(WorkDate, 1, 4) = ?", str(d.C))
    claim(abs(hours_all - p["hours"]) < 0.005,
          "the Manufacturing cost center holds all the year's manufacturing hours, so a role that leaves Employee unfiltered shows the Sales Manager the plant's hours")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE CostCenterID IS NULL") > 0,
          "some ledger lines have no cost center, so VALUES of CostCenterName would add a blank member that DISTINCT leaves out")
    role_row = lay_out(check_expr(claim, "Guided Tutorial B.1", "as employee006 (Sales Manager): Cost Centers Shown"))
    dax_role = ('EVALUATE\nROW (\n    "Cost centers shown as the Sales Manager",\n    ' + role_row.replace("\n", "\n    ") + "\n)")
    return dict(version=version(), n_exercises=sum(ex.values()), n_questions=n_q, n_longest=len(longest),
                longest_correct=and_list(longest), steps1=step_count(1), steps2=step_count(2),
                n_checks_t1=check_count("Guided Tutorial B.1"), n_checks_e1=check_count("Exercise B.1"),
                n_checks_e2=check_count("Exercise B.2"), n_role_rows=check_count("Guided Tutorial B.1", "as employee"),
                n_users=len(nb.SECURITY), n_centers=len(nb.centers(d)), n_employees=len(nb.employees(d)),
                n_term_managers=len(review["terminated"]), n_flagged=len(review["flagged"]),
                w_flagged=nb.word(len(review["flagged"])).capitalize(), w_terminated=nb.word(len(review["terminated"])),
                w_exercises=nb.word(sum(ex.values())), w_questions=nb.word(n_q), w_steps1=nb.word(step_count(1)),
                w_steps2=nb.word(step_count(2)),
                leak_revenue=nb.invoice_revenue(d), company=company, plant_hours=hours_all, dax_role=dax_role,
                n_unmapped=len(unmapped))


# --- Exercise B.1 ------------------------------------------------------------------------------------------------------

def tmdl_script(claim) -> dict:
    """The TMDL view tab Ex B.1 of the project: the scripted role with the column permission added, rules abbreviated."""
    text = (MODEL / "TMDLScripts" / "Ex B.1.tmdl").read_text(encoding="utf-8")
    lines = text.rstrip("\n").split("\n")
    claim(lines[0] == "createOrReplace", "the TMDL script of the project opens with createOrReplace")
    claim(any(l.strip() == "metadataPermission: none" for l in lines), "the TMDL script sets a metadata permission of none")
    rules = [l for l in lines if l.strip().startswith("tablePermission") and "=" in l]
    claim(len(rules) == 4, "the TMDL script keeps the role's four row rules (CostCenter, Employee, Item, Security)")
    out, shown = [], False
    for l in lines:
        if l.strip().startswith("tablePermission") and "=" in l:
            if not shown:
                out.append("\t\t// the four tablePermission rules of Guided Tutorial B.1, unchanged")
                shown = True
            continue
        if l.strip() == "" and out and out[-1] == "":
            continue
        out.append(l)
    i = next(k for k, l in enumerate(lines) if l.strip() == "tablePermission LaborTimeEntry")
    add = [l[2:] if l.startswith("\t\t") else l for l in lines[i:i + 3]]
    claim([l.strip() for l in add] == ["tablePermission LaborTimeEntry", "columnPermission ExtendedLaborCost", "metadataPermission: none"],
          "the three lines the exercise adds are the table permission, the column permission and the metadata permission of none")
    return dict(text="\n".join(out).replace("\n\n\n", "\n\n"), n_rules=len(rules), add="\n".join(add))


@context("appB.g1")
def g1(d, claim):
    need(d, claim, "CostCenter", "Employee", "LaborTimeEntry", "GLEntry", "Account", "SalesInvoiceLine", "Item", "SalesInvoice")
    y = d.C
    titles = labor_by_title(d, y)
    manuf = [t for t in titles if t["hours"] is not None]
    other = [t for t in titles if t["hours"] is None]
    total = sum(t["cost"] for t in titles)
    claim(len(manuf) >= 1 and len(other) >= 1,
          "some job titles have manufacturing hours and others have labor time that is all non-manufacturing, so Labor Cost lists titles whose hours are blank")
    claim(abs(total - d.one("SELECT SUM(ExtendedLaborCost) FROM LaborTimeEntry WHERE substr(WorkDate, 1, 4) = ?", str(y))) < 0.005,
          "the job titles' labor cost adds up to the year's labor time")
    # What the Production Manager's role shows without the column permission (the rule on Employee filters the labor time).
    pm = labor_by_title(d, y, [PRODUCTION_CC])
    pm_cost = sum(t["cost"] for t in pm)
    claim(all(t["hours"] is not None for t in pm), "every job title of the Manufacturing cost center has manufacturing hours")
    claim(abs(pm_cost - sum(t["cost"] for t in manuf)) < 0.005,
          "the Manufacturing cost center's employees hold all the manufacturing job titles' labor cost")
    people = d.q("SELECT l.EmployeeID, SUM(l.ExtendedLaborCost) FROM LaborTimeEntry l JOIN Employee e ON e.EmployeeID = l.EmployeeID "
                 "WHERE e.CostCenterID = ? AND substr(l.WorkDate, 1, 4) = ? GROUP BY 1", PRODUCTION_CC, str(y))
    p = nb.view_as(d, nb.PRODUCTION)
    claim(p["ccs"] == [PRODUCTION_CC], "the Production Manager is mapped to the Manufacturing cost center")
    claim(p["hours"] and p["ratio"], "the Production Manager's Plant page shows hours and a ratio")
    all_years = d.one("SELECT SUM(ExtendedLaborCost) FROM LaborTimeEntry")
    claim(all_years > total, "the labor time of the other fiscal years adds to the table that has no year filter")
    s = nb.view_as(d, nb.SALES)
    claim(s["hours"] is None, "the Sales cost center's employees record no labor time, so the Sales Manager has no hours")
    script = tmdl_script(claim)
    m_hours = measure(claim, "Manufacturing Hours")
    n_ols = _model_text("definition/roles/Cost Center Managers.tmdl").count("metadataPermission: none")
    claim(n_ols == 1, "the role Cost Center Managers of the solution project sets one column's metadata permission to none")
    return dict(y=y, n_ols=n_ols, titles=titles, n_titles=len(titles), manuf=manuf, other=other, n_manuf=len(manuf), n_other=len(other),
                total=total, other_cost=sum(t["cost"] for t in other), pm=pm, pm_cost=pm_cost, pm_share=pm_cost / total,
                n_people=len(people), person_low=min(c for _, c in people), person_high=max(c for _, c in people),
                all_years=all_years, p=p, n_centers=len(nb.centers(d)), company=nb.company_net_income(d),
                tmdl=script["add"], n_rules=script["n_rules"], w_rules=nb.word(script["n_rules"]),
                w_centers=nb.word(len(nb.centers(d))), w_titles=nb.word(len(titles)).capitalize(), w_other=nb.word(len(other)),
                w_manuf=nb.word(len(manuf)),
                m_cost=measure(claim, "Labor Cost"), m_hours=m_hours,
                t_table=visual_title(claim, "exb1", "laborByTitle"),
                dax_cost=check_expr(claim, "Exercise B.1", f"{y} Labor Cost (no role)"),
                dax_ols=check_expr(claim, "Exercise B.1", "column permissions set to None (object-level security)"))


# --- Exercise B.2 ------------------------------------------------------------------------------------------------------

@context("appB.g2")
def g2(d, claim):
    need(d, claim, "CostCenter", "Employee")
    emp = nb.employees(d)
    emails = nb.by_email(d)
    names = nb.centers(d)
    claim(len(emails) == len(emp), "every employee has a distinct Email, so LOOKUPVALUE on Email finds one row")
    claim(TYPO not in emails, "the typo address of the test row matches no employee")
    us = nb.users(d)
    unmapped = [cc for cc in sorted(names) if cc not in {c for _, c in nb.SECURITY}]
    manager = emp[d.one("SELECT ManagerID FROM CostCenter WHERE CostCenterID = ?", unmapped[0])]
    in_unmapped = sum(1 for e in emp.values() if e["cc"] == unmapped[0])
    # Test rows an instructor adds to a copy of Security: the three failures the flag names.
    former = emails[nb.FORMER]
    warehouse = emails[nb.WAREHOUSE]
    tests = [dict(upn=nb.FORMER, cc=former["cc"], emp=former, flag=flag(former, former["cc"])),
             dict(upn=nb.WAREHOUSE, cc=2, emp=warehouse, flag=flag(warehouse, 2)),
             dict(upn=TYPO, cc=2, emp=None, flag=flag(None, 2))]
    claim([t["flag"] for t in tests] == ["Terminated", "Mapped to another cost center", "No matching employee"],
          "the three test rows get the three flags: terminated, another cost center, no matching employee")
    claim(all(u["employee"] is not None and flag(u["employee"], u["cc"]) is None for u in us), "no user of the security table is flagged")
    # Wrong order of the SWITCH: a name that matches no employee reads BLANK <> "Active", which is true, so it is called terminated.
    wrong_order = "Terminated"
    # The security table typed with the cost centers in sequence (1 to 9) instead of tbl-b-02's cost center IDs.
    seq = [(upn, i) for i, (upn, _) in enumerate(nb.SECURITY, 1)]
    seq_flagged = [dict(upn=u, cc=cc, own=emails[u.lower()]["cc"], title=emails[u.lower()]["title"],
                        see=names[cc]) for u, cc in seq if emails[u.lower()]["cc"] != cc]
    seq_unmapped = [names[cc] for cc in sorted(names) if cc not in {c for _, c in seq}]
    claim(len(seq_flagged) == 2, "typed in sequence, two users are mapped to another cost center")
    # Run under a manager's role the review sees one cost center and one security row, so it finds nothing to report.
    under_role = []
    for upn, cc in nb.SECURITY:
        visible_cc, visible_security = {cc}, {(upn, cc)}
        under_role.append([c for c in visible_cc if not any(c == sc for _, sc in visible_security)])
    claim(all(not u for u in under_role), "run as a manager the review reports no unmapped cost center (the role hides the rows it tests)")
    s = nb.view_as(d, nb.SALES)
    n_terminated = d.one("SELECT COUNT(*) FROM Employee WHERE EmploymentStatus <> 'Active'")
    claim(n_terminated > 0, "the employee table lists terminated employees, so AccessEmployees shows their termination dates")
    claim(d.one("SELECT COUNT(*) FROM Employee WHERE Email IS NULL OR Email = ''") == 0, "every employee has an Email")
    blocks = query_blocks(claim)
    m_import = table_m("AccessEmployees")
    claim(any("T74_Employee" in l for l in m_import), "the model answer's AccessEmployees query reads T74_Employee")
    claim(any("Removed Other Columns" in l for l in m_import), "the model answer keeps seven columns of T74_Employee")
    return dict(center=names[unmapped[0]], center_id=unmapped[0], manager=manager, in_unmapped=in_unmapped,
                n_users=len(us), tests=tests, wrong_order=wrong_order, seq_flagged=seq_flagged, seq_unmapped=seq_unmapped,
                s_employees=s["employees"], n_employees=len(emp), n_terminated=n_terminated,
                q2=blocks["2"], q3=blocks["3"], q4=blocks["4"],
                title_table=visual_title(claim, "exb2", "accessEmployees"),
                dax_unmapped=check_expr(claim, "Exercise B.2", "cost centers with no row in the security table"),
                dax_matched=check_expr(claim, "Exercise B.2", "users matching an active employee's Email"),
                dax_rows=check_expr(claim, "Exercise B.2", "AccessEmployees rows"))
