<!-- Instructor notes, Exercise 7.6: forecast / orders by year, the four product groups: {% for y in years %}{{ y.year }} about {{ y.ratio|num(2) }} ({% if loop.first %}{% for g, r in y.groups %}{{ g }} {{ r|num(2) }}{{ ', ' if not loop.last }}{% endfor %}{% else %}{% for g, r in y.groups %}{{ r|num(2) }}{{ ' / ' if not loop.last }}{% endfor %}{% endif %}){{ '; ' if not loop.last }}{% endfor %}. The forecast is consistently more than twice the
     orders in every product group, and the bias grows each year, so it is not consistent with historical experience. Services, whose forecasts
     and orders are hours of design work, runs the other way: its forecast is {{ svc|map('num', 2)|join(', ') }} of the hours ordered, an underforecast
     to explain separately; it is not added to the product units. {{ d.C }} product-group totals:
     forecast {{ years[-1].forecast|num(1) }} units, budget {{ budget|num(1) }} units (higher still), orders {{ years[-1].orders|num(1) }}, invoiced {{ invoiced|num(1) }}. Forecast methods in the Table:
     {{ methods[:-1]|join(', ') }}, and {{ methods[-1] }}; the forecast weeks run to {{ last_month }} {{ d.N }}. All {{ rows|count }} rows are IsCurrent 1
     (one version, {{ version }}). Requirement (5): every forecast is within about 10 percent of its baseline (ratios {{ low|num(2) }}-{{ high|num(2) }})
     except DemandForecastID {{ adjusted[:-1]|map(attribute='id')|join(', ') }}, and {{ adjusted[-1].id }}, the first forecast week of {{ d.F }}, {{ d.P }}, and {{ d.C }} ({{ adjusted|map(attribute='date')|join(', ') }})
     for item {{ code }} ({{ name }}, {{ group }}) at warehouse {{ warehouse_id }}, {{ warehouse }}: ForecastMethod
     {{ method }}, ForecastQuantity {{ multiple|num(1) }} times BaselineForecastQuantity ({% for a in adjusted %}{{ a.forecast|num(2) }} against {{ a.baseline|num(2) }}{{ ', ' if not loop.last }}{% endfor %}), planner employee {{ planner_id }}, {{ planner }}, a {{ title }}, and no ApprovedByEmployeeID. They are the only unapproved forecasts in the
     Table, so the control is the approval of planner adjustments: every other adjustment has an approver recorded, which shows the approval
     step was taken, not how carefully each change was reviewed. The quantities are small, but
     an unapproved override by a buyer, who also places purchase orders (employee {{ planner_id }} plans most
     forecasts and created {{ pos|count }} purchase orders), is a control exception worth reporting. Consequences: inflated purchasing and
     production plans, excess inventory and a possible need for an obsolescence reserve, and a budget whose volume cannot be used to evaluate
     performance (Tutorial 7.2). Evidence to request: the forecasting method and its inputs, the planners' adjustments, and management's own
     comparisons of forecast with actual. -->
