"""The preflight of a yearly roll: does a new dataset build carry the book, and what would the roll change?

    python facts/roll.py preflight --db NEW/CharlesRiver.sqlite [--old facts/visible-2026.json] [--workdir DIR]
    python facts/roll.py rehearse  --db NEW/CharlesRiver.sqlite --workdir DIR [--render] [--clean]   # see facts/roll_rehearse.py

Four steps, each timed, and a verdict (see facts/ROLL.md for the whole runbook):

1. the data contract on the new build (facts/contract.py): every storyline and quirk the chapters rely on;
2. the registry of the new build (facts/phase7_cli.py visible): the years, document IDs, dates and values the text
   shows; a selection rule that finds nothing is listed and fails the preflight;
3. the generated notes on the new build (facts/notes): every claim a note's wording makes, evaluated on the new data;
   a failing claim is wording to revise (the notes are no longer in the chapters; they are rendered into the solution
   files and Instructor-Notes-2026.zip);
4. a dry run of the text rewriter (facts/roll_text.py, no --apply): how many literals change, and whether any is
   unresolved, stale or unclassified.

Nothing in the book is changed. The reports and a log (roll-log.md) go to the work directory.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))


def run(args: list[str], log: Path) -> tuple[int, str, float]:
    """Run a command in the repository folder; its output is appended to the log. Returns (exit code, text, seconds)."""
    start = time.time()
    done = subprocess.run([sys.executable, *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    text = (done.stdout or "") + (done.stderr or "")
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {' '.join(args)}\n\n```\n{text.strip()}\n```\n")
    return done.returncode, text, time.time() - start


def failing_notes(db: Path) -> tuple[int, int, list[str]]:
    """(notes, notes with a failing claim or an error, their keys) on the dataset."""
    from db import Data
    from notes import load, render
    d = Data(db)
    bad = []
    notes = load()
    for key, note in notes.items():
        try:
            _text, _ctx, failed = render(note, d)
        except Exception as exc:                 # a note that cannot be computed on the new window is a failure
            bad.append(f"{key} (error: {str(exc)[:70]})")
            continue
        if failed:
            bad.append(f"{key} ({len(failed)} claim{'s' if len(failed) > 1 else ''})")
    return len(notes), len(bad), bad


def preflight(args: argparse.Namespace) -> int:
    work = args.workdir
    work.mkdir(parents=True, exist_ok=True)
    log = work / "roll-log.md"
    log.write_text(f"# Roll preflight\n\nDataset: `{args.db}`\nOld registry: `{args.old}`\n", encoding="utf-8")
    rows, problems, todo = [], [], []     # problems stop the roll; todo is wording for a person (step 6 of facts/ROLL.md)
    t0 = time.time()

    code, text, sec = run(["facts/contract.py", "--db", str(args.db), "--json", str(work / "contract.json")], log)
    result = json.loads((work / "contract.json").read_text(encoding="utf-8"))["results"] if (work / "contract.json").exists() else []
    failed = [r["id"] for r in result if not r["ok"]]
    rows.append(("data contract", f"{len(result) - len(failed)} of {len(result)} pass" + (f"; failing: {', '.join(failed)}" if failed else ""), sec))
    if failed or not result:
        problems.append(f"the contract fails: {', '.join(failed) or 'it did not run'}: the generator must plant the condition again, or the chapter must change")

    new_json = work / "visible-new.json"
    code, text, sec = run(["facts/phase7_cli.py", "visible", "--db", str(args.db), "--out", str(new_json)], log)
    missing = []
    if new_json.exists():
        snap = json.loads(new_json.read_text(encoding="utf-8"))
        missing = list(snap.get("missing", []) or [])
    summary = re.search(r"fiscal [\d-]+, \d+ keys", text)
    rows.append(("registry of the new build", (summary.group(0) if summary else "no registry") + (f"; rules that found nothing: {', '.join(map(str, missing))}" if missing else ""), sec))
    if not new_json.exists():
        problems.append("the registry could not be built on the new dataset")
    elif missing:
        problems.append(f"{len(missing)} selection rule(s) found nothing: {', '.join(map(str, missing))}")

    start = time.time()
    try:
        total, n_bad, bad = failing_notes(args.db)
        rows.append(("generated notes", f"{total - n_bad} of {total} render with every claim true" + (f"; wording to revise: {', '.join(bad)}" if bad else ""), time.time() - start))
        if bad:
            todo.append(f"{n_bad} note(s) have failing claims: wording to revise before the instructor files are rebuilt")
    except Exception as exc:
        rows.append(("generated notes", f"could not run: {exc}", time.time() - start))
        problems.append("the notes could not be evaluated")

    if new_json.exists():
        report = work / "roll-report.md"
        code, text, sec = run(["facts/roll_text.py", "--from", str(args.old), "--to", str(new_json), "--report", str(report)], log)
        last = next((l for l in reversed(text.strip().splitlines()) if "planned" in l), (text.strip().splitlines() or ["no output"])[-1])
        rows.append(("dry run of the rewriter", last.strip()[:150], sec))
        m = re.search(r"(\d+) unresolved, (\d+) stale, (\d+) unclassified", last)
        if code != 0 or not m or any(int(x) for x in m.groups()):
            problems.append(f"the rewriter reports: {last.strip()[:120]} (see {report})")

    lines = [f"Preflight of {args.db} against {args.old}", ""]
    lines += [f"  {name:28} {sec:6.0f}s  {detail}" for name, detail, sec in rows]
    lines += ["", f"  total {time.time() - t0:.0f}s; reports in {work}", ""]
    if problems:
        lines += ["  VERDICT: NOT YET:"] + [f"    - {p}" for p in problems]
    else:
        lines += ["  VERDICT: GO: the build carries the book; run the roll (facts/ROLL.md step 4)"]
        if todo:
            lines += ["  For a person, after the roll:"] + [f"    - {x}" for x in todo]
    out = "\n".join(lines)
    print(out)
    with log.open("a", encoding="utf-8") as fh:
        fh.write("\n# Summary\n\n```\n" + out + "\n```\n")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preflight", help="contract, registry, notes and a dry-run roll on a new dataset build")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--old", type=Path, default=HERE / "visible-2026.json")
    p.add_argument("--workdir", type=Path, default=REPO / "outputs" / "roll-preflight")
    p = sub.add_parser("rehearse", help="roll a copy of the book on a new build and run the checks, timed (facts/roll_rehearse.py)")
    import roll_rehearse
    roll_rehearse.add_arguments(p)
    args = parser.parse_args()
    return roll_rehearse.rehearse(args) if args.command == "rehearse" else preflight(args)


if __name__ == "__main__":
    raise SystemExit(main())
