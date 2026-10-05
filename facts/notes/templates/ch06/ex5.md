<!-- Instructor notes, Exercise 6.5: flagged (over 10% and over $50,000): {% for r in flagged %}{{ r.group }} Q{{ r.q }} {{ '+' if r.diff > 0 }}{{ r.diff|money }} ({{ r.pct|spct }}){{ ', ' if not loop.last }}{% endfor %}.
     Not flagged: {% for r in missed %}{{ r.group }} Q{{ r.q }} {{ '+' if r.diff > 0 }}{{ r.diff|money }} ({{ r.pct|spct }}){{ ', the ' ~ largest ~ ' dollar difference, and ' if loop.first }}{% endfor %}. A percentage test
     alone misses large dollar differences in {{ lines }}; a tolerable amount based on materiality, or an expectation that
     reflects known changes such as the promotion, would treat them differently. Prior-year revenue is a weak expectation because it
     ignores growth and known events, which students may note. Follow-up examples: {{ example.group }} Q{{ example.q }}, the largest flagged
     difference, is mostly {{ example.driver }} (units {{ example.units|spct }}, price per unit {{ example.price|spct }}), so the evidence is {% if example.driver == 'volume' %}its invoice lines
     by customer and item, traced to their orders and shipping documents, and the question is which customers bought {{ 'more' if example.diff > 0 else 'less' }} and why{% else %}the price
     lists, promotions, and overrides on its lines, and the question is what changed in pricing{% endif %}{% if example.group != 'Services' %}; for
     Services, engagement and time records by quarter{% endif %}.{% if furniture_q4_missed %} Furniture Q4, which the threshold misses, would still call for the promotion
     discounts (Tutorial 6.3) and the late-invoiced promotion lines (Tutorial 5.2).{% endif %} -->
