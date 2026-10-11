"""The print palette: the CMYK value and the gray level of every color the book's figures use.

The figures (scripts/figures/drawio.py) and the LaTeX styles are drawn in RGB for the screen. The print
interiors (scripts/print/build.py) replace each RGB color with the value below: CMYK for the color
interior and gray for the black-and-white one, so the printer never converts colors itself.

CMYK values come from an ICC conversion of the sRGB color to Ghostscript's SWOP profile (relative
colorimetric), except that text ink is 100% K (IngramSpark: text of 24 pt or less is best in 100%
black) and the near-neutral tints and rules are K only. IngramSpark rejects files above 240% total ink.

Gray levels are chosen by hand rather than by brightness, which would make teal, coral and amber
almost the same gray and print the light tints at 3-6%, which can vanish on the press. Text ink is
black; the five dark fills keep white text at 4.5:1 or better and stay apart; the tints are at least
12% black; the highlight is darker than any tint; rules are at least 40% black.

print/book-print-color.tex and print/book-print-bw.tex repeat the values the LaTeX styles use;
tests/test_print.py checks that they agree with this file.
"""
from __future__ import annotations

MAX_TOTAL_INK = 240  # percent: IngramSpark File Creation Guide, color interiors

# RGB hex (as in scripts/figures/drawio.py) -> (name, CMYK percentages, gray level 0 black .. 1 white)
FIGURE_COLORS: dict[str, tuple[str, tuple[int, int, int, int], float]] = {
    '#2C3E50': ('INK', (0, 0, 0, 100), 0.00),
    '#FFFFFF': ('WHITE', (0, 0, 0, 0), 1.00),
    # The dark fills, spread as far apart as white text allows (lighter than 0.46 drops below 4.5:1),
    # in the order of their screen brightness.
    '#1A5276': ('BLUE', (100, 73, 35, 19), 0.10),
    '#117A65': ('TEAL', (92, 31, 72, 17), 0.20),
    '#B03A2E': ('CORAL', (22, 96, 100, 15), 0.29),
    '#8A5D00': ('AMBER', (37, 61, 100, 27), 0.38),
    '#5D6D7E': ('GRAY', (71, 54, 39, 14), 0.46),
    '#EAF2F8': ('BLUE_TINT', (6, 2, 1, 0), 0.85),
    '#FDEDEC': ('CORAL_TINT', (0, 8, 4, 0), 0.86),
    '#E8F6F3': ('TEAL_TINT', (7, 0, 5, 0), 0.88),
    '#FEF5E7': ('AMBER_TINT', (0, 3, 9, 0), 0.88),
    '#F2F3F4': ('GRAY_TINT', (0, 0, 0, 6), 0.88),
    '#F39C12': ('HIGHLIGHT', (3, 46, 100, 0), 0.70),
    '#D5D8DC': ('RULE', (0, 0, 0, 20), 0.60),
}

# The colors of styles/book-pdf.tex and of the code shading, as print/book-print-*.tex define them:
# LaTeX name -> (CMYK percentages, gray level).
LATEX_COLORS: dict[str, tuple[tuple[int, int, int, int], float]] = {
    'Ink': ((0, 0, 0, 100), 0.00),
    'PrimaryBlue': ((100, 73, 35, 19), 0.00),
    'Teal': ((82, 11, 62, 1), 0.30),
    'Coral': ((3, 91, 95, 0), 0.30),
    'Amber': ((3, 46, 100, 0), 0.50),
    'LightGray': ((0, 0, 0, 6), 0.88),
    'BorderGray': ((0, 0, 0, 20), 0.60),
    'shadecolor': ((0, 0, 0, 6), 0.88),
}

# The learning objectives box (ObjectivesTint in styles/book-pdf.tex is PrimaryBlue!6 on screen): in the
# black-and-white interior a 6% tint of black would be too light to print.
OBJECTIVES_TINT_GRAY = 0.88


def hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_key(rgb: tuple[float, float, float]) -> str:
    """The palette key of an RGB triplet as a PDF content stream writes it (rounded to 1/255)."""
    return '#' + ''.join(f'{round(component * 255):02X}' for component in rgb)


def total_ink(cmyk: tuple[int, int, int, int]) -> int:
    return sum(cmyk)


def contrast(gray_a: float, gray_b: float) -> float:
    """WCAG contrast ratio of two gray levels, read as sRGB values."""
    def luminance(gray: float) -> float:
        return gray / 12.92 if gray <= 0.04045 else ((gray + 0.055) / 1.055) ** 2.4
    high, low = sorted((luminance(gray_a), luminance(gray_b)), reverse=True)
    return (high + 0.05) / (low + 0.05)
