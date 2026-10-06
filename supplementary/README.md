# Supplementary files

Start files for the guided tutorials (`start-files/`) and solutions to the exercises, the comprehensive cases, and the capstone cases (`solutions/`) of *Accounting Analytics: An Integrated Approach* (2026 edition), built from Charles River dataset release v2026.1 (fiscal 2024–2026). Everything is public, like the rest of the book. The site serves this folder at `/supplementary/`, and the book's [Downloads](https://aa.accountinganalyticshub.com/front-matter/downloads.html#sec-companion-files) page lists the files by chapter and explains how to use them.

## Start and end files of the tutorials (`start-files/`)

A start file holds the work as it stands at the end of the previous tutorial, so it also lets you check your own work. Each chapter's download holds the file at the start of each tutorial that continues it and at the end of the chapter.

| File | Contents |
|---|---|
| Chapter04-companion.zip | Charles River Furniture Analysis.xlsx at the start of Tutorials 4.2 and 4.3, and at the end of Chapter 4 |
| Chapter05-companion.zip | The same workbook at the start of Tutorials 5.1, 5.2, and 5.3, and at the end of Chapter 5 |
| Chapter06-companion.zip | The same workbook at the start of Tutorials 6.1, 6.2, and 6.3, and at the end of Chapter 6 |
| Chapter07-companion.zip | The same workbook at the start of Tutorials 7.1, 7.2, and 7.3, and at the end of Chapter 7 |
| Chapter08-companion.zip | AuditAnalytics.xlsx at the start of Tutorials 8.2 and 8.3, and at the end of Chapter 8 |
| Chapter09-companion.zip | Chapter09.sql at the start of Tutorials 9.2 and 9.3, and at the end of Chapter 9 |
| Chapter10-companion.zip | Chapter10.sql at the start of Tutorials 10.2 and 10.3, and at the end of Chapter 10 |
| Chapter11-companion.zip | Chapter11.sql at the start of Tutorials 11.2 and 11.3, and at the end of Chapter 11, with Setup_Part3_Views.sql |
| Chapter12-companion.zip | Audit.sql at the start of Tutorials 12.2 and 12.3, and at the end of Chapter 12 |
| Setup_Part3_Views.sql | Recreates the view MonthlyLaborEfficiency of Tutorial 11.3 in a working copy, for the Part III case |
| Chapter13-companion.zip | Charles River Reports (a Power BI project) at the start of Tutorials 13.2 and 13.3, and at the end of Chapter 13 |
| Chapter14-companion.zip | The same project at the start of Tutorials 14.1, 14.2, and 14.3, and at the end of Chapter 14 |
| Chapter15-companion.zip | The same project at the start of Tutorials 15.1, 15.2, and 15.3, and at the end of Chapter 15 |
| Chapter16-companion.zip | Audit Monitoring at the start of Tutorials 16.2 and 16.3 (with Charles River Reports at the end of Chapter 15) and at the end of Chapter 16 |
| AppendixA-companion.zip | Charles River Reports and Audit Monitoring at the start of Guided Tutorial A.1, and Charles River Reports at the start of A.2 |

## Solutions (`solutions/`)

Try the work first, then compare it with the solution. Every file explains itself. An Excel workbook has a Solution Notes worksheet that lists the exercises or requirements with their instructor notes and checks each result against the dataset after a refresh. A Power BI project has a Notes page with the same sections and a Checks query in DAX query view that tests every value. A SQL script opens with the book's header comment, gives each query's result on this dataset release, and ends with a notes block that repeats the requirements and instructor notes and lists the values checked.

| File | Contents |
|---|---|
| Chapter04-exercises.zip | Chapter 4 Exercises - Solutions.xlsx |
| Chapter05-exercises.zip | Chapter 5 Exercises - Solutions.xlsx |
| Chapter06-exercises.zip | Chapter 6 Exercises - Solutions.xlsx |
| Chapter07-exercises.zip | Chapter 7 Exercises - Solutions.xlsx |
| Chapter08-exercises.zip | Chapter 8 Exercises - Solutions.xlsx |
| PartII-case.zip | Charles River Promotion Case.xlsx, the Part II case |
| Chapter09-exercises-sql.zip | Ex 09.1.sql to Ex 09.6.sql, one script for each exercise |
| Chapter10-exercises-sql.zip | Ex 10.1.sql to Ex 10.6.sql, one script for each exercise |
| Chapter11-exercises-sql.zip | Ex 11.1.sql to Ex 11.6.sql, one script for each exercise |
| Chapter12-exercises-sql.zip | Ex 12.1.sql to Ex 12.6.sql, one script for each exercise |
| PartIII-case-sql.zip | Case.sql, the Part III case |
| Chapter13-exercises-pbi.zip | Chapter 13 Exercises - Solutions, a Power BI project |
| Chapter14-exercises-pbi.zip | Chapter 14 Exercises - Solutions, a Power BI project |
| Chapter15-exercises-pbi.zip | Chapter 15 Exercises - Solutions, a Power BI project |
| Chapter16-exercises-pbi.zip | Chapter 16 Exercises - Solutions, a Power BI project |
| AppendixA-exercises-pbi.zip | The exercises of the appendix on publishing and security |
| PartIV-case.zip | Charles River Cash Case, the Part IV case |
| Chapter17-capstone-excel.zip | Charles River Lender Package.xlsx, the Excel part of the Chapter 17 capstone |
| Chapter17-capstone-pbi.zip | Charles River Lender Review, the Power BI part (reads Charles River Lender Package.xlsx from C:\CharlesRiver) |
| Chapter17-capstone-sql.zip | LenderPackage.sql, the SQL part of the Chapter 17 capstone |
| Chapter18-capstone-excel.zip | Make Buy Reprice.xlsx, the Excel part of the Chapter 18 capstone |
| Chapter18-capstone-pbi.zip | Product Costs, the Power BI part (reads Make Buy Reprice.xlsx from C:\CharlesRiver) |
| Chapter18-capstone-sql.zip | MakeBuy.sql, the SQL part of the Chapter 18 capstone |
| Chapter19-capstone-excel.zip | Credits Audit.xlsx, the Excel part of the Chapter 19 capstone |
| Chapter19-capstone-pbi.zip | Credits Analytics, with RefundFlags.csv (put it in C:\CharlesRiver) |
| Chapter19-capstone-pbi-monitoring.zip | Audit Monitoring updated with the credits cycle's continuing tests |
| Chapter19-capstone-sql.zip | Credits.sql, the SQL part of the Chapter 19 capstone |
| Instructor-Notes.zip | The instructor notes, the tutorials' expected values, and the multiple-choice answer keys of every chapter, case, and appendix, as Markdown and Word files |

Every file reads CharlesRiver.xlsx from C:\CharlesRiver (or point it at your copy with Change Source: Data > Get Data > Data Source Settings in Excel, Home > Transform data > Data source settings in Power BI Desktop). The Power BI projects hold no data until you refresh them, and the capstone projects read the solution workbook of the same capstone from the same folder.

## Updating the files

The files are built into `outputs/companion/` (gitignored) and copied here, so that a push publishes them with the site.

1. Build the files into `outputs/companion/start-files/` and `outputs/companion/solutions/`: `python scripts/companion/build.py --tool sql [--solutions]`, then the Excel files in the venv of `scripts/companion/requirements-excel.txt` (`--tool excel [--solutions]`, about an hour, one build at a time), then `--tool pbi [--solutions]` (Power BI Desktop opens and closes by itself for each file), then `python facts/instructor/package.py` for Instructor-Notes.zip.
2. Run `python scripts/companion/build.py --publish`. It copies every built zip and script whose bytes changed into this folder, removes files that are no longer built, and stops unless the folder matches the links of the Downloads page (`front-matter/downloads.qmd`).
3. Review `git status`. An Excel rebuild changes every workbook's bytes even when its content is the same, and every committed copy stays in the repository's history, so stage only the files you meant to change.
4. Commit and push: `publish.yml` renders the book, and Quarto copies this folder into the site (`project.resources` in `_quarto.yml`).

A file is replaced within an edition only to correct it. A new edition replaces the files in place; the previous edition's files stay in the history of its last commit.
