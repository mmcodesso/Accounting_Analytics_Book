<!-- Instructor notes, Exercise 16.6 (SQL; Chapter 8 and Exercise 12.6; the measures checked in Desktop 2.158's engine on the AM16
     reference model): {{ pairs }} supplier-and-amount pairs on different dates among the payments through {{ asof }}, {{ within30 }} within 30
     days, none paying the same invoice (Chapter 8: near-duplicates, not duplicates). Orders Approved = CALCULATE ( COUNTROWS (
     PurchaseOrder ), TREATAS ( VALUES ( Employee[EmployeeID] ), PurchaseOrder[ApprovedByEmployeeID] ) ); Registers Approved the
     same on PayrollRegister; Entries Approved = COUNTROWS ( JournalEntry ); the entries' share divides by CALCULATE ( COUNTROWS (
     JournalEntry ), REMOVEFILTERS ( Employee ) ), while the other two divide by COUNTROWS of their table, which Employee does not
     filter. Shares: {{ cfo.name }} ({{ cfo.title }}) {{ cfo.n|count }} orders, {{ cfo.share|pct(2) }}, and {{ cfo_entries.n }} entries, {{ cfo_entries.share|pct(2) }}; {{ controller.name }}
     ({{ controller.title }}) {{ controller.n|count }} entries, {{ controller.share|pct(2) }}; {{ manager.name }} ({{ manager.title }}) {{ manager.n|count }} registers, {{ manager.share|pct(0) }}, and {{ manager_entries.n }} entries, {{ manager_entries.share|pct(2) }}; the other
     {{ other_orders }} orders spread over {{ other_people }} employees (buyers, procurement analysts, the Purchasing Manager, the Production Manager and a
     Production Supervisor, and the departed Account Executive, {{ executive }}). The exceptions by approver put the Accounting Manager first
     ({{ first }}) and the CFO second ({{ second }}), but the shares show that each of three processes rests on one person, a design question for
     segregation of duties and for absences (who approves when that person is away, and who approves that person's own
     documents). -->
