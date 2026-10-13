---
note: ch19.r10
uses: [ch19.g10]
title: Keep the tests running (Chapter 16)
kind: requirement
number: '10'
unit: '19'
perspective: auditing
tool: powerbi
minutes: 90
solution: "Chapter19-capstone-pbi-monitoring.zip: Audit Monitoring/Audit Monitoring.pbip (the pages Credits Cycle, Anomalies and Change Log added to those of Chapter 16; the Tests and Checks tabs in DAX query view)"
figures:
  - id: IF-19-10-A
    kind: pbi-mock
    purpose: The Credits Cycle page, where the new tests and the design findings show.
    shows: "The Credits Cycle page of Audit Monitoring: a matrix of the four new tests by year with exceptions, population and rate per 1,000, a row of cards for the exceptions, the reviewed exceptions, the exceptions covered by a design finding and the open exceptions, and a table of the design findings with the period each covers and the date it is to be fixed."
    data: The Audit Monitoring model answer on the pinned dataset.
  - id: IF-19-10-B
    kind: diagram
    purpose: How the flags reach the register, the picture a student needs when a rate comes out blank.
    shows: "A left-to-right flow: the applications and the credit memos and refunds feed two flag queries, which are unpivoted into two exception queries, appended into the register with the dispositions and the design findings, and tied by the test identifier to the Tests table and by the process name to the Population measure. A side branch marks the anomaly columns that stop at the refund table."
    data: none; the flow follows the model answer's queries.
---
{% set g = ch19_g10 %}
# Requirement 10: Keep the tests running (Chapter 16)

{{ header() }}

## Purpose and learning outcomes

An audit that ends with a report tests the past. The register of Chapter 16 already runs the rule tests of earlier chapters with every refresh, and adding this cycle's rules to it, under the change control that chapter described, turns the audit into monitoring. Two judgments carry the requirement. A rule test, where a document either passes or fails, belongs in the register; an anomaly, a reason to look, stays outside it. And the historical exceptions of the new tests are recorded once, as a finding about the control's design, so that they do not flood the review. The analytics type is prescriptive: the tests are the action that outlasts the report.

Students can add rule tests and their populations to a register (Part 1), keep anomalies outside it (Part 2), treat historical exceptions as one design finding and close it on a retest (Part 3), build the small alternative when no register exists (Part 4), and recheck the date the data run through and record the change (Part 5).

**Competencies practiced.** CPA Evolution ISC M2 (tests of internal controls, logical access and change management) and Core S2 M9; IMA Reporting and Control (internal control); IFAC IES 2 (g) and (i); AACSB A5 parts 5.1 (Power BI) and 5.3 (learning to learn).

## Before you assign

- **Files.** Audit Monitoring.pbix as Chapter 16 leaves it, CharlesRiver.xlsx, and Power BI Desktop (Windows only). Students use the definitions of Requirement 4; a different definition of "before the payment" changes a count ({{ rcpt_n }} refunds by the receipts' dates, and a register of {{ rcpt_new }} rows).
- **Data conditions.** The credits end {{ cm_last }} and the refunds {{ rf_last }}, after payroll's last pay date, {{ through }}, so Data Through stays where it is. No exception of the new tests is dated after the audited year.
- **Verify first.** In DAX query view, run the Checks tab: {{ g.n_r10_checks }} rows for the requirement and the register's chain, {{ g.per_section['Milestone 2'] }} and {{ g.per_section['Milestone 3'] }} for the milestones, all agree.

## How to run it

Pairs, about 90 minutes: 35 for the flags and the exception queries, 10 for the tests and the populations, 15 for the anomalies, 15 for the design finding, 15 for Data Through and the change log. Hold back the design finding until the register shows the flood, then ask what the committee would do with it. **Collect** the project and a screenshot of the Tests tab.

## Step-by-step solution

### Part 1: Add the four rule tests and the two processes

**Step 1. Build the flags in Power Query.** Two queries from CashReceiptApplication do not load (clear **Enable load**): Last Payments, the last application date of each invoice, and Appliers, the applications grouped by invoice and applier.

```jinja
{{ g.m_last }}
{{ g.m_appliers }}
```

CreditMemo then merges the approver's limit and the appliers and adds its two flags.

```jinja
{{ g.m_cm }}
```

CustomerRefund merges the limit, the credit's invoice and the last application, and adds its two.

```jinja
{{ g.m_rf }}
```

**Check:** the flags count {{ tests[0].n }}, {{ tests[1].n }}, {{ tests[2].n }} and {{ tests[3].n }}. **Watch for:** the appliers merged on the invoice alone, which flags {{ g.any_app }} of {{ g.n_credits }} credits instead of those whose approver applied the cash, and a refund compared with `<=`, which flags {{ g.same_day }} instead of {{ tests[3].n }}.

**Step 2. Turn each flag into register rows.** One query for the credits and one for the refunds unpivots its two flags, keeps the ones, and names the test; the register's Source step then combines them with the existing queries.

```jinja
{{ g.m_cmx }}
```

{{ figure('IF-19-10-B') }}

**Check:** the register grows from {{ old }} to {{ new }} rows, and each test and document pair is still unique. **Watch for:** a TestID that differs from the one in the Tests table.

**Step 3. Add the tests and the processes.** Four rows join the Tests table (TestID, Test, Process, Source), with the processes Credit memos and Refunds, and the Population measure counts them; relate the credit and refund dates to Date.

```jinja
{{ g.d_pop }}
```

| Test | Exceptions | By year | `Rate per 1,000` |
|---|---:|---|---:|
{% for t in tests %}
| {{ t.name }} | {{ t.n }} | {{ t.years|join(' / ') }} | {{ t.rate|num(1) }} |
{% endfor %}

**Check:** the rates by year in the table above, from populations of {{ pop_c|join(' / ') }} credits and {{ pop_r|join(' / ') }} refunds. **Watch for:** a process spelled differently from the measure's, which leaves the population and the rate blank while the exceptions still count.

### Part 2: Keep the refund method and the missing offset outside the register

**Step 4. Add them as columns of the refund table, with their own measures and page.**

```jinja
{{ g.m_anom }}
```

**Check:** {{ g.mism }} refunds by a method no receipt on the invoice used, and {{ g.pd2 }} paid while the customer's past-due balance was at least the refund. They stay out because no customer pays by one method only and a method chosen at random would mismatch about as often, and because the records hold no policy that requires an offset. **Watch for:** adding them to the register, which makes it {{ g.anomaly_flood|count }} rows and buries the rule failures.

### Part 3: Give the historical exceptions one design-finding treatment

**Step 5. Record the finding once and keep every exception.** A Design Findings table (**Home > Enter data**) holds, for each new test, the finding, the date it covers through and the date it is to be fixed. Merge it into the register by TestID and add a Covered column, then measure the open exceptions without the covered ones.

```jinja
{{ g.m_cov }}
{{ g.d_open }}
{{ g.d_cov }}
```

{{ figure('IF-19-10-A') }}

**Check:** the findings cover exceptions dated through the end of the audited year and are to be fixed by {{ g.fix_by }}; {{ g.new_rows }} exceptions are covered, {{ g.reviewed }} reviewed, and {{ g.open_old }} open, as before. Exceptions dated later stay open for review, and a finding closes when a retest after the fix shows the control works, not on its planned date. **Watch for:** the open measure without the Covered condition, which reads {{ g.open_flood }}, and the covered period set to the fix-by date, which would hide later exceptions until then. After remediation the two authority tests should fall to zero; the other two would catch the next case.

### Part 4: If you did not build Audit Monitoring.pbix

**Step 6. Build a small register in Credits Analytics.** A Tests table by Enter data with the four rows, and an exceptions table that combines the two unpivoted flag queries, as in Steps 1 to 3; the refund flags of Requirement 4's export hold two of the four tests. The model answer builds only the Audit Monitoring path, so grade this path by its structure: four tests, two processes, a unique pair on each row.

**Check:** {{ g.new_rows }} exceptions, one row for each test and document.

### Part 5: Recheck Data Through and record the change

**Step 7. Take the earliest of the processes' last dates, and log the change.** The measure adds the last credit and refund dates to the earlier three; the Change Log table (Enter data) records what changed and why.

```jinja
{{ g.d_through }}
```

**Check:** Data Through reads {{ through }}, set by payroll, the earliest of the five; the Change Log has {{ g.n_log }} rows. **Watch for:** the latest date in place of the earliest, which reads {{ g.max_through }} and claims more than payroll's records show. In DAX query view, rerun Tests 1 to 6; the instructor check is Test 6:

```jinja
{{ g.test6 }}
```

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Exceptions of the four tests | {{ tests[0].n }}; {{ tests[1].n }}; {{ tests[2].n }}; {{ tests[3].n }} | 1 |
| Register rows, before and after | {{ old }}; {{ new }} | 2 |
| Covered by a design finding; reviewed; open | {{ g.new_rows }}; {{ g.reviewed }}; {{ g.open_old }} | 5 |
| Anomalies: method mismatch; missed offset | {{ g.mism }}; {{ g.pd2 }} | 4 |
| Data Through; Change Log rows | {{ through }}; {{ g.n_log }} | 7 |

{{ expected() }}

## What a strong answer says

- **The four tests use Requirement 4's definitions,** and the definition of "before the payment" is stated.
- **The processes are in the populations,** so each rule has a `Rate per 1,000` by year.
- **Anomalies stay outside the register,** with the reason.
- **The historical exceptions are one design finding with a fix-by date,** each kept in the register, later exceptions reviewed, and the finding closed on a retest.
- **Data Through is rechecked and the change is logged.**

A weak answer floods the register with the anomalies or the history, or closes the finding on the date.

## Common mistakes and how to respond

- **Appliers merged on the invoice alone.** *Symptom:* {{ g.any_app }} credits flagged. *Response:* ask whom the control is about.
- **A same-day refund flagged.** *Symptom:* {{ g.same_day }} refunds. *Response:* ask what the records say about the order within a day.
- **A process label that does not match.** *Symptom:* a blank rate beside a count. *Response:* compare the Tests table with the measure.
- **The anomalies in the register.** *Symptom:* {{ g.anomaly_flood|count }} rows. *Response:* ask which of them is a rule failure.
- **No design finding.** *Symptom:* {{ g.open_flood }} open exceptions. *Response:* ask who reviews that many.
- **The finding closed on the date.** *Symptom:* a status of closed with no retest. *Response:* ask what shows the control works.
- **The latest date as Data Through.** *Symptom:* {{ g.max_through }}. *Response:* ask which process ends first.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Four rule tests with Requirement 4's definitions | 30 | All four, counts agreeing | Three, or a changed definition unstated |
| Two processes in the populations | 15 | A `Rate per 1,000` by year | Counts only |
| Anomalies kept outside | 10 | Columns, measures and a page, with the reason | In the register |
| One design finding | 20 | Covered period, fix-by date, later exceptions open | History left open |
| Data Through rechecked | 10 | The earliest date, with the reason | Latest date |
| Change recorded | 15 | Log with object, change and reason | No record |

## Extensions and discussion questions

- Record a disposition for the largest refund's exception with Chapter 16's Dispositions merge, and watch Reviewed Exceptions rise by one.
- Add the anomaly tests to the register once a refund policy exists, and say what the policy must state.
- Discuss: after the fix, which two tests should fall to zero, and which two would catch the next case?
- Discuss: how long should a design finding stay open when the retest keeps failing?
