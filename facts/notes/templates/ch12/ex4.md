<!-- Instructor notes, Exercise 12.4: {{ n|count }} approvals, spread almost evenly over {{ n_reasons }} reason codes in every year ({{ reasons|join(', ') }}; about a quarter each), so the mix of reasons does not explain why overtime grew, although it does not show that the reasons are false. The
     Production Manager approved {{ manager_n|count }} approvals (about {{ manager_share|pct(0) }}). Every approval grants exactly the hours requested, and every approval is
     dated on the work date itself: no recorded request was reduced and none was approved on an earlier day, although a date
     cannot show whether approval came before the overtime within the day, and a sound request need not be reduced. All {{ entries|count }} clock entries of the {{ days }} surge days
     were approved by the Production Manager on the work date. The shift rosters show that the same manager also created the roster of
     every surge-day entry, a separate test that the approval queries alone do not make. Manufacturing overtime on other days {{ other_trend }} ({{ other|map('num')|join(', ') }} hours), while overtime on surge days grew from {{ surge[0]|num }} to {{ surge[1:]|map('num')|join(' and ') }} hours: all the growth. The control looks like a record of overtime
     rather than an authorization of it, to confirm with the requests, their timestamps, evidence of review, and the policy that applies. Approval in advance, a limit per employee and week, and informative reasons reviewed by someone outside
     production would make it a stronger control. -->
