"""Two corrections to the rendered website that Quarto does not make (the project's post-render step, _quarto.yml).

    python scripts/finish_site.py [--site DIR]

1. The sitemap names each page at its canonical address. Quarto lists the homepage in sitemap.xml as
   https://.../index.html, while the <link rel="canonical"> it writes for that page is https://.../ (canonical-url:
   true), so the sitemap named an address that the page itself says is not its own. A page called index.html is
   listed at its directory's address, as its canonical link has it.
2. Every page's og:site_name is the website's name. Quarto sets og:site_name to the book's title after rendering each
   page (the site title handler of its HTML post-processor), whatever book.open-graph.site-name says, which would
   make Open Graph name the site by its title while the structured data (filters/book-metadata.lua) names it
   "Accounting Analytics". The name is indexing.site-identity.name in _quarto.yml.

DIR defaults to $QUARTO_PROJECT_OUTPUT_DIR, which Quarto sets for a post-render script, and then to _book. A render
that writes no sitemap.xml (one file, the PDF, the print profiles) leaves it alone, and HTML already correct is not
rewritten. The slide decks that scripts/build_all.py puts in the site afterwards are not pages of the book."""
from __future__ import annotations

import argparse
import html
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX_LOC = re.compile(r'(<loc>[^<]*/)index\.html(</loc>)')
OG_SITE_NAME = re.compile(r'(<meta\s+property="og:site_name"\s+content=")[^"]*(")')
SKIPPED_DIRECTORIES = {'site_libs', 'slides'}


def normalize_sitemap(sitemap: str) -> str:
    """The sitemap's text with every <loc> that ends in /index.html ending in / instead."""
    return INDEX_LOC.sub(r'\1\2', sitemap)


def set_site_name(page: str, name: str) -> str:
    """The page's HTML with its og:site_name meta tag, if it has one, saying `name`."""
    return OG_SITE_NAME.sub(lambda match: match.group(1) + html.escape(name, quote=True) + match.group(2), page)


def site_name(root: Path = ROOT) -> str | None:
    config = yaml.safe_load((root / '_quarto.yml').read_text(encoding='utf-8'))
    return (((config.get('indexing') or {}).get('site-identity') or {}).get('name')) or None


def rewrite(path: Path, transform) -> bool:
    """Apply transform to the text of path (line endings kept as they are) and report whether it changed."""
    with path.open(encoding='utf-8', newline='') as handle:
        text = handle.read()
    fixed = transform(text)
    if fixed == text:
        return False
    with path.open('w', encoding='utf-8', newline='') as handle:
        handle.write(fixed)
    return True


def finish(site: Path, name: str | None) -> list[str]:
    """Correct the sitemap and the pages under `site`; the paths changed, relative to it."""
    changed: list[str] = []
    sitemap = site / 'sitemap.xml'
    if sitemap.is_file() and rewrite(sitemap, normalize_sitemap):
        changed.append(sitemap.name)
    if name:
        for page in sorted(site.rglob('*.html')):
            relative = page.relative_to(site)
            if SKIPPED_DIRECTORIES.intersection(relative.parts[:-1]):
                continue
            if rewrite(page, lambda text: set_site_name(text, name)):
                changed.append(relative.as_posix())
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--site', type=Path, help='the rendered site (default $QUARTO_PROJECT_OUTPUT_DIR or _book)')
    args = parser.parse_args()
    site = args.site or Path(os.environ.get('QUARTO_PROJECT_OUTPUT_DIR') or '_book')
    if not site.is_absolute():
        site = ROOT / site
    if not site.is_dir():
        return
    changed = finish(site, site_name())
    if changed:
        print(f'finish_site: corrected {len(changed)} file(s): ' + ', '.join(changed[:6])
              + (' ...' if len(changed) > 6 else ''))


if __name__ == '__main__':
    main()
