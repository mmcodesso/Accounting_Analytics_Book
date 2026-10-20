"""The book's metadata (_quarto.yml): identifiers with valid check digits, CITATION.cff current with it, and the
copyright page and robots.txt naming the same identifiers and address."""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import citation_cff

CONFIG = yaml.safe_load((ROOT / '_quarto.yml').read_text(encoding='utf-8'))
AUTHOR = CONFIG['book']['author'][0]


def mod11_2(digits: str) -> str:
    """The check character of an ORCID iD or an ISNI (ISO 7064 MOD 11-2) for its first 15 digits."""
    total = 0
    for digit in digits:
        total = (total + int(digit)) * 2
    result = (12 - total % 11) % 11
    return 'X' if result == 10 else str(result)


class IdentifierTests(unittest.TestCase):
    def test_orcid_and_isni_have_valid_check_characters(self):
        for name, value in (('orcid', AUTHOR['orcid']), ('isni', AUTHOR['isni'])):
            digits = re.sub(r'[\s-]', '', str(value))
            self.assertRegex(digits, r'^\d{15}[\dX]$', name)
            self.assertEqual(mod11_2(digits[:15]), digits[15], f'{name} {value} has a wrong check character')

    def test_doi_is_blank_or_a_doi(self):
        doi = str(CONFIG.get('doi') or '')
        if doi:
            self.assertRegex(doi, r'^10\.\d{4,}/\S+$', 'type the DOI without https://doi.org/')

    def test_bisac_codes_look_like_bisac_codes(self):
        for subject in CONFIG['indexing']['bisac']:
            self.assertRegex(subject['code'], r'^[A-Z]{3}\d{6}$')
            self.assertTrue(subject['heading'].strip())

    def test_citation_isbn_is_the_pdf_isbn(self):
        self.assertEqual(CONFIG['citation']['isbn'], CONFIG['isbn']['pdf'])

    def test_site_url_has_no_final_slash(self):
        # Quarto appends the social cards' image path (/visuals/...) to it.
        self.assertFalse(CONFIG['book']['site-url'].endswith('/'))


class SearchAppearanceTests(unittest.TestCase):
    """What Google reads to name and show the website (indexing.site-identity and indexing.hub, the footer, the icons)."""

    def test_open_graph_site_name_is_the_sites_name(self):
        self.assertEqual(CONFIG['indexing']['site-identity']['name'], CONFIG['book']['open-graph']['site-name'])

    def test_the_site_is_not_named_by_the_books_title_or_the_publisher(self):
        identity = CONFIG['indexing']['site-identity']
        self.assertNotEqual(identity['name'], CONFIG['book']['title'])
        self.assertNotEqual(identity['name'], CONFIG['indexing']['hub']['name'])
        self.assertTrue(identity['alternate-name'])
        self.assertNotIn(identity['name'], identity['alternate-name'])

    def test_the_sidebar_shows_the_sites_name(self):
        self.assertEqual(CONFIG['indexing']['site-identity']['name'], CONFIG['book']['sidebar']['title'])
        self.assertTrue((ROOT / CONFIG['book']['sidebar']['logo']).is_file())

    def test_description_fits_a_search_result(self):
        self.assertLessEqual(len(CONFIG['description']), 160)

    def test_hub_addresses_are_https_and_end_in_a_slash(self):
        hub = CONFIG['indexing']['hub']
        for key in ('url', 'book-url', 'author-url'):
            self.assertRegex(hub[key], r'^https://[^/]+/.*/$|^https://[^/]+/$', key)
        self.assertTrue(hub['book-url'].startswith(hub['url']))
        self.assertTrue(hub['author-url'].startswith(hub['url']))
        self.assertEqual(hub['name'], CONFIG['citation']['publisher'])

    def test_the_footer_links_the_hub_and_its_page_for_the_book(self):
        footer = CONFIG['book']['page-footer']
        self.assertIn(f'href="{CONFIG["indexing"]["hub"]["url"]}"', footer['left'])
        self.assertIn(f'href="{CONFIG["indexing"]["hub"]["book-url"]}"', footer['right'])
        # A Markdown link in the book's metadata would become an unused hyperlink relationship in the DOCX.
        self.assertNotIn('](', footer['left'] + footer['right'])

    def test_the_icons_are_project_resources_and_linked_from_every_html_page(self):
        head = (ROOT / CONFIG['format']['html']['include-in-header']).read_text(encoding='utf-8')
        icons = ['favicon.ico', 'favicon-48x48.png', 'favicon-96x96.png', 'favicon-192x192.png', 'apple-touch-icon.png']
        for icon in icons:
            self.assertIn(icon, CONFIG['project']['resources'], icon)
            self.assertIn('/' + icon, head, icon)
            self.assertTrue((ROOT / icon).is_file(), icon)
        # Quarto's own favicon option would add a second rel="icon".
        self.assertNotIn('favicon', CONFIG['book'])
        self.assertNotIn('<!--', head)

    def test_robots_does_not_block_the_icons(self):
        robots = (ROOT / 'robots.txt').read_text(encoding='utf-8')
        self.assertNotRegex(robots, r'(?im)^\s*disallow:\s*\S')

    def test_the_post_render_step_finishes_the_site(self):
        self.assertIn('python scripts/finish_site.py', CONFIG['project']['post-render'])

    def test_the_free_editions_are_offered_at_a_heading_that_exists(self):
        # The offers' address, front-matter/downloads.html#latest-book-version (filters/book-metadata.lua).
        downloads = (ROOT / 'front-matter/downloads.qmd').read_text(encoding='utf-8')
        self.assertRegex(downloads, r'(?m)^## Latest Book Version\s*$')
        lua = (ROOT / 'filters/book-metadata.lua').read_text(encoding='utf-8')
        self.assertIn("'front-matter/downloads.html#latest-book-version'", lua)


class CopyTests(unittest.TestCase):
    def test_copyright_page_prints_the_orcid_and_the_isni(self):
        pages = (ROOT / 'front-matter/_book-pages.qmd').read_text(encoding='utf-8')
        self.assertIn(f'https://orcid.org/{AUTHOR["orcid"]}', pages)
        isni = re.sub(r'\s', '', str(AUTHOR['isni']))
        self.assertIn('ISNI ' + ' '.join(isni[i:i + 4] for i in range(0, 16, 4)), pages)
        self.assertIn('[doi]{.doi}', pages)

    def test_robots_names_the_sitemap_of_the_site(self):
        robots = (ROOT / 'robots.txt').read_text(encoding='utf-8')
        self.assertIn(f'Sitemap: {CONFIG["book"]["site-url"]}/sitemap.xml', robots)

    def test_citation_cff_is_current(self):
        current = (ROOT / 'CITATION.cff').read_text(encoding='utf-8')
        self.assertEqual(current, citation_cff.render(ROOT),
                         'CITATION.cff is out of date: run python scripts/citation_cff.py')

    def test_citation_cff_names_the_license_by_its_spdx_identifier(self):
        self.assertEqual('CC-BY-SA-4.0', citation_cff.spdx('https://creativecommons.org/licenses/by-sa/4.0/'))

    def test_a_new_revision_becomes_the_citation_version(self):
        from scripts import release
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('_quarto.yml', '_variables.yml', 'CITATION.cff'):
                shutil.copy(ROOT / name, root / name)
            release.bump(root, '2099.1')
            self.assertEqual('2099.1', yaml.safe_load((root / 'CITATION.cff').read_text(encoding='utf-8'))['version'])


if __name__ == '__main__':
    unittest.main()
