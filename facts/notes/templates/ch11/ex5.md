<!-- Instructor notes, Exercise 11.5: {{ entries }} journal entries. Flags: {% for f, n in counts %}{{ f }} {{ n }}{{ ', ' if not loop.last }}{% endfor %};
     scores {% for s, n in scores %}{{ s }}: {{ n }}{{ ', ' if not loop.last }}{% endfor %}{% if missing %} (no entry scores {{ missing[0] }}, so that row does not appear){% endif %}, the same as Chapter 8. Working formulas: Weekend
     strftime('%w', CreatedDate) IN ('0', '6'); Backdated date(CreatedDate) > PostingDate; RoundAmount TotalAmount = ROUND(TotalAmount /
     1000, 0) * 1000 (the % operator truncates decimals in SQLite, so it is not safe on amounts); AboveLimit with a LEFT JOIN to Employee
     on ApprovedByEmployeeID (every entry has an approver with a limit here; COALESCE(MaxApprovalAmount, 0) would count a missing
     approver as a breach, so a missing approver is better reported as a test of its own). The score-{{ top_score }} entry is {{ top_entry }}, the opening balance entry created by the chief financial officer. -->
