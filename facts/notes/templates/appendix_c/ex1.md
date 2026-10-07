<!-- Instructor notes, Exercise C.1: fiscal {{ C }} by quarter (lines, revenue, list amount, discounts):
     {% for q in quarters %}Q{{ q.q }} {{ q.n|count }}, {{ q.rev|money }}, {{ q.list|money }}, {{ q.disc|money }}{{ '; ' if not loop.last }}{% endfor %}.
     The quarters add up to the Validation row: {{ year.n|count }} lines, {{ year.rev|money }}, {{ year.list|money }}, {{ year.disc|money }} (the discounts may differ from
     the sum of the rounded quarters by a cent). (4) Q{{ top.q }} carries {{ share|pct(1) }} of the year's discounts: {% for name, v in top.promos %}{{ name }} {{ v|money }}{{ '; ' if not loop.last }}{% endfor %}.
     The {{ top.promos[0][0] }} ran in September and October, but its orders were invoiced through December. (5) A query in Tests.dax does not
     change when a page is edited, and DAX query view in the browser discards its tabs on close. -->
