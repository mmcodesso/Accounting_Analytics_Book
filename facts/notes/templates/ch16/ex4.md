{%- set names = {'JE': 'journal entries', 'PO': 'purchase orders', 'PR': 'payroll'} -%}
<!-- Instructor notes, Exercise 16.4 (AM16 reference model, checked in Desktop 2.158's engine): exceptions / population / rate per
     1,000 by year: {% for p, rows in table %}{{ names[p] }} {% for k, pop, r in rows %}{{ k }} / {{ pop|count }} / {{ r|num(2) }}{{ ', ' if not loop.last }}{% endfor %}{{ '; ' if not loop.last }}{% endfor %}. (1) Population
     uses SELECTEDVALUE ( Tests[Process] ), blank when several processes are in context, so a rate across processes, which
     would mix populations, is never shown. (2) CALCULATE ( [Exceptions], Exceptions[Disposition] <> "Expected", Tests[TestID]
     <> "PR SelfApproved" ) divided by [Population], times 1,000 (a blank Disposition is not equal to "Expected", so open
     exceptions stay in): journal entries {{ unexplained.JE|map('num', 2)|join(', ') }} (the two closes a year removed); payroll {{ unexplained.PR|map('num', 2)|join(', ') }};
     purchase orders unchanged. (4) the count rose by a third ({{ po_n[1] }} to {{ po_n[2] }}) while the rate barely moved ({{ po_r[1]|num(2) }} to {{ po_r[2]|num(2) }}), because the
     number of orders grew by about {{ growth|pct(0) }}; from {{ d.F }} the rate fell by two-thirds while orders more than doubled. (5) Journal
     entries are the process to watch: their unexplained rate fell in {{ d.P }} and rose in {{ d.C }}, mostly because of single
     documents that fail several tests (the opening entry's {{ opening }} in {{ opening_year }}, the debt reclassifications' {{ reclass }} each in {{ reclass_years|join(' and ') }}),
     while {% for name, v in stable %}{{ name }} ({{ v|join(', ') }}){% if loop.revindex == 2 %}, and {% elif not loop.last %}, {% endif %}{% endfor %} barely move; payroll's unexplained
     exceptions are {{ pr_left }} a year, so its rate is almost entirely the design finding. -->
