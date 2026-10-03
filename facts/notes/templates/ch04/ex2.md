<!-- Instructor notes, Exercise 4.2: lines / LineTotal / DiscountAmount by promotion (DiscountAmount = ROUND(Quantity*UnitPrice*Discount,2);
     Excel rounding may move totals by a few cents): {% for p in promos %}{{ p.id }} {{ p.name }} {{ p.lines|count }} / {{ p.total|money }} / {{ p.discount|money }}; {% endfor %}all {{ lines|count }} lines /
     {{ discount|money }}. Promotion {{ top.id }} holds about {{ (100 * top.share)|num }} percent of the discount dollars. The consistency test finds no differences: every promotion
     line carries its promotion's DiscountPct, and no line has a discount without a PromotionID. Students may notice that promotions {{ backwards[:-1]|join(', ') }}{{ ',' if backwards|length > 2 }} and {{ backwards[-1] }}
     have an EffectiveEndDate earlier than their EffectiveStartDate and promotion {{ single[0] }} is effective for a single day; testing billing dates
     against the effective dates needs the invoice dates, which a later chapter brings onto the lines. -->
