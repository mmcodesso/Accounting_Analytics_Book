<!-- Answer key, Chapter 9 (for instructors; HTML comments are removed from every rendered format):
     1 B, 2 D, 3 A, 4 C, 5 C, 6 A, 7 D, 8 B, 9 A, 10 D, 11 B, 12 C, 13 A, 14 D, 15 B.
     1 B: a column list separated by commas returns just those columns.
     2 D: GLEntry.AccountID is the Account table's surrogate key; 5080 has AccountID {{ variance }}.
     3 A: = compares text exactly, including case; the stored value is WorkOrderClose.
     4 C: dates stored as year-month-day text are compared with dates written the same way, in quotes.
     5 C: AND is evaluated before OR, so the condition adds every {{ d.C }} posting of every account.
     6 A: no comparison with NULL is true; IS NULL finds the missing values.
     7 D: DISTINCT reveals the values in use, so a filter is not written for a value that does not exist.
     8 B: DESC sorts from the largest, and LIMIT 10 keeps the first ten rows.
     9 A: without ORDER BY, LIMIT returns an undefined selection of rows.
     10 D: a working copy keeps the download safe; DB Browser opens files for writing unless opened read-only, and a SELECT never changes a file.
     11 B: without the comma, AccountName becomes an alias for AccountNumber, a logical error.
     12 C: the clauses must be written as SELECT, FROM, WHERE, ORDER BY, LIMIT.
     13 A: % matches any run of characters; = compares the pattern literally, _ matches exactly one character, and IN needs an exact value.
     14 D: documentation lets another person understand, rerun, and review the queries.
     15 B: two whole numbers divide as whole numbers, a decimal keeps the fraction, and text never equals a number when
     neither side is a column; SELECT needs no FROM. -->
