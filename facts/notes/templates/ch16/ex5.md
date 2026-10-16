<!-- Instructor notes, Exercise 16.5 (SQL; Chapters 8 and 12): {{ n|count }} payments dated through {{ asof }}; MAD {{ mad.all|num(5) }} (marginally
     acceptable conformity); full payments {{ n_full|count }}, MAD {{ mad.full|num(5) }} (acceptable); partial payments {{ n_partial|count }}, MAD {{ mad.partial|num(5) }}
     (nonconformity), plausibly because only invoices of $1,000 or more are paid in parts, a selection by size that can distort
     the digits; a digit test cannot show that the payments are genuine. A DAX first digit: VALUE ( LEFT ( FORMAT (
     Payments[Amount], "0.00000000E+00" ), 1 ) ). Taking the first character of the amount as text fails on the {{ small }} payments below
     $1, whose text begins with 0. The observed share is a count of the payments with the digit divided by the count of all
     payments in the filter context; MAD = AVERAGEX of the nine absolute differences inside CALCULATE ( ..., REMOVEFILTERS (
     Digits ) ), so a digit selected on the page cannot narrow it to one digit's deviation. Nickell, Schwebke, and Goldwater (2023) is a
     Power BI and Benford teaching case. -->
