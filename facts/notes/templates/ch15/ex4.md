<!-- Instructor notes, Exercise 15.4 (CR15 reference model and Python): (1) a whole-number parameter, GENERATESERIES ( 0, 20,
     1 ), {{ steps }} values with a default of 12, divided by 100 in the measures (a decimal range from 0 to 0.2 by 0.01 stopped at
     0.19 in Desktop, 20 values). Promotion {{ id }} {{ d.C }} lines: {{ units|num(2) }} units, price before discount
     {{ price|num(2) }} per unit, standard cost {{ cost|num(2) }} per unit (the Part II case's inputs). Break-even lift = (p (1 - 0.01903) - c) / (p (1 - d)
     (1 - 0.01903) - c) - 1: {% for x, lift in lifts %}{{ x|pct(0) }} {{ lift|pct }}{% if x == 0.12 %} (the Part II case){% endif %}{{ ', ' if not loop.last }}{% endfor %}. The case found no lift in any
     promotion's months (from {{ low|spct }} to {{ high|spct }} against the other months of the year), {{ 'so even' if five != 'less than' else 'and' }} a 5% discount needs {{ five }} the largest
     increase ever measured; a defensible answer is not to repeat it, or to test a small discount on a defined group first. -->
