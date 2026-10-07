"""Rehearse a yearly roll on a copy of the book: what breaks, how long it takes, and what needs a human.

    python facts/roll.py rehearse --db NEW/CharlesRiver.sqlite --workdir DIR [--render] [--clean] [--skip-notes]
    python facts/roll_rehearse.py  --db ... --workdir DIR ...          # the same, without roll.py

The rehearsal never touches the book. It copies the tree to DIR/tree (the book's files, facts/ and scripts/companion/;
not outputs/, datasets/, _book/, .quarto/, .git/, node_modules/, drafts/, slides/_build, __pycache__), puts the new
dataset in DIR/data, and then, as a roll would:

 1. rolls the pins of the copy (_variables.yml: edition, window, version, SHA-256; the companion tags of
    scripts/companion/manifest.yml);
 2. checks the new build: the data contract (facts/contract.py), the selection rules of the registry
    (facts/contract_phase7.py), and the claims of the generated notes (facts/notes);
 3. builds the registry of the new build (facts/phase7_cli.py visible), rewrites the copy (facts/roll_text.py --apply)
    and lints the rewritten copy against the new registry;
 4. runs, in the copy, with CHARLESRIVER_DATA at the new dataset: the figure builders (keeping going after a failure),
    check_figures, sql_check, tutorial_queries_check, var_keys_check, the SQL companion build, and
    scripts/build_all.py --check (the slide decks cite figures and tables that exist); with --render, a Quarto HTML
    render of chapters 3 and 11 and a search of the pages for the old edition's IDs and dates.

Every step is timed. DIR/rehearsal-report.md lists each step with its seconds and result, then "Needs a human": the
failing figures with the storyline each one tests, the notes with failing claims, and the
rest. A step ends OK, NEEDS A HUMAN (it ran and found something to decide), or FAILED (it crashed or could not run).
The exit status is 1 only when a step FAILED. Excel and Power BI builds are not run (see the runbook for estimates).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

OK, HUMAN, FAILED, SKIPPED = "OK", "NEEDS A HUMAN", "FAILED", "skipped"
SKIP_NAMES = {"outputs", "datasets", "_book", ".quarto", ".git", "node_modules", "__pycache__", "drafts", "debug.log"}
SKIP_PATHS = {"slides/_build"}
TIMEOUT = 3600

# What each failing figure tests: a storyline of the chapters. Specific figures first, then the chapter.
FIGURE_STORY = {
    "fig-01-06": "the traced sale of Chapters 1 and 3: one revenue posting of an invoice of two desks (SI-2025-007947 in the 2026 edition)",
    "fig-04-04": "Tutorial 4.1's first invoice lines: they predate every promotion (no PromotionID, one Discount value), the 200-row type trap",
    "fig-06-08": "Part II storyline: Furniture's Q3 to Q4 margin falls on the promotion price effect (volume, mix, price lists and cost small beside it)",
    "fig-06-09": "Part II storyline: Furniture's Q3 to Q4 margin bridge is driven by promotions",
    "fig-07-01": "Chapter 7: the first month is a half-size start-up month, so the trend is read with and without it",
    "fig-07-02": "Chapter 7: the regression of monthly revenue on time, with and without the start-up month",
    "fig-07-03": "Chapter 7: the forecast backtest, trend against mean against same quarter last year",
    "fig-10-03": "Part III storyline: the manufacturing variance grows by item group and year (Furniture holds about 70%; no group falls back)",
    "fig-10-06": "Chapter 10: the pre-closing trial balance balances (and equals Chapter 6's)",
    "fig-10-07": "Part III storyline: account 1090's flow (payroll debits rise, standard cost released stays level, the labor variance is favorable and shrinks)",
    "fig-10-09": "Part III storyline: hours per standard hour rise year by year (direct below one, indirect about 0.3 to 0.6)",
    "fig-11-02": "Part III storyline: indirect time is almost absent in the first year's February to May and present every month from June",
    "fig-11-03": "Part III storyline: the direct overtime share is about a tenth in the first half of the first year and a quarter or more in most months of the last",
    "fig-11-05": "Part III storyline: the year-to-date gap in account 1090 grows, and the three-pay-date months are the largest",
    "fig-11-10": "Part III storyline: the trailing twelve-month measure (TTMTotal rises, peaks in the last year's autumn)",
    "fig-12-03": "Chapter 12: the revenue cutoff errors (invoices dated before their shipment, December deliveries invoiced in January)",
    "fig-12-04": "Chapter 12: the three-way match statuses (matched, received not fully invoiced, not yet received, partly received)",
    "fig-12-06": "Chapter 12: purchase order approvals (self-approved, above limit, approved after termination)",
    "fig-12-08": "Part III storyline: surge days (every hourly employee clocks the same hours) grow year by year and hold the growth in overtime",
    "fig-12-10": "Part III storyline: direct labor recorded after its operation ended grows year by year, most of it on surge days",
    "fig-13-05": "Chapter 13: the Validation page's yearly totals reproduce Chapter 6's",
    "fig-13-08": "Chapter 13: monthly revenue stays in a narrow band, so a truncated value axis exaggerates it",
    "fig-14-01": "Chapter 14: the Date table covers every invoice date",
    "fig-14-04": "Chapter 14: context transition (a measure inside an iterator takes the row's values)",
    "fig-14-05": "Chapter 14: CALCULATE replaces and combines filters",
    "fig-14-06": "Chapter 14: the DAX query view's yearly results equal the model's",
    "fig-14-07": "Chapter 14: Furniture's margin falls in the last year's fourth quarter",
    "fig-14-09": "Chapter 14: the year-end closes zero the income statement unless they are excluded",
    "fig-14-11": "Chapter 14: the expense expectation flags the three-pay-date months and the start-up month",
    "fig-15-06": "Chapter 15: the budget variance (flexed commission, the classification effect, the remaining variance)",
    "fig-15-08": "Chapter 15: the budget variance by cost center",
    "fig-15-09": "Chapter 15: the variance reconciliation (flexed budget, classification effect, remaining)",
    "fig-15-12": "Chapter 15: the About page states the data's last dates (time records end before the open pay periods)",
    "fig-16-05": "Chapter 16: the monitoring page's exception counts by test",
    "fig-16-07": "Chapter 16: the review page's open exceptions",
    "fig-19-01": "Chapter 19: the credits cycle's postings, asserted from the ledger",
}
CHAPTER_STORY = {
    1: "Part I: the controller's question and the traced sale", 2: "Part I: data-quality conditions in the tables",
    3: "Part I: the table groups and the traced sale", 4: "Part II: invoice lines and Power Query", 5: "Part II: data preparation",
    6: "Part II storyline: Furniture's margin falls on the promotion price effect", 7: "Part II: monthly revenue, forecast and budget",
    8: "Part II: audit tests (payments, receivables, journal entries)", 9: "Part III storyline: the manufacturing variance",
    10: "Part III storyline: the manufacturing variance and hours", 11: "Part III storyline: indirect time, overtime and the monthly measure",
    12: "Part III storyline: surge days and hours paid beyond the work", 13: "Part IV: the sales report", 14: "Part IV: models and DAX",
    15: "Part IV: management reports", 16: "Part IV: audit monitoring", 17: "Part V: statements for a lender",
    18: "Part V: make, buy, or reprice", 19: "Part V: the customer credits cycle",
}


@dataclass
class Step:
    name: str
    status: str = SKIPPED
    seconds: float = 0.0
    detail: str = ""


@dataclass
class State:
    work: Path
    tree: Path
    data: Path
    steps: list[Step] = field(default_factory=list)
    human: dict[str, list[str]] = field(default_factory=dict)
    limits: list[str] = field(default_factory=list)
    figures: list[dict] = field(default_factory=list)
    env: dict = field(default_factory=dict)

    def need(self, section: str, *items: str) -> None:
        self.human.setdefault(section, []).extend(items)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tidy(text: str, n: int = 200) -> str:
    return re.sub(r"\s+", " ", text).strip()[:n]


def sh(st: State, name: str, args: list[str], cwd: Path | None = None, timeout: int = TIMEOUT) -> tuple[int, str]:
    """Run a command, append its output to DIR/logs/<name>.log, and return (exit code, output)."""
    logs = st.work / "logs"
    logs.mkdir(exist_ok=True)
    try:
        done = subprocess.run(args, cwd=cwd or st.tree, env=st.env, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
        code, text = done.returncode, (done.stdout or "") + (done.stderr or "")
    except subprocess.TimeoutExpired as exc:
        code, text = 124, f"timed out after {timeout}s\n{(exc.stdout or b'')[-2000:]}"
    (logs / f"{name}.log").write_text(f"$ {' '.join(map(str, args))}\n\n{text}", encoding="utf-8")
    return code, text


def py(*args) -> list[str]:
    return [sys.executable, *map(str, args)]


def step(st: State, name: str):
    """Decorator-free helper: run fn(step) and record it. fn sets status and detail; an exception is a FAILED step."""
    def run(fn):
        s = Step(name)
        st.steps.append(s)
        t0 = time.time()
        print(f"... {name}", flush=True)
        try:
            fn(s)
        except Exception as exc:                       # a crashed step is a failure, not a finding
            s.status, s.detail = FAILED, f"{type(exc).__name__}: {tidy(str(exc), 300)}"
        s.seconds = time.time() - t0
        print(f"    {s.status}: {s.detail[:140]} ({s.seconds:.0f}s)", flush=True)
        return s
    return run


# --- 1. the copy -------------------------------------------------------------------------------------------------

def copy_tree(src: Path, dest: Path) -> int:
    n = 0
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src).as_posix()
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES and (f"{rel}/{d}" if rel != "." else d) not in SKIP_PATHS]
        target = dest / rel if rel != "." else dest
        target.mkdir(parents=True, exist_ok=True)
        for f in files:
            if f in SKIP_NAMES or f.endswith(".pyc"):
                continue
            shutil.copy2(Path(root) / f, target / f)        # a real copy: the rewriter writes in place
            n += 1
    return n


def place_data(db: Path, data: Path) -> dict:
    """The new dataset in DIR/data (hard links where possible); a stand-in workbook if the build has none."""
    data.mkdir(parents=True, exist_ok=True)
    out = {}
    for name in ("CharlesRiver.sqlite", "CharlesRiver_support.xlsx", "CharlesRiver.xlsx"):
        src = db.parent / name if name != "CharlesRiver.sqlite" else db
        if not src.is_file():
            continue
        dst = data / name
        if dst.exists():
            dst.unlink()
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
        out[name] = dst
    if "CharlesRiver.xlsx" not in out:
        stand_in = data / "CharlesRiver.xlsx"
        stand_in.write_bytes(b"stand-in for the rehearsal: the SQL companion build only checks this file's hash")
        out["CharlesRiver.xlsx"] = stand_in
        out["stand_in"] = True
    return out


def roll_pins(tree: Path, window: tuple[int, int], sqlite_sha: str, xlsx_sha: str) -> list[str]:
    """_variables.yml and the companion tags, as a roll would set them. Returns what changed."""
    F, C = window
    changed = []
    vp = tree / "_variables.yml"
    text = vp.read_text(encoding="utf-8")
    old_edition = re.search(r'^edition:\s*"?(\d{4})"?', text, re.M).group(1)
    old_version = re.search(r'^\s*version:\s*"(v[\d.]+)"', text, re.M).group(1)
    new_edition, new_version = str(C), f"v{C}.1"
    text = re.sub(r'^(edition:\s*)"?\d{4}"?', rf'\g<1>"{new_edition}"', text, flags=re.M)
    text = re.sub(r'(window:\s*")fiscal \d{4}–\d{4}(")', rf"\g<1>fiscal {F}–{C}\g<2>", text)
    text = text.replace(old_version, new_version)
    text = re.sub(r'(sqlite:\s*")[0-9a-f]{64}(")', rf"\g<1>{sqlite_sha}\g<2>", text)
    text = re.sub(r'(xlsx:\s*")[0-9a-f]{64}(")', rf"\g<1>{xlsx_sha}\g<2>", text)
    vp.write_text(text, encoding="utf-8")
    changed.append(f"_variables.yml: edition {old_edition} to {new_edition}, {old_version} to {new_version}, window fiscal {F}-{C}, SHA-256 of the SQLite file")
    return changed


# --- 2 and 3. the new build, the registry, the roll ------------------------------------------------------------------

def claims_of_notes(db: Path) -> list[tuple[str, list[str]]]:
    """[(note key, its failing claims or its error)] on the dataset (facts/notes)."""
    from db import Data
    from notes import load, render
    d = Data(db)
    bad = []
    for key, note in load().items():
        try:
            _text, _ctx, failed = render(note, d)
        except Exception as exc:
            bad.append((key, [f"cannot render: {tidy(str(exc), 120)}"]))
            continue
        if failed:
            bad.append((key, failed))
    return bad


# --- 4. the figure worker (runs in the copy) -------------------------------------------------------------------

def figures_worker(tree: Path, out: Path) -> int:
    """Build every figure of the checkout, keeping going after a failure; write {figure: message} to `out`."""
    import traceback
    sys.path[:0] = [str(tree / "scripts" / "figures"), str(tree / "scripts"), str(tree)]
    import build                                   # scripts/figures/build.py of the copy
    fails, ok = {}, 0
    groups = list(build.CHAPTERS.items()) + list(build.APPENDICES.items())
    for _key, figures in groups:
        for name, fn in figures.items():
            try:
                fn().save(build.SRC_DIR / f"{name}.drawio")
                ok += 1
            except BaseException as exc:            # an assertion on the data is a finding, not a crash
                tb = traceback.extract_tb(exc.__traceback__)[-1]
                fails[name] = dict(error=type(exc).__name__, message=str(exc)[:240], where=f"{Path(tb.filename).name}:{tb.lineno}",
                                   code=(tb.line or "")[:160])
    out.write_text(json.dumps(dict(built=ok, failed=fails), indent=1), encoding="utf-8")
    return 0


def story_of(figure: str) -> str:
    for prefix, text in FIGURE_STORY.items():
        if figure.startswith(prefix):
            return text
    m = re.match(r"fig-(\d\d)-", figure)
    if m:
        return CHAPTER_STORY.get(int(m.group(1)), "")
    return "Appendix: publishing and security" if figure.startswith("fig-b-") else ""


# --- the rehearsal ---------------------------------------------------------------------------------------------

def rehearse(args: argparse.Namespace) -> int:
    t_all = time.time()
    db = Path(args.db).resolve()
    work = Path(args.workdir).resolve()
    if not db.is_file():
        print(f"error: the new dataset {db} does not exist", file=sys.stderr)
        return 2
    if REPO in work.parents and work.relative_to(REPO).parts[0] not in SKIP_NAMES:
        print(f"error: the work directory {work} is inside the book and would be copied into itself; use outputs/... or a folder outside", file=sys.stderr)
        return 2
    work.mkdir(parents=True, exist_ok=True)
    tree, data = work / "tree", work / "data"
    st = State(work, tree, data)
    st.env = {**os.environ, "PYTHONIOENCODING": "utf-8", "CHARLESRIVER_DATA": str(data)}
    st.env.pop("QUARTO_PROFILE", None)
    old_path = Path(args.old)
    old_rel = old_path.relative_to(REPO).as_posix() if old_path.is_absolute() and REPO in old_path.parents else str(old_path)
    new_json = work / "visible-new.json"
    ctx: dict = {}

    @step(st, "copy the tree")
    def _(s):
        if tree.exists():
            shutil.rmtree(tree, ignore_errors=True)
        n = copy_tree(REPO, tree)
        s.status, s.detail = OK, f"{n} files copied to {tree}"

    @step(st, "place the new dataset")
    def _(s):
        placed = place_data(db, data)
        ctx["sqlite_sha"] = sha256(placed["CharlesRiver.sqlite"])
        ctx["xlsx_sha"] = sha256(placed["CharlesRiver.xlsx"])
        s.status = OK
        s.detail = f"SHA-256 {ctx['sqlite_sha'][:12]}...; " + ("stand-in workbook (the build has no CharlesRiver.xlsx)" if placed.get("stand_in") else "workbook found")
        if placed.get("stand_in"):
            st.limits.append("The new build has no CharlesRiver.xlsx (a stand-in file carries the pinned hash): the figures that read "
                             "the workbook need the real workbook of the new build.")

    @step(st, "contract on the new build")
    def _(s):
        code, text = sh(st, "contract", py("facts/contract.py", "--db", db, "--json", work / "contract.json"), cwd=REPO)
        results = json.loads((work / "contract.json").read_text(encoding="utf-8"))["results"] if (work / "contract.json").exists() else []
        if not results:
            s.status, s.detail = FAILED, "the contract did not run: " + tidy(text, 160)
            return
        failed = [r for r in results if not r["ok"]]
        ctx["window"] = tuple(json.loads((work / "contract.json").read_text(encoding="utf-8")).get("window", ()) or ())
        s.status = HUMAN if failed else OK
        s.detail = f"{len(results) - len(failed)} of {len(results)} pass" + (f"; failing: {', '.join(r['id'] for r in failed)}" if failed else "")
        ctx["contract_failed"] = {r["id"] for r in failed}
        for r in failed:
            st.need("Contract failures on the new build (the generator must plant the condition again, or the chapter must change)",
                    f"{r['id']}: {tidy(r.get('check') or r.get('text') or '', 170)}: {tidy(r.get('detail', ''), 200)}")

    @step(st, "registry rules (contract_phase7)")
    def _(s):
        code, text = sh(st, "contract_phase7", py("facts/contract_phase7.py", "--db", db, "--json", work / "contract_phase7.json"), cwd=REPO)
        p = work / "contract_phase7.json"
        if not p.exists():
            s.status, s.detail = FAILED, "contract_phase7 did not run: " + tidy(text, 160)
            return
        results = json.loads(p.read_text(encoding="utf-8"))["checks"]
        failed = [r for r in results if not r["ok"]]
        s.status = HUMAN if failed else OK
        s.detail = f"{len(results) - len(failed)} of {len(results)} pass" + (f"; failing: {', '.join(r['id'] for r in failed)}" if failed else "")
        for r in failed:
            if r["id"] in ctx.get("contract_failed", ()):
                continue                                   # the contract already lists it
            st.need("Selection rules of the registry that fail on the new build (the wording or the generator must change)",
                    f"{r['id']}: {tidy(r['text'], 170)}: {tidy(r['detail'], 200)}")

    if not args.skip_notes:
        @step(st, "notes claims on the new build")
        def _(s):
            bad = claims_of_notes(db)
            s.status = HUMAN if bad else OK
            s.detail = f"{len(bad)} note(s) with failing claims" if bad else "every claim of every note is true"
            for key, claims in bad:
                st.need("Notes with failing claims (wording to revise before the solution files and Instructor-Notes are rebuilt)",
                        f"{key}: " + "; ".join(tidy(c, 130) for c in claims[:3]) + (f" (+{len(claims) - 3} more)" if len(claims) > 3 else ""))

    @step(st, "registry of the new build")
    def _(s):
        code, text = sh(st, "visible_new", py("facts/phase7_cli.py", "visible", "--db", db, "--out", new_json), cwd=tree)
        if not new_json.exists():
            s.status, s.detail = FAILED, "no registry: " + tidy(text, 200)
            return
        snap = json.loads(new_json.read_text(encoding="utf-8"))
        ctx["new"], ctx["window"] = snap, tuple(snap["window"])
        missing = snap.get("missing", {})
        s.status = HUMAN if missing else OK
        s.detail = f"fiscal {snap['window'][0]}-{snap['window'][1]}, {len(snap['keys'])} keys" + (f"; found nothing: {', '.join(missing)}" if missing else "")
        for name, why in missing.items():
            st.need("Selection rules of the registry that fail on the new build (the wording or the generator must change)", f"{name}: {tidy(why, 160)}")

    @step(st, "roll the pins of the copy")
    def _(s):
        if "window" not in ctx:
            s.status, s.detail = FAILED, "no window: the registry step failed"
            return
        changed = roll_pins(tree, ctx["window"], ctx["sqlite_sha"], ctx["xlsx_sha"])
        s.status, s.detail = OK, "; ".join(c.split(":")[0] for c in changed)

    @step(st, "roll the text of the copy")
    def _(s):
        if "new" not in ctx:
            s.status, s.detail = FAILED, "no new registry"
            return
        report = work / "roll-report.md"
        code, text = sh(st, "roll_text", py("facts/roll_text.py", "--from", old_rel, "--to", new_json, "--apply", "--root", tree,
                                           "--report", report), cwd=tree)
        m = re.search(r"applied: (\d+) rewrites in (\d+) files; (\d+) unresolved, (\d+) stale, (\d+) unclassified", text)
        if not m:
            s.status, s.detail = FAILED, ("the rewriter refused or crashed: " + tidy(text, 220))
            return
        rewrites, files, unresolved, stale, unclassified = map(int, m.groups())
        amb = 0
        if report.exists():
            rep = report.read_text(encoding="utf-8")
            sec = re.search(r"## Ambiguous after the roll.*?\n\n(.*?)\n\n## ", rep, re.S)
            amb = len(re.findall(r"^- ", sec.group(1), re.M)) if sec else 0
            warn = re.search(r"## Warnings for the author\n\n(.*?)\n\n## ", rep, re.S)
            for line in (warn.group(1).splitlines() if warn else []):
                st.need("Warnings of the rewriter (wording tied to a document the new build cannot reproduce exactly)", line.lstrip("- ").strip())
            for title, label in (("Unresolved", "Literals the rewriter could not resolve (no value in the new registry)"),
                                 ("Stale", "Stale literals (the text differs from the old registry)"),
                                 ("Ambiguous after the roll", "Classification collisions after the roll (add a context in values.yml)")):
                sec = re.search(rf"## {title}[^\n]*\n\n(.*?)\n\n## ", rep, re.S)
                for line in (sec.group(1).splitlines() if sec else []):
                    if line.startswith("- "):
                        st.need(label, tidy(line[2:], 240))
        flag = unresolved or stale or unclassified or amb
        s.status = HUMAN if flag else OK
        s.detail = f"{rewrites} literals rewritten in {files} files; {unresolved} unresolved, {stale} stale, {unclassified} unclassified, {amb} ambiguous"

    @step(st, "lint the rolled copy")
    def _(s):
        if "new" not in ctx:
            s.status, s.detail = FAILED, "no new registry"
            return
        code, text = sh(st, "lint_rolled", py("facts/phase7_cli.py", "lint", "--snapshot", new_json, "--root", tree), cwd=tree)
        m = re.search(r"(\d+) literals classified in scope, (\d+) problem", text)
        if not m:
            s.status, s.detail = FAILED, "the lint did not run: " + tidy(text, 200)
            return
        problems = [l for l in text.splitlines() if re.match(r"\S+:\d+: ", l)]
        s.status = HUMAN if int(m.group(2)) else OK
        s.detail = f"{m.group(1)} literals classified, {m.group(2)} problem(s)"
        for line in problems:
            st.need("Literals of the rolled text no rule covers (classify them in facts/literals/)", tidy(line, 230))

    # the checks run in the copy, on the new dataset
    @step(st, "figures: build every figure")
    def _(s):
        out = work / "figures.json"
        if out.exists():
            out.unlink()
        code, text = sh(st, "figures", py("facts/roll_rehearse.py", "--figures-worker", tree, out), cwd=tree)
        if not out.exists():
            s.status, s.detail = FAILED, "the figure worker crashed: " + tidy(text, 220)
            return
        res = json.loads(out.read_text(encoding="utf-8"))
        fails = res["failed"]
        env_fail = {k: v for k, v in fails.items() if v["error"] in ("BadZipFile", "FileNotFoundError") or "zip" in v["message"].lower()}
        s.status = HUMAN if fails else OK
        s.detail = f"{res['built']} built, {len(fails)} failed" + (f" ({len(env_fail)} need the workbook)" if env_fail else "")
        for name in sorted(fails):
            v = fails[name]
            workbook = name in env_fail
            st.figures.append(dict(name=name, **v, workbook=workbook, story=("the figure reads CharlesRiver.xlsx, which the new build does not have"
                                                                               if workbook else story_of(name))))

    @step(st, "figures: check the figure standard")
    def _(s):
        code, text = sh(st, "check_figures", py("scripts/figures/check_figures.py"))
        m = re.search(r"(\d+) figures checked, (\d+) with problems", text)
        if not m:
            s.status, s.detail = FAILED, "check_figures did not run: " + tidy(text, 200)
            return
        s.status = HUMAN if int(m.group(2)) else OK
        s.detail = m.group(0)
        if int(m.group(2)):
            for line in text.splitlines():
                if "problem" in line.lower() and not line.startswith("fig-") or re.search(r"\bERROR\b|\bFAIL\b", line):
                    st.need("Figure standard problems on the rebuilt figures", tidy(line, 200))

    @step(st, "SQL blocks: sql_check")
    def _(s):
        code, text = sh(st, "sql_check", py("scripts/verify/sql_check.py"))
        m = re.search(r"(\d+) problem", text)
        if not m:
            s.status, s.detail = FAILED, "sql_check did not run: " + tidy(text, 200)
            return
        ok = len(re.findall(r"^ok\b", text, re.M))
        s.status = HUMAN if int(m.group(1)) else OK
        s.detail = f"{ok} blocks ok, {m.group(1)} problem(s)"
        for line in text.splitlines():
            if line.startswith("ERROR") or line.startswith("SLOW"):
                st.need("SQL blocks that no longer run on the new build", tidy(line, 200))

    @step(st, "SQL blocks: tutorial_queries_check")
    def _(s):
        code, text = sh(st, "tutorial_queries_check", py("scripts/verify/tutorial_queries_check.py"))
        m = re.search(r"(\d+) problem", text)
        if not m:
            s.status, s.detail = FAILED, "tutorial_queries_check did not run: " + tidy(text, 200)
            return
        n = sum(int(x) for x in re.findall(r"(\d+) queries checked", text))
        s.status = HUMAN if int(m.group(1)) else OK
        s.detail = f"{n} queries checked, {m.group(1)} problem(s)"
        for line in text.splitlines():
            if line and not re.match(r"chapter \d+:|\d+ problem", line):
                st.need("Tutorial SQL that differs from its figure script", tidy(line, 200))

    @step(st, "variables: var_keys_check")
    def _(s):
        code, text = sh(st, "var_keys_check", py("scripts/verify/var_keys_check.py"))
        m = re.search(r"(\d+) var shortcodes checked, (\d+) problem", text)
        if not m:
            s.status, s.detail = FAILED, "var_keys_check did not run: " + tidy(text, 200)
            return
        s.status = HUMAN if int(m.group(2)) else OK
        s.detail = m.group(0)
        for line in text.splitlines():
            if "unknown variable" in line:
                st.need("Unknown {{< var >}} keys", tidy(line, 200))

    @step(st, "SQL companion build")
    def _(s):
        code, text = sh(st, "companion_sql", py("scripts/companion/build.py", "--tool", "sql"))
        built = re.findall(r"^(\S+): (\d+) scripts? -> (\S+)", text, re.M)
        if code != 0 or not built:
            s.status, s.detail = FAILED, f"exit {code}: " + tidy(text[-300:], 240)
            return
        s.status, s.detail = OK, f"{len(built)} chains built ({sum(int(b[1]) for b in built)} scripts)"

    @step(st, "slides: build_all --check")
    def _(s):
        # The decks cite the book's figures and tables by ID and follow the rolled text on the next build;
        # there is no slide review. The check fails only if a deck cites something the book no longer has.
        code, text = sh(st, "build_all_check", py("scripts/build_all.py", "--check"))
        if code == 0:
            s.status, s.detail = OK, "every cited figure, table and tutorial exists"
            return
        s.status, s.detail = FAILED, f"exit {code}: " + tidy(text[-300:], 240)

    if args.render:
        @step(st, "HTML render of chapters 3 and 11")
        def _(s):
            q = tree / "_quarto.yml"
            text = q.read_text(encoding="utf-8")
            q.write_text(re.sub(r"^  pre-render:\n(?:    - .*\n)+", "", text, flags=re.M), encoding="utf-8")   # the figures are the copy's own
            quarto = shutil.which("quarto") or os.environ.get("QUARTO_BIN")
            if not quarto:
                s.status, s.detail = SKIPPED, "quarto not found"
                return
            pages = ["chapters/03-accounting-data-environment/chapter.qmd", "chapters/11-analytical-queries/chapter.qmd"]
            for page in pages:
                code, text = sh(st, "render_" + Path(page).parent.name, [quarto, "render", page, "--to", "html"])
                if code != 0:
                    s.status, s.detail = FAILED, f"quarto render {page} exited {code}: " + tidy(text[-300:], 240)
                    return
            old = json.loads((tree / old_rel).read_text(encoding="utf-8"))["keys"] if (tree / old_rel).exists() else {}
            new = ctx.get("new", {}).get("keys", {})
            probes = {k: str(old[k]) for k in ("id.trace.invoice", "date.time_records_end", "id.close.pl.C") if k in old and old.get(k) != new.get(k)}
            left = []
            for page in pages:
                html = tree / "_book" / Path(page).with_suffix(".html")
                body = html.read_text(encoding="utf-8") if html.is_file() else ""
                if not body:
                    s.status, s.detail = FAILED, f"no rendered page {html}"
                    return
                for k, v in probes.items():
                    if v in body:
                        left.append(f"{Path(page).parent.name}: {v} ({k}) remains {body.count(v)} time(s)")
            s.status = HUMAN if left else OK
            s.detail = f"2 pages rendered; " + ("old literals remain: " + "; ".join(left) if left else f"none of {', '.join(probes.values()) or 'the probes'} remains")
            for l in left:
                st.need("Old literals still in the rendered pages (the rewriter missed them)", l)

    total = time.time() - t_all
    write_report(st, db, args, total)
    if args.clean:
        shutil.rmtree(tree, ignore_errors=True)
        shutil.rmtree(data, ignore_errors=True)
    failed = [s for s in st.steps if s.status == FAILED]
    print(f"\nrehearsal: {len(st.steps)} steps, {len(failed)} failed, {sum(1 for s in st.steps if s.status == HUMAN)} need a human; "
          f"{total:.0f}s; report {work / 'rehearsal-report.md'}")
    return 1 if failed else 0


def write_report(st: State, db: Path, args, total: float) -> None:
    L = ["# Rehearsal of the roll", "",
         f"- Dataset: `{db}`", f"- Old registry: `{args.old}`", f"- Work directory: `{st.work}`",
         f"- Date: {time.strftime('%Y-%m-%d %H:%M')}; total {total:.0f} s ({total / 60:.1f} min)",
         f"- Impact report of the roll (every literal rewritten, with its key): `{st.work / 'roll-report.md'}`; step logs: `{st.work / 'logs'}`",
         f"- The rolled copy: `{st.tree}`" + (" (removed: --clean)" if getattr(args, "clean", False) else ""), "",
         "| Step | Seconds | Result | Detail |", "|---|---:|---|---|"]
    for s in st.steps:
        L.append(f"| {s.name} | {s.seconds:.0f} | {s.status} | {s.detail.replace('|', '/')} |")
    L.append(f"| **Total** | **{total:.0f}** | | {sum(1 for s in st.steps if s.status == FAILED)} failed, "
             f"{sum(1 for s in st.steps if s.status == HUMAN)} need a human |")
    L += ["", "## Needs a human", ""]
    if st.figures:
        real = [f for f in st.figures if not f["workbook"]]
        L += [f"### Figures that fail on the new build ({len(real)})", "",
              "An AssertionError is a figure builder stating a condition of the data; the storyline says what the chapter relies on. "
              "Either the generator plants the condition or the wording and the assertion change. Any other error is a layout "
              "or code failure to look at.", "",
              "| Figure | Storyline it tests | Assertion | Where |", "|---|---|---|---|"]
        for f in real:
            msg = (f["message"] or f["code"]).replace("|", "/").replace("\n", " ")
            L.append(f"| {f['name']} | {f['story']} | {f['error']}: {msg[:110]} | `{f['where']}` |")
        wb = [f for f in st.figures if f["workbook"]]
        if wb:
            L += ["", f"### Figures that need the new build's CharlesRiver.xlsx ({len(wb)})", "",
                  ", ".join(f["name"] for f in wb), ""]
    for section, items in st.human.items():
        L += ["", f"### {section} ({len(items)})", ""] + [f"- {i}" for i in items]
    if not st.figures and not st.human:
        L.append("Nothing: every step passed.")
    L += ["", "## Not rehearsed", ""] + [f"- {x}" for x in st.limits] + [
          "- Excel, Power BI and the Python-driven Office builds (they need Windows with Excel and Power BI Desktop): see the runbook for time estimates.",
          "- PDF, EPUB and DOCX renders; a full HTML render; slide decks' render.", ""]
    (st.work / "rehearsal-report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("--db", type=Path, required=True, help="the new build's CharlesRiver.sqlite")
    p.add_argument("--workdir", type=Path, required=True, help="where the copy, the data and the report go")
    p.add_argument("--old", type=Path, default=HERE / "visible-2026.json", help="the old edition's registry")
    p.add_argument("--render", action="store_true", help="also render chapters 3 and 11 to HTML and search them for old IDs and dates")
    p.add_argument("--clean", action="store_true", help="remove DIR/tree and DIR/data when done (the report and logs stay)")
    p.add_argument("--skip-notes", action="store_true", help="skip the notes' claims (about 90 s)")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--figures-worker"]:
        return figures_worker(Path(argv[1]), Path(argv[2]))
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    add_arguments(parser)
    return rehearse(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
