<!-- Instructor notes, Exercise 16.2 (SQL; Chapter 12 L5-L6): by InvoiceDate, {{ n_prior }} invoices were delivered in the prior year: {{ g[0].n }}
     invoiced in January {{ g[0].year }} for December {{ g[0].year - 1 }} deliveries and {{ g[1].n }} in January {{ g[1].year }} for December {{ g[1].year - 1 }} deliveries (SubTotal {{ sub|money }}
     together). Chapter 12, by GL posting date, counts {{ posted[0] }} and {{ posted[1] }}: {{ odd.number }} is dated in {{ odd.dated }} but posted {{ odd.posted }},
     and it shipped on {{ odd.shipped }}, so by posting date it joins {{ odd.joins }} (the revenue cutoff error of Chapter 6). The {{ unbilled }}
     shipment lines never invoiced are all December {{ d.C }} deliveries (standard cost {{ cost|money }}). {{ n_before }} invoices are dated in a year
     before their delivery ({{ before|join(', ') }}), a different direction, not asked here. -->
