<!-- Instructor notes, Exercise B.2 (SQL twins; the CR16 reference model): (2) one cost center, {{ center }} ({{ cc }}),
     whose manager of record is {{ an }} {{ title }}. Security is unrelated, so RELATEDTABLE cannot be used; EXCEPT ( VALUES (
     CostCenter[CostCenterID] ), VALUES ( Security[CostCenterID] ) ), or a FILTER on CostCenter with a COUNTROWS ( FILTER (
     Security, ... ) ) = 0 test, finds it. (3) none: {{ users }} users, {{ ccs }} cost centers. (4) all {{ users }} names match the Email
     of an active employee ({% for id, t in matches %}{{ id }} {{ t }}{{ ', ' if not loop.last }}{% endfor %}),
     each in the cost center the table gives them, so no user is flagged; LOOKUPVALUE ( AccessEmployees[EmployeeID],
     AccessEmployees[Email], Security[UserPrincipalName] ) inside ADDCOLUMNS. (5) every row of AccessEmployees, all {{ n_employees }}
     employees with their addresses and termination dates, because no rule filters an unrelated table (the same reason the
     Customer table still lists every customer for a user missing from the security table). A rule of FALSE () on the table
     for Cost Center Managers, or keeping the table out of the published file, closes it. Run the review whenever the table
     changes and at least quarterly, with the controller's approval recorded. -->