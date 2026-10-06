"""Copy the chapter 15 reference model to CR16 and add Tutorial 16.3: Employee.CostCenterID, the
Security table, the measures Cost Centers Shown and Who Am I, and the roles."""
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, XLSX as _XLSX  # noqa: E402

SRC = REFERENCE_MODELS / "ch15_ref"
OUT = REFERENCE_MODELS / "ch16_ref"
T = "\t"

for sub in ["CR16.SemanticModel", "CR16.Report", "CR16.pbip"]:
    p = OUT / sub
    if p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()
shutil.copytree(SRC / "CR15.SemanticModel", OUT / "CR16.SemanticModel")
shutil.copytree(SRC / "CR15.Report", OUT / "CR16.Report")
(OUT / "CR16.pbip").write_text((SRC / "CR15.pbip").read_text(encoding="utf-8").replace("CR15", "CR16"),
                               encoding="utf-8", newline="\n")
pbir = OUT / "CR16.Report" / "definition.pbir"
pbir.write_text(pbir.read_text(encoding="utf-8").replace("CR15", "CR16"), encoding="utf-8", newline="\n")
d = OUT / "CR16.SemanticModel" / "definition"
(d / "database.tmdl").write_text("database CR16\n\tcompatibilityLevel: 1601\n", encoding="utf-8", newline="\n")


def edit(path, old, new):
    s = path.read_text(encoding="utf-8")
    assert s.count(old) == 1, (path, old[:60])
    path.write_text(s.replace(old, new), encoding="utf-8", newline="\n")


emp = d / "tables" / "Employee.tmdl"
edit(emp, f"{T}column PayClass\n", f"{T}column CostCenterID\n{T*2}dataType: int64\n{T*2}isHidden\n{T*2}summarizeBy: none\n"
     f"{T*2}sourceColumn: CostCenterID\n\n{T}column PayClass\n")
edit(emp, '"JobTitle", "PayClass"}),', '"JobTitle", "PayClass", "CostCenterID"}),')
edit(emp, '{"JobTitle", type text}, {"PayClass", type text}})', '{"JobTitle", type text}, {"PayClass", type text}, {"CostCenterID", Int64.Type}})')

security_rows = [
    ("employee001@charlesriver.example", 1), ("employee006@charlesriver.example", 2),
    ("employee007@charlesriver.example", 3), ("employee004@charlesriver.example", 4),
    ("employee010@charlesriver.example", 5), ("employee005@charlesriver.example", 6),
    ("employee011@charlesriver.example", 7), ("employee012@charlesriver.example", 9),
    ("employee014@charlesriver.example", 10),
]
rows_m = ",\n".join(T * 4 + "    {" + f'"{u}", {c}' + "}" for u, c in security_rows)
(d / "tables" / "Security.tmdl").write_text(f"""table Security
{T}isHidden

{T}column UserPrincipalName
{T*2}dataType: string
{T*2}isHidden
{T*2}summarizeBy: none
{T*2}sourceColumn: UserPrincipalName

{T}column CostCenterID
{T*2}dataType: int64
{T*2}isHidden
{T*2}summarizeBy: none
{T*2}sourceColumn: CostCenterID

{T}partition Security = m
{T*2}mode: import
{T*2}source =
{T*3}let
{T*3}    Source = #table(type table [UserPrincipalName = text, CostCenterID = Int64.Type], {{
{rows_m}
{T*3}    }})
{T*3}in
{T*3}    Source
""", encoding="utf-8", newline="\n")

# Measures on GLEntry (the reference model's host for ledger measures).
gl = d / "tables" / "GLEntry.tmdl"
s = gl.read_text(encoding="utf-8")
anchor = "table GLEntry\n\n"
assert s.startswith(anchor)
s = anchor + (f"{T}measure 'Cost Centers Shown' = CONCATENATEX ( DISTINCT ( CostCenter[CostCenterName] ), CostCenter[CostCenterName], \", \", CostCenter[CostCenterName], ASC )\n\n"
              f"{T}measure 'Who Am I' = USERPRINCIPALNAME ()\n\n") + s[len(anchor):]
gl.write_text(s, encoding="utf-8", newline="\n")

rule = "[CostCenterID] IN CALCULATETABLE ( VALUES ( Security[CostCenterID] ), Security[UserPrincipalName] = USERPRINCIPALNAME () )"
roles = d / "roles"
roles.mkdir(exist_ok=True)
(roles / "Cost Center Managers.tmdl").write_text(f"""role 'Cost Center Managers'
{T}modelPermission: read

{T}tablePermission CostCenter = {rule}

{T}tablePermission Employee = {rule}

{T}tablePermission Item = USERPRINCIPALNAME () IN VALUES ( Security[UserPrincipalName] )

{T}tablePermission Security = [UserPrincipalName] = USERPRINCIPALNAME ()
""", encoding="utf-8", newline="\n")
(roles / "Finance.tmdl").write_text(f"role Finance\n{T}modelPermission: read\n", encoding="utf-8", newline="\n")
# Test roles: the same rule with a literal user, so the engine can show what each manager sees.
for tag, upn in [("Test Sales Manager", "employee006@charlesriver.example"),
                 ("Test Warehouse Manager", "employee007@charlesriver.example"),
                 ("Test Production Manager", "employee004@charlesriver.example"),
                 ("Test Former Sales Rep", "employee083@charlesriver.example")]:
    lit = f'"{upn}"'
    r = rule.replace("USERPRINCIPALNAME ()", lit)
    (roles / f"{tag}.tmdl").write_text(f"""role '{tag}'
{T}modelPermission: read

{T}tablePermission CostCenter = {r}

{T}tablePermission Employee = {r}

{T}tablePermission Item = {lit} IN VALUES ( Security[UserPrincipalName] )

{T}tablePermission Security = [UserPrincipalName] = {lit}
""", encoding="utf-8", newline="\n")

m = d / "model.tmdl"
edit(m, '"Employee","WorkCenter"]', '"Employee","WorkCenter","Security"]')
for f in sorted(roles.iterdir()):
    print(f.name)
print("ok")
