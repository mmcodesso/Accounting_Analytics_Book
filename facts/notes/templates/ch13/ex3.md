<!-- Instructor notes, Exercise 13.3: fiscal {{ d.C }} promotion lines and discounts by month: {% for p in promos %}{{ p.short }} ({{ p.id }}{{ p.when }})
     {% if p.style == 'one' %}{{ p.months[0].name }} {{ p.months[0].n }} lines, {{ p.disc|money }}{% elif p.style == 'total' %}{% for m in p.months %}{{ m.name }} {{ m.n }}{{ ', ' if not loop.last }}{% endfor %} ({{ p.disc|money }}){% else %}{% for m in p.months %}{{ m.name }} {{ m.n }} ({{ m.disc|money }}){{ ', ' if not loop.last }}{% endfor %}{% endif %}{{ '; ' if not loop.last }}{% endfor %}.
     Total {{ total|money }}. By item group (requirement 5): {% for g, v in groups %}{{ g }} {{ v|money }}{% if loop.first %} ({{ (v / total)|pct }}){% endif %}{{ ', ' if not loop.last }}{% endfor %}{% for g in no_disc %}; {{ g }} none{% endfor %}.
     Promotions {% for p in one_group %}{{ p.id }}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{% endfor %} each stayed in one group ({% for p in one_group %}{{ p.id }} {{ p.groups[0] }}{{ ', ' if not loop.last }}{% endfor %}), while the segment
     promotions {{ spread|map(attribute='id')|join(' and ') }} reached {{ spread[0].groups[:-1]|join(', ') }}, and {{ spread[0].groups[-1] }}, so a promotion's name does not say where its discounts fell.
     The (Blank) row is the {{ blank|count }} lines without a promotion ({{ blank_rev|money }} of revenue, zero discount), a meaningful
     blank (Chapter 5), not a broken key. Lines invoiced after the end date in {{ d.C }}: {% for p in current %}promotion {{ p.id }}, {{ p.after }} lines in {{ p.after_months|join(' and ') }}{% if loop.first %}
     (all ordered within the promotion's dates, Chapter 5){% endif %}; {% endfor %}promotions {{ earlier|map(attribute='id')|join(' and ') }} ({{ d.P }} promotions) all
     {{ d.C }} lines; promotion {{ invalid.id }} ({{ invalid.collection }}) ends {{ invalid.end }} before its {{ invalid.start }} start, so all its {{ invalid.n }} lines fall after the end date: a
     master-data error, since its lines were ordered in {{ invalid.ordered|join(' and ') }} (the Part II case). The discount is applied when the order is
     priced, so invoicing later does not remove it. The report cannot show whether the promotions paid off: that needs margin and
     volume lift (Chapter 7, Part II case). -->
