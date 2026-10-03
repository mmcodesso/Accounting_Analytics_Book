<!-- Instructor notes, Exercise 5.3: Furniture revenue by product type, Q3 / Q4 (quantity Q3 / Q4): {% for code, r3, r4, q3, q4 in types %}{{ code }} {{ r3|money }} / {{ r4|money }} ({{ q3|money }} / {{ q4|money }}){{ '; ' if not loop.last }}{% endfor %}. Totals {{ total3|money }} / {{ total4|money }}. Nightstands and sideboards lost the most revenue;
     consoles and bookcases gained. Share changes: {% for code, pts in shifts %}{{ code }} {{ pts }} pts{{ ', ' if not loop.last }}{% endfor %}; the two-point threshold highlights
     none, a useful result: the mix shift is modest. Quantities are fractional on most lines (the validity finding), so unit counts are not
     whole products; revenue shares avoid the issue. -->
