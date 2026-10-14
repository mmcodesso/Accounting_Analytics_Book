"""The artwork behind the print covers: the front cover's background carried across the whole wrap.

The front cover's picture (visuals/cover/background.png, one 8.5 x 11 in page) is placed on the front face
and continued to the left across the spine and the back by mirroring it at its edges, so the rising chart
and the dotted surface run on without a seam. The bleed beyond the trim is the same reflection. Behind the
back cover's text the picture is darkened in a soft rectangle, so the synopsis reads on it.

Resolution: the source is 1103 x 1426 pixels (about 130 ppi on the page); it is resampled to 300 ppi
(IngramSpark's minimum for images) with Lanczos and a light unsharp mask, and a little noise is added
before the JPEG so the dark gradients do not band. Resampling cannot add detail: the dots of the surface
are as soft as the source. A background made again at 300 ppi or more would replace the source file here.

The CMYK copy is converted with Ghostscript's own SWOP profile (the one the PDF/X output intent names)
and its total ink is held to 240%, IngramSpark's limit.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageFilter

from scripts.print.cover_template import PT, Box, Template

SOURCE_IN = (8.5, 11.0)          # the source picture covers one 8.5 x 11 in page
TARGET_PPI = 300
MAX_TOTAL_INK = 240.0            # percent
NAVY = (3, 9, 36)                # the picture's dark ground, for the darkened rectangles


@dataclass
class Art:
    rgb: np.ndarray              # height x width x 3, uint8, at `ppi`
    ppi: int
    box: Box                     # the art box on the page, in points

    @property
    def size(self) -> tuple[int, int]:
        return self.rgb.shape[1], self.rgb.shape[0]

    def px(self, x_pt: float, y_pt: float) -> tuple[float, float]:
        """A page point (points) in pixels of this image."""
        return (x_pt - self.box.x0) / PT * self.ppi, (y_pt - self.box.y0) / PT * self.ppi


def _reflect(index: np.ndarray, length: int) -> np.ndarray:
    """Mirror an index range back into 0..length-1 (symmetric about both edges, repeating)."""
    period = 2 * length
    index = np.mod(index, period)
    return np.where(index >= length, period - 1 - index, index)


def _left_columns(index: np.ndarray, length: int, strip: int) -> np.ndarray:
    """Source columns for canvas columns `index` (0 = the picture's left edge, negative = further left).

    To the right of the edge the picture is used as it is (reflected back at its right edge for the
    bleed). To the left only the picture's leftmost `strip` columns are used, mirrored over and over: the
    rising chart stays on the front, and the back carries the low start of the chart and the surface,
    which leaves the dark upper part free for text.
    """
    inside = _reflect(index, length)
    outside = _reflect(index, strip)
    return np.where(index < 0, outside, inside)


def load_source(path: Path, ppi: int = TARGET_PPI) -> Image.Image:
    """The background resampled to SOURCE_IN at `ppi`, lightly sharpened."""
    image = Image.open(path).convert('RGB')
    size = (round(SOURCE_IN[0] * ppi), round(SOURCE_IN[1] * ppi))
    image = image.resize(size, Image.LANCZOS)
    return image.filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))


def compose(template: Template, source: Path, ppi: int = TARGET_PPI, strip_in: float = 3.4) -> Art:
    """The artwork for the template's whole bleed box (`strip_in`: width of the strip mirrored leftward)."""
    picture = np.asarray(load_source(source, ppi))
    pic_h, pic_w = picture.shape[:2]
    box = template.art
    width, height = round(box.w / PT * ppi), round(box.h / PT * ppi)
    # The picture's bottom right corner sits at the front face's: its top left corner, in canvas pixels.
    left = (template.front.x1 - SOURCE_IN[0] * PT - box.x0) / PT * ppi
    top = (template.front.y1 - SOURCE_IN[1] * PT - box.y0) / PT * ppi
    columns = _left_columns(np.arange(width) - round(left), pic_w, round(strip_in * ppi))
    rows = _reflect(np.arange(height) - round(top), pic_h)
    return Art(rgb=picture[np.ix_(rows, columns)].copy(), ppi=ppi, box=box)


def darken(art: Art, area: Box, strength: float, feather_in: float = 0.6, color=NAVY) -> None:
    """Blend a soft-edged rectangle (page points) toward the picture's dark ground, in place."""
    x0, y0 = art.px(area.x0, area.y0)
    x1, y1 = art.px(area.x1, area.y1)
    feather = feather_in * art.ppi
    xs = np.arange(art.rgb.shape[1], dtype=np.float32)
    ys = np.arange(art.rgb.shape[0], dtype=np.float32)
    ramp_x = np.clip(np.minimum(xs - x0, x1 - xs) / feather + 0.5, 0, 1)
    ramp_y = np.clip(np.minimum(ys - y0, y1 - ys) / feather + 0.5, 0, 1)
    # smoothstep, so the edge of the rectangle never shows as a line
    ramp_x = ramp_x * ramp_x * (3 - 2 * ramp_x)
    ramp_y = ramp_y * ramp_y * (3 - 2 * ramp_y)
    amount = (strength * np.outer(ramp_y, ramp_x))[..., None]
    ground = np.array(color, dtype=np.float32)
    art.rgb[:] = np.clip(art.rgb * (1 - amount) + ground * amount, 0, 255).astype(np.uint8)


def with_noise(rgb: np.ndarray, sigma: float = 0.9, seed: int = 20270101) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, size=rgb.shape[:2]).astype(np.float32)[..., None]
    return np.clip(rgb.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def jpeg_bytes(rgb: np.ndarray, quality: int, ppi: int | None = None) -> bytes:
    buffer = io.BytesIO()
    kwargs = {'dpi': (ppi, ppi)} if ppi else {}
    Image.fromarray(rgb).save(buffer, 'JPEG', quality=quality, subsampling=0, optimize=True, **kwargs)
    return buffer.getvalue()


def proxy_jpeg(art: Art, width: int = 2400, quality: int = 86) -> bytes:
    """A small copy for the Draw.io source: enough to lay the text out, never printed."""
    image = Image.fromarray(art.rgb)
    height = round(image.height * width / image.width)
    return jpeg_bytes(np.asarray(image.resize((width, height), Image.LANCZOS)), quality)


def cmyk_profile_path(gs_path: str) -> Path:
    return Path(gs_path).resolve().parent.parent / 'iccprofiles' / 'default_cmyk.icc'


def _transforms(profile: Path):
    srgb = ImageCms.createProfile('sRGB')
    swop = ImageCms.getOpenProfile(str(profile))
    kwargs = {'renderingIntent': ImageCms.Intent.RELATIVE_COLORIMETRIC, 'flags': ImageCms.Flags.BLACKPOINTCOMPENSATION}
    return (ImageCms.buildTransform(srgb, swop, 'RGB', 'CMYK', **kwargs),
            ImageCms.buildTransform(swop, srgb, 'CMYK', 'RGB', **kwargs))


def _icc_cmyk(rgb: np.ndarray, forward) -> np.ndarray:
    """RGB points (n x 3, uint8) to CMYK percentages (n x 4) through the profile."""
    out = ImageCms.applyTransform(Image.fromarray(rgb.reshape(1, -1, 3)), forward)
    return np.asarray(out).reshape(-1, 4).astype(np.float32) / 255.0 * 100.0


def _icc_rgb(cmyk: np.ndarray, backward) -> np.ndarray:
    """CMYK percentages (n x 4) to the sRGB (n x 3, uint8) the profile prints them as."""
    data = np.clip(np.rint(cmyk * 2.55), 0, 255).astype(np.uint8).reshape(1, -1, 4)
    out = ImageCms.applyTransform(Image.fromarray(data, 'CMYK'), backward)
    return np.asarray(out).reshape(-1, 3)


def _lab(rgb: np.ndarray) -> np.ndarray:
    x = rgb.astype(np.float32) / 255.0
    x = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    matrix = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], dtype=np.float32)
    xyz = x @ matrix.T / np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def _limit_ink(points: np.ndarray, raw: np.ndarray, forward, backward, limit: float, seed: int = 7) -> np.ndarray:
    """CMYK for the colors whose profile conversion uses more than `limit` percent ink: the mix of inks that
    adds up to `limit` and prints closest (in Lab) to what the profile would have printed. The deep navy of the
    artwork is one of them; scaling its inks back evenly turns it gray and violet, so the search keeps its hue
    and its depth, mostly by giving the shadows more black and less of the colored inks."""
    rng = np.random.default_rng(seed)
    target = _lab(_icc_rgb(raw, backward))
    total = raw.sum(axis=1)
    out = raw.copy()
    heavy = np.where(total > limit)[0]
    if heavy.size == 0:
        return out
    best = raw[heavy] * (limit / total[heavy])[:, None]
    best_cost = np.linalg.norm(_lab(_icc_rgb(best, backward)) - target[heavy], axis=1)
    samples = 1600
    for sigma in (22.0, 12.0, 6.0, 3.0, 1.5):
        noise = rng.normal(0.0, sigma, size=(heavy.size, samples, 4)).astype(np.float32)
        noise[:, 0, :] = 0.0
        candidates = np.clip(best[:, None, :] + noise, 0.0, 100.0)
        sums = candidates.sum(axis=2, keepdims=True)
        candidates = candidates * np.minimum(1.0, limit / np.maximum(sums, 1e-6))
        flat = candidates.reshape(-1, 4)
        cost = np.linalg.norm(_lab(_icc_rgb(flat, backward)) - np.repeat(target[heavy], samples, axis=0), axis=1)
        cost = cost.reshape(heavy.size, samples)
        pick = cost.argmin(axis=1)
        rows = np.arange(heavy.size)
        better = cost[rows, pick] < best_cost
        best[better] = candidates[rows, pick][better]
        best_cost = np.where(better, cost[rows, pick], best_cost)
    out[heavy] = best
    return out


# the LUT's nodes along each RGB axis: dense in the shadows, where the ink limit bites
LUT_NODES = np.array([0, 2, 4, 6, 8, 10, 13, 16, 20, 25, 30, 36, 44, 54, 66, 80, 100, 125, 160, 200, 255])


@lru_cache(maxsize=4)
def _table(profile: Path, limit: float) -> np.ndarray:
    forward, backward = _transforms(profile)
    n = len(LUT_NODES)
    grid = np.stack(np.meshgrid(LUT_NODES, LUT_NODES, LUT_NODES, indexing='ij'), axis=-1).reshape(-1, 3)
    raw = _icc_cmyk(grid.astype(np.uint8), forward)
    return _limit_ink(grid, raw, forward, backward, limit).reshape(n, n, n, 4)


def to_cmyk(art_rgb: np.ndarray, profile: Path, limit: float = MAX_TOTAL_INK) -> np.ndarray:
    """RGB to CMYK (height x width x 4, uint8, 0 = no ink) through the SWOP profile, ink held to `limit`.

    The conversion is a look-up table over RGB (the profile's CMYK, with the ink limit searched at each
    node) applied with linear interpolation to the colors the picture contains.
    """
    from scipy.interpolate import RegularGridInterpolator
    table = _table(Path(profile), float(limit))
    interpolate = RegularGridInterpolator((LUT_NODES, LUT_NODES, LUT_NODES), table, method='linear')
    flat = art_rgb.reshape(-1, 3)
    packed = (flat[:, 0].astype(np.uint32) << 16) | (flat[:, 1].astype(np.uint32) << 8) | flat[:, 2]
    unique, inverse = np.unique(packed, return_inverse=True)
    colors = np.stack([(unique >> 16) & 255, (unique >> 8) & 255, unique & 255], axis=1).astype(np.float32)
    converted = interpolate(colors)
    total = converted.sum(axis=1, keepdims=True)
    converted = converted * np.minimum(1.0, limit / np.maximum(total, 1e-6))   # interpolation overshoot
    out = converted[inverse].reshape(art_rgb.shape[:2] + (4,))
    return np.clip(np.rint(out / 100.0 * 255.0), 0, 255).astype(np.uint8)


def strip_adobe_marker(jpeg: bytes) -> bytes:
    """The JPEG without its Adobe APP14 segment. Readers differ on whether an Adobe marker means the CMYK
    samples are inverted (Photoshop's convention, told to a PDF consumer by a /Decode array); Pillow writes
    them as they are, so without the marker no reader has anything to guess."""
    out = bytearray(jpeg[:2])
    position = 2
    while position < len(jpeg):
        if jpeg[position] != 0xFF:
            raise ValueError('not a JPEG segment stream')
        marker = jpeg[position + 1]
        if marker == 0xDA:  # start of scan: the rest is entropy-coded data
            out += jpeg[position:]
            break
        length = int.from_bytes(jpeg[position + 2:position + 4], 'big')
        if marker != 0xEE:
            out += jpeg[position:position + 2 + length]
        position += 2 + length
    return bytes(out)


def cmyk_jpeg_bytes(cmyk: np.ndarray, quality: int, ppi: int) -> bytes:
    """A CMYK JPEG (samples as they are, no Adobe marker), for the PDF's DCTDecode with DeviceCMYK."""
    buffer = io.BytesIO()
    Image.fromarray(cmyk, 'CMYK').save(buffer, 'JPEG', quality=quality, subsampling=0, optimize=True,
                                       dpi=(ppi, ppi))
    return strip_adobe_marker(buffer.getvalue())


def decode_cmyk_jpeg(jpeg: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(jpeg)))


def max_total_ink(cmyk: np.ndarray, percentile: float = 100.0) -> float:
    total = cmyk.astype(np.float32).sum(axis=2) / 255.0 * 100.0
    return float(np.percentile(total, percentile))
