<!-- Instructor notes, Exercise 9.2: 5060 {{ name }} is AccountID {{ account }}. Fiscal {{ d.C }} source types: PurchaseInvoice and
     JournalEntry; the JournalEntry row is closing entry {{ close }}, a credit of {{ close_amount|money }}, which clears the account. PurchaseInvoice
     postings: {{ pi_rows|count }} rows with three descriptions: "Record unfavorable purchase variance" {{ unf.n|count }} debits ({{ unf.amount|money }}), "Record favorable
     purchase variance" {{ fav.n|count }} credits ({{ fav.amount|money }}), and "Record nonrecoverable purchase tax" {{ tax.n|count }} debits ({{ tax.amount|money }}); the net, {{ net|money }},
     equals the close. The purchase variance is the invoice price against the purchase-order price at which the goods were received (the
     invoice clears goods received not invoiced, account 2020, at the receipt value); a credit means the supplier billed below the order
     price{% if rounding %} ({{ rounding }} on lines billed at the order price {{ rounding_verb }} rounding){% endif %}. The
     account also absorbs purchase tax that cannot be recovered. Largest unfavorable variance {{ largest|money }} ({% for p in postings %}{{ p.date }}, voucher {{ p.voucher }}{{ '; ' if not loop.last }}{% endfor %}{{ ', a tie' if postings|length > 1 }}); next {{ next[0]|money }} and {{ next[1]|money }}. Purchase variance is recorded when a supplier invoice is posted; manufacturing variance
     when a work order closes, comparing actual with standard production cost. -->
