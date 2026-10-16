<!-- Instructor notes, Exercise 10.4: GL variance postings of fiscal {{ d.C }} (descriptions ending in "purchase variance") net {{ gl|money }}.
     Largest suppliers: {% for s in top %}{{ s.id }} {{ s.name }} {{ s.amount|money }}{{ '; ' if not loop.last }}{% endfor %}. The line-level recalculation for invoices dated in {{ d.C }} is {{ lines|money }},
     {{ gap|money }} below the ledger. The ledger posts each line's stored LineTotal less the GRNI it clears, both rounded to the cent, and against the
     unrounded quantity times unit cost the line totals add {{ inv_round|money }} and the GRNI cleared {{ grni_round|money }}, so stored LineTotal less GRNI
     cleared ({{ stored|money }} less {{ cleared|money }}) reproduces {{ gl|money }} exactly (rounding each line's price difference instead gives {{ each_line|money }}). By supplier the two agree to within about {{ supplier_gap|num(2) }}. Of the {{ n_lines|count }} fiscal {{ d.C }} invoice lines
     linked to purchase-order lines ({{ unlinked|count }} of the year's {{ n_all|count }} have none and fall outside the test), {{ above|count }} are billed above the order price, {{ below|count }} below, and {{ at|count }} at it. The differences range from {{ low|pct }} below to {{ high|pct }} above. Amount
     invoiced against orders (SUM of Quantity times the invoice UnitCost) and variance: {% for y in years %}{{ y.year }} {{ y.amount|num }} and {{ y.variance|num }} ({{ y.rate|pct(2) }}){{ '; ' if not loop.last }}{% endfor %}; SUM(LineTotal) differs by {{ line_gap_low|num(2) }} to {{ line_gap_high|num(2) }} a year (the rounding of each line). The rate stays near half a percent while the amount
     invoiced grows, so most of the variance's growth from {{ bridge.first }} to {{ bridge.last }}, {{ bridge.increase|money }}, comes with the larger amount
     invoiced ({{ bridge.base|money }}, {{ bridge.base_share|pct(0) }}, at the {{ bridge.first }} rate) and the rest from the higher {{ bridge.last }} rate ({{ bridge.rate|money }}); the
     amount invoiced mixes quantity, order prices, and mix, so this does not show that Charles River simply bought more. The measure is an invoice
     price variance: a price rise already built into the purchase-order prices would not show in it. The rest of account 5060 is
     nonrecoverable purchase tax ({{ tax|money }} in {{ d.C }}). -->
