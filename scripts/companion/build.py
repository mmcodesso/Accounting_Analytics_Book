"""Build the companion files listed in manifest.yml into outputs/companion/<start_folder>/.

Usage: python scripts/companion/build.py [--tool sql|excel] [--chapter 10]
       python scripts/companion/build.py --publish   (copy the built files into supplementary/)

SQL chains come from the chapter scripts in scripts/figures (dbbrowser.Script), the same
scripts the tutorial text and figures must match. For every tutorial the builder writes the
script as it stands at the end of that tutorial. A start file is exactly the script the reader
would have typed, so its line numbers match the book's figures. Two things are added, and
neither changes the line count:
  - the header's "your name, date" becomes a stamp (the checkpoint and the dataset release);
  - each query's last line gets a trailing "-- Result: ..." comment from running it read-only.
The builder refuses to run unless datasets/CharlesRiver.sqlite is the release pinned in
_variables.yml, so every expected result comes from the files readers download.

Excel chains are built through COM in a hidden Excel instance of their own (scripts/companion/xlbuild): one function
per tutorial applies its steps, and every checkpoint gets a Solution Notes worksheet whose checks compare live
formulas with values computed from the dataset. Each saved checkpoint points its queries at C:\\CharlesRiver, and is
then reopened, pointed back at datasets/, refreshed, and accepted only if every check agrees. Excel builds need
Windows, Excel for Microsoft 365, and pywin32 and openpyxl (scripts/companion/requirements-excel.txt).
"""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import importlib
import json
import re
import shutil
import sqlite3
import sys
import time
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DB, FIGURES, REPO, XLSX, db_uri, require_dataset  # noqa: E402

sys.path.insert(0, str(FIGURES))
import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
TUTORIAL = re.compile(r"^-- Tutorial (\d+)\.(\d+)\b")
ZIP_DATE = (2026, 1, 1, 0, 0, 0)          # fixed, so a rebuild of unchanged files is byte-identical
SITE = "https://aa.accountinganalyticshub.com/front-matter/downloads.html#sec-companion-files"
SUPPLEMENTARY = REPO / "supplementary"              # gitignored; scripts/release.py uploads it to the release
DOWNLOADS = REPO / "front-matter" / "downloads.qmd"
NEUTRAL = "C:\\CharlesRiver\\CharlesRiver.xlsx"   # where the Excel and Power BI files look for the workbook


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_dataset(variables: dict) -> None:
    require_dataset()
    for path, key in ((DB, "sqlite"), (XLSX, "xlsx")):
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        pinned = variables["dataset"]["sha256"][key]
        if digest.hexdigest() != pinned:
            raise SystemExit(f"{path} is not dataset release {variables['dataset']['version']} "
                             f"(SHA-256 {digest.hexdigest()}, expected {pinned}).")


def load_script(ref: str):
    module, attr = ref.split(".")
    return getattr(importlib.import_module(module), attr)


# --- running queries -------------------------------------------------------------------------

def statements(sql: str):
    buf = ""
    for line in sql.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                yield buf.strip()
            buf = ""
    if buf.strip():
        yield buf.strip()


def value_text(value: object) -> str:
    """A value as DB Browser shows it: REAL with 15 significant digits, ".0" kept on whole numbers."""
    if value is None:
        return "NULL"
    if isinstance(value, float):
        text = f"{value:.15g}"
        return text if any(ch in text for ch in ".en") else text + ".0"
    text = str(value)
    return text if len(text) <= 40 else text[:39] + "…"


def result_note(con: sqlite3.Connection, sql: str) -> str:
    """Run a query read-only (a view becomes a TEMP view) and describe what it returns."""
    rows = cols = view = None
    for stmt in statements(sql):
        stmt = re.sub(r"\bDROP\s+VIEW\s+IF\s+EXISTS\s+(\w+)", r"DROP VIEW IF EXISTS temp.\1", stmt, flags=re.I)
        m = re.search(r"\bCREATE\s+VIEW\s+(\w+)", stmt, flags=re.I)
        if m:
            view = m.group(1)
            stmt = re.sub(r"\bCREATE\s+VIEW\b", "CREATE TEMP VIEW", stmt, flags=re.I)
        cur = con.execute(stmt)
        if cur.description:
            cols, rows = [c[0] for c in cur.description], cur.fetchall()
    if rows is None:
        return f"-- Result: creates the view {view}" if view else "-- Result: no rows"
    if len(rows) == 1 and len(cols) <= 3:
        pairs = ", ".join(f"{c} = {value_text(v)}" for c, v in zip(cols, rows[0]))
        return f"-- Result: 1 row ({pairs})"
    return f"-- Result: {len(rows)} rows"


# --- SQL chains --------------------------------------------------------------------------------

def tutorial_of(comment: str) -> str:
    m = TUTORIAL.match(comment)
    if not m:
        raise SystemExit(f"Query comment does not name its tutorial: {comment!r}")
    return f"{m.group(1)}.{m.group(2)}"


def stamp(header: str, text: str) -> str:
    assert header.count("your name, date") == 1, "the header must hold one 'your name, date'"
    return header.replace("your name, date", text)


def script_text(header: str, queries: list[tuple[str, str, str]], notes: dict[str, str]) -> str:
    parts = [header]
    for key, comment, sql in queries:
        assert sql.rstrip().endswith(";"), f"{key}: the query must end with a semicolon"
        parts.append(f"{comment}\n{sql.rstrip()}  {notes[key]}")
    return "\n\n".join(parts) + "\n"


def strip_additions(text: str, header: str, stamped: str) -> str:
    """The checkpoint text without the stamp and the result comments (for verification)."""
    text = text.replace(stamped, header, 1)
    return re.sub(r"  -- Result: [^\n]*", "", text).rstrip("\n")


def build_sql_chain(chain: dict, variables: dict, out: Path) -> tuple[Path, list[Path]]:
    script = load_script(chain["script"])
    release = variables["dataset"]["version"]
    con = sqlite3.connect(db_uri(), uri=True)
    notes = {key: result_note(con, sql) for key, _, sql in script.queries}
    con.close()

    order = []
    for _, comment, _ in script.queries:
        t = tutorial_of(comment)
        if not order or order[-1] != t:
            assert t not in order, f"{chain['id']}: the queries of Tutorial {t} are not contiguous"
            order.append(t)

    folder = out / f"Chapter{chain['chapter']:02d}"
    if folder.exists():
        shutil.rmtree(folder)
    written = []
    readme = [f"Accounting Analytics: An Integrated Approach ({variables['book']['edition']} edition)",
              f"Companion files for Chapter {chain['chapter']}: {chain['file']}", "",
              f"Built from Charles River dataset release {release} ({variables['dataset']['window']}).",
              f"CharlesRiver.sqlite SHA-256 {variables['dataset']['sha256']['sqlite']}", ""]
    for i, t in enumerate(order):
        upto = max(j for j, (_, c, _) in enumerate(script.queries) if tutorial_of(c) == t) + 1
        stamped = stamp(script.header, f"companion file, end of Tutorial {t}; dataset {release}")
        text = script_text(stamped, script.queries[:upto], notes)
        # Verification: the file is the book's script up to this tutorial, line for line.
        expected = "\n\n".join([script.header] + [f"{c}\n{s.rstrip()}" for _, c, s in script.queries[:upto]])
        assert strip_additions(text, script.header, stamped) == expected, f"{chain['id']} {t}: text differs"
        assert text.count("\n") == expected.count("\n") + 1, f"{chain['id']} {t}: line count differs"
        lines, cursor = text.split("\n"), 0
        for key, comment, _ in script.queries[:upto]:
            cursor = lines.index(comment.split("\n")[0], cursor) + 1
            assert cursor == script.location(key)[2], f"{chain['id']} {key}: comment on line {cursor}"
        last = i == len(order) - 1
        targets = ([f"Start of Tutorial {order[i + 1]}"] if not last else []) + \
                  ([f"End of Chapter {chain['chapter']}"] if last else [])
        for name in targets:
            path = folder / name / chain["file"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            written.append(path)
            readme.append(f"{name}/{chain['file']}".ljust(44) +
                          f"the script at the end of Tutorial {t}")
    readme += ["", "How to use a start file:",
               "1. Make your working copy CharlesRiver_Work.sqlite of the downloaded CharlesRiver.sqlite,",
               "   as Tutorial 9.1 describes, if you don't have one yet.",
               f"2. Copy {chain['file']} from the folder of your tutorial into the folder of the working copy.",
               "3. In DB Browser for SQLite, open CharlesRiver_Work.sqlite, go to the Execute SQL tab, and",
               "   open the script with Open SQL file(s) (Ctrl+Shift+T).",
               "4. Continue at the end of the script, as the tutorial says.", "",
               "Each query ends with a comment that gives its result on this dataset release, and the line",
               "numbers match the book's figures. With a different release, the results differ.",
               f"More: {SITE}", ""]
    (folder / "README.txt").write_text("\n".join(readme), encoding="utf-8", newline="\n")
    written.append(folder / "README.txt")
    return folder, written


def build_extra(extra: dict, variables: dict, out: Path) -> Path:
    ref, key = extra["from"].split(":")
    script = load_script(ref)
    comment, sql, _ = script.location(key)
    con = sqlite3.connect(db_uri(), uri=True)
    note = result_note(con, sql)
    con.close()
    release = variables["dataset"]["version"]
    header = ("/* Setup_Part3_Views.sql: recreates the view MonthlyLaborEfficiency of Tutorial 11.3\n"
              "   Database: CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)\n"
              f"   Prepared by: companion file; dataset {release}\n"
              "   Run it once on your working copy, then select Write Changes. The Part III case reads the view. */")
    path = out / extra["file"]
    path.write_text(f"{header}\n\n{comment}\n{sql.rstrip()}  {note}\n", encoding="utf-8", newline="\n")
    return path


# --- Excel chains ----------------------------------------------------------------------------------------------

def chapter_id(text: str) -> int | str:
    """A chapter number, or an appendix letter ("B")."""
    return int(text) if str(text).isdigit() else str(text).upper()


def folder_name(ch: int | str) -> str:
    """The build folder of a chapter (Chapter13) or an appendix (AppendixB)."""
    return f"Chapter{ch:02d}" if isinstance(ch, int) else f"Appendix{ch}"


def part_name(ch: int | str) -> str:
    return f"Chapter {ch}" if isinstance(ch, int) else f"Appendix {ch}"


def tutorials_in(chapter: int | str) -> int:
    if isinstance(chapter, str):
        folder = next((REPO / "appendices").glob(f"{chapter.lower()}-*"))
    else:
        folder = next((REPO / "chapters").glob(f"{chapter:02d}-*"))
    return len(list(folder.glob("_tutorial-*.qmd")))


def checkpoint_roles(t: str, chapters: list[int | str]) -> list[tuple[int | str, str]]:
    """The folders the end file of tutorial t goes into: (chapter of the folder, folder name). An appendix that
    follows a chain's last chapter (chapters [13, 14, 15, "B"]) starts from that chapter's end file."""
    head, k = t.split(".")
    ch, k = chapter_id(head), int(k)
    if k < tutorials_in(ch):
        return [(ch, f"Start of Tutorial {ch}.{k + 1}")]
    roles = [(ch, f"End of {part_name(ch)}")]
    after = chapters[chapters.index(ch) + 1] if ch in chapters and chapters.index(ch) + 1 < len(chapters) else None
    if isinstance(ch, int) and ch + 1 in chapters:
        roles.append((ch + 1, f"Start of Tutorial {ch + 1}.1"))
    elif isinstance(after, str):
        roles.append((after, f"Start of Tutorial {after}.1"))
    return roles


def workbook_contents(wb, notes_sheet: str) -> dict[str, list[str]]:
    sheets = [ws for ws in wb.Worksheets if ws.Name != notes_sheet]
    return {
        "Queries": [q.Name for q in wb.Queries],
        "Worksheets": [ws.Name for ws in sheets],
        "Named cells": [n.Name for n in wb.Names if n.Visible and not n.Name.startswith("_")
                        and not n.Name.startswith("Slicer_")],
        "PivotTables": [f"{ws.Name} ({pt.Name})" for ws in sheets for pt in ws.PivotTables()],
        "Charts": [ws.Name for ws in sheets if ws.ChartObjects().Count],
        "Slicers": [sl.Name for sc in wb.SlicerCaches for sl in sc.Slicers],
    }


def verify_excel(paths: dict[str, Path], real: str) -> None:
    """Reopen each saved file in a fresh instance, point it at datasets/, refresh, and require every check to agree."""
    from xlbuild import notes, xl
    for t, path in paths.items():
        with xl.excel() as app:                # a fresh instance per file: one session of many large refreshes can crash
            wb = xl.retry(app.Workbooks.Open, str(path), 0, True)      # UpdateLinks=0, ReadOnly=True
            xl.wait_ready(app)                                        # a data table recalculates on opening
            stray = xl.retry(lambda: [q.Name for q in wb.Queries if real in q.Formula])
            assert not stray, f"{path.name}: queries still read the build path: {stray}"
            xl.repoint(wb, NEUTRAL, real)
            seconds = xl.refresh_all(wb)
            ok, failed = xl.retry(lambda: notes.read_result(*notes.locate(wb.Worksheets(notes.NOTES_SHEET))))
            xl.retry(wb.Close, False)
            del wb
            if not ok:
                raise SystemExit(f"{path.name}: checks fail after a refresh:\n  " + "\n  ".join(failed))
            print(f"  verified {t}: refresh {seconds:.0f}s, every check agrees")


def build_excel_chain(chain: dict, variables: dict, out: Path) -> list[Path]:
    from xlbuild import notes, xl
    from xlbuild.expected import Expected
    module = importlib.import_module(chain["builder"])
    real = str(XLSX)
    con = sqlite3.connect(db_uri(), uri=True)
    year = int(con.execute("SELECT MAX(substr(InvoiceDate, 1, 4)) FROM SalesInvoice").fetchone()[0])
    con.close()
    release, sha = variables["dataset"]["version"], variables["dataset"]["sha256"]["xlsx"]
    stamp = dict(
        book=f"Accounting Analytics: An Integrated Approach, {variables['book']['edition']} edition",
        dataset=f"Charles River dataset release {release} ({variables['dataset']['window']}); "
                f"CharlesRiver.xlsx SHA-256 {sha}",
        source=f"Power Query reads {NEUTRAL}. Put your copy of CharlesRiver.xlsx in that folder, or point the "
               "queries at your copy with Data > Get Data > Data Source Settings > Change Source; then choose "
               "Data > Refresh All.",
        built=f"{date.today().isoformat()}; every check below agreed after a refresh on the dataset release above")
    work = out.parent / f"_work-{out.name}" / chain["id"]     # outside the build folder, so it is never published
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    order = [t for t, _ in module.TUTORIALS]
    ends: dict[str, Path] = {}
    with xl.excel() as app:
        wb = app.Workbooks.Add()
        wb.SaveAs(str(work / "building.xlsx"), xl.XL_OPENXML_WORKBOOK)
        b = module.Build(wb=wb, src=real, xlsx=XLSX, exp=Expected(year), year=year)
        for t, apply in module.TUTORIALS:
            start = time.time()
            apply(b)
            uses = [f"the start file of {name[len('Start of '):]}" if name.startswith("Start of") else
                    f"the end-of-chapter file of {name[len('End of '):]}"
                    for _, name in checkpoint_roles(t, chain["chapters"])]
            role = f"the workbook at the end of Tutorial {t}: " + " and ".join(uses)
            ws, first, last = notes.write(wb, file_name=chain["file"], role=role,
                                          sections=notes.tutorial_sections(order[:order.index(t) + 1]),
                                          stamp=stamp, contents=workbook_contents(wb, notes.NOTES_SHEET),
                                          checks=b.checks)
            app.CalculateFull()
            xl.wait_ready(app)
            ok, failed = xl.retry(lambda: notes.read_result(ws, first, last))
            if not ok:
                raise SystemExit(f"Tutorial {t}: checks fail while building:\n  " + "\n  ".join(failed))
            ws.Activate()
            ws.Range("A1").Select()
            xl.repoint(wb, real, NEUTRAL)
            ends[t] = work / f"end-{t}.xlsx"
            xl.save_copy(wb, ends[t])
            xl.repoint(wb, NEUTRAL, real)
            print(f"  built end of Tutorial {t} in {time.time() - start:.0f}s ({last - first + 1} checks agree)")
        wb.Close(False)
    verify_excel({f"end of Tutorial {t}": p for t, p in ends.items()}, real)
    return distribute_excel(chain, variables, out, ends)


def distribute_excel(chain: dict, variables: dict, out: Path, ends: dict[str, Path]) -> list[Path]:
    """Copy each verified end file into the folders of the tutorials it starts, write the READMEs, and zip."""
    release, sha = variables["dataset"]["version"], variables["dataset"]["sha256"]["xlsx"]
    folders: dict[int, Path] = {}
    for t, path in ends.items():
        for ch, name in checkpoint_roles(t, chain["chapters"]):
            folder = folders.setdefault(ch, out / f"Chapter{ch:02d}")
            target = folder / name / chain["file"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    for ch, folder in folders.items():
        files = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*.xlsx"))
        readme = [f"Accounting Analytics: An Integrated Approach ({variables['book']['edition']} edition)",
                  f"Companion files for Chapter {ch}: {chain['file']}", "",
                  f"Built from Charles River dataset release {release} ({variables['dataset']['window']}).",
                  f"CharlesRiver.xlsx SHA-256 {sha}", ""] + files + [
                  "", "How to use a start file:",
                  "1. Copy the workbook from the folder of your tutorial into a folder of your own.",
                  f"2. Its queries read {NEUTRAL}. Put your copy of CharlesRiver.xlsx there, or open the workbook",
                  "   and point the queries at your copy: Data > Get Data > Data Source Settings > Change Source.",
                  "3. Choose Data > Refresh All. The Solution Notes worksheet then checks every control total.",
                  "4. Continue with the tutorial.", "", f"More: {SITE}", ""]
        (folder / "README.txt").write_text("\n".join(readme), encoding="utf-8", newline="\n")
    return [zip_folder(folder) for folder in folders.values()]


# --- Power BI chains ----------------------------------------------------------------------------------------------

def project_contents(project) -> dict[str, list[str]]:
    m = project.model
    return {
        "Queries": [q for q in m.query_order],
        "Tables": [t.name + (" (hidden)" if t.hidden else "") for t in m.tables.values()],
        "Measures": [f"{t.name}[{x.name}]" for t in m.tables.values() for x in t.measures],
        "Relationships": [f"{r.from_column} to {r.to_column}" + ("" if r.active else " (inactive)")
                          for r in m.relationships],
        "Roles": [r.name for r in m.roles],
        "Report pages": [p.display + (" (hidden)" if p.hidden else "") for p in project.report.pages
                         if p.name != "notes"],
        "DAX query tabs": list(project.queries),
    }


def same_but_path(a: Path, b: Path, path_a: str, path_b: str, also: list[tuple[str, str]] = ()) -> None:
    """The shipped project must be the verified one with only the source path changed (compared before Desktop opens
    the verification copy and adds its own files). `also`: the (verified, shipped) paths of any other source."""
    files_a = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    assert files_a == files_b, f"{b}: the shipped files differ from the verified ones"
    for f in files_a:
        ta, tb = (a / f).read_text(encoding="utf-8"), (b / f).read_text(encoding="utf-8")
        for x, y in [(path_a, path_b), *also]:
            ta = ta.replace(x, y)
        assert ta == tb, f"{f}: differs beyond the source path"


def build_pbi_chain(chain: dict, variables: dict, out: Path) -> list[Path]:
    """Write the project as it stands at the end of each tutorial, verify each checkpoint in Power BI Desktop (load,
    refresh, the Checks query, every page rendered, the DAX query tabs), and distribute the shipped copies."""
    from pbibuild import verify
    from xlbuild import notes
    from xlbuild.expected import Expected
    module = importlib.import_module(chain["builder"])
    real = str(XLSX)
    con = sqlite3.connect(db_uri(), uri=True)
    year = int(con.execute("SELECT MAX(substr(InvoiceDate, 1, 4)) FROM SalesInvoice").fetchone()[0])
    con.close()
    release, sha = variables["dataset"]["version"], variables["dataset"]["sha256"]["xlsx"]
    stamp = dict(
        book=f"Accounting Analytics: An Integrated Approach, {variables['book']['edition']} edition",
        dataset=f"Charles River dataset release {release} ({variables['dataset']['window']}); "
                f"CharlesRiver.xlsx SHA-256 {sha}",
        source=f"Power Query reads {NEUTRAL}. Put your copy of CharlesRiver.xlsx in that folder, or point the "
               "queries at your copy with Home > Transform data > Data source settings > Change Source; then "
               "choose Home > Refresh.",
        built=f"{date.today().isoformat()}; every check agreed in Power BI Desktop after a refresh on the dataset "
              "release above")
    work = out.parent / f"_work-{out.name}" / chain["id"]
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    order = [t for t, _ in module.TUTORIALS]
    b = module.Build(xlsx=XLSX, exp=Expected(year), year=year)
    ends: dict[str, Path] = {}
    for t, apply in module.TUTORIALS:
        start = time.time()
        apply(b)
        uses = [f"the start file of {name[len('Start of '):]}" if name.startswith("Start of") else
                f"the end-of-chapter file of {name[len('End of '):]}"
                for _, name in checkpoint_roles(t, chain["chapters"])]
        role = f"the project at the end of Tutorial {t}: " + " and ".join(uses)
        p = b.project
        p.notes_page(stamp, role, notes.tutorial_sections(order[:order.index(t) + 1]), project_contents(p))
        check_pbip = p.write(work / f"verify-{t}", real)
        ship = p.write(work / f"end-{t}", NEUTRAL).parent
        same_but_path(check_pbip.parent, ship, real, NEUTRAL)
        checks = check_pbip.parent / f"{p.name}.SemanticModel" / "DAXQueries" / "Checks.dax"
        # a hidden page's tab reads "Hidden <name>" in Desktop
        tab = lambda pg: f"Hidden {pg.display}" if pg.hidden else pg.display
        pages = [tab(pg) for pg in p.report.pages]
        roles = role_checks_file(getattr(b, "role_checks", None), work / f"roles-{t}")
        result = verify.run(check_pbip, chain["table"], checks, pages, work / f"result-{t}.json", role_checks=roles)
        problems = verify.judge(result, {tab(pg): pg.expect for pg in p.report.pages}, list(p.queries))
        if problems:
            raise SystemExit(f"Tutorial {t}: Power BI Desktop verification fails:\n  " + "\n  ".join(problems))
        ends[t] = ship
        print(f"  built and verified end of Tutorial {t} in {time.time() - start:.0f}s "
              f"(refresh {result['refreshSeconds']}s, {len(p.checks)} checks agree, {len(pages)} pages render)")
    return distribute_pbi(chain, variables, out, ends)


def role_checks_file(role_checks: dict | None, folder: Path) -> Path | None:
    """Write a builder's checks that must run under a role (label -> (role, effective user or None, [(section,
    Check)]), optionally with a fourth item, text the query's error must contain when the role may not see what it
    reads) as checks queries and the JSON list verify.ps1 reads; None when there are none."""
    if not role_checks:
        return None
    from pbibuild.project import checks_query
    folder.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, (label, (role, user, checks, *expect)) in enumerate(role_checks.items()):
        path = folder / f"role-{i}.dax"
        path.write_text(checks_query(checks), encoding="utf-8")
        entries.append({"label": label, "role": role, "user": user, "file": str(path)} |
                       ({"expectError": expect[0]} if expect else {}))
    target = folder / "roles.json"
    target.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return target


def also_copies(chain: dict, out: Path) -> dict[int, list[str]]:
    """Copy the verified checkpoints of other chains that a tutorial of this chain also needs (manifest key `also`:
    folder -> {chain, after}) into that tutorial's folder, from the other chain's distributed files. Returns, per
    chapter, the README lines for the copies; a checkpoint that is not built yet is reported and left out."""
    chains = {c["id"]: c for c in load_yaml(HERE / "manifest.yml")["chains"]}
    lines: dict[int, list[str]] = {}
    for role, ref in (chain.get("also") or {}).items():
        other = chains[ref["chain"]]
        name = other["file"].removesuffix(".pbip")
        src_ch, src_role = checkpoint_roles(ref["after"], other["chapters"])[0]
        source = out / folder_name(src_ch) / src_role / name
        ch = chapter_id(role.rsplit(" ", 1)[-1].split(".")[0])
        if not source.is_dir():
            print(f"  WARNING: {ref['chain']} has no verified end of Tutorial {ref['after']} ({source} is missing), so "
                  f"'{role}' lacks {name}: rebuild {part_name(ch)} after {ref['chain']}")
            continue
        shutil.copytree(source, out / folder_name(ch) / role / name)
        lines.setdefault(ch, []).append(f"{role}/{name}/{name}.pbip (the end of Tutorial {ref['after']}, which "
                                        f"Tutorial {role.rsplit(' ', 1)[-1]} also uses)")
    return lines


def distribute_pbi(chain: dict, variables: dict, out: Path, ends: dict[str, Path]) -> list[Path]:
    release, sha = variables["dataset"]["version"], variables["dataset"]["sha256"]["xlsx"]
    name = chain["file"].removesuffix(".pbip")
    folders: dict[int, Path] = {}
    for t, project in ends.items():
        for ch, role in checkpoint_roles(t, chain["chapters"]):
            folder = folders.setdefault(ch, out / folder_name(ch))
            target = folder / role / name
            shutil.copytree(project, target)
    also = also_copies(chain, out)
    for ch, folder in folders.items():
        roles = sorted(p.name for p in folder.iterdir() if p.is_dir())
        readme = [f"Accounting Analytics: An Integrated Approach ({variables['book']['edition']} edition)",
                  f"Companion files for {part_name(ch)}: {name} (a Power BI project)", "",
                  f"Built from Charles River dataset release {release} ({variables['dataset']['window']}).",
                  f"CharlesRiver.xlsx SHA-256 {sha}", ""] + [f"{r}/{name}/{name}.pbip" for r in roles] + (
                  also.get(ch, [])) + [
                  "", "How to use a start file:",
                  f"1. Copy the folder {name} from the folder of your tutorial into a folder of your own. It holds",
                  f"   {name}.pbip and two folders, which belong together.",
                  f"2. Open {name}.pbip in Power BI Desktop (the September 2026 release or later).",
                  f"3. Its queries read {NEUTRAL}. Put your copy of CharlesRiver.xlsx there, or point the queries",
                  "   at your copy: Home > Transform data > Data source settings > Change Source.",
                  "4. Choose Home > Refresh. The project holds no data until you refresh it.",
                  f"5. Choose File > Save as and save it as {name}.pbix, the file the tutorials use.",
                  "6. Continue with the tutorial. The Notes page lists what the file holds; in DAX query view, the",
                  "   Checks tab checks every control total (choose Run).", "", f"More: {SITE}", ""]
        (folder / "README.txt").write_text("\n".join(readme), encoding="utf-8", newline="\n")
    return [zip_folder(folder) for folder in folders.values()]


# --- Excel solutions (instructor) -------------------------------------------------------------------------------

def build_excel_solution(entry: dict, variables: dict, out_root: Path, start_folder: str, work_suffix: str = "") -> Path:
    """Apply a solution builder (exercises, a case, or a capstone) to its starting workbook, write the Solution Notes,
    verify, and zip.

    Exercises start from the verified chapter-end checkpoint (`base`) and their sections come from _exercises.qmd. A
    case or capstone (`kind: requirements`, `source`: its .qmd) starts from a blank workbook, as the case tells the
    reader to, and its sections are its Requirements and Milestones with their instructor notes."""
    from xlbuild import notes, solutions, xl
    module = importlib.import_module(entry["builder"])
    kind = entry.get("kind", "exercises")
    base = None
    if entry.get("base"):
        base = out_root.parent / f"_work-{start_folder}" / entry["base"]["chain"] / f"end-{entry['base']['after']}.xlsx"
        if not base.exists():
            raise SystemExit(f"{entry['id']}: build the chain {entry['base']['chain']} first (no {base})")
    real = str(XLSX)
    con = sqlite3.connect(db_uri(), uri=True)
    year = int(con.execute("SELECT MAX(substr(InvoiceDate, 1, 4)) FROM SalesInvoice").fetchone()[0])
    con.close()
    release, sha = variables["dataset"]["version"], variables["dataset"]["sha256"]["xlsx"]
    stamp = dict(
        book=f"Accounting Analytics: An Integrated Approach, {variables['book']['edition']} edition (instructor solutions)",
        dataset=f"Charles River dataset release {release} ({variables['dataset']['window']}); "
                f"CharlesRiver.xlsx SHA-256 {sha}",
        source=f"Power Query reads {NEUTRAL}. Put CharlesRiver.xlsx in that folder, or point the queries at your copy "
               "with Data > Get Data > Data Source Settings > Change Source; then choose Data > Refresh All.",
        built=f"{date.today().isoformat()}; every check below agreed after a refresh on the dataset release above")
    work = out_root.parent / f"_work-{out_root.name}" / (entry["id"] + work_suffix)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    target = work / entry["file"]
    chapter = entry.get("chapter")
    order = [e for e, _ in module.EXERCISES]
    if kind == "exercises":
        role = (f"solutions to the exercises of Chapter {chapter}, built on a copy of the workbook at the end of "
                f"Tutorial {entry['base']['after']}")
        sections = lambda done: solutions.exercise_sections(chapter, done)
        prefix, label = "Exercise", f"Chapter {chapter} exercises"
    else:
        role = entry["role"]
        sections = lambda done: solutions.requirement_sections(REPO / entry["source"], done)
        prefix, label = "", entry["id"]
    with xl.excel() as app:
        if base is not None:
            shutil.copyfile(base, target)
            wb = xl.retry(app.Workbooks.Open, str(target))
            xl.wait_ready(app)
            xl.repoint(wb, NEUTRAL, real)
        else:
            wb = xl.retry(app.Workbooks.Add)
            xl.retry(wb.SaveAs, str(target), xl.XL_OPENXML_WORKBOOK)
            xl.wait_ready(app)
        b = solutions.ExerciseBuild(wb=wb, src=real, xlsx=XLSX, year=year)
        for e, apply in module.EXERCISES:
            start = time.time()
            apply(b)
            ws, first, last = notes.write(
                wb, file_name=entry["file"], role=role, sections=sections(order[:order.index(e) + 1]), stamp=stamp,
                contents=workbook_contents(wb, notes.NOTES_SHEET), checks=b.checks, items_heading="Requirements",
                meaning_heading="Instructor notes", check_prefix=prefix)
            app.CalculateFull()
            xl.wait_ready(app)
            ok, failed = xl.retry(lambda: notes.read_result(ws, first, last))
            if not ok:
                raise SystemExit(f"{prefix} {e}: checks fail while building:\n  " + "\n  ".join(failed))
            print(f"  built {prefix} {e} in {time.time() - start:.0f}s ({last - first + 1} checks agree)".replace("  built  ", "  built "))
        ws.Activate()
        ws.Range("A1").Select()
        xl.repoint(wb, real, NEUTRAL)
        xl.retry(wb.Save)
        xl.wait_ready(app)
        xl.retry(wb.Close, False)
        del wb
    verify_excel({label: target}, real)
    folder = out_root / (entry["folder"] if "folder" in entry else f"Chapter{chapter:02d}-exercises")
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    shutil.copyfile(target, folder / entry["file"])
    readme = [f"Accounting Analytics: An Integrated Approach ({variables['book']['edition']} edition), instructor files",
              (f"Solutions to the exercises of Chapter {chapter}: {entry['file']}" if kind == "exercises"
               else f"{role[0].upper() + role[1:]}: {entry['file']}"), "",
              f"Built from Charles River dataset release {release} ({variables['dataset']['window']}).",
              f"CharlesRiver.xlsx SHA-256 {sha}", "",
              ("The workbook is the end-of-chapter companion file with one worksheet per exercise. Its Solution Notes"
               if kind == "exercises" else
               "The workbook answers the requirements that the case does in Excel. Its Solution Notes"),
              "worksheet lists the requirements, checks the results against the dataset, and repeats the",
              "instructor notes. Its queries read " + NEUTRAL + "; point them at your copy with",
              "Data > Get Data > Data Source Settings > Change Source, and choose Data > Refresh All.",
              "These files are public, like the rest of the book. Try an exercise first, then compare your work.", ""]
    (folder / "README.txt").write_text("\n".join(readme), encoding="utf-8", newline="\n")
    return zip_folder(folder, suffix="")


def build_pbi_solution(entry: dict, variables: dict, out_root: Path, start_folder: str, work_suffix: str = "") -> Path:
    """The Power BI counterpart of build_excel_solution. Exercises replay the chain's tutorials up to the chapter-end
    checkpoint (`base`), as the reader's Save as copy starts there, and apply one function per exercise; a case or
    capstone (`kind: requirements`) starts a new project. The Notes page lists the exercises or requirements with their
    instructor notes, and the project is verified once in Power BI Desktop like a chain checkpoint."""
    from pbibuild import verify
    from xlbuild import solutions
    from xlbuild.expected import Expected
    module = importlib.import_module(entry["builder"])
    kind = entry.get("kind", "exercises")
    con = sqlite3.connect(db_uri(), uri=True)
    year = int(con.execute("SELECT MAX(substr(InvoiceDate, 1, 4)) FROM SalesInvoice").fetchone()[0])
    con.close()
    release, sha = variables["dataset"]["version"], variables["dataset"]["sha256"]["xlsx"]
    stamp = dict(
        book=f"Accounting Analytics: An Integrated Approach, {variables['book']['edition']} edition (instructor solutions)",
        dataset=f"Charles River dataset release {release} ({variables['dataset']['window']}); "
                f"CharlesRiver.xlsx SHA-256 {sha}",
        source=f"Power Query reads {NEUTRAL}. Put CharlesRiver.xlsx in that folder, or point the queries at your copy "
               "with Home > Transform data > Data source settings > Change Source; then choose Home > Refresh.",
        built=f"{date.today().isoformat()}; every check agreed in Power BI Desktop after a refresh on the dataset "
              "release above")
    # also_sources: other files the project reads (name -> its built copy, relative to the repo); the module's queries
    # read C:\CharlesRiver\<name>, and the verification copy is pointed at the built copy
    also = {f"C:\\CharlesRiver\\{n}": str(REPO / rel) for n, rel in (entry.get("also_sources") or {}).items()}
    if hasattr(module, "prepare"):                  # a builder that writes a source itself (Chapter 19's RefundFlags.csv)
        module.prepare(also)
    for neutral, real in also.items():
        if not Path(real).exists():
            raise SystemExit(f"{entry['id']}: build {Path(real).name} first (no {real})")
        stamp["source"] += (f" It also reads {neutral}: copy {Path(real).name} from "
                            f"{Path(real).parent.name}.zip into that folder.")
    chapter = entry.get("chapter")
    name = entry["file"].removesuffix(".pbip")
    if entry.get("base"):
        chain = next(c for c in load_yaml(HERE / "manifest.yml")["chains"] if c["id"] == entry["base"]["chain"])
        chain_module = importlib.import_module(chain["builder"])
        b = chain_module.Build(xlsx=XLSX, exp=Expected(year), year=year)
        for t, apply in chain_module.TUTORIALS:          # the reader's file at the end of the chapter's tutorials
            apply(b)
            if t == entry["base"]["after"]:
                break
        table = chain["table"]
        role = (f"solutions to the exercises of {part_name(chapter)}, built on a copy of the project at the end of "
                f"Tutorial {entry['base']['after']}")
        if kind == "requirements":                  # a capstone that updates a chapter's file (Chapter 19's monitoring)
            role = entry["role"]
            sections = solutions.requirement_sections(REPO / entry["source"], [e for e, _ in module.EXERCISES])
        else:
            sections = solutions.exercise_sections(chapter, [e for e, _ in module.EXERCISES])
    else:
        b = module.Build(xlsx=XLSX, exp=Expected(year), year=year, **({"sources": also} if also else {}))
        table = entry["table"]
        role = entry["role"]
        sections = solutions.requirement_sections(REPO / entry["source"], [e for e, _ in module.EXERCISES])
    b.project.name = name
    for e, apply in module.EXERCISES:
        start = time.time()
        apply(b)
        print(f"  built {e} in {time.time() - start:.0f}s ({len(b.project.checks)} checks so far)")
    p = b.project
    p.notes_page(stamp, role, sections, project_contents(p))
    work = out_root.parent / f"_work-{out_root.name}" / (entry["id"] + work_suffix)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    check_pbip = p.write(work / "verify", str(XLSX))
    for f in (check_pbip.parent / f"{name}.SemanticModel").rglob("*.tmdl") if also else ():
        text = f.read_text(encoding="utf-8")
        for neutral, real in also.items():
            text = text.replace(neutral, real)
        f.write_text(text, encoding="utf-8", newline="\n")
    ship = p.write(work / "ship", NEUTRAL).parent
    same_but_path(check_pbip.parent, ship, str(XLSX), NEUTRAL, [(real, neutral) for neutral, real in also.items()])
    tab = lambda pg: f"Hidden {pg.display}" if pg.hidden else pg.display
    pages = [tab(pg) for pg in p.report.pages]
    roles = role_checks_file(getattr(b, "role_checks", None), work / "roles")
    result = verify.run(check_pbip, table, check_pbip.parent / f"{name}.SemanticModel" / "DAXQueries" / "Checks.dax",
                        pages, work / "result.json", role_checks=roles)
    problems = verify.judge(result, {tab(pg): pg.expect for pg in p.report.pages}, list(p.queries))
    if problems:
        raise SystemExit(f"{entry['id']}: Power BI Desktop verification fails:\n  " + "\n  ".join(problems))
    print(f"  verified {entry['id']}: refresh {result['refreshSeconds']}s, {len(p.checks)} checks agree, "
          f"{len(pages)} pages render")
    folder = out_root / (entry["folder"] if "folder" in entry else f"{folder_name(chapter)}-exercises-pbi")
    # include_sources: other sources shipped beside the project, in its zip (kept across the folder's rebuild)
    kept = {n: Path(also[f"C:\\CharlesRiver\\{n}"]).read_bytes() for n in entry.get("include_sources") or ()}
    if folder.exists():
        shutil.rmtree(folder)
    shutil.copytree(ship, folder / name)
    for n, data in kept.items():
        (folder / n).write_bytes(data)
    readme = [f"Accounting Analytics: An Integrated Approach ({variables['book']['edition']} edition), instructor files",
              (f"Solutions to the Power BI exercises of {part_name(chapter)}: {name} (a Power BI project)"
               if kind == "exercises" else f"{role[0].upper() + role[1:]}: {name} (a Power BI project)"), "",
              f"Built from Charles River dataset release {release} ({variables['dataset']['window']}).",
              f"CharlesRiver.xlsx SHA-256 {sha}", "",
              f"Open {name}/{name}.pbip in Power BI Desktop (the September 2026 release or later). Its queries read",
              f"{NEUTRAL}; point them at your copy with Home > Transform data > Data source settings >",
              "Change Source, choose Home > Refresh, and save it as a .pbix file if you prefer. The Notes page lists the",
              "exercises or requirements with the instructor notes; in DAX query view, the Checks tab tests every value.",
              "These files are public, like the rest of the book. Try an exercise first, then compare your work.", ""]
    for neutral, real in also.items():
        readme[-2:-2] = [f"It also reads {neutral}: copy {Path(real).name} from {Path(real).parent.name}.zip",
                         "into that folder, or point those queries at your copy the same way."]
    (folder / "README.txt").write_text("\n".join(readme), encoding="utf-8", newline="\n")
    return zip_folder(folder, suffix="")


def build_sql_solution(entry: dict, variables: dict, out_root: Path, start_folder: str, work_suffix: str = "") -> Path:
    """Write the SQL solution scripts of an exercise set, a case, or a capstone (sqlbuild/script.py), run every query
    read-only with its checks, run each finished file top to bottom as DB Browser would, and zip."""
    from sqlbuild.script import Build, notes_block, run
    from xlbuild import solutions
    module = importlib.import_module(entry["builder"])
    kind = entry.get("kind", "exercises")
    chapter = entry.get("chapter")
    release = variables["dataset"]["version"]
    b = Build()
    for e, apply in module.EXERCISES:
        b.current = e
        apply(b)
        for s in b.scripts.values():
            for q in s.queries:
                q.section = q.section or e

    def connect() -> sqlite3.Connection:
        con = sqlite3.connect(db_uri(), uri=True)
        if entry.get("setup_views"):         # the view of Tutorial 11.3, as TEMP, for work that reads it
            extra = next(x for x in load_yaml(HERE / "manifest.yml")["extras"] if x["id"] == "part3-views")
            ref, key = extra["from"].split(":")
            run(con, load_script(ref).location(key)[1], statements)
        return con

    def result_line(res, view) -> str:
        if res is None:
            return f"-- Result: creates the view {view}" if view else "-- Result: no rows"
        if len(res.rows) == 1 and len(res.columns) <= 3:
            return "-- Result: 1 row (" + ", ".join(f"{c} = {value_text(v)}" for c, v in zip(res.columns, res.rows[0])) + ")"
        return f"-- Result: {len(res.rows)} rows"

    folder = out_root / (entry.get("folder") or f"{folder_name(chapter)}-exercises-sql")
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    prepared = f"instructor solution, built {date.today().isoformat()} on dataset {release}"
    total = 0
    for s in b.scripts.values():
        con = connect()
        results, checks, failed = [], [], []
        for q in s.queries:
            start = time.time()
            res, view = run(con, q.sql, statements)
            results.append(result_line(res, view))
            for c in q.checks:
                ok, got = c.agrees(res)
                checks.append((q.section, c, got))
                if not ok:
                    failed.append(f"{q.section}: {c.label}: expected {c.expected}, got {got}")
            if time.time() - start > 60:
                print(f"  WARNING: {s.file}: '{q.what}' took {time.time() - start:.0f}s")
        con.close()
        if failed:
            raise SystemExit(f"{s.file}: checks fail:\n  " + "\n  ".join(failed))
        if kind == "exercises":
            sections = solutions.exercise_sections(chapter, s.sections)
        else:
            sections = solutions.requirement_sections(REPO / entry["source"], s.sections)
        text = s.text(prepared, results, notes_block(sections, checks, release))
        path = folder / s.file
        path.write_text(text, encoding="utf-8", newline="\n")
        con = connect()                          # the file as written runs top to bottom
        for stmt in statements(path.read_text(encoding="utf-8")):
            run(con, stmt, statements)
        con.close()
        total += len(checks)
        print(f"  wrote {s.file}: {len(s.queries)} queries, {len(checks)} checks agree")
    files = sorted(p.name for p in folder.glob("*.sql"))
    readme = [f"Accounting Analytics: An Integrated Approach ({variables['book']['edition']} edition), instructor files",
              (f"SQL solutions to the exercises of {part_name(chapter)}" if kind == "exercises"
               else f"{entry['role'][0].upper() + entry['role'][1:]}"), "",
              f"Built from Charles River dataset release {release} ({variables['dataset']['window']}).",
              f"CharlesRiver.sqlite SHA-256 {variables['dataset']['sha256']['sqlite']}", ""] + files + [
              "", "Open a script in DB Browser for SQLite (Execute SQL > Open SQL file(s)) on a working copy of",
              "CharlesRiver.sqlite. Each query ends with its result on this dataset release, and the notes block at",
              "the end repeats the requirements and the instructor notes and lists the values checked.",
              "These files are public, like the rest of the book. Try an exercise first, then compare your work.", ""]
    (folder / "README.txt").write_text("\n".join(readme), encoding="utf-8", newline="\n")
    print(f"  {entry['id']}: {len(files)} scripts, {total} checks agree")
    return zip_folder(folder, suffix="")


def zip_folder(folder: Path, extra_files: list[Path] = (), suffix: str = "-companion") -> Path:
    target = folder.with_name(f"{folder.name}{suffix}.zip")
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files + list(extra_files):
            arc = p.relative_to(folder).as_posix() if p.is_relative_to(folder) else p.name
            info = zipfile.ZipInfo(arc, ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, p.read_bytes())
    return target


def publish(manifest: dict) -> int:
    """Copy the built zips and scripts into supplementary/start-files/ and supplementary/solutions/, which
    scripts/release.py publishes on the release of the book's revision (the site links them there). The set of files
    must equal the set of /supplementary/ links of the Downloads page. Only files whose bytes changed are copied, so
    only real rebuilds are uploaded again; files no longer built are removed."""
    folders = {"start-files": REPO / "outputs" / "companion" / manifest["start_folder"],
               "solutions": REPO / "outputs" / "companion" / manifest["solutions_folder"]}
    built = {f"{sub}/{f.name}": f for sub, folder in folders.items()
             for f in sorted(folder.glob("*")) if f.is_file() and f.suffix in (".zip", ".sql")}
    linked = set(re.findall(r"\]\(/supplementary/([^)\s]+)\)", DOWNLOADS.read_text(encoding="utf-8")))
    missing, unlinked = sorted(linked - built.keys()), sorted(built.keys() - linked)
    for rel in missing:
        print(f"linked on the Downloads page but not built: {rel}")
    for rel in unlinked:
        print(f"built but not linked on the Downloads page: {rel}")
    if missing or unlinked:
        return 1
    updated = 0
    for rel, source in built.items():
        target = SUPPLEMENTARY / rel
        if target.is_file() and filecmp.cmp(source, target, shallow=False):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        updated += 1
        print(f"updated {target.relative_to(REPO).as_posix()} ({source.stat().st_size / 1e6:.1f} MB)")
    for sub in folders:
        for f in sorted((SUPPLEMENTARY / sub).glob("*")):
            if f.is_file() and f"{sub}/{f.name}" not in built:
                f.unlink()
                print(f"removed {f.relative_to(REPO).as_posix()}")
    print(f"{len(built)} files in supplementary/, {updated} updated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tool", choices=["sql", "excel", "pbi"], default=None)
    parser.add_argument("--chapter", type=chapter_id, default=None, help="a chapter number or an appendix letter")
    parser.add_argument("--id", default=None, help="build only the solution with this manifest id (with --solutions)")
    parser.add_argument("--work-suffix", default="",
                        help="build a solution in a fresh work folder (when a stale Excel instance holds the usual one)")
    parser.add_argument("--solutions", action="store_true",
                        help="build the instructor solutions (exercises, cases, capstones) instead of the chains")
    parser.add_argument("--publish", action="store_true",
                        help="copy the built files into supplementary/, which release.py publishes, and check them "
                             "against the links of the Downloads page")
    args = parser.parse_args()

    manifest = load_yaml(HERE / "manifest.yml")
    if args.publish:
        return publish(manifest)
    variables = load_yaml(REPO / "_variables.yml")
    check_dataset(variables)
    out = REPO / "outputs" / "companion" / manifest["start_folder"]
    out.mkdir(parents=True, exist_ok=True)
    if args.solutions:
        instructor = REPO / "outputs" / "companion" / manifest["solutions_folder"]
        instructor.mkdir(parents=True, exist_ok=True)
        for entry in manifest.get("solutions", []):
            if args.tool not in (None, entry["tool"]) or args.chapter not in (None, entry.get("chapter")):
                continue
            if args.id not in (None, entry["id"]):
                continue
            print(f"{entry['id']}: building {entry.get('file', 'the SQL scripts')}")
            build = {"excel": build_excel_solution, "pbi": build_pbi_solution, "sql": build_sql_solution}[entry["tool"]]
            archive = build(entry, variables, instructor, manifest["start_folder"], args.work_suffix)
            print(f"{entry['id']}: -> {archive.relative_to(REPO)}")
        return 0

    extras = {e["id"]: build_extra(e, variables, out) for e in manifest.get("extras", [])
              if args.tool in (None, e["tool"]) and args.chapter in (None, 11)}
    for chain in manifest["chains"]:
        chapters = chain.get("chapters", [chain.get("chapter")])
        if args.tool not in (None, chain["tool"]) or args.chapter not in (None, *chapters):
            continue
        if chain["tool"] in ("excel", "pbi"):
            for ch in chapters:
                if (out / folder_name(ch)).exists():
                    shutil.rmtree(out / folder_name(ch))
            print(f"{chain['id']}: building {chain['file']}")
            build = build_excel_chain if chain["tool"] == "excel" else build_pbi_chain
            for archive in build(chain, variables, out):
                print(f"{chain['id']}: -> {archive.relative_to(REPO)}")
            continue
        folder, files = build_sql_chain(chain, variables, out)
        add = [extras["part3-views"]] if chain["chapter"] == 11 and "part3-views" in extras else []
        archive = zip_folder(folder, add)
        print(f"{chain['id']}: {len(files) - 1} scripts -> {archive.relative_to(REPO)}")
    for path in extras.values():
        print(f"extra: {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
