<!-- Instructor notes, Exercise 8.4: fiscal {{ d.C }} payments: {{ n|count }} payments to {{ suppliers }} suppliers, {{ total|money }}. {{ n50 }} suppliers make up 50%, {{ n80 }}
     make up 80%, and {{ n90 }} make up 90% of spending; the largest supplier ({{ top.name }}, {{ top.category }}) has {{ top.share|pct(2) }}, so
     dollar concentration is low (a low-spend supplier can still be critical, which the dollars do not show). By category: {% for c, v in categories %}{{ c }} {{ v|money }}{{ '; ' if not loop.last }}{% endfor %}.
     Timing: {{ before|count }} payments
     before the due date, {{ on|count }} on it, and {{ after|count }} after it ({{ after_share|pct }}, holding {{ after_value|pct }} of the value); median {{ median|num }} days after due, mean {{ mean|num(1) }}; {{ late30|count }}
     payments more than 30 days late. Paying late conserves cash but risks supplier relationships and late fees; paying early uses
     cash sooner, and no supplier's recorded terms offer an early-payment discount, although contracts may hold terms the data
     do not show. -->
