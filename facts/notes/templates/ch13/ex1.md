{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 13.1: line totals by year and group:
     {% for y in years %}{{ y.year }} {% for g, v in y.groups %}{{ g }} {{ v|money }}; {% endfor %}total {{ y.total|money }}{{ '.' if not loop.last }}
     {% endfor %}(Chapter 6). SubTotal by year equals the line totals exactly ({% for y in years %}{{ y.n|count }}{{ sep(loop) }}{% endfor %} invoices; no invoice without lines).
     GrandTotal {{ years|map(attribute='grand')|map('money')|join('; ') }} = SubTotal + freight ({{ years|map(attribute='freight')|map('money')|join('; ') }}) + tax
     ({{ years|map(attribute='tax')|map('money')|join('; ') }}). Revenue from goods and services is SubTotal; freight posts to its own revenue account
     (4050) and sales tax is a liability (2050), as Chapter 10's trace of {{ traced }} showed. (4) A second table with the same key
     would be a second path from the invoices to the lines; the model keeps one table per entity, and InvoiceHeaders exists only to
     test the header amounts. -->
