<!-- Instructor notes, Exercise 5.2: {{ w_prefix }} invoices carry the next year's number prefix: {% for n, dt in prefix %}{{ n }} ({{ dt }}){{ ', ' if not loop.last }}{% endfor %}. {{ w_order|capitalize }} invoices are dated
     before their order: {% for n, dt, od in before_order %}{{ n }} ({{ dt }}, order {{ od }}){{ ', ' if not loop.last }}{% endfor %}. These {{ w_both }} are exactly the {{ w_both }} invoices dated before their first shipment in Tutorial 2.1. Together they suggest
     backdated invoices: numbered in the later period but dated earlier, which is a revenue cutoff risk. Order and shipment numbers show no
     such mismatch. Evidence to request: the invoice creation logs, the shipping documents, and customer acknowledgments. -->
