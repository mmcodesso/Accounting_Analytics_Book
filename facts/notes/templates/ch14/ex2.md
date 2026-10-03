<!-- Instructor notes, Exercise 14.2 (the reference model related SalesInvoiceLine[ShipmentDate] inactively, with the same results):
     (3) Date and ShippedLines are already related on InvoiceDate, and only one path between two tables can be active. (4) By invoice
     date {% for v in by_invoice %}{{ v|money }}{{ '; ' if not loop.last }}{% endfor %}; by ship date {% for v in by_ship %}{{ v|money }}{{ '; ' if not loop.last }}{% endfor %}; (Blank) {{ blank|money }},
     the {{ n_services|count }} Services lines ({% for v in by_services %}{{ v|money }}{{ '; ' if not loop.last }}{% endfor %}), which have no shipment, so the inactive relationship finds no
     date for them; both columns total {{ all|money }}. {{ n_shipped|count }} lines have a shipment. (5) {{ n_cross }} lines cross a year: {% for g in late %}{{ g.lines }} lines on {{ g.invoices }} invoices
     dated {{ g.first }} to {{ g.last[5:] }} for shipments of December {{ g.ship_year }} ({{ g.amount|money }}){{ ' and ' if not loop.last }}{% endfor %}, the invoices for December deliveries posted in January (Chapter 12 counts {{ ch12.n }} invoices,
     {{ ch12.sub|money }}, for {{ d.P }} because it also includes {{ odd.number }}, which is dated in {{ d.P }} and posted on {{ odd.posted }}, and so crosses by
     posting date, not by invoice date); {% for g in early %}{{ g.lines }} lines on {{ g.numbers }}, dated {{ g.dates }} and shipped {{ g.shipped }}
     ({{ g.amount|money }}){{ ', and ' if not loop.last }}{% endfor %}, the invoices
     dated before their shipment (Chapter 12; their numbers carry the next year's prefix, Chapter 5). (6) Revenue is recognized when
     control passes, which for Charles River's goods is at shipment or delivery (every shipment is delivered in the year it ships);
     invoice-date revenue misstates the years by the late invoices, and Services have no ship date, so a ship-date report needs a rule
     for them (their invoice date). Revenue by ship date is lower in each year mainly because Services drop to (Blank). -->
