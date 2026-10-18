---
note: ch19.r6
uses: [ch19.g6]
title: Sample what the database cannot show (Chapter 8)
kind: requirement
number: '6'
unit: '19'
perspective: auditing
tool: excel
minutes: 150
solution: "Chapter19-capstone-excel.zip: Credits Audit.xlsx, worksheet Sample (attributes, parameters, key items, the rule, the frozen selection, D1 and A3)"
figures:
  - id: IF-19-6-A
    kind: excel-mock
    purpose: The plan a student hands in before testing anything.
    shows: "The Sample worksheet: named parameter cells, the table of sizes with the used cell outlined, the key items with the reason each is key, and the rule table for zero to three deviations with the limit and Yes or No."
    data: The case's parameters and the refunds of Requirement 4's Refunds Table.
  - id: IF-19-6-B
    kind: chart
    purpose: Why the plausible draws point the same way, and why the population test is the better evidence.
    shows: "Bars of the probability of each deviation count in a draw from the remainder, the plausible range shaded, the model answer's frozen draw marked, and the upper deviation limit labeled at each end of the range."
    data: The hypergeometric distribution for the remainder and its deviating refunds, and the model workbook's frozen draw.
---
{% set g = ch19_g6 %}
# Requirement 6: Sample what the database cannot show (Chapter 8)

{{ header() }}

## Purpose and learning outcomes

This is the one requirement where sampling is the right tool, and the point is to know why. The records cannot show whether a customer asked in writing for a refund, whether someone independent checked the payee, or whether anyone inspected goods returned damaged. Those are documents, examined one at a time. Students plan the sample, with its rule, before anything is selected, take the key items in full, then draw and freeze the rest with the plan. On the one attribute the data can test, they see that a query of the whole population finds what a sample can only estimate. The analytics type is statistical inference: the upper deviation limit says what the population could be, not what will happen.

Students can size an attribute sample from the case's table, take key items in full, write the rule first, draw and freeze the rest with the plan (Parts 1 to 4), and compare a sample with the population test (Part 5), while refusing to report results the database cannot hold (Part 6).

**Competencies practiced.** CPA Evolution Core S2 M8 (audit evidence and tests of controls); IMA Data Analytics and Insights (statistical analysis); IFAC IES 2 (f); AACSB A5 part 5.1 (Excel).

## Before you assign

- **Files.** Credits Audit.xlsx. Before this requirement, load the Refunds, Credits and ReturnLines Tables with the case note's build contract (Refunds carries BeforePayment), or open the model workbook: Requirement 4's SQL output alone does not create these Tables. Excel for Microsoft 365: the draw needs RANDARRAY and SORTBY, the rule BETA.INV; the model also uses LET, FILTER, HSTACK, TAKE and XLOOKUP.
- **Data conditions.** No table holds a request, a payee check or an inspection record. The reason for a return is SalesReturn.ReasonCode, which is what defines the third attribute's population. Students' draws differ from the model's, so grade the plan, not the count: no draw-specific count, such as the model's, is a criterion.
- **Verify first.** The size cell reads {{ n }} with {{ g.conf|pct(0) }} confidence, a {{ g.tol|pct(0) }} tolerable rate and no expected deviations, and the key items and the remainder read {{ g.nk }} and {{ g.n_rest }}.

## How to run it

Individual or pairs, about 150 minutes: 25 for the attributes, 15 for the parameters and size, 25 for the key items, 25 for the draw and freeze, 15 for the rule, 25 for D1 and the comparison, 20 for A3 and the write-up. Hold back the third attribute's own population until students have a draw, and the comparison with Requirement 4 until the rule is frozen. **Collect** the workbook with the frozen selection, its date and parameters, and the rule dated before the count.

## Step-by-step solution

### Part 1: Define three attributes that need outside evidence

**Step 1. Name each attribute and its deviation.** On the Sample sheet, list A1 (a written request, dated before the refund and for its amount), A2 (a payee checked against the customer master by someone independent) and A3 (an inspection record, for refunds of returns coded Damaged only), each with the evidence and what counts as a deviation. Add D1, the data attribute: the refund dated before the last application of the customer's payments, as Requirement 4 defined it.

**Check:** A1 and A2 apply to all {{ g.n_all }} refunds, A3 to {{ s.dmg.n }} of them ({{ s.dmg.key }} key items and {{ s.dmg.rest }} in the remainder). **Watch for:** A3 sampled like the others. A draw of {{ n }} from the remainder expects about {{ s.dmg.mean|num(1) }} Damaged refunds, so the other refunds of the draw are not tests of an inspection.

### Part 2: Choose the parameters and read the size

**Step 2. Enter the parameters and take the size from the table.** Enter the confidence, the tolerable rate and the expected rate in cells, and name them as the model does (SampleConfidence, TolerableRate, ExpectedRate, SampleSize). The model reads the size and the deviations the plan allows from the case's table by the two-way lookup below; typing the value is acceptable.

```jinja
{{ g.f_size }}
```

**Check:** {{ n }} refunds, no deviation allowed. **Watch for:** a size from the wrong column: {{ g.size_tol10 }} (the next column) and {{ g.size_conf90 }} (the {{ 0.9|pct(0) }} column) have limits of {{ g.udl_tol10|pct(1) }} and {{ g.udl_conf90|pct(1) }} at no deviation, above the tolerable rate, so the plan fails before any test.

### Part 3: List the key items

**Step 3. List the key items.** Name the thresholds in cells (KeyAmount and KeyCustomerTotal) and spill the key items with one formula, which reads each refund's amount and its customer's three-year total.

```jinja
{{ g.f_key }}
```

**Check:** {{ g.nk }} key items (${{ s.key_total|money }}): {{ g.focus_n }} from customer {{ g.focus }}, whose refunds total ${{ g.focus_total|money }}, and the rest by amount. The remainder is {{ g.n_rest }} refunds (${{ s.rest_total|money }}). **Watch for:** a test on the refund's own amount, which finds {{ g.by_amount }}, or the refund threshold applied to the customer total, which finds {{ g.key_if_5000 }}.

### Part 4: Write the rule, then draw and freeze

**Step 4. Write the evaluation rule, then select.** Choose and record the attributes, population, key-item rules, confidence, tolerable and expected rates and the rule first; only then select and freeze the sample, and never backdate a rule after the outcomes are seen. The rule tabulates the upper deviation limit for zero to three deviations (one more than the plan allows, if more), with a guarded boundary: a whole number k from 0 to n, and a limit of 100 percent when every item deviates.

```
=IF(OR(k<0,k>n,k<>INT(k)),"Not evaluable",IF(k=n,1,BETA.INV(confidence,k+1,n-k)))
```

**Check:** {{ s.udl[0]|pct(2) }}, {{ s.udl[1]|pct(2) }}, {{ s.udl[2]|pct(2) }} and {{ s.udl[3]|pct(2) }}. Only no deviation supports reliance at the tolerable rate. **Watch for:** a rule written after the count, which ends at the count it found. Date it before the draw.

{{ figure('IF-19-6-A') }}

**Step 5. Draw the remainder and freeze it with its plan.** The model draws once, in a single cell that spills.

```jinja
{{ g.f_draw }}
```

a. Enter the formula below the header of the selection and confirm it spills {{ n }} rows.
b. Copy the spill and choose **Home > Paste > Paste Values** without moving the selection.
c. Record the selected IDs, the date and the method, with a copy of the plan (rates, planned size, key-item thresholds, population and key-item counts); the model keeps it in columns M and N as values.

**Check:** {{ n }} distinct refunds, none of them a key item, {{ s.share|pct(1) }} of the remainder. **Watch for:** two errors. An unfrozen draw changes at every recalculation, and with it the count of deviations ({{ s.lo }} to {{ s.hi }} in {{ s.inside|pct(0) }} of draws). A draw from all {{ g.n_all }} refunds holds about {{ g.exp_key|num(1) }} key items, and about one draw in nine holds none, so the error hides itself.

### Part 5: Apply D1 to the sample and compare it with the population

**Step 6. Count D1's deviations in the draw, then in the remainder.** A column of the frozen selection looks up each refund's flag; the count and the limit follow. The limit uses the frozen plan and the actual tested count (valid, distinct, eligible IDs with an outcome), after the selected, distinct, eligible and tested counts are reconciled: an incomplete test, a count above n, or missing or duplicate IDs read "Not evaluable", and every item deviating reads 100 percent.

```jinja
{{ g.f_count }}
```

**Check:** the model's draw holds {{ g.k_drawn }} deviations ({{ g.draw_rate|pct(1) }}), an upper limit of {{ g.udl_drawn|pct(1) }}: no reliance. The population test finds {{ s.dev|length }} of the {{ g.n_rest }} ({{ g.pop_rate|pct(1) }}) and {{ s.key_dev }} of the {{ g.nk }} key items, the same conclusion. A draw holds {{ s.lo }} to {{ s.hi }} deviations in {{ s.inside|pct(0) }} of cases, with limits from {{ s.udl_lo|pct(0) }} to {{ s.udl_hi|pct(0) }}, and a draw with no deviation has probability {{ g.p_zero }}.

**Watch for:** the draw's rate offered as the population's, or the limit as a forecast, and a limit on the planned size instead of the tested count (one deviation reads {{ s.udl[1]|pct(4) }} at {{ g.size }} and {{ g.udl1_exp1|pct(4) }} at a planned {{ g.size_exp1 }}, which would wrongly cross the {{ g.tol|pct(0) }} boundary). A changed plan means a new selection: the model reads "Plan changed: redraw or revalidate the selection". Where the data hold the evidence, the query replaces the sample.

{{ figure('IF-19-6-B') }}

### Part 6: Plan A3 on its own population, and deliver no results

**Step 7. Size A3 on the Damaged refunds.** Count them, split the key items from the remainder, and see what the draw holds.

```jinja
{{ g.f_a3 }}
```

**Check:** {{ s.dmg.n }} refunds, {{ s.dmg.key }} key and {{ s.dmg.rest }} in the remainder. The model's draw holds {{ g.dmg_drawn }}, and even if all of them passed the limit would be {{ g.udl_dmg|pct(2) }}, so examine all {{ s.dmg.n }}: with no sample, no sampling risk. **Watch for:** the whole draw counted as inspected, which gives {{ s.udl[0]|pct(2) }} and a false pass.

**Step 8. Mark what is not tested.** Fill the attribute columns of the draw with the words the model uses (Not tested: no document in the database; Not applicable for A3 on a refund of another return). The deliverable is the plan, the frozen selection and the rule.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Sample size; deviations the plan allows | {{ n }}; 0 | 2 |
| Key items; amount | {{ g.nk }}; ${{ s.key_total|money }} | 3 |
| Remainder; amount | {{ g.n_rest }}; ${{ s.rest_total|money }} | 3 |
| Upper limit at zero to three deviations | {{ s.udl[0]|pct(2) }}; {{ s.udl[1]|pct(2) }}; {{ s.udl[2]|pct(2) }}; {{ s.udl[3]|pct(2) }} | 4 |
| D1 in the remainder; in the key items | {{ s.dev|length }} of {{ g.n_rest }}; {{ s.key_dev }} of {{ g.nk }} | 6 |
| Model draw: deviations; limit; Damaged refunds | {{ g.k_drawn }}; {{ g.udl_drawn|pct(1) }}; {{ g.dmg_drawn }} | 6, 7 |
| Damaged refunds: all; in the remainder | {{ s.dmg.n }}; {{ s.dmg.rest }} | 7 |

{{ expected() }}

## What a strong answer says

- **Each attribute states its evidence and its deviation,** and the third has its own population.
- **The plan comes first:** the parameters, the size from the table, the key items in full and the rule, then the draw frozen with its date and plan.
- **The rule is written and dated before the draw,** and no result is invented: the plan, the selection and the rule are the deliverable.
- **D1 shows the point:** the sample and the population agree, and the population is the better evidence.

A weak answer samples A3 across all refunds, or reports passes for documents nobody has seen.

## Common mistakes and how to respond

- **The wrong table column.** *Symptom:* a size of {{ g.size_tol10 }}. *Response:* ask what the limit at no deviation is, and compare it with the tolerable rate.
- **Key items by amount only.** *Symptom:* {{ g.by_amount }} key items. *Response:* ask which customer's refunds the rule was written for.
- **The customer threshold at the refund's.** *Symptom:* {{ g.key_if_5000 }} key items. *Response:* ask the two thresholds apart.
- **An unfrozen draw.** *Symptom:* a count that moves on recalculation. *Response:* ask where the selection is recorded.
- **A3 across the draw.** *Symptom:* {{ n }} refunds inspected, none deviating. *Response:* ask how many were of Damaged returns.
- **Invented results.** *Symptom:* "No deviation" under A1 to A3. *Response:* ask for the document.
- **A rule written after the count.** *Symptom:* rows that stop at the count found. *Response:* ask when the rule was dated, and what the draw would have changed.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Three attributes, A3 on its own population | 20 | Evidence, deviation and population for each | A3 sampled across all refunds |
| Parameters and size | 15 | Named cells, size from the table | Size without parameters |
| Key items in full | 15 | Both thresholds, {{ g.nk }} items | The amount threshold only |
| Frozen selection | 15 | Distinct, not key, dated, with its parameters as a frozen plan | Live formula |
| Rule written first | 15 | Zero to three deviations, dated before the draw | Rule after the count |
| D1 on the sample and the population | 10 | Both, compared | Sample only |
| No invented results | 10 | Tested columns marked as such | Passes reported |

## Extensions and discussion questions

- A sample of {{ n }} is {{ s.share|pct(0) }} of the remainder. Why would a finite-population correction allow a smaller one, and why does the size at a `2%` expected rate, {{ g.size_2pct }}, call for examining all?
- Discuss: the sample's limit is {{ g.udl_drawn|pct(1) }}. What can the committee do with it, and what can it not?
