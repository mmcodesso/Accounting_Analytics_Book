<!-- Instructor notes, Exercise 13.6: pie: {{ n_slices }} slices of {% for g, s in slices %}{{ s|pct }} ({{ g }}){{ ',
     ' if not loop.last }}{% endfor %}; the small slices cannot be ranked by eye; replace with a sorted bar chart with labels. Card: Average of Discount
     in fiscal {{ d.C }} is {{ avg|pct(2) }}, an unweighted average of line rates; discount dollars over the dollars before discount are {{ ratio|pct(2) }}
     ({{ of_list|pct(2) }} of list), and Furniture's average rate is {{ f_avg|pct(2) }}; the right figure is a ratio of totals, which needs a measure (Chapter 14);
     until then, show discount dollars and the list amount side by side. Line chart: the default axis and the January {{ d.F }} start-up
     month ({{ start|money }} against {{ low|num }} to {{ high|num }} in the other months) suggest growth of almost 80% to December {{ d.C }}; whole
     years show {{ changes|map('spct')|join(' and ') }}; start the axis at zero and compare whole years. Combo chart: the discounts get their own axis and
     appear comparable to revenue ({{ peak.month }} {{ d.C }} discounts were {{ peak.share|pct }} of that month's revenue); use one axis or two charts. Hidden
     filter: excluding Services removes {{ services|money }} ({{ services_share|pct }}) of fiscal {{ d.C }} revenue without telling the reader; move it to a visible
     slicer or state it in the titles. -->
