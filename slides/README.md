# Chapter presentations

This independent Quarto project renders one chapter source to Reveal.js and
PowerPoint. The inventory contains all 19 numbered chapters. Chapter 1's 47-slide
storytelling revision was approved on 5 October 2026; the other decks retain their approval.
Each deck includes public teaching notes and both output formats.

| Chapter | Status | Teaching slides | Module dividers | Total including opening |
|---|---|---:|---:|---:|
| 1 | Approved | 41 | 5 | 47 |
| 2 | Approved | 35 | 4 | 40 |
| 3 | Approved | 40 | 4 | 45 |
| 4 | Approved | 30 | 4 | 35 |
| 5 | Approved | 29 | 3 | 33 |
| 6 | Approved | 30 | 4 | 35 |
| 7 | Approved | 30 | 4 | 35 |
| 8 | Approved | 34 | 4 | 39 |
| 9 | Approved | 32 | 4 | 37 |
| 10 | Approved | 34 | 4 | 39 |
| 11 | Approved | 33 | 3 | 37 |
| 12 | Approved | 37 | 4 | 42 |
| 13 | Approved | 30 | 3 | 34 |
| 14 | Approved | 32 | 3 | 36 |
| 15 | Approved | 30 | 3 | 34 |
| 16 | Approved | 30 | 3 | 34 |
| 17 | Approved | 26 | 4 | 31 |
| 18 | Approved | 27 | 4 | 32 |
| 19 | Approved | 29 | 3 | 33 |

The intended audience has introductory financial and managerial accounting
knowledge. No prior analytics, programming, or accounting information systems
course is required.

## Default teaching structure

Use a recurring accounting investigation within each module. The stages guide
teaching, rather than impose six slides or a fixed chapter length.

| Stage | Purpose | Observable student work |
|---|---|---|
| Situation | Business event, decision maker, consequence | Recognize the accounting context |
| Question | Question, population, period, measure | Clarify what must be explained or decided |
| Evidence | Relevant records, figures, results | Observe, compare, locate, predict |
| Method | Needed concept and visible intermediate steps | Follow a worked process |
| Check | Verify understanding or a result | Calculate, match, diagnose, explain |
| Interpretation | Supported conclusion, limits, next evidence | Produce a qualified response |

Repeat the sequence where useful. Concept chapters emphasize comparisons and
processes, software chapters intermediate results and troubleshooting, and
cases competing explanations and decisions. These teaching stages differ from
the book's six-stage analytical workflow.

Each teaching slide has one principal purpose, an evidence source or student
task, and public notes stating **Purpose, Evidence, Timing, Narration, Expected
response, Misconception, and Transition**. Ordinary explanations allow 45–90
seconds; activities state a longer practical timing. Every activity names an
observable output. Keep its instructions visible throughout student work.

Selected checks use a separate response slide, preserving the pause in both
formats. Fragments pace explanations in Reveal, while essential reasoning stays
complete in static PowerPoint. Do not hide a required instruction in a fragment
or rely on animation inside a diagram. Use one teaching purpose per figure view,
with consistent link meanings and attribution.

## Chapter 1 recording modules

The five modules can be taught together or recorded separately:

| Module | Purpose |
|---|---|
| The controller's question | Define and interpret a qualified margin preview |
| Questions and workflow | Distinguish analytics types and the six stages |
| Tools and the Charles River business | Connect tool choices, activities, and tables |
| Tracing one revenue posting | Follow a public invoice-line example into the ledger |
| Guided exploration | Complete Tutorial 1.1 and transition to assigned practice |

Speaker notes give each teaching slide a purpose, suggested timing, narration,
questions for students, and a transition. Ordinary explanation slides allow
approximately 45–90 seconds. Workbook activity slides allow two to three minutes.
Use those timings as prompts rather than automatic advancement. Notes travel in
both outputs and are public. The tutorial checkpoint responses are already
public in the book. Exercise, comprehensive-case, and capstone solutions belong
outside this project and its dependencies.

The Furniture exhibit previews Chapter 6's public calculation. Its measure is
**invoice-based margin at standard cost**. It does not reconcile financial-statement
gross profit or reveal the diagnostic explanation. The posting trace checks one
revenue credit, not a complete journal entry. Its displayed values and identifiers
come from the prepared public facts through the `slide.trace` variables.

The 2026 margin comparison and **5 March 2025** navigation trace have distinct
evidence boundaries. The trace verifies one invoice line against one revenue
credit and provides no diagnosis of the 2026 decline. Review the complete
storyboard and original-slide dispositions in
[the implementation record](reviews/chapter-01-storytelling.md).

Focused, dataset-free authoring checks and renders:

```text
python scripts/build_all.py --check --chapter chapter-01
python scripts/build_all.py --slides-only --chapter chapter-01
python scripts/build_all.py --preview chapter-01
```

Explicit authoring refresh, followed by the focused build:

```text
python scripts/build_all.py --slides-only --chapter chapter-01 --refresh-shared
```

Focused renders use isolated Quarto output directories before replacing the
selected chapter. Other decks and approved release bundles remain intact. The
chapter report is `outputs/build/chapter-01/build-report.json`. Chapter selection
is rejected for full-site assembly and public export: those operations validate
the whole inventory. The preview watcher uses selected-chapter checks as well.

`scripts/slides/refresh_storytelling.py` owns supplemental Chapter 1 views and
native table fragments in `shared/generated/chapter-01/storytelling/`. It reads
the pinned database only on explicit refresh, verifies its unchanged checksum,
and records generator, canonical-input, and artifact hashes. The original
`refresh.py` and the provenance of other chapter generators remain unchanged.

## Teaching Chapters 2-3

Chapter 2 moves from fitness for use and data types through quality exceptions,
tidy data, and Accounting Core checks. Its public Tutorial 2.1 and 2.2 activities
keep observations separate from conclusions. Budget and quality exhibits use
the same example functions as the book figures.

Chapter 3 covers tables and types, keys, cardinality, table groups, and the public
Tutorial 3.2 sale. Focused ER views use the book's observed-cardinality function.
They omit unrelated fields and retain the distinction between logical key links
and the source-document trace. The financial tables remain native PowerPoint
tables. The shipment exhibit explicitly selects the item-cost postings, while
the invoice exhibit shows that invoice's complete posting group.

## Teaching Chapters 4-8

The five decks form the Excel teaching sequence. Chapter 4 builds a reviewable
workbook, Chapter 5 prepares related attributes, Chapter 6 profiles and explains
the Furniture margin, Chapter 7 tests forecasts and management decisions, and
Chapter 8 documents audit procedures and their follow-up.

Each deck includes its chapter's public guided activities and checkpoints.
Use the matching start file on the book's Companion Files page when joining
mid-sequence. Chapters 4-7 extend the Furniture Analysis workbook; Chapter 8
starts AuditAnalytics.xlsx. Financial tables and code remain native editable
PowerPoint content. Cropped reference panels and focused charts are embedded
figures with public sources or chart data included in the source export.

The notes distinguish standard-cost margin from ledger gross profit, the
forecast's planning range from a formal prediction interval, assumed promotion
lift from observed demand, and audit flags from supported findings. Chapter 8's
sample size is a teaching selection, not a general audit sample-size rule.

Use `chapter-04` through `chapter-08` with the preview command below. Review both
formats and the public notes when revising a deck. Future drafts use `pilot`
until author approval is recorded in the manifest. Default site assembly and source export include
approved decks. `--include-pilot` is an explicit local review option.

## Authoring conventions

Sparse teaching slides keep their titles at the top and center the content
below them. Selected Reveal slides introduce one point, comparison column, or
table row at a time. The first item is visible on arrival; press **Right Arrow**
or **Space** to reveal the next item, and **Left Arrow** to go back. Earlier
items stay visible and the layout stays in place. There is no automatic advance.
PowerPoint shows the complete content as editable text and tables.
The preview stays in slide mode on narrow screens so advancing remains explicit.

Opt into these treatments on a teaching-slide heading:

```markdown
## Explain the finding {#ch01-example .balanced .stepwise}
```

- `.balanced` centers the content beneath the title with more space between points.
- `.stepwise` reveals paragraphs, list items, or comparison columns in sequence.
- `.step-rows` reveals table rows in sequence, keeping the heading and first row visible.
- A `.persistent` fenced div keeps an accounting qualification or instruction
  visible throughout a stepped explanation. PowerPoint includes it as native text.

Omit the step class when students need the complete exhibit or instructions at
once. Keep a brief delivery cue in the public notes for slides taught in steps.
These classes affect Reveal; PowerPoint spacing comes from the reference layouts.

- Keep one `chapter-NN/index.qmd` source for both formats. Use `#` for module
  dividers, `##` for teaching slides, and unique `chNN-` identifiers.
- Set per-format filenames to `index.html` and `chapter-NN.pptx` in the chapter's
  metadata. Keep chapter prose and slides as separate teaching narratives.
- Give each teaching slide a `.notes` block. Include an accounting qualification
  where it changes the interpretation, and distinguish evidence from hypotheses.
- Use native Markdown text, lists, and simple tables so PowerPoint content stays
  editable. Prefer at most two balanced columns. Split crowded slides rather
  than reducing instructional text below the approved size.
- Put explanatory prose before a table. Pandoc's PowerPoint writer can start an
  untitled extra slide when prose follows a table. Artifact checks reject slide
  counts that differ from the source's opening, module, and teaching slides.
- Reference staged images under `/_shared/` and provide meaningful `fig-alt`
  text. The presentation filter selects PNG derivatives for PowerPoint.
  Embedded graphics can be resized or replaced, while their canonical sources
  remain the place to edit their internal labels and shapes.
- Include small shared definitions and references from `shared/fragments/`
  through the staged `/_shared/fragments/` paths. Shared fragments have no
  headings, YAML, page breaks, or book-only cross-references.
- Use root variable shortcodes for edition and dataset information. Preparation
  copies `_variables.yml`; never maintain a separate presentation copy manually.
- Use explicit published book URLs for further instructions. Keep the essential
  teaching sequence usable without animation or interactivity.
- Identify source and license. Adaptations retain CC BY-SA 4.0 credit unless a
  particular asset states separate terms.

## Sources and generated inputs

Canonical book figure builders and Draw.io sources continue to own their
content. Focused presentation views and the native margin table live in
`shared/generated/chapter-01/`. The public calculation consumes the pinned
dataset through a read-only connection during an explicit authoring refresh.
Ordinary public builds consume the reviewed generated facts without a dataset.

Chapter 2–3 generated examples live in their corresponding `shared/generated/`
folders. `shared/calculations/foundations.py` supplies public book and slide
examples, and `scripts/slides/refresh_foundations.py` writes the presentation
views, native table includes, and prepared variable values. Source hashes and
artifact hashes enforce the same explicit-refresh contract as Chapter 1.

Chapter 4-8 public exhibits are prepared by `scripts/slides/refresh_excel.py`.
The book and decks share `shared/calculations/excel_analysis.py` for the margin
bridge, forecast backtest, flexible budget, promotion model, and audit examples.
The explicit refresh checks the pinned dataset, rebuilds canonical book diagrams,
exports them, and then prepares the focused slide views. Ordinary builds check
provenance and consume the committed artifacts without opening the dataset.

`slides/_shared/`, the copied variables, and `_build/` are disposable prepared
inputs and outputs. Do not edit them. Modify the corresponding canonical source,
then prepare and render again. A changed chapter source needs editorial review
of its deck even when no shared fragment changed.

## Teaching Chapters 9-12

The SQL decks follow the public manufacturing-variance tutorials. Chapter 9
introduces SELECT, filters, NULLs, types, and ranking. Chapter 10 adds joins,
aggregation, grain controls, and comparable labor/output populations. Chapter 11
builds monthly measures with CASE, dates, windows, CTEs, and a saved view.
Chapter 12 tests document traces, cutoff, purchasing controls, and labor evidence.

Query definitions in `shared/calculations/sql_ch09.py` through `sql_ch12.py`
serve both book figures and slide exhibits. `scripts/slides/refresh_sql.py`
executes only public SELECT queries against the read-only pinned database.
It evaluates the view definition as a CTE without creating a database object.
Ordinary builds use committed facts, tables, SQL excerpts, and chart data.
Changing a shared query requires the explicit shared refresh.

SQL examples and results occupy successive slides. Clauses taken from longer
queries are identified in the narration; structural patterns with ellipses are
explicitly labeled. The book and its public tutorial scripts supply the complete
procedures. The `sql-example` class increases Reveal code type without changing
earlier decks. Native PowerPoint code text and result tables remain editable.

Use `chapter-09` through `chapter-12` in the preview command.

## Teaching Chapters 13-16

The Power BI decks move from prepared tables and filter paths to explicit DAX
measures, management reporting pages, and an exception register. Static states
show what a selection changes and how a filtered visual window differs from a
model measure. The short code examples and simple financial tables are editable
PowerPoint content; the focused model and monitoring diagrams are graphics.

`shared/calculations/bi_ch13.py` through `bi_ch16.py` supply the public calculations
to both the canonical book figure builders and `scripts/slides/refresh_bi.py`.
Their database functions accept the caller's read-only connection. Ordinary
builds read committed examples without Power BI Desktop or the private dataset.
The explicit shared refresh checks the dataset checksum and recreates the facts,
tables, focused diagrams, and chart data. The separate tutorial instructions in
the book remain the complete procedure for working inside Power BI Desktop.

Use `chapter-13` through `chapter-16` in the preview command. Check model meaning,
formula/result sequences, interaction explanations, and public teaching notes.
These slides do not execute the Power BI tutorials or substitute for inspecting
the actual Power BI report. The public notes identify the Key Measures home
table and Companion Files starting points for students joining mid-sequence.

## Teaching Chapters 17-19

The capstone decks brief the independent work. Chapter 17 organizes the lender
package around its four milestones. Chapter 18 structures the make, buy, and
reprice decision. Chapter 19 connects audit planning, fieldwork, evaluation,
and continuing monitoring. Each deck identifies the required files, evidence,
decision points, and deliverables without disclosing computed case solutions.

These briefings use public requirements directly, with editable text and simple
tables. They do not need new generated data. Links point to the relevant book
requirements, and source hashes flag later requirement changes for review.
The instructor can pause at milestone checkpoints and assign independent work.
Chapter 19 distinguishes planned external procedures from work actually performed.

Use `chapter-17` through `chapter-19` in the preview command. Review the assignment
scope, pacing, checkpoints, and public narration when revising the assignment.

## Local workflow

From the repository root:

```sh
python scripts/build_all.py
python scripts/build_all.py --refresh-shared
python scripts/build_all.py --preview chapter-01
```

The full build stages the book downloads and both slide formats independently,
renders book HTML last, and then assembles the site. Use the ordinary `quarto
preview` command for book editing. A browser preview checks HTML appearance,
navigation, notes, and resources. Review the separate PowerPoint output in
PowerPoint for layout, reading order, notes, hyperlinks, and direct editing of
text and table cells.

To browse the assembled book, slide links, and downloads, run this from the
repository root after the full build:

```sh
python -m http.server 8002 --bind 127.0.0.1 --directory _book
```

Open `http://127.0.0.1:8002/front-matter/downloads.html`. Keeping the server's
working directory at the repository root lets later builds replace `_book` on
Windows. The preview is local to this computer.

Future pilots remain review artifacts until their approval status allows
publication. Automated checks supplement visual review. They cannot
establish that every slide is readable in a classroom or that native PowerPoint
behavior has been inspected.

For automated browser review, install the optional review requirements and use
an existing Chrome installation:

```sh
python -m pip install -r scripts/slides/requirements-review.txt
python scripts/slides/browser_check.py --chapter chapter-01
```

The browser checker serves only the generated Reveal directory on a temporary
loopback port. It records keyboard and speaker-view behavior, resources, image
alt text, and element bounds in desktop and narrow views. Screenshots, a contact
sheet, and `outputs/build/browser-review.json` support visual inspection.
`--chrome PATH` selects a nonstandard Chrome installation. The checker does not
download a browser, inspect native PowerPoint, or establish screen-reader
accessibility. Remote runtime dependencies fail the check because published
decks must carry their required resources locally.

On Windows with Microsoft PowerPoint installed, the native artifact checker
opens a dedicated hidden copy, exports each slide, checks text/table fit, and
tests editing and reopening a separate copy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/slides/powerpoint_check.ps1
```

It saves images and a report under `outputs/build/powerpoint-review/`. It leaves
the generated deck unchanged. Inspect the rendered slides individually and
review the notes. Slide-show UI behavior, reading order, and screen-reader
behavior still require an interactive review.

The propagation acceptance script runs isolated theme, layout, fragment,
variable, diagram, and calculation experiments:

```sh
python scripts/slides/propagation_check.py
```

That authoring check requires the pinned dataset and `rsvg-convert`, in addition
to Quarto and the build requirements. Set `CHARLESRIVER_DATA` to point at an
existing dataset directory. Its deliberate test changes stay under
`outputs/build/propagation-check/` and must never be published.
