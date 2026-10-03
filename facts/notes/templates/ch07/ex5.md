<!-- Instructor notes, Exercise 7.5: revenue on invoice count: R2 {{ r2_with|num(3) }} with January {{ d.F }}, {{ r2_without|num(3) }} without it (slope about {{ slope|num }} per invoice); the
     residual standard error without January {{ d.F }} is about {{ se|num }}, roughly 5% of average monthly revenue ({{ average|num }}), so the expectation cannot
     reliably detect a 5% misstatement. Commission (GL 6290) on revenue, fitted {{ d.F }}-{{ d.P }}: intercept {{ a|money }}, slope {{ b|num(5) }}, R2 {{ r2|num(3) }}.
     {{ d.C }} differences above 3%: {% for r in flagged %}{{ r.month }} {{ '{:+,.0f}'.format(r.diff) }} ({{ r.pct|spct }}){{ ', ' if not loop.last }}{% endfor %}; all other months within 2.5%.
     The January and February differences nearly offset, which suggests timing of accruals between months rather than a misstatement;
     evidence: accrual dates against invoice dates, and credit-memo adjustments. {{ d.C }} accruals {{ accruals|money }} less SalesCommissionAdjustment
     rows ({{ adj_rows|count }}, from credit memos) {{ adj_amount|money }} = GL {{ gl|money }}. -->
