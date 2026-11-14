"""Controlli sul sito costruito, prima del deploy:

    python tools/check_site.py

- ogni pagina schema mostra esattamente schema e soluzione di data/puzzles.json;
- i link interni (href e src) puntano a file che esistono;
- ogni blocco JSON-LD è JSON valido e ha i campi che servono al suo tipo;
- ogni pagina ha canonical assoluta, lang, title, description e, se ha una
  versione nell'altra lingua, hreflang reciproci.
Esce con codice 1 se trova problemi.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
import build_site as B  # noqa: E402

ROOT = B.ROOT
REQUIRED = {
    'MobileApplication': ['name', 'operatingSystem', 'applicationCategory', 'offers', 'inLanguage', 'screenshot', 'downloadUrl', 'featureList'],
    'WebSite': ['name', 'url'],
    'Organization': ['name', 'email'],
    'BreadcrumbList': ['itemListElement'],
    'FAQPage': ['mainEntity'],
}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ld, self.alts, self.tables = [], [], {}, []
        self.lang = self.canonical = self.title = self.desc = None
        self._ld = self._title = self._table = self._cell = None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'html':
            self.lang = a.get('lang')
        for k in ('href', 'src'):
            if a.get(k):
                self.links.append(a[k])
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical = a['href']
        if tag == 'link' and a.get('rel') == 'alternate' and a.get('hreflang'):
            self.alts[a['hreflang']] = a['href']
        if tag == 'meta' and a.get('name') == 'description':
            self.desc = a.get('content')
        if tag == 'title':
            self._title = ''
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self._ld = ''
        if tag == 'table' and 'sudoku' in (a.get('class') or ''):
            self._table = []
        if tag == 'td' and self._table is not None:
            self._cell = ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self.title, self._title = self._title, None
        if tag == 'script' and self._ld is not None:
            self.ld.append(self._ld)
            self._ld = None
        if tag == 'td' and self._cell is not None:
            self._table.append(self._cell.strip())
            self._cell = None
        if tag == 'table' and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, d):
        if self._title is not None:
            self._title += d
        if self._ld is not None:
            self._ld += d
        if self._cell is not None:
            self._cell += d


def local_file(url, page_dir):
    u = urlparse(url)
    if u.scheme in ('http', 'https'):
        if not url.startswith(B.SITE_URL):
            return None
        path = os.path.join(ROOT, url[len(B.SITE_URL):])
    elif u.scheme or url.startswith('#'):
        return None
    elif u.path.startswith(B.BASE):
        path = os.path.join(ROOT, u.path[len(B.BASE):])
    elif u.path.startswith('/'):
        return '?'  # fuori dal sito
    else:
        path = os.path.normpath(os.path.join(page_dir, u.path))
    if path.endswith(('/', '\\')) or os.path.isdir(path):
        path = os.path.join(path, 'index.html')
    return os.path.normpath(path)


def main():
    problems = []
    pages = []
    for dirpath, _, files in os.walk(ROOT):
        if os.sep + 'play' in dirpath or os.sep + '.git' in dirpath or os.sep + 'tools' in dirpath:
            continue
        for f in files:
            if f == 'index.html':
                pages.append(os.path.join(dirpath, f))
    parsed = {}
    for file in pages:
        p = Page()
        p.feed(open(file, encoding='utf-8').read())
        parsed[os.path.normpath(file)] = p
        rel = os.path.relpath(file, ROOT)
        for url in p.links:
            target = local_file(url, os.path.dirname(file))
            if target and (target == '?' or not os.path.exists(target)):
                problems.append(f'{rel}: link rotto {url}')
        for block in p.ld:
            try:
                obj = json.loads(block)
            except ValueError as ex:
                problems.append(f'{rel}: JSON-LD non valido ({ex})')
                continue
            missing = [k for k in REQUIRED.get(obj.get('@type'), []) if k not in obj]
            if obj.get('@context') != 'https://schema.org' or missing:
                problems.append(f'{rel}: JSON-LD {obj.get("@type")} incompleto {missing}')
        if not (p.lang and p.title and p.desc and p.canonical and p.canonical.startswith(B.SITE_URL)):
            problems.append(f'{rel}: manca lang, title, description o canonical assoluta')
        for lang, url in p.alts.items():
            if lang == 'x-default':
                continue
            other = local_file(url, '')
            if other and other in parsed or other and os.path.exists(other):
                q = Page()
                q.feed(open(other, encoding='utf-8').read())
                if q.alts.get(p.lang) != p.canonical:
                    problems.append(f'{rel}: hreflang {lang} non reciproco')
    for pz in B.load_puzzles():
        for lang in B.C.LANGS:
            file = os.path.normpath(os.path.join(ROOT, pz[f'path_{lang}'], 'index.html'))
            if pz['variant'] == 'killer':
                # Griglie in SVG: lo schema vuoto, poi la soluzione cifra per cifra.
                svgs = re.findall(r'<svg class="ksvg".*?</svg>', open(file, encoding='utf-8').read())
                got = [re.findall(r'text-anchor="middle"[^>]*>(\d)<', s) for s in svgs]
                if got != [[], [str(v) for v in pz['solution']]]:
                    problems.append(f'{pz[f"path_{lang}"]}: griglia diversa da data/killer.json')
                if not os.path.exists(os.path.join(ROOT, pz[f'pdf_{lang}'])):
                    problems.append(f'{pz[f"path_{lang}"]}: manca il PDF')
                continue
            tables = parsed[file].tables
            want = [[str(v or '') for v in pz['puzzle']], [str(v) for v in pz['solution']]]
            # la prima td è la casella vuota d'angolo delle intestazioni
            if [t[1:] for t in tables] != want:
                problems.append(f'{pz[f"path_{lang}"]}: griglia diversa da puzzles.json')
            if not os.path.exists(os.path.join(ROOT, pz[f'pdf_{lang}'])):
                problems.append(f'{pz[f"path_{lang}"]}: manca il PDF')
    print(f'{len(pages)} pagine controllate')
    print('\n'.join(problems) if problems else 'Nessun problema.')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
