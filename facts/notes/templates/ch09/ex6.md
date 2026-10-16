{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 9.6: {{ n_labor }} Direct Manufacturing labor rows have no WorkOrderOperationID: LaborTimeEntryIDs {% for r in labor %}{{ r.id }} (employee
     {{ r.employee }}, work order {{ r.work_order }}, {{ r.date }}, {{ r.hours|num(2) }} hours){{ sep(loop) }}{% endfor %}; employee{{ 's' if employees|length > 1 }} {% for e in employees %}{{ e }}{{ sep(loop) }}{% endfor %} {{ 'are' if employees|length > 1 else 'is' }} {{ title }}. They are planted anomalies (invalid direct labor operation
     link). ClockStatus values: {% for s, k in clock %}{{ s }} ({{ k|count }}){{ ' and ' if not loop.last }}{% endfor %}. {{ n_missing }} entries have no ClockOutTime, all for employee {{ clock_employee }} ({{ clock_title }}) on January 1 of {{ d.F }}, {{ d.P }}, and {{ d.C }}, with Pending status (planted missing clock-out). {{ terminated }} employees have a
     TerminationDate; all are Terminated with IsActive 0, so the three columns agree. The direct rows are charged to their work orders, whose
     closes count them in actual direct labor, but they cannot be traced to an operation, so an operation-level comparison leaves them
     out. The missing link does not show that the hours are wrong. The missing clock-outs mean recorded hours without a complete time
     record. Their linked labor records are NonManufacturing, with no work order, so these tests show a gap in the time and payroll
     support, not an effect on manufacturing cost, and whether the hours were paid is a payroll question, which Chapter 12 tests. -->
