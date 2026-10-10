# Accounting Analytics: An Integrated Approach

**Mauricio Codesso**

Welcome to the repository for *Accounting Analytics: An Integrated Approach*, an
open educational resource. The book helps accounting students develop analytical
skills through accounting examples and applications using Excel, SQL, and Power BI.

**[Read the book online](https://aa.accountinganalyticshub.com/)**

The book website is the starting point for reading the chapters and finding
available book downloads and the companion dataset.

<p align="center">
  <a href="https://aa.accountinganalyticshub.com/">
    <img src="visuals/cover/cover-web.png" alt="Cover of Accounting Analytics: An Integrated Approach by Mauricio Codesso" width="240">
  </a>
</p>

## For accounting educators

Designed for undergraduate and graduate accounting courses, the book introduces
analytics through familiar accounting questions. Students need no prior analytics
or programming experience; introductory financial and managerial accounting
knowledge provides the foundation.

The teaching approach combines learning objectives, guided tutorials, and applied
exercises. Examples connect analytical skills to financial accounting, managerial
accounting, and auditing, helping students interpret results from different
professional perspectives.

The shared Charles River Accounting Dataset follows a fictional company and
provides a common setting for learning across Excel, SQL, and Power BI. Instructors
can use the material to support classroom discussion, guided practice, and
independent assignments.

Visit the [Charles River dataset website](https://charlesriver.accountinganalyticshub.com/)
for documentation and additional information. All dataset changes and updates
will be posted there.

**The book is under development.** Chapters and supporting materials are being
added and refined. Please review the available content when planning your course.

## Contributing to the book

Faculty, students, and practitioners are welcome to help improve the book.
Contributions can include:

- Corrections to the text, examples, or exercises.
- Suggestions for clearer explanations or new accounting applications.
- Classroom experiences and ideas for teaching with the material.

**No coding experience is required to share feedback.**
[Report an error or suggest an improvement](https://github.com/mmcodesso/Accounting_Analytics_Book/issues)
through GitHub. You will need a GitHub account. Identify the chapter or section
and describe your suggestion; a proposed correction or example is helpful.

To propose direct edits, see the [contributor guide](CONTRIBUTING.md).

## Building and publishing the book

GitHub Pages serves the website, and GitHub Actions renders it on every push to
`main`: the chapters in HTML and the slides for the browser. Everything readers
download is built on your own computer and published as the files of the book's
current revision, a GitHub release of this repository: the PDF, EPUB, and DOCX,
the PowerPoint decks, and the companion and solution files. **So after every
change to the book, build it locally and publish it.**

Install once:

- [Quarto](https://quarto.org/) 1.10.19, a TeX distribution for the PDF (such as
  MiKTeX), and the [Draw.io desktop app](https://www.drawio.com/) for the figures;
- Python, then `python -m pip install -r scripts/slides/requirements.txt`;
- the [GitHub CLI](https://cli.github.com/), signed in: `winget install --id GitHub.cli`,
  then `gh auth login`.

Then, for every change:

1. Commit your changes on `main`.
2. Run `python scripts/release.py publish`. It builds what is out of date (the
   PDF, EPUB, and DOCX, or only the decks whose sources changed; never the website,
   which GitHub Actions renders), uploads only the files that changed to the
   release of the current revision, and pushes `main`, which deploys the website.
   Add `--dry-run` to see the plan without changing anything.

To preview the website locally as well, run the full build,
`python scripts/build_all.py`; `publish` then reuses its files if nothing changed
since.

`python scripts/release.py status` lists every file: whether it is built, whether
it was built from the current text, and whether the release has the same copy. A
plain `git push` also deploys the website but leaves the downloads as they were;
the workflow's summary then lists the files that are older than the text.

The revision is set in `_variables.yml` (`book.revision`). To start a new one, run
`python scripts/release.py bump <revision>` (for example `2027.2`), commit, and
publish: the new revision gets a tag and release of its own, and earlier revisions
keep theirs. The companion and solution files are built with
`scripts/companion/build.py` and kept, untracked, in `supplementary/` (see
[its README](supplementary/README.md)). The [contributor guide](CONTRIBUTING.md#building-the-book)
has the details.

## Citing the book

If you use this book in your teaching or research, please cite it as:

> Codesso, M. (2027). *Accounting analytics: An integrated approach*. Accounting Analytics Hub. https://aa.accountinganalyticshub.com/

## License and reuse

Unless otherwise noted, this work is licensed under
[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).

You may share and adapt the material, including for commercial use. Give
appropriate credit, link to the license, and indicate any changes. Distribute
adaptations under the same license, without adding restrictions that limit the
permissions it provides. See the [repository license](LICENSE) for details.
