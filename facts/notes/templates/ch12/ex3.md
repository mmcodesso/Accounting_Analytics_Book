<!-- Instructor notes, Exercise 12.3: counting only the time recorded while the operation was open, every work center falls below plan in
     fiscal {{ d.C }}: {% for c in centers %}{{ c }} {{ now[loop.index0]|num(2) }}{{ ', ' if not loop.last }}{% endfor %} (against all-hours ratios of
     {{ now_all|map('num', 2)|join(', ') }}; operations that ended by {{ cutoff }}, the last day with time records, as in Tutorial 11.2). In {{ d.F }} the
     in-window ratios were {{ then|map('num', 2)|join(', ') }}. The Packing excess disappears, which shows that it came from time charged after the
     operation ended; Packing is the last operation of every routing, so late time lands there. January to July {{ d.F }}: work orders released
     {{ released|map('count')|join(', ') }}; units completed {{ completed|map('num')|join(', ') }}; manufactured units shipped {{ shipped|map('num')|join(', ') }}. From {{ build_from }} to {{ build_to }} the plant completed about {{ surplus|num }} more units than it shipped, an
     inventory build that kept every hour on work orders; when releases and completions fell to the rate of shipments from July, the same
     {{ staff }} employees kept their hours, and the unassigned days became indirect time. The late-recorded share was {{ late_low|num(2) }}-{{ late_high|num(2) }} a month through
     {{ before }} {{ before_year }} and {{ late_first|num(2) }} in {{ first }} {{ first_year }}, the month surge days began in earnest. Operation-level efficiency cannot be measured until time is
     recorded against open operations; the plant-level measure of Chapter 11 is unaffected. -->
