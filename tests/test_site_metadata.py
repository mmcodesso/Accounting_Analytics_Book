"""The website's search metadata checks (scripts/verify/site_metadata_check.py), the post-render corrections
(scripts/finish_site.py) and the icons (scripts/make_favicons.py), on fixture pages and on the icon files themselves."""
from __future__ import annotations

import copy
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts' / 'verify'))
sys.path.insert(0, str(ROOT / 'scripts'))
import finish_site
import make_favicons
import site_metadata_check as check

EXPECTED = check.settings(ROOT)
SITE, HUB = EXPECTED['site'], EXPECTED['hub']


def good_graph() -> list:
    """A graph that satisfies every check, built from _quarto.yml the way the filter writes it."""
    publisher = {'@id': HUB['url'] + '#organization'}
    author = {'@id': HUB['author-url'] + '#person'}
    editions = []
    for key, isbn in EXPECTED['isbn'].items():
        edition = {'@type': 'Book', '@id': f'{HUB["book-url"]}#edition-{key}', 'name': f'Title — {key}', 'isbn': isbn,
                   'exampleOfWork': {'@id': SITE + '#book'}, 'author': [author], 'publisher': publisher}
        if key in check.FREE_EDITIONS:
            edition['isAccessibleForFree'] = True
            edition['offers'] = {'@type': 'Offer', 'price': 0, 'priceCurrency': 'USD'}
        editions.append(edition)
    return [
        {'@type': 'Book', '@id': SITE + '#book', 'name': EXPECTED['title'], 'author': [author], 'publisher': publisher,
         'identifier': {'@type': 'PropertyValue', 'propertyID': 'DOI', 'value': EXPECTED['doi']},
         'sameAs': [HUB['book-url'], 'https://doi.org/' + EXPECTED['doi']], 'workExample': editions},
        {'@type': 'WebPage', '@id': SITE + '#webpage', 'isPartOf': {'@id': SITE + '#website'},
         'mainEntity': {'@id': SITE + '#book'}},
        {'@type': 'Person', '@id': HUB['author-url'] + '#person', 'name': 'Author'},
        {'@type': 'Organization', '@id': HUB['url'] + '#organization', 'name': HUB['name'], 'url': HUB['url']},
        {'@type': 'WebSite', '@id': SITE + '#website', 'url': SITE, 'name': EXPECTED['name'],
         'alternateName': EXPECTED['alternate'], 'publisher': publisher, 'about': {'@id': SITE + '#book'}},
    ]


def page(rel: str = 'index.html', *, graph: list | None = None, site_name: str | None = None,
         footer: tuple[str, ...] | None = None, extra_head: str = '') -> str:
    graph = good_graph() if graph is None else graph
    home = rel == 'index.html'
    links = footer if footer is not None else (HUB['url'], HUB['book-url'])
    ld = f'<script type="application/ld+json">{json.dumps({"@graph": graph})}</script>' if home else ''
    og = (f'<meta property="og:type" content="website"><meta property="og:url" content="{SITE}">'
          f'<meta name="description" content="{EXPECTED["description"]}">' if home else '')
    title = EXPECTED['title'] if home else 'A chapter'
    footer_html = ''.join(f'<a href="{link}">x</a>' for link in links)
    return (f'<html><head><title>{title}</title>'
            f'<meta property="og:site_name" content="{site_name or EXPECTED["name"]}">'
            f'<link rel="canonical" href="{check.canonical_of(rel, SITE)}">{og}{ld}'
            f'<link rel="icon" href="./favicon.ico"><link rel="apple-touch-icon" href="./apple-touch-icon.png">'
            f'{extra_head}</head><body><footer>{footer_html}</footer></body></html>')


class PageTests(unittest.TestCase):
    def test_a_good_homepage_has_no_problems(self):
        self.assertEqual([], check.check_page('index.html', page(), EXPECTED))
        self.assertEqual([], check.check_homepage(page(), EXPECTED))

    def test_a_good_chapter_page_has_no_problems(self):
        rel = 'chapters/01-role-of-analytics/chapter.html'
        self.assertEqual([], check.check_page(rel, page(rel), EXPECTED))

    def test_og_site_name_must_be_the_sites_name(self):
        problems = check.check_page('index.html', page(site_name=EXPECTED['title']), EXPECTED)
        self.assertTrue(any('og:site_name' in problem for problem in problems))

    def test_canonical_must_be_the_pages_own_address(self):
        html = page().replace(SITE + '"', SITE + 'elsewhere.html"', 1)
        self.assertTrue(any('canonical' in problem for problem in check.check_page('index.html', html, EXPECTED)))

    def test_footer_must_link_the_publisher_and_its_page_for_the_book(self):
        problems = check.check_page('index.html', page(footer=(HUB['url'],)), EXPECTED)
        self.assertEqual(1, len(problems))
        self.assertIn(HUB['book-url'], problems[0])

    def test_noindex_is_refused(self):
        html = page(extra_head='<meta name="robots" content="noindex">')
        self.assertTrue(any('indexed' in problem for problem in check.check_page('index.html', html, EXPECTED)))


class GraphTests(unittest.TestCase):
    def problems(self, mutate) -> list[str]:
        graph = copy.deepcopy(good_graph())
        mutate(graph)
        return check.check_graph(graph, EXPECTED)

    def test_a_good_graph_has_no_problems(self):
        self.assertEqual([], check.check_graph(good_graph(), EXPECTED))

    def test_two_website_nodes_are_refused(self):
        problems = self.problems(lambda g: g.append(copy.deepcopy(g[-1])))
        self.assertTrue(any('2 WebSite' in problem for problem in problems))

    def test_the_site_name_and_alternate_name_come_from_the_settings(self):
        def mutate(graph):
            graph[-1]['name'] = EXPECTED['title']
            graph[-1]['alternateName'] = []
        problems = self.problems(mutate)
        self.assertTrue(any('name is' in problem for problem in problems))
        self.assertTrue(any('alternateName' in problem for problem in problems))

    def test_a_product_node_is_refused(self):
        problems = self.problems(lambda g: g[0]['workExample'][0].update({'@type': ['Book', 'Product']}))
        self.assertTrue(any('Product' in problem for problem in problems))

    def test_a_printed_edition_carries_no_offer_and_no_free_flag(self):
        def mutate(graph):
            graph[0]['workExample'][-1]['offers'] = {'@type': 'Offer', 'price': 0}
        self.assertTrue(any('printed' in problem for problem in self.problems(mutate)))

    def test_a_free_edition_needs_a_price_of_zero(self):
        def mutate(graph):
            graph[0]['workExample'][0]['offers']['price'] = 29.95
        problems = self.problems(mutate)
        self.assertTrue(any('free' in problem for problem in problems))
        self.assertTrue(any('29.95' in problem for problem in problems))

    def test_an_isbn_must_match_the_settings(self):
        problems = self.problems(lambda g: g[0]['workExample'][0].update({'isbn': '9780000000002'}))
        self.assertTrue(any('ISBN' in problem for problem in problems))

    def test_an_undefined_id_is_refused_unless_the_publisher_defines_it(self):
        def mutate(graph):
            graph[1]['mainEntity'] = {'@id': SITE + '#nowhere'}
        self.assertTrue(any('nowhere' in problem for problem in self.problems(mutate)))

        def external(graph):
            graph[1]['mainEntity'] = {'@id': HUB['book-url'] + '#book'}
        self.assertEqual([], self.problems(external))

    def test_the_doi_must_match(self):
        problems = self.problems(lambda g: g[0]['identifier'].update({'value': '10.0000/other'}))
        self.assertTrue(any('DOI' in problem for problem in problems))


class SiteTests(unittest.TestCase):
    def test_canonical_addresses(self):
        self.assertEqual(SITE, check.canonical_of('index.html', SITE))
        self.assertEqual(SITE + 'a/b.html', check.canonical_of('a/b.html', SITE))
        self.assertEqual(SITE + 'a/', check.canonical_of('a/index.html', SITE))

    def test_the_sitemap_must_list_canonical_addresses(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            (site / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n', encoding='utf-8')
            canonicals = {'index.html': SITE, 'a/b.html': SITE + 'a/b.html'}
            sitemap = site / 'sitemap.xml'
            sitemap.write_text(f'<urlset><url><loc>{SITE}</loc></url><url><loc>{SITE}a/b.html</loc></url></urlset>',
                               encoding='utf-8')
            self.assertEqual([], check.check_robots_and_sitemap(site, EXPECTED, canonicals))
            sitemap.write_text(f'<urlset><url><loc>{SITE}index.html</loc></url></urlset>', encoding='utf-8')
            problems = check.check_robots_and_sitemap(site, EXPECTED, canonicals)
            self.assertTrue(any('index.html' in problem for problem in problems))
            (site / 'robots.txt').write_text('User-agent: *\nDisallow: /favicon.ico\n', encoding='utf-8')
            self.assertTrue(any('disallows' in problem for problem in
                                check.check_robots_and_sitemap(site, EXPECTED, canonicals)))


class FinishSiteTests(unittest.TestCase):
    def test_the_homepage_is_listed_at_its_canonical_address(self):
        text = f'<loc>{SITE}index.html</loc><loc>{SITE}a/index.html</loc><loc>{SITE}a/b.html</loc>'
        self.assertEqual(f'<loc>{SITE}</loc><loc>{SITE}a/</loc><loc>{SITE}a/b.html</loc>', finish_site.normalize_sitemap(text))

    def test_og_site_name_is_replaced_and_the_rest_is_kept(self):
        html = '<meta property="og:site_name" content="The Book: A Title"><p>og:site_name</p>'
        self.assertEqual('<meta property="og:site_name" content="Accounting Analytics"><p>og:site_name</p>',
                         finish_site.set_site_name(html, 'Accounting Analytics'))

    def test_finish_corrects_pages_once_and_leaves_decks_and_libraries_alone(self):
        tag = '<meta property="og:site_name" content="Old">'
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            (site / 'slides/chapter-01').mkdir(parents=True)
            (site / 'site_libs').mkdir()
            (site / 'a').mkdir()
            for name in ('index.html', 'a/b.html', 'slides/chapter-01/index.html', 'site_libs/x.html'):
                (site / name).write_text(tag, encoding='utf-8', newline='')
            (site / 'sitemap.xml').write_text(f'<loc>{SITE}index.html</loc>', encoding='utf-8')
            changed = finish_site.finish(site, 'Accounting Analytics')
            self.assertEqual(['sitemap.xml', 'a/b.html', 'index.html'], changed)
            self.assertEqual(tag, (site / 'slides/chapter-01/index.html').read_text(encoding='utf-8'))
            self.assertEqual(tag, (site / 'site_libs/x.html').read_text(encoding='utf-8'))
            self.assertEqual([], finish_site.finish(site, 'Accounting Analytics'))

    def test_the_name_comes_from_the_settings(self):
        self.assertEqual(EXPECTED['name'], finish_site.site_name(ROOT))


class IconTests(unittest.TestCase):
    @unittest.skipUnless(make_favicons.SOURCE.is_file(), 'visuals/branding/favicon.png is not in this checkout')
    def test_the_icon_files_are_current_with_the_script_and_the_source(self):
        # Compared as pixels: the compressed bytes of a PNG differ between zlib builds.
        mark = make_favicons.crop_mark(Image.open(make_favicons.SOURCE))
        master = make_favicons.master_tile(mark, make_favicons.MARK_SHARE, rounded=True)
        expected = {size: make_favicons.resample(master, size) for size in make_favicons.ICO_SIZES}
        data = (ROOT / 'favicon.ico').read_bytes()
        for index, size in enumerate(sorted(check.ico_sizes(data))):
            length, offset = struct.unpack('<II', data[6 + 16 * index + 8:6 + 16 * index + 16])
            frame = Image.open(io.BytesIO(data[offset:offset + length])).convert('RGBA')
            extrema = ImageChops.difference(frame, expected[size]).getextrema()
            self.assertLessEqual(max(high for _, high in extrema), 1,
                                 f'favicon.ico {size}px differs from the script: run python scripts/make_favicons.py')

    def test_the_icons_have_the_sizes_the_links_name(self):
        self.assertEqual(check.ICO_SIZES, check.ico_sizes((ROOT / 'favicon.ico').read_bytes()))
        for name, size in check.PNG_ICONS.items():
            self.assertEqual((size, size), check.png_size((ROOT / name).read_bytes()), name)
        # Google recommends a favicon larger than 48 x 48 px.
        self.assertTrue(any(size > 48 for size in check.PNG_ICONS.values()))

    def test_the_apple_icon_is_opaque(self):
        with Image.open(ROOT / 'apple-touch-icon.png') as icon:
            self.assertEqual('RGB', icon.mode)


if __name__ == '__main__':
    unittest.main()
