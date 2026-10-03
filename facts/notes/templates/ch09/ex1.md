{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 9.1: {{ n }} accounts: {% for t, k in types %}{{ t }} {{ k }}{{ ', ' if not loop.last }}{% endfor %}. {{ n_subtypes }} subtypes,
     including {% for s, k in subtypes %}{{ s }} ({{ k }}){{ ', ' if not loop.last }}{% endfor %}.
     Header accounts: {{ headers }}; {{ n_top }} top-level headers ({{ top|join(', ') }}) have a NULL ParentAccountID, while
     {% for s in subs %}{{ s.number }} {{ s.name }}{{ sep(loop) }}{% endfor %} are sub-headers under {% for s in subs %}{{ s.parent }}{{ sep(loop) }}{% endfor %}, so the chart has two levels of headers. No
     header account has a posting. Opposite normal balances ({{ n_opposite }}): {% for a in asset_other %}{{ a.number }} {{ a.name }}, {% endfor %}{{ depreciation|join('/') }} accumulated
     depreciation (contra assets, credit); {% for a in equity %}{{ a.number }} {{ a.name }}{{ sep(loop) }}{% endfor %} (contra equity, debit); {% for a in revenue %}{{ a.number }} {{ a.name }}{{ sep(loop) }}{% endfor %} (contra revenue, debit). The query needs parentheses:
     (AccountType IN ('Asset','Expense') AND NormalBalance = 'Credit') OR (AccountType IN ('Liability','Equity','Revenue') AND NormalBalance = 'Debit').
     Inactive ({{ n_inactive }}), none with any posting: {% for a in inactive %}{{ a.number }} {{ a.name }}{% if a.subtype == 'Header' %} (header){% endif %}{{ ', ' if not loop.last }}{% endfor %}. Manufacturing salaries and factory overhead are charged to 1090 {{ clearing_name }} (AccountID {{ clearing }}) and reach cost of
     goods sold through inventory and 5080 {{ variance_name }}. Memo points: 1030 has no postings, so no allowance has ever been recorded
     (Chapter 8); 4070 is inactive, so discounts are netted in revenue (Part II case). -->
