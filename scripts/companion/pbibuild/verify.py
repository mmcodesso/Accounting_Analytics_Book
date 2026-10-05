"""Run verify.ps1 on a project and judge the result: the model loads and refreshes, every check in the Checks query
agrees, and every report page shows its visuals with no error message."""

from __future__ import annotations

import json
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK_FILE = Path(os.environ.get("TEMP", ".")) / "accounting-analytics-pbidesktop.lock"


@contextmanager
def desktop_lock(timeout: float = 4 * 3600):
    """One verification at a time on this machine: verify.ps1 knows its Desktop instance only as the one that was
    not running before it started, so two runs at once could each take, and close, the other's instance."""
    import msvcrt
    fh = open(LOCK_FILE, "a+b")
    deadline = time.time() + timeout
    while True:
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            break
        except OSError:
            if time.time() > deadline:
                fh.close()
                raise TimeoutError("another Power BI verification held the lock for too long")
            time.sleep(3)
    try:
        yield
    finally:
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            fh.close()
ERRORS = ("Something's wrong", "Can't display", "Couldn't load", "couldn't be displayed", "Fields that need to be fixed",
          "See details", "Error fetching data")


def run(pbip: Path, table: str, checks_file: Path, pages: list[str], out_json: Path, render_seconds: int = 12,
        dax_view: bool = True, role_checks: Path | None = None, capture_dir: Path | None = None) -> dict:
    """`role_checks`: an optional JSON file listing checks queries to run under a role ([{label, role, user, file}]).
    `capture_dir`: an optional folder for an image of Desktop's window on each page (what UI Automation cannot read)."""
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "verify.ps1"),
           "-Pbip", str(pbip), "-Table", table, "-ChecksFile", str(checks_file), "-OutJson", str(out_json),
           "-RenderSeconds", str(render_seconds)] + (["-DaxView"] if dax_view else [])
    if role_checks:
        cmd += ["-RoleChecks", str(role_checks)]
    if capture_dir:
        cmd += ["-CaptureDir", str(capture_dir)]
    if pages:
        cmd += ["-Pages", ";".join(pages)]
    if out_json.exists():
        out_json.unlink()
    with desktop_lock():
        run = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=3600)
    if not out_json.exists():
        raise RuntimeError("\n".join(["verify.ps1 wrote no result:", run.stdout, run.stderr]))
    return json.loads(out_json.read_text(encoding="utf-8-sig"))


def judge(result: dict, expect_pages: dict[str, list[str]], dax_tabs: list[str] = ()) -> list[str]:
    """Problems found: an unloaded model, a check that does not agree, a page with an error or a missing visual.
    `expect_pages` maps a page's display name to strings that must appear among its names (titles, values)."""
    problems = []
    if result.get("error"):
        problems.append(f"verification error: {result['error']}")
    if not result.get("loaded"):
        problems.append("the model did not load")
        return problems
    checks = result.get("checks") or []
    if isinstance(checks, dict):
        checks = [checks]
    if not checks:
        problems.append("the Checks query returned nothing")
    for c in checks:
        if c.get("Agrees") is not True:
            problems.append(f"check fails: {c.get('Section')}: {c.get('Check')}: expected {c.get('Expected')}, "
                            f"actual {c.get('Actual')}")
    for label, rc in (result.get("roleChecks") or {}).items():
        rows = rc.get("rows") or []
        rows = [rows] if isinstance(rows, dict) else rows
        if rc.get("expectError"):                 # the query must fail for the role (object-level security)
            if rc["expectError"].lower() not in (rc.get("error") or "").lower():
                problems.append(f"role checks {label}: expected an error containing '{rc['expectError']}', got "
                                f"{rc.get('error') or 'no error'}")
            continue
        if rc.get("error") or not rows:
            problems.append(f"role checks {label}: {rc.get('error') or 'the query returned nothing'}")
        for c in rows:
            if c.get("Agrees") is not True:
                problems.append(f"role check fails ({label}): {c.get('Check')}: expected {c.get('Expected')}, "
                                f"actual {c.get('Actual')}")
    for page, wanted in expect_pages.items():
        info = (result.get("pages") or {}).get(page)
        if not info:
            problems.append(f"page {page}: not read")
            continue
        if not info.get("selected"):
            problems.append(f"page {page}: its tab could not be selected")
        names = info.get("names") or []
        bad = [n for n in names if any(err.lower() in n.lower() for err in ERRORS)]
        if bad:
            problems.append(f"page {page}: shows an error: {bad[:3]}")
        for w in wanted:
            if not any(w in n for n in names):
                problems.append(f"page {page}: '{w}' not found on the canvas")
    if dax_tabs:
        view = result.get("daxView") or {}
        if not view.get("selected"):
            problems.append("DAX query view could not be selected")
        for tab in dax_tabs:
            if tab not in (view.get("names") or []):
                problems.append(f"DAX query view: no query tab '{tab}'")
    return problems
