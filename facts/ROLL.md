# The yearly roll

Each summer the book moves to a new three-year window: the 2026 edition is fiscal 2024–2026 (dataset release v2026.1), the 2027 edition would be fiscal 2025–2027 (v2027.1). The generator is seeded, so almost every value changes. A roll is a scripted pipeline plus a review of what the scripts could not decide. This runbook is the order of work; the tools are all in the repository.

Everything is public. The chapters stay clean: no hidden comments, notes or markers in the text.

## What a roll changes, and what it cannot

| Scripted | Needs a person |
|---|---|
| The dataset build and its release | The wording of notes whose claims fail on the new data (`facts/notes/templates`) |
| The years, document IDs, dates and exact values in the text, the slides and the code that mirrors them (`facts/roll_text.py`) | Figure assertions on storylines the new data tells differently (the preflight and rehearsal list them) |
| The companion and solution files, rebuilt and verified against the new data | Weekdays and prose tied to the old window ("the first Friday", start-up months) |
| The instructor-notes package | A look at the slide decks: they show the book's figures and tables by ID and follow the rolled text on the next build, with no review step |

## Steps

All commands run from the book folder. `NEW` is the new `CharlesRiver.sqlite`; the old edition's registry is `facts/visible-2026.json`.

### 1. Build the dataset (about 35 minutes, unattended)

In the generator repository (`greenfield_database`, branch with the book scenarios committed), copy `config/settings.yaml`, set `fiscal_year_start` and `fiscal_year_end` to the new window, leave `random_seed` unchanged, keep `book_scenarios.enabled: true`, point `sqlite_path` and the report folder at a new output folder, and run in the pinned environment (`requirements-lock.txt`: Python 3.13, pandas 3.0.2, numpy 2.4.4, Faker 40.15.0):

    python generate_dataset.py path\to\settings-2025-2027.yaml

The three book scenarios (`cutoff_invoices`, `traced_sale`, `stranded_work_orders`) plant the storylines that are accidents of one seed on one window, only when the build lacks them. Check the log for their `BOOK SCENARIO` lines.

The same code with the window 2024-2026 rebuilds v2026.1 table for table (83 of 83; checked on 2026-10-06 after the last change to the scenarios), so the scenarios change nothing on the shipped window.

Keep the exports the release needs switched on (`export_sqlite`, `export_excel`, the CSV bundle, `export_support_excel`): the tutorials read `CharlesRiver.xlsx`, and the builds of the rehearsals switched the workbook and CSV exports off to save time, so a rehearsal's dataset has no workbook (the five figures that read it need the real one).

### 2. Preflight (about 3 minutes)

    python facts/roll.py preflight --db NEW --workdir outputs/roll-preflight

It runs the data contract (every storyline and quirk the chapters rely on; 41 checks), builds the new registry, evaluates every generated note's claims, and does a dry run of the text rewriter. The verdict is GO or NOT YET with the reasons; a GO lists the work that is left for a person.

- A failing contract check means the generator must plant the condition again, or a chapter must change. Fix the generator and rebuild; do not continue past a failing contract.
- A selection rule that finds nothing means a document the text names has no twin in the new build.
- A rewriter report with an unresolved, stale, unclassified or ambiguous literal stops the roll: classify it in `facts/literals/` first (an ambiguous literal needs a `context` in `values.yml`).
- A note with a failing claim is wording to revise (step 6), not a blocker.

### 3. Pin the new dataset

Create the dataset release with a new tag (v2027.1). Never re-upload assets under an existing tag. Then edit `_variables.yml` (edition, `dataset.version`, `dataset.window`, the two URLs, the three SHA-256 values). The companion files carry no edition in their names, so `scripts/companion/manifest.yml` needs no change. Put the files in `datasets/` and run:

    python scripts/verify/pinned_dataset.py --verify datasets/CharlesRiver.sqlite

### 4. Roll the text (about 1 minute)

    python facts/phase7_cli.py visible --db NEW --out facts/visible-2027.json
    python facts/roll_text.py --from facts/visible-2026.json --to facts/visible-2027.json --report outputs/roll-report.md
    python facts/roll_text.py --from facts/visible-2026.json --to facts/visible-2027.json --apply
    python facts/phase7_cli.py lint --snapshot facts/visible-2027.json

The first call is a dry run: read the report (rewrites by file; anything unresolved, stale, unclassified or ambiguous stops the run). `--apply` rewrites the book, the slides, `shared/` and the code that mirrors the text, and rolls the classification files (`facts/literals/`) with it. `git diff` is the impact report. Real-world years (citations, standards, software releases, Microsoft Learn dates) stay literal by rule.

A new literal that the lint does not know must be classified in `facts/literals/` before the text is committed.

### 5. Refresh the figures

    python scripts/figures/build.py
    python scripts/figures/check_figures.py --exports
    python scripts/export_drawio_svgs.py

A figure builder that fails asserts a storyline the new data tells differently: read the message, then fix the figure's wording or the builder. The rehearsal lists them in advance.

### 6. The human work

- Revise the notes whose claims fail (`facts/notes/templates/<chapter>/<note>.md` and `facts/notes/<chapter>.py`); rerun the preflight until the list is as short as the data allow. A claim is kept only where an exercise or storyline depends on that exact condition.
- Fix the figure assertions and any prose the roll could not follow.
- Look through the slide decks (`python scripts/build_all.py --slides-only`); `python scripts/build_all.py --check` and `python -m unittest discover -s tests -p 'test_*.py'` must pass before a push (the publish workflow runs both).
- Rewrite `facts/baseline-2026.md`, or retire it: it is hand-written prose of data facts that the registry and the notes now carry.

### 7. Verify

    python facts/contract.py --db NEW
    python scripts/verify/sql_check.py
    python scripts/verify/tutorial_queries_check.py
    python scripts/verify/var_keys_check.py
    python facts/instructor/check_equivalence.py

DAX blocks of the Power BI chapters are verified by the Power BI builds (step 8).

### 8. Rebuild the companion and solution files

Machine time, mostly unattended; one Excel build at a time, one Desktop verification at a time (machine-wide locks serialize them). Estimates from the 2026 builds:

| Build | Command | Time |
|---|---|---|
| SQL start files | `python scripts/companion/build.py --tool sql` | a few minutes |
| SQL solutions | `python scripts/companion/build.py --solutions --tool sql` | about 5 minutes |
| Excel start files (venv of `scripts/companion/requirements-excel.txt`) | `... build.py --tool excel` | about 40 minutes |
| Excel solutions | `... build.py --solutions --tool excel` | about 1.5 hours |
| Power BI start files | `... build.py --tool pbi` (then `--chapter A`, then `--chapter 16` for the shared folders) | about 40 minutes |
| Power BI solutions | `... build.py --solutions --tool pbi` | about 1 hour |
| Instructor notes package | `python facts/instructor/package.py` | a few minutes |

A build that stops names the failing check: a value that no longer agrees is a storyline to investigate, not a build to force.

### 9. Render and check

    quarto render --to html
    quarto render --to pdf -M keep-tex:true      # then the overfull check in CLAUDE.md
    quarto render --to epub
    quarto render --to docx

### 10. Publish

Release the dataset (step 3), copy the rebuilt companion and solution files into `supplementary/` with `python scripts/companion/build.py --publish` (see `supplementary/README.md`), start the edition's first revision with `python scripts/release.py bump <revision>`, commit, and run `python scripts/release.py publish`: it builds the PDF, EPUB, DOCX and decks, creates the revision's release with every file, and pushes `main`, so `publish.yml` deploys the site and `verify-data.yml` runs. The previous edition's revisions keep their own releases.

## Rehearsal

`python facts/roll.py rehearse --db NEW --workdir DIR [--render] [--clean]` does steps 2, 4 and 5 and the checks of step 7 on a copy of the tree and writes `rehearsal-report.md` with each step's time and the list that needs a person. The Excel and Power BI builds are not rehearsed (their estimates are above).

The rehearsal of 2026-10-06 rolled the 2026 edition to a fiscal 2025-2027 build (seed 20260401, the three book scenarios on, `scenario_end_year` unset; kept in the gitignored `outputs/rehearsal-data/fiscal-2025-2027/`, with its settings and log, so the rehearsal can be repeated without a 35-minute build). It ran 17 steps in 5 minutes with none failed:

| What | Result |
|---|---|
| Data contract (41) and registry rules (6) | all pass; the cutoff story (three consecutive invoices, one posting date, one shipped in the prior year), the traced sale and the stranded work orders are planted by the generator |
| The rewriter | 2,607 literals in 185 files, 0 unresolved, 0 stale, 0 unclassified, 0 ambiguous; the rolled copy lints clean (13,389 literals) |
| Tutorial queries, SQL blocks, `{{< var >}}` keys, SQL companion files | all run on the new data |
| The figure standard | 160 figures checked, 0 problems |
| An HTML render of Chapters 3 and 11 | none of the old document IDs or dates remains |

What a person has to do (the sizes of the 2026-10-06 rehearsal; plan a day or two for the first two):

- **Slides.** No review step since 2026-10-07: the decks cite the book's figures and tables by ID and pick up the rolled text and figures on the next build. Look through them once.
- **Figures.** 29 of 160 fail to build: 5 need the new `CharlesRiver.xlsx`, 23 assert a storyline that the new window tells differently (Part III: the manufacturing variance by group, hours per standard hour, the start-up months, overtime share, the year-to-date gap, the surge days; Part II: the Furniture margin bridge, the first invoice lines; Part IV: the budget variance, the Chapter 16 exception counts; the rest are one-number assertions) and 1 is a layout error (Figure 7.1's trend line leaves its frame). Read each message, then fix the figure's wording and assertion, or plant the condition in the generator.
- **Notes.** 14 of 161 have a claim that fails on the new data (the Part II case commission rate, Chapter 7's offsetting months, Chapter 18's make-or-buy conditions, Chapter 19's expectation, and similar). Revise the template wording (`facts/notes/templates`), keeping a claim only where an exercise or storyline depends on that exact condition.
- **Prose** tied to the old calendar (weekdays, "the first Friday", start-up months) is not rewritten.

## Not handled

- Weekdays: the generator's calendar changes with the window; prose that names a weekday or a start-up month is in the "needs a human" list.
- Another seed breaks the manufacturing variance and cash stories; the seed stays fixed.
- `_variables.yml` and `scripts/companion/manifest.yml` are not rolled by the rewriter (step 3).
