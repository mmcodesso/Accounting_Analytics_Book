<!-- Instructor notes, Exercise 7.3: {{ d.C }} revenue {{ revenue|money }} (including Services); standard cost of products {{ cost|money }}; commissions
     (GL 6290, excluding close {{ close }}) {{ commissions|money }}; contribution margin {{ cm|money }}; CM ratio {{ ratio|pct(2) }}. Fixed costs: {{ d.C }}
     operating-expense budget {{ opex|money }} less commission budget {{ budget_commission|money }} = {{ fixed|money }} (the budget is reasonable because salaries,
     rent, depreciation, and the other recurring accounts came within a few percent of actual, as Tutorial 7.2 showed). Break-even revenue
     {{ breakeven|money }}; margin of safety {{ safety|money }} ({{ safety_pct|pct }}). Adding {% for n, name, amount in added %}{{ 'and ' if loop.last }}{{ n }} {{ name }} {{ amount|money }}{{ ', ' if not loop.last }}{% endfor %} (total {{ added_total|money }}): break-even {{ breakeven2|money }}, margin of safety {{ safety2_pct|pct }}. Goal Seek for operating
     income of 4,000,000 under (4): revenue {{ goal|money }}; without the added items it would be {{ goal_without|money }}. Treating Services' design staff
     as fixed and all product standard cost as variable are further simplifications worth naming. -->
