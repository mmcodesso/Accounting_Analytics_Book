<!-- Instructor notes, Exercise 9.3: {{ n }} manufactured items ({% for g, k in groups %}{{ g }} {{ k }}{{ ', ' if not loop.last }}{% endfor %}). Material cost =
     StandardCost - StandardConversionCost, from {{ material_low|money }} to {{ material_high|money }}. The component check returns no rows: labor + variable overhead + fixed
     overhead = conversion for every item, and no component is NULL, so no item escapes the test (a NULL would make the comparison
     unknown, not true). Labor rate per standard hour ranges from {{ rate_low|money }} to {{ rate_high|money }}, so rates are item-specific, not one plant
     rate. Highest conversion cost: {% for t in top %}{{ t.code }}{% if loop.first %} {{ t.name }}{% endif %} ({{ t.cost|money }}){{ ', ' if not loop.last }}{% endfor %};
     the top ten are {{ top_group }}. -->
