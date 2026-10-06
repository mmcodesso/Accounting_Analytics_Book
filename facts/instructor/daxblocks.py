"""The marked DAX blocks of a tutorial or exercise file, with or without the `<!-- dax-check: kind -->` markers.

The Power BI builders (scripts/companion/pbibuild) read the measures, tables and test queries of the tutorials from the
code blocks that carry a marker.  The public text no longer holds the markers (the upstream removal of 2026-10-05), so
a file without markers is read through the index archived from commit 4feb03f (dax-markers-4feb03f.json): for each
marked file, the kind of each marker and the position of its code block among the file's fenced blocks.  The blocks
themselves always come from the text as it is now, so a roll that rewrites a year inside a block is followed.

    python facts/instructor/daxblocks.py --build-index    # rebuild the index from commit 4feb03f (needs git history)
    python facts/instructor/daxblocks.py --check          # the index on today's files equals the markers of 4feb03f

A file whose number of fenced blocks differs from the archived count raises an error: the structure changed, and the
index must be revised (by whoever changed the text) before a build.
"""

from __future__ import annotations

import json
import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INDEX = HERE / "dax-markers-4feb03f.json"
CRLF, LF = chr(13) + chr(10), chr(10)
FENCE = re.compile(r"^```[^\n]*\n(.*?)\n```", re.M | re.S)
MARKED = re.compile(r"<!-- dax-check: (\w+) -->\s*\n```\s*\n(.*?)\n```", re.S)


def rel(path: Path | str) -> str:
    p = Path(path)
    return p.resolve().relative_to(REPO).as_posix() if p.is_absolute() else p.as_posix()


def tidy(body: str) -> str:
    return textwrap.dedent(body).strip("\n")


def blocks_with_markers(text: str, kind: str) -> list[str]:
    """The original reading: the blocks whose marker is in the text."""
    return [tidy(m.group(2)) for m in MARKED.finditer(text) if m.group(1) == kind]


def fenced(text: str) -> list[str]:
    return [m.group(1) for m in FENCE.finditer(text)]


def dax_blocks(path: Path | str, kind: str, text: str | None = None) -> list[str]:
    """The blocks of `kind` ('measure', 'column', 'table', 'query', 'skip') of the file, in order, without their
    common indent: by the markers when the text has them, else by the archived index."""
    path = Path(path)
    text = path.read_text(encoding="utf-8") if text is None else text
    if "<!-- dax-check:" in text:
        return blocks_with_markers(text, kind)
    entry = json.loads(INDEX.read_text(encoding="utf-8"))["files"].get(rel(path))
    if entry is None:
        return []                                  # a file that never held markers
    all_blocks = fenced(text)
    if len(all_blocks) != entry["fences"]:
        raise ValueError(f"{rel(path)} has {len(all_blocks)} code blocks, the archived index {entry['fences']}: "
                         "the markers' index no longer fits the text; revise facts/instructor/dax-markers-4feb03f.json")
    return [tidy(all_blocks[m["fence"]]) for m in entry["markers"] if m["kind"] == kind]


# --- the index and its proof -------------------------------------------------------------------------------------------

def ordered_blocks(path: Path | str, text: str | None = None) -> list[tuple[int, str, str]]:
    """(line, kind, body) of every marked block of the file, in file order, with the line of its code fence: by the
    markers when the text has them, else by the archived index. The DAX scripts of scripts/verify use this."""
    path = Path(path)
    text = path.read_text(encoding="utf-8") if text is None else text
    if "<!-- dax-check:" in text:
        return [(text[:m.start()].count(LF) + 1, m.group(1), tidy(m.group(2))) for m in MARKED.finditer(text)]
    entry = json.loads(INDEX.read_text(encoding="utf-8"))["files"].get(rel(path))
    if entry is None:
        return []
    fences = list(FENCE.finditer(text))
    if len(fences) != entry["fences"]:
        raise ValueError(f"{rel(path)} has {len(fences)} code blocks, the archived index {entry['fences']}: "
                         "the markers' index no longer fits the text; revise facts/instructor/dax-markers-4feb03f.json")
    return [(text[:fences[mk["fence"]].start()].count(LF) + 1, mk["kind"], tidy(fences[mk["fence"]].group(1)))
            for mk in entry["markers"]]


def build_index() -> dict:
    sys.path.insert(0, str(HERE))
    import archive as arch
    files = {}
    for path in arch.book_files():
        text = arch.read(path).replace(CRLF, LF)
        if "<!-- dax-check:" not in text:
            continue
        spans = [(m.start(), m.end()) for m in FENCE.finditer(text)]
        markers = []
        for m in MARKED.finditer(text):
            fence_start = text.index("```", m.start())
            index = next(i for i, (a, _b) in enumerate(spans) if a == fence_start)
            markers.append(dict(kind=m.group(1), fence=index))
        files[path] = dict(fences=len(spans), markers=markers)
    return dict(commit=arch.COMMIT, files=files)


def check() -> int:
    sys.path.insert(0, str(HERE))
    import archive as arch
    differences = total = 0
    for path in arch.book_files():
        old = arch.read(path).replace(CRLF, LF)
        if "<!-- dax-check:" not in old:
            continue
        current = (REPO / path).read_text(encoding="utf-8")
        for kind in sorted(set(re.findall(r"<!-- dax-check: (\w+) -->", old)) | {"measure", "column", "table", "query", "skip"}):
            want = blocks_with_markers(old, kind)
            got = dax_blocks(REPO / path, kind, text=current)
            total += len(want)
            if want != got:
                differences += 1
                print(f"DIFF {path} {kind}: {len(want)} blocks in 4feb03f, {len(got)} now")
    print(f"{total} marked blocks compared, {differences} difference(s)")
    return 1 if differences else 0


if __name__ == "__main__":
    if "--build-index" in sys.argv:
        data = build_index()
        INDEX.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        print(f"{sum(len(v['markers']) for v in data['files'].values())} markers in {len(data['files'])} files")
    elif "--check" in sys.argv:
        sys.exit(check())
    else:
        print(__doc__)
