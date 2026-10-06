"""The facts registry: generated instructor notes, kept in step with the dataset.

    python scripts/facts.py check [--db PATH]      # does every note render, and does every claim its wording makes hold? (exit 1 if not)
    python scripts/facts.py build [--db PATH] --out snapshot.json   # values, text, and claims of every note
    python scripts/facts.py diff OLD.json NEW.json [--out report.md]  # what a new dataset changes, note by note
    python scripts/facts.py sync | mark            # retired: the chapters carry no notes (see below)

The notes are rendered from their templates (facts/notes/templates) into the solution files and
Instructor-Notes.zip (facts/instructor/package.py), never into the chapter text: the chapters stay clean
(author's decision, 2026-10-05). `sync` and `mark` wrote notes into the .qmd between markers in the first design; they
now refuse to run, unless --inline is given (the old behavior, only for a copy of the book that wants notes inline).
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DB, REPO  # noqa: E402

sys.path.insert(0, str(REPO / "facts"))
import notes  # noqa: E402
from db import Data  # noqa: E402


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def rendered_all(d: Data) -> dict[str, tuple[str, dict, list[str]]]:
    return {key: notes.render(n, d) for key, n in notes.load().items()}


def cmd_check(args) -> int:
    d = Data(args.db)
    problems = 0
    lock = notes.read_lock()
    for key, (text, _, failed) in rendered_all(d).items():
        n = notes.NOTES[key]
        found = notes.regions(REPO / n.file).get(key)
        if found is None:
            status = "ok (rendered; the chapters carry no notes)"
        elif found[2] == text:
            status = "ok"
        elif norm(found[2]) == norm(text):
            status = "ok (line breaks differ; sync rewraps)"
        elif key in lock and notes.digest(found[2]) != lock[key]:
            status = "EDITED BY HAND since the last sync"
        else:
            status = "DIFFERS from the data (run sync)"
        bad = not status.startswith("ok") or failed
        problems += bool(bad)
        print(f"{'ok  ' if not bad else 'FAIL'} {key:10} {status}")
        for f in failed:
            print(f"       claim fails: {f}")
    print(f"{len(notes.NOTES)} notes, {problems} problem(s), fiscal {d.F}-{d.C}")
    return 1 if problems else 0


def retired(args, name: str) -> bool:
    """sync and mark write comments into the chapters, which stay clean: refuse unless --inline is given."""
    if getattr(args, "inline", False):
        return False
    print(f"{name} is retired: the chapters carry no notes (rendered into the solution files and Instructor-Notes.zip "
          "by facts/instructor/package.py). Pass --inline only for a copy of the book that should carry them.")
    return True


def cmd_sync(args) -> int:
    if retired(args, "sync"):
        return 2
    d = Data(args.db)
    lock = notes.read_lock()
    by_file: dict[str, list[tuple[str, str]]] = {}
    refused = 0
    for key, (text, _, failed) in rendered_all(d).items():
        n = notes.NOTES[key]
        found = notes.regions(REPO / n.file).get(key)
        if found is None:
            print(f"skip {key}: no marker in {n.file} (run mark)")
            continue
        if failed and not args.force:
            print(f"skip {key}: claims fail on this dataset ({'; '.join(failed)}); revise the template")
            refused += 1
            continue
        current = found[2]
        edited = key in lock and notes.digest(current) != lock[key] and current != text
        first = key not in lock and norm(current) != norm(text)
        if (edited or first) and not args.force:
            why = "edited by hand since the last sync" if edited else "not yet synced and its text differs"
            print(f"skip {key}: {why}; port the change to the template, or use --force")
            refused += 1
            continue
        by_file.setdefault(n.file, []).append((key, text))
    for file, items in by_file.items():
        path = REPO / file
        content = path.read_text(encoding="utf-8")
        found = notes.regions(path)
        changed = 0
        for key, text in sorted(items, key=lambda kt: -found[kt[0]][0]):    # from the end, so offsets stay valid
            start, end, current = found[key]
            if current != text:
                content = content[:start] + text + content[end:]
                changed += 1
            lock[key] = notes.digest(text)
        if changed:
            path.write_text(content, encoding="utf-8", newline="")
        print(f"{file}: {changed} of {len(items)} notes rewritten")
    notes.write_lock(lock)
    return 1 if refused else 0


def cmd_mark(args) -> int:
    if retired(args, "mark"):
        return 2
    d = Data(args.db)
    for key, (text, _, _) in rendered_all(d).items():
        n = notes.NOTES[key]
        path = REPO / n.file
        if key in notes.regions(path):
            continue
        content = path.read_text(encoding="utf-8")
        target = norm(text)
        hits = [m for m in re.finditer(r"<!--.*?-->", content, flags=re.S) if norm(m.group(0)) == target]
        if len(hits) != 1:
            print(f"{key}: {len(hits)} matching comments in {n.file}; not marked")
            continue
        m = hits[0]
        content = content[:m.start()] + f"<!-- notes: {key} -->\n" + content[m.start():]
        path.write_text(content, encoding="utf-8", newline="")
        print(f"{key}: marked in {n.file}")
    return 0


def cmd_preview(args) -> int:
    """Render one module's notes before they are marked: each must match a comment of its file
    (whitespace aside), and its claims must hold on the edition's dataset."""
    import importlib
    importlib.import_module(f"notes.{args.module}")
    keys = [k for k in notes.NOTES if k.startswith(args.module + ".")]
    d = Data(args.db)
    extra = Data(args.also) if args.also else None
    problems = 0
    for key in keys:
        n = notes.NOTES[key]
        try:
            text, _, failed = notes.render(n, d)
        except Exception as exc:  # report and go on to the next note
            print(f"FAIL {key}: render error: {type(exc).__name__}: {exc}")
            problems += 1
            continue
        content = (REPO / n.file).read_text(encoding="utf-8")
        comments = [m.group(0) for m in re.finditer(r"<!--.*?-->", content, flags=re.S)]
        match = any(norm(c) == norm(text) for c in comments)
        if args.reworded:
            # A rewording pass: the note may differ from its comment; show how, word by word.
            current = notes.regions(REPO / n.file).get(key)
            if current and norm(current[2]) != norm(text):
                a, b = norm(current[2]).split(" "), norm(text).split(" ")
                for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
                    if op != "equal":
                        print(f"     {key} {op}: {' '.join(a[i1:i2])[:160]!r} -> {' '.join(b[j1:j2])[:160]!r}")
            match = True
        status = "matches its comment" if match else "NO MATCHING COMMENT"
        if not match:
            label = text.split(":", 1)[0]
            near = next((c for c in comments if c.startswith(label)), None)
            if near:
                a, b = norm(text), norm(near)
                i = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
                status += f"\n       rendered: ...{a[max(0, i - 60):i + 80]}\n       comment:  ...{b[max(0, i - 60):i + 80]}"
        bad = not match or failed
        problems += bool(bad)
        print(f"{'ok  ' if not bad else 'FAIL'} {key:12} {status}")
        for f in failed:
            print(f"       claim fails on the edition's dataset: {f}")
        if extra is not None:
            try:
                _, _, failed2 = notes.render(n, extra)
                for f in failed2:
                    print(f"       (rolled dataset) claim fails: {f}")
            except Exception as exc:
                print(f"       (rolled dataset) render error: {type(exc).__name__}: {exc}")
    print(f"{len(keys)} notes in {args.module}, {problems} problem(s)")
    return 1 if problems else 0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_build(args) -> int:
    d = Data(args.db)
    snapshot = dict(db=str(args.db), sha256=sha256(Path(args.db)), window=[d.F, d.C], notes={})
    for key, (text, values, failed) in rendered_all(d).items():
        snapshot["notes"][key] = dict(file=notes.NOTES[key].file, values=notes.plain(values), text=text, failed=failed)
    Path(args.out).write_text(json.dumps(snapshot, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out}: {len(snapshot['notes'])} notes, fiscal {d.F}-{d.C}")
    return 0


def flatten(value, prefix=""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from flatten(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from flatten(v, f"{prefix}[{i}]")
    else:
        yield prefix, value


def cmd_diff(args) -> int:
    old = json.loads(Path(args.old).read_text(encoding="utf-8"))
    new = json.loads(Path(args.new).read_text(encoding="utf-8"))
    lines = [f"# What the new dataset changes in the notes", "",
             f"- Old: `{old['db']}`, fiscal {old['window'][0]}-{old['window'][1]}",
             f"- New: `{new['db']}`, fiscal {new['window'][0]}-{new['window'][1]}", ""]
    summary = []
    for key in sorted(set(old["notes"]) | set(new["notes"])):
        a, b = old["notes"].get(key), new["notes"].get(key)
        if a is None or b is None:
            summary.append((key, "added" if a is None else "removed", 0, []))
            continue
        va, vb = dict(flatten(a["values"])), dict(flatten(b["values"]))
        changed = [(k, va.get(k), vb.get(k)) for k in sorted(set(va) | set(vb)) if va.get(k) != vb.get(k)]
        summary.append((key, "claims fail" if b["failed"] else ("changed" if changed else "unchanged"), len(changed), b["failed"]))
        if not changed and not b["failed"]:
            continue
        lines += [f"## {key} ({b['file']})", ""]
        for f in b["failed"]:
            lines.append(f"- **Claim fails, revise the wording:** {f}")
        if b["failed"]:
            lines.append("")
        lines.append(f"{len(changed)} values change.")
        lines += ["", "```diff"] + list(difflib.unified_diff(a["text"].splitlines(), b["text"].splitlines(), "old", "new", lineterm="", n=0)) + ["```", ""]
    head = ["| Note | Status | Values changed |", "|---|---|---|"] + [f"| {k} | {s} | {n} |" for k, s, n, _ in summary] + [""]
    report = "\n".join(lines[:5] + head + lines[5:])
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(report)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("check", "sync", "mark", "build"):
        p = sub.add_parser(name)
        p.add_argument("--db", type=Path, default=DB)
        if name in ("sync", "mark"):
            p.add_argument("--inline", action="store_true", help="write the notes into the chapters (retired)")
        if name == "sync":
            p.add_argument("--force", action="store_true")
        if name == "build":
            p.add_argument("--out", required=True)
    p = sub.add_parser("diff")
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--out")
    p = sub.add_parser("preview")
    p.add_argument("module")
    p.add_argument("--db", type=Path, default=DB)
    p.add_argument("--also", type=Path, help="a second dataset (a rolled build) to run the claims on")
    p.add_argument("--reworded", action="store_true",
                   help="a rewording pass: do not require the note to match its comment; show the word changes")
    args = parser.parse_args()
    return dict(check=cmd_check, sync=cmd_sync, mark=cmd_mark, build=cmd_build, diff=cmd_diff,
                preview=cmd_preview)[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
