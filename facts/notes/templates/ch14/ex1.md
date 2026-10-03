<!-- Instructor notes, Exercise 14.1 (Desktop 2.158 reference model through the local engine, and SQL): (2) at {{ d.C }}-12 (AsOf
     {{ asof }}): Asset {{ now.Asset|money }}; Liability {{ now.Liability|money }}; Equity {{ now.Equity|money }}; Revenue {{ now.Revenue|money }}; Expense {{ now.Expense|money }};
     total {{ total|money }}. Revenue and expense together {{ (-ni)|money }}, the net income of fiscal {{ d.C }}; {{ liab|money }} + {{ equity|money }} + {{ ni|money }}
     = {{ now.Asset|money }}, Chapter 6's balance sheet. (3) {{ d.C }}-06: Asset {{ mid.Asset|money }}; Liability {{ mid.Liability|money }}; Equity {{ mid.Equity|money }};
     Revenue {{ mid.Revenue|money }}; Expense {{ mid.Expense|money }}; {{ d.F }}-12: Asset {{ first.Asset|money }}; Liability {{ first.Liability|money }}; Equity {{ first.Equity|money }};
     Revenue {{ first.Revenue|money }}; Expense {{ first.Expense|money }} (net income {{ ni_first|money }}); both total 0. The closes of {{ d.F }} and {{ d.P }} are dated
     December 31 of those years, before the as-of date, so the measure keeps them and they zero the revenue and expense accounts.
     (4) No close filter at {{ d.C }}-12: Equity {{ kept_equity|money }}, revenue and expense 0 (post-closing; the {{ d.C }} net income is already in
     retained earnings). On GL Amount: Equity {{ gl.Equity|money }} (the opening equity only, without the {{ d.F }} and {{ d.P }} net incomes), Revenue
     {{ gl.Revenue|money }} and Expense {{ gl.Expense|money }} ({{ years }} years). Assets are {{ now.Asset|money }} in all three. (5) {{ n_contra }} accounts, the contra
     accounts of Chapter 9: {{ allowance.number }} {{ allowance.name }}, {{ depreciation[:-1]|join(', ') }} and {{ depreciation[-1] }} accumulated depreciation (Asset, Credit);
     {{ equity_contra.number }} {{ equity_contra.name }} (Equity, Debit); {% for r in revenue %}{{ r.number }} {{ r.name }}{{ ' and ' if not loop.last }}{% endfor %} (Revenue, Debit).
     Signing by NormalBalance would show accumulated depreciation as a positive amount and add it to the assets instead of deducting it,
     and add the contra revenue to revenue. -->
