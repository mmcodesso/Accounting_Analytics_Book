{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 8.6: promotions {% for p in flagged %}{{ p.id }} ({{ p.code }}, {{ p.collection }} Collection, {{ 'effective ' if loop.first }}{{ p.start }} to {{ p.end }}){{ sep(loop) }}{% endfor %}
     are {{ pct|pct(0) }} collection
     promotions approved by EmployeeID {{ approver.id }} ({{ approver.name }}, {{ approver.title }}) on their start dates. All of their invoice lines were ordered
     outside the effective dates: {% for f in flagged_lines %}{{ f.n|count }} lines with {{ 'discounts of ' if loop.first }}{{ f.discount|money }}{{ sep(loop) }}{% endfor %}, a total of
     {{ n_lines|count }} lines and {{ discount|money }}, ordered in {% for m in order_months %}{{ m }}{{ sep(loop) }}{% endfor %} of each year and invoiced through {{ last_months|join(' or ') }}. Every line of the other
     promotions was ordered within its dates.
     Pending overrides: IDs {% for o in overrides %}{{ o.id }}{{ sep(loop) }}{% endfor %}
     on SalesOrderLineIDs {% for o in overrides %}{{ o.line }}{{ sep(loop) }}{% endfor %}. They were
     billed on {{ billed }} invoice lines
     ({% for o in overrides %}{% for i in o.invoices %}{{ i }}{{ sep(loop) }}{% endfor %}{% if o.invoices|length > 1 %}, {{ o.shipments }} shipments of one order line{% endif %}{{ '; ' if not loop.last }}{% endfor %}) at
     the pending ApprovedUnitPrice ({% for o in overrides %}{{ o.approved|money }}{{ ', ' if not loop.last }}{% endfor %}) under a price-list PricingMethod ({{ methods|join(' or ') }})
     with a blank PriceOverrideApprovalID, {{ below|money }} below the reference prices in total. Price lists: {% for l in expired %}{{ l.id }} ({{ l.label }}, ends
     {{ l.end }}{% if l.end < l.start %}, before its {{ l.start }} start{% endif %}){{ sep(loop) }}{% endfor %} are Expired and
     have no successor, yet they priced {{ after|count }} order lines dated after their end dates ({{ after_total|money }}):
     {% for p in per_list %}list {{ p.id }} {% if p.all %}all {{ p.n|count }} of its lines ({% for y, n in p.years %}{{ n|count }}{{ ', ' if not loop.last }}{% endfor %}){% else %}{% for y, n in p.years %}{{ n|count }} in {% if y|string == p.end_year %}late December {% endif %}{{ y }}{{ sep(loop) }}{% endfor %}{% endif %}{% if not loop.last %};
     {% endif %}{% endfor %}.
     Lists {% for u in unused %}{{ u }}{{ sep(loop) }}{% endfor %}, {{ n_unused }} Active copies of the {{ original.segment }} list named Overlap with the same dates as list {{ original.id }}, have no
     price list lines and price nothing. Customer lists: {% if customers|length == 1 %}customer{% else %}customers{% endif %} {% for c in customers %}{{ c.id }} ({{ c.name }}, {{ c.segment }}, list {{ c.list }}){{ sep(loop) }}{% endfor %} {{ 'has' if customers|length == 1 else 'have' }} {{ n_own }}
     order lines under {{ method }} that cite list {{ cited }}: SalesOrderLineIDs {% for o in own %}{{ o.line }} ({{ o.date }}){{ sep(loop) }}{% endfor %}. Their UnitPrice equals {{ 'the' if customers|length == 1 else 'each' }} customer's own list ({% for o in own %}{{ o.price|money }}{{ ', ' if not loop.last }}{% endfor %}), not list {{ cited }} ({% for o in own %}{{ o.cited|money }}{{ ', ' if not loop.last }}{% endfor %}): {{ 'the' if customers|length == 1 else 'each' }}
     customer paid its contract price, but the record names the wrong{% if stale %}, and in {% for y in stale %}{{ y }}{{ sep(loop) }}{% endfor %} expired,{% endif %} list. No other customer with its
     own list has {{ method }} lines. Design: the system accepts end dates before start dates, lets an order line carry a
     pending price, and prices from expired lists. Operation: the approvals did not prevent the discounts, and nobody renewed the
     {{ renewed }}. -->
