<!-- Instructor notes, Exercise 14.6 (reference model through the local engine; all tests pass within 0.01): invoice lines {{ n|count }};
     revenue {{ rev|money }} (Chapter 6); net income {{ ni|money }} ({{ close }}); journal entry debits {{ debits|money }} (all years,
     closes included, equal to JournalEntry TotalAmount, Chapter 8; written with SUM ( GLEntry[Debit] ) and SourceDocumentType =
     "JournalEntry", not with GL Amount); 5080 in fiscal {{ d.C }} {{ variance|money }} (Chapter 10, Account[AccountNumber] = 5080 with GL Amount);
     invoice revenue in the ledger {{ ledger|money }} (Exercise 10.1). (2) The ledger exceeds the lines by {{ gap|money }}: {{ numbers }} ({% for a in amounts %}{{ a|money }}{{ ' + ' if not loop.last }}{% endfor %}), dated in late {{ d.P }} and posted on {{ d.C }}-01-01 (Chapter 6, Exercise 6.1); a reconciling item
     is tested as its own expected difference, not left as a failure. (3) With the closes kept: net income 0 and 5080 0 fail; invoice
     lines, revenue, journal entry debits, invoice revenue in the ledger, and Test 3's trial balance (which excludes the two closes by
     VoucherNumber) still pass. (4) The tests show agreement of totals with earlier, independent calculations on the same database;
     they cannot show that individual rows are right, that the source data is complete or valid, or that a total no test covers is
     right; run them after every refresh and every change to the model, before the report is shared. -->
