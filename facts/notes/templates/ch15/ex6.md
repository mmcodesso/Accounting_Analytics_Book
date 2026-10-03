<!-- Instructor notes, Exercise 15.6 (SQL): direct lines that join both an operation and a clock entry: {{ both|count }}. Disagreements by year
     (lines / of / hours): {% for y in years %}{{ y.year }} {{ y.differ|count }} / {{ y.lines|count }} / {{ y.hours|num(1) }}; {% endfor %}{{ total|count }} in
     all. {{ d.C }} matrix (hours): {{ m[0].label }} operations clocked at {{ m[0].label }} {{ m[0].diag|num(1) }}{% for n, h in m[0].off %}, {{ 'at ' if loop.first }}{{ n }} {{ h|num(1) }}{% endfor %}; {{ m[1].label }} operations at {{ m[1].label }} {{ m[1].diag|num(1) }}; {{ m[2].label }} operations at {{ m[2].label }} {{ m[2].diag|num(1) }}, at {{ m[2].off[0][0] }}
     {{ m[2].off[0][1]|num(1) }}; {{ m[3].label }} at {{ m[3].label }} {{ m[3].diag|num(1) }}; {{ m[4].label }} at {{ m[4].label }} {{ m[4].diag|num(1) }}, at {{ m[4].off[0][0] }} {{ m[4].off[0][1]|num(1) }}. After the operation's end: {{ late_differ|count }} of the {{ differ|count }} disagreeing
     lines ({{ (late_differ / differ)|pct(0) }}) against {{ late_all|count }} of {{ now|count }} direct lines ({{ (late_all / now)|pct(0) }}), so the disagreement concentrates in the late time of Chapter 12. Indirect
     {{ d.C }} by clock work center: {% for n, h in indirect %}{{ n }} {{ h|num(1) }}{{ ', ' if not loop.last }}{% endfor %}. Conclusion:
     the operation path answers "what work was the time charged to"; the clock path "where the employee was"; neither alone supports
     the Packing finding, which needs corroboration (Chapter 12). -->
