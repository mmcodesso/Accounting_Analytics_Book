<!-- Instructor notes, Exercise 13.4: fiscal {{ d.C }} by segment: {% for s in segments %}{{ s.name }} {{ s.rev|money }} ({{ s.customers }}{{ ' customers with revenue' if loop.first }}; {{ 'discounts ' if loop.first }}{% if s.disc %}{{ s.disc|money }}{% else %}0, services carry no promotion{% endif %}){{ ',
     ' if not loop.last }}{% endfor %}. By region: {% for r, v in regions %}{{ r }} {{ v|money }}{{ ', ' if not loop.last }}{% endfor %}. Largest cell: {{ cell.segment }}-{{ cell.region }} {{ cell.rev|num }}. Cognitive fit: the bar chart for the comparison
     (a spatial task), the matrix for the exact figures (a symbolic task). Clicking a bar cross-highlights the matrix by default
     (or filters it) and filters the card; setting the matrix to None keeps the full table visible while the card answers for one
     segment. A restriction such as excluding the Design Services segment from a merchandise page, or keeping only sellable items,
     belongs to the report and can sit in the Filters pane, provided the title says so. -->
