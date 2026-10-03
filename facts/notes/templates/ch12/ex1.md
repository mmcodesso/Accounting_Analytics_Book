<!-- Instructor notes, Exercise 12.1: revenue by delivery date (every shipment is delivered in the year it ships). {{ g1.word }} invoices for goods
     delivered in December {{ d.F }} were invoiced and posted in January {{ d.P }} (SubTotal {{ g1.sub|money }}), and {{ g2.word }} for December {{ d.P }} deliveries were
     posted in January {{ d.C }} ({{ g2.sub|money }}), among them {{ odd.number }} (dated {{ odd.date }}, shipped {{ odd.shipped }}, posted {{ odd.posted }}). {{ n_unbilled }} December
     {{ d.C }} shipment lines were never invoiced by the end of the data: standard cost {{ cost|money }}, already posted to cost of goods sold; about
     {{ value|money }} at order price. Net effect on revenue: {{ d.F }} understated {{ eff1|money }}; {{ d.P }} overstated {{ eff2|money }} ({{ g1.sub|money }} received less
     {{ g2.sub|money }} moved on); {{ d.C }} understated about {{ eff3|num }} ({{ g2.sub|money }} received less {{ value|money }} unbilled). Cost of goods sold is posted at
     shipment, so margin moves by the whole revenue amount. {{ n_before }} invoices are dated before their shipment but posted in the year of
     delivery ({{ before|join(', ') }}): an invoice-dating failure, not a revenue
     cutoff error; they are Exercise 5.2's invoices except {{ odd.number }}. Exercises 6.1 and 10.1 compared InvoiceLines, built on invoice
     dates, with the ledger: of their {{ n_differences }} {{ d.C }} differences, only {{ odd.number }} is a revenue cutoff error. Supplier invoices post on their
     ReceivedDate (no exception); one, {{ supplier.number }} (dated {{ supplier.date }}, received {{ supplier.received }}, {{ supplier.total|money }}, supplier {{ supplier.id }}), crosses the
     year-end. Payroll: {% for h in hourly %}{{ 'hourly labor ' if loop.first }}of {{ h.work }} work paid in fiscal {{ h.paid }}, {{ h.total|money }} (manufacturing {{ h.mfg|money }}){{ '; ' if not loop.last }}{% endfor %}. With salaries and employer taxes and benefits allocated by working day, the full cost of
     late-December work is about {{ full[0]|num }} ({{ d.F }}) and {{ full[1]|num }} ({{ d.P }}). Periods {{ first }}-{{ last }} average {{ avg|money }} (manufacturing {{ avg_mfg|money }}); the {{ days }}
     working days of {{ start_day }}-31 December {{ d.C }} cost about {{ low|num }}-{{ high|num }} (manufacturing about {{ mfg_low|num }}-{{ mfg_high|num }}), never recorded. Account 2030
     holds only the opening {{ opening|num }}, so no year-end accrues the wages; each year-end's liability is understated by the amounts above. -->
