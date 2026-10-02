# Contributing to Accounting Analytics

Thank you for helping improve *Accounting Analytics: An Integrated Approach*.
Contributions from instructors, students, and practitioners are welcome.

## Share feedback

You do not need coding experience to contribute. To report an error, suggest an
exercise, or share classroom feedback, open an issue in the
[public book repository](https://github.com/mmcodesso/Accounting_Analytics_Book/issues).
A GitHub account is required. Include the chapter or section, describe the issue
or suggestion, and explain any proposed correction.

## Propose an edit

If you would like to edit the book directly, submit a pull request to the
[public book repository](https://github.com/mmcodesso/Accounting_Analytics_Book).
For substantial additions or changes, start with an issue to discuss the proposal.
Keep each contribution focused, describe what changed and why, and check the
rendered result when changing book content or formatting.

The following guide explains the source files and local build process. For an
introduction to the book and its teaching approach, see the [README](README.md).

## Book source layout

The book sources use Quarto Markdown (`.qmd`); `README.md` is the repository guide.
Each chapter has its own numbered folder under
`chapters/`, with one main narrative file and smaller companion files:

```text
chapters/
  01-role-of-analytics/
    chapter.qmd
    _tutorial-01.qmd
    _summary.qmd
    _key-terms.qmd
    _multiple-choice.qmd
    _exercises.qmd
    _further-reading.qmd
    _references.qmd
  02-understanding-data/
    chapter.qmd
    _tutorial-01.qmd
    _tutorial-02.qmd
    ...same supporting files
  03-accounting-data-environment/
    chapter.qmd
    _tutorial-01.qmd
    _tutorial-02.qmd
    ...same supporting files
cases/
  part-1-case.qmd
front-matter/
  preface.qmd
  to-the-student.qmd
  about-the-dataset.qmd
  downloads.qmd
index.qmd
```

Parts I to IV each close with a comprehensive case in `cases/part-N-case.qmd`, registered in `_quarto.yml` after the Part's last chapter. Its requirements build on every chapter in the Part, and the expected answers for instructors sit in hidden comments after each requirement. The chapters of Part V are themselves case chapters: each folder holds `chapter.qmd`, `_further-reading.qmd`, and `_references.qmd`, with no tutorials, summary, key terms, questions, or exercises.

Edit the homepage content and metadata directly in the root `index.qmd`, and
edit the downloads page in `front-matter/downloads.qmd`. The root `index.qmd` is
registered in `_quarto.yml`; it is not an include wrapper. Mark the homepage's
section headings with `{.unnumbered}` to preserve their formatting in print.
The published homepage remains `index.html`, and the former `downloads.html`
address redirects to the moved page. Book download links use project-root paths
(`/downloads/book-latest.pdf`, etc.) to match the publishing workflow.
Visuals and styles remain in their shared directories. The downloads page links
to the companion dataset's releases.

## Editing a chapter

Open only the file relevant to the task, adding other files as needed for context:

| What you are editing | File |
| --- | --- |
| Chapter title, learning objectives, opening scenario, explanations, callouts, or Looking Ahead | `chapter.qmd` |
| A guided tutorial, including its steps, figures, and checkpoint | `_tutorial-01.qmd`, `_tutorial-02.qmd`, etc. |
| Chapter summary | `_summary.qmd` |
| Definitions | `_key-terms.qmd` |
| Multiple-choice questions | `_multiple-choice.qmd` |
| Financial accounting, managerial accounting, and auditing exercises | `_exercises.qmd` |
| Further reading | `_further-reading.qmd` |
| Full APA 7 list of every source cited in the chapter | `_references.qmd` |

`chapter.qmd` includes each tutorial right after the section it practices, at the
end of a `##` section, using a standalone directive surrounded by blank lines:

```markdown
{{< include _tutorial-01.qmd >}}
```

At the end, it includes the supporting files in this order: summary, key terms,
multiple-choice questions, exercises, further reading, and references. Each companion file
owns its section heading and any preceding page break. The reader still sees one
complete chapter.

Keep chapter metadata in `chapter.qmd`; companion files must not have YAML
metadata. Prefix companion filenames with `_` so Quarto does not render them as
standalone pages. Preserve the existing heading levels, question and exercise
numbers, and figure identifiers when editing.

For multiple-choice options, use an uppercase letter, a period, and **two spaces**
before the text. Quarto then renders each option as a separate list item with
aligned continuation lines. Keep a blank line between the question and its options:

```markdown
**1.** Question text?

A.  First option
B.  Second option
C.  Third option
D.  Fourth option
```

Keep each question's A-D choices together as one list. This works across HTML,
PDF, EPUB, and Word; a single space after `A.` is treated as ordinary paragraph
text. See [Pandoc's lettered-list rules](https://pandoc.org/MANUAL.html#extension-fancy_lists).

List each key term in the chapter that teaches it. A later chapter repeats a
term only when it adds something new, and the repeated entry keeps the same
first sentence, so readers never meet two competing definitions.

Cite sources in APA 7 style, for example (Vasarhelyi et al., 2015) or
(Provost & Fawcett, 2013), and list every cited source in `_references.qmd`.
Further Reading is a separate, annotated selection of five to eight sources.
Refer to figures in the text with Quarto cross-references such as `@fig-01-03`
rather than typing "Figure 1.3", so numbers stay correct when figures move.
Caption tables with a line such as `: Title {#tbl-02-01}` directly after the
table, and refer to them as `@tbl-02-01`. Quarto numbers them and keeps each
caption with its table in the PDF.
Place each table inline in `chapter.qmd`, right after the paragraph that
introduces it; tables are not kept in separate files.

Use project-root paths for shared assets, for example
`![Caption](/visuals/svg/figure.svg)`. Paths within an included file are resolved
from `chapter.qmd`, not from the companion file. See the
[Quarto includes documentation](https://quarto.org/docs/authoring/includes.html).

For a new chapter, create `chapters/NN-short-title/chapter.qmd` and register only
that main file in the appropriate part of `_quarto.yml`. Add companion files and
include directives as content is written. Keep existing `aliases` metadata when
editing moved pages: it preserves the former HTML addresses.

## Figures

Diagrams are Draw.io files in `visuals/src/`, one page per file, named
`fig-CC-NN-slug.drawio`. The pre-render hook exports each diagram twice: a
light-theme SVG in `visuals/svg/` for the website, EPUB, and Word, and a vector
PDF in `visuals/pdf/`. For the PDF book, `filters/pdf-figures.lua` swaps the PDF
in for the SVG, so figure text stays sharp and searchable in print. Always
reference the SVG in the chapter; the filter handles the PDF.

Every figure follows one design standard, so it reads well on screen, in the
PDF, and on paper:

| Rule | Value |
| --- | --- |
| Frame | 860 px wide (an invisible full-width shape), at most 980 px tall, white background. Every figure then prints at the same scale. |
| Text | Helvetica. Body 13 px, headers 14 px bold, never below 12 px, which prints at 7 pt or larger. Ink #2C3E50 on white or light fills. |
| Dark fills (white text) | Blue #1A5276, teal #117A65, gray #5D6D7E, coral #B03A2E, amber #8A5D00 |
| Light fills (ink text) | #EAF2F8, #E8F6F3, #FEF5E7, #FDEDEC, #F2F3F4. Orange #F39C12 is a highlight fill for ink text only. |
| Contrast | Every text and background pair at 4.5:1 or better |
| Lines | At least 1.5 px, with the same meaning in every figure: solid gray for links within a table group or a process flow, heavier (2.5 px) solid amber for links to another table group, and dashed amber for postings to the ledger and the source-document trace. |
| Meaning | Never carried by color alone: add a label, a line style, or a symbol |
| Content | No titles, counts, or "Appendix" text inside the figure (the caption supplies the title), and only real Charles River values. ER line endings are computed from the data. |

The Part I figures are generated by `scripts/figures/`, which reads
`datasets/CharlesRiver.sqlite` (read-only), so sample rows are real and every
crow's-foot ending matches the data:

```sh
python scripts/figures/build.py                    # rebuild every generated figure
python scripts/figures/build.py --figure fig-03-07 # rebuild one figure
python scripts/figures/check_figures.py --exports  # check all figures and their exports
```

`check_figures.py` checks every `.drawio` file against the standard, whether or
not it was generated: frame width, font sizes, palette, contrast, and ER
endings. If you hand-edit a generated figure, port the change to the generator
(or remove the figure from its chapter module), or the next build will
overwrite it.

## Screenshots

Excel screenshots go in `visuals/png/`. Capture at 125–150% zoom and crop to at
most eight columns so the text prints at 7 pt or larger; hide the columns in
between when a step needs columns that are far apart. Mark the cells the step
discusses with a single red box, and keep the status bar in the shot when the
step relies on a record count. Make sure the alt text describes what the image
actually shows.

## Building the book

From the project root, render the desired format:

```sh
quarto render --to html
quarto render --to pdf
quarto render --to epub
quarto render --to docx
```

The pre-render hook requires Python and the Draw.io desktop executable to export
diagrams and the cover. Set `DRAWIO_BIN` if Draw.io is not found automatically.
PDF output also requires a TeX installation; diagrams reach the PDF as the
vector PDFs that the hook exports. The existing publishing workflow installs
these build dependencies.

## License

Contributions to the book are shared under the same
[CC BY-SA 4.0 license](LICENSE) as the existing material. Give appropriate credit
for material you adapt, link to its license, and indicate any changes. Only
include material you have the right to share under these terms.
