<!-- Instructor notes, Exercise 13.3: fiscal {{ d.C }} promotion lines and discounts by month: {% for p in promos %}{{ p.short }} ({{ p.id }}{{ p.when }})
     {% if p.style == 'one' %}{{ p.months[0].name }} {{ p.months[0].n }} lines, {{ p.disc|money }}{% elif p.style == 'total' %}{% for m in p.months %}{{ m.name }} {{ m.n }}{{ ', ' if not loop.last }}{% endfor %} ({{ p.disc|money }}){% else %}{% for m in p.months %}{{ m.name }} {{ m.n }} ({{ m.disc|money }}){{ ', ' if not loop.last }}{% endfor %}{% endif %}{{ '; ' if not loop.last }}{% endfor %}.
     Total {{ total|money }}. The (Blank) row is the {{ blank|count }} lines without a promotion ({{ blank_rev|money }} of revenue, zero discount), a meaningful
     blank (Chapter 5), not a broken key. Lines invoiced after the end date in {{ d.C }}: {% for p in current %}promotion {{ p.id }}, {{ p.after }} lines in {{ p.after_months|join(' and ') }}{% if loop.first %}
     (all ordered within the promotion's dates, Chapter 5){% endif %}; {% endfor %}promotions {{ earlier|map(attribute='id')|join(' and ') }} ({{ d.P }} promotions) all
     {{ d.C }} lines; promotion {{ invalid.id }} ({{ invalid.collection }}) ends {{ invalid.end }} before its {{ invalid.start }} start, so all its {{ invalid.n }} lines fall after the end date: a
     master-data error, since its lines were ordered in {{ invalid.ordered|join(' and ') }} (the Part II case). The discount is applied when the order is
     priced, so invoicing later does not remove it. The report cannot show whether the promotions paid off: that needs margin and
     volume lift (Chapter 7, Part II case). -->
