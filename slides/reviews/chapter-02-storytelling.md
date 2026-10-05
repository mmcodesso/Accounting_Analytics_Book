# Chapter 2 storytelling implementation review

Status: **pilot; fresh-render acceptance pending**. Requested 5 October 2026.
One cover, four recording-module dividers, and 45 content slides: **50 total**.
The previous approved publication and transfer bundles remain the baseline.
Revised slides are not authorized for release until their fresh renders are accepted.

## Story and evidence boundaries

New internal auditors assess operational and ledger readiness for **fiscal
2024–2026**, then report tested evidence, limits, unresolved questions, and next
actions to the supervisor. This is a data assessment, not an audit opinion.
The six teaching stages guide all four modules without requiring six slides.
All six book objectives are grouped into meaning/sources, quality/tests, and
structure/traceability; every activity specifies an observable output.

The extract extends to **23 February 2027**, with **526 DisbursementPayment
posting rows** in fiscal 2027, not 526 distinct payments. Later settlements may
support earlier-year questions without entering earlier-year activity totals.
The displayed **$731,949,908.31** debit and credit totals include that tail;
their **$0.00** difference is an arithmetic check over the whole extract.

The date example is invoice SI-2024-000001, order 41: 1 January 2024 precedes
earliest shipment 3 January 2024. The prompt omits its flag; the next slide shows
**Check**. MINIFS uses shipment dates D:D, order IDs C:C, and invoice order key
E2. IF retains the zero-helper guard. No-match and valid service contexts need
interpretation; an OK flag does not validate recognition.

The separate **5 March 2025** trace uses GLEntry 126312, AccountID 42,
AccountNumber 4010, invoice 7947, line 10645: **2 × $344.21 = $688.42**.
GrandTotal **$787.48** has a different scope. One matched account/credit does
not establish classification, complete journal entry, settlement, population
completeness, or revenue recognition, and does not explain the 2026 margin change.

Quality exhibits retain selected-record qualifications. The Sales salary budget
pair preserves fiscal-2025 values and makes the fixed account context visible.
The illustrative both-zero rows are not asserted dataset exceptions. All speaker
notes and selected public tutorial responses remain public; assigned practice
receives the evidence-record format without answers.

## Disposition of all 40 original slides

| Original slide / ID | Disposition | Revised position |
|---|---|---|
| 1 title-slide | Book title and chapter subtitle; remove author | 1 |
| 2 ch02-objectives | Move after scenario; cover all six objectives in three pairs | 4 |
| 3 ch02-module-purpose | Keep recording-module boundary | 2 |
| 4 ch02-scenario | Add internal-auditor role, supervisor, and review period | 3 |
| 5 ch02-fit | Add paid-versus-outstanding population task | 6 |
| 6 ch02-types | Use FreightCost and Status examples | 7 |
| 7 ch02-identifiers | Distinguish internal ID, account code, and amount | 8 |
| 8 ch02-structure | Retain readable native table | 9 |
| 9 ch02-sources | Retain table; ask source choice before new response | 10 |
| 10 ch02-erp | Expand ERP; ask about bank timing | 12 |
| 11 ch02-module-quality | Keep module boundary | 13 |
| 12 ch02-dimensions | Retain four practical questions | 14 |
| 13 ch02-missing | Preserve selected rows and scope limits | 15 |
| 14 ch02-blank-meaning | Distinguish bought/sold service roles | 16 |
| 15 ch02-status | Remove unsupported as-of assertion | 17 |
| 16 ch02-duplicate-invoice | Request evidence; distinguish repeat from payment error | 18 |
| 17 ch02-names | Keep qualified comparison task; invent no named pair | 19 |
| 18 ch02-freight | Preserve zero-baseline chart; ask for peers | 20 |
| 19 ch02-tutorial-start | Cover all eight steps; retain working copy and link | 22 |
| 20 ch02-minifs | Replace small code block with full-width native formula | 23 |
| 21 ch02-date-check | Explain all branches; retain outer guard | 24 |
| 22 ch02-finding | Move immediately before activity setup | 21 |
| 23 ch02-module-tidy | Keep module boundary | 28 |
| 24 ch02-tidy-rules | Ground observation in fixed salary context | 29 |
| 25 ch02-budget-wide | Highlight Sales; add reshape task | 31 |
| 26 ch02-budget-long | Adjacent response; preserve amounts and selected scope | 32 |
| 27 ch02-grain | Move before budget pair and retain counting question | 30 |
| 28 ch02-tidy-clean | Apply missing-amount question | 33 |
| 29 ch02-module-core | Keep module boundary | 34 |
| 30 ch02-core-start | Cover all eight steps; add entry-point tutorial link | 35 |
| 31 ch02-balance-limit | Add native totals; label full extract; ask limitation | 36 |
| 32 ch02-account-keys | Add actual AccountID matching task | 38 |
| 33 ch02-periods | Add verified coverage and posting-row count | 40 |
| 34 ch02-zero | Add illustrative contrast; retain AND condition | 41 |
| 35 ch02-trace | Add focused source/line view; split amount scope into task/response | 43 |
| 36 ch02-checkpoint | Rewrite as four-sentence supervisor assessment | 46 |
| 37 ch02-summary | Retire generic summary ID; replace with qualified model | 47 |
| 38 ch02-next | Keep practice approach and Chapter 3 transition | 48 |
| 39 ch02-references | Add end-only Codesso attribution; retain APA note entries | 49 |
| 40 ch02-credits | Match Chapter 1 surname-only credit and public-note policy | 50 |

New slides: 5 scope; 11 source response; 25 date task; 26 date response;
27 operational checkpoint; 37 balance response; 39 account response;
42 expected-source check; 44 amount task; 45 amount response.

## Build and review record

The supplemental generator owns Chapter 2 storytelling evidence only. Explicit
refresh checks the pinned database checksum, opens SQLite read-only, and records
source/input/artifact hashes. Ordinary checks/builds/previews never require the
dataset. Text hashing normalizes line endings across Windows and Linux.

Focused builds use isolated Quarto staging and preserve other decks. Chapter
selection remains prohibited for full assembly and public export. Durable
sources and this review are tracked; outputs are disposable renders and reports.

Fresh Reveal and PPTX builds pass the automated artifact checks: both formats
contain the intended 50 slides, public notes, native tables/text, embedded media,
and valid local resources/package relationships. The regression suite passes
79 tests, including selected refresh isolation, dataset-free provenance,
LF/CRLF equivalence, artifact tampering, and focused output preservation.

Native inspection was stopped with the physical Escape key before the deck was
opened. **PowerPoint visual inspection and Excel formula execution remain
unverified.** Reveal slide/fragment visual inspection and a fresh sanitized-bundle
render also remain unverified. Automated checks do not substitute for those
acceptance checks. Author acceptance and coordinated release remain pending.
