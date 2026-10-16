<!-- Instructor notes, Exercise 15.6 (SQL): direct lines that join both an operation and a clock entry: {{ both|count }}. Disagreements by year
     (lines / of / hours): {% for y in years %}{{ y.year }} {{ y.differ|count }} / {{ y.lines|count }} / {{ y.hours|num(1) }}; {% endfor %}{{ total|count }} in
     all. {{ d.C }} matrix (hours; the first row in full, the others with their largest off-diagonal cell): {{ m[0].label }} operations clocked at {{ m[0].label }} {{ m[0].diag|num(1) }}{% for n, h in m[0].off %}, {{ 'at ' if loop.first }}{{ n }} {{ h|num(1) }}{% endfor %}{% for r in m[1:] %}; {{ r.label }} operations at {{ r.label }} {{ r.diag|num(1) }}{% if r.off %}, at {{ r.off[0][0] }} {{ r.off[0][1]|num(1) }}{% endif %}{% endfor %}.
     After the operation's end: {{ late_differ|count }} of the {{ differ|count }} disagreeing
     lines ({{ (late_differ / differ)|pct }}) against {{ late_direct|count }} of all {{ direct|count }} direct lines of {{ d.C }} ({{ (late_direct / direct)|pct(2) }}); the {{ untested|count }} without an operation cannot be tested, and among the {{ now|count }} lines that join both
     paths the share is {{ (late_all / now)|pct(2) }}. Accept either denominator when it is named. The disagreement concentrates in the late time of Chapter 12. Indirect
     {{ d.C }} by clock work center: {% for n, h in indirect %}{{ n }} {{ h|num(1) }}{{ ', ' if not loop.last }}{% endfor %}. Conclusion:
     the operation path answers "what work was the time charged to"; the clock path "where the time clock placed the employee"; neither alone supports
     the Packing finding, which needs corroboration (Chapter 12). -->
