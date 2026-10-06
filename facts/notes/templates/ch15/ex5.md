<!-- Instructor notes, Exercise 15.5: actual fiscal {{ d.C }} Q4 revenue {{ actual|money }} (invoice lines; {{ fit_months }} months from January {{ d.F }} to
     September {{ d.C }} fit the forecast). Chapter 7's backtest for the same quarter: trend {{ errors.trend.quarter|spct(2) }} error, mean {{ errors.mean.quarter|spct(2) }} (monthly error
     {{ errors.mean.monthly|pct(2) }}), same quarter last year {{ errors.last.quarter|spct(2) }} ({{ errors.last.monthly|pct(2) }} monthly). Power BI's forecast is computed in the visual (exponential smoothing,
     Microsoft 2014) and its values cannot be read from the model; students read them from the forecast's tooltip. A good answer
     reports the forecast's quarter error beside the benchmarks, notes that a seasonal pattern needs more than {{ years }} years to detect
     reliably, and checks the effect of the start-up month, January {{ d.F }} at {{ start|pct(0) }} of the year's other months, on the fit (requirement 5). The note should require any forecast
     shown to managers to carry its hindcast error and the benchmark it beat or did not beat. -->
