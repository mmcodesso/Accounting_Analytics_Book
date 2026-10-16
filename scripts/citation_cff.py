"""Write CITATION.cff, the book's citation for GitHub's "Cite this repository", Zenodo and reference managers.

Every value comes from _quarto.yml (title, author and ORCID iD, affiliation, date, website, the PDF's ISBN, the DOI,
the long description, the keywords, the license, the publisher) and _variables.yml (the revision), so the file never
disagrees with the book's own metadata. Run it after changing any of them; tests/test_metadata.py fails while the file
is out of date, and `python scripts/release.py bump` rewrites it with the new revision.

  python scripts/citation_cff.py           write CITATION.cff
  python scripts/citation_cff.py --check   exit 1 if CITATION.cff is out of date
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HEADER = ('# Written by scripts/citation_cff.py from _quarto.yml and _variables.yml: edit those and run the script, not\n'
          '# this file. GitHub shows it as "Cite this repository"; Zenodo and reference managers read it too.\n')


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8')) or {}


def _text(value) -> str:
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def spdx(license_url: str) -> str | None:
    """The SPDX identifier of a Creative Commons license URL (https://creativecommons.org/licenses/by-sa/4.0/)."""
    match = re.search(r'creativecommons\.org/licenses/([a-z-]+)/(\d+\.\d+)', license_url or '')
    return f'CC-{match.group(1).upper()}-{match.group(2)}' if match else None


def citation(root: Path = ROOT) -> dict:
    config = _load(root / '_quarto.yml')
    variables = _load(root / '_variables.yml')
    book = config.get('book') or {}
    indexing = config.get('indexing') or {}
    authors = []
    for author in book.get('author') or []:
        author = {'name': author} if isinstance(author, str) else author
        given, _, family = _text(author['name']).rpartition(' ')
        entry = {'family-names': family, 'given-names': given}
        if author.get('orcid'):
            entry['orcid'] = f'https://orcid.org/{author["orcid"]}'
        affiliations = author.get('affiliations') or []
        if affiliations:
            entry['affiliation'] = _text(affiliations[0].get('name'))
        authors.append(entry)
    site = _text(book.get('site-url')).rstrip('/')
    release = _text((variables.get('book') or {}).get('release'))
    repository = re.sub(r'/releases/.*$', '', release) or None
    license_id = spdx((config.get('license') or {}).get('link'))
    doi = _text(config.get('doi'))
    isbn = _text((config.get('isbn') or {}).get('pdf'))
    publisher = _text((config.get('citation') or {}).get('publisher'))
    date = _text(book.get('date'))

    preferred = {'type': 'book', 'title': _text(book['title']), 'authors': copy.deepcopy(authors)}
    if publisher:
        preferred['publisher'] = {'name': publisher}
    if date:
        preferred['year'] = int(date[:4])
    if isbn:
        preferred['isbn'] = isbn
    if doi:
        preferred['doi'] = doi
    preferred['url'] = site
    if license_id:
        preferred['license'] = license_id
    preferred['languages'] = ['en']

    data = {
        'cff-version': '1.2.0',
        'message': 'If you use this book in your teaching or research, please cite it as below.',
        'title': _text(book['title']),
        'abstract': _text(indexing.get('summary')),
        'authors': authors,
        'version': _text((variables.get('book') or {}).get('revision')),
    }
    if date:
        data['date-released'] = date
    if doi:
        data['doi'] = doi
    if license_id:
        data['license'] = license_id
    data['url'] = site
    if repository:
        data['repository-code'] = repository
    data['keywords'] = [_text(keyword) for keyword in indexing.get('keywords') or []]
    data['preferred-citation'] = preferred
    return data


def render(root: Path = ROOT) -> str:
    body = yaml.safe_dump(citation(root), sort_keys=False, allow_unicode=True, width=110, default_flow_style=False)
    return HEADER + body


def write(root: Path = ROOT) -> bool:
    """Write CITATION.cff; True when it changed."""
    path = root / 'CITATION.cff'
    text = render(root)
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return False
    path.write_text(text, encoding='utf-8', newline='\n')
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true', help='exit 1 if CITATION.cff is out of date')
    args = parser.parse_args(argv)
    path = ROOT / 'CITATION.cff'
    if args.check:
        current = path.read_text(encoding='utf-8') if path.exists() else ''
        if current != render(ROOT):
            print('CITATION.cff is out of date: run python scripts/citation_cff.py', file=sys.stderr)
            return 1
        print('CITATION.cff is current.')
        return 0
    print('CITATION.cff written.' if write(ROOT) else 'CITATION.cff was already current.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
