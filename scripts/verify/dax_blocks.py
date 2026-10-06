"""Extract the DAX blocks marked <!-- dax-check: measure|table|query --> from a chapter and write a
query file for dax_check.ps1. Measures are tested as query-scoped definitions (DEFINE MEASURE),
evaluated by fiscal year; tables are counted; queries run as written."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "facts" / "instructor"))
from daxblocks import ordered_blocks  # the markers, or the index archived from commit 4feb03f (chapters carry none)

chapter = Path(sys.argv[1])
out = Path(sys.argv[2])
host = {"GL": "GLEntry"}           # table that hosts a measure in the reference model
queries = []
for f in sorted(chapter.glob("*.qmd")):
    for line, kind, body in ordered_blocks(f):
        label = f"{f.name}:{line} {kind}"
        if kind == "query":
            queries.append((label, body))
        elif kind == "table":
            name, expr = body.split("=", 1)
            queries.append((label, f"EVALUATE ROW ( \"Rows\", COUNTROWS ( {expr.strip()} ) )"))
        elif kind == "measure":
            # One block may hold several one-line measures; split at lines that start a definition.
            defs = re.split(r"(?m)^(?!VAR|RETURN)(?=[A-Za-z][\w %&]*? =)", body)
            for d in [d.strip() for d in defs if d.strip()]:
                name, expr = d.split(" = ", 1) if " = " in d.split("\n")[0] else d.split(" =", 1)
                name = name.strip()
                table = "GLEntry" if re.search(r"GLEntry|Account|Operating|GL Amount|P&L|Net Income", expr + name) else "SalesInvoiceLine"
                q = (f"DEFINE MEASURE {table}[{name}] =\n{expr.strip()}\n"
                     f"EVALUATE SUMMARIZECOLUMNS ( 'Date'[Year], \"{name}\", [{name}] )\nORDER BY 'Date'[Year]")
                queries.append((f"{label} {name}", q))
with out.open("w", encoding="utf-8", newline="\n") as fh:
    for label, q in queries:
        fh.write(f"-- @@ {label}\n{q}\n")
print(len(queries), "queries written to", out)
