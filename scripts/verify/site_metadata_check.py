"""Check the rendered website's search metadata, so that what Google reads survives every rebuild.

Reads the site Quarto rendered (default _book) and the settings in _quarto.yml, and fails on any of these:
  every page   a canonical link that is the page's own address, og:site_name equal to the site's name
               (indexing.site-identity.name), the publisher's links in the footer, and the icon links
  homepage     the title and the short description, og:type and og:url, and one JSON-LD graph with exactly one WebSite
               (name and alternateName from indexing.site-identity) and one Book; the publisher, author and editions take the
               ids that accountinganalyticshub.com gives them (indexing.hub) and the ISBNs and DOI of _quarto.yml;
               no Product node; an offer only on the free editions (PDF, EPUB), with a price of 0; no printed edition
               marked free; every @id used is defined in the graph or on the publisher's website
  site         the icon files (ICO with 16, 32 and 48 px frames, square PNGs of at least 48 px, the 180 px Apple icon)
               and the icon links that resolve to them, a robots.txt with no Disallow, and a sitemap that lists each
               page at its canonical address

    python scripts/verify/site_metadata_check.py [--site _book]

It checks files only, and cannot tell what Google will show; the Search Console steps are in CONTRIBUTING.md."""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKIPPED_DIRECTORIES = {'site_libs', 'slides'}
FREE_EDITIONS = {'pdf', 'epub'}
PNG_ICONS = {'favicon-48x48.png': 48, 'favicon-96x96.png': 96, 'favicon-192x192.png': 192, 'apple-touch-icon.png': 180}
ICO_SIZES = {16, 32, 48}
MAX_DESCRIPTION = 160


class Head(HTMLParser):
    """The parts of a page that the checks read: title, meta tags, links, footer links, JSON-LD scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ''
        self.metas: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.footer_links: list[str] = []
        self.json_ld: list[str] = []
        self._in = ''
        self._footer = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or '' for key, value in attrs}
        if tag == 'title' and not self.title:
            self._in = 'title'
        elif tag == 'meta':
            self.metas.append(values)
        elif tag == 'link':
            self.links.append(values)
        elif tag == 'footer':
            self._footer += 1
        elif tag == 'a' and self._footer and values.get('href'):
            self.footer_links.append(values['href'])
        elif tag == 'script' and values.get('type') == 'application/ld+json':
            self._in = 'json'
            self.json_ld.append('')

    def handle_endtag(self, tag: str) -> None:
        if tag == 'footer' and self._footer:
            self._footer -= 1
        if tag in {'title', 'script'}:
            self._in = ''

    def handle_data(self, data: str) -> None:
        if self._in == 'title':
            self.title += data
        elif self._in == 'json':
            self.json_ld[-1] += data

    def meta(self, key: str) -> list[str]:
        return [m.get('content', '') for m in self.metas if m.get('name') == key or m.get('property') == key]

    def link(self, rel: str) -> list[dict[str, str]]:
        return [link for link in self.links if rel in link.get('rel', '').split()]


def parse(html: str) -> Head:
    head = Head()
    head.feed(html)
    return head


def settings(root: Path = ROOT) -> dict:
    """What the checks expect, from _quarto.yml."""
    config = yaml.safe_load((root / '_quarto.yml').read_text(encoding='utf-8'))
    site = config['book']['site-url'].rstrip('/') + '/'
    return {
        'site': site,
        'title': config['book']['title'],
        'description': config['description'],
        'name': config['indexing']['site-identity']['name'],
        'alternate': list(config['indexing']['site-identity'].get('alternate-name') or []),
        'hub': config['indexing']['hub'],
        'isbn': {key: re.sub(r'[\s-]', '', str(value)) for key, value in config['isbn'].items()},
        'doi': str(config.get('doi') or ''),
    }


def canonical_of(rel: str, site: str) -> str:
    """The canonical address Quarto gives a page: its path under the site, with index.html shortened to the folder."""
    path = rel[:-len('index.html')] if rel == 'index.html' or rel.endswith('/index.html') else rel
    return site + path


def nodes(graph: list) -> list[dict]:
    """Every dict in the graph, nested ones included."""
    found: list[dict] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            found.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(graph)
    return found


def types_of(node: dict) -> list[str]:
    kind = node.get('@type', [])
    return [kind] if isinstance(kind, str) else list(kind)


def check_page(rel: str, html: str, expected: dict) -> list[str]:
    """Problems on any page of the book."""
    head, problems = parse(html), []
    site, hub = expected['site'], expected['hub']
    canonical = [link.get('href', '') for link in head.link('canonical')]
    if canonical != [canonical_of(rel, site)]:
        problems.append(f'{rel}: canonical link is {canonical}, expected {canonical_of(rel, site)}')
    if head.meta('og:site_name') != [expected['name']]:
        problems.append(f'{rel}: og:site_name is {head.meta("og:site_name")}, expected {expected["name"]!r}')
    for url in (hub['url'], hub['book-url']):
        if url not in head.footer_links:
            problems.append(f'{rel}: the footer does not link {url}')
    if not any(link.get('href', '').endswith('favicon.ico') for link in head.link('icon')):
        problems.append(f'{rel}: no <link rel="icon"> for favicon.ico')
    if not head.link('apple-touch-icon'):
        problems.append(f'{rel}: no apple-touch-icon link')
    if any('noindex' in value.lower() for value in head.meta('robots')):
        problems.append(f'{rel}: the page asks not to be indexed')
    return problems


def check_graph(graph: list, expected: dict) -> list[str]:
    problems: list[str] = []
    site, hub = expected['site'], expected['hub']
    everything = nodes(graph)
    sites = [n for n in everything if 'WebSite' in types_of(n)]
    if len(sites) != 1:
        problems.append(f'homepage JSON-LD has {len(sites)} WebSite nodes, expected 1')
    else:
        node = sites[0]
        if node.get('@id') != site + '#website' or node.get('url') != site:
            problems.append(f'WebSite id/url are {node.get("@id")}/{node.get("url")}')
        if node.get('name') != expected['name']:
            problems.append(f'WebSite name is {node.get("name")!r}, expected {expected["name"]!r}')
        alternate = node.get('alternateName')
        alternate = [alternate] if isinstance(alternate, str) else list(alternate or [])
        if alternate != expected['alternate']:
            problems.append(f'WebSite alternateName is {alternate}, expected {expected["alternate"]}')
    books = [n for n in graph if 'Book' in types_of(n)]
    if [b.get('@id') for b in books] != [site + '#book']:
        problems.append(f'homepage JSON-LD top-level Book nodes are {[b.get("@id") for b in books]}')
    for node in everything:
        if 'Product' in types_of(node):
            problems.append(f'{node.get("@id") or node.get("name")}: typed Product')
    defined = {n['@id'] for n in everything if '@id' in n and len(n) > 1}
    for node in everything:
        reference = node.get('@id')
        if reference and len(node) == 1 and reference not in defined and not reference.startswith(hub['url']):
            problems.append(f'@id {reference} is used but defined nowhere')
    by_id = {n['@id']: n for n in everything if '@id' in n and len(n) > 1}
    if hub['url'] + '#organization' not in by_id:
        problems.append(f'no Organization node with the publisher id {hub["url"]}#organization')
    if hub['author-url'] + '#person' not in by_id:
        problems.append(f'no Person node with the author id {hub["author-url"]}#person')
    book = by_id.get(site + '#book', {})
    if book:
        if expected['doi'] and (book.get('identifier') or {}).get('value') != expected['doi']:
            problems.append(f'Book DOI is {(book.get("identifier") or {}).get("value")}, expected {expected["doi"]}')
        if hub['book-url'] not in (book.get('sameAs') or []):
            problems.append(f'Book sameAs does not name the publisher page {hub["book-url"]}')
    editions = {e.get('@id', ''): e for e in book.get('workExample', [])}
    for key, isbn in expected['isbn'].items():
        edition = editions.get(f'{hub["book-url"]}#edition-{key}')
        if edition is None:
            problems.append(f'no edition node for {key} with the publisher\'s id')
            continue
        if edition.get('isbn') != isbn:
            problems.append(f'{key} edition ISBN is {edition.get("isbn")}, expected {isbn}')
        offer = edition.get('offers')
        if key in FREE_EDITIONS:
            if not edition.get('isAccessibleForFree') or not offer or offer.get('price') != 0:
                problems.append(f'{key} edition is free and needs a price-0 offer')
        elif offer or edition.get('isAccessibleForFree'):
            problems.append(f'{key} edition is printed and must carry no offer and no free flag')
    for node in everything:
        if 'Offer' in types_of(node) and node.get('price') != 0:
            problems.append(f'an Offer with price {node.get("price")!r}')
    return problems


def check_homepage(html: str, expected: dict) -> list[str]:
    head, problems = parse(html), []
    site = expected['site']
    if head.title.strip() != expected['title']:
        problems.append(f'homepage title is {head.title.strip()!r}, expected {expected["title"]!r}')
    description = head.meta('description')
    if description != [expected['description']]:
        problems.append(f'homepage description is {description}')
    if len(expected['description']) > MAX_DESCRIPTION:
        problems.append(f'description is {len(expected["description"])} characters, over {MAX_DESCRIPTION}')
    if head.meta('og:type') != ['website'] or head.meta('og:url') != [site]:
        problems.append(f'og:type/og:url are {head.meta("og:type")}/{head.meta("og:url")}')
    if len(head.json_ld) != 1:
        problems.append(f'homepage has {len(head.json_ld)} JSON-LD scripts, expected 1')
        return problems
    try:
        graph = json.loads(head.json_ld[0])['@graph']
    except (ValueError, KeyError) as error:
        return problems + [f'homepage JSON-LD is not a valid graph: {error}']
    return problems + check_graph(graph, expected)


def ico_sizes(data: bytes) -> set[int]:
    reserved, kind, count = struct.unpack('<HHH', data[:6])
    if (reserved, kind) != (0, 1):
        return set()
    return {(data[6 + 16 * i] or 256) for i in range(count)}


def png_size(data: bytes) -> tuple[int, int] | None:
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    return struct.unpack('>II', data[16:24])


def check_icons(site: Path, homepage: str) -> list[str]:
    problems: list[str] = []
    ico = site / 'favicon.ico'
    if not ico.is_file():
        problems.append('favicon.ico is missing from the site')
    elif ico_sizes(ico.read_bytes()) != ICO_SIZES:
        problems.append(f'favicon.ico has frames {sorted(ico_sizes(ico.read_bytes()))}, expected {sorted(ICO_SIZES)}')
    for name, size in PNG_ICONS.items():
        path = site / name
        if not path.is_file():
            problems.append(f'{name} is missing from the site')
        elif png_size(path.read_bytes()) != (size, size):
            problems.append(f'{name} is {png_size(path.read_bytes())}, expected {size}x{size}')
    for link in parse(homepage).links:
        if 'icon' in link.get('rel', '').split() or link.get('rel') == 'apple-touch-icon':
            target = posixpath.normpath(posixpath.join('.', urlsplit(link.get('href', '')).path.lstrip('/')))
            if not (site / target).is_file():
                problems.append(f'icon link {link.get("href")} does not resolve in the site')
    return problems


def check_robots_and_sitemap(site: Path, expected: dict, canonicals: dict[str, str]) -> list[str]:
    problems: list[str] = []
    robots = site / 'robots.txt'
    if not robots.is_file():
        problems.append('robots.txt is missing from the site')
    else:
        text = robots.read_text(encoding='utf-8')
        if re.search(r'(?im)^\s*disallow:\s*\S', text):
            problems.append('robots.txt disallows something')
        if f'Sitemap: {expected["site"]}sitemap.xml' not in text:
            problems.append('robots.txt does not name the sitemap')
    sitemap = site / 'sitemap.xml'
    if not sitemap.is_file():
        return problems + ['sitemap.xml is missing from the site']
    locs = re.findall(r'<loc>([^<]+)</loc>', sitemap.read_text(encoding='utf-8'))
    for loc in locs:
        if loc not in canonicals.values():
            problems.append(f'sitemap lists {loc}, which is no page\'s canonical address')
    for rel, canonical in canonicals.items():
        if canonical not in locs:
            problems.append(f'{rel}: its canonical address {canonical} is not in the sitemap')
    return problems


def is_redirect_stub(html: str) -> bool:
    """Quarto's page for an old address (the aliases: of a page): a script that sends the reader on."""
    start = html[:3000]
    return 'http-equiv="refresh"' in start or ('var redirects' in start and 'window.location.replace' in html)


def book_pages(site: Path) -> list[Path]:
    """The book's pages: not the libraries, the decks, or the redirect stubs of the old addresses."""
    pages = []
    for page in sorted(site.rglob('*.html')):
        relative = page.relative_to(site)
        if SKIPPED_DIRECTORIES.intersection(relative.parts[:-1]):
            continue
        if is_redirect_stub(page.read_text(encoding='utf-8', errors='replace')):
            continue
        pages.append(page)
    return pages


def check_site(site: Path, root: Path = ROOT) -> list[str]:
    expected = settings(root)
    homepage = site / 'index.html'
    if not homepage.is_file():
        return [f'{site} has no index.html: render the book first']
    problems: list[str] = []
    canonicals: dict[str, str] = {}
    for page in book_pages(site):
        rel = page.relative_to(site).as_posix()
        html = page.read_text(encoding='utf-8')
        problems += check_page(rel, html, expected)
        canonicals[rel] = canonical_of(rel, expected['site'])
    home_html = homepage.read_text(encoding='utf-8')
    problems += check_homepage(home_html, expected)
    problems += check_icons(site, home_html)
    problems += check_robots_and_sitemap(site, expected, canonicals)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--site', type=Path, default=ROOT / '_book', help='the rendered site (default _book)')
    args = parser.parse_args()
    site = args.site if args.site.is_absolute() else ROOT / args.site
    problems = check_site(site)
    for problem in problems:
        print(f'  {problem}')
    pages = len(book_pages(site)) if (site / 'index.html').is_file() else 0
    print(f'site metadata: {len(problems)} problem(s) in {pages} page(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
