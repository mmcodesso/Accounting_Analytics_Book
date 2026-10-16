<!-- Instructor notes, Exercise 12.3: {{ no_op|count }} direct entries ({{ no_op_hours|num(2) }} hours) have no valid operation, a NULL key
     or one that matches no operation, and stay in Requirement (1) as a group of their own, outside the ratios. Counting only the
     time recorded while the operation was open (on or before its ActualEndDate; no direct time with an operation is dated before
     its ActualStartDate), every work center falls below plan in
     fiscal {{ d.C }}: {% for c in centers %}{{ c }} {{ now[loop.index0]|num(2) }}{{ ', ' if not loop.last }}{% endfor %} (against all-hours ratios of
     {{ now_all|map('num', 2)|join(', ') }}; operations that ended by {{ cutoff }}, the last day with time records, as in
     Tutorial 11.2, with both ratios dividing unrounded hours). In {{ d.F }} the
     in-window ratios were {{ then|map('num', 2)|join(', ') }}{% if above %}, and {% for a in above %}{{ a.center }} was above plan even on that time in {% for y in a.years %}{{ y.year }}{{ ' and ' if not loop.last }}{% endfor %} ({% for y in a.years %}{{ y.ratio|num(2) }}{{ ' and ' if not loop.last }}{% endfor %}){{ ', ' if not loop.last }}{% endfor %}, so the below-plan reading belongs to {{ d.C }}{% endif %}. The Packing excess disappears, which shows how much of it was time dated after the
     operation ended; Packing is the last operation of every routing, so late time lands there. A ratio below plan on the dated
     time does not show efficiency by itself, because the hours left out may still be work to reassign or redate. January to {{ months_to }} {{ d.F }}: work orders released
     {{ released|map('count')|join(', ') }}; units completed {{ completed|map('num')|join(', ') }}; manufactured units shipped {{ shipped|map('num')|join(', ') }}. From {{ build_from }} to {{ build_to }} the plant completed about {{ surplus|num }} more units than it shipped, an
     inventory build consistent with the little indirect time from {{ quiet_from }} to {{ quiet_to }}, although {{ build_to }} already
     had {{ build_end_indirect|num }} indirect hours. When releases and completions fell to the rate of shipments from {{ after }}, the same
     {{ staff }} employees kept recording their hours, and more of them were recorded as indirect time. The build is a plausible
     explanation, to confirm with the production schedules and the way hours were assigned. The late-recorded share was {{ late_low|num(2) }}-{{ late_high|num(2) }} a month through
     {{ before }} {{ before_year }} and {{ late_first|num(2) }} in {{ first }} {{ first_year }}, the month surge days began in earnest. Operation-level efficiency cannot be measured until time is
     recorded against open operations. The plant-level measure of Chapter 11 does not depend on which operation the time is
     charged to, although its hours and the standards still need corroboration. -->
