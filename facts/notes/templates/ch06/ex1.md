<!-- Instructor notes, Exercise 6.1: the pre-closing trial balance at {{ asof }} (GLEntry with PostingDate before {{ d.N }}-01-01, without
     {{ close1 }} and {{ close2 }}, {{ close_rows }} rows) has {{ accounts }} accounts, {{ zero }} of them with a zero balance; debit and credit balances are both
     {{ debits|money }}. Revenue and expense accounts show only fiscal {{ d.C }} because the {{ d.F }} and {{ d.P }} closing entries zeroed them.
     Income statement: operating revenue {{ opr|money }} ({{ (opr / net_rev)|pct(2) }} of net revenue); sales returns and allowances {{ contra|money }} (4060); net
     revenue {{ net_rev|money }}; cost of goods sold {{ cogs|money }} ({{ (-cogs / net_rev)|pct(2) }}; includes freight-out 5050, purchase price variance 5060, and
     manufacturing variance 5080); gross margin {{ gm|money }} ({{ (gm / net_rev)|pct(2) }}); operating expenses {{ opex|money }} ({{ (-opex / net_rev)|pct(2) }}); operating income
     {{ oi|money }} ({{ (oi / net_rev)|pct(2) }}); other income and expense {{ other|money }} (loss on asset disposal 7020 of {{ loss|money }}, an account typed Revenue with
     subtype Other Income or Expense, and interest expense 7030 of {{ interest|money }}); net income {{ ni|money }} ({{ (ni / net_rev)|pct(2) }}), equal to {{ close2 }}.
     Balance sheet: assets {{ assets|money }} = liabilities {{ liabilities|money }} + equity {{ equity|money }} + net income {{ ni|money }}. The balances
     include the unsupported opening balances found in Chapter 8. Revenue reconciliation, account balance vs InvoiceLines {{ d.C }}: {% for r in recon %}{{ r.account }}
     {{ r.balance|money }} vs {{ r.group }}{% if r.diff == 0 %}, equal{% else %} {{ r.lines|money }} ({{ '+' if r.diff > 0 }}{{ r.diff|money }}){% endif %}{{ '; ' if not loop.last }}{% endfor %}. The differences are
     {% for i in invoices %}{{ 'and ' if loop.last and not loop.first }}{{ i.number }} ({{ i.group }}, {{ 'dated ' if loop.first }}{{ i.date }}){{ ', ' if not loop.last }}{% endfor %},
     dated in {{ d.P }} with the next year's number and posted {{ posted }}. InvoiceLines assigns them to fiscal {{ d.P }} by their invoice dates,
     the ledger to fiscal {{ d.C }}. The date that determines the period is the delivery of the goods, not the invoice date or number (every
     shipment is delivered in the year it ships). Only {{ early.number }} shipped in {{ d.P }} (on {{ early.shipped }}), so its {{ early.amount|money }} is a revenue cutoff error; the other
     {{ others }} shipped on {{ others_shipped }}, so the ledger is right and their invoice dates are wrong. Tutorial 12.1 tests cutoff by delivery date for
     every invoice. Freight revenue (4050, {{ freight|money }}) has no invoice line. -->
