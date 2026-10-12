{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 13.1: line totals by year and group:
     {% for y in years %}{{ y.year }} {% for g, v in y.groups %}{{ g }} {{ v|money }}; {% endfor %}total {{ y.total|money }}{{ '.' if not loop.last }}
     {% endfor %}(Chapter 6). SubTotal by year equals the line totals exactly ({% for y in years %}{{ y.n|count }}{{ sep(loop) }}{% endfor %} invoices; no invoice without lines).
     Equal annual totals cannot show that every invoice agrees, since differences between invoices could offset (Tutorial 4.1,
     Step 10); compared invoice by invoice, all {{ n_all|count }} invoices equal their lines within half a cent.
     GrandTotal {{ years|map(attribute='grand')|map('money')|join('; ') }} = SubTotal + freight ({{ years|map(attribute='freight')|map('money')|join('; ') }}) + tax
     ({{ years|map(attribute='tax')|map('money')|join('; ') }}). Revenue from goods and services is SubTotal; freight posts to its own revenue account
     (4050) and sales tax is a liability (2050), as Chapter 10's trace of {{ traced }} showed. (4) InvoiceHeaders is a control:
     its totals come from the invoice table alone, so they test the model instead of depending on its relationships. Relating
     it would not create an ambiguous path, but it would give the model a second table for the same invoices, whose FiscalYear
     could filter the lines alongside SalesInvoice's, and its header amounts would still not respond to an Item filter, which
     flows only toward the lines. Accept any answer that keeps the control separate for a stated reason. -->
