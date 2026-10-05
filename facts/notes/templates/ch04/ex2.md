<!-- Instructor notes, Exercise 4.2: lines / LineTotal / DiscountAmount by promotion (DiscountAmount = ROUND(Quantity*UnitPrice*Discount,2);
     Excel rounding may move totals by a few cents): {% for p in promos %}{{ p.id }} {{ p.name }} {{ p.lines|count }} / {{ p.total|money }} / {{ p.discount|money }}; {% endfor %}all {{ lines|count }} lines /
     {{ discount|money }}. Promotion {{ top.id }} holds about {{ (100 * top.share)|num }} percent of the discount dollars. The consistency test finds no differences: every promotion
     line carries its promotion's DiscountPct, and no line has a discount without a PromotionID. Students may notice that {% if n_backwards %}promotion{{ 's' if n_backwards > 1 }} {{ backwards }}
     {{ 'have an EffectiveEndDate earlier than their' if n_backwards > 1 else 'has an EffectiveEndDate earlier than its' }} EffectiveStartDate{{ ' and ' if n_single }}{% endif %}{% if n_single %}promotion{{ 's' if n_single > 1 }} {{ single }} {{ 'are' if n_single > 1 else 'is' }} effective for a single day{% endif %}; testing billing dates
     against the effective dates needs the invoice dates, which a later chapter brings onto the lines. -->
