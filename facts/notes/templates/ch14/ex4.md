{%- macro s(x) -%}{{ '+' if x >= 0 }}{{ x|money }}{%- endmacro -%}
<!-- Instructor notes, Exercise 14.4 (reference model through the local engine; Bridge Check 0 in every row): Furniture {{ d.C }} by quarter
     (Margin PQ, volume, mix, price lists, promotions, margin): {% for q in quarters %}{{ q.label }} {{ q.pq|money }}, {{ s(q.volume) }}, {{ s(q.mix) }}, {{ s(q.lists) }}, {{ s(q.promotions) }},
     {{ q.gm|money }}{{ '; ' if not loop.last }}{% endfor %}
     (Chapter 6's bridge). (3) Each item has one StandardCost, so cost per unit changes only with the mix, which the mix effect
     already includes (Chapter 6). (5) Q3: fewer units than Q2 (volume) and the first month of promotion {{ promotion }} ({{ start_month }}) together; Q4:
     volume, mix and price lists small, promotions larger than the whole decline. (6) Lighting {{ d.C }}-Q4: {{ lighting.pq|money }} to {{ lighting.gm|money }};
     volume {{ s(lighting.volume) }}, mix {{ s(lighting.mix) }}, price lists {{ s(lighting.lists) }}, promotions {{ s(lighting.promotions) }}: a volume decline, not a price effect. -->
