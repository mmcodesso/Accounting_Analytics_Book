<!-- Instructor notes, Exercise 12.2: receivables at {{ asof }} (days past due = julianday of the as-of date less julianday of DueDate;
     Current is zero or less): {{ n|count }} invoices with a positive open balance, {{ total|money }}, from {{ customers }} customers. {% for x in b %}{{ x.name }} {{ x.n|count }}{{ ' invoices' if loop.first }},
     {{ x.amount|money }}{{ '; ' if not loop.last }}{% endfor %}, the aging of
     Tutorial 8.2. Account 1020 (AccountID {{ ar }}) at {{ asof }} is {{ ledger|money }}; the {{ difference|money }} difference is the opening-balance line of
     {{ entry }}, which no invoice supports (Chapter 8's finding). {{ n_negative }} invoices have a negative balance ({{ negative|money }} in all):
     credit memos on invoices already paid ({{ paid_in_full|count }} of them in full), which post to account 2060 and are refunded ({{ refunded|count }} of the {{ n_negative }} by {{ asof }}),
     so they are not receivables. Strata by customer:
     under 1,000, {{ strata[0].n }} customers, {{ strata[0].amount|money }}; 1,000-9,999, {{ strata[1].n }}, {{ strata[1].amount|money }}; 10,000-49,999, {{ strata[2].n }}, {{ strata[2].amount|money }}; 50,000 and over, {{ strata[3].n }},
     {{ strata[3].amount|money }}, {{ key_share|pct }} of the balance, the key items of Tutorial 8.2. Receipts not invoiced: {{ grni_lines|count }} receipt lines, {{ grni|money }} (account
     2020 is {{ gl2020|money }}; the {{ rounding|money }} is the rounding of each invoice line's clearing amount). By receipt month: {% for m, v, n in months %}{{ m }} {{ v|money }} ({{ n|count }}{{ ' lines' if loop.first }}){{ '; ' if not loop.last }}{% endfor %}. Largest suppliers: {% for s, n, v in suppliers %}{{ s }} ({{ n }}{{ ' lines' if loop.first }},
     {{ v|money }}){{ ', ' if not loop.last }}{% endfor %}. Receipts from {{ old_from }} to {{ old_to }} are more than two months old and need follow-up
     (disputed invoices, lost invoices, or receipts recorded against the wrong order). -->
