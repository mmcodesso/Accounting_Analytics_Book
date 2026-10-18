<!-- Instructor notes, Exercise 4.5: {{ shipments|count }} shipments. Blank TrackingNumber: {{ blank|count }} ({{ blank_delivered|count }} Delivered, {{ blank_transit|count }} In Transit). In Transit: {{ transit|count }} shipments
     from every year of the data ({% for y, n in transit_by_year %}{{ y }}: {{ n|count }}{{ ', ' if not loop.last }}{% endfor %}). With ReviewDate {{ review }}, {{ late|count }} In Transit shipments have a DeliveryDate
     before the review date{% if others %} ({% if others == 1 %}the other is{% else %}the other {{ others_word }} are{% endif %} due {% if after_review == 0 %}on the review date itself{% elif on_review == 0 %}after it{% else %}on it or after it, {{ on_review|count }} on it and {{ after_review|count }} after{% endif %}){% endif %}; with ReviewDate {{ review2 }} the count is {{ late2|count }}. A slicer on Status shows all {{ transit|count }} In Transit
     shipments, so it confirms the count only together with a filter on DeliveryDate before the review date. All {{ blank_transit|count }} In Transit
     shipments with a blank tracking number are in both categories. No ShipmentDate or DeliveryDate is blank. If DeliveryDate records the
     delivery, Status and DeliveryDate conflict, a consistency and timeliness problem (Chapter 2). If it is an expected date, the
     records show the shipments past it, and they need follow-up. Carrier evidence and the status history come before either
     conclusion. The run at {{ review2 }} is a sensitivity of the same extract, not the status on that date. The blank tracking numbers
     are a completeness problem. -->
