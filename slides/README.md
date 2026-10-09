# Chapter slides

Each chapter can have one deck, `slides/chapter-NN/index.qmd`, which Quarto renders twice: a Reveal.js
deck for the browser and a native PowerPoint file. A deck is published as soon as its source exists,
like a chapter. There is no approval or review step, and editing a chapter never blocks a build.

A deck holds only its slides. The title slide, the footer, and every figure and table come from the book
at each build, so when a chapter changes, its deck changes with it.

## The deck standard

Every deck follows the same sequence, so students always know where they are.

| Part | Slides | How |
|---|---|---|
| Opening | Title: "Chapter N: Title" with the book's title | generated; the deck has no YAML |
| | In this chapter: the Part, the chapter's place in it, and the deck's modules (two columns past eight modules, at the evidence size when a column would pass about twelve lines; tutorials by number) | `::: {.roadmap}` |
| | Learning objectives, on a second slide "Learning objectives (continued)" when they do not fit one (about 650 characters) | `{{< book-objectives >}}`, or `1-3` and `4-6` |
| | Opening scenario: who, the business question, why it matters | written |
| Modules | one per numbered section of the chapter: a divider `# <section title>`, then 2–6 slides | dividers get the book's section number |
| Tutorials | `# Guided Tutorial N.k: Title`, the step titles, one key figure, the checkpoint | `{{< book-steps N.k >}}`, `{{< book-checkpoint N.k >}}` |
| Closing | `# Looking Ahead`: summary, key terms, practice and next chapter, About these slides | `{{< book-terms >}}`, `{{< book-exercises >}}`, `{{< book-next >}}` |

A deck has about 30–45 teaching slides, depending on how many sections the chapter has, and 3–4
check-and-answer pairs. `slides/chapter-01/index.qmd` and `slides/chapter-02/index.qmd` are the reference decks;
`slides/chapter-03/index.qmd` shows a figure in detail.

## Case decks

The capstone cases of Part V (and, later, the comprehensive cases that close Parts I–IV) have no tutorials,
key terms or exercises. Their decks follow a case standard instead, so that one deck can open the case and
then guide students through it phase by phase (the author's decision: a kickoff plus a phase guide, with
method guidance and no answers). `slides/chapter-17/index.qmd` is the reference deck.

| Part | Slides | How |
|---|---|---|
| Opening (the kickoff) | Title · In this chapter · Learning objectives · Opening scenario · What you will hand in · How your work will be judged (two slides when long) | `{{< book-deliverables >}}`, `{{< book-criteria 1-3 >}}` |
| The case's own sections | a `#` module for each section before the requirements (The Situation, The Data You Will Use, …): the request and its conditions, the exhibit tables, the tools and files, the Watch outs as slides, In Practice in the notes | book tables by ID |
| Getting Started | Set up before you begin · the milestones · Choose the tool for each step · a check on the choice of tool | `{{< book-milestones >}}` |
| One module per phase | divider: the book's `###` phase title, which gets its number (17.4.1). Phase N at a glance · a requirement card per requirement, with its figures and tables · a Watch out or check where the book has one · Milestone N: before you hand it in | `{{< book-requirements 3-5 >}}`, `{{< book-milestones 2-2 >}}`, `{{< book-requirement 3 >}}` |
| Closing | `# Deliverables and Checklist`: Before you submit · `# Looking Ahead`: what the case practiced (the four analytics types), what comes after, About these slides | written |

A capstone deck has about 50–55 teaching slides; a comprehensive case about 25–30.

**Requirement card.** The title states the point. Under it, the requirement's gray source line from the book,
then four bullets that open with a bold label:

```markdown
## Rebuild accrued expenses from their documents

{{< book-requirement 3 >}}

- **Produce:** the balance split into its parts at three year-ends
- **Tool:** SQL: four tables joined under conditions on dates
- **Revisit:** Chapter 3's trace, Chapter 10's joins, Chapter 12's tests
- **Check:** the parts add up to the ledger's balance at every year-end
```

The notes give the requirement's tasks and pitfalls. **Phase at a glance** lists the phase's requirements and
its milestone (`book-milestones` with a range of one gives "Milestone 2: …" as a paragraph). **Milestone
check-in** is four qualitative self-checks ("every adjusted trial balance balances"); its notes may say that
the instructor can release checkpoint values, the book's own words. Checks test the method judgments the
book teaches (which tool, error or estimate, what the records can settle), never the case's results.

Rules for case decks, in addition to those below: no values, expected results or answers anywhere, the notes
included (they live in the released solution files), and never the words "instructor notes" or "answer key",
which the site check rejects.

## Slide patterns

Use only these patterns. Each slide's title states its point.

**Concept.** At most five bullets of about twelve words each.

**Figure.** The book's figure, with "Figure 1.2 · Caption" under it and the book's alt text:

```markdown
## Six stages take a question to a recommendation

{{< book-figure fig-01-02 >}}
```

A tall or dense figure, such as a large ER diagram, can follow its whole view with details. `crop` takes
the left edge, top edge, width and height as fractions of the figure, and the caption reads
"Figure 3.7 · Caption (detail)":

```markdown
{{< book-figure fig-03-07 crop="0,0,1,0.572" >}}
```

The fractions are of the figure's drawing (its SVG viewBox), and the PowerPoint PNG is cut through the same
geometry, so both formats cut in the same place. Set them from the drawing's coordinates in its `.drawio`
source (a fraction is the y of the cut over the drawing's height), and cut through blank space or along a
row boundary of a mocked grid. Two details may overlap, so that a table
or relationship needed by both appears whole in each. The crop is cut from the book's figure at every build,
so a change to the figure flows into it, but a change to its layout can move what the crop shows: look at
the detail slides again after the figure changes.

**Table.** A native, editable table from the chapter, with "Table 1.2 · Caption" above it (a caption's first
sentence, when it goes on to define the table's symbols; put the definitions in the notes). `columns` and
`rows` narrow it, each a comma-separated list of headers or first-column values; `rows` keeps every row
whose first cell matches, so `rows="Quantitative"` takes all of a group. Column widths follow the content,
so no column is narrower than its longest word (a word in code, such as `USERELATIONSHIP`, gets the extra
room its wider font needs):

```markdown
{{< book-table tbl-01-03 columns="Table Group,Primary Accounting Use" rows="Accounting Core,Master Data" >}}
```

A long table goes on two slides, each with its own rows. Leave out a column the slide does not need rather
than let the table run off the slide (the PowerPoint check cannot flag that, so look at the images). A
range takes rows by position, which also works when the first cells hold commas, such as function
signatures, that `rows` cannot name:

```markdown
{{< book-table tbl-05-01 1-5 >}}
```

**Code.** A short query (about six lines of at most about 50 characters, no data values) goes in a
```` ```sql ```` block, which both formats show in the code font at the evidence size, without line numbers. Longer queries, and their results, come from the book's DB Browser mocks.

**Comparison.** Two columns (`:::: {.columns}` with two `::: {.column}`); PowerPoint takes at most two.

**Callout.** `## In Practice: …`, `## Watch out: …` or `## Connecting the Dots: …` with the class
`.in-practice`, `.watch-out` or `.connecting-dots`. The slide gets the book's teal, coral or amber bar.

**Check and answer.** A question slide, then its answer on the next slide, so the pause works in both
formats:

```markdown
## Check your understanding {.check}

Which stage of the workflow usually takes the most time?

## Preparing and cleaning the data {.answer}
```

**Notes.** Every `##` slide ends with 2–4 sentences of talk track in `::: {.notes}`, and a check slide's
notes or its answer slide give the answer.

## Rules

- No YAML front matter, and no author name anywhere.
- No data values, document IDs or dates typed into slides or notes. They stay in the book's figures and
  tables, which the slides pull in. Describe counts qualitatively, as the chapters do. A literal the
  chapter itself uses (an illustration, a framework's year) needs a rule in `facts/literals/`, which
  `python facts/phase7_cli.py lint` checks.
- Put text before a table, never after it: in PowerPoint, text after a table starts an untitled slide.
- Use `::: {.incremental}` for bullets that appear one at a time. A `. . .` pause prints as text in
  PowerPoint.
- Write to the student as "you", as the chapters do.

## Other shortcodes

| Shortcode | Shows |
|---|---|
| `{{< book-objectives >}}`, `{{< book-objectives 4-6 >}}` | the chapter's learning objectives, verbatim, all or a range |
| `{{< book-steps 1.1 >}}`, `{{< book-steps 4.1 7-11 >}}` | the step titles of a Guided Tutorial, all or a range (a tutorial of more than about eight steps goes on two slides) |
| `{{< book-checkpoint 1.1 answers="hide" >}}`, `{{< book-checkpoint 10.3 1-4 lead="true" >}}` | the tutorial's checkpoint, all or a range of items (a checkpoint of more than five items goes on two slides, the second titled "Checkpoint (continued)"), without the answers in parentheses |
| `{{< book-terms >}}` | the chapter's key terms, in one paragraph |
| `{{< book-exercises >}}` | the exercise titles, by perspective |
| `{{< book-next >}}`, `{{< book-title >}}`, `{{< book-link >}}` | the next chapter, the book's title, and the chapter's web address (inline) |
| `{{< book-requirement 3 >}}` | a case requirement's source line, "Requirement 3 · Title (Chapters …)", gray at the evidence size in both formats |
| `{{< book-requirements >}}`, `{{< book-requirements 3-5 >}}` | the case's requirement titles with their chapters, all or a range by number |
| `{{< book-milestones >}}`, `{{< book-milestones 2-2 >}}` | the milestones of Getting Started, numbered, or one of them as a paragraph |
| `{{< book-deliverables >}}`, `{{< book-criteria 1-3 >}}` | the numbered items of Deliverables and Checklist, and the bullets of What a Strong Submission Includes, all or a range |

Shared definitions can be included as in the book: `{{< include /_shared/fragments/_accounting-analytics.qmd >}}`.

## Commands

From the repository root:

```sh
python scripts/build_all.py --check                         # fast source checks (no Quarto, no dataset)
python scripts/build_all.py --slides-only --chapter chapter-01   # render one deck in both formats
python scripts/build_all.py --preview chapter-01            # live browser preview
python scripts/build_all.py                                 # the book and every deck
```

Rendered decks land in `slides/_build/` (`revealjs/chapter-NN/index.html`, `pptx/chapter-NN/chapter-NN.pptx`);
the full build assembles the Reveal decks into `_book/slides/`. The PowerPoint files are built only locally and
published as `chapter-NN.pptx` on the GitHub release of the book's revision (`python scripts/release.py publish`);
GitHub Actions renders the Reveal decks with the site (`python scripts/build_all.py --site`).

To look at a deck the way students will see it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/slides/powerpoint_check.ps1 -Deck slides/_build/pptx/chapter-01/chapter-01.pptx
python scripts/slides/browser_check.py --chapter chapter-01
```

The first exports every PowerPoint slide as an image to `outputs/build/powerpoint-review/` and flags text that
overflows its box (a table that runs off the slide is not flagged, so look at the images). The second takes
screenshots of the Reveal deck in `outputs/build/browser-review/` and checks layout, notes and resources; it needs
`scripts/slides/requirements-review.txt` and Chrome.

## Starting a deck for chapter N

1. Create `slides/chapter-NN/index.qmd`, starting from Chapter 1's deck structure.
2. Write a `#` divider for each numbered section, using the section's exact title so it gets its number.
3. Cite the chapter's figures and tables by ID; check their IDs in the chapter.
4. Run `python scripts/build_all.py --check`, then `--slides-only --chapter chapter-NN`, and look at both formats.

The chapter page's "View slides · Download PowerPoint" links and the Downloads page's Slides column appear
on their own once the deck exists.

## How it works

| File | Role |
|---|---|
| `scripts/slides/book_index.py` | reads the book (`_quarto.yml` and each chapter, includes expanded) into `_shared/book.json`: titles, Parts, sections, objectives, figures, tables, key terms, tutorials, exercises, and a case's requirements, milestones, deliverables and criteria |
| `scripts/slides/prepare.py` | writes each deck's `_metadata.yml` (title, subtitle, footer, output names), stages the cited figures with a PNG for PowerPoint (exported by Draw.io from the same source, cached in `outputs/slide-png/`) and each crop under its own name, the fragments, the backgrounds and the themed templates |
| `shortcodes/book.lua` | the `book-*` shortcodes, which read `_shared/book.json` |
| `filters/deck.lua` | numbers the dividers, fills the roadmap, gives dividers, callouts and checks their backgrounds |
| `filters/images.lua` | swaps a hand-placed SVG for its PNG in PowerPoint |
| `theme/tokens.yml` | colors, fonts and sizes for both formats |
| `theme/reveal.scss` | the Reveal design |
| `scripts/slides/pptx_theme.py` | the PowerPoint template, built from Pandoc's default: layouts, backgrounds, footer, slide numbers, text sizes |
| `scripts/slides/pptx_finish.py` | after rendering, formats PowerPoint's tables and figure captions like Reveal's (PowerPoint draws only built-in table styles) |
| `scripts/slides/verify.py` | the source checks of `--check` and the checks of the rendered decks and the assembled site |

Everything under `_shared/`, `_build/`, each deck's `_metadata.yml` and `slides/_variables.yml` is generated and
gitignored; edit the sources above instead.
