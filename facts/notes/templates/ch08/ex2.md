<!-- Instructor notes, Exercise 8.2: open invoices at {{ asof }}: {{ open_ap|money }}. GL 2010 (credit minus debit): {{ gl|money }}, made up of
     PurchaseInvoice {{ pi|money }}, DisbursementPayment {{ dp|money }}, and JournalEntry {{ '+' if je > 0 }}{{ je|money }}. The JournalEntry rows are {{ rows }}:
     (a) {{ entry }}, the opening balance entry, credits 2010 with {{ opening|money }}, accounts payable with no invoice detail that has never
     been paid; the same entry debits cash with exactly the same amount, a coincidence worth a question; (b) {{ capital[0].entry }} (Debt Reclass,
     {{ capital[0].amount|money }}) and (c) {{ capital[1].entry }} (Debt Reclass, {{ capital[1].amount|money }}) debit 2010 and credit 2110 Notes Payable, reclassifying note-financed
     capital invoices {{ capital[0].number }} and {{ capital[1].number }} (supplier {{ capital[0].supplier }}, {{ capital[0].supplier_name }}), which have no supplier payments and therefore
     still appear open in the invoice detail. Reconciliation: {{ open_ap|money }} - {{ reclassed|money }} + {{ opening|money }} = {{ gl|money }}. The reclasses are
     explained (the invoice detail should be closed or flagged as settled by a note), while the opening balance is unsupported, the same
     finding as accounts receivable. The purchase orders behind the two capital invoices, {{ capital[0].po }} and {{ capital[1].po }}, were created
     and approved by the {{ role }}, whose limit is {{ limit|num }} (Exercise 8.5). -->
