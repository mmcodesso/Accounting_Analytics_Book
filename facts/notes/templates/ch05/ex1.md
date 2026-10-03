<!-- Instructor notes, Exercise 5.1: gross Furniture revenue {{ d.C }} Q1-Q4 {{ gross|map('money')|join(' / ') }}.
     Furniture credit memo lines by CreditMemoDate: {% for c in credits %}Q{{ c.q }} {{ c.lines|count }} lines {{ c.amount|money }}{{ '; ' if not loop.last }}{% endfor %}
     ({{ credit_lines|count }} lines, {{ credit_total|money }}). Net: {{ net|map('money')|join(' / ') }}. No unmatched rows. {{ earlier|count }} credit memo lines dated in
     {{ d.C }} reverse invoices from earlier years. For a margin comparison by quarter, assigning credits to the credit memo's date matches how
     the ledger records them; assigning them to the original invoice's quarter measures the net sale, but restates closed periods. Either
     is defensible if stated. The credits are small relative to revenue and do not explain the change between Q3 and Q4. -->
