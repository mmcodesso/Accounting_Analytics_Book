<!-- Instructor notes, Exercise 9.4: {{ n }} work orders have a NULL ClosedDate: {% for s, k in status.items() %}{{ s }} {{ k }}{{ ', ' if not loop.last }}{% endfor %} (completed but not
     closed). Every WorkOrderNumber carries the year of its ReleasedDate, and {% if by_year|length == 1 %}every open work order is a {{ by_year[0][0] }} work order{% else %}the open work orders are {% for y, k in by_year %}{{ y }} work orders ({{ k }}){{ ' and ' if not loop.last }}{% endfor %}{% endif %} (released
     {{ released_low }} to {{ released_high }}); COALESCE shows not completed for the {{ not_completed }} released or in progress and a date for the {{ status['Completed'] }} completed. Due on or before {{ end }}: {{ due }} ({% for s, k in due_status %}{{ s }} {{ k }}{{ ', ' if not loop.last }}{% endfor %}). The oldest is {{ oldest.number }}, released {{ oldest.released }}
     and due {{ oldest.due }}, still marked Released in the records; the next are {{ next[0].number }} (due {{ next[0].due }}) and {{ next[1].number }} (due
     {{ next[1].due }}). Hundreds of work orders are past due and still Released, but the status is not proof that work has not
     started: {{ active.n }} of the {{ released }} have material issues, production completions, and started operations in other tables{% if active.labor < active.n %}
     ({{ active.labor }} also labor time){% endif %}{% if named_active %}, including the three named above{% endif %}, which a cross-table check beyond this chapter's single-table queries
     finds (Chapter 10's joins can show it). The statuses need reconciling with production; for the others, the absence of recorded
     activity in the extract is not proof that nothing happened. Completed output on {{ completed_out }} of the open work orders, all {{ status['Completed'] }}
     Completed ones among them, has already moved its standard cost to finished goods, so only the cost not yet relieved stays in work
     in process and 1090. A variance would be recorded only if and when an order closes, and the open status does not say whether it
     will close, or how large or in which direction its variance would be. Counting needs one query per status (COUNT comes in Chapter 10). -->
