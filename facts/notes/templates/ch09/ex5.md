<!-- Instructor notes, Exercise 9.5: Status values {% for s, k in status %}{{ s }} ({{ k|count }}){{ ' and ' if not loop.last }}{% endfor %}; ShippedBy {{ carriers|join(', ') }}. No TrackingNumber (NULL): {{ n|count }} shipments, dated {{ low }} to {{ high }}. In Transit with DeliveryDate
     before {{ end }}: {{ transit|count }}, the oldest delivered {{ oldest }}{% if later %} ({{ later_word }} more In Transit shipment{{ 's have' if later > 1 else ' has' }} a DeliveryDate on or after {{ end }}){% endif %}. The
     SQL results equal the Excel filters of Tutorial 2.1. Dimensions: completeness (tracking number) and consistency or timeliness (status
     that contradicts the delivery date). The tests are saved as text and rerun with one click. -->
