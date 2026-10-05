<!-- Instructor notes, Exercise 4.1: invoices by fiscal year {{ years|join(' / ') }}: {{ n|map('count')|join(' / ') }} ({{ invoices|count }} in all{% if outside %}; the grid leaves out {{ outside.n|count }} invoice{{ 's' if outside.n > 1 }} dated {{ outside.first }}{% if outside.last != outside.first %} to {{ outside.last }}{% endif %}, outside its fiscal years, SubTotal {{ outside.sub|money }}{% endif %}).
     SubTotal {{ sub|map('money')|join(' / ') }} ({{ sub_total|money }}); FreightAmount {{ frt|map('money')|join(' / ') }};
     TaxAmount {{ tax|map('money')|join(' / ') }}; GrandTotal {{ gt|map('money')|join(' / ') }}.
     SubTotal + Freight + Tax = GrandTotal on every invoice. Limitations: credit memos are not netted ({{ cm_n|map('count')|join(' / ') }} credit memos,
     SubTotal {{ cm_sub|map('money')|join(' / ') }}), sales tax is a liability collected for the government rather than revenue, and freight
     billed is recorded in its own revenue account (4050). Grid formula, for example
     =SUMIFS(SalesInvoice[SubTotal],SalesInvoice[[InvoiceDate]:[InvoiceDate]],">="&DATE($A5,1,1),SalesInvoice[[InvoiceDate]:[InvoiceDate]],"<="&DATE($A5,12,31)),
     entered once and filled right and down: filling across shifts SubTotal to the adjacent FreightAmount, TaxAmount, and GrandTotal
     columns, as the grid needs, while the locked [[InvoiceDate]:[InvoiceDate]] and the mixed $A5 stay put (the Watch out on structured
     references). Pasted instead of filled, the formula keeps SubTotal in every column. -->
