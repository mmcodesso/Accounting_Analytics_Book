# Verification tools

These scripts check the book against the Charles River dataset. None of them is part of the render. Each reads its paths from `scripts/paths.py`. Set `CHARLESRIVER_DATA` to test another dataset folder.

| Tool | What it checks | Run |
|---|---|---|
| `sql_check.py` | Runs every ```` ```sql ```` block of chapters 9–12 read-only. The markers `<!-- sql-check: skip\|error\|view -->` go on the line before a block. | `python scripts/verify/sql_check.py [9 10 …] [--show]` |
| `tutorial_queries_check.py` | Checks that the tutorial SQL blocks equal the `dbbrowser.Script` queries in `scripts/figures/ch09.py`–`ch12.py`. | `python scripts/verify/tutorial_queries_check.py` |
| `dax_blocks.py` | Turns a chapter's `<!-- dax-check: … -->` blocks into one DEFINE MEASURE / EVALUATE query per block. | `python scripts/verify/dax_blocks.py <chapter folder> <out.dax>` |
| `dax_blocks_all.py` | Does the same, but defines all of the chapter's measures in every query, each on its host table taken from a reference model (chapter 15 on). | `python scripts/verify/dax_blocks_all.py <chapter folder> <model.SemanticModel> <out.dax>` |
| `dax_check.ps1` | Runs a `.dax` file (queries separated by `-- @@ label` lines) through ADOMD.NET against the open Power BI Desktop model that holds `-Table`. | `powershell -File scripts/verify/dax_check.ps1 -QueryFile q.dax [-Table GLEntry]` |
| `dax_check_role.ps1` | Does the same under a role (`-Roles`). | as above, plus `-Roles "Cost Center Managers"` |
| `dax/*.dax` | The saved check queries of the reference models. The expected values are in the labels. | with `dax_check.ps1` |
| `twins/*.py` | SQL twins that recompute every value in the instructor notes of chapters 15–19 and the Part IV case. | `python scripts/verify/twins/ch17_twins.py` |

The Power BI reference models are built by `scripts/companion/pbi/make_*.py` into `scripts/companion/pbi/reference/`. Open a model's `.pbip` in Power BI Desktop and refresh it before running `dax_check.ps1`. Run `twins/ch18_twins.py` before `make_cr18.py`, because the twin writes the two CSVs that CR18 reads.
