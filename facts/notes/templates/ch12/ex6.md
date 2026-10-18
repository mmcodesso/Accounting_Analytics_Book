<!-- Instructor notes, Exercise 12.6: (1) {{ n_dupes }} supplier invoice numbers each appear twice for the same supplier; each pair has different
     amounts, and each invoice was paid once (Exercise 2.6). Standardized numbers (UPPER, TRIM, and REPLACE of hyphens and spaces)
     find the same {{ n_dupes }} pairs and no others: the numbers are entered consistently. (2) {{ n_checks }} check numbers are used twice, both for
     supplier {{ check_supplier }}: {{ checks|join(' and ') }}; ACH and wire payments carry no check number, so they need a separate payment-reference test. (3) {{ pairs|count }}
     pairs share supplier and amount on different dates; {{ within30 }} are within 30 days (the chapter's example, with 14 days, finds {{ within14 }}), and
     none pays the same recorded invoice, which within the test's scope (same supplier and amount, different dates) does not
     exclude a duplicate bill under another number, on the same date, or at another amount, so the pairs within 30 days need their invoices, orders, and receipts reviewed before they are treated as
     distinct purchases.
     (4) No gaps in any series. Sales invoices and cash receipts continue across years (SI {% for lo, hi in series[0] %}{{ lo|count }}-{{ hi|count }} in {{ d.years[loop.index0] }}{{ ', ' if not loop.last }}{% endfor %}; CR {% for lo, hi in series[1] %}{{ lo|count }}-{{ hi|count }}{{ ', ' if not loop.last }}{% endfor %}), as do purchase orders ({% for lo, hi in series[2] %}{{ lo|count }}-{{ hi|count }}{{ ', ' if not loop.last }}{% endfor %}); journal entries restart each year ({% for lo, hi in series[3] %}{{ lo|count }}-{{ hi|count }}{{ ', ' if not loop.last }}{% endfor %}). A LAG partitioned by year on a continuing series would miss a
     gap between the last number of one year and the first of the next. (5) MAD: all payments {{ mad_all|num(5) }}, full payments {{ mad_full|num(5) }}, partial payments
     {{ mad_partial|num(5) }}, exactly the values of Tutorial 8.1. All nine digits occur in
     each group, so the average is over nine (a quarter missing a digit needs the nine listed and joined). The partial payments'
     nonconformity plausibly reflects a selection by size (only invoices of {{ partial_floor|count }} or more are paid in parts), and
     conformity would not prove the payments genuine. printf('%.15e') writes 688.42 as 6.884200000000000e+02 and {{ smallest|money }} as {{ smallest_e }}, so the first
     character is the first significant digit for every positive amount (the smallest payment is {{ smallest|money }}); with
     printf's default of six decimals, an amount just below a power of ten would round up (999,999.99 to 1.000000e+06),
     although no payment here changes its digit. LOG10 needs SQLite's math functions, which depend on how the library was built
     (SELECT LOG10(10.0) returns 1 when they are present); the Windows release of DB Browser for SQLite includes them and DB Browser for SQLCipher lacks
     them, and a CASE that lists the nine expected proportions can replace it (test B2 of the model script). -->
