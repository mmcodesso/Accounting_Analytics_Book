<!-- Instructor notes, Exercise 11.2: the only journal entries that post to the revenue accounts are the year-end closes ({{ closes[:-1]|join(',\n     ') }}, {{ closes[-1] }}), so SourceDocumentType <> 'JournalEntry' removes exactly them. {{ rows }} rows ({{ lines }} lines x {{ months }} months). December
     year-to-date, fiscal {{ d.C }}: {% for name, amount in ytd %}{{ name }} {{ amount|money }}, {% endfor %}total {{ total|money }}, equal to the trial balance balances of those accounts (operating revenue in the trial balance also
     includes 4050 Freight, {{ freight|money }}) and to the SalesInvoice postings of Exercise 10.1. Furniture, fiscal {{ d.C }}
     against {{ d.P }}: largest decline {{ down.month }} ({{ down.now|money }} against {{ down.before|money }}, {{ down.pct|spct }}), largest increase {{ up.month }} ({{ up.now|money }} against
     {{ up.before|money }}, {{ up.pct|spct }}). October {{ d.P }} was unusually high; the fiscal {{ d.C }} promotion (Chapter 6) lowered prices in September and October
     and its orders were invoiced into November and December, so the timing of invoicing and promotions is the first thing to examine. -->
