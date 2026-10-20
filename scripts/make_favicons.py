"""Makes the website's icons and its sidebar logo from the logo in visuals/branding/favicon.png.

    python scripts/make_favicons.py [--preview FILE]

The logo is wide (two A's over an open book) and has a transparent background, which disappears on a dark browser
tab, so each icon is the mark centered on a white rounded square, with the mark kept inside the circle that Google's
mobile search results crop a favicon to. Every size is resampled from one 1024 px master, so the icons agree.

Written at the project root, because browsers and search engines ask for /favicon.ico there, and listed under
project.resources in _quarto.yml and linked by styles/book-html-head.html:

    favicon.ico             16, 32 and 48 px frames
    favicon-48x48.png       favicon-96x96.png      favicon-192x192.png
    apple-touch-icon.png    180 px, opaque (iOS puts transparent pixels on black)

and visuals/branding/aa-logo.png, the mark alone, cropped, for the sidebar of every page.

--preview writes a contact sheet (each size on white and on dark, and under a circular crop) to look at before
committing the icons. The source is raster, so there is no SVG icon."""
from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'visuals/branding/favicon.png'
LOGO = ROOT / 'visuals/branding/aa-logo.png'

# The mark's width as a share of the icon, and the tile's corner radius as a share of its side.
MARK_SHARE = 0.78
TILE_RADIUS = 0.22
APPLE_SHARE = 0.72
MASTER = 1024

PNG_ICONS = {'favicon-48x48.png': 48, 'favicon-96x96.png': 96, 'favicon-192x192.png': 192}
ICO_SIZES = (16, 32, 48)
APPLE_TOUCH = ('apple-touch-icon.png', 180)
LOGO_WIDTH = 360
LOGO_PADDING = 0.03


def crop_mark(source: Image.Image) -> Image.Image:
    """The logo cropped to the pixels that are not transparent."""
    rgba = source.convert('RGBA')
    box = rgba.getchannel('A').point(lambda value: 255 if value > 8 else 0).getbbox()
    if box is None:
        raise SystemExit(f'{SOURCE} is fully transparent')
    return rgba.crop(box)


def master_tile(mark: Image.Image, share: float, *, rounded: bool) -> Image.Image:
    """The mark centered on a white tile, MASTER px square (a white square with no rounding when not rounded)."""
    tile = Image.new('RGBA', (MASTER, MASTER), (255, 255, 255, 0))
    if rounded:
        ImageDraw.Draw(tile).rounded_rectangle((0, 0, MASTER - 1, MASTER - 1), radius=round(MASTER * TILE_RADIUS),
                                               fill=(255, 255, 255, 255))
    else:
        tile.paste((255, 255, 255, 255), (0, 0, MASTER, MASTER))
    width = round(MASTER * share)
    scaled = mark.resize((width, round(mark.height * width / mark.width)), Image.LANCZOS)
    tile.alpha_composite(scaled, ((MASTER - scaled.width) // 2, (MASTER - scaled.height) // 2))
    return tile


def resample(master: Image.Image, size: int) -> Image.Image:
    return master.resize((size, size), Image.LANCZOS)


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def ico_bytes(frames: list[Image.Image]) -> bytes:
    """An ICO file whose frames are PNG images, each resampled by resample() rather than by Pillow's writer."""
    payloads = [png_bytes(frame) for frame in frames]
    header = struct.pack('<HHH', 0, 1, len(frames))
    offset = len(header) + 16 * len(frames)
    entries = b''
    for frame, payload in zip(frames, payloads):
        side = frame.width if frame.width < 256 else 0
        entries += struct.pack('<BBBBHHII', side, side, 0, 0, 1, 32, len(payload), offset)
        offset += len(payload)
    return header + entries + b''.join(payloads)


def write_if_changed(path: Path, data: bytes) -> bool:
    if path.is_file() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def sidebar_logo(mark: Image.Image) -> Image.Image:
    pad = round(mark.width * LOGO_PADDING)
    padded = Image.new('RGBA', (mark.width + 2 * pad, mark.height + 2 * pad), (255, 255, 255, 0))
    padded.alpha_composite(mark, (pad, pad))
    return padded.resize((LOGO_WIDTH, round(padded.height * LOGO_WIDTH / padded.width)), Image.LANCZOS)


def contact_sheet(master: Image.Image) -> Image.Image:
    """Each size at its own scale (top) and magnified 3x (below), on white, on dark, and under a circular crop."""
    sizes = (16, 32, 48, 96)
    zoom = 3
    cell_width, cell_height = 96 * zoom + 24, 96 + 96 * zoom + 32
    sheet = Image.new('RGB', (cell_width * len(sizes), cell_height * 3), (255, 255, 255))
    for row, (background, circular) in enumerate(((None, False), ((32, 33, 36), False), (None, True))):
        sheet.paste(Image.new('RGB', (sheet.width, cell_height), background or (255, 255, 255)), (0, row * cell_height))
        for column, size in enumerate(sizes):
            icon = resample(master, size)
            if circular:
                mask = Image.new('L', (size * 8, size * 8), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, size * 8 - 1, size * 8 - 1), fill=255)
                icon.putalpha(Image.composite(icon.getchannel('A'), Image.new('L', icon.size, 0),
                                              mask.resize(icon.size, Image.LANCZOS)))
            x, y = column * cell_width + 12, row * cell_height + 8
            sheet.paste(icon, (x, y), icon)
            big = icon.resize((size * zoom, size * zoom), Image.NEAREST)
            sheet.paste(big, (x, y + 96 + 8), big)
    return sheet


def build(preview: Path | None) -> list[str]:
    mark = crop_mark(Image.open(SOURCE))
    rounded = master_tile(mark, MARK_SHARE, rounded=True)
    changed: list[str] = []

    def put(path: Path, data: bytes) -> None:
        if write_if_changed(path, data):
            changed.append(str(path.relative_to(ROOT)))

    put(ROOT / 'favicon.ico', ico_bytes([resample(rounded, size) for size in ICO_SIZES]))
    for name, size in PNG_ICONS.items():
        put(ROOT / name, png_bytes(resample(rounded, size)))
    apple = master_tile(mark, APPLE_SHARE, rounded=False)
    put(ROOT / APPLE_TOUCH[0], png_bytes(resample(apple, APPLE_TOUCH[1]).convert('RGB')))
    put(LOGO, png_bytes(sidebar_logo(mark)))
    if preview:
        preview.parent.mkdir(parents=True, exist_ok=True)
        contact_sheet(rounded).save(preview)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--preview', type=Path, help='write a contact sheet of the icons to this PNG file')
    args = parser.parse_args()
    changed = build(args.preview)
    print('written: ' + ', '.join(changed) if changed else 'all icons are current')


if __name__ == '__main__':
    main()
