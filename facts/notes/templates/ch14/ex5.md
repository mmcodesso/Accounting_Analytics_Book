<!-- Instructor notes, Exercise 14.5 (reference model through the local engine): (1) Customer Rows {{ customers }} for every group (the
     Customer table, unfiltered by Item or Date because the filter does not flow from the lines to Customer); Customers Invoiced
     {% for g in invoiced %}{{ g.group }} {{ g.n }}{{ ', ' if not loop.last }}{% endfor %} ({{ n_invoiced }} in all); Customer Rows Both equals Customers Invoiced.
     A report uses the distinct count on the fact table, which needs no change to the model. CROSSFILTER changes the direction
     only inside the calculation that calls it; setting the stored relationship to Both in Model view could change other
     calculations and visuals that use it, so the exercise leaves the model unchanged. (2) Operating Expense {{ opex|money }} for every group; with Both on the Date relationship, a selection on Item filters
     Date to the days with an invoice of that group, and the ledger follows: {% for g in others %}{{ g.group }} {{ g.opex|money }} ({{ g.days }}{{ ' days' if loop.first }}), {% endfor %}{{ services.group }} {{ services.opex|money }} ({{ services.days }} days), total {{ opex|money }} ({{ year_days }}). The
     Services figure is the operating expense of the {{ services_word }} days on which design services were invoiced, neither a share
     of the year's operating expense that belongs to Services nor Services' own cost: a selection in one fact table has
     filtered the other. (3) REMOVEFILTERS: {% for s in shares %}{{ s.group }} {{ s.rf|pct(2) }}, {% endfor %}total 100%; ALL(SalesInvoiceLine): {% for s in shares %}{{ s.all|pct(2) }}, {% endfor %}total {{ all_total|pct(2) }}, the share of
     fiscal {{ d.C }} in {{ years }} years of revenue ({{ every|money }}{% if outside %}, with {{ outside.n }} line{{ 's' if outside.n != 1 }} dated {{ outside.dates }}{% endif %}), because ALL on the fact table removes the year as well. (4) Both
     directions (inspect the cross filter direction in Model view, then compare one known slice with CROSSFILTER set to Single
     and to Both); a count taken from a dimension or header (compare with a distinct count on the facts); ALL on a fact table in
     a share (shares must total 100%); inactive relationships used without USERELATIONSHIP (inspect which relationships are
     active and the measure's formula, then compare the two dates on a line known to cross a year, because equal totals alone
     do not show the cause); (Blank) members (count the unmatched keys); measures that keep the closing entries (Exercise 14.6). -->
