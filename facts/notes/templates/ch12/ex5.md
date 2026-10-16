{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 12.5: (1) {{ n_after }} registers pay the {{ title }} (employee {{ emp }}, {{ center }} cost center, terminated
     {{ terminated }}) after the termination: {% for r in after %}{{ r.id }} ({% if loop.first %}period from {{ r.start }}, {% endif %}paid {{ r.paid }}){{ sep(loop) }}{% endfor %}, {{ gross|money }} gross each, about {{ times }} times the employee's usual gross pay ({{ usual|money }}) and the amount of the chief
     executive's register, all charged to the {{ charged }} cost center. The chief executive has a register in every other pay period but none in
     these {{ n_after }}, so the chief executive's pay for them appears to have been recorded under employee {{ emp }}; only the bank
     records can show who received it. Only {{ first }}, whose period includes the termination date, could be a
     final paycheck, and even it pays {{ times }} times the usual amount. {% for r in unpaid %}{{ r }}{{ sep(loop) }}{% endfor %} are the registers of Tutorial 12.1 with no payment
     record. (2) One person, the {{ approver_title }} (employee {{ approver }}), approved all {{ registers|count }} registers, each on its pay date. (3) {{ own }} registers,
     net pay {{ own_net|money }}, are the {{ approver_title }}'s own; {{ n_early }} payments ({% for p in early %}{{ p }}{{ sep(loop) }}{% endfor %}, {{ early_net|money }} net) pay the chief financial
     officer the day before the register was approved. (4) The {{ n_after }} post-termination registers are few, but they recur in {{ pay_years }} pay years
     under the same employee and the {{ charged }} cost center, and {{ n_unpaid }} have no payment record, so they may share a cause in how pay is
     mapped to employees rather than be isolated lapses. Investigate the common cause and trace the payments to the bank records, and
     accept either classification if it is reasoned. A single approver who approves their own pay is a pattern that points to a weakness
     in the design of the control, to confirm against the policy and any independent review. Suggested
     changes: a second approver for registers and for the approver's own pay, and payments released only after approval. -->
