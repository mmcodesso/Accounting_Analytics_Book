<!-- Instructor notes, Exercise 13.5: Profile_Lines ({{ n|count }} rows): PromotionID empty {{ promo|count }} ({{ (promo / n)|pct }}) on the entire data set, {{ top_empty|pct(0) }} on
     the top 1,000; PriceOverrideApprovalID empty {{ override|count }} ({{ (override / n)|pct }}) against {{ override_top }} of 1,000; PriceListLineID and ShipmentLineID empty on {{ base }}
     lines ({{ (base / n)|pct }}, the Base List design-service lines) against {{ base_top }} of 1,000; PricingMethod {{ methods }} distinct values on both bases; Discount {{ discounts }}
     distinct on the entire set, {{ discounts_top }} (zero) on the top 1,000; Quantity is fractional on {{ fractional|count }} lines (Chapter 5's validity check).
     Profile_Invoices ({{ invoices|count }}): PaymentDate empty on {{ unpaid }} (open invoices) against {{ unpaid_top }} of 1,000; Status {{ statuses|length }} distinct ({{ statuses|join(', ') }}) against {{ top_statuses|length }} ({{ top_statuses|join(', ') }}) on the top 1,000, because the earliest invoices were all paid. Profile_Items ({{ items }}; {{ sellable }}
     with a ListPrice): ListPrice empty on {{ unpriced }} items bought, not sold; CollectionName empty on {{ blank }} of the sellable items (all {{ acc }} Accessories,
     {{ fur }} Furniture, the {{ svc }} services). Profile_Customers ({{ customers }}): no empty values; CustomerName has {{ names }} distinct values ({{ dup|join(' and ') }}
     twice). The first rows are the earliest records, before promotions, overrides, and unpaid invoices existed. Meaningful blanks:
     PromotionID (no promotion), PaymentDate (unpaid), PriceListLineID on Base List lines; follow-up: CollectionName on the {{ fur_word }}
     Furniture items (the Part II case found one of them, {{ item }}, ordered under the {{ collection }} promotion). -->
