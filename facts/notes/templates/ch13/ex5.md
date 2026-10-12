<!-- Instructor notes, Exercise 13.5: empty values in every column that has any, on the top 1,000 rows against the entire data
     set (each share is of the rows on its basis):
     {% for t in census %}{{ t.query }} ({{ t.n|count }} rows{% if t.n <= 1000 %}, all of them within the top 1,000, so the two bases agree{% endif %}): {% for c in t.columns %}{{ c.name }} {% if t.n > 1000 %}{{ c.top|count }} ({{ (c.top / t.top_n)|pct }}) against {% endif %}{{ c.full|count }} ({{ (c.full / t.n)|pct }}){{ '; ' if not loop.last }}{% else %}no empty values{% endfor %}.
     {% endfor %}No other column has an empty value. Distinct values: PricingMethod {{ methods }} on both bases; Discount {{ discounts_top }} (zero) on the
     top 1,000 against {{ discounts }}; Status {{ top_statuses|length }} ({{ top_statuses|join(', ') }}) against {{ statuses|length }} ({{ statuses|join(', ') }}). The changes that matter are PromotionID, PaymentDate,
     Discount, and Status; the blanks of {{ small[:-1]|join(', ') }}, and {{ small[-1] }} move by under one percentage point (overrides on {{ ((1000 - override_top) / 1000)|pct }}
     of the top 1,000 against {{ ((n - override) / n)|pct }} overall). The first rows are almost all the earliest records (lines to {{ first_line }}, invoices to {{ first_invoice }};
     only {{ later_lines }} later lines and {{ later_invoices }} later invoices are dated earlier), before the first promotion and with almost every invoice paid.
     Quantity is fractional on {{ fractional|count }} lines (Chapter 5's validity check, not an empty value). PriceListLineID and ShipmentLineID are empty on the
     same {{ base }} Base List lines, the design services, which ship nothing. PaymentDate's {{ unpaid }} blanks are {{ unpaid_open }} open invoices and {{ unpaid_settled }} Settled.
     ListPrice is empty on {{ unpriced }} items bought, not sold. CollectionName is empty on {{ coll_raw }} of the {{ items }} items, {{ blank }} of them among the {{ sellable }} sellable
     (all {{ acc }} Accessories, {{ fur }} Furniture, the {{ svc }} services) and the rest bought. Customer has no empty values, but CustomerName has {{ names }} distinct
     values for {{ customers }} customers ({{ dup|join(' and ') }} twice). Meaningful blanks: PromotionID (no promotion), PaymentDate on the open
     invoices, PriceListLineID and ShipmentLineID on the design services; follow-up: PaymentDate on the Settled invoices, and
     CollectionName on the {{ fur_word }} Furniture items (the Part II case found one of them, {{ item }}, ordered under the {{ collection }} promotion).
     The other Item blanks (the routing, the accounts, and the product attributes) depend on each item's type and supply mode,
     so read them by those before calling them errors. Accept other reasoned classifications, and a memo whose figures sit
     in an attached table. -->
