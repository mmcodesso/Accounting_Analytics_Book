<!-- Instructor notes, Exercise 14.5 (reference model through the local engine): (1) Customer Rows {{ customers }} for every group (the
     Customer table, unfiltered by Item or Date because the filter does not flow from the lines to Customer); Customers Invoiced
     {% for g in invoiced %}{{ g.group }} {{ g.n }}{{ ', ' if not loop.last }}{% endfor %} ({{ n_invoiced }} in all); Customer Rows Both equals Customers Invoiced.
     A report uses the distinct count on the fact table; Both gives the same answer here but changes every measure that uses the
     relationship. (2) Operating Expense {{ opex|money }} for every group; with Both on the Date relationship, a selection on Item filters
     Date to the days with an invoice of that group, and the ledger follows: {% for g in others %}{{ g.group }} {{ g.opex|money }} ({{ g.days }}{{ ' days' if loop.first }}), {% endfor %}{{ services.group }} {{ services.opex|money }} ({{ services.days }} days), total {{ opex|money }} ({{ year_days }}). The
     Services figure is the operating expense of the {{ services_word }} days on which design services were invoiced, a number with no meaning:
     a selection in one fact table has filtered the other. (3) REMOVEFILTERS: {% for s in shares %}{{ s.group }} {{ s.rf|pct(2) }}, {% endfor %}total 100%; ALL(SalesInvoiceLine): {% for s in shares %}{{ s.all|pct(2) }}, {% endfor %}total {{ all_total|pct(2) }}, the share of
     fiscal {{ d.C }} in {{ years }} years of revenue ({{ every|money }}{% if outside %}, with {{ outside.n }} line{{ 's' if outside.n != 1 }} dated {{ outside.dates }}{% endif %}), because ALL on the fact table removes the year as well. (4) Both
     directions (compare a count with and without CROSSFILTER); a count taken from a dimension or header (compare with a distinct count
     on the facts); ALL on a fact table in a share (shares must total 100%); inactive relationships used without USERELATIONSHIP;
     (Blank) members (count the unmatched keys); measures that keep the closing entries (Exercise 14.6). -->
