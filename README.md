# Accounting Analytics: An Integrated Approach

This repository contains the source for *Accounting Analytics: An Integrated
Approach*, an open educational resource textbook. The book is designed to help
accounting and business students learn how to extract, prepare, analyze, and
visualize data using Excel, SQL, and Power BI.


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
  02-understanding-data/
    chapter.qmd
    _tutorial-01.qmd
    _tutorial-02.qmd
    ...same five supporting files
  03-accounting-data-environment/
    chapter.qmd
front-matter/
  index.qmd
  preface.qmd
  to-the-student.qmd
  about-the-dataset.qmd
  downloads.qmd
index.qmd
```

Edit the homepage in `front-matter/index.qmd` and the downloads page in
`front-matter/downloads.qmd`. Quarto requires a homepage entry at the project root,
so `index.qmd` contains only an include directive for `front-matter/index.qmd`.
Keep homepage content and metadata in that Quarto file, and mark its section
headings with `{.unnumbered}` to preserve their formatting in print. Register the wrapper
in `_quarto.yml`, not the included homepage file. The published homepage remains
`index.html`, and the former `downloads.html` address redirects to the moved page.
Book download links use project-root paths (`/downloads/book-latest.pdf`, etc.)
to match the publishing workflow. Visuals, datasets, and styles remain in their
shared directories.
Chapter 3 is a placeholder; add companion files when those sections are written.

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

`chapter.qmd` includes each tutorial where it belongs in the narrative, using a
standalone directive surrounded by blank lines:

```markdown
{{< include _tutorial-01.qmd >}}
```

At the end, it includes the supporting files in this order: summary, key terms,
multiple-choice questions, exercises, and further reading. Each companion file
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

Unless otherwise noted, this work is licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).

You may share and adapt the material for any purpose, including commercial use,
provided that you give appropriate attribution and distribute adaptations under
the same license.
