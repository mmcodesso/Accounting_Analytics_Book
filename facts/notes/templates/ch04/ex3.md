<!-- Instructor notes, Exercise 4.3: {{ items|count }} finished goods. The {{ services }} design services have a StandardCost of 0, so their MarginPct is 100 percent.
     Average UnitMargin / average MarginPct: {% for g in groups %}{{ g.name }} {{ g.margin|money }} / {{ g.pct|pct }}{{ '; ' if not loop.last }}{% endfor %}. MarginPct ranges from {{ low|pct }} to {{ high|pct }}, so no item is below 30 percent; {{ below|count }} items are below 0.45 ({% for name, n in below_by %}{{ name }} {{ n|count }}{{ ', ' if not loop.last }}{% endfor %}). {{ top_group }} has the highest average list-price margin per unit but the lowest average percentage. The group figures are simple
     averages that count each item once, whatever it sold, so they are not the groups' margins on sales. The design services change
     neither the count below the target nor the group averages, because their MarginPct is 100 percent and their ItemGroup is
     Services, so a formula without the ItemType condition happens to give the same results here; the condition is still needed,
     because a filter does not limit COUNTIFS or AVERAGEIFS. List-price margin is not the realized margin.
     Most sales are billed at price-list prices below list and some carry promotional discounts, which lower it, and StandardCost is a
     standard, not an actual cost, so actual costs can differ from it in either direction. -->
