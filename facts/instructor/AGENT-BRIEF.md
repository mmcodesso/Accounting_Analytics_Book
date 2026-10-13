# Agent brief: write the instructor guides for one unit

You write the instructor guides of **one unit** of *Accounting Analytics: An Integrated Approach*: a chapter (`1`..`19`), a comprehensive case (`case1`..`case4`) or an appendix (`appB`, `appC`). The unit is named in your instruction. Work on that unit only, then stop and report.

Read first, in this order:

1. `facts/instructor/STANDARD.md`: the format, the voice, the rules, the commands. Follow it exactly.
2. `CLAUDE.md` (project instructions, already in your context if you were given them): the book's conventions, the data rules, the verified UI labels of DB Browser and Power BI, the Part V independence rule.
3. A finished neighbor unit as a style example, when your instruction names one (its templates are in `facts/instructor/guides/<folder>/`, its output in `instructor-notes/<folder>/`).

## Work plan

1. **Scaffold and gather sources.**
   `python facts/instructor/guides.py scaffold --unit U` creates the templates (it keeps any that exist).
   `python facts/instructor/guides.py sources --unit U --out <scratch>/U-sources.md` writes one file with the unit's expanded text, the existing generated instructor notes and their context keys, the slide deck path, the solution folders and builder modules, and the competency map entries. Read it in chunks (it is long). Use your scratch folder for every temporary file (the path is in your instructions); never `/tmp` or `%TEMP%`.
2. **Read the unit's sources** (only these):
   - the chapter text and exercises (in the sources file);
   - `facts/baseline-2026.md`, only the paragraphs for this unit (search for the chapter number or case name);
   - the slide deck `slides/chapter-NN/index.qmd` (or `slides/case-part-N/index.qmd`) and its speaker notes, for the lecture flow and the points the author stresses;
   - the model answers: the built solution folder in `outputs/companion/solutions/` (Excel workbooks: copy to scratch and read with `openpyxl` read-only, `data_only=True`; SQL scripts; Power BI projects: the Notes page and the TMDL and PBIR text) and the builder module (`scripts/companion/xlbuild|sqlbuild|pbibuild/*.py`), which shows the exact sequence of steps;
   - the generated notes' context functions in `facts/notes/<module>.py` for the values each exercise's steps can use (`guides.py context KEY` lists the keys and current values).
   Verify anything you intend to state about the data with a read-only query on `datasets/CharlesRiver.sqlite` (`sqlite3.connect("file:...?mode=ro", uri=True)`; there is no sqlite3 CLI, use Python).
3. **Write the chapter or case note, then every item file** in `facts/instructor/guides/<folder>/`, replacing every TODO. Put the data values in the context, not in the prose. Declare figure placeholders where STANDARD.md says.
4. **Render and check** until clean:
   `python facts/instructor/guides.py render --unit U` and `python facts/instructor/guides.py check --unit U`. Then read each rendered file in `instructor-notes/<folder>/` once, as an instructor would, and fix what reads badly, repeats the exercise text, or states something the data does not show.
5. **Refresh the figure inventory:** `python facts/instructor/guides.py figures`.
6. If you added a key to a note module: `python facts/instructor/render.py` must still end with exactly `168 notes rendered, 161 in the archive, {'identical': 73, 'differs': 88}, 95 problem(s)` (the baseline before any guide work: the archive predates later wording edits, so 95 is the expected number, not 0).

## Hard limits

- Do not edit anything in `chapters/`, `cases/`, `appendices/`, `slides/`, `visuals/`, `scripts/` (except adding a guide context under `facts/instructor/guide_contexts/` and, additively, keys in an existing `facts/notes/*.py` context function), `datasets/`, `outputs/`, or the rendered `instructor-notes/` by hand.
- Do not run Excel, Power BI Desktop, Quarto or any build; do not use COM or UI automation; do not run git commands (the author commits).
- Do not start another agent.
- Do not invent: a UI label, a menu path, a formula, a query, a measure or a value that you did not read in the book, the solution file, a builder or the data. When something cannot be confirmed, say so in the file in general terms and list it in your report.
- If the book, a solution file and the data disagree, write the guide to what the solution file and the data show and report the disagreement; do not change the book.

## Work efficiently (the budget is shared by 25 units)

- Read the sources bundle once, in a few large chunks; read a solution file or builder only for the items it covers; do not re-read a file you already hold.
- Write each template with one Write call (draft the whole file, then write it), not many small edits. Expect `render` and `check` twice, not ten times.
- Proofread by reading the rendered output of one or two items fully and spot-checking the rest with `grep`, not by re-reading everything.
- Hold to the length targets in STANDARD.md (items 900-1,700 words, notes 2,200-3,500): a guide that is complete and dense beats a long one.

## Lessons from finished units

- Any number of four or more digits (account numbers such as 5080, years, "1,000") must come through the context or the check flags it; numbers inside inline code and fenced blocks are exempt.
- A `{% endfor %}` or `{% endif %}` at the end of a prose line swallows the blank line after it: put loops and conditions on their own lines.
- A guide context should check every table and column its template names against the database (Chapter 1's `facts/instructor/guide_contexts/ch01.py` has helpers `schema()` and `in_group()`; reuse or copy them).
- `visible.trace(d)` (facts/visible.py) gives the identifiers of the traced sale.
- Replace the scaffold's truncated `### Requirement (N): ...` headings with short titles; the check only needs the `### Requirement (N)` prefix.
- Do not use `items`, `keys`, `values`, `none` or any dict-method name as a context key: Jinja silently returns the method, so `check` passes while the output is wrong. Read the rendered output.
- `check` does not catch a sentence that starts with a number or a lowercase word-number from a note context; read for them. Put `$` in front of `|money` in templates (the earlier guides show amounts with a currency sign).
- A PivotTable ignores the worksheet's filters, so a step that relies on a filtered result must put the field in the PivotTable itself.
- Part I units have no solution file: use `tool: conceptual` with `solution: ''` and describe the Excel path step by step, saying in your report which formulas you ran only in SQL.
- A guide context must not reuse a registered note's key. Use `<unit>.gN` plus `uses:`; with both `note:` and `uses:`, read the extra context through its namespaced name (`{% set g = case1_g1 %}` after the front matter, then `g.value`).
- Write negative money as `-${{ (x|abs)|money }}`, because `$-` trips the leak check. A colon followed by a space inside a figure's `shows:` or `purpose:` breaks the YAML: quote the value. Put `{{ figure() }}` on its own line, never inside a bullet. Jinja's `capitalize` lowercases the rest of the string.
- Write long Python edit scripts to a scratch file and run them; shell heredocs with apostrophes, backslashes and `EOF` break.
- Excel step format that worked (Chapter 4): a bold step title, lettered actions when there are three or more, formulas over about 50 characters in bare fences, then a `**Check:**` line with template values and a `**Watch for:**` line naming the silent failure and its symptom. Compute Table column letters in the context (`letters_of()` in `guide_contexts/ch04.py`). A fence that holds template values needs the info string `jinja`. Build "1, 4 and 7" lists in the context (`|join` gives "1 and 4 and 7"). Where a wrong formula still passes on this data, add a claim and say so in the guide. Excel items run over the 1,700-word target because of the steps; the 2,700 maximum holds.
- Where the solution workbook shares one file across exercises, map its prefixed sheets to the names a student would use and say so.
- `check` flags any 4+ digit number, any decimal with two or more places and any year in plain prose, including a threshold such as 0.02 or a year such as 1900 in a "Watch for" line: wrap such values in backticks (code) or pass them through a context filter (`|count`, `|money`), in bullets too.
- Run any model result you describe (Solver, regression, Goal Seek, a forecast) through an independent computation (`scipy` is available) before writing a mistakes list: a plausible symptom is often wrong. Use `|min` and `|max` on a list of ratios, not the first and last element. Put account IDs inside formula fences through a `jinja` fence so a roll updates them.
- If an item's note context already has a key named `g` (or any short name you planned to use), name your own context variable something else. Put a blank line between a `**Check:**` line and a `{% for %}` bullet list, or the list runs on from the paragraph. A mistake's symptom reads best when a claim in the context backs it (a guard on blank dates, for example).
- SQL steps (Chapter 9): quote each query with both of its comment lines, contiguous in the solution script (the check matches whitespace-normalized text; the trailing `-- Result:` comment is not needed). The SQL fences count toward the word limit (about 450 words in a large item), so keep prose near 1,500 words. Run every wrong variant read-only inside the guide context and print its row count in the "Watch for" line (`LIKE '%favorable%'` also matches "unfavorable"; `<` and `<=` can return the same rows; a missing LaborType filter changes a count). The pane reads "N rows" with no thousands separator, so use `|count` in prose. Put the one-line routine (type, select, **Execute all/selected SQL**, read the pane) in each item, since items ship as separate files. Mark queries the model answer has beyond the exercise text as hints or extra credit. Stored LaborType values are `Direct Manufacturing`, `Indirect Manufacturing` and `NonManufacturing`.
- Place each trap query by its own table: joins and anti-joins from the ledger on type, document ID and line ID are fast, but a join on an ID alone, or a reverse anti-join from `GLEntry` on `SourceLineID` alone, can run for minutes (no index on several foreign keys; see CLAUDE.md). A heading like `### Requirement (4) and (5)` fails the check: give each requirement its own heading. `check --unit` can take over a minute (existing note contexts); for quick iteration render one file at a time with a small scratch script that calls `guides.render_template`.
- A scratch expander that pulls each quoted query verbatim from the solution script by its first comment line avoids transcription errors (write one in your scratch folder); `check` verifies the quotes. `{{ expected() }}` adds about 200 words and each figure placeholder 60 to 90, so keep the Expected results table and each `shows:` short. `Default` is a SQLite keyword: do not use it as a column alias in a context query. Add up each plan's minutes with a script.
- `|count` on a float prints ".0": use `|num`. Counter keys such as `per_req` are ints in templates (`c.per_req[1]`). A guide context that creates TEMP views must drop them afterward (the contexts share one connection and Chapter 11 uses the same view name).
- Power BI steps (Chapter 13): lettered actions by pane and label, then a **Check:** line with the page and visual title, then **Watch for:** with a symptom computed from the data. Quote M and DAX from the solution project's `.SemanticModel` through `jinja` fences; reuse the helpers in `facts/instructor/guide_contexts/ch13.py` (`table_m`, `expression_m`, `steps`, `entry`, `check_expr`, which finds a Checks-tab row by label). Add one `EVALUATE ROW (...)` instructor check per item. A `jinja` fence cannot hold DAX braces (`{ }`): use a plain fence for those. Read `uses:` contexts as `ch13_t1` and set short names after the front matter; index note dicts with `t1['items']`, because `.items` returns the dict method. The project encodes visual structure, not rendered output: say which results the Checks tab proves and which are visible only in Desktop. The "unresolved template expression" check ignores code fences, so M and DAX with `{{` are fine inside them.
- `spct` is a percent filter, not signed money: for signed dollars use a one-line `{% macro sm(x) %}` that prints the sign before the `$`. A template only has `y` or `n` if its context returns them (return them from the `g` context and read `g.y`). `{{ 0|money }}` avoids a literal `$0.00` that the check flags.
- Table view has no Modeling tab: use Report view for New column. A note key such as `now` cannot be re-set with `{% set %}` in a template that uses that note.
- Budget the generated note first: `{{ expected() }}` adds 600-770 words in the long Part V and case items and counts toward the 2,700 cap, so figures and long SQL have to be short. Two small scratch runners help (a context runner that prints failed claims, and a per-section word counter).
- Part V units are written by two agents (the note plus the first requirements, then the rest): the second extends the first's guide-context module and its `PLAN`/`WEIGHTS` tables; both follow the plan minutes and rubric weights already committed in the case note.
- Style examples: Chapter 1 (`facts/instructor/guides/chapter-01-role-of-analytics/`, conceptual) shows the voice, the Expected results table, the grading table and the figure declarations. Tool units add the tool steps described in STANDARD.md.

## Final message (the only thing the orchestrator reads)

Keep it under 400 words:

- files written (count, folder);
- `check` result and the number of rendered words;
- figure placeholders: total, by kind, and the ids of the three most valuable;
- context functions or note-context keys added;
- claims that fail on this dataset;
- mismatches or unverified items found (file and line, what differs);
- anything the next unit's agent should know about the standard (a rule that was unclear, a pattern that worked well).
