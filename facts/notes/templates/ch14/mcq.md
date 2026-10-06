<!-- Answer key, Chapter 14 (for instructors; HTML comments are removed from every rendered format):
     1 A, 2 C, 3 B, 4 D, 5 C, 6 A, 7 B, 8 D, 9 B, 10 D, 11 A, 12 C, 13 B, 14 C, 15 A.
     1 A: the grain is the event one row represents, one line of one invoice.
     2 C: a dimension that reaches the facts only through another table is a snowflake.
     3 B: an attribute kept in the fact table without a dimension table is a degenerate dimension.
     4 D: with Both, a filter on Item reaches Date through the lines and then the ledger (in {{ d.C }}, Services leaves {{ days }} days of operating expense).
     5 C: the ship-date relationship is inactive; USERELATIONSHIP switches it on inside CALCULATE.
     6 A: unique, contiguous days covering full years.
     7 B: a ratio of totals that changes with the cell is a measure; the others belong to each row.
     8 D: the cost is multiplied line by line and then added; totals multiplied give a meaningless number.
     9 B: the row, the column, and the slicer all filter the cell.
     10 D: a row context does not filter other tables; CALCULATE's context transition would.
     11 A: a filter argument replaces the existing filter on the same column.
     12 C: ALL on the fact table removes the filters that reach it from Date as well (Furniture {{ all_share|pct(2) }} instead of {{ rf_share|pct(2) }}).
     13 B: a test compares the model's result with a total trusted from elsewhere.
     14 C: the {{ d.N }} rows of the date table have {{ d.C }} as their prior year.
     15 A: the closes move each year's revenue and expenses to retained earnings, netting them to zero. -->
