"""Like dax_blocks.py, but every query defines all of the chapter's measures up to that block, on the
table that hosts the measure in the reference model, so a measure that refers to another chapter
measure uses the chapter's text and not the model's copy."""
import re
import sys
from pathlib import Path

chapter = Path(sys.argv[1])
model = Path(sys.argv[2])
out = Path(sys.argv[3])
DEFAULT_HOST = sys.argv[4] if len(sys.argv) > 4 else "SalesInvoiceLine"

host = {}
for f in model.glob("*.tmdl"):
    for m in re.finditer(r"(?m)^\tmeasure (?:'([^']+)'|([^ =]+)) =", f.read_text(encoding="utf-8")):
        host[m.group(1) or m.group(2)] = f.stem


def table_of(name):
    return host.get(name, DEFAULT_HOST)


defined = {}          # name -> (table, expr), in chapter order
queries = []
for f in sorted(chapter.glob("*.qmd")):
    text = f.read_text(encoding="utf-8")
    for m in re.finditer(r"<!-- dax-check: (\w+) -->\s*\n\s*```\s*\n(.*?)\n\s*```", text, re.S):
        kind, body = m.group(1), m.group(2)
        lines = body.split("\n")
        indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
        body = "\n".join(l[indent:] for l in lines)
        label = f"{f.name}:{text[:m.start()].count(chr(10)) + 1} {kind}"

        def define_block():
            return "DEFINE\n" + "\n".join(f"MEASURE '{t}'[{n}] =\n{e}" for n, (t, e) in defined.items()) + "\n" if defined else ""

        if kind == "query":
            q = body
            if defined:
                q = define_block() + re.sub(r"^\s*DEFINE\s*\n", "", body) if body.lstrip().startswith("DEFINE") else define_block() + body
            queries.append((label, q))
        elif kind == "measure":
            defs = re.split(r"(?m)^(?!VAR|RETURN)(?=[A-Za-z][\w %&-]*? =)", body)
            for d in [d.strip() for d in defs if d.strip()]:
                name, expr = d.split(" = ", 1) if " = " in d.split("\n")[0] else d.split(" =", 1)
                name = name.strip()
                defined[name] = (table_of(name), expr.strip())
                q = define_block() + (f"EVALUATE SUMMARIZECOLUMNS ( 'Date'[Year], \"{name}\", [{name}] )\n"
                                      f"ORDER BY 'Date'[Year]")
                queries.append((f"{label} {name}", q))
with out.open("w", encoding="utf-8", newline="\n") as fh:
    for label, q in queries:
        fh.write(f"-- @@ {label}\n{q}\n")
print(len(queries), "queries written to", out, "| hosts:", {n: t for n, (t, _) in defined.items()})
