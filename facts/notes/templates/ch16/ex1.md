<!-- Instructor notes, Exercise 16.1 (SQL; Chapter 8 and Exercise 12.2): open balance = GrandTotal - applications - credit memos
     (on OriginalSalesInvoiceID), both dated <= {{ asof }}, rounded, kept if > 0: {{ n|count }} invoices, {{ total|money }} ({{ customers }} customers).
     Buckets by DueDate at {{ asof }}: {% for x in b %}{{ x.name }} {{ x.amount|money }}{{ '; ' if not loop.last }}{% endfor %}
     ({{ oldest.n }} small residual{{ 's' if oldest.n != 1 }} of invoices paid almost in full, the largest {{ oldest.largest|money }}). GL 1020 at {{ asof }}: {{ ledger|money }}; the difference, {{ difference|money }}, is the receivables line of the
     opening entry {{ entry }}, unsupported by any invoice (the author's decision: an audit finding). (5) {{ n_negative }} invoices have a
     negative balance, {{ negative|money }}: credit memos on paid invoices, credited to 2060 and refunded on {{ refunded }} of them (Chapter 8). -->
