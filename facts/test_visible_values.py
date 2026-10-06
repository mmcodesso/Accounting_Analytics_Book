"""Self-tests for facts/visible_values.py: the display formats, the lint, and the edition's classification.

    python facts/test_visible_values.py          # runs without pytest; exit 1 on a failure
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

import visible_values as v  # noqa: E402


class Formats(unittest.TestCase):
    CASES = [("$29,756,420.08", 29756420.08), ("47.49%", 0.4749), ("29.8M", 29.8e6), ("−3,317.93", -3317.93),
             ("+7,885.63", 7885.63), ("($115,046.07)", -115046.07), ("380_000", 380000), ("31 percent", 0.31),
             ("$100 million", 1e8), ("6.884200e+02", 688.42), ("2.33×", 2.33), ("-0.80", -0.8), ("0.10", 0.1),
             ("007947", 7947), ("$0.00", 0), ("+26.9 percent", 0.269), ("1,446", 1446)]

    def test_round_trip(self):
        for literal, value in self.CASES:
            parsed = v.parse_literal(literal)
            self.assertIsNotNone(parsed, literal)
            x, fmt = parsed
            self.assertAlmostEqual(x, value, places=6, msg=literal)
            self.assertEqual(v.display(value, fmt), literal)

    def test_flags(self):
        self.assertEqual(v.display(152.2, "~10 $.0"), "$150")
        self.assertEqual(v.display(815921, "floor100000 ,.0"), "800,000")
        self.assertEqual(v.display(0.308, "floor5 .0p"), "30")
        self.assertEqual(v.display(0.308, "ceil5 .0 percent"), "35 percent")
        self.assertEqual(v.display(-2011.14, "abs .2"), "2011.14")
        self.assertEqual(v.display(0.08, ".0p"), "8")

    def test_half_up_as_excel(self):
        self.assertEqual(v.display(2006.895, ",.2"), "2,006.90")


class Lint(unittest.TestCase):
    PATH = "chapters/04-excel-essentials/chapter.qmd"

    def test_new_value_is_flagged(self):
        text = (v.REPO / self.PATH).read_text(encoding="utf-8")
        found = [u["literal"] for u in v.unclassified(self.PATH, text + "\n\nRevenue was $12,345.67 on 4,321 lines.\n")]
        self.assertEqual(found, ["$12,345.67", "4,321"])

    def test_references_and_years_are_not_values(self):
        text = "See Tutorial 4.1, Step 3, and Chapter 12 in fiscal 2026 (Figure 4.2). Allow 60 seconds.\n"
        self.assertEqual(v.unclassified(self.PATH, text), [])


class Edition(unittest.TestCase):
    def test_every_literal_in_scope_is_classified(self):
        left = [(u["file"], u["line"], u["literal"]) for p in v.scope_files() for u in v.unclassified(p)]
        self.assertEqual(left, [])

    def test_keys_equal_the_text_on_the_edition(self):
        self.assertEqual(v.check(), [])


@unittest.skipUnless(__import__("os").environ.get("CHARLESRIVER_ROLLED"), "set CHARLESRIVER_ROLLED to a rolled dataset folder")
class RollRehearsal(unittest.TestCase):
    """Rewrite every keyed literal for a rolled dataset, rewrite the classification, and lint the result."""

    def test_roll_then_lint(self):
        import os
        import visible
        from db import Data
        old, new = visible.snapshot(Data()), visible.snapshot(Data(Path(os.environ["CHARLESRIVER_ROLLED"]) / "CharlesRiver.sqlite"))
        yml, problems = v.roll_classification(old, new)
        self.assertEqual([p for p in problems if "looks like a year" not in p], [])
        texts = {}
        for p in v.scope_files():
            with open(p, encoding="utf-8", newline="") as fh:
                text = fh.read()
            for a, b, lit in v.edits(p, new, text)[0]:
                text = text[:a] + lit + text[b:]
            texts[p] = text
        v.load_yml(text=yml)
        try:
            left = [(v.rel_path(p), u["line"], u["literal"]) for p, t in texts.items() for u in v.unclassified(p, t)]
            wrong = [(v.rel_path(p), o.line, o.literal) for p, t in texts.items() for o in v.classify(p, t)
                     if o.cls == "key" and o.key in new and v.display(new[o.key], o.fmt) != o.literal]
        finally:
            v.load_yml(force=True)
        self.assertEqual(left, [])
        self.assertEqual(wrong, [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
