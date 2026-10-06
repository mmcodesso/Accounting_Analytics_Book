{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 10.1: the four-table join returns {{ rows|count }} rows, one per invoice line. Fiscal {{ d.C }} invoice lines by group:
     {% for g, amount in groups %}{{ g }} {{ amount|money }}{{ ', ' if not loop.last }}{% endfor %}; total
     {{ lines_total|money }}, Chapter 6's control total. Ledger, SalesInvoice postings in fiscal {{ d.C }}: {% for number, amount in ledger %}{{ number }} {{ amount|money }}{{ ', ' if not loop.last }}{% endfor %}; total {{ ledger_total|money }}. The difference of {{ diff|money }} is {{ n_cutoff }} invoices dated in late {{ d.P }}
     and posted on {{ posted }}: {% for c in cutoff %}{{ c.number }} ({{ 'dated ' if loop.first }}{{ c.date }}, {{ 'adding ' if loop.first }}{% for a, amount in c.accounts %}{{ amount|money }} to {{ a }}{{ ' and ' if not loop.last }}{% endfor %}){{ sep(loop) }}{% endfor %}
     (Exercise 6.1; Exercise 5.2's cutoff invoices). Freight is billed on the invoice
     header, not on the lines, so it posts to 4050 without a line to match. -->
