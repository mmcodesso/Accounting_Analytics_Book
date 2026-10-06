<!-- Instructor notes, Exercise 8.1: at {{ asof }}, aging by due date (OpenBalance > 0 after cash applications and credit memos dated
     on or before the as-of date): Current {{ b[0].n|count }} invoices, {{ b[0].amount|money }}; 1-30 days {{ b[1].n|count }}, {{ b[1].amount|money }}; 31-60 days {{ b[2].n|count }}, {{ b[2].amount|money }}; 61-90 days
     {{ b[3].n|count }}, {{ b[3].amount|money }}; over 90 days {{ b[4].n|count }}, {{ b[4].amount|money }}; total {{ n|count }} invoices, {{ total|money }}. Expected losses at the given rates: {{ b[0].loss|money }} + {{ b[1].loss|money }} +
     {{ b[2].loss|money }} + {{ b[3].loss|money }} + {{ b[4].loss|money }} = {{ loss|money }}. With the {{ opening|money }} opening balance ({{ entry }}, account 1020) at 40%: {{ loss_with|money }}. The
     opening balance has no invoice detail and no cash application, so its age and collectability are unknown; the honest answer is
     that it must be supported (conversion-date customer detail) or written off, not merely aged. Balances under $10: {{ small }} invoices
     totalling {{ small_total|money }} ({% for y in young %}{{ y.number }} {{ y.balance|money }} is {{ y.age }}{{ '; ' if loop.last else ', ' }}{% endfor %}{{ 'the others are' if young else 'all are' }} 61+ days past due, from {{ low|money }} to {{ high|money }}). Entry: Dr 6170 Bad Debt
     Expense, Cr 1030 Allowance for Doubtful Accounts. Neither account has any GL rows. ASC 326-20-30-3 accepts aging-schedule methods
     and 326-20-30-10 requires the estimate to reflect risk even when remote; Example 5 (326-20-55-37 to 55-40) adjusts historical
     bucket rates for current conditions and forecasts. -->
