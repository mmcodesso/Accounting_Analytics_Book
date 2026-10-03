<!-- Instructor notes, Exercise 4.5: {{ shipments|count }} shipments. Blank TrackingNumber: {{ blank|count }} ({{ blank_delivered|count }} Delivered, {{ blank_transit|count }} In Transit). In Transit: {{ transit|count }} shipments
     from every year of the data ({% for y, n in transit_by_year %}{{ y }}: {{ n|count }}{{ ', ' if not loop.last }}{% endfor %}). With ReviewDate {{ review }}, {{ late|count }} In Transit shipments have a DeliveryDate
     before the review date (the other is due on the review date itself); with ReviewDate {{ review2 }} the count is {{ late2|count }}. All {{ blank_transit|count }} In Transit
     shipments with a blank tracking number are in both categories. No ShipmentDate or DeliveryDate is blank. The Status conflict is a
     consistency and timeliness problem (Chapter 2); the blank tracking numbers are a completeness problem. -->
