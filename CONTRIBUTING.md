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
  downloads.qmd
supplementary/
  start-files/
  solutions/
  README.md
index.qmd
```

Parts I to IV each close with a comprehensive case in `cases/part-N-case.qmd`, registered in `_quarto.yml` after the Part's last chapter. Its requirements build on every chapter in the Part, and the expected answers for instructors sit in hidden comments after each requirement. The chapters of Part V are themselves case chapters: each folder holds `chapter.qmd`, `_further-reading.qmd`, and `_references.qmd`, with no tutorials, summary, key terms, questions, or exercises. They are independent capstone cases: none mentions another, so a course can assign any one as a final project, and each has a Getting Started section with milestones and a Deliverables and Checklist section. The book's closing page is `back-matter/closing.qmd`, registered after Part V.

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
light-theme SVG in `visuals/svg/` for the website and the slides, and a vector
PDF in `visuals/pdf/` (the EPUB and Word carry PNGs of the diagrams, see below). For the PDF book, `filters/pdf-figures.lua` swaps the PDF
in for the SVG, so figure text stays sharp and searchable in print. Always
reference the SVG in the chapter; the filter handles the PDF.

Draw.io writes every label of an SVG as HTML (a `foreignObject`), which browsers draw, plus a fallback for viewers
that cannot. The exporter asks Draw.io for its plain-text fallback (`--embed-svg-fonts false`) instead of a PNG of
every label, and removes the markup that no viewer needs, so the 165 SVGs are about 10 MB instead of 101 MB and
the website and the Reveal decks look exactly as before. `--svg-labels png-fallback` brings the PNGs back (only
`rsvg-convert` and Inkscape need them, see below). This runs automatically during export and uses only Python's
standard library.

The cover source is `visuals/cover/accounting_analytics_cover.drawio`. The exporter
creates `cover-web.png` at 510 x 660 pixels for the website and README,
`cover.png` at 1105 x 1430 pixels for EPUB (close to the background's native
1103 x 1426 resolution), and `cover.pdf` for the PDF book's
full-page cover. PNG exports use lossless compression; the PDF preserves the
source's vector text over its raster background. All three variants use the
same checksum-based incremental export checks as the chapter figures.

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
vector PDFs that the hook exports.

### The whole build in one command

`python scripts/build_everything.py` runs every build step in order (checks, figures, companion and solution
files, instructor guides and PDFs, the book and its decks, tests) and skips what is current; `--plan` shows what
would run and why. The [README](README.md#the-complete-build-in-one-command) describes it. The rest of this
section is what each step runs.

### What is built where

GitHub Actions (`.github/workflows/publish.yml`) renders and deploys only the
website: `python scripts/build_all.py --site` renders the book's HTML and the
Reveal decks, with no TeX, Draw.io, or PowerPoint step. It checks that the
committed Draw.io exports are current (`export_drawio_svgs.py --verify`), so
export changed figures locally and commit them. Everything readers download is
built locally and published by `scripts/release.py` as the assets of the GitHub
release of the book's revision (`book` in `_variables.yml`):
the PDF, EPUB and DOCX named from the edition and revision (for the first edition,
revision 2027.1, `Accounting_Analytics_First_Edition_Rev_2027_1.pdf`), `chapter-NN.pptx` for each deck,
and the companion and solution files, which live untracked in `supplementary/`.
The text keeps linking them by root path (`/downloads/book-latest.pdf`,
`/supplementary/...`), and `filters/slide-links.lua` points those links at the
release in every format.

```sh
python scripts/release.py status            # built, current, and on the release?
python scripts/release.py publish --dry-run # the plan: what would be built and uploaded
python scripts/release.py publish           # build what is stale, upload what changed, push main
python scripts/release.py bump 2027.2       # start a new revision, then commit and publish
python scripts/release.py notes             # preview the release page (--update puts it on the release)
```

The text of the release is a page in the manner of the Downloads page: the book (with a link to the website, which
always shows the newest text, and to the newest revision), the dataset, the slides, companion and solution files by
chapter, and the checksums. `release_notes` in `scripts/release.py` builds it from the Supplementary Material table
of `front-matter/downloads.qmd`, the `dataset` block of `_variables.yml`, and the release's manifest, so a new row on
the Downloads page appears on the release too. `publish` writes it every time (`publish --dry-run` previews it in
`outputs/release/release-notes.md`); `notes` rewrites it without publishing.

`publish` needs a clean `main` and the GitHub CLI, signed in. A local build
records what its files were built from (`outputs/build/fingerprints.json`), so
`publish` rebuilds only what is out of date: the PDF, EPUB, DOCX and every deck
when any book source changed (`build_all.py --release`), otherwise only the decks
whose sources changed (`--release --slides-only --chapter chapter-NN`). It never
renders the HTML or the Reveal decks, which GitHub Actions renders with the site;
the full local build (`build_all.py`) still does, for a preview, and records its
files as current too. It uploads a book or
deck file when it was built from other sources than the copy on the release (a
rebuild changes the bytes, not the content), a companion file when its SHA-256
changed, and any file the release lacks, then uploads `manifest.json`, which
records each file's size, SHA-256, and sources. A new revision is tagged at the
commit it is first published from; later publishes of the same revision replace
only the changed files. The workflow's check fails when the site links a file the
release lacks, and warns when a file on the release is older than the text.

### The diagrams in the EPUB and the DOCX

The website and the PDF keep the diagrams as SVG and vector PDF. The labels of an SVG are HTML, which an EPUB reader or
Word cannot draw, and Draw.io's SVGs used to carry a PNG of every label for them (101 MB in all), so Pandoc put 101 MB
into the EPUB as it was and into the DOCX twice (the SVG and a PNG made from it) and the two formats were 69 and 83 MB.
They now carry one optimized PNG per diagram instead, drawn from the Draw.io source, and the SVG files stay the
authoritative copies: nothing in `visuals/src`, `visuals/svg` or `visuals/pdf` is touched. (The SVGs themselves are now
about 10 MB, see "Smaller SVG files" below, but their plain-text label fallback would show long or bold labels cut
short in an EPUB, so the PNGs stay.)

**How it works.** `filters/raster-figures.lua` (registered in `_quarto.yml`, active only for `epub` and `docx`)
points each `visuals/svg/<name>.svg` at `outputs/ebook-figures/<name>.png`. `scripts/figure_raster.py` makes those
files: it renders the Draw.io source at 1728 pixels across (the book's own exporter, so fonts and labels are exact),
checks that the aspect ratio is the SVG's, reduces the image to the smallest adaptive palette of at most 256 colors
that stays within a small error (no dithering; the white background and the flat fills stay exact; a figure that cannot
be reduced, such as a photograph, stays an RGB PNG), and stamps a pixel density that keeps it as large on the page as
the SVG was. Pandoc then writes the picture parts, relationships and sizes itself, so the files stay normal EPUB and
Word documents. The settings are in `visuals/ebook-figures.yml`.

**Install once** (on top of Quarto and the Draw.io desktop app):

```sh
python -m pip install -r scripts/requirements-ebook.txt   # Pillow, NumPy, PyYAML
python scripts/install_epubcheck.py                       # EPUBCheck, and Java if there is none, under outputs/tools/
```

EPUBCheck is the validator that distributors such as Draft2Digital run on an uploaded EPUB, so install it: the build then
runs it on every EPUB (nothing is installed on the system; deleting `outputs/tools/` removes it). Optional: Inkscape or
`rsvg-convert` (to render the SVG instead of the Draw.io source), and PyMuPDF (`python -m pip install pymupdf`) and Word
for the previews.

**Build.**

```sh
quarto render --to epub            # or --to docx: any PNG that is missing or out of date is made on the way (quietly)
python scripts/build_ebooks.py            # both formats: the PNGs with progress, the renders, the checks, a size report
python scripts/build_ebooks.py --epub     # one format (or --docx); add --force-figures to render every diagram again
python scripts/build_ebooks.py --baseline # also build the same text with SVG diagrams, and prove nothing else changed
python scripts/build_all.py               # the full local build does the same for both formats
python scripts/release.py publish         # publishes the optimized files like any other build
```

The files land in `_book/` and are copied to `outputs/build/downloads/book-latest.epub` and `.docx`, which the
release uses. `outputs/build/ebook-report.json` has the sizes, the number of figures, how many figures are palette
or RGB, and the checks.

**The cache.** `outputs/ebook-figures/` (untracked) holds `<name>.png` (the finished picture, shared by the EPUB and
the DOCX), `raw/<name>.png` (what the renderer drew) and `manifest.json`. A PNG is made again only when its Draw.io
source, the SVG's size or a render setting (renderer, width, background) changed, which is decided by a SHA-256
over them, so repeated builds reuse every figure. Changing only a palette setting reduces the cached renders again
in about a minute with no Draw.io. A cold cache takes about ten minutes for the whole book.

```sh
python scripts/figure_raster.py settings             # the settings in effect
python scripts/figure_raster.py ensure --all         # make what is missing or stale (--force renders everything again)
python scripts/figure_raster.py verify               # list PNGs that are missing or stale; renders nothing
python scripts/figure_raster.py prune [--raw]        # delete PNGs of figures that no longer exist (and the renders)
```

**Changing the look.** Edit `visuals/ebook-figures.yml`: `width` (pixels across; 1728 is about 190 pixels an inch on the
SVG's 9-inch page and about 296 on the 5.8-inch column Pandoc gives a Word picture), `palette.max-colors` and
`min-colors`, and the tolerances (the largest difference in any color channel, on a scale of 0 to 255: `tolerance` is the
target for 99.99% of the pixels, `mean-tolerance` and `max-tolerance` are limits). A lower tolerance picks larger
palettes and bigger files. `palette.enabled: false` keeps every figure an RGB PNG. To render from the SVG with Inkscape
instead of from the Draw.io source, set `renderer: inkscape` (or `AA_FIGURE_RENDERER=inkscape`); `INKSCAPE_BIN`,
`RSVG_CONVERT_BIN` and `DRAWIO_BIN` name an executable that is not on the path. Inkscape and rsvg-convert cannot draw the
HTML labels of the committed SVGs, so they need a copy that carries Draw.io's PNG of every label, made once with
`python scripts/export_drawio_svgs.py --svg-labels png-fallback --out-dir outputs/ebook-figures/svg --skip-pdf --skip-cover
--manifest outputs/ebook-figures/svg-manifest.json` (`figure_raster.py` reads that copy when it exists and otherwise says
that labels will come out cut short). They draw each label from that low-resolution image, so their PNGs are softer than
the Draw.io render.

**Checks.** `python scripts/ebook_validate.py --epub FILE --docx FILE [--baseline-epub OLD] [--baseline-docx OLD]`
reads the EPUB as a ZIP and as XML (the stored `mimetype` first, the package, manifest, spine, cover, every page, image
and internal link, no SVG left) and the DOCX the same way (every part, relationship and content type, each picture's
aspect ratio, the text column and its resolution), runs EPUBCheck (installed by `install_epubcheck.py`, or `epubcheck` on
the path, or `EPUBCHECK_JAR` with Java) and fails on any error it reports, and with a baseline build proves that only the
pictures changed. `filters/epub-markup.lua` keeps the EPUB valid where Quarto's own markup is not: Quarto copies each
figure's alt text onto the wrapping `<div>`, which HTML5 forbids, so every figure was an EPUBCheck error (RSC-005) and
Draft2Digital refused the file. `python scripts/ebook_preview.py word|epub|figures` draws pages for a
look: the DOCX through a hidden Word (this is also the check that Word opens it), the EPUB pages in headless Edge, and
sampled figures against their SVG. The checks that need no book build are in `tests/test_figure_raster.py`,
`tests/test_ebook_validate.py` and `tests/test_build_ebooks.py`.

**Troubleshooting.** The render stops with the figure's name when a conversion fails: Draw.io not found
(`DRAWIO_BIN`), Python not found by Quarto (`AA_PYTHON`), an aspect ratio that differs from the SVG's (an out-of-date
export: run `python scripts/export_drawio_svgs.py`), or a renderer timeout. To keep SVG diagrams in a build, for
example to compare, set `AA_EBOOK_FIGURES=svg`.

### Smaller SVG files

The 165 SVGs in `visuals/svg` were 101 MB, and 90% of that was one PNG per text label (9,238 labels, no other image in
any diagram). Draw.io writes each label as an HTML `foreignObject` and, for viewers that cannot draw it, a fallback. By
default the fallback is a PNG of the label at four times its size, which browsers never use and gzip cannot shrink (the
set was 67 MB gzipped). Since 2026-10-20 `scripts/export_drawio_svgs.py` asks Draw.io for its plain-text fallback
instead (`--embed-svg-fonts false`) and then removes the markup that no viewer needs (`scripts/svg_native.py`: the
`style` that repeats `fill` and `stroke`, the `pointer-events` of shapes, an empty `<defs/>` and the DOCTYPE). The SVGs
are now about 9.6 MB, 0.54 MB gzipped, and Edge, Chrome and Firefox draw exactly the same pixels as before (0 differing
pixels in all 165 diagrams in Edge, and in 11 test diagrams in the other two). Nothing else changed: the `.drawio`
sources, the PDFs (`filters/pdf-figures.lua` swaps every SVG for its vector PDF) and the EPUB and DOCX PNGs.

```sh
python scripts/export_drawio_svgs.py                       # the plain-text fallback (default)
python scripts/export_drawio_svgs.py --svg-labels png-fallback --out-dir outputs/ebook-figures/svg --skip-pdf --skip-cover     --manifest outputs/ebook-figures/svg-manifest.json     # a copy with the PNGs, for rsvg-convert and Inkscape only
python scripts/figures/check_figures.py --exports          # also fails on a PNG fallback or an SVG over 400 KB
```

The label mode is part of each SVG's entry in `visuals/export-manifest.json`, so changing it makes only the SVGs stale. In
a viewer that cannot draw HTML labels (`rsvg-convert`, Inkscape, MuPDF) the fallback is complete text for 95% of the labels
(8,813 of 9,238) and the first line, in one weight, for the other 417. Nothing in the book's builds uses such a viewer
(`figure_raster.py` draws from the Draw.io source by default), and its `rsvg` and `inkscape` renderers read the copy with
the PNGs, as described above. Safari was not tested; it draws the HTML label as the other browsers do.

**What was measured, and what was not adopted.** `scripts/svg_lab.py` is the lab that compared the options, writing
only to `outputs/svg-lab/` (untracked). Its baseline is the SVGs with PNG labels (`baseline --rev <commit before
2026-10-20>`, or a new export with `--svg-labels png-fallback`).

```sh
python scripts/svg_lab.py baseline --rev COMMIT                          # v0, the files with a PNG of every label
python scripts/svg_lab.py audit                                          # what is in the SVGs; picks the test diagrams
python scripts/svg_lab.py build --variants v1 v2 v3 --set representative # or --set all (about 16 minutes)
python scripts/svg_lab.py compare --set all --engines edge chrome firefox  # outputs/svg-lab/report.md
python scripts/svg_lab.py determinism --set representative
```

| variant | what it does | all 165 diagrams |
|---|---|---|
| v1 | strips the markup and keeps the PNGs | 100.4 MB (-0.9%) |
| **v2** | **the plain-text fallback and the stripping: this is the exporter now** | **9.6 MB (-90.6%), 0.54 MB gzipped** |
| v3 | v2, and every label that fits on one line becomes native `<text>` (Draw.io's "Convert labels to SVG", the style `convertToSvg=1`, switched on in a temporary copy of the source) | 4.0 MB (-96.0%), 0.41 MB gzipped |

v2's output is byte for byte the same on a second export. v3 keeps every cell's characters, weight, slant and color, but
its text sits 0.5 to 1.0 pixel lower in Chromium, bold text is a little lighter, one diagram's drawing is a pixel shorter,
and only 94.5% of the labels can be converted: Draw.io's conversion does not wrap text, does not read `<br>`, and drops a
label's background (an edge label would show the line through it), so `svg_native.single_line_cells` converts only labels
it measures with Arial to fit on one line (checked against the heights of the old PNG fallbacks: no label that wraps was
ever taken for one line). It saves 5 MB more than v2 (0.13 MB gzipped), so it was not adopted. `native_labels_copy` is in
`svg_native.py` if vector text outside browsers ever matters.

## Chapter slides

`slides/` is a separate Quarto project. Each chapter's deck, `slides/chapter-NN/index.qmd`,
renders to both Reveal.js and PowerPoint. A deck is published as soon as it exists, like a
chapter; there is no approval step, and editing a chapter never blocks the build. Use
Python 3.13, Quarto 1.10.19, and Draw.io 29.6.6, with the usual book dependencies above,
then install the pinned Python package:

```sh
python -m pip install -r scripts/slides/requirements.txt
python scripts/build_all.py --check
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/build_all.py --slides-only --chapter chapter-01
python scripts/build_all.py --preview chapter-01
python scripts/build_all.py
```

A deck cites the book's own figures and tables by ID (`{{< book-figure fig-01-02 >}}`,
`{{< book-table tbl-01-02 >}}`), so its title, figures, captions, alt text and tables always
match the chapter. `slides/README.md` describes the deck standard every chapter follows, the
slide patterns, the shortcodes, and how to start a deck. `--check` needs neither Quarto nor
the dataset: it fails only if a deck cites something the book lacks, a slide has no notes,
or a deck names the author.

The full build (local) stages the PDF, EPUB, and DOCX in `outputs/build/downloads/`,
renders both presentation formats separately (the PowerPoint files stay in
`slides/_build/pptx/`), renders book HTML last, then assembles `_book/`, which
holds the Reveal decks but not the PowerPoint files or the book downloads: those
are published on the revision's release (see Building the book). It exports
Draw.io SVGs, vector PDFs, and the cover once before the book renders;
all four book formats reuse those files, and the slides export a PNG of each figure
they cite for PowerPoint. `visuals/export-manifest.json` records
source/output checksums and export settings so that a fresh checkout can tell which
figures are current despite unreliable checkout timestamps; the site build on GitHub
Actions has no Draw.io and fails when an export is out of date. Commit that manifest
with changed sources and exports. Missing or changed outputs, changed sources, and changed
settings trigger an export; `python scripts/export_drawio_svgs.py --force` rebuilds
everything. Existing local exports without manifest entries are adopted once when
their timestamps are current and default settings are used; CI never trusts those
timestamps. Standalone
`quarto render` commands continue to export through the pre-render hook.
Pull requests build the site and check the release without deploying.

Edit the slide palette and type in `slides/theme/tokens.yml`, the Reveal design in
`slides/theme/reveal.scss`, and the PowerPoint template in `scripts/slides/pptx_theme.py`.
Do not edit the generated `slides/_shared/`, `slides/_variables.yml`, the decks'
`_metadata.yml`, or `slides/_build/`. Every slide has notes for the speaker; assessment
solutions do not belong in a deck or its notes.

## License

Contributions to the book are shared under the same
[CC BY-SA 4.0 license](LICENSE) as the existing material. Give appropriate credit
for material you adapt, link to its license, and indicate any changes. Only
include material you have the right to share under these terms.
