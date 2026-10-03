<!-- Instructor notes, Exercise 4.1: invoices by fiscal year {{ years|join(' / ') }}: {{ n|map('count')|join(' / ') }} ({{ invoices|count }} in all).
     SubTotal {{ sub|map('money')|join(' / ') }} ({{ sub_total|money }}); FreightAmount {{ frt|map('money')|join(' / ') }};
     TaxAmount {{ tax|map('money')|join(' / ') }}; GrandTotal {{ gt|map('money')|join(' / ') }}.
     SubTotal + Freight + Tax = GrandTotal on every invoice. Limitations: credit memos are not netted ({{ cm_n|map('count')|join(' / ') }} credit memos,
     SubTotal {{ cm_sub|map('money')|join(' / ') }}), sales tax is a liability collected for the government rather than revenue, and freight
     billed is recorded in its own revenue account (4050). Grid formula, for example
     =SUMIFS(SalesInvoice[SubTotal],SalesInvoice[InvoiceDate],">="&DATE($A5,1,1),SalesInvoice[InvoiceDate],"<="&DATE($A5,12,31)),
     pasted (not filled) across, with the sum column changed per measure or locked with [[Col]:[Col]]. -->
