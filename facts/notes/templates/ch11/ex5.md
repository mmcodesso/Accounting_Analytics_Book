<!-- Instructor notes, Exercise 11.5: {{ entries }} journal entries. Flags: {% for f, n in counts %}{{ f }} {{ n }}{{ ', ' if not loop.last }}{% endfor %};
     scores {% for s, n in scores %}{{ s }}: {{ n }}{{ ', ' if not loop.last }}{% endfor %}{% if missing %} (no entry scores {{ missing[0] }}, so that row does not appear){% endif %}, the same as Chapter 8. Working formulas: Weekend
     strftime('%w', CreatedDate) IN ('0', '6'); Backdated date(CreatedDate) > PostingDate; RoundAmount TotalAmount = ROUND(TotalAmount /
     1000, 0) * 1000 (the % operator truncates decimals in SQLite, so it is not safe on amounts); AboveLimit TotalAmount >
     MaxApprovalAmount with a LEFT JOIN to Employee on ApprovedByEmployeeID, so a missing approver or limit leaves the flag at 0,
     which means a breach was not established, not that the entry was authorized (COALESCE(MaxApprovalAmount, 0) would count it
     as a breach). The model reports those entries in a separate ApprovalDataMissing flag, outside the score, so the score stays
     comparable with Chapter 8; {% if data_missing == 0 %}every entry has an approver with a recorded limit here{% else %}{{ data_missing }}
     entries miss an approver or a limit{% endif %}. The score-{{ top_score }} entry is {{ top_entry }}, the opening balance entry created by the chief financial officer. -->
