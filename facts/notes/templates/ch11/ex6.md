<!-- Instructor notes, Exercise 11.6: bands of $50 from 4,700: {% for n in bands %}{{ n }}{% if loop.index == 6 %} (4,950-4,999.99){% elif loop.index == 7 %} (5,000-5,049.99){% endif %}{{ ', ' if not loop.last }}{% endfor %}. The
     band just below 5,000 holds {{ bands[5] }}, against {{ bands[4] }} just below it and {{ bands[6] }} just above{% if twice %}, at least twice either neighbor{% endif %}; the counts are a screen, not evidence of splitting by themselves. Two runs of three consecutive requisitions of {{ amount|money }}, each on January 1:
     {% for r in runs %}{{ r.first }} to {{ r.last }} ({{ r.date }}, requesters {{ r.requesters|join(', ') }}){{ ' and ' if not loop.last }}{% endfor %}. In each
     run, two requisitions have no approver (IDs {{ unapproved|join(', ') }}) and the third was approved by employee {{ cfo }}, the chief financial
     officer; all six were converted to purchase orders. The unapproved ones are among the six of Exercise 2.5, and all six of those, the only requisitions without an approver, fall just below 5,000 ({{ low|money }} to {{ high|money }}). LAG and LEAD flag only the middle row of each run ({{ middles|join(' and ') }}); to list all three, keep the flagged rows in a CTE with
     LAG(RequisitionID) and LEAD(RequisitionID) and join back to the requisitions whose RequisitionID lies between them, or flag
     the first and last rows too with offsets of 2. The approval limits in
     Employee are 0, 5,000 (two production employees), 25,000, and 250,000. -->
