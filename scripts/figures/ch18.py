"""Chapter 18 figures (make, buy, or reprice).

Both figures are generic: they show how the costing views and the make-or-buy test are built, and carry no
values, so they do not give away the case's answers.
"""

from __future__ import annotations

from drawio import (AMBER, AMBER_TINT, BLUE, BLUE_TINT, GRAY, GRAY_TINT, HEAD, RULE, SMALL, TEAL, TEAL_TINT,
                    WHITE, Diagram)

BOTTOM, TOP, LEFT, RIGHT = (0.5, 1), (0.5, 0), (0, 0.5), (1, 0.5)


def fig_18_01() -> Diagram:
    d = Diagram("Three Ways to Cost the Plant's Time")
    top = d.box("<b>What the plant paid for in a year</b><br>Crew, supervision, equipment, and factory overhead",
                130, 0, 600, 56, fill=BLUE, stroke=BLUE, color=WHITE)
    views = [
        ("Standard costing", BLUE,
         "Standard rate × standard hours of the output",
         "<b>Variance</b>: everything else, charged to cost of goods sold when each work order closes",
         False, "Good for control while the rates are current"),
        ("Actual absorption", GRAY,
         "All of the year's cost divided by the units made",
         "<b>Nothing left over</b>: idle time is spread into the cost of every unit",
         True, "Unit cost rises whenever volume falls"),
        ("Time-driven costing", TEAL,
         "Capacity cost rate × routing time used, plus factory overhead",
         "<b>Unused capacity</b>: reported as a cost of the plant, not of the products",
         False, "Separates what products use from what sits idle"),
    ]
    w, gap = 272, 22
    for i, (title, fill, products, rest, empty, note) in enumerate(views):
        x = i * (w + gap)
        head = d.box(f"<b>{title}</b>", x, 110, w, 40, fill=fill, stroke=fill, color=WHITE, size=HEAD,
                     rounded=False)
        d.arrow(top, head, exit=(0.15 + 0.35 * i, 1), entry=TOP)
        d.text("<b>Charged to products</b>", x, 160, w, 20, size=SMALL, color=GRAY, align="left")
        d.box(products, x, 182, w, 74, fill=BLUE_TINT, stroke=BLUE)
        d.text("<b>Left out of product cost</b>", x, 266, w, 20, size=SMALL, color=GRAY, align="left")
        d.box(rest, x, 288, w, 74, fill=WHITE if empty else AMBER_TINT, stroke=GRAY if empty else AMBER,
              dashed=empty)
        d.box(f"<i>{note}</i>", x, 372, w, 44, fill=GRAY_TINT, stroke=RULE, size=SMALL)
    return d


def fig_18_02() -> Diagram:
    d = Diagram("The Make-or-Buy Test for One Family")
    qw, qh, L = 300, 64, 40
    start = d.box("<b>Delivered quote</b><br>price plus inbound freight, per unit", L, 0, qw, 52, fill=GRAY_TINT,
                  stroke=GRAY)
    q1 = d.box("Is it below <b>materials plus factory overhead</b>, the cost that stops even if the crew "
               "stays?", L, 92, qw, qh, fill=WHITE, stroke=BLUE, stroke_width=1.5)
    q2 = d.box("Is it below that cost <b>plus the crew time</b> the family uses?", L, 206, qw, qh,
               fill=WHITE, stroke=BLUE, stroke_width=1.5)
    q3 = d.box("Will the crew be <b>reduced in step</b> with the hours freed?", L, 320, qw, qh,
               fill=WHITE, stroke=BLUE, stroke_width=1.5)
    buy1 = d.box("<b>Buy</b>, if the terms, quality, and minimum volume are acceptable", 470, 92, 390, qh,
                 fill=TEAL_TINT, stroke=TEAL)
    buy2 = d.box("<b>Buy, with the crew plan</b>: weigh tooling and severance over the quote's two years",
                 470, 320, 390, qh, fill=TEAL_TINT, stroke=TEAL)
    make1 = d.box("<b>Keep making</b>: buying adds cost while the crew stays; test the price as well", 470, 434, 390, qh,
                  fill=BLUE_TINT, stroke=BLUE)
    make2 = d.box("<b>Keep making</b>, and test the price against the margin floor", L, 434, qw, qh,
                  fill=BLUE_TINT, stroke=BLUE)
    floor = d.box("<b>Below the floor?</b> Reprice, and weigh the volume the increase could cost", L, 548, qw,
                  qh, fill=AMBER_TINT, stroke=AMBER)
    d.arrow(start, q1, exit=BOTTOM, entry=TOP)
    d.arrow(q1, buy1, label="Yes", exit=RIGHT, entry=LEFT)
    d.arrow(q1, q2, label="No", exit=BOTTOM, entry=TOP)
    d.arrow(q2, q3, label="Yes", exit=BOTTOM, entry=TOP)
    d.arrow(q2, make2, label="No", exit=LEFT, entry=LEFT, points=[(14, 238), (14, 466)])
    d.arrow(q3, buy2, label="Yes", exit=(1, 0.3), entry=(0, 0.3))
    d.arrow(q3, make1, label="No", exit=(1, 0.8), entry=LEFT, points=[(405, 371.2), (405, 466)])
    d.arrow(make2, floor, exit=BOTTOM, entry=TOP)
    return d


FIGURES = {
    "fig-18-01-costing-views": fig_18_01,
    "fig-18-02-make-or-buy-test": fig_18_02,
}
