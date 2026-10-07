"""Index the book's own content so the slide decks can cite it by ID.

A deck writes {{< book-figure fig-01-02 >}} or {{< book-table tbl-01-02 >}}; the shortcodes in
slides/shortcodes/book.lua read this index, so a deck always shows the book's current figure,
caption, alt text and table. The index reads only the book sources (the root _quarto.yml and
each chapter with its includes), so it needs neither Quarto nor the dataset.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

INCLUDE = re.compile(r"^\{\{<\s*include\s+([^\s>]+)\s*>\}\}\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*(?:\{([^}]*)\})?\s*$")
FENCE = re.compile(r"^(`{3,}|~{3,})")
DIV = re.compile(r"^(:{3,})\s*(.*)$")
FIGURE = re.compile(r"!\[(?P<caption>.*?)\]\((?P<src>[^)\s]+)\)\{(?P<attrs>[^}]*?#(?P<id>fig-[\w-]+)[^}]*)\}")
ALT = re.compile(r'fig-alt="([^"]*)"')
TABLE_CAPTION = re.compile(r"^:\s+(?P<caption>.*?)\s*\{#(?P<id>tbl-[\w-]+)\}\s*$")
OBJECTIVE = re.compile(r"^\d+\.\s+(.*)$")
TERM = re.compile(r"^\*\*(.+?)\.\*\*\s")
STEP = re.compile(r"^\*\*Step (\d+)\.\s+(.+?)\.?\*\*")
LABELED = re.compile(r"^\*\*(Context and objective|Prerequisites|Checkpoint)\.\*\*\s*(.*)$")
EXERCISE = re.compile(r"^\*\*Exercise ([0-9A-Z]+\.\d+):\s*(.+?)\.?\*\*\s*$")
TUTORIAL = re.compile(r"^Guided Tutorial ([0-9A-Z]+\.\d+):\s*(.+)$")
BOOK_URL = "https://aa.accountinganalyticshub.com/"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def deck_id(number: int) -> str:
    return f"chapter-{number:02d}"


def read_lines(path: Path, root: Path) -> list[str]:
    """The file's lines with every include expanded in place, as Quarto renders them."""
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = INCLUDE.match(line.strip())
        if match:
            target = match[1]
            included = root / target.lstrip("/") if target.startswith("/") else path.parent / target
            lines.extend(read_lines(included, root))
        else:
            lines.append(line)
    return lines


def split_front_matter(lines: list[str]) -> tuple[dict, list[str]]:
    if lines and lines[0].strip() == "---":
        for end in range(1, len(lines)):
            if lines[end].strip() == "---":
                return yaml.safe_load("\n".join(lines[1:end])) or {}, lines[end + 1:]
    return {}, lines


def strip_markup(text: str) -> str:
    return re.sub(r"[*_`]", "", text).strip()


def split_row(line: str) -> list[str]:
    """Cells of one pipe-table row; a | inside code or escaped as \\| stays in its cell."""
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    cells, cell, code, i = [], "", False, 0
    while i < len(text):
        char = text[i]
        if char == "\\" and text[i + 1:i + 2] == "|":
            cell += "\\|"
            i += 2
            continue
        if char == "`":
            code = not code
        if char == "|" and not code:
            cells.append(cell.strip())
            cell = ""
        else:
            cell += char
        i += 1
    cells.append(cell.strip())
    return cells


def parse_table(lines: list[str]) -> dict:
    header, separator, *body = [split_row(line) for line in lines]
    return {"header": header, "separator": separator, "rows": body}


def book_entries(root: Path) -> tuple[str, list[dict]]:
    """The book's title and its registered pages in reading order, each with its Part."""
    config = yaml.safe_load((root / "_quarto.yml").read_text(encoding="utf-8"))
    book = config["book"]
    entries: list[dict] = []
    parts = 0

    def walk(items, part):
        for item in items:
            if isinstance(item, str):
                entries.append({"path": item, "part": part})
            elif isinstance(item, dict) and "part" in item:
                nonlocal parts
                label = f"Part {ROMAN[parts]}: {item['part']}"
                parts += 1
                walk(item.get("chapters", []), label)
            elif isinstance(item, dict) and "href" in item:
                entries.append({"path": item["href"], "part": part})

    walk(book.get("chapters", []), None)
    walk(book.get("appendices", []), "Appendices")
    return book["title"], entries


def page_title(path: Path, root: Path) -> str:
    meta, lines = split_front_matter(read_lines(path, root))
    if meta.get("title"):
        return str(meta["title"])
    for line in lines:
        match = HEADING.match(line)
        if match and len(match[1]) == 1:
            return match[2]
    return path.stem


def index_chapter(path: Path, root: Path, label: str) -> dict:
    meta, lines = split_front_matter(read_lines(path, root))
    chapter: dict = {"title": str(meta.get("title", "")), "objectives": [], "sections": [],
                     "figures": [], "tables": [], "key_terms": [], "tutorials": [], "exercises": []}
    divs: list[str] = []
    fence = None
    counters = [0, 0, 0]
    heading = ""
    perspective = ""
    tutorial = None
    checkpoint = None
    for number, line in enumerate(lines):
        fence_match = FENCE.match(line)
        if fence:
            if fence_match and line.startswith(fence):
                fence = None
            continue
        if fence_match:
            fence = fence_match[1]
            continue
        div = DIV.match(line)
        if div:
            if div[2].strip():
                divs.append(div[2].strip())
            elif divs:
                divs.pop()
            continue
        match = HEADING.match(line)
        if match and not divs and len(match[1]) in (2, 3):
            level, title, attrs = len(match[1]) - 2, match[2], match[3] or ""
            heading = title
            checkpoint = None
            if ".unnumbered" not in attrs and not re.search(r"(^|\s)-(\s|$)", attrs):
                counters[level] += 1
                for deeper in range(level + 1, len(counters)):
                    counters[deeper] = 0
                section_number = ".".join([label] + [str(n) for n in counters[:level + 1]])
                chapter["sections"].append({"number": section_number, "title": title, "level": level + 2})
            if level == 0:
                found = TUTORIAL.match(title)
                tutorial = None
                if found:
                    tutorial = {"id": found[1], "title": found[2], "heading": title, "objective": "",
                                "prerequisites": "", "steps": [], "checkpoint": {"lead": "", "items": [], "close": ""}}
                    chapter["tutorials"].append(tutorial)
            else:
                perspective = title
            continue
        if divs and any(".learning-objectives" in d for d in divs):
            found = OBJECTIVE.match(line)
            if found:
                chapter["objectives"].append(found[1])
            continue
        for found in FIGURE.finditer(line):
            alt = ALT.search(found["attrs"])
            chapter["figures"].append({
                "id": found["id"], "number": f"{label}.{len(chapter['figures']) + 1}",
                "caption": found["caption"].strip().rstrip("."), "src": found["src"],
                "alt": alt[1] if alt else ""})
        found = TABLE_CAPTION.match(line)
        if found:
            start = number - 1
            while start >= 0 and not lines[start].strip():
                start -= 1
            end = start + 1
            while start >= 0 and lines[start].lstrip().startswith("|"):
                start -= 1
            table = parse_table(lines[start + 1:end])
            table.update({"id": found["id"], "number": f"{label}.{len(chapter['tables']) + 1}",
                          "caption": found["caption"].strip().rstrip(".")})
            chapter["tables"].append(table)
            continue
        if heading == "Key Terms":
            found = TERM.match(line)
            if found:
                chapter["key_terms"].append(found[1])
            continue
        found = EXERCISE.match(line)
        if found:
            chapter["exercises"].append({"id": found[1], "title": found[2], "perspective": perspective})
            continue
        if tutorial is None:
            continue
        found = STEP.match(line)
        if found:
            tutorial["steps"].append({"number": int(found[1]), "title": found[2]})
            checkpoint = None
            continue
        found = LABELED.match(line)
        if found:
            if found[1] == "Context and objective":
                tutorial["objective"] = found[2]
            elif found[1] == "Prerequisites":
                tutorial["prerequisites"] = found[2]
            else:
                checkpoint = tutorial["checkpoint"]
                checkpoint["lead"] = found[2]
            continue
        if checkpoint is not None:
            if line.startswith("- "):
                checkpoint["items"].append(line[2:].strip())
            elif line.strip() and not checkpoint["close"] and checkpoint["items"]:
                checkpoint["close"] = line.strip()
    return chapter


def build(root: Path) -> dict:
    """Every numbered chapter of the book, with lookups of its figures and tables by ID."""
    title, entries = book_entries(root)
    chapters: dict[str, dict] = {}
    order = []
    for position, entry in enumerate(entries):
        path = root / entry["path"]
        found = re.fullmatch(r"chapters/(\d{2})-[^/]+/chapter\.qmd", entry["path"])
        if found:
            number = int(found[1])
            chapter = index_chapter(path, root, str(number))
            chapter.update({"id": deck_id(number), "number": number, "path": entry["path"],
                            "part": entry["part"]})
            chapters[chapter["id"]] = chapter
            order.append((position, chapter["id"]))
    for position, identifier in order:
        chapter = chapters[identifier]
        same_part = [chapters[other]["number"] for _, other in order
                     if chapters[other]["part"] == chapter["part"]]
        chapter["part_chapters"] = same_part
        following = entries[position + 1] if position + 1 < len(entries) else None
        if following:
            found = re.fullmatch(r"chapters/(\d{2})-[^/]+/chapter\.qmd", following["path"])
            name = page_title(root / following["path"], root)
            chapter["next"] = f"Chapter {int(found[1])}: {name}" if found else name
        else:
            chapter["next"] = ""
    figures = {fig["id"]: {**fig, "chapter": cid} for cid, ch in chapters.items() for fig in ch["figures"]}
    tables = {tab["id"]: {**tab, "chapter": cid} for cid, ch in chapters.items() for tab in ch["tables"]}
    return {"book_title": title, "book_url": BOOK_URL, "chapters": chapters, "figures": figures, "tables": tables}


def write(root: Path, target: Path) -> dict:
    index = build(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return index


if __name__ == "__main__":
    import sys
    repo = Path(__file__).resolve().parents[2]
    data = build(repo)
    wanted = sys.argv[1:] or sorted(data["chapters"])
    for identifier in wanted:
        chapter = data["chapters"][identifier]
        print(f"{identifier}: {chapter['title']} ({chapter['part']})")
        print(f"  sections {len([s for s in chapter['sections'] if s['level'] == 2])}, objectives "
              f"{len(chapter['objectives'])}, figures {len(chapter['figures'])}, tables "
              f"{len(chapter['tables'])}, key terms {len(chapter['key_terms'])}, tutorials "
              f"{[(t['id'], len(t['steps'])) for t in chapter['tutorials']]}, exercises "
              f"{len(chapter['exercises'])}; next: {chapter['next']}")
