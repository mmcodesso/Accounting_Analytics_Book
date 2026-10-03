<!-- Instructor notes, Exercise 4.4: {{ shipments|count }} shipments. FreightTerms values are Prepaid ({{ pp.n|count }} shipments) and Prepaid and Add ({{ pa.n|count }}).
     Every Prepaid shipment has BillableFreightAmount 0, so all are negative by design: FreightMargin {{ pp.margin|money }} (average FreightCost {{ pp.avg_cost|money }}).
     Prepaid and Add shipments bill freight: {{ pa.above|count }} above cost, {{ pa.below|count }} below, {{ pa.equal|count }} equal; FreightMargin {{ pa.margin|money }} (average FreightCost {{ pa.avg_cost|money }};
     billed freight averages about {{ (100 * pa.ratio)|num }} percent of cost). Total FreightMargin {{ margin|money }}; {{ negative|count }} negative shipments. FreightCost ranges from
     {{ low|money }} to {{ high|money }}. The finding: freight is absorbed by design on Prepaid orders, and freight billed under Prepaid and Add recovers most but
     not all of the carrier cost. -->
