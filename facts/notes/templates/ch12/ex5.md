{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 12.5: (1) {{ n_after }} registers pay the {{ title }} (employee {{ emp }}, {{ center }} cost center, terminated
     {{ terminated }}) after the termination: {% for r in after %}{{ r.id }} ({% if loop.first %}period from {{ r.start }}, {% endif %}paid {{ r.paid }}){{ sep(loop) }}{% endfor %}, {{ gross|money }} gross each, about {{ times }} times the employee's usual gross pay ({{ usual|money }}) and the amount of the chief
     executive's register, all charged to the {{ charged }} cost center. Only {{ first }}, whose period includes the termination date, could be a
     final paycheck, and even it pays {{ times }} times the usual amount. {% for r in unpaid %}{{ r }}{{ sep(loop) }}{% endfor %} are the registers of Tutorial 12.1 with no payment
     record. (2) One person, the {{ approver_title }} (employee {{ approver }}), approved all {{ registers|count }} registers, each on its pay date. (3) {{ own }} registers,
     net pay {{ own_net|money }}, are the {{ approver_title }}'s own; {{ n_early }} payments ({% for p in early %}{{ p }}{{ sep(loop) }}{% endfor %}, {{ early_net|money }} net) pay the chief financial
     officer the day before the register was approved. (4) The unpaid and post-termination registers are isolated exceptions, to be
     traced to the bank records; a single approver who approves their own pay is a weakness in the design of the control. Suggested
     changes: a second approver for registers and for the approver's own pay, and payments released only after approval. -->
