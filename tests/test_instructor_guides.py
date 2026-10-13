"""Tests for facts/instructor/guides.py: the template engine of the instructor guides (no dataset needed)."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
for p in (REPO / "facts" / "instructor", REPO / "facts", REPO / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import guides  # noqa: E402

HAS_JINJA = importlib.util.find_spec("jinja2") is not None


def fake_env():
    import jinja2
    jenv = jinja2.Environment(undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                              keep_trailing_newline=True, autoescape=False)

    class Claims:
        def __init__(self):
            self.failed = []

    return SimpleNamespace(jenv=jenv, notes=SimpleNamespace(Claims=Claims), d=None)


def fake_unit():
    base = SimpleNamespace(kind="chapter", number="6", title="Descriptive Analytics", lines=[])
    return guides.GUnit("6", "06", "chapter-06-test", base)


TEMPLATE = """---
title: Example
kind: exercise
number: '6.1'
unit: '6'
perspective: financial
tool: excel
minutes: 60
solution: Example.xlsx
figures:
  - {id: IF-06-1-A, kind: excel-mock, purpose: The table after Step 2., shows: The totals row., data: The trial balance.}
---
# Exercise 6.1: Example

{{ header() }}

Text with {{ 1 + 1 }} in it.

```dax
Total = SUMX ( T, { 1, 2 } )
```

```sql jinja
SELECT {{ 40 + 2 }};
```

{{ figure('IF-06-1-A') }}
"""


class SlugTests(unittest.TestCase):
    def test_slug_is_short_and_plain(self):
        self.assertEqual(guides.slugify("From the Ledger to the Income Statement"), "from-the-ledger-to-the-income-statement")
        self.assertLessEqual(len(guides.slugify("Mapping Table Groups to the Financial Reporting Cycle")), 48)

    def test_slug_drops_the_chapter_reference(self):
        self.assertEqual(guides.slugify("Frame the question (Chapter 1)"), "frame-the-question")


class FenceTests(unittest.TestCase):
    def test_code_fences_are_protected_and_restored(self):
        body = "a {{ x }}\n```dax\nT = { 1 }\n```\nb"
        protected, blocks = guides.protect_fences(body)
        self.assertNotIn("{ 1 }", protected)
        self.assertEqual(guides.restore_fences(protected, blocks), body)

    def test_jinja_fence_stays_live_and_loses_its_marker(self):
        protected, blocks = guides.protect_fences("```sql jinja\nSELECT {{ d.C }};\n```")
        self.assertEqual(blocks, {})
        self.assertTrue(protected.startswith("```sql\n"))
        self.assertIn("{{ d.C }}", protected)

    def test_unclosed_fence_is_an_error(self):
        with self.assertRaises(ValueError):
            guides.protect_fences("```sql\nSELECT 1;")

    def test_indented_fence_in_a_list(self):
        protected, blocks = guides.protect_fences("1. step\n\n   ```sql\n   SELECT {{ 1 }};\n   ```\n2. next")
        self.assertEqual(len(blocks), 1)

    def test_fenced_blocks_listing(self):
        found = guides.fenced_blocks("x\n```sql\nSELECT 1;\n```\n```\nplain\n```")
        self.assertEqual(found, [("sql", "SELECT 1;"), ("", "plain")])


class StrayNumberTests(unittest.TestCase):
    def scan(self, text, allowed=""):
        protected, _ = guides.protect_fences(text)
        return guides.stray_numbers(protected, allowed)

    def test_dataset_values_are_flagged(self):
        flagged = self.scan("Net revenue was $29,731,057.92 in 2026, 15.15% of sales, invoice SI-2025-007947 on 2025-12-04.")
        for tok in ("$29,731,057.92", "2026", "15.15%", "SI-2025-007947", "2025-12-04"):
            self.assertIn(tok, flagged)

    def test_references_and_small_numbers_pass(self):
        self.assertEqual(self.scan("See Exercise 6.1, Step 3 and Table 12.2. Allow 90 minutes for 6 students."), [])

    def test_template_values_code_and_fences_are_not_prose(self):
        text = "Value {{ ni|money }} and `=SUM(A1:A2000)` and\n```sql\nSELECT 123456;\n```\nand {% if x > 10000 %}x{% endif %}"
        self.assertEqual(self.scan(text), [])

    def test_a_number_in_the_exercise_text_is_allowed(self):
        self.assertEqual(self.scan("The threshold is $50,000.", "flag payments of $50,000 or more"), [])
        self.assertEqual(self.scan("Years 2026.", ""), ["2026"])


@unittest.skipUnless(HAS_JINJA, "jinja2 is not installed")
class RenderTests(unittest.TestCase):
    def render(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ex.md"
            path.write_text(text, encoding="utf-8")
            return guides.render_template(fake_env(), fake_unit(), path)

    def test_renders_values_fences_header_and_figure(self):
        text, meta, failed, _ = self.render(TEMPLATE)
        self.assertEqual(failed, [])
        self.assertIn("Text with 2 in it.", text)
        self.assertIn("Total = SUMX ( T, { 1, 2 } )", text)
        self.assertIn("SELECT 42;", text)
        self.assertNotIn("jinja", text)
        self.assertIn("| Solution file | Example.xlsx |", text)
        self.assertIn("[Figure placeholder IF-06-1-A]", text)
        self.assertIn("Status: planned", text)
        self.assertEqual(meta["number"], "6.1")

    def test_undeclared_figure_is_an_error(self):
        with self.assertRaises(KeyError):
            self.render(TEMPLATE.replace("figure('IF-06-1-A')", "figure('IF-06-1-B')"))

    def test_unused_figure_is_reported(self):
        _, _, failed, _ = self.render(TEMPLATE.replace("{{ figure('IF-06-1-A') }}", ""))
        self.assertTrue(any("never used" in f for f in failed))

    def test_missing_value_is_an_error(self):
        import jinja2
        with self.assertRaises(jinja2.UndefinedError):
            self.render(TEMPLATE.replace("{{ 1 + 1 }}", "{{ nothing_here }}"))

    def test_front_matter_is_required(self):
        with self.assertRaises(ValueError):
            self.render("# no front matter\n")


class ScaffoldTests(unittest.TestCase):
    def test_item_scaffold_has_the_required_headings_and_a_step_per_requirement(self):
        g = fake_unit()
        item = guides.Item("exercise", "6.1", "From the Ledger", "x.qmd", "financial", parts=["Build the trial balance", "Explain it"])
        text = guides.scaffold_item(g, item)
        meta, body = guides.split_front(text)
        self.assertEqual(meta["number"], "6.1")
        import re
        self.assertEqual(re.findall(r"^## (.+)$", body, re.M), guides.ITEM_HEADINGS)
        self.assertIn("### Requirement (1): Build the trial balance", body)
        self.assertIn("### Requirement (2): Explain it", body)

    def test_item_file_names(self):
        ex = guides.Item("exercise", "6.1", "From the Ledger", "x.qmd")
        rq = guides.Item("requirement", "3", "Test the data (Chapter 2)", "x.qmd")
        self.assertEqual(ex.filename, "ex-6.1-from-the-ledger.md")
        self.assertEqual(rq.filename, "req-3-test-the-data.md")
        self.assertEqual(ex.item_no, "1")


if __name__ == "__main__":
    unittest.main()
