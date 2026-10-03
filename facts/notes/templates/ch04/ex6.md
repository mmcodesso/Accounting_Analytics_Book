<!-- Instructor notes, Exercise 4.6: {{ requests|count }} requests; {{ approved|count }} Approved, {{ pending|count }} Pending. All {{ approved|count }} approvals were made by EmployeeID {{ approver.id }} ({{ approver.name }},
     {{ approver.title }}). Requests by requester: {% for e, n in by_requester %}{{ 'EmployeeID ' if loop.first }}{{ e }} {{ n|count }}{{ ', ' if not loop.last }}{% endfor %}. The {{ approver.title }} approved {{ self_approved|count }} of her
     own {{ own|count }} requests; her other {{ pending|count }} requests are the {{ pending|count }} Pending ones (IDs {{ ids[:-1]|join(', ') }}{{ ',' if ids|length > 2 }} and {{ ids[-1] }}), which have no approver or approval date. These
     {{ pending_word }} are the AnomalyLog's missing_price_override_approval items. DiscountFromReference ranges from about {{ low|pct }} to {{ high|pct }}. Follow-up
     for the pending requests: their SalesOrderLineIDs ({{ lines|join(', ') }}) were invoiced at the pending ApprovedUnitPrice under a price-list
     PricingMethod (AnomalyLog sale_below_price_floor_without_approval), which students can find by filtering SalesInvoiceLine on
     SalesOrderLineID; the full test is part of the audit analytics later in Part II. The self-approval pattern is a design issue:
     the only approver is also a requester. -->
