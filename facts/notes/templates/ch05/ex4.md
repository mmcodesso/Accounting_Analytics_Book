<!-- Instructor notes, Exercise 5.4: order-to-invoice lag across all {{ invoices|count }} invoices: median {{ median }} days, mean {{ mean|num(1) }} (90th percentile {{ p90 }} days);
     the mean exceeds the median because a minority of orders take much longer to invoice (right skew). Fiscal {{ d.C }} by quarter, invoices and
     average lag: {% for x in quarters %}Q{{ x.q }} {{ x.invoices|count }}, {{ x.mean|num(1) }}{{ ' days' if loop.first }}{{ '; ' if not loop.last }}{% endfor %} (medians {% for x in quarters %}{{ x.median }}{{ ', ' if not loop.last }}{% endfor %}): stable. Promotion lines invoiced after the end date:
     {% for code, late, total in promos %}{{ code }} {{ late|count }} of {{ total|count }}{{ ', ' if not loop.last }}{% endfor %}. Promotions {{ every }} have
     every line after the end date because their dates are wrong (a one-day promotion, and two whose end dates precede their start dates);
     these are left for the audit analytics chapter. Revenue belongs to the invoice date; the order date explains the price. {{ negative }} invoices
     have a negative lag (Exercise 5.2). -->
