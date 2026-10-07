<!-- Instructor notes, Exercise C.2: fiscal {{ C }} discounts by segment, with each segment's peak month:
     {% for s, m, v, t in peaks %}{{ s }} peaks in {{ m }} ({{ v|money }} of {{ t|money }}){{ '; ' if not loop.last }}{% endfor %}.
     (4) Design Trade peaks in {{ trade_month }}, the month of the {{ trade }}; {% for s, m in others %}{{ s }} peaks in {{ m }}{{ ', ' if not loop.last }}{% endfor %}, the months of the
     {{ autumn }} ({{ autumn_months }}). (5) {{ no_discount|join(', ') }} received no discounts. A segment promotion reaches one segment, while
     an item-group promotion reaches every segment that buys the group, so a calendar aimed at one segment should use a segment promotion. -->
