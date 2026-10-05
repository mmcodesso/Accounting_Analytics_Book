# Chapter 1 storytelling implementation review

Status: **approved by the author on 5 October 2026**. Requested 5 October 2026.
The revised source has one opening, five recording-module dividers, and 41
teaching slides (47 total). The previous approved site and transfer bundles
remain the release baseline until the full inventory passes its release checks.

## Evidence boundaries

The 2026 exhibit uses Furniture invoice lines and item standard cost. Values
come from the original unrounded quarterly calculation. Q3 is 42.26%, Q4
40.78%, with about 1.48 percentage points of decline. No diagnostic cause is
supplied. Financial-statement gross profit needs separate reconciliation.

The navigation example is dated **5 March 2025**: GLEntry 126312, SalesInvoice
7947, line 10645, quantity 2, unit price $344.21, credit $688.42. Agreement
establishes one line-to-posting relationship, not the complete entry,
settlement, completeness, or appropriate revenue recognition. It does not
explain the separate 2026 decline.

## Disposition of all 39 original slides

| Original slide / ID | Disposition | Revised position |
|---|---|---|
| 1 title-slide | Keep minimal cover | 1 |
| 2 ch01-objectives | Rewrite to cover all five book outcomes; move after request | 4 |
| 3 ch01-module-question | Keep module divider | 2 |
| 4 ch01-controller | Add Charles River and staff-accountant context | 3 |
| 5 ch01-definition | Merge definition and accounting judgment | 11 |
| 6 ch01-accountant-contribution | Merge into definition and its notes | 11 |
| 7 ch01-margin-definition | Reorder calculation; show reconciliation qualification | 6 |
| 8 ch01-margin-table | Move after chart; use as verification task | 8 |
| 9 ch01-margin-chart | Keep authoritative chart; move before table | 7 |
| 10 ch01-first-conclusion | Respond to verification with generated change | 9 |
| 11 ch01-module-workflow | Keep divider | 10 |
| 12 ch01-four-types | Rewrite as question-classification task | 12 |
| 13 ch01-roles | Keep role comparison with choice prompt | 14 |
| 14 ch01-workflow | Keep focused Figure 1.2 and concrete check | 15 |
| 15 ch01-scope | Move before formula and results | 5 |
| 16 ch01-preparation | Concrete checks and consequences | 16 |
| 17 ch01-communication | Merge into controller-update task and model | 43–44 |
| 18 ch01-module-tools | Keep divider | 17 |
| 19 ch01-tools | Replace catalog with Figure 1.3 and choice task | 19 |
| 20 ch01-business | Keep fuller context; introductory context also on slide 3 | 18 |
| 21 ch01-operating-groups | Replace catalog with operating/core view | 21 |
| 22 ch01-shared-groups | Replace catalog with reference/planning view | 22 |
| 23 ch01-keys | Use real repeated-key matching task | 23 |
| 24 ch01-module-trace | Keep divider | 25 |
| 25 ch01-source-trace | Keep focused trace; visibly date 2025 example | 27 |
| 26 ch01-source-fields | Convert to matching task; add separate native response | 28–29 |
| 27 ch01-worked-calculation | Keep calculation response; add prior amount task | 30–31 |
| 28 ch01-trace-limit | Mark only checked revenue credit; state limits in notes | 32 |
| 29 ch01-module-tutorial | Keep divider | 33 |
| 30 ch01-tutorial-setup | Workbook map with observable output | 34 |
| 31 ch01-tutorial-customer | Full Customer inspection and order-1 lookup; add response | 35–36 |
| 32 ch01-tutorial-item-account | Split into Item and Account activities | 37–38 |
| 33 ch01-tutorial-ledger | Include both WorkOrder and PayrollRegister | 39 |
| 34 ch01-tutorial-checkpoint | Keep public questions and demonstrate lookup | 40 |
| 35 ch01-mistakes | Rewrite as misconception task; add response | 41–42 |
| 36 ch01-summary | Replace recap with authored controller update and model | 43–44 |
| 37 ch01-next | Preserve next tasks; link Figure 1.8 outside canvas | 45 |
| 38 ch01-references | Keep references and shared APA entries in notes | 46 |
| 39 ch01-credits | Keep attribution/license and public-note notice | 47 |

New IDs identify the analytics-type response (13), architecture overview (20),
key response (24), forward process (26), field response (29), amount task (30),
customer response (36), separate Item/Account tasks (37–38), misconception
response (42), controller task (43), and model response (44).

## Sources and implementation

Supplemental figure labels and meanings come from canonical Draw.io Figures
1.1, 1.3, 1.4, 1.5, and 3.5. Figure 1.4 keeps dashed posting links and solid
shared-key links. Figure 1.5's goods process has an explicit service-invoice
qualification in notes. Existing focused Figures 1.2, 1.6, and 1.7 remain.
The source-field, customer, repeated-key, and account views use native tables.
Worksheet illustrations are labeled mocks. SVG and high-resolution PNG views
share generating inputs. No global refresh renderer was modified.

Repeated-key records use Chapter 3's authoritative orders 62/85 to customer 1
and order 59 to customer 4. Tutorial 1.1 separately uses order 1 to customer 81,
Koch-Ali. AccountID 42 uses account number 4010 and parent AccountID 41, whose
account number is 4000. Explicit refresh reads only the pinned dataset.

The build wrapper supports selected-chapter checks, slide builds, and preview.
It rejects selection for publication/export. Isolated render staging protects
other chapter outputs, and selected reports cannot overwrite release reports.

## Acceptance record

Validation completed on 5 October 2026. The detailed results are recorded in
`outputs/build/chapter-01/validation-summary.json`, with chapter-specific source,
browser, PowerPoint, and public-reproduction reports in the same directory.

- Both formats contain 47 slides, including five module dividers and 41 teaching
  slides. Artifact checks passed for notes, resources, hyperlinks, alt text,
  embedded media, and native text/tables. All 62 slide-build tests passed.
- All 47 Reveal slides and 30 intermediate fragment states were inspected.
  Desktop and narrow-screen bounds, keyboard navigation, and speaker view
  passed, with no missing resources. The margin qualification stays visible
  from arrival throughout the explanation steps.
- All 47 native PowerPoint slide exports were inspected. There were no overflow
  flags; editable text and 24-point native table cells were verified by editing,
  saving, and reopening a copy. Interactive slide-show appearance, reading order,
  screen-reader behavior, and Linux font substitution remain unverified.
- Both formats reproduced from 138 sanitized public input files without datasets
  or instructor tooling. PowerPoint slide, note, and media parts matched the
  authoring render. Raw public-source checks passed.
- Checksums for 41 preservation-baseline files were unchanged, including both
  datasets, other chapter outputs, the original shared renderer, and the previous
  approved transfer bundles.

The author approved the finished revision in this chat: “Great. I aprove this
version”. Chapter 1 is approved in the manifest, with hashes identifying the
accepted source, generated facts, Reveal output, and PowerPoint output. On
5 October 2026, the Chapter 18 source change was reviewed against the previous
sanitized public export. Its public text is identical; the change affects only
a private comment. The reviewed source hash was updated without changing the
Chapter 18 teaching deck. Full source checks now pass, and the author has
authorized publication of the approved Chapter 1 revision.

## Requested finishing adjustments

The author liked the revised slides and requested cover, attribution, and
architecture-overview adjustments before continuing. The cover now presents
*Accounting Analytics: An Integrated Approach* and the Chapter 1 title, without
a presenter name. The closing reference uses the requested surname-only author
form, Codesso, with the edition year and italicized book title.

The architecture overview now uses equal-height rows, vertically centered labels,
and connectors anchored at each box's center. Both sides share the same row
positions, and the Accounting Core is centered between them. The original
dashed-posting and solid-shared-key meanings remain unchanged. The supplemental
generator regenerated SVG/PNG counterparts and their provenance.

Fresh Reveal and native PowerPoint renders passed their artifact and bounds
checks. Slides 1, 20, 46, and 47 were visually rechecked in both formats; all
62 existing tests passed, and dataset-free reproduction was repeated. The
datasets, other chapter outputs, and prior approved bundles remain unchanged.

## Deferred accuracy priority

Chapter 13 remains unchanged. Its next review must distinguish original Excel
table names (T4_Customer, T16_SalesInvoice, T17_SalesInvoiceLine, T44_Item) from
renamed queries. Align slide tasks with Tutorial 13.1's model/validation work,
Tutorial 13.2's Sales and Discounts page, and Tutorial 13.3's Review page and
three misleading-chart corrections. Correctly resolving links alone does not
verify that the linked activity matches the task.
