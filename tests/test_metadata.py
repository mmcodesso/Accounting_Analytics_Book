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
