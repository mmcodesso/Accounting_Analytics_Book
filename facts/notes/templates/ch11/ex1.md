<!-- Instructor notes, Exercise 11.1: pre-closing balances at {{ asof }} (PostingDate <= '{{ asof }}', without {{ close1 }} and
     {{ close2 }}), credits less debits by subtype: Operating Revenue {{ opr|money }}; Contra Revenue {{ contra|money }}; COGS {{ cogs|money }};
     Operating Expense {{ opex|money }}; Other Expense {{ oexp|money }}; Other Income or Expense {{ oie|money }}. Net revenue {{ net_rev|money }}; gross margin
     {{ gm|money }} ({{ gm_pct|pct(2) }}); operating income {{ oi|money }} ({{ oi_pct|pct(2) }}); net income {{ ni|money }}, equal to the credit of {{ close2 }} to
     retained earnings (Chapter 6). Assets: Current {{ current|money }} + Fixed {{ fixed|money }} - Contra Fixed {{ contra_fixed|money }} = {{ assets|money }};
     liabilities {{ cl|money }} + {{ ltl|money }} and equity {{ equity|money }} plus net income {{ ni|money }} = {{ le_total|money }}. The Closing subtype
     (8010 Income Summary) has a zero balance before the closes. A CTE such as `WITH Params AS (SELECT '{{ asof }}' AS AsOfDate)`, read with
     `(SELECT AsOfDate FROM Params)`, makes the date one parameter; the closes are found with `EntryType LIKE 'Year-End Close%'
     AND PostingDate = AsOfDate` ({{ close1 }} and {{ close2 }} at {{ asof }}), so nothing else changes with the year. -->
