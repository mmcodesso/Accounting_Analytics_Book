<!-- Instructor notes, Exercise 5.1: billed Furniture revenue (after line discounts, before credit memos) {{ d.C }} Q1-Q4 {{ gross|map('money')|join(' / ') }}.
     Furniture credit memo lines by CreditMemoDate: {% for c in credits %}Q{{ c.q }} {{ c.lines|count }} lines {{ c.amount|money }}{{ '; ' if not loop.last }}{% endfor %}
     ({{ credit_lines|count }} lines, {{ credit_total|money }}). Net: {{ net|map('money')|join(' / ') }}. No unmatched rows. {{ earlier|count }} credit memo lines dated in
     {{ d.C }}, across the item groups and {{ earlier_furniture|count }} of them Furniture, reverse invoices from earlier years. For this schedule of
     recorded activity, assigning credits to the credit memo's date matches how the ledger records them. Assigning them to the original
     invoice's quarter answers a different question, the net result of each quarter's sales, and belongs in a separate schedule, labeled
     and reconciled to this one. Neither changes the ledger, and an adjustment to an earlier period would need accounting and transaction
     evidence. The credits are small relative to revenue and do not explain the change between Q3 and Q4. -->
