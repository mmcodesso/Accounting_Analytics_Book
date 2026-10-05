{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Instructor notes, Exercise 16.3 (SQL; Chapter 12 H8): surge days {% for y, k in by_year %}{{ k }} in {{ y }}{{ ', ' if not loop.last }}{% endfor %} ({{ total }} in all); the
     first is {{ first }}, then surge days in {{ with_surge }} of the {{ span }} months from {{ several }} (about {{ average|num }} a month), up to {{ peak }} in {{ peak_month }}; every surge day has all {{ employees }} hourly
     manufacturing employees at {{ regular|num(1) }} regular plus {{ overtime|num(1) }} overtime hours. Surge overtime {% for h in on_surge %}{{ h|num }}{{ sep(loop) }}{% endfor %} hours, {% for s in shares %}{{ s|num(3) }}{{ sep(loop) }}{% endfor %}
     of the year's manufacturing overtime; overtime on other days did not grow ({{ other|map('num')|join(', ') }}). All {{ entries|count }} surge entries
     were approved by the Production Manager on the work date. Distinct values of total hours: Group By with "Count Distinct Rows"
     on the hours column; one value means everyone clocked the same hours. (5) The production manager approved every entry the
     test flags; telling the approver what the test detects is the prompt notification that Gonzalez and Hoffman (2018) found
     can encourage fraud when detection is weak, so the test stays with internal audit and goes to the audit committee. The
     Plant page's overtime share is a management measure; the surge-day test is an audit test. -->
