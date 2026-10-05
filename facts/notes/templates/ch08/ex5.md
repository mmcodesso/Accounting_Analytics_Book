{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
{%- macro an(title) -%}{{ 'an' if title[0] in 'AEIOU' else 'a' }}{%- endmacro -%}
<!-- Instructor notes, Exercise 8.5: {{ orders|count }} purchase orders; the CFO approved {{ cfo_share|pct }} of them. SelfApproved: {{ selfs|length }}
     ({% for s in selfs %}{{ s.number }}{% if s.big %} for {{ s.total|money }}{% endif %}{{ sep(loop) }}{% endfor %}; the {{ n_big }}
     large ones were created and approved by the {{ big_role }}, limit {{ big_limit|num }}, and are the note-financed capital purchases of Exercise
     8.2). AboveLimit: {{ n_above }}, including orders approved by {% for t in zero_titles %}{{ t }}{{ sep(loop) }}{% endfor %} with a limit of 0,
     {% for o in others %}{{ o.number }} ({{ o.title }}, {{ o.total|money }} against {{ o.limit|num }}){{ sep(loop) }}{% endfor %}.
     AfterTermination: {{ term|length }}
     ({{ term|join(', ') }}), all approved by {{ term_name }}, {{ an(term_title) }} {{ term_title }} terminated on {{ term_date }}. Risk
     scores: {{ s2 }} orders score 2 and {{ s1 }} score 1. Requisition bands from 4,800: {{ bands|join(', ') }}, so the 4,950-4,999.99 band has twice
     the count of any neighbor. Its {{ band }} requisitions were all converted to POs; {{ unapproved|length }} have no approver ({{ unapproved|join(', ') }}, the requisitions of Exercise 2.5). {% for r in runs %}{{ r.first }} to {{ r.last }}{{ sep(loop) }}{% endfor %} are
     {{ run_len }} consecutive requisitions each, dated January 1, all for {{ qty|num }} units at {{ cost|money }} ({{ value|money }}), for different items and {{ requesters }}. {{ n_five }} employees have a 5,000 limit ({% for t in five %}{{ an(t) }} {{ t }}{{ sep(loop) }}{% endfor %}). Supplier invoices: the CFO
     approved {{ inv_cfo|count }} of {{ inv_total|count }}; the other {{ inv_other }} are PI {% for i in g.zero.ids %}{{ i }}{{ sep(loop) }}{% endfor %} ({% for t in g.zero.totals %}{{ t|money }}{{ ', ' if not loop.last }}{% endfor %}), approved by {{ g.zero.name }},
     {{ an(g.zero.title) }} {{ g.zero.title }} with a limit of {{ g.zero.limit|num }}; PI {% for i in g.within.ids %}{{ i }}{{ sep(loop) }}{% endfor %} ({% for t in g.within.totals %}{{ t|money }}{{ ', ' if not loop.last }}{% endfor %}), approved by {{ g.within.name }}, {{ an(g.within.title) }} {{ g.within.title }},
     within the {{ g.within.limit|num }} limit but outside the purchasing and accounting roles;
     and PI {% for i in g.beyond.ids %}{{ i }}{{ sep(loop) }}{% endfor %} ({% for t in g.beyond.totals %}{{ t|money }}{{ sep(loop) }}{% endfor %}), approved by {{ g.beyond.name }},
     the {{ g.beyond.title }}, above the {{ g.beyond.limit|num }} limit, the note-financed capital invoices of
     Exercise 8.2. Near-duplicates, payments dated before {{ d.N }}-01-01: SameAmount flags {{ n_payments }} payments in {{ pairs }} pairs (no group larger than
     two; {{ within30 }} pairs at most 30 days apart); SameInvoice flags none, so every pair pays two different invoices and no invoice was paid twice.
     Gap test: {% for g in gaps %}PO-{{ g.year }} {{ 'runs ' if loop.first }}{{ g.low|count }} to {{ g.high|count }} ({{ g.n|count }}{{ ' orders' if loop.first }}){{ ', ' if not loop.last }}{% endfor %}; no numbers
     are missing, and the sequence continues across years rather than restarting. -->
