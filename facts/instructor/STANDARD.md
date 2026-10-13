# Instructor guides: the standard

Every chapter, comprehensive case and exercise-bearing appendix gets a folder with a **chapter (or case) note** and **one file per exercise or requirement**. This file is the standard every file is written to. `python facts/instructor/guides.py check --unit U` enforces the parts a machine can check.

## How the files are made

- **Source:** `facts/instructor/guides/<unit folder>/<file>.md`, a Markdown template with a YAML front matter and a Jinja body. This is the only place anyone edits.
- **Output:** `python facts/instructor/guides.py render --unit U` writes the filled-in Markdown to `instructor-notes/<unit folder>/`. That folder is what ships (Instructor-Notes.zip). Never edit it by hand.
- **Values:** every number that comes from the dataset (amounts, counts, percentages, IDs, dates, years) is a template value, never typed. The engine is the one the generated notes use (`facts/notes/`): the filters `money`, `num(places)`, `pct(places)`, `spct`, `count`, the window `d.F`, `d.P`, `d.C`, `d.N`, and an undefined name is an error.
- **Contexts:** the front matter key `note: ch06.ex1` loads the values of that registered note (`facts/notes/ch06.py`; list them with `guides.py context ch06.ex1`). `uses: [ch06.t3]` adds another context under the name `ch06_t3` (`{{ ch06_t3.margin|money }}`). A value no note supplies goes in a guide context, `facts/instructor/guide_contexts/<unit>.py`, with `@context("ch01.ex2")`, written like a note's context function (a function `(d, claim)` that queries read-only and returns a dict). Add a key to an existing note's context function only additively, then run `python facts/instructor/render.py` (it must still report 0 problems).
- **Claims:** a statement the guide makes about the data that a different dataset could falsify ("no payment is above its invoice", "the largest group is Furniture") goes through `claim(condition, text)` in the context, so a roll flags it.
- **Code fences are literal.** Braces inside a fenced block (DAX, M, SQL) are protected from Jinja. A fence whose info string ends in the word `jinja` (for example ```` ```sql jinja ````) is rendered, so a value can sit inside it. Inline braces outside code need `{% raw %}{{ ... }}{% endraw %}`; inline code spans are not protected, so avoid `{{` there.
- **Macros** available in a template: `{{ header() }}` (the header table, from the front matter, required once under the title), `{{ figure('IF-06-1-A') }}`, `{{ expected() }}` (the unit's existing generated instructor note for this item, as a quoted block, when the front matter has `note:`), `{{ mcq_key() }}` (the multiple-choice key with its rationales, chapter notes only).

## Front matter

Items (exercise or requirement):

```yaml
---
note: ch06.ex1             # optional: the registered note or guide context that supplies values
uses: []                   # optional: more contexts
title: From the Ledger to the Income Statement
kind: exercise             # exercise | requirement
number: '6.1'              # exercise number, or the requirement number
unit: '6'
perspective: financial     # financial | managerial | auditing | general
tool: excel                # conceptual | excel | sql | powerbi | mixed
minutes: 90                # the time a student needs, as a positive integer
solution: "Chapter06-exercises.zip: Chapter 6 Exercises - Solutions.xlsx, sheet Ex 6.1"   # empty only for tool: conceptual
figures: []                # see Figure placeholders
---
```

Chapter or case notes carry `title`, `kind` (`chapter-notes` or `case-notes`), `unit`, `minutes` (class time for the whole unit, optional), `tool`, `figures`, and optionally `note`/`uses`. The scaffold writes all of it; fill in `tool`, `minutes`, `solution` and `figures`.

## Voice and rules for every file

- **Audience:** the instructor who teaches this unit. Write to "you" for the instructor and "students" for the class. Be concrete and practical: say what to do, in what order, in how many minutes.
- **Neutral language for people:** name roles (the controller, the staff accountant, the Production Manager) and use they/them or the role; never he, she, him or her.
- **No new claims about the data:** state a data condition only through a context value or a claim. In prose, say "several hundred", "a handful", or "see the Expected results"; put the number in a value.
- **No outside claims:** no education research, statistics or citations beyond what the book already cites. Teaching advice is advice, not evidence.
- **Style:** the book's rules: no "namely" before a list; "&" is not used in prose; spell out "for example"; keep sentences short; no filler openers.
- **Public and complete:** the notes are public with the solutions. A step-by-step solution may show the answer; frame it as the model path ("compare your work with this path").
- **Part V independence:** Chapters 17-19 are independent final-project options. A note for one must not mention another capstone; it may mention earlier chapters and the Part I-IV cases as context or an optional head start.
- **Do not edit the book.** If a requirement, a tutorial or a note disagrees with the data or with the solution file, finish the guide on what the solution file and the data show, and report the mismatch in your final message (file, line, what differs).
- **Do not run Excel or Power BI Desktop** (no COM, no UI automation), and never write to `datasets/`. SQL is read-only (`mode=ro`).

## Chapter or case note

Required `##` headings, in this order (the check enforces them). A chapter with tutorials and questions uses the first list; a case, and a chapter made of requirements (Chapters 17-19), the second.

Chapter: At a glance; What students should be able to do afterward; Preparing to teach; Teaching approaches; Tutorial guide; Difficult ideas and misconceptions; Discussion prompts; Using the exercises; Multiple-choice questions; Connections.

Case: At a glance; What students should be able to do afterward; Preparing to teach; Teaching approaches; (Milestone guide, when the case has milestones); Difficult ideas and misconceptions; Discussion prompts; Using the requirements; Assessment rubric; Connections.

What goes in each (target 2,200-3,500 words in all, hard maximum 4,600 counting the generated multiple-choice table):

- **At a glance:** a short table or list: the Part, the analytics types the unit names, the tools, the number of tutorials, exercises and questions, the files students need (by name, from the Downloads page), a realistic total of class and student hours, and the data conditions the unit depends on, qualitatively (take them from `facts/baseline-2026.md`).
- **What students should be able to do afterward:** 4-6 observable outcomes, each tied to the exercise or requirement that practices it. Where Appendix D maps the item to a framework competency, name it in the item's file, not here.
- **Preparing to teach:** the setup an instructor must check beforehand (software and versions, the working copy of the workbook or database, the start file for each tutorial, the Downloads items), what to do the week before, and the pitfalls that cost class time.
- **Teaching approaches:** two or three complete plans, each with a session-by-session or minute-by-minute outline and when it fits (for example a lecture with a live demonstration, a lab-first session, a case-first session, a flipped plan with the tutorials as homework). Use the unit's slide deck (`slides/chapter-NN/index.qmd`) and its talk-track notes as the source of a lecture plan, and say which slides carry which part. Give the trade-offs honestly.
- **Tutorial guide** (chapters with tutorials): a `### Guided Tutorial N.k: Title` subsection for each tutorial: its purpose, what to demonstrate live and what to leave to students, minutes, the stumbles students hit (from the tutorial's own Watch outs and from the builders' pitfalls), and the checkpoint to look for (a value through a context when the tutorial has a note, otherwise point to the tutorial's own checkpoint).
- **Milestone guide** (cases with milestones): a `### Milestone N: Title` subsection for each milestone: what a student should hold at that point and how to check it quickly.
- **Difficult ideas and misconceptions:** the concepts students get wrong, each with how it shows up (a wrong exercise answer, a tempting multiple-choice distractor) and how to respond. Ground them in the chapter's text, the exercises and the question rationales.
- **Discussion prompts:** 5-8 open questions for class, each with a line on what a good discussion reaches.
- **Using the exercises / requirements:** a table with the item, perspective, tool, time, difficulty (basic, intermediate, advanced) and outcome, then two or three suggested assignment bundles (for example by perspective for a three-track course, or a one-exercise-per-session plan), and which items suit grading and which suit in-class discussion.
- **Multiple-choice questions** (chapters with questions): `{{ mcq_key() }}`, then a short discussion of the questions where a wrong option is tempting and why, and how to use the questions (quiz, clicker, review).
- **Assessment rubric** (cases): the weights across requirements and the common criteria (accuracy, evidence, judgment, communication), consistent with the requirement files' grading guides.
- **Connections:** what the unit builds on and what builds on it (chapters, cases, appendices), by name and number.

## Exercise or requirement file

Required `##` headings, in this order. Target 900-1,700 words (hard maximum 2,700), at the top of the range only for a long, multi-part requirement. Be dense: no restating the exercise, no repeating a value in prose that the Expected results table holds.

1. **Purpose and learning outcomes:** what the item is for in the unit's argument, the outcomes, the competency it practices (name and code from Appendix D, in your own words), and the analytics type it exercises.
2. **Before you assign:** the files and software, what students need from earlier tutorials or items, data conditions the item relies on (qualitatively; name the table and column), and anything an instructor should verify first.
3. **How to run it:** individual, pairs or in class; a time budget by phase; the hints to hold back and when to give each; what to collect.
4. **Step-by-step solution:** one `###` subsection per numbered requirement of an exercise, headed exactly `### Requirement (N): ...` (the scaffold writes them), and for a case requirement one subsection per bullet or phase. Each step says what to do, in order, with the exact labels, then what you should see and why it matters. See "Writing the steps".
5. **Expected results:** the values a correct answer reports, as a table with the quantity, the value (a template value), and where it appears (the step). Finish with `{{ expected() }}` when the item has a generated note, so the complete instructor note rides along. Values must come from the context.
6. **What a strong answer says:** for each written or judgment requirement, the points a strong answer makes and the evidence it cites, as a model-answer outline (not a full essay), and what separates a strong answer from a weak one.
7. **Common mistakes and how to respond:** 4-8 mistakes, each with the symptom you will see in the work, the cause, and the one-sentence response that moves the student forward.
8. **Grading guide:** a table of criteria with points that add to 100, a short descriptor of full credit and of partial credit for each, keyed to the requirements.
9. **Extensions and discussion questions:** 2-4 extensions for strong students and 2-3 discussion questions that connect the item to the next chapter, the case, or practice.

### Writing the steps

Every step: a short imperative title in bold (**Step 3. Group by account.**), the actions (a lettered list when there are three or more), then a line that starts **Check:** and says what you should see, with a value where one exists. A step that students commonly get wrong gets a **Watch for:** line. Do not restate the exercise; refer to its requirement numbers.

- **Labels:** bold for what you click or choose (ribbon commands and menu paths such as **Data > Get Data**, buttons, tabs, panes, dialog names, worksheet and query names); column names plain; typed text, formulas, queries and DAX in code; keyboard shortcuts as text (Ctrl+T). Use only labels the book's own tutorials or `CLAUDE.md` give as verified. If a step needs a label you cannot confirm, write the action in general terms ("open the query's context menu and choose to load it only as a connection") and list it in your report as unverified.
- **Excel:** the model answer is in the Solution Notes worksheet and the `Ex N.M` worksheet of the solution workbook (read it with openpyxl in read-only mode from a copy in your scratch folder) and in `scripts/companion/xlbuild/exNN.py`, which builds it step by step. A formula longer than about 50 characters goes in its own fenced block. Name the worksheet and the cells or Table columns the way the solution does.
- **SQL:** quote each query verbatim from the solution script (`Ex N.M.sql`, `Case.sql` and the like in `outputs/companion/solutions/`), including its comment lines; the check confirms it. After a query, say how to read the result and what the row count means (a value through a context, or the script's own `-- Result:` comment is not enough on its own because the number can roll). A query is a fenced ```` ```sql ```` block.
- **Power BI:** the model answer is in the solution project's Notes page and its TMDL and PBIR files (`outputs/companion/solutions/ChapterNN-exercises-pbi/...`) and in `scripts/companion/pbibuild/exNN.py`. Give Desktop steps by pane and label, measures in fenced DAX blocks quoted from the project, and the page and visual that shows the result. For an exercise that is DAX only, show the measure, then a DAX query view test that returns the check value.
- **Conceptual (Chapters 1-3 and Part I):** a step is a reasoning move ("Name the business event that creates a row", "State the join path"): give the move, the evidence to look at (worksheet, column), the model conclusion in one or two sentences, and what to check. The memo requirement gets an outline of the memo, not the memo.
- **Mixed tools (Part V and some cases):** a subsection per tool where the requirement says which fits, and the reason the tool fits.

## Figure placeholders

Declare each figure once in the front matter and place it with `{{ figure('IF-06-1-A') }}` where it belongs. The build shows a placeholder block until `instructor-notes/figures/<unit folder>/IF-06-1-A.png` exists, then the image, so the figure phase edits no guide.

```yaml
figures:
  - id: IF-06-1-A            # IF-<unit>-<item>-<letter>; unit 06, C1, AB; item 0 for the chapter note
    kind: excel-mock         # excel-mock | sql-mock | pbi-mock | diagram | chart
    purpose: The TrialBalance table after Step 4, with the Total Row on.
    shows: The Table with Debit, Credit, Balance, DebitBalance and CreditBalance columns and the Total Row, scrolled to the totals.
    data: The pre-closing trial balance at the end of the current fiscal year, from GLEntry and Account (the Expected results query).
```

- **When:** only where a picture adds what the words cannot: an exercise's expected end state (the worksheet, the query result, the model or the report page), a step where students typically stumble, or a chapter-level diagram (a decision tree, a process map, a session timeline). At most 3 per item and 4 per chapter note. Many items need none.
- **What:** a mock that a generator can draw from the dataset: Excel (`excel-mock`: worksheet grid, Table, PivotTable, Power Query steps, dialog), DB Browser for SQLite (`sql-mock`: editor with the query and the result grid), Power BI Desktop (`pbi-mock`: report page, Model view, DAX query view), a `diagram` (flow, decision tree, ER, bridge) or a `chart`. Say in `shows` what is on screen in enough detail to draw it (columns, rows, selections, highlighted cells, the visible numbers by name), and in `data` where its values come from. Never put a value in the front matter; name the quantity.
- **Design:** the figures will follow the book's figure standard (`CLAUDE.md`, Figures): Helvetica, the palette, nothing below 12 px, meaning never by color alone, real Charles River values only. Do not write a caption that repeats a figure's numbers.

## Teaching content that is checked by hand

- **Plans add up:** a plan's minutes sum to its stated total.
- **Every outcome is practiced:** each outcome in the chapter note maps to at least one exercise or requirement.
- **Grading guides add to 100** and match the requirements.
- **Tutorial guide:** one subsection for each tutorial of the unit, in order.
- **Consistency across the unit:** the same difficulty labels, the same perspective names, the same file names as the Downloads page.

## Finishing a unit

1. `python facts/instructor/guides.py render --unit U`, then `check --unit U`, until both are clean. Read every rendered file once in `instructor-notes/<unit folder>/`.
2. `python facts/instructor/guides.py figures` to refresh the figure inventory.
3. If you added a context key to a note module, `python facts/instructor/render.py` must report 0 problems.
4. Report: the files written, the figure placeholders (id, kind), context functions added, claims that fail, and every mismatch between the book, the solution files and the data. Do not commit.
