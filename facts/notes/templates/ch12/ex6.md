<!-- Instructor notes, Exercise 12.6: (1) {{ n_dupes }} supplier invoice numbers each appear twice for the same supplier; each pair has different
     amounts, and each invoice was paid once (Exercise 2.6). Standardized numbers (UPPER, TRIM, and REPLACE of hyphens and spaces)
     find the same {{ n_dupes }} pairs and no others: the numbers are entered consistently. (2) {{ n_checks }} check numbers are used twice, both for
     supplier {{ check_supplier }}: {{ checks|join(' and ') }} (the AnomalyLog lists {{ n_logged }} duplicate references, but only {{ n_with_check }} have check numbers). (3) {{ pairs|count }}
     pairs share supplier and amount on different dates; {{ within30 }} are within 30 days (the chapter's example, with 14 days, finds {{ within14 }}), and
     none pays the same invoice, so they are recurring purchases rather than duplicates. Grouping finds identical values; comparing
     each payment with other payments across a range of dates needs the table joined to itself.
     (4) No gaps in any series. Sales invoices and cash receipts continue across years (SI {% for lo, hi in series[0] %}{{ lo|count }}-{{ hi|count }} in {{ d.years[loop.index0] }}{{ ', ' if not loop.last }}{% endfor %}; CR {% for lo, hi in series[1] %}{{ lo|count }}-{{ hi|count }}{{ ', ' if not loop.last }}{% endfor %}), as do purchase orders ({% for lo, hi in series[2] %}{{ lo|count }}-{{ hi|count }}{{ ', ' if not loop.last }}{% endfor %}); journal entries restart each year ({% for lo, hi in series[3] %}{{ lo|count }}-{{ hi|count }}{{ ', ' if not loop.last }}{% endfor %}). A LAG partitioned by year on a continuing series would miss a
     gap between the last number of one year and the first of the next. (5) MAD: all payments {{ mad_all|num(5) }}, full payments {{ mad_full|num(5) }}, partial payments
     {{ mad_partial|num(5) }}, exactly the values of Tutorial 8.1. printf writes 688.42 as 6.884200e+02 and {{ smallest|money }} as {{ smallest_e }}, so the first character is
     the first significant digit for every positive amount (the smallest payment is {{ smallest|money }}); LOG10 needs SQLite's math functions, which DB
     Browser 3.13.1 includes. -->
