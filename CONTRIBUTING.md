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
    ...same supporting files as chapter 1
    _tutorial-01.qmd
    _tutorial-02.qmd
    _summary.qmd
    _key-terms.qmd
    _multiple-choice.qmd
    _exercises.qmd
    _further-reading.qmd
front-matter/
  preface.qmd
  to-the-student.qmd
  about-the-dataset.qmd
  downloads.qmd
index.qmd
```

Edit the homepage content and metadata directly in the root `index.qmd`, and
edit the downloads page in `front-matter/downloads.qmd`. The root `index.qmd` is
registered in `_quarto.yml`; it is not an include wrapper. Mark the homepage's
section headings with `{.unnumbered}` to preserve their formatting in print.
The published homepage remains `index.html`, and the former `downloads.html`
address redirects to the moved page. Book download links use project-root paths
(`/downloads/book-latest.pdf`, etc.) to match the publishing workflow.
Visuals and styles remain in their shared directories. The downloads page links
to the companion dataset's releases.
Chapter 3 follows the same split structure, with two tutorials and five supporting
sections. Add `_references.qmd` when its separate reference list is written.

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

`chapter.qmd` includes each tutorial where it belongs in the narrative, using a
standalone directive surrounded by blank lines:

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
PDF output also requires a TeX installation and SVG conversion support. The
existing publishing workflow installs these build dependencies.

## License

Contributions to the book are shared under the same
[CC BY-SA 4.0 license](LICENSE) as the existing material. Give appropriate credit
for material you adapt, link to its license, and indicate any changes. Only
include material you have the right to share under these terms.
