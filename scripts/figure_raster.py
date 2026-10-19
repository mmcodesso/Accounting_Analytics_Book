#!/usr/bin/env python3
"""Optimized PNG copies of the book's diagrams, for the EPUB and the DOCX.

The website and the PDF keep the diagrams as SVG and vector PDF (scripts/export_drawio_svgs.py). Draw.io's SVG
files are large, because every text label carries a PNG fallback inside a <foreignObject>, and Pandoc puts them
into the EPUB as they are and into the DOCX twice (the SVG and a PNG made from it). filters/raster-figures.lua
therefore swaps each visuals/svg/<name>.svg for the PNG that this module makes, in those two formats only.

For each figure the module

1. renders a PNG of the Draw.io source (visuals/src/<name>.drawio) at the configured width, or of its SVG with
   Inkscape or rsvg-convert, and checks that the aspect ratio is the SVG's;
2. reduces it to an adaptive palette of at most 256 colors, with no dithering, and keeps the smallest palette
   (from min-colors up) whose error stays inside the tolerance. The palette maps the colors the figure uses
   most to exactly themselves, so the white background stays white. A figure that cannot be reduced within the
   tolerance (a photograph, a gradient) stays an optimized RGB PNG;
3. writes it to the cache folder under the figure's name, with a pixel density that makes it as large on the
   page as the SVG was, and records in manifest.json what it was made from.

A figure is made again only when its source, the SVG's size or a setting changed (a SHA-256 over all of them),
so repeated builds reuse the PNGs, and the EPUB and the DOCX share them. Nothing here changes visuals/src,
visuals/svg or visuals/pdf. Settings: visuals/ebook-figures.yml. Usage: python
scripts/figure_raster.py --help.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

CONFIG_FILE = "visuals/ebook-figures.yml"
# Bump when the recipe changes in a way that needs new PNGs.
RECIPE_VERSION = 1
MANIFEST_NAME = "manifest.json"
PALETTE_STEPS = (16, 32, 48, 64, 96, 128, 192, 256)
SVG_DPI = 96.0
# More distinct colors than this is a photograph, never a diagram: it stays RGB without trying a palette.
PHOTO_UNIQUE_COLORS = 250000
# How many of the most frequent colors the palette keeps exactly.
SNAP_COLORS = 16
STEM_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class RasterError(RuntimeError):
    """A figure could not be made; the build must stop rather than leave it out."""


@dataclass(frozen=True)
class Settings:
    renderer: str = "drawio"          # drawio (from the .drawio source), inkscape or rsvg (from the SVG)
    width: int = 1728                 # pixels, whatever the figure's height
    background: str = "#FFFFFF"
    palette: bool = True              # false keeps every figure an RGB PNG
    max_colors: int = 256
    min_colors: int = 64
    tolerance: float = 8.0            # target: the 99.99th percentile of the largest channel difference, of 255
    mean_tolerance: float = 1.5       # limit: the mean of the largest channel difference
    max_tolerance: float = 16.0       # limit: no pixel may differ by more than this
    aspect_tolerance: float = 0.005   # how far the PNG's aspect ratio may be from the SVG's
    timeout: int = 180                # seconds for one render
    cache_dir: str = "outputs/ebook-figures"

    def render_fields(self) -> dict:
        """What changes the rendered PNG: the render key hashes these."""
        return {"renderer": self.renderer, "width": self.width, "background": self.background}

    def encode_fields(self) -> dict:
        """What changes how the render is reduced and saved: the cache key hashes these too."""
        return {"palette": self.palette, "max_colors": self.max_colors, "min_colors": self.min_colors,
                "tolerance": self.tolerance, "mean_tolerance": self.mean_tolerance,
                "max_tolerance": self.max_tolerance}

    def steps(self) -> list[int]:
        steps = [n for n in PALETTE_STEPS if self.min_colors <= n <= self.max_colors]
        if self.palette and not steps:
            raise RasterError(f"No palette size lies between min-colors {self.min_colors} and "
                              f"max-colors {self.max_colors}; use one of {PALETTE_STEPS}.")
        return steps


def load_settings(root: Path, **overrides) -> Settings:
    """Defaults, then visuals/ebook-figures.yml, then the overrides that are not None."""
    values: dict = {}
    config = root / CONFIG_FILE
    if config.is_file():
        import yaml
        block = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        palette = block.get("palette") or {}
        mapping = {"renderer": block.get("renderer"), "width": block.get("width"),
                   "background": block.get("background"), "cache_dir": block.get("cache-dir"),
                   "timeout": block.get("timeout"), "aspect_tolerance": block.get("aspect-tolerance"),
                   "palette": palette.get("enabled"), "max_colors": palette.get("max-colors"),
                   "min_colors": palette.get("min-colors"), "tolerance": palette.get("tolerance"),
                   "mean_tolerance": palette.get("mean-tolerance"), "max_tolerance": palette.get("max-tolerance")}
        values = {k: v for k, v in mapping.items() if v is not None}
    values.update({k: v for k, v in overrides.items() if v is not None})
    settings = Settings(**values)
    if settings.renderer not in RENDERERS:
        raise RasterError(f"Unknown renderer {settings.renderer!r}; choose one of {', '.join(RENDERERS)}.")
    if settings.width < 200:
        raise RasterError(f"width must be at least 200 pixels, not {settings.width}.")
    settings.steps()
    return settings


# --- Rendering ------------------------------------------------------------------------------------------------

def run_tool(command: list[str], what: str, timeout: int) -> None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RasterError(f"{what} did not finish within {timeout} seconds.") from exc
    except OSError as exc:
        raise RasterError(f"{what} could not be started ({exc}).") from exc
    if result.returncode != 0:
        details = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())
        raise RasterError(f"{what} failed with exit code {result.returncode}.\n{details}".rstrip())


class Renderer:
    """Turns one figure's source into a PNG at the requested width."""

    name = ""
    source_kind = ""            # "drawio" or "svg": which file of the figure it reads

    def __init__(self, settings: Settings):
        self.settings = settings
        self.binary = self.locate()

    def locate(self) -> str:
        raise NotImplementedError

    def command(self, source: Path, target: Path) -> list[str]:
        raise NotImplementedError

    def render(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
        run_tool(self.command(source, target), f"{self.name} rendering {source.name}", self.settings.timeout)
        if not target.is_file() or target.stat().st_size == 0:
            raise RasterError(f"{self.name} reported success but made no PNG for {source.name}.")


def find_binary(env: str, names: Sequence[str], windows: Sequence[str], hint: str) -> str:
    explicit = os.environ.get(env)
    if explicit:
        if Path(explicit).expanduser().is_file():
            return str(Path(explicit).expanduser())
        raise RasterError(f"{env} is set to {explicit}, which does not exist.")
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    if os.name == "nt":
        for candidate in windows:
            path = Path(os.path.expandvars(candidate))
            if path.is_file():
                return str(path)
    raise RasterError(f"{hint} Searched PATH for {', '.join(names)}; set {env} to the executable to use another.")


class DrawioRenderer(Renderer):
    name = "Draw.io"
    source_kind = "drawio"

    def locate(self) -> str:
        from scripts import export_drawio_svgs
        try:
            return str(export_drawio_svgs.find_drawio_executable(None))
        except export_drawio_svgs.ExportError as exc:
            raise RasterError(str(exc)) from exc

    def command(self, source: Path, target: Path) -> list[str]:
        # No border: the PNG covers the diagram's bounds, as the SVG's viewBox does.
        return [self.binary, "-x", "-f", "png", "--width", str(self.settings.width), "-o", str(target), str(source)]


class InkscapeRenderer(Renderer):
    name = "Inkscape"
    source_kind = "svg"

    def locate(self) -> str:
        return find_binary("INKSCAPE_BIN", ("inkscape", "inkscape.com"),
                           (r"%ProgramFiles%\Inkscape\bin\inkscape.com", r"%ProgramFiles%\Inkscape\bin\inkscape.exe",
                            r"%LOCALAPPDATA%\Programs\Inkscape\bin\inkscape.com"),
                           "Inkscape is not installed (https://inkscape.org/release/).")

    def command(self, source: Path, target: Path) -> list[str]:
        return [self.binary, "--export-type=png", f"--export-filename={target}", f"--export-width={self.settings.width}",
                f"--export-background={self.settings.background}", "--export-background-opacity=1", str(source)]


class RsvgRenderer(Renderer):
    name = "rsvg-convert"
    source_kind = "svg"

    def locate(self) -> str:
        return find_binary("RSVG_CONVERT_BIN", ("rsvg-convert",), (r"C:\tools\rsvg-convert.exe",),
                           "rsvg-convert is not installed (librsvg).")

    def command(self, source: Path, target: Path) -> list[str]:
        return [self.binary, "-f", "png", "-w", str(self.settings.width), "-b", self.settings.background,
                "-o", str(target), str(source)]


RENDERERS: dict[str, type[Renderer]] = {"drawio": DrawioRenderer, "inkscape": InkscapeRenderer, "rsvg": RsvgRenderer}


# --- Sources and the cache key --------------------------------------------------------------------------------

def text_digest(path: Path) -> str:
    """SHA-256 of a source file, line endings normalized (git may convert them between Windows and Linux)."""
    data = path.read_bytes()
    if path.suffix.lower() in {".drawio", ".svg"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def svg_size(path: Path) -> tuple[float, float]:
    """The SVG's width and height in CSS pixels (the size it has on a page), from its root element."""
    try:
        for _event, element in ET.iterparse(path, events=("start",)):
            root = element
            break
        else:
            raise RasterError(f"{path} is empty.")
    except ET.ParseError as exc:
        raise RasterError(f"{path} is not valid SVG: {exc}") from exc

    def length(value: str | None) -> float | None:
        if not value:
            return None
        match = re.fullmatch(r"\s*([0-9.]+)\s*(px|pt|in|cm|mm|pc)?\s*", value)
        if not match:
            return None
        factor = {"px": 1.0, None: 1.0, "pt": 96 / 72, "in": 96.0, "cm": 96 / 2.54, "mm": 96 / 25.4, "pc": 16.0}
        return float(match.group(1)) * factor[match.group(2)]

    width, height = length(root.get("width")), length(root.get("height"))
    if width is None or height is None:
        box = (root.get("viewBox") or "").replace(",", " ").split()
        if len(box) != 4:
            raise RasterError(f"{path} has neither a width and height nor a viewBox.")
        width, height = float(box[2]), float(box[3])
    if width <= 0 or height <= 0:
        raise RasterError(f"{path} has no size.")
    return width, height


@dataclass
class Figure:
    stem: str
    source: Path            # the file the renderer reads
    svg: Path               # the SVG the book links (its size sets the aspect ratio and the density)
    target: Path            # the cached PNG


def check_stems(stems: Iterable[str]) -> list[str]:
    """Names must be plain file names, and distinct even on a case-insensitive disk."""
    seen: dict[str, str] = {}
    result: list[str] = []
    for stem in stems:
        if not STEM_PATTERN.match(stem) or stem.endswith("."):
            raise RasterError(f"{stem!r} is not a plain figure name (letters, digits, dot, dash and underscore).")
        folded = stem.casefold()
        if folded in seen and seen[folded] != stem:
            raise RasterError(f"Figures {seen[folded]!r} and {stem!r} would share one PNG file name on a "
                              f"case-insensitive disk; rename one.")
        if stem not in result:
            result.append(stem)
        seen[folded] = stem
    return result


class Project:
    """The folders of a book project that the figures live in."""

    def __init__(self, root: Path, settings: Settings):
        self.root = root.resolve()
        self.settings = settings
        self.cache = (self.root / settings.cache_dir)
        self.svg_dir = self.root / "visuals" / "svg"
        self.src_dir = self.root / "visuals" / "src"

    def discover(self) -> list[str]:
        if not self.svg_dir.is_dir():
            raise RasterError(f"{self.svg_dir} does not exist.")
        return check_stems(sorted(path.stem for path in self.svg_dir.glob("*.svg")))

    def figure(self, stem: str, kind: str) -> Figure:
        svg = self.svg_dir / f"{stem}.svg"
        if not svg.is_file():
            raise RasterError(f"No SVG for {stem}: expected {svg}. Export the diagrams "
                              f"(python scripts/export_drawio_svgs.py).")
        source = self.src_dir / f"{stem}.drawio" if kind == "drawio" else svg
        if not source.is_file():
            raise RasterError(f"No Draw.io source for {stem}: expected {source}.")
        return Figure(stem, source, svg, self.cache / f"{stem}.png")

    def relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()


def render_key(settings: Settings, figure: Figure, size: tuple[float, float]) -> str:
    """Identifies the rendered PNG: the source, the SVG's size and the render settings."""
    material = {"recipe": RECIPE_VERSION, "render": settings.render_fields(),
                "source": text_digest(figure.source), "svg_width": size[0], "svg_height": size[1]}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def figure_key(settings: Settings, rendered: str) -> str:
    """Identifies the finished PNG: the render and the settings that reduce it."""
    material = {"recipe": RECIPE_VERSION, "render": rendered, "encode": settings.encode_fields()}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


# --- Reducing the colors --------------------------------------------------------------------------------------

@dataclass
class Encoding:
    mode: str                 # "palette" or "rgb"
    colors: int               # palette entries, or the distinct colors of an RGB image
    mean_error: float
    p9999_error: float
    max_error: float
    image: object = field(repr=False, default=None)


def flatten(image, background: str):
    """The image as RGB on the background color (a transparent export becomes opaque)."""
    from PIL import Image, ImageColor
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        base = Image.new("RGBA", rgba.size, ImageColor.getrgb(background) + (255,))
        return Image.alpha_composite(base, rgba).convert("RGB")
    return image.convert("RGB")


def palette_encoding(unique, inverse, counts, size, colors: int, image) -> Encoding:
    """The image on an adaptive palette of at most `colors` entries, with no dithering.

    Pillow chooses the palette (maximum coverage); every distinct color of the image is then mapped to its nearest
    entry exactly (Pillow's own mapping works on 6 bits a channel, which turns white into off-white), and the
    most frequent colors replace their nearest entries, so flat fills and the background are exact."""
    import numpy as np
    from PIL import Image
    rgb = np.stack([(unique >> 16) & 255, (unique >> 8) & 255, unique & 255], axis=1).astype(np.int32)
    if len(unique) <= colors:
        palette = rgb.copy()
    else:
        reduced = image.quantize(colors=colors, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE)
        raw = np.array(reduced.getpalette()[:3 * colors], dtype=np.int32).reshape(-1, 3)
        palette = np.unique(raw, axis=0)[:colors]
        taken: set[int] = set()
        for index in np.argsort(-counts)[:SNAP_COLORS]:
            distance = ((palette - rgb[index]) ** 2).sum(axis=1)
            nearest = int(distance.argmin())
            if nearest not in taken and distance[nearest] <= 3 * 12 * 12:
                palette[nearest] = rgb[index]
                taken.add(nearest)
    mapped = np.empty(len(unique), dtype=np.int64)
    for start in range(0, len(unique), 8192):
        chunk = rgb[start:start + 8192]
        mapped[start:start + 8192] = ((chunk[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
    error = np.abs(rgb - palette[mapped]).max(axis=1)
    order = np.argsort(error, kind="stable")
    cumulative = np.cumsum(counts[order])
    total = int(cumulative[-1])
    p9999 = float(error[order][min(len(order) - 1, int(np.searchsorted(cumulative, 0.9999 * total)))])
    mean = float((error * counts).sum() / total)
    indices = mapped[inverse].reshape(size[1], size[0]).astype(np.uint8)
    reduced = Image.fromarray(indices, "P")
    flat = np.zeros(768, dtype=np.uint8)
    flat[:palette.size] = palette.astype(np.uint8).ravel()
    reduced.putpalette(flat.tolist())
    return Encoding("palette", len(palette), mean, p9999, float(error.max()), reduced)


def choose_encoding(image, settings: Settings) -> Encoding:
    """The smallest palette that reaches the tolerance; failing that the largest one inside the limits (mean and
    worst pixel); failing that, the RGB image itself."""
    import numpy as np
    rgb = flatten(image, settings.background)
    pixels = np.asarray(rgb)
    packed = ((pixels[..., 0].astype(np.uint32) << 16) | (pixels[..., 1].astype(np.uint32) << 8)
              | pixels[..., 2]).ravel()
    unique, inverse, counts = np.unique(packed, return_inverse=True, return_counts=True)
    original = Encoding("rgb", int(len(unique)), 0.0, 0.0, 0.0, rgb)
    if not settings.palette or len(unique) > PHOTO_UNIQUE_COLORS:
        return original
    if len(unique) <= settings.max_colors:
        return palette_encoding(unique, inverse, counts, rgb.size, len(unique), rgb)
    best = None
    for colors in settings.steps():
        candidate = palette_encoding(unique, inverse, counts, rgb.size, colors, rgb)
        if candidate.mean_error > settings.mean_tolerance or candidate.max_error > settings.max_tolerance:
            continue
        if candidate.p9999_error <= settings.tolerance:
            return candidate
        best = candidate        # within the limits, not within the target: a larger palette may still reach it
    return best or original


def encode_png(image, dpi: float) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True, dpi=(dpi, dpi))
    return buffer.getvalue()


# --- The cache ------------------------------------------------------------------------------------------------

def read_manifest(cache: Path) -> dict:
    path = cache / MANIFEST_NAME
    if not path.is_file():
        return {"version": 1, "figures": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise RasterError(f"{path} is not valid JSON ({exc}); delete it to rebuild the cache.") from exc
    if data.get("version") != 1 or not isinstance(data.get("figures"), dict):
        raise RasterError(f"{path} has an unsupported structure; delete it to rebuild the cache.")
    return data


def write_manifest(cache: Path, manifest: dict) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    temporary = cache / f".{MANIFEST_NAME}.tmp"
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(cache / MANIFEST_NAME)


@dataclass
class Result:
    stem: str
    status: str               # "rendered" or "cached"
    path: Path
    entry: dict
    seconds: float = 0.0


def is_current(entry: dict | None, key: str, target: Path) -> bool:
    return bool(entry and entry.get("key") == key and target.is_file()
                and target.stat().st_size == entry.get("bytes") and file_digest(target) == entry.get("png_sha256"))


def raw_path(project: Project, stem: str) -> Path:
    return project.cache / "raw" / f"{stem}.png"


def is_raw_current(entry: dict | None, rkey: str, path: Path) -> bool:
    return bool(entry and entry.get("render_key") == rkey and path.is_file()
                and file_digest(path) == entry.get("raw_sha256"))


def render_raw(renderer: Renderer, figure: Figure, destination: Path) -> None:
    """Render the figure into the raw cache (atomically)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    scratch = destination.with_name(f".{destination.name}.render.png")
    try:
        renderer.render(figure.source, scratch)
        scratch.replace(destination)
    finally:
        if scratch.exists():
            scratch.unlink()


def make_figure(project: Project, figure: Figure, rkey: str, key: str, size: tuple[float, float],
                raw_file: Path) -> dict:
    """Check the rendered PNG's aspect ratio, reduce its colors and write the finished PNG; return its entry."""
    from PIL import Image
    settings = project.settings
    partial = project.cache / f".{figure.stem}.partial.png"
    try:
        with Image.open(raw_file) as opened:
            opened.load()
            raw = opened.copy()
    except Exception as exc:
        raise RasterError(f"the rendered PNG of {figure.stem} is unreadable: {exc}") from exc
    width, height = raw.size
    drift = abs((width / height) / (size[0] / size[1]) - 1)
    if drift > settings.aspect_tolerance:
        raise RasterError(f"the PNG is {width}x{height} but its SVG is {size[0]:g}x{size[1]:g}; the aspect ratio "
                          f"differs by {drift:.2%} (limit {settings.aspect_tolerance:.2%}).")
    encoding = choose_encoding(raw, settings)
    dpi = SVG_DPI * width / size[0]
    data = encode_png(encoding.image, dpi)
    try:
        partial.write_bytes(data)
        partial.replace(figure.target)
    finally:
        if partial.exists():
            partial.unlink()
    return {"key": key, "render_key": rkey, "source": project.relative(figure.source), "renderer": settings.renderer,
            "width": width, "height": height, "svg_width": size[0], "svg_height": size[1],
            "dpi": round(dpi, 3), "mode": encoding.mode, "colors": encoding.colors,
            "mean_error": round(encoding.mean_error, 4), "p9999_error": encoding.p9999_error,
            "max_error": encoding.max_error, "raw_bytes": raw_file.stat().st_size,
            "raw_sha256": file_digest(raw_file), "bytes": len(data),
            "svg_bytes": figure.svg.stat().st_size, "png_sha256": hashlib.sha256(data).hexdigest()}


def ensure(root: Path, stems: Sequence[str] | None = None, *, settings: Settings | None = None, force: bool = False,
           log: Callable[[str], None] | None = None) -> list[Result]:
    """Make the PNG of each figure (all of them when `stems` is None) unless its cached copy is current.

    Two caches: the renderer's PNG (raw/, made again only when the source, the SVG size or the render settings
    change) and the finished PNG (made again when the palette settings change too, which needs no renderer).
    Stops at the first figure that cannot be made. The manifest is saved after every figure, so a build that was
    interrupted (or stopped by an error) resumes where it was. `force` renders everything again."""
    settings = settings or load_settings(root)
    project = Project(root, settings)
    names = project.discover() if stems is None else check_stems(stems)
    log = log or (lambda message: None)
    manifest = read_manifest(project.cache)
    figures = manifest["figures"]
    renderer: Renderer | None = None
    kind = RENDERERS[settings.renderer].source_kind
    results: list[Result] = []
    for number, stem in enumerate(names, 1):
        figure = project.figure(stem, kind)
        size = svg_size(figure.svg)
        rkey = render_key(settings, figure, size)
        key = figure_key(settings, rkey)
        entry = figures.get(stem)
        if not force and is_current(entry, key, figure.target):
            results.append(Result(stem, "cached", figure.target, entry))
            continue
        started = time.perf_counter()
        raw_file = raw_path(project, stem)
        rendered = force or not is_raw_current(entry, rkey, raw_file)
        try:
            if rendered:
                if renderer is None:
                    renderer = RENDERERS[settings.renderer](settings)
                render_raw(renderer, figure, raw_file)
            figures[stem] = make_figure(project, figure, rkey, key, size, raw_file)
        except RasterError as exc:
            raise RasterError(f"{stem}: {exc}") from exc
        write_manifest(project.cache, manifest)
        seconds = time.perf_counter() - started
        entry = figures[stem]
        results.append(Result(stem, "rendered" if rendered else "reduced", figure.target, entry, seconds))
        log(f"[{number}/{len(names)}] {stem}: {entry['width']}x{entry['height']} {entry['mode']}"
            f"{' ' + str(entry['colors']) if entry['mode'] == 'palette' else ''} "
            f"{entry['bytes']:,} B ({'rendered' if rendered else 'from the cached render'}, {seconds:.1f}s)")
    return results


def verify(root: Path, stems: Sequence[str] | None = None, *, settings: Settings | None = None) -> list[str]:
    """Problems with the cached PNGs (missing, changed, or made from an older source or setting); renders nothing."""
    settings = settings or load_settings(root)
    project = Project(root, settings)
    names = project.discover() if stems is None else check_stems(stems)
    kind = RENDERERS[settings.renderer].source_kind
    figures = read_manifest(project.cache)["figures"]
    problems: list[str] = []
    for stem in names:
        try:
            figure = project.figure(stem, kind)
            key = figure_key(settings, render_key(settings, figure, svg_size(figure.svg)))
        except RasterError as exc:
            problems.append(str(exc))
            continue
        entry = figures.get(stem)
        if entry is None:
            problems.append(f"{stem}: no cached PNG")
        elif not figure.target.is_file():
            problems.append(f"{stem}: {project.relative(figure.target)} is missing")
        elif not is_current(entry, key, figure.target):
            problems.append(f"{stem}: the cached PNG is out of date or was changed")
    return problems


def prune(root: Path, *, settings: Settings | None = None, raw: bool = False) -> list[Path]:
    """Delete cached PNGs (and manifest entries) of figures that no longer exist in visuals/svg.

    With raw=True also delete every renderer PNG (raw/): they are made again when a figure is rendered, and
    while they exist a change of the palette settings needs no render."""
    settings = settings or load_settings(root)
    project = Project(root, settings)
    wanted = set(project.discover())
    manifest = read_manifest(project.cache)
    removed: list[Path] = []
    for stem in sorted(set(manifest["figures"]) - wanted):
        del manifest["figures"][stem]
    for folder, keep in ((project.cache, wanted), (project.cache / "raw", set() if raw else wanted)):
        if folder.is_dir():
            for path in sorted(folder.glob("*.png")):
                if path.stem not in keep:
                    path.unlink()
                    removed.append(path)
    if project.cache.is_dir():
        write_manifest(project.cache, manifest)
    return removed


def summarize(results: Sequence[Result]) -> dict:
    entries = [result.entry for result in results]
    return {"figures": len(results), "rendered": sum(r.status == "rendered" for r in results),
            "cached": sum(r.status == "cached" for r in results),
            "reduced": sum(r.status == "reduced" for r in results),
            "palette": sum(e["mode"] == "palette" for e in entries), "rgb": sum(e["mode"] == "rgb" for e in entries),
            "png_bytes": sum(e["bytes"] for e in entries), "svg_bytes": sum(e["svg_bytes"] for e in entries),
            "raw_bytes": sum(e["raw_bytes"] for e in entries),
            "max_error": max((e["max_error"] for e in entries), default=0.0)}


# --- Command line ---------------------------------------------------------------------------------------------

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimized PNG copies of the book's diagrams for the EPUB and DOCX.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="The book project (default: this repository).")
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--renderer", choices=sorted(RENDERERS), help="Override the configured renderer.")
    common.add_argument("--width", type=int, help="Override the PNG width in pixels.")
    common.add_argument("--no-palette", action="store_true", help="Keep every figure an RGB PNG.")
    common.add_argument("--max-colors", type=int)
    common.add_argument("--min-colors", type=int)
    common.add_argument("--tolerance", type=float)
    ensure_parser = sub.add_parser("ensure", parents=[common], help="Make the PNGs that are missing or out of date.")
    ensure_parser.add_argument("figures", nargs="*", help="Figure names (default with --all: every figure).")
    ensure_parser.add_argument("--all", action="store_true", help="Every figure in visuals/svg.")
    ensure_parser.add_argument("--force", action="store_true", help="Make them again even when current.")
    ensure_parser.add_argument("--porcelain", action="store_true",
                               help="Print 'name<TAB>path' for each figure (the Lua filter reads this).")
    ensure_parser.add_argument("--report", type=Path, help="Write a JSON report of the figures here.")
    sub.add_parser("verify", parents=[common], help="Check the cache without rendering.")
    prune_parser = sub.add_parser("prune", parents=[common], help="Delete PNGs of figures that no longer exist.")
    prune_parser.add_argument("--raw", action="store_true", help="Also delete the renderer PNGs (raw/).")
    sub.add_parser("settings", parents=[common], help="Print the settings in effect.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    try:
        settings = load_settings(
            root, renderer=args.renderer or os.environ.get("AA_FIGURE_RENDERER"), width=args.width,
            palette=False if args.no_palette else None, max_colors=args.max_colors, min_colors=args.min_colors,
            tolerance=args.tolerance)
        if args.command == "settings":
            print(json.dumps(asdict(settings), indent=2))
            return 0
        if args.command == "prune":
            for path in prune(root, settings=settings, raw=args.raw):
                print(f"removed {path}")
            return 0
        if args.command == "verify":
            problems = verify(root, settings=settings)
            for problem in problems:
                print(problem, file=sys.stderr)
            print(f"{len(problems)} problem(s).", file=sys.stderr)
            return 1 if problems else 0
        if not args.all and not args.figures:
            raise RasterError("Name the figures to make, or pass --all.")
        results = ensure(root, None if args.all else args.figures, settings=settings, force=args.force,
                         log=lambda message: print(message, file=sys.stderr, flush=True))
        project = Project(root, settings)
        if args.porcelain:
            for result in results:
                print(f"{result.stem}\t{project.relative(result.path)}")
        total = summarize(results)
        print(f"{total['figures']} figure(s): {total['rendered']} rendered, {total['reduced']} reduced again "
              f"from their cached render, {total['cached']} from the cache; "
              f"{total['palette']} palette, {total['rgb']} RGB; {total['png_bytes'] / 1e6:.1f} MB of PNG "
              f"against {total['svg_bytes'] / 1e6:.1f} MB of SVG.", file=sys.stderr)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({"summary": total, "settings": asdict(settings),
                                               "figures": {r.stem: r.entry for r in results}}, indent=2) + "\n",
                                   encoding="utf-8")
        return 0
    except RasterError as exc:
        # stdout as well as stderr: Pandoc's Lua pipe shows the output of a failed command.
        message = f"figure_raster: {exc}"
        print(message, file=sys.stderr)
        if getattr(args, "porcelain", False):
            print(message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
