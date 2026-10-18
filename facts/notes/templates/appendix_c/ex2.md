<!-- Instructor notes, Exercise C.2: fiscal {{ C }} discounts by segment, with each segment's peak month:
     {% for s, m, v, t in peaks %}{{ s }} peaks in {{ m }} ({{ v|money }} of {{ t|money }}){{ '; ' if not loop.last }}{% endfor %}.
     (4) Design Trade peaks in {{ trade_month }}, the month of the {{ trade }}, which gives {{ trade_own|money }} of it, while {{ trade_rest|money }} comes from
     the {{ autumn }}'s lines invoiced that month. {% for s, m in others %}{{ s }} peaks in {{ m }}{{ ', ' if not loop.last }}{% endfor %}, the months of the
     {{ autumn }} ({{ autumn_months }}). (5) {{ no_discount|join(', ') }} received no discounts. The segment promotion reached one segment, while
     the item-group promotion reached every segment that bought the group. The pattern shows the discounts by invoice month, not what the
     promotions did to sales, so a calendar aimed at one segment also needs that segment's orders and margins. (6) The saved page reopens in
     Reading view with fiscal {{ C }} selected, the assigned chart title and the alt text. -->
