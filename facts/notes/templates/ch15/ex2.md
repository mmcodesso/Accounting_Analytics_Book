<!-- Instructor notes, Exercise 15.2 (CR15 reference model): {{ d.C }} net income by month: {% for m, v in months %}{{ m }} {{ v|money }}{{ '; ' if not loop.last }}{% endfor %}; YTD at June {{ june|money }}, December {{ ni|money }} (equal to {{ close }}). Visual calculations:
     YTD = RUNNINGSUM ( [Net Income] ); Change = [Net Income] - PREVIOUS ( [Net Income] ). (3) Filtered to July-December, the running
     sum starts at July and reaches {{ h2|money }} in December, while TOTALYTD still shows {{ july|money }} in July and {{ ni|money }} in
     December, because the measure reads the model and the visual calculation only the visual's rows. (4) July is the month with three
     pay dates (Chapters 11 and 14) and the low point; October has Furniture revenue {{ october|pct }} below October {{ d.P }} (Chapter 11) at the peak
     of the promotion's discounts. (5) The measure, which is right whatever the visual shows and can be exported. -->
