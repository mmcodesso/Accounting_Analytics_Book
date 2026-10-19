"""The diagram optimizer for the EPUB and the DOCX: scripts/figure_raster.py and filters/raster-figures.lua."""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from scripts import figure_raster as fr  # noqa: E402

# The workflow that runs the tests installs only Pillow and PyYAML: the optimizer's own tests need NumPy too.
needs_numpy = unittest.skipUnless(importlib.util.find_spec("numpy"), "NumPy is not installed")


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def diagram(width: int = 864, height: int = 400) -> Image.Image:
    """A diagram-like image: white page, flat fills, thin lines, anti-aliased shapes (drawn large, then reduced)."""
    scale = 4
    big = Image.new("RGB", (width * scale, height * scale), "white")
    draw = ImageDraw.Draw(big)
    fills = ["#1A5276", "#117A65", "#EAF2F8", "#FEF5E7", "#F2F3F4", "#B03A2E"]
    for index, fill in enumerate(fills):
        left = 20 + index * 130
        draw.rounded_rectangle((left * scale, 40 * scale, (left + 110) * scale, 150 * scale), radius=8 * scale, fill=fill,
                               outline="#2C3E50", width=2 * scale)
        draw.ellipse(((left + 30) * scale, 200 * scale, (left + 80) * scale, 250 * scale), outline="#8A5D00",
                     width=2 * scale)
        draw.line(((left + 55) * scale, 150 * scale, (left + 55) * scale, 200 * scale), fill="#2C3E50", width=2 * scale)
        draw.polygon([((left + 55) * scale, 270 * scale), ((left + 100) * scale, 320 * scale),
                      ((left + 55) * scale, 370 * scale), ((left + 10) * scale, 320 * scale)], outline="#5D6D7E",
                     width=2 * scale)
    return big.resize((width, height), Image.LANCZOS)


def photograph(size: int = 300) -> Image.Image:
    """A smooth gradient with noise: far more colors than a palette can keep within the tolerance."""
    import numpy as np
    rng = np.random.default_rng(7)
    x = np.linspace(0, 255, size)
    pixels = np.stack(np.broadcast_arrays(x[None, :], x[:, None], (x[None, :] + x[:, None]) / 2), axis=2)
    pixels = pixels + rng.normal(0, 14, pixels.shape)
    return Image.fromarray(np.clip(pixels, 0, 255).astype("uint8"), "RGB")


SAMPLE_LABEL = base64.b64encode(png_bytes(Image.new("RGB", (8, 8), (234, 242, 248)))).decode()
DRAWIO_SVG = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="874px" height="398px" viewBox="-0.5 -0.5 874 398" style="background-color: #FFFFFF;"><rect x="-0.5" y="-0.5" width="874" height="398" fill="#FFFFFF"/><defs/><g>
<g data-cell-id="frame"><rect x="10" y="0" width="860" height="394" fill="none" stroke="none" pointer-events="all"/></g>
<g data-cell-id="box"><rect x="20" y="20" width="190" height="66" rx="4" ry="4" fill="#EAF2F8" stroke="#1A5276" stroke-width="1.5"/>
<switch><foreignObject style="overflow: visible; text-align: left;" width="100%" height="100%" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility"><div xmlns="http://www.w3.org/1999/xhtml">Customer</div></foreignObject><image x="30" y="40" width="60" height="20" xlink:href="data:image/png;base64,{SAMPLE_LABEL}"/></switch></g>
<g data-cell-id="decision"><path d="M 400 30 L 470 80 L 400 130 L 330 80 Z" fill="#FEF5E7" stroke="#8A5D00" stroke-width="1.5"/><text x="400" y="85" text-anchor="middle" font-family="Helvetica" font-size="13px" fill="#2C3E50">Approved?</text></g>
<g data-cell-id="edge"><path d="M 210 53 L 330 80" fill="none" stroke="#5D6D7E" stroke-width="1.5" stroke-miterlimit="10" pointer-events="stroke"/><path d="M 334 81 L 326 84 L 328 80 L 326 76 Z" fill="#5D6D7E"/></g>
<g data-cell-id="ellipse"><ellipse cx="600" cy="80" rx="60" ry="40" fill="#E8F6F3" stroke="#117A65" stroke-width="1.5"/></g></g></svg>
"""


class StubRenderer(fr.Renderer):
    """Stands in for Draw.io: writes a diagram PNG of the requested width, or whatever `fault` says."""

    name = "Stub"
    source_kind = "drawio"
    calls: list[str] = []
    fault: str | None = None
    ratio: float | None = None

    def locate(self) -> str:
        return "stub"

    def render(self, source: Path, target: Path) -> None:
        type(self).calls.append(source.name)
        if type(self).fault == "error":
            raise fr.RasterError("Stub rendering failed with exit code 3.\nsomething went wrong")
        if type(self).fault == "empty":
            raise fr.RasterError("Stub reported success but made no PNG.")
        width = self.settings.width
        ratio = type(self).ratio or 398 / 874
        target.parent.mkdir(parents=True, exist_ok=True)
        diagram(width // 2, int(width // 2 * ratio)).resize((width, int(width * ratio)), Image.LANCZOS).save(target)


def make_project(root: Path, stems: tuple[str, ...] = ("fig-01-01-sample",), *, extra: str = "") -> None:
    (root / "visuals" / "svg").mkdir(parents=True, exist_ok=True)
    (root / "visuals" / "src").mkdir(parents=True, exist_ok=True)
    for stem in stems:
        (root / "visuals" / "svg" / f"{stem}.svg").write_text(DRAWIO_SVG, encoding="utf-8")
        (root / "visuals" / "src" / f"{stem}.drawio").write_text(f"<mxfile><diagram>{stem}{extra}</diagram></mxfile>",
                                                                 encoding="utf-8")


def settings(**overrides) -> fr.Settings:
    values = {"width": 800, "cache_dir": "cache"}
    values.update(overrides)
    return fr.Settings(**values)


@needs_numpy
class EncodingTests(unittest.TestCase):
    def test_a_diagram_becomes_a_small_palette_with_the_background_exactly_white(self) -> None:
        source = diagram()
        encoding = fr.choose_encoding(source, settings())
        self.assertEqual(encoding.mode, "palette")
        self.assertLessEqual(encoding.colors, 256)
        self.assertLessEqual(encoding.p9999_error, 8)
        data = fr.encode_png(encoding.image, 192)
        with Image.open(io.BytesIO(data)) as decoded:
            self.assertEqual(decoded.mode, "P")
            rgb = decoded.convert("RGB")
        self.assertEqual(rgb.getpixel((0, 0)), (255, 255, 255))
        self.assertLess(len(data), len(png_bytes(source)))
        # Flat fills that fill the most pixels are exact, not merely close.
        self.assertEqual(rgb.getpixel((40, 100)), source.getpixel((40, 100)))

    def test_no_dithering_and_no_new_colors_outside_the_palette(self) -> None:
        encoding = fr.choose_encoding(diagram(), settings())
        palette = encoding.image.getpalette()[: 3 * encoding.colors]
        used = {tuple(palette[3 * i: 3 * i + 3]) for i in set(encoding.image.getdata())}
        self.assertLessEqual(len(used), encoding.colors)

    def test_a_photograph_stays_rgb_and_lossless(self) -> None:
        source = photograph()
        encoding = fr.choose_encoding(source, settings())
        self.assertEqual(encoding.mode, "rgb")
        decoded = Image.open(io.BytesIO(fr.encode_png(encoding.image, 96))).convert("RGB")
        self.assertEqual(list(decoded.getdata()), list(source.getdata()))

    def test_a_figure_that_misses_the_tolerance_takes_the_largest_palette_inside_the_limits(self) -> None:
        strict = settings(tolerance=0.0, min_colors=64, max_colors=128)
        encoding = fr.choose_encoding(diagram(), strict)
        self.assertEqual(encoding.mode, "palette")
        self.assertEqual(encoding.colors, 128)

    def test_palette_can_be_turned_off(self) -> None:
        self.assertEqual(fr.choose_encoding(diagram(), settings(palette=False)).mode, "rgb")

    def test_a_figure_with_few_colors_is_kept_exactly(self) -> None:
        flat = Image.new("RGB", (100, 80), "white")
        ImageDraw.Draw(flat).rectangle((10, 10, 60, 50), fill=(26, 82, 118))
        encoding = fr.choose_encoding(flat, settings())
        self.assertEqual((encoding.mode, encoding.colors, encoding.max_error), ("palette", 2, 0.0))

    def test_transparency_is_flattened_onto_the_background(self) -> None:
        transparent = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
        self.assertEqual(fr.flatten(transparent, "#FFFFFF").getpixel((3, 3)), (255, 255, 255))

    def test_output_is_deterministic(self) -> None:
        first = fr.encode_png(fr.choose_encoding(diagram(), settings()).image, 192)
        second = fr.encode_png(fr.choose_encoding(diagram(), settings()).image, 192)
        self.assertEqual(first, second)

    def test_the_palette_range_must_hold_a_size(self) -> None:
        with self.assertRaises(fr.RasterError):
            settings(min_colors=250, max_colors=255).steps()


class SettingsTests(unittest.TestCase):
    def test_the_book_settings_file_loads(self) -> None:
        loaded = fr.load_settings(ROOT)
        self.assertEqual((loaded.renderer, loaded.width, loaded.max_colors), ("drawio", 1728, 256))

    def test_overrides_beat_the_file(self) -> None:
        self.assertEqual(fr.load_settings(ROOT, width=900, renderer="rsvg").width, 900)

    def test_unknown_renderer_and_small_width_are_refused(self) -> None:
        with self.assertRaises(fr.RasterError):
            fr.load_settings(ROOT, renderer="photoshop")
        with self.assertRaises(fr.RasterError):
            fr.load_settings(ROOT, width=50)

    def test_cache_key_changes_with_the_pixels_not_with_logging(self) -> None:
        self.assertNotEqual(settings(width=800).render_fields(), settings(width=900).render_fields())
        self.assertEqual(settings(timeout=10).render_fields(), settings(timeout=99).render_fields())
        self.assertEqual(settings(timeout=10).encode_fields(), settings(timeout=99).encode_fields())


class RendererTests(unittest.TestCase):
    def fake(self, cls, binary="/opt/tool"):
        renderer = cls.__new__(cls)
        renderer.settings = settings(width=1728, background="#FFFFFF")
        renderer.binary = binary
        return renderer

    def test_inkscape_command_line(self) -> None:
        command = self.fake(fr.InkscapeRenderer).command(Path("in.svg"), Path("out.png"))
        self.assertEqual(command[0], "/opt/tool")
        for part in ("--export-type=png", "--export-filename=out.png", "--export-width=1728",
                     "--export-background=#FFFFFF", "--export-background-opacity=1"):
            self.assertIn(part, command)
        self.assertEqual(command[-1], "in.svg")

    def test_rsvg_command_line(self) -> None:
        command = self.fake(fr.RsvgRenderer).command(Path("in.svg"), Path("out.png"))
        self.assertEqual(command[1:], ["-f", "png", "-w", "1728", "-b", "#FFFFFF", "-o", "out.png", "in.svg"])

    def test_drawio_command_line_fits_the_width_and_adds_no_border(self) -> None:
        command = self.fake(fr.DrawioRenderer).command(Path("in.drawio"), Path("out.png"))
        self.assertEqual(command[1:5], ["-x", "-f", "png", "--width"])
        self.assertIn("1728", command)
        self.assertNotIn("--border", command)

    def test_a_missing_inkscape_says_how_to_get_it(self) -> None:
        with patch.dict(os.environ, {}, clear=False), patch("shutil.which", return_value=None), \
                patch.object(fr.os, "name", "posix"):
            os.environ.pop("INKSCAPE_BIN", None)
            with self.assertRaises(fr.RasterError) as raised:
                fr.InkscapeRenderer(settings())
        self.assertIn("Inkscape is not installed", str(raised.exception))
        self.assertIn("INKSCAPE_BIN", str(raised.exception))

    def test_an_explicit_binary_that_does_not_exist_is_an_error(self) -> None:
        with patch.dict(os.environ, {"INKSCAPE_BIN": str(ROOT / "no" / "such" / "inkscape")}):
            with self.assertRaises(fr.RasterError) as raised:
                fr.InkscapeRenderer(settings())
        self.assertIn("does not exist", str(raised.exception))

    def test_a_failing_tool_reports_its_output(self) -> None:
        with self.assertRaises(fr.RasterError) as raised:
            fr.run_tool([sys.executable, "-c", "import sys; print('boom'); sys.exit(4)"], "Tool", 30)
        self.assertIn("exit code 4", str(raised.exception))
        self.assertIn("boom", str(raised.exception))

    def test_a_tool_that_cannot_start_and_one_that_hangs_are_errors(self) -> None:
        with self.assertRaises(fr.RasterError):
            fr.run_tool([str(ROOT / "no-such-tool.exe")], "Tool", 30)
        with self.assertRaises(fr.RasterError) as raised:
            fr.run_tool([sys.executable, "-c", "import time; time.sleep(30)"], "Tool", 1)
        self.assertIn("did not finish", str(raised.exception))

    def test_a_renderer_that_writes_nothing_is_an_error(self) -> None:
        class Silent(fr.Renderer):
            name = "Silent"

            def locate(self) -> str:
                return "silent"

            def command(self, source: Path, target: Path) -> list[str]:
                return [sys.executable, "-c", "pass"]

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(fr.RasterError) as raised:
                Silent(settings()).render(Path("x.svg"), Path(temp) / "x.png")
        self.assertIn("made no PNG", str(raised.exception))


class NameTests(unittest.TestCase):
    def test_plain_names_pass_and_repeats_collapse(self) -> None:
        self.assertEqual(fr.check_stems(["fig-01-a", "fig-02.b", "fig-01-a"]), ["fig-01-a", "fig-02.b"])

    def test_names_that_are_paths_or_empty_are_refused(self) -> None:
        for bad in ("../x", "a/b", "a\\b", "", ".hidden", "with space", "ends."):
            with self.assertRaises(fr.RasterError, msg=bad):
                fr.check_stems([bad])

    def test_names_that_differ_only_in_case_collide(self) -> None:
        with self.assertRaises(fr.RasterError) as raised:
            fr.check_stems(["Fig-01", "fig-01"])
        self.assertIn("case-insensitive", str(raised.exception))


class SvgSizeTests(unittest.TestCase):
    def write(self, text: str) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return Path(handle.name)

    def test_size_comes_from_width_and_height(self) -> None:
        self.assertEqual(fr.svg_size(self.write(DRAWIO_SVG)), (874.0, 398.0))

    def test_units_are_converted_to_pixels(self) -> None:
        path = self.write('<svg xmlns="http://www.w3.org/2000/svg" width="1in" height="72pt"/>')
        self.assertEqual(fr.svg_size(path), (96.0, 96.0))

    def test_the_view_box_is_the_fallback(self) -> None:
        path = self.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 150"/>')
        self.assertEqual(fr.svg_size(path), (300.0, 150.0))

    def test_broken_svg_is_an_error(self) -> None:
        with self.assertRaises(fr.RasterError):
            fr.svg_size(self.write("<svg"))
        with self.assertRaises(fr.RasterError):
            fr.svg_size(self.write('<svg xmlns="http://www.w3.org/2000/svg"/>'))


@needs_numpy
class EnsureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="Libro de contabilidad ü ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        StubRenderer.calls = []
        StubRenderer.fault = None
        StubRenderer.ratio = None
        patcher = patch.dict(fr.RENDERERS, {"drawio": StubRenderer})
        patcher.start()
        self.addCleanup(patcher.stop)
        make_project(self.root, ("fig-01-01-a", "fig-01-02-b"))

    def run_ensure(self, stems=None, **kwargs):
        return fr.ensure(self.root, stems, settings=kwargs.pop("settings", settings()), **kwargs)

    def test_makes_a_png_for_each_figure_in_an_unusual_path(self) -> None:
        results = self.run_ensure()
        self.assertEqual([r.status for r in results], ["rendered", "rendered"])
        for result in results:
            self.assertTrue(result.path.is_file())
            self.assertEqual(result.path.parent, self.root / "cache")
            with Image.open(result.path) as image:
                self.assertEqual(image.size[0], 800)

    def test_the_png_is_as_large_on_the_page_as_the_svg(self) -> None:
        result = self.run_ensure(["fig-01-01-a"])[0]
        with Image.open(result.path) as image:
            dpi = image.info["dpi"][0]
        self.assertAlmostEqual(800 / dpi * 96, 874, delta=2)
        self.assertAlmostEqual(result.entry["dpi"], 96 * 800 / 874, places=2)

    def test_the_aspect_ratio_is_the_svgs(self) -> None:
        entry = self.run_ensure(["fig-01-01-a"])[0].entry
        self.assertAlmostEqual(entry["width"] / entry["height"], 874 / 398, delta=874 / 398 * 0.005)

    def test_a_distorted_render_is_refused(self) -> None:
        StubRenderer.ratio = 0.6
        with self.assertRaises(fr.RasterError) as raised:
            self.run_ensure(["fig-01-01-a"])
        self.assertIn("aspect ratio", str(raised.exception))
        self.assertFalse((self.root / "cache" / "fig-01-01-a.png").exists())

    def test_a_second_build_renders_nothing(self) -> None:
        self.run_ensure()
        calls = len(StubRenderer.calls)
        again = self.run_ensure()
        self.assertEqual([r.status for r in again], ["cached", "cached"])
        self.assertEqual(len(StubRenderer.calls), calls)

    def test_a_changed_source_renders_only_that_figure(self) -> None:
        self.run_ensure()
        (self.root / "visuals" / "src" / "fig-01-02-b.drawio").write_text("<mxfile>changed</mxfile>", encoding="utf-8")
        StubRenderer.calls = []
        again = self.run_ensure()
        self.assertEqual({r.stem: r.status for r in again}, {"fig-01-01-a": "cached", "fig-01-02-b": "rendered"})
        self.assertEqual(StubRenderer.calls, ["fig-01-02-b.drawio"])

    def test_line_endings_in_the_source_do_not_matter(self) -> None:
        self.run_ensure()
        path = self.root / "visuals" / "src" / "fig-01-01-a.drawio"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") + b"")
        path.write_bytes(path.read_bytes())
        StubRenderer.calls = []
        self.assertEqual(self.run_ensure(["fig-01-01-a"])[0].status, "cached")

    def test_a_new_render_setting_renders_again(self) -> None:
        self.run_ensure()
        StubRenderer.calls = []
        again = self.run_ensure(settings=settings(width=900))
        self.assertEqual([r.status for r in again], ["rendered", "rendered"])

    def test_a_new_palette_setting_reduces_again_without_a_render(self) -> None:
        self.run_ensure()
        StubRenderer.calls = []
        again = self.run_ensure(settings=settings(max_colors=128))
        self.assertEqual([r.status for r in again], ["reduced", "reduced"])
        self.assertEqual(StubRenderer.calls, [])

    def test_force_renders_everything(self) -> None:
        self.run_ensure()
        StubRenderer.calls = []
        again = self.run_ensure(force=True)
        self.assertEqual([r.status for r in again], ["rendered", "rendered"])

    def test_a_png_that_was_changed_or_deleted_is_made_again(self) -> None:
        self.run_ensure(["fig-01-01-a"])
        target = self.root / "cache" / "fig-01-01-a.png"
        target.write_bytes(b"not a png")
        self.assertEqual(self.run_ensure(["fig-01-01-a"])[0].status, "reduced")
        target.unlink()
        self.assertEqual(self.run_ensure(["fig-01-01-a"])[0].status, "reduced")
        for raw in (self.root / "cache" / "raw").glob("*.png"):
            raw.unlink()
        target.unlink()
        self.assertEqual(self.run_ensure(["fig-01-01-a"])[0].status, "rendered")

    def test_a_duplicate_request_renders_once(self) -> None:
        results = self.run_ensure(["fig-01-01-a", "fig-01-01-a"])
        self.assertEqual(len(results), 1)
        self.assertEqual(StubRenderer.calls, ["fig-01-01-a.drawio"])

    def test_a_failed_conversion_stops_names_the_figure_and_keeps_earlier_work(self) -> None:
        self.run_ensure(["fig-01-01-a"])
        StubRenderer.fault = "error"
        with self.assertRaises(fr.RasterError) as raised:
            self.run_ensure(force=True)
        self.assertIn("fig-01-01-a", str(raised.exception))
        self.assertIn("something went wrong", str(raised.exception))
        leftovers = [p.name for p in (self.root / "cache").rglob("*") if p.name.startswith(".") and p.is_file()
                     and p.name != ".manifest.json.tmp"]
        self.assertEqual(leftovers, [])

    def test_a_figure_without_a_source_is_an_error_not_a_gap(self) -> None:
        (self.root / "visuals" / "src" / "fig-01-02-b.drawio").unlink()
        with self.assertRaises(fr.RasterError) as raised:
            self.run_ensure()
        self.assertIn("No Draw.io source", str(raised.exception))

    def test_a_figure_without_an_svg_is_an_error(self) -> None:
        with self.assertRaises(fr.RasterError) as raised:
            self.run_ensure(["fig-99-missing"])
        self.assertIn("No SVG", str(raised.exception))

    def test_verify_reports_stale_missing_and_changed_pngs(self) -> None:
        self.assertEqual(len(fr.verify(self.root, settings=settings())), 2)
        self.run_ensure()
        self.assertEqual(fr.verify(self.root, settings=settings()), [])
        (self.root / "visuals" / "src" / "fig-01-01-a.drawio").write_text("<mxfile>new</mxfile>", encoding="utf-8")
        (self.root / "cache" / "fig-01-02-b.png").write_bytes(b"x")
        problems = fr.verify(self.root, settings=settings())
        self.assertEqual(len(problems), 2)

    def test_prune_removes_figures_that_no_longer_exist(self) -> None:
        self.run_ensure()
        (self.root / "visuals" / "svg" / "fig-01-02-b.svg").unlink()
        removed = fr.prune(self.root, settings=settings())
        self.assertEqual(sorted(p.name for p in removed), ["fig-01-02-b.png", "fig-01-02-b.png"])
        self.assertNotIn("fig-01-02-b", fr.read_manifest(self.root / "cache")["figures"])
        self.assertTrue((self.root / "cache" / "fig-01-01-a.png").is_file())

    def test_the_manifest_survives_an_interrupted_build(self) -> None:
        StubRenderer.fault = None
        original = StubRenderer.render
        state = {"count": 0}

        def flaky(self_, source, target):
            state["count"] += 1
            if state["count"] == 2:
                raise fr.RasterError("interrupted")
            return original(self_, source, target)

        with patch.object(StubRenderer, "render", flaky):
            with self.assertRaises(fr.RasterError):
                self.run_ensure()
        figures = fr.read_manifest(self.root / "cache")["figures"]
        self.assertEqual(list(figures), ["fig-01-01-a"])
        StubRenderer.calls = []
        self.run_ensure()
        self.assertEqual(StubRenderer.calls, ["fig-01-02-b.drawio"])

    def test_a_damaged_manifest_is_a_clear_error(self) -> None:
        self.run_ensure()
        (self.root / "cache" / "manifest.json").write_text("{not json", encoding="utf-8")
        with self.assertRaises(fr.RasterError) as raised:
            self.run_ensure()
        self.assertIn("manifest.json", str(raised.exception))

    def test_the_command_line_prints_names_and_paths_for_the_filter(self) -> None:
        make_project(self.root, ("fig-01-01-a",))
        (self.root / "visuals").joinpath("ebook-figures.yml").write_text("renderer: rsvg\nwidth: 600\ncache-dir: cache\n",
                                                                         encoding="utf-8")
        exe = shutil.which("rsvg-convert")
        if not exe and not Path(r"C:\tools\rsvg-convert.exe").is_file():
            self.skipTest("rsvg-convert is not installed")
        completed = subprocess.run([sys.executable, str(ROOT / "scripts" / "figure_raster.py"), "--root", str(self.root),
                                    "ensure", "--porcelain", "fig-01-01-a"], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "fig-01-01-a\tcache/fig-01-01-a.png")

    def test_the_command_line_fails_with_a_message_on_both_streams_for_the_filter(self) -> None:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts" / "figure_raster.py"), "--root", str(self.root),
                                    "ensure", "--porcelain", "fig-99-missing"], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("No SVG", completed.stdout)
        self.assertIn("No SVG", completed.stderr)


def rsvg_available() -> bool:
    return bool(shutil.which("rsvg-convert") or Path(r"C:\tools\rsvg-convert.exe").is_file())


@needs_numpy
@unittest.skipUnless(rsvg_available(), "rsvg-convert is not installed")
class SvgRenderingTests(unittest.TestCase):
    """A real render of a Draw.io-style SVG (text, connectors, a decision shape, a foreignObject with an image)."""

    def test_the_svg_fixture_becomes_a_palette_png_of_the_right_shape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="svg ü ") as temp:
            root = Path(temp)
            make_project(root)
            result = fr.ensure(root, ["fig-01-01-sample"], settings=fr.Settings(renderer="rsvg", width=1200,
                                                                                  cache_dir="cache"))[0]
            with Image.open(result.path) as image:
                self.assertEqual(image.size[0], 1200)
                self.assertAlmostEqual(image.size[0] / image.size[1], 874 / 398, delta=0.02)
                rgb = image.convert("RGB")
            self.assertEqual(rgb.getpixel((2, 2)), (255, 255, 255))
            dark = sum(1 for p in rgb.getdata() if sum(p) < 600)
            self.assertGreater(dark, 500, "the diagram's lines and text are drawn")
            self.assertEqual(result.entry["mode"], "palette")


# --- The Lua filter, under plain Pandoc ---------------------------------------------------------------------

def find_pandoc() -> str | None:
    found = shutil.which("pandoc")
    if found:
        return found
    quarto = shutil.which("quarto")
    if quarto:
        for candidate in (Path(quarto).resolve().parent / "tools").rglob("pandoc*"):
            if candidate.name in ("pandoc", "pandoc.exe"):
                return str(candidate)
    return None


@needs_numpy
@unittest.skipUnless(find_pandoc() and rsvg_available(), "Pandoc or rsvg-convert is not installed")
class FilterTests(unittest.TestCase):
    def setUp(self) -> None:
        # A space, as in the book's own path; Pandoc's Lua mangles non-ASCII text in environment variables.
        self.temp = tempfile.TemporaryDirectory(prefix="Libro de contabilidad ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        make_project(self.root)
        (self.root / "scripts").mkdir()
        shutil.copy2(ROOT / "scripts" / "figure_raster.py", self.root / "scripts" / "figure_raster.py")
        (self.root / "visuals" / "ebook-figures.yml").write_text("renderer: rsvg\nwidth: 900\ncache-dir: cache\n",
                                                                 encoding="utf-8")
        (self.root / "chapter.md").write_text(
            "A figure.\n\n![A caption.](visuals/svg/fig-01-01-sample.svg){#fig-1 fig-alt=\"A diagram\"}\n\n"
            "The same figure again.\n\n![Again.](visuals/svg/fig-01-01-sample.svg)\n", encoding="utf-8")

    def convert(self, target: str, output: str, **env) -> subprocess.CompletedProcess:
        environment = dict(os.environ)
        environment.update({"AA_PROJECT_ROOT": str(self.root), "AA_PYTHON": sys.executable})
        environment.update(env)
        return subprocess.run([find_pandoc(), "chapter.md", "-f", "markdown", "-t", target, "-o", output, "--standalone",
                               "--lua-filter", str(ROOT / "filters" / "raster-figures.lua")],
                              cwd=self.root, env=environment, capture_output=True, text=True)

    def test_docx_gets_the_png_and_no_svg(self) -> None:
        done = self.convert("docx", "out.docx")
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        names = zipfile.ZipFile(self.root / "out.docx").namelist()
        media = [n for n in names if n.startswith("word/media/")]
        self.assertTrue(media and all(n.endswith(".png") for n in media), media)
        self.assertTrue((self.root / "cache" / "fig-01-01-sample.png").is_file())

    def test_epub_gets_the_png_and_no_svg(self) -> None:
        done = self.convert("epub3", "out.epub")
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        names = zipfile.ZipFile(self.root / "out.epub").namelist()
        media = [n for n in names if "/media/" in n]
        self.assertTrue(media and all(n.endswith(".png") for n in media), media)

    def test_html_keeps_the_svg(self) -> None:
        done = self.convert("html", "out.html")
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        html = (self.root / "out.html").read_text(encoding="utf-8")
        self.assertIn("visuals/svg/fig-01-01-sample.svg", html)
        self.assertNotIn("ebook-figures", html)
        self.assertFalse((self.root / "cache").exists(), "HTML does not make the PNGs")

    def test_the_svg_can_be_kept_for_a_comparison_build(self) -> None:
        done = self.convert("docx", "out.docx", AA_EBOOK_FIGURES="svg")
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        self.assertFalse((self.root / "cache").exists())

    def test_a_failed_conversion_stops_the_render(self) -> None:
        done = self.convert("docx", "out.docx", AA_FIGURE_RENDERER="inkscape",
                            INKSCAPE_BIN=str(self.root / "missing-inkscape"))
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("INKSCAPE_BIN", done.stderr + done.stdout)
        self.assertFalse((self.root / "out.docx").exists())

    def test_python_that_is_missing_is_a_clear_error(self) -> None:
        done = self.convert("docx", "out.docx", AA_PYTHON="no-such-python-here", PATH="")
        self.assertNotEqual(done.returncode, 0)


if __name__ == "__main__":
    unittest.main()
