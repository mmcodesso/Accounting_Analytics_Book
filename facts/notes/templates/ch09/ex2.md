<!-- Instructor notes, Exercise 9.2: 5060 {{ name }} is AccountID {{ account }}. Fiscal {{ d.C }} source types: PurchaseInvoice and
     JournalEntry; the JournalEntry row is closing entry {{ close }}, a credit of {{ close_amount|money }}, which clears the account. PurchaseInvoice
     postings: {{ pi_rows|count }} rows with three descriptions: "Record unfavorable purchase variance" {{ unf.n|count }} debits ({{ unf.amount|money }}), "Record favorable
     purchase variance" {{ fav.n|count }} credits ({{ fav.amount|money }}), and "Record nonrecoverable purchase tax" {{ tax.n|count }} debits ({{ tax.amount|money }}); the net, {{ net|money }},
     equals the close. The purchase variance is the invoice price against the purchase-order price at which the goods were received (the
     invoice clears goods received not invoiced, account 2020, at the receipt value); a credit means the supplier billed below the order
     price. The account also absorbs purchase tax that cannot be recovered. Largest unfavorable variance {{ top[0].amount|money }} ({{ top[0].date }}, voucher
     {{ top[0].voucher }}); next {{ top[1].amount|money }} and {{ top[2].amount|money }}. Purchase variance is recorded when a supplier invoice is posted; manufacturing variance
     when a work order closes, comparing actual with standard production cost. -->
