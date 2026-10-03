<!-- Instructor notes, Exercise 10.2: {{ inv.number }} (SalesInvoiceID {{ inv.id }}, dated {{ inv.date }}, customer {{ inv.customer }} {{ inv.customer_name }}) posts {{ n_rows }}
     rows on {{ posted }}: {% for r in rows %}{{ 'GLEntry ' if loop.first }}{{ r.id }} {{ r.side }} {{ r.amount|money }} to {{ r.number }} {{ r.name }}{% if r.line %}
     with SourceLineID {{ r.line }}{% endif %}{{ '; ' if not loop.last }}{% endfor %}. Debits {{ debits|money }} =
     credits {{ credits|money }} = GrandTotal (SubTotal {{ inv.subtotal|money }}, freight {{ inv.freight|money }}, tax {{ inv.tax|money }}). Line {{ line.id }} is the {{ line.name }}, {{ line.qty|num }} units at
     {{ line.price|money }}. Requirement (3): {{ tested|count }} SalesInvoice postings of fiscal {{ d.C }} carry a SourceLineID, and none is orphaned (the anti-join returns no
     rows); the header-level rows (receivable, freight, tax) have no SourceLineID. Trap: a join on SourceDocumentID alone returns {{ trap_rows }} rows
     from {{ trap_types }} document types for ID {{ inv.id }}; the join must also require SourceDocumentType = 'SalesInvoice'. -->
