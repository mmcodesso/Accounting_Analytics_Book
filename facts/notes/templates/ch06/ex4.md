<!-- Instructor notes, Exercise 6.4: Furniture margin {{ q3|money }} (Q3) to {{ q4|money }} (Q4), change {{ change|money }}. Product-type bridge:
     price {{ '+' if price > 0 }}{{ price|money }}, cost {{ '+' if cost > 0 }}{{ cost|money }}, volume {{ '+' if volume > 0 }}{{ volume|money }}, mix {{ '+' if mix > 0 }}{{ mix|money }} (sums exactly). The cost effect is not zero because each type's
     average standard cost per unit depends on which of its items were sold: {{ top.code }} ({{ top.plural }}) price per unit {{ top.p3|money }} to {{ top.p4|money }} and cost per unit
     {{ top.c3|money }} to {{ top.c4|money }}, as cheaper {{ top.plural }} made up more of the quarter; {{ same|join(', ') }}, and others move the same way. At this level, within-type item
     mix appears as price and cost; the price effect also contains the promotional discount (about {{ promotions|num }} at this level). Units by type
     Q3 to Q4: {% for t, a, b in fell %}{{ t }} {{ a|num(2) }} to {{ b|num(2) }}{{ ' and ' if not loop.last }}{% endfor %} fell; {% for t, a, b in rose %}{{ t }} {{ a|num(2) }} to {{ b|num(2) }}{{ ' and ' if not loop.last }}{% endfor %} rose. Tutorial
     6.3's Furniture-level bridge is the better headline because each of its effects has one meaning (cost zero, mix at the item level),
     with the product-type view as supporting detail for the sales team. -->
