<!-- Instructor notes, Exercise 8.3: {{ customers }} customers have open balances at {{ asof }}. {{ n_over }} exceed their credit limit, and {% if late %}{{ n_late }} of them {{ 'has' if late == 1 else 'have' }} a
     past-due balance{% else %}none of them has
     any past-due balance{% endif %}:
     {% for c in over %}{{ c.name }} {{ c.balance|money }} against {{ c.limit|money }} ({{ c.segment }}, {{ c.terms }}{% if c.past_due %}, {{ c.past_due|money }} past due{% endif %}){{ ', ' if not loop.last }}{% endfor %}. {% if not late %}They are over the
     limit because of recent billing, not slow payment, which argues for reviewing the limits rather than stopping shipments.{% elif late < over|length %}The
     others are over the limit because of recent billing, not slow payment, which argues for reviewing their limits rather than stopping
     their shipments.{% endif %} Largest
     balances: {% for c in top %}{{ c.name }}{% if not c.over %} {{ c.balance|money }}{% endif %}, {% endfor %}all {{ segment_top }}.
     Top 5 hold {{ top5|pct }} and top 10 {{ top10|pct }} of the open balance.
     By segment: {% for s, v in segments %}{{ s }} {{ v|money }}{{ ', ' if not loop.last }}{% endfor %}. By terms (open, past due, customers):
     {% for t, v, pd, n in terms %}{{ t }} {{ v|money }}, {{ pd|money }}, {{ n }}{{ '; ' if not loop.last }}{% endfor %}. Every invoice's due date matches its customer's PaymentTerms. -->
