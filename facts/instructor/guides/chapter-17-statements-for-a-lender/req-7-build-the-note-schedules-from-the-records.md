---
note: ch17.r7
uses: [ch17.g7]
title: Build the note schedules from the records (Chapters 6, 10, 11, and 14)
kind: requirement
number: '7'
unit: '17'
perspective: financial
tool: mixed
minutes: 150
solution: "Chapter17-capstone-sql.zip: LenderPackage.sql, the queries headed Requirement 7 (the register and its depreciation, disposals, notes, maturities, revenue, contract balances, services, components); Chapter17-capstone-excel.zip: Charles River Lender Package.xlsx, worksheets Notes (the schedules and the text of the notes) and Fixed Assets"
figures: []
---
{% macro sm(x) %}{{ "-" if x < 0 else "" }}${{ (x|abs)|money }}{% endmacro %}
{% set g = ch17_g7 %}
# Requirement 7: Build the note schedules from the records (Chapters 6, 10, 11, and 14)

{{ header() }}

## Purpose and learning outcomes

The notes this requirement asks for rest on schedules that the records can produce, and each schedule must agree with the statements. Notes on policies and uncertainties are text, judged on their evidence. Rebuilding a register, a debt schedule or revenue by product line joins documents to the ledger, which suits SQL; the workbook formats each schedule beside its statement and holds the text. The case allows Chapter 14's sales model for the revenue note if it is reconciled to the ledger and the cutoff, so students choose and say why. The analytics type is descriptive.

Students can roll property and equipment forward and reconcile it (Part 1), state the notes' terms, maturities and current portion (Part 2), disaggregate revenue on the adjusted basis (Part 3), break accrued liabilities and inventories into components (Part 4), and write the notes (Part 5).

**Competencies practiced.** CPA Evolution Core S1 M1 to M3 and BAR M10 (advanced data analytics: data models and joins); IMA Reporting and Control (financial statement preparation); IFAC IES 2 (a); AACSB A5 part 5.1 (technology integration: Excel and SQL).

## Before you assign

- **Files.** `LenderPackage.sql`, the workbook with Requirements 1 to 6 done, and CharlesRiver.xlsx for the Fixed Assets Table.
- **Data conditions.** FixedAsset holds no residual values; each note links to its asset through DebtAgreement.FixedAssetID, and no column records a security interest; design services and freight billed each have their own revenue account; `2070` is unused.
- **Verify first.** The register, at monthly amounts rounded to the cent, reproduces the ledger's depreciation.

## How to run it

Pairs, about 150 minutes: 35 for property and equipment, 20 for the notes payable, 35 for revenue, 20 for accrued liabilities and inventories, 30 for the text, 10 to check. Give the dates rule (the month after service through the month before disposal) only when the register and the ledger differ. **Collect** the Notes worksheet.

## Step-by-step solution

### Part 1: Property and equipment

**Step 1. Rebuild the register's depreciation.** In Excel load FixedAsset with its account numbers and add a first month, a last month and a monthly amount; the SQL does the same in the Register CTE of the first two Requirement 7 queries. The model's last month ends at the life or the month before disposal:

```jinja
{{ g.f.last_month }}
```

**Check:** the register's depreciation equals the ledger's Depreciation entries, ${{ dep_p|money }} in {{ d.P }} and ${{ dep_c|money }} in {{ d.C }}, on lives of {{ life_low }} to {{ life_high }} months and no residual value. **Watch for:** counting the month of disposal, one more month for each disposed asset: the register exceeds the ledger by ${{ g.over[d.P]|money }} in {{ d.P }} and ${{ g.over[d.C]|money }} in {{ d.C }}.

**Step 2. Roll cost and accumulated depreciation forward by class.** Four classes; for each year the opening balance, additions, disposals and closing balance, with the opening and closing taken from WorkingTB, disposals from the credits of the Asset Disposal entries, and a check column against the register.

**Check:** cost ${{ cost_f|money }}, ${{ cost_p|money }}, ${{ cost_c|money }}; accumulated depreciation ${{ acc_f|money }}, ${{ acc_p|money }}, ${{ acc_c|money }}. Disposals: {{ disp_p.code }} (loss ${{ disp_p.loss|money }}, proceeds ${{ disp_p.proceeds|money }}) and {{ disp_c.code }} (loss ${{ disp_c.loss|money }}, no proceeds); the {{ d.C }} addition, {{ add_c.codes[0] }}, was financed by a note, a noncash event. Of ${{ dep_c|money }}, ${{ to1090_c|money }} went to `1090`, not to an expense. **Watch for:** summing the register's cost without removing disposed assets: ${{ g.all_cost|money }}, ${{ g.disposed|money }} above the ledger.

### Part 2: Notes payable

**Step 3. State each note's terms, maturities and current portion.** The script's notes payable query joins DebtAgreement to FixedAsset and sums DebtScheduleLine's principal after each year-end, with the ledger's `2110` beside it as a check; a second query sums the principal due by year, and the first year is the current portion that Requirement 5 reclassified.

**Check:** note 1, ${{ notes[0].principal|money }} at {{ notes[0].rate }}, finances {{ notes[0].asset }}; note 2, ${{ notes[1].principal|money }} at {{ notes[1].rate }}, finances {{ notes[1].asset }}. Balances ${{ notes[0].c|money }} and ${{ notes[1].c|money }}, ${{ notes_total|money }} in all, equal to `2110`. Principal due: {{ g.mat_text }}. Interest paid ${{ g.interest_paid[d.C]|money }}. **Watch for:** two slips. Summing scheduled payments instead of principal gives ${{ g.five_total|money }} over five years, ${{ g.interest_left|money }} above the balance, and a current portion of ${{ g.next_payments|money }}, not ${{ g.next_principal|money }}. Calling a note secured by its asset claims what the records do not show.

### Part 3: Revenue

**Step 4. Disaggregate revenue on the adjusted basis.** Adjusted revenue is the ledger's revenue by account plus Requirement 4's cutoff items by year of delivery. The model's revenue query builds the items in a Cutoff CTE: each late invoice added to its delivery year and taken out of its posting year, and each shipment line never invoiced at order price less discount.

The workbook reads the adjusted trial balance by revenue account and adds the cutoff to the invoice lines for the segments.

**Check:** by product line, design services, freight and the five segments, the amounts of the instructor note below; at a point in time ${{ point_c|money }} and over time ${{ svc_c|money }} in {{ d.C }}. {{ d.P }}'s product revenue, ${{ ship_p|money }}, equals Exercise 14.2's revenue by ship date. The schedule is operating revenue before returns, so tie it to that line and bridge it to net revenue through the returns. The segments plus freight add up to operating revenue. **Watch for:** the ledger's revenue without the cutoff: ${{ g.revenue_gap[d.C]|money }} below the adjusted income statement in {{ d.C }} and ${{ (g.revenue_gap[d.P]|abs)|money }} above it in {{ d.P }}.

**Step 5. Show the contract balances and test the services.** Receivables are ${{ recv_p|money }} and ${{ recv_c|money }}, each including the opening line that no document supports; no contract asset or liability is recorded; customer credits awaiting refund (`2060`) are ${{ credits[1]|money }} and ${{ credits[2]|money }}, {{ issued }} Issued credit memos at the last year-end. The services query tests each year-end, engagement by engagement, setting the hours worked through it against the hours billed on invoices posted by it, in hours and amount.

**Check:** no difference at any year-end ({{ svc_ye[0].n }}, {{ svc_ye[1].n }} and {{ svc_ye[2].n }} engagements), so the records show no recorded service work left unbilled at a year-end, though they cannot show that every hour worked was recorded. **Watch for:** a test over the whole extract or by today's status, which cannot see December work billed in January. And engagement {{ engs[0].id }}'s planned hours less its billed hours, {{ g.short_hours|num(2) }}, are planned work not recorded as worked, not unbilled work.

### Part 4: Accrued liabilities and inventories

**Step 6. Break each line into its components.** Accrued liabilities by payroll, commissions, accrued expenses after A3 and interest, and inventories by finished goods as recorded, materials at purchase-order cost and work in process net of the `1090` credit. Each total must equal its balance sheet line.

**Check:** accrued liabilities ${{ s_c.accrued|money }}, of which payroll ${{ s_c.payroll|money }}; inventories ${{ s_c.inv|money }}, of which materials ${{ s_c.mat|money }}. **Watch for:** showing only the wages owed, ${{ g.payroll_only|money }}. The total misses the balance sheet by the ${{ opening_2030|money }} opening line.

### Part 5: The text of the notes

**Step 7. Write the notes.** Five notes, each tied to the statements.

| Note | It must say | Ties to |
|---|---|---|
| Property and equipment | Method and lives; additions, disposals, the noncash acquisition | The roll-forward |
| Notes payable | Terms, linked asset, maturities, current portion, interest paid | `2110` |
| Revenue | Timing and its assumption; disaggregation; contract balances; no recorded service work unbilled | The income statement |
| Accrued liabilities | Components, the opening line named | The balance sheet |
| Correction of {{ d.P }} | Each error, each affected {{ d.P }} line as reported, adjusted and restated, the effect on opening retained earnings, the tax effect still open, A3's assumption, and unchanged cash-flow totals | The equity statement and the {{ d.P }} column |

Notes still to be written (policies, inventories, Requirement 9's matters) go on the memo's list.

## Expected results

| Quantity | Value | Step |
|---|---|---|
| Cost at the three year-ends | ${{ cost_f|money }}; ${{ cost_p|money }}; ${{ cost_c|money }} | 2 |
| Notes payable at the last year-end | ${{ notes_total|money }} | 3 |

{{ expected() }}

## What a strong answer says

- **Property and equipment and notes.** Method, lives, both disposals, the noncash acquisition; the asset each note financed, with no security interest claimed.
- **Revenue.** The adjusted basis, both timing assumptions stated (delivery for the goods, the over-time criteria for the services), and the bridge to net revenue.
- **Accrued liabilities and the correction.** The opening line named; no effect on cash.

A weak answer lists balances without reconciling them to the statements.

## Common mistakes and how to respond

- **Disposal month counted.** *Symptom:* register ${{ g.over[d.C]|money }} above the ledger. *Response:* ask the month the asset left.
- **All assets' cost.** *Symptom:* cost ${{ g.disposed|money }} high. *Response:* ask which assets the company still owns.
- **Payments as principal.** *Symptom:* maturities ${{ g.interest_left|money }} above the balance. *Response:* ask what the payment includes.
- **Ledger revenue.** *Symptom:* ${{ g.revenue_gap[d.C]|money }} short of the income statement. *Response:* ask which year the delivery belongs to.
- **Planned hours.** *Symptom:* {{ g.short_hours|num(2) }} hours unbilled. *Response:* ask what the time records show.

## Grading guide

| Criterion | Points | Full credit | Partial credit |
|---|---:|---|---|
| Property and equipment | 25 | Roll-forward by class, register reconciled, disposals and method | Balances without reconciliation |
| Notes payable | 15 | Terms, asset, maturities, current portion, interest | Balance only |
| Revenue and contract balances | 25 | Three disaggregations on the adjusted basis, contract balances, services test | Ledger basis |
| Accrued liabilities and inventories | 15 | Components equal the lines | Totals only |
| Text of the notes | 20 | Five notes, accurate, tied to the statements | Missing the correction note |

## Extensions and discussion questions

- Discuss: why is the link to the financed asset not enough to describe a note as secured, and which executed agreement would establish the security terms?
