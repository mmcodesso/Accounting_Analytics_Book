"""Build the companion files listed in manifest.yml into outputs/companion/<release_tag>/.

Usage: python scripts/companion/build.py [--tool sql] [--chapter 10]

SQL chains come from the chapter scripts in scripts/figures (dbbrowser.Script), the same
scripts the tutorial text and figures must match. For every tutorial the builder writes the
script as it stands at the end of that tutorial. A start file is exactly the script the reader
would have typed, so its line numbers match the book's figures. Two things are added, and
neither changes the line count:
  - the header's "your name, date" becomes a stamp (the checkpoint and the dataset release);
  - each query's last line gets a trailing "-- Result: ..." comment from running it read-only.
The builder refuses to run unless datasets/CharlesRiver.sqlite is the release pinned in
_variables.yml, so every expected result comes from the files readers download.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import re
import shutil
import sqlite3
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DB, FIGURES, REPO, db_uri, require_dataset  # noqa: E402

sys.path.insert(0, str(FIGURES))
import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
TUTORIAL = re.compile(r"^-- Tutorial (\d+)\.(\d+)\b")
ZIP_DATE = (2026, 1, 1, 0, 0, 0)          # fixed, so a rebuild of unchanged files is byte-identical
SITE = "https://aa.accountinganalyticshub.com/front-matter/companion-files.html"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_dataset(variables: dict) -> None:
    require_dataset()
    digest = hashlib.sha256()
    with DB.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    pinned = variables["dataset"]["sha256"]["sqlite"]
    if digest.hexdigest() != pinned:
        raise SystemExit(f"{DB} is not dataset release {variables['dataset']['version']} "
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
    readme = [f"Accounting Analytics: An Integrated Approach ({variables['edition']} edition)",
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


def zip_folder(folder: Path, extra_files: list[Path] = ()) -> Path:
    target = folder.with_name(f"{folder.name}-companion.zip")
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files + list(extra_files):
            arc = p.relative_to(folder).as_posix() if p.is_relative_to(folder) else p.name
            info = zipfile.ZipInfo(arc, ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, p.read_bytes())
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tool", choices=["sql"], default=None)
    parser.add_argument("--chapter", type=int, default=None)
    args = parser.parse_args()

    manifest = load_yaml(HERE / "manifest.yml")
    variables = load_yaml(REPO / "_variables.yml")
    check_dataset(variables)
    out = REPO / "outputs" / "companion" / manifest["release_tag"]
    out.mkdir(parents=True, exist_ok=True)

    extras = {e["id"]: build_extra(e, variables, out) for e in manifest.get("extras", [])
              if args.tool in (None, e["tool"]) and args.chapter in (None, 11)}
    for chain in manifest["chains"]:
        if args.tool not in (None, chain["tool"]) or args.chapter not in (None, chain["chapter"]):
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
