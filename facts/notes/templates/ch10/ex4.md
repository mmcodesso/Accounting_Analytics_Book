<!-- Instructor notes, Exercise 10.4: GL variance postings of fiscal {{ d.C }} (descriptions ending in "purchase variance") net {{ gl|money }}.
     Largest suppliers: {% for s in top %}{{ s.id }} {{ s.name }} {{ s.amount|money }}{{ '; ' if not loop.last }}{% endfor %}. The line-level recalculation for invoices dated in {{ d.C }} is {{ lines|money }},
     {{ gap|money }} from the ledger because each posting is rounded; by supplier the two agree to within about {{ supplier_gap|num(2) }}. Of {{ n_lines|count }} fiscal {{ d.C }} invoice lines,
     {{ above|count }} are billed above the order price, {{ below|count }} below, and {{ at|count }} at it; the differences range from {{ low|pct }} below to {{ high|pct }} above. Amount
     invoiced against orders (SUM of Quantity times the invoice UnitCost) and variance: {% for y in years %}{{ y.year }} {{ y.amount|num }} and {{ y.variance|num }} ({{ y.rate|pct(2) }}){{ '; ' if not loop.last }}{% endfor %}; SUM(LineTotal) differs by {{ line_gap_low|num(2) }} to {{ line_gap_high|num(2) }} a year (the rounding of each line). The rate is steady, so the
     account grew because purchases grew, not because suppliers raised their billing relative to the order price. The measure is an invoice
     price variance: a price rise already built into the purchase-order prices would not show in it. The rest of account 5060 is
     nonrecoverable purchase tax ({{ tax|money }} in {{ d.C }}). -->
