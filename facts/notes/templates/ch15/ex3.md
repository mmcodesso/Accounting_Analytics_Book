<!-- Instructor notes, Exercise 15.3 (CR15 reference model): Labor Cost per Standard Hour = DIVIDE ( CALCULATE ( SUM (
     LaborTimeEntry[ExtendedLaborCost] ), KEEPFILTERS ( LaborTimeEntry[LaborType] <> "NonManufacturing" ) ), [Standard Hours to Cut-off] ).
     By year: hours per standard hour {{ years|map(attribute='ratio')|map('num', 2)|join(', ') }}; overtime share {{ years|map(attribute='share')|map('num', 3)|join(', ') }}; labor cost per standard hour {{ years|map(attribute='per_std')|map('num', 2)|join(', ') }} (manufacturing labor cost {{ years|map(attribute='cost')|map('money')|join('; ') }}). (4) Cost per standard hour = hours per standard
     hour x cost per hour; overtime hours cost a premium, and the overtime share grew, so the cost per hour rose too (rates also rose).
     (5) Learn: field parameters cannot be the linked fields of a drill-through or tooltip page; link the underlying fields instead. -->
