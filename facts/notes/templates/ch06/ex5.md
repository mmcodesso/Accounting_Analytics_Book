<!-- Instructor notes, Exercise 6.5: flagged (over 10% and over $50,000): {% for r in flagged %}{{ r.group }} Q{{ r.q }} {{ '+' if r.diff > 0 }}{{ r.diff|money }} ({{ r.pct|spct }}){{ ', ' if not loop.last }}{% endfor %}.
     Not flagged: {% for r in missed %}{{ r.group }} Q{{ r.q }} {{ '+' if r.diff > 0 }}{{ r.diff|money }} ({{ r.pct|spct }}){{ ', the largest dollar difference, and ' if loop.first }}{% endfor %}. A percentage test
     alone misses large dollar differences in the largest product line; a tolerable amount based on materiality, or an expectation that
     reflects known changes such as the promotion, would treat them differently. Prior-year revenue is a weak expectation because it
     ignores growth and known events, which students may note. Follow-up examples: for {{ missed[0].group }} Q{{ missed[0].q }}, the promotion discounts (Tutorial 6.3)
     and the late-invoiced promotion lines (Tutorial 5.2); for Services, engagement and time records by quarter. -->
