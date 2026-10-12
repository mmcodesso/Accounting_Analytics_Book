<!-- Instructor notes, Exercise 11.4: {{ employees }} employees recorded manufacturing overtime in fiscal {{ year }} (LaborType other than
     NonManufacturing, by WorkDate: {{ total|num }} hours; the payroll year of Chapter 10 gives {{ payroll|num }}). The largest totals are close together: {% for id, title, hours in top %}{% if loop.first %}employee {% endif %}{{ id }} ({{ title }}) {{ hours|num(1) }}{{ ' hours' if loop.first }}{{ ', ' if not loop.last }}{% endfor %}. Half of the overtime is reached at rank {{ half }}, half of the
     employees, so recorded overtime is spread across the employees who recorded it, about {{ weekly }} hours each for every week of
     the year (the year's total divided by 52). By job title: {% for title, n, hours in titles %}{{ title }} {{ n }}{{ ' employees' if loop.first }}, {{ hours|num }}{{ ' hours' if loop.first }} ({{ (hours / n)|num(1) }}{{ ' each' if loop.first }}){{ '; ' if not loop.last }}{% endfor %}. The claim is not supported by these totals: recorded overtime is spread across the plant's hourly employees; staffing,
     demand, approvals, and how time is captured still need to be examined before naming a cause. A
     running share needs SUM(x) OVER (ORDER BY x DESC ROWS UNBOUNDED PRECEDING) divided by SUM(x) OVER (), both taught in the
     section on window functions; ROWS matters if two employees tie. -->
