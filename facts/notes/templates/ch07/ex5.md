<!-- Instructor notes, Exercise 7.5: revenue on invoice count: R2 {{ r2_with|num(3) }} with January {{ d.F }}, {{ r2_without|num(3) }} without it (slope about {{ slope|num }} per invoice); the
     residual standard error without January {{ d.F }} is about {{ se|num }}, roughly {{ se_share|pct(0) }} of average monthly revenue ({{ average|num }}), so the expectation cannot
     reliably detect a 5% misstatement. Commission (GL 6290) on revenue, fitted {{ d.F }}-{{ d.P }}: intercept {{ a|money }}, slope {{ b|num(5) }}, R2 {{ r2|num(3) }}.
     {{ d.C }} differences above 3%: {% for r in flagged %}{{ r.month }} {{ '{:+,.0f}'.format(r.diff) }} ({{ r.pct|spct }}){{ ', ' if not loop.last }}{% endfor %}; all other months within {{ within }}.
     The {{ pair[0] }} and {{ pair[1] }} differences nearly offset, but not through timing: every SalesCommissionAccrual row is dated on its
     invoice's date except {{ misdated|count }} of {{ accrual_rows|count }} (the invoices dated before their first shipment, Tutorial 2.1; {{ other_month|count }} of them in another month). The cause is the
     customer mix: commission rates run from {{ low|pct(1) }} (Wholesale) to {{ high|pct(0) }} (design services), and Wholesale was {{ share[0]|pct(0) }} of {{ pair[0] }}'s commission
     base against {{ share[1]|pct(0) }} of {{ pair[1] }}'s ({{ share_year|pct(0) }} for the year), so the accrual rate was {{ rate[0]|pct(2) }} against {{ rate[1]|pct(2) }}, which one regression slope
     cannot follow. Evidence: the accruals by customer segment and month, and the credit-memo adjustments. {{ d.C }} accruals {{ accruals|money }} less SalesCommissionAdjustment
     rows ({{ adj_rows|count }}, from credit memos) {{ adj_amount|money }} = GL {{ gl|money }}. -->
