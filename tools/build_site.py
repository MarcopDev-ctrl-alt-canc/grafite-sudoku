"""Costruisce le pagine statiche del sito da data/puzzles.json e dai testi in
site_content.py.

    python tools/build_site.py            # pagine, PDF e immagini mancanti, sitemap
    python tools/build_site.py --force    # rigenera anche PDF e immagini esistenti
    python tools/build_site.py --pages    # solo HTML e sitemap (niente Chrome)

Serve Python 3 (solo libreria standard) e, per PDF e immagini di anteprima,
Google Chrome o Chromium (variabile CHROME se non è nel percorso di Windows
standard). Tutte le URL partono da SITE_URL: per passare a un dominio
proprio basta cambiare quella riga (o la variabile d'ambiente SITE_URL).

Non tocca index.html? Sì, lo riscrive: la home italiana e quella inglese sono
generate qui. Non tocca invece sudoku-da-stampare.html (il generatore nel
browser) né i file compilati della demo in play/.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from urllib.parse import quote, urlparse

sys.path.insert(0, os.path.dirname(__file__))
import site_content as C  # noqa: E402
import sudoku_engine as eng  # noqa: E402

SITE_URL = os.environ.get('SITE_URL', 'https://marcopdev-ctrl-alt-canc.github.io/grafite-sudoku/')
BASE = urlparse(SITE_URL).path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAY_BASE = 'https://play.google.com/store/apps/details?id=com.grafitesoft.grafitesudoku'
VERIFY_META = '<meta name="google-site-verification" content="WP-10qfUs4_3SNMS-6EU87PhdrAV6gjnLxrvXVHdN6A">'
GENERATOR = 'sudoku-da-stampare.html'
APP_LANGUAGES = ['it', 'en', 'es', 'pt', 'id', 'de', 'fr']
e = html.escape

# Badge di PixelPicked (immagine live con like e follower): l'unica risorsa
# esterna delle pagine, caricata solo quando si arriva al piè di pagina e
# senza referer.
PIXELPICKED_BADGE = ('<a href="https://pixelpicked.com/game/7SViDJjd0No/grafite-sudoku-offline-puzzle" target="_blank" rel="noopener"><img src="https://api.pixelpicked.com/api/badges/7SViDJjd0No/live.png?theme=dark" width="250" height="54" alt="Approved on PixelPicked" loading="lazy" referrerpolicy="no-referrer"></a>')


def play_url(campaign):
    """Link alla scheda Play con la campagna della pagina: Play Console
    (Acquisizione utenti) legge solo il parametro `referrer`."""
    ref = f'utm_source=site&utm_medium=web&utm_campaign={campaign}'
    return f'{PLAY_BASE}&referrer={quote(ref, safe="")}'


def href(path):
    return BASE + path


def absolute(path):
    return SITE_URL + path


# ------------------------------------------------------------------ dati

def load_puzzles():
    data = json.load(open(os.path.join(ROOT, 'data', 'puzzles.json'), encoding='utf-8'))
    for p in data:
        cat = p['category']
        for lang in C.LANGS:
            if p.get('serie3_slug') and lang == 'en':
                slug = p['serie3_slug']
            else:
                prefix = {'it': {'easy': 'sudoku-facile', 'medium': 'sudoku-medio', 'hard': 'sudoku-difficile',
                                 'large-print': 'sudoku-caratteri-grandi', 'x': 'sudoku-x', 'jigsaw': 'sudoku-jigsaw'},
                          'en': {'easy': 'easy-sudoku', 'medium': 'medium-sudoku', 'hard': 'hard-sudoku',
                                 'large-print': 'large-print-sudoku', 'x': 'x-sudoku', 'jigsaw': 'jigsaw-sudoku'}}[lang][cat]
                slug = f'{prefix}-{p["number"]}'
            p[f'slug_{lang}'] = slug
            p[f'path_{lang}'] = f'{C.PATHS[lang]["printable"]}{slug}/'
            p[f'pdf_{lang}'] = f'pdf/grafite-sudoku-{slug}.pdf'
            p[f'og_{lang}'] = f'assets/og/{lang}-{slug}.png'
    return data


def by_category(puzzles, cat):
    return [p for p in puzzles if p['category'] == cat]


def cat_path(lang, cat):
    return C.PATHS[lang]['printable'] + C.CATEGORIES[lang][cat]['slug'] + '/'


def guide_path(lang, key):
    return C.PATHS[lang]['guides'] + C.GUIDES[lang][key]['slug'] + '/'


def puzzle_name(lang, p):
    return C.CATEGORIES[lang][p['category']]['name']


# ------------------------------------------------------------------ hint

def first_hint(p, lang):
    """Il primo passo con un singolo: casella con un solo candidato oppure
    numero con un solo posto in un'unità. Frase pronta nella lingua."""
    T = C.PUZZLE[lang]
    units = eng.units_for(p['variant'], p['regions'])
    peers = eng.peers_from(units)
    grid = p['puzzle']
    cands = eng.candidates(grid, peers)
    for i in range(81):
        if grid[i] == 0 and bin(cands[i]).count('1') == 1:
            return T['hint_naked'].format(r=i // 9 + 1, c=i % 9 + 1)
    # unità: 0-8 righe, 9-17 colonne, 18-26 riquadri o regioni, 27-28 diagonali (X)
    for u_idx, u in enumerate(units):
        for d in range(1, 10):
            if any(grid[i] == d for i in u):
                continue
            spots = [i for i in u if grid[i] == 0 and cands[i] & (1 << (d - 1))]
            if len(spots) != 1:
                continue
            i = spots[0]
            r, c = i // 9 + 1, i % 9 + 1
            dd = number_phrase(lang, d)
            if u_idx < 9:
                return T['hint_hidden_row'].format(r=r, dd=dd)
            if u_idx < 18:
                return T['hint_hidden_col'].format(c=c, dd=dd)
            if u_idx < 27:
                if p['variant'] == 'jigsaw':
                    return T['hint_hidden_region'].format(r=r, c=c, dd=dd)
                return T['hint_hidden_box'].format(box=T['boxes'][eng.box_of(i)], dd=dd)
            return T['hint_hidden_diag'].format(corner=T['corners'][u_idx - 27], dd=dd)
    return None


def number_phrase(lang, d):
    if lang == 'it':
        return ("l'" if d in (1, 8) else 'il ') + str(d)
    return f'the {d}'


# ------------------------------------------------------------ griglie HTML

REGION_TINTS = ['#f6e7c8', '#e3efd9', '#dfe9f3', '#f3e0e0', '#ece4f3', '#f7efd9', '#dcefec', '#f3e7da', '#e8ecd5']


def cell_classes(p, i):
    r, c = divmod(i, 9)
    cls = []
    if p['variant'] == 'jigsaw':
        reg = p['regions']
        if c < 8 and reg[i] != reg[i + 1]:
            cls.append('br')
        if r < 8 and reg[i] != reg[i + 9]:
            cls.append('bb')
    else:
        if c in (2, 5):
            cls.append('br')
        if r in (2, 5):
            cls.append('bb')
    if p['variant'] == 'x' and (r == c or r + c == 8):
        cls.append('dg')
    return cls


def grid_table(p, lang, values, caption, solution=False):
    T = C.PUZZLE[lang]
    big = ' big' if p['category'] == 'large-print' else ''
    rows = [f'<table class="sudoku{big}"><caption>{e(caption)}</caption>',
            '<thead><tr><td style="border:0;background:none"></td>' + ''.join(f'<th scope="col" abbr="{T["col"]} {c}">{c}</th>' for c in range(1, 10)) + '</tr></thead><tbody>']
    for r in range(9):
        cells = [f'<th scope="row" abbr="{T["row"]} {r + 1}">{r + 1}</th>']
        for c in range(9):
            i = r * 9 + c
            cls = cell_classes(p, i)
            v = values[i]
            if v and p['puzzle'][i]:
                cls.append('g')
            style = ''
            if p['variant'] == 'jigsaw':
                style = f' style="background:{REGION_TINTS[p["regions"][i]]}"'
            cl = f' class="{" ".join(cls)}"' if cls else ''
            cells.append(f'<td{cl}{style}>{v or ""}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    rows.append('</tbody></table>')
    return ''.join(rows)


def mini_svg(p, size=96):
    """Miniatura decorativa della griglia (aria-hidden)."""
    s = size / 9
    parts = [f'<svg class="mini" viewBox="0 0 {size} {size}" width="{size}" height="{size}" aria-hidden="true" focusable="false">',
             f'<rect width="{size}" height="{size}" fill="#F0EAD9"/>']
    for i in range(81):
        r, c = divmod(i, 9)
        if p['variant'] == 'jigsaw':
            parts.append(f'<rect x="{c*s:.1f}" y="{r*s:.1f}" width="{s:.1f}" height="{s:.1f}" fill="{REGION_TINTS[p["regions"][i]]}"/>')
        elif p['variant'] == 'x' and (r == c or r + c == 8):
            parts.append(f'<rect x="{c*s:.1f}" y="{r*s:.1f}" width="{s:.1f}" height="{s:.1f}" fill="#e7d7b0"/>')
        if p['puzzle'][i]:
            parts.append(f'<rect x="{c*s+s*.32:.1f}" y="{r*s+s*.32:.1f}" width="{s*.36:.1f}" height="{s*.36:.1f}" fill="#14181F"/>')
    for k in (3, 6):
        if p['variant'] != 'jigsaw':
            parts.append(f'<path d="M{k*s:.1f} 0V{size}M0 {k*s:.1f}H{size}" stroke="#14181F" stroke-width="1.2"/>')
    parts.append(f'<rect width="{size}" height="{size}" fill="none" stroke="#14181F" stroke-width="2"/></svg>')
    return ''.join(parts)


# ---------------------------------------------------------------- layout

CSS = """
:root{--ink:#14181F;--ink-soft:#2a3040;--paper:#F0EAD9;--paper-line:#dcd3ba;--gold:#C99A3E;--gold-soft:#e3c583;--cream:#f7f3e8;--muted:#b9bdc7;--max:1060px}
*{box-sizing:border-box}html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--ink);color:var(--cream);font-family:"Noto Sans",system-ui,-apple-system,sans-serif;line-height:1.6;font-size:1rem}
h1,h2,h3{font-family:"Shippori Mincho","Noto Serif",serif;font-weight:700;line-height:1.25;margin:0 0 .5em;color:var(--cream)}
h1{font-size:clamp(1.8rem,5vw,2.8rem)}h2{font-size:clamp(1.35rem,3.4vw,1.9rem);margin-top:1.6em}h3{font-size:1.1rem}
a{color:var(--gold-soft)}a:hover{color:#fff}p,li{color:#dde0e6}
.wrap{max-width:var(--max);margin:0 auto;padding:0 16px}
.rule{height:3px;background:linear-gradient(90deg,var(--gold),transparent)}
.top{display:flex;flex-wrap:wrap;align-items:center;gap:8px 18px;padding:14px 16px;max-width:var(--max);margin:0 auto}
.brand{display:flex;align-items:center;gap:10px;font-family:"Shippori Mincho",serif;font-weight:700;font-size:1.1rem;color:var(--cream);text-decoration:none;margin-right:auto}
.brand img{border-radius:8px}
.top nav{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:.92rem}
.top nav a{color:var(--cream);text-decoration:none;padding:6px 0;min-height:44px;display:inline-flex;align-items:center}
.top nav a:hover,.top nav a[aria-current]{color:var(--gold-soft)}
.lang{border:1px solid var(--paper-line);border-radius:999px;padding:4px 12px!important;min-height:32px!important}
main{padding:8px 0 48px}
.crumbs{font-size:.85rem;color:var(--muted);margin:10px 0 18px}.crumbs ol{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:6px}
.crumbs li{color:var(--muted)}.crumbs li+li:before{content:"›";margin-right:6px}.crumbs a{color:var(--muted)}
.lead{font-size:1.06rem;max-width:720px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:13px 22px;border-radius:12px;font-weight:700;text-decoration:none;min-height:48px;border:0;font-size:1rem;cursor:pointer}
.btn-primary{background:var(--gold);color:#1a1408}.btn-primary:hover{color:#000;background:#d8ab52}
.btn-secondary{background:transparent;color:var(--cream);border:1.5px solid var(--paper-line)}.btn-secondary:hover{color:var(--gold-soft)}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.card{background:#1c212c;border:1px solid #2a3040;border-radius:16px;padding:20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.card h3{margin-top:0}.card p{margin:.3em 0 0;color:#c4c8d1;font-size:.95rem}
.pz-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;list-style:none;padding:0;margin:0}
.pz-list a{display:flex;flex-direction:column;align-items:center;gap:8px;background:#1c212c;border:1px solid #2a3040;border-radius:14px;padding:14px;text-decoration:none;color:var(--cream);text-align:center;font-size:.92rem}
.pz-list a:hover{border-color:var(--gold)}.pz-list small{color:var(--muted)}
.sheet{background:var(--paper);color:var(--ink);border-radius:16px;padding:10px 8px;max-width:560px;overflow-x:auto}
table.sudoku{border-collapse:collapse;margin:0 auto;font-family:"Noto Sans",sans-serif;color:var(--ink)}
table.sudoku caption{caption-side:bottom;font-size:.8rem;color:#5a5446;padding-top:8px}
table.sudoku th{font-size:.62rem;font-weight:600;color:#7a7260;padding:0 3px 0 0;width:12px}
table.sudoku thead th{height:14px}
table.sudoku td{width:min(calc((100vw - 74px) / 9),52px);height:min(calc((100vw - 74px) / 9),52px);border:1px solid #b9ae92;text-align:center;font-size:min(5vw,1.55rem);color:#3d4a6b;background:#fbf8ef;padding:0}
table.sudoku.big td{font-size:min(6.4vw,1.9rem)}
table.sudoku td.g{color:var(--ink);font-weight:700}
table.sudoku td.dg{background:#efe2c2}
table.sudoku td.br{border-right:3px solid var(--ink)}table.sudoku td.bb{border-bottom:3px solid var(--ink)}
table.sudoku tbody tr:first-child td{border-top:3px solid var(--ink)}table.sudoku tbody tr:last-child td{border-bottom:3px solid var(--ink)}
table.sudoku tbody td:nth-child(2){border-left:3px solid var(--ink)}table.sudoku tbody td:last-child{border-right:3px solid var(--ink)}
.layout{display:grid;grid-template-columns:minmax(0,560px) minmax(0,1fr);gap:28px;align-items:start}
@media (max-width:860px){.layout{grid-template-columns:1fr}}
details{background:#1c212c;border:1px solid #2a3040;border-radius:14px;padding:12px 16px;margin-top:16px}
summary{cursor:pointer;font-weight:700;color:var(--gold-soft);min-height:32px;display:flex;align-items:center}
details .sheet{margin-top:12px}
.note{font-size:.88rem;color:var(--muted)}
.hint{border-left:3px solid var(--gold);padding:4px 0 4px 14px;margin:16px 0}
.pager{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-top:28px}
.pager a{min-height:44px;display:inline-flex;align-items:center}
.cta{margin-top:40px;background:var(--paper);color:var(--ink);border-radius:18px;padding:22px;display:flex;flex-wrap:wrap;gap:18px;align-items:center}
.cta h2{color:var(--ink);margin:0 0 .3em;font-size:1.35rem}.cta p{color:var(--ink-soft);margin:0}.cta>div{flex:1 1 260px}
figure{margin:20px 0;background:var(--paper);border-radius:16px;padding:14px;max-width:520px}
figure svg{width:100%;height:auto;display:block}
figcaption{color:var(--ink-soft);font-size:.88rem;margin-top:8px}
.faq dt{font-weight:700;color:var(--cream);margin-top:12px}.faq dd{margin:4px 0 0;color:#c4c8d1}
footer.site{border-top:1px solid #2a3040;padding:28px 0 40px;font-size:.88rem;color:#a3a8b4;text-align:center}
footer.site .links{display:flex;flex-wrap:wrap;justify-content:center;gap:4px 18px;margin-bottom:12px}
footer.site .links a{min-height:44px;display:inline-flex;align-items:center}
footer.site p{color:#a3a8b4;margin:.4em auto;max-width:720px}
footer.site .badge{margin-top:16px}footer.site .badge img{display:inline-block;max-width:100%;height:auto}
#androidAppBanner{display:none;position:sticky;top:0;z-index:100;align-items:center;gap:12px;background:#0d1016;border-bottom:1px solid var(--gold);padding:10px 16px;font-size:.88rem}
#androidAppBanner .msg{flex:1;color:var(--cream)}
#androidAppBanner .cta-b{background:var(--gold);color:#1a1408;font-weight:700;padding:8px 16px;border-radius:8px;text-decoration:none;white-space:nowrap}
#androidAppBanner .close{background:none;border:none;color:#c4c8d1;font-size:1.1rem;cursor:pointer;min-width:44px;min-height:44px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:var(--gold);color:#000;padding:8px;z-index:200}
"""

HOME_CSS = """
.hero{padding:40px 0 56px;text-align:center}.hero img{border-radius:26px;box-shadow:0 18px 40px rgba(0,0,0,.45);margin-bottom:24px}
.hero .tagline{color:var(--gold-soft);font-family:"Shippori Mincho",serif;font-size:1.25rem;margin-bottom:10px}
.hero p.sub{max-width:580px;margin:0 auto 28px;color:#d0d3db}.hero .row{justify-content:center}
.quick{margin-top:18px;justify-content:center;font-size:.95rem}.quick a{min-height:44px;display:inline-flex;align-items:center}
section{padding:48px 0}section.alt{background:#191e28}
.head{text-align:center;max-width:660px;margin:0 auto 32px}.head h2{margin-top:0}.head p{color:#c4c8d1}
.card .emoji{font-size:1.7rem;display:block;margin-bottom:8px}
.avatars{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px}
.avatar{background:var(--paper);border-radius:18px;padding:16px 12px;text-align:center}
.avatar img{width:100%;max-width:150px;height:auto;margin-bottom:8px}
.avatar span{display:block;color:var(--ink);font-weight:700;font-size:.9rem}.avatar small{color:var(--ink-soft);font-size:.8rem}
.qr{display:flex;align-items:center;justify-content:center;gap:16px;max-width:420px;margin:24px auto 0;padding:16px 20px;background:var(--paper);border-radius:16px;text-align:left}
.qr b{color:var(--ink);display:block}.qr small{color:var(--ink-soft)}
.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:18px}
.shots img{width:100%;height:auto;border-radius:18px;border:1px solid #2a3040}
.demo-note{background:#1c212c;border:1px solid #2a3040;border-radius:16px;padding:18px 22px;max-width:720px;margin:24px auto 0;color:#d0d3db}
"""


def fonts_head():
    f = href('assets/fonts/')
    return (f'<link rel="preload" href="{f}noto-sans-latin.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="preload" href="{f}shippori-mincho-700-latin.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="stylesheet" href="{f}fonts.css">')


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '</script>'


def breadcrumb_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList',
            'itemListElement': [{'@type': 'ListItem', 'position': n, 'name': name, 'item': absolute(path)}
                                for n, (name, path) in enumerate(items, start=1)]}


def breadcrumb_html(lang, items):
    lis = []
    for n, (name, path) in enumerate(items):
        if n == len(items) - 1:
            lis.append(f'<li aria-current="page">{e(name)}</li>')
        else:
            lis.append(f'<li><a href="{href(path)}">{e(name)}</a></li>')
    return f'<nav class="crumbs" aria-label="{C.UI[lang]["breadcrumb"]}"><ol>{"".join(lis)}</ol></nav>'


def cta_block(lang, campaign):
    U = C.UI[lang]
    return (f'<aside class="cta"><div><h2>{U["cta_title"]}</h2><p>{U["cta_text"]}</p></div>'
            f'<a class="btn btn-primary play-store-link" data-utm-campaign="{campaign}" href="{e(play_url(campaign))}" '
            f'rel="noopener">{U["cta_button"]}</a></aside>')


def page(*, lang, path, title, description, body, alternates, campaign, og_image='assets/og-image.png',
         ld=(), extra_css='', extra_head='', section=None):
    """Una pagina completa. `alternates`: {lingua: percorso} per hreflang."""
    U = C.UI[lang]
    other = U['other_lang_code']
    alt_tags = ''.join(f'<link rel="alternate" hreflang="{l}" href="{absolute(p)}">' for l, p in alternates.items())
    if 'en' in alternates:
        alt_tags += f'<link rel="alternate" hreflang="x-default" href="{absolute(alternates["en"])}">'
    other_path = alternates.get(other, C.PATHS[other]['home'])
    nav = []
    for key, label, target in (('printable', U['nav_printable'], C.PATHS[lang]['printable']),
                               ('guides', U['nav_guides'], C.PATHS[lang]['guides']),
                               ('play', U['nav_play'], 'play/')):
        cur = ' aria-current="page"' if section == key else ''
        nav.append(f'<a href="{href(target)}"{cur}>{label}</a>')
    nav.append(f'<a class="lang" href="{href(other_path)}" hreflang="{other}" lang="{other}">{U["other_lang"]}</a>')
    og = absolute(og_image)
    privacy = U['privacy_line'].format(exodus=C.EXODUS_URL)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="theme-color" content="#14181F">
{extra_head}<link rel="canonical" href="{absolute(path)}">
{alt_tags}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Grafite Sudoku">
<meta property="og:locale" content="{'it_IT' if lang == 'it' else 'en_US'}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{absolute(path)}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{og}">
<link rel="icon" type="image/png" href="{href('assets/icon.png')}">
{fonts_head()}
<style>{CSS}{extra_css}</style>
{''.join(jsonld(x) for x in ld)}
</head>
<body>
<a class="skip" href="#main">{'Vai al contenuto' if lang == 'it' else 'Skip to content'}</a>
<div id="androidAppBanner"><span class="msg">{U['android_banner']}</span><a class="cta-b play-store-link" data-utm-campaign="{campaign}-banner" href="{e(play_url(campaign + '-banner'))}" rel="noopener">{U['android_install']}</a><button type="button" class="close" onclick="dismissAndroidBanner()" aria-label="{U['close']}">✕</button></div>
<div class="rule"></div>
<header class="top"><a class="brand" href="{href(C.PATHS[lang]['home'])}"><img src="{href('assets/icon.webp')}" alt="" width="34" height="34">Grafite Sudoku</a>
<nav aria-label="{U['menu']}">{''.join(nav)}</nav></header>
<main id="main">
{body}
</main>
<footer class="site"><div class="wrap">
<div class="links"><a href="{href(C.PATHS[lang]['printable'])}">{U['nav_printable']}</a><a href="{href(C.PATHS[lang]['guides'])}">{U['nav_guides']}</a><a href="{href(GENERATOR)}">{'Generatore di schemi' if lang == 'it' else 'Puzzle generator'}</a><a href="{C.PRIVACY_URL}">{U['privacy_policy']}</a><a href="mailto:grafitesoft@gmail.com">{U['contact']}</a><a href="https://paypal.me/grafitesoft">{U['coffee']}</a></div>
<p>{privacy}</p>
<p>{U['footer_tag']}</p>
<p class="badge">{PIXELPICKED_BADGE}</p>
</div></footer>
<script src="{href('assets/play-links.js')}" defer></script>
</body>
</html>
"""


# ------------------------------------------------------------------ pagine

def puzzle_page(puzzles, p, lang):
    T = C.PUZZLE[lang]
    cat = C.CATEGORIES[lang][p['category']]
    name = cat['name']
    level = T['level'][p['level']]
    path = p[f'path_{lang}']
    siblings = by_category(puzzles, p['category'])
    k = siblings.index(p)
    crumbs = [(C.UI[lang]['nav_home'], C.PATHS[lang]['home']), (C.UI[lang]['nav_printable'], C.PATHS[lang]['printable']),
              (cat['short'], cat_path(lang, p['category'])), (f'{name} {"n. " if lang == "it" else "#"}{p["number"]}', path)]
    hint = first_hint(p, lang)
    facts = T['facts'].format(clues=p['clues'], level=level, singles=T['singles_yes'] if p['singles_only'] else T['singles_no'])
    rules = C.RULES[lang][p['variant']]
    tips = C.TIPS[lang][p['category']]
    pager = []
    if k > 0:
        pager.append(f'<a href="{href(siblings[k - 1][f"path_{lang}"])}">{T["prev"]}</a>')
    pager.append(f'<a href="{href(cat_path(lang, p["category"]))}">{T["all"].format(short=cat["short"].lower())}</a>')
    if k < len(siblings) - 1:
        pager.append(f'<a href="{href(siblings[k + 1][f"path_{lang}"])}">{T["next"]}</a>')
    caption = T['caption'].format(name=name, n=p['number'], clues=p['clues'])
    body = f"""<div class="wrap">
{breadcrumb_html(lang, crumbs)}
<h1>{e(T['h1'].format(name=name, n=p['number']))}</h1>
<p class="lead">{e(facts)}</p>
<div class="layout">
<div>
<div class="sheet">{grid_table(p, lang, p['puzzle'], caption)}</div>
<div class="row" style="margin-top:16px"><a class="btn btn-primary" href="{href(p[f'pdf_{lang}'])}" download>{T['pdf']}</a></div>
<p class="note">{e(T['print_note'])}</p>
<details><summary>{T['show_solution']}</summary><div class="sheet">{grid_table(p, lang, p['solution'], T['solution_caption'].format(name=name, n=p['number']), solution=True)}</div></details>
</div>
<div>
<h2 style="margin-top:0">{T['hint_title']}</h2>
<p class="hint">{e(hint or '')}</p>
<h2>{T['rules_title']}</h2>
<p>{e(rules)}</p>
<h2>{T['tips_title']}</h2>
<ul>{''.join(f'<li>{e(t)}</li>' for t in tips)}</ul>
</div>
</div>
<nav class="pager" aria-label="{'Altri schemi' if lang == 'it' else 'More puzzles'}">{''.join(pager)}</nav>
{cta_block(lang, slug_campaign(path))}
</div>"""
    return page(lang=lang, path=path, title=T['title'].format(name=name, n=p['number']),
                description=T['description'].format(name=name, n=p['number'], level=level), body=body,
                alternates={l: p[f'path_{l}'] for l in C.LANGS}, campaign=slug_campaign(path),
                og_image=p[f'og_{lang}'], ld=[breadcrumb_ld(crumbs)], section='printable')


def slug_campaign(path):
    return path.strip('/').replace('/', '-') or 'home'


def puzzle_cards(puzzles, lang, cat):
    T = C.PUZZLE[lang]
    items = []
    for p in by_category(puzzles, cat):
        name = C.CATEGORIES[lang][cat]['name']
        label = f'{name} {"n. " if lang == "it" else "#"}{p["number"]}'
        items.append(f'<li><a href="{href(p[f"path_{lang}"])}">{mini_svg(p)}<span>{e(label)}</span>'
                     f'<small>{T["level"][p["level"]]} · {p["clues"]} {"numeri" if lang == "it" else "clues"}</small></a></li>')
    return f'<ul class="pz-list">{"".join(items)}</ul>'


def category_page(puzzles, lang, cat):
    D = C.CATEGORIES[lang][cat]
    path = cat_path(lang, cat)
    crumbs = [(C.UI[lang]['nav_home'], C.PATHS[lang]['home']), (C.UI[lang]['nav_printable'], C.PATHS[lang]['printable']), (D['short'], path)]
    gen = C.UI[lang]['generator_text'].format(gen=href(GENERATOR))
    guide_links = ''.join(f'<li><a href="{href(guide_path(lang, g))}">{e(C.GUIDES[lang][g]["name"])}</a></li>'
                          for g in (('hidden-single', 'locked', 'hidden-pair') if cat in ('easy', 'large-print', 'x', 'jigsaw') else ('locked', 'hidden-pair', 'x-wing', 'xy-wing')))
    body = f"""<div class="wrap">
{breadcrumb_html(lang, crumbs)}
<h1>{e(D['h1'])}</h1>
{''.join(f'<p class="lead">{e(t)}</p>' for t in D['intro'])}
<h2>{'Gli schemi' if lang == 'it' else 'The puzzles'}</h2>
{puzzle_cards(puzzles, lang, cat)}
<h2>{'Tecniche utili' if lang == 'it' else 'Useful techniques'}</h2>
<ul>{guide_links}</ul>
<p>{gen}</p>
{cta_block(lang, slug_campaign(path))}
</div>"""
    first = by_category(puzzles, cat)[0]
    return page(lang=lang, path=path, title=D['title'], description=D['description'], body=body,
                alternates={l: cat_path(l, cat) for l in C.LANGS}, campaign=slug_campaign(path),
                og_image=first[f'og_{lang}'], ld=[breadcrumb_ld(crumbs)], section='printable')


def hub_page(puzzles, lang):
    H = C.HUB[lang]
    path = C.PATHS[lang]['printable']
    crumbs = [(C.UI[lang]['nav_home'], C.PATHS[lang]['home']), (C.UI[lang]['nav_printable'], path)]
    sections = []
    for cat in C.CATEGORY_ORDER:
        D = C.CATEGORIES[lang][cat]
        sections.append(f'<h3><a href="{href(cat_path(lang, cat))}">{e(D["h1"])}</a></h3>'
                        f'<p>{e(D["intro"][0])}</p>{puzzle_cards(puzzles, lang, cat)}')
    faq_html = ''.join(f'<dt>{e(q)}</dt><dd>{e(a)}</dd>' for q, a in H['faq'])
    faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage',
              'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in H['faq']]}
    guides = ''.join(f'<li><a href="{href(guide_path(lang, g))}">{e(C.GUIDES[lang][g]["name"])}</a></li>' for g in C.GUIDE_ORDER)
    body = f"""<div class="wrap">
{breadcrumb_html(lang, crumbs)}
<h1>{e(H['h1'])}</h1>
{''.join(f'<p class="lead">{e(t)}</p>' for t in H['intro'])}
<h2>{H['categories_title']}</h2>
{''.join(sections)}
<h2>{C.UI[lang]['generator_link']}</h2>
<p>{C.UI[lang]['generator_text'].format(gen=href(GENERATOR))}</p>
<h2>{H['guides_title']}</h2>
<p>{H['guides_text']}</p>
<ul>{guides}</ul>
<h2>{H['faq_title']}</h2>
<dl class="faq">{faq_html}</dl>
{cta_block(lang, slug_campaign(path))}
</div>"""
    return page(lang=lang, path=path, title=H['title'], description=H['description'], body=body,
                alternates={l: C.PATHS[l]['printable'] for l in C.LANGS}, campaign=slug_campaign(path),
                ld=[breadcrumb_ld(crumbs), faq_ld], section='printable')


def guides_hub(lang):
    G = C.GUIDES_HUB[lang]
    path = C.PATHS[lang]['guides']
    crumbs = [(C.UI[lang]['nav_home'], C.PATHS[lang]['home']), (C.UI[lang]['nav_guides'], path)]
    cards = ''.join(f'<div class="card"><h3><a href="{href(guide_path(lang, g))}">{e(C.GUIDES[lang][g]["h1"])}</a></h3>'
                    f'<p>{e(C.GUIDES[lang][g]["description"])}</p></div>' for g in C.GUIDE_ORDER)
    body = f"""<div class="wrap">
{breadcrumb_html(lang, crumbs)}
<h1>{e(G['h1'])}</h1>
{''.join(f'<p class="lead">{e(t)}</p>' for t in G['intro'])}
<div class="cards" style="margin-top:24px">{cards}</div>
<p style="margin-top:24px"><a href="{href(C.PATHS[lang]['printable'])}">{e(C.HUB[lang]['h1'])}</a></p>
{cta_block(lang, slug_campaign(path))}
</div>"""
    return page(lang=lang, path=path, title=G['title'], description=G['description'], body=body,
                alternates={l: C.PATHS[l]['guides'] for l in C.LANGS}, campaign=slug_campaign(path),
                ld=[breadcrumb_ld(crumbs)], section='guides')


def guide_page(lang, key):
    G = C.GUIDES[lang][key]
    U = C.GUIDE_UI[lang]
    path = guide_path(lang, key)
    crumbs = [(C.UI[lang]['nav_home'], C.PATHS[lang]['home']), (C.UI[lang]['nav_guides'], C.PATHS[lang]['guides']), (G['name'], path)]
    parts = []
    for kind, val in G['body']:
        if kind == 'p':
            parts.append(f'<p>{e(val)}</p>')
        elif kind == 'h2':
            parts.append(f'<h2>{e(val)}</h2>')
        elif kind in ('ol', 'ul'):
            parts.append(f'<{kind}>{"".join(f"<li>{e(x)}</li>" for x in val)}</{kind}>')
        elif kind == 'figure':
            svg, info = DIAGRAMS[val](lang)
            cap = G['caption'].format(**info) if info else G['caption']
            parts.append(f'<figure>{svg}<figcaption>{e(cap)}</figcaption></figure>')
    k = C.GUIDE_ORDER.index(key)
    pager = []
    if k > 0:
        g = C.GUIDE_ORDER[k - 1]
        pager.append(f'<a href="{href(guide_path(lang, g))}">← {e(C.GUIDES[lang][g]["name"])}</a>')
    pager.append(f'<a href="{href(C.PATHS[lang]["guides"])}">{U["all"]}</a>')
    if k < len(C.GUIDE_ORDER) - 1:
        g = C.GUIDE_ORDER[k + 1]
        pager.append(f'<a href="{href(guide_path(lang, g))}">{e(C.GUIDES[lang][g]["name"])} →</a>')
    practice = cat_path(lang, 'medium' if key != 'city' else 'easy')
    body = f"""<div class="wrap" style="max-width:820px">
{breadcrumb_html(lang, crumbs)}
<h1>{e(G['h1'])}</h1>
{''.join(parts)}
<div class="card" style="margin-top:28px"><h3>{e(U['academy'].format(lesson=G['lesson']))}</h3><p>{e(U['academy_text'])}</p></div>
{'' if key == 'city' else f'<p style="margin-top:20px"><a href="{href(practice)}">{e(U["practice"])}</a></p>'}
<nav class="pager" aria-label="{U['all']}">{''.join(pager)}</nav>
{cta_block(lang, slug_campaign(path))}
</div>"""
    return page(lang=lang, path=path, title=G['title'], description=G['description'], body=body,
                alternates={l: guide_path(l, key) for l in C.LANGS}, campaign=slug_campaign(path),
                ld=[breadcrumb_ld(crumbs)], section='guides')


def home_page(puzzles, lang):
    H = C.HOME[lang]
    path = C.PATHS[lang]['home']
    campaign = 'home' if lang == 'it' else 'en-home'
    qr = href(f'assets/qr-play-{campaign}.svg')
    quick = ''.join(f'<a href="{href(C.PATHS[lang][k])}">{e(t)}</a>' for k, t in H['quick'])
    cards = ''.join(f'<div class="card"><span class="emoji" aria-hidden="true">{em}</span><h3>{e(t)}</h3><p>{e(d)}</p></div>' for em, t, d in H['cards'])
    avatars = ''.join(f'<div class="avatar"><img src="{href(f"assets/{f}.webp")}" alt="{e(a)}" width="300" height="300" loading="lazy" decoding="async"><span>{e(n)}</span><small>{e(s)}</small></div>'
                      for f, n, s, a in H['avatars'])
    shots = ''.join(f'<img src="{href(f"assets/{f}.webp")}" alt="{e(a)}" width="480" height="1077" loading="lazy" decoding="async">' for f, a in H['shots'])
    print_cards = ''.join(f'<div class="card"><h3><a href="{href(cat_path(lang, c))}">{e(C.CATEGORIES[lang][c]["h1"])}</a></h3></div>' for c in C.CATEGORY_ORDER)
    play_link = e(play_url(campaign))
    body = f"""<section class="hero"><div class="wrap">
<img src="{href('assets/icon.webp')}" alt="{'Icona di Grafite Sudoku' if lang == 'it' else 'Grafite Sudoku icon'}" width="120" height="120" fetchpriority="high">
<h1>{e(H['h1'])}</h1>
<div class="tagline">{e(H['tagline'])}</div>
<p class="sub">{e(H['sub'])}</p>
<div class="row"><a class="btn btn-primary" href="{href('play/')}">{H['play']}</a><a class="btn btn-secondary play-store-link" data-utm-campaign="{campaign}" href="{play_link}" rel="noopener">{C.UI[lang]['cta_button']}</a></div>
<div class="row quick">{quick}</div>
</div></section>
<section><div class="wrap"><div class="head"><h2>{e(H['why_title'])}</h2><p>{e(H['why_sub'])}</p></div><div class="cards">{cards}</div></div></section>
<section class="alt"><div class="wrap"><div class="head"><h2>{e(H['app_title'])}</h2><p>{e(H['app_sub'])}</p>
<div class="qr"><img src="{qr}" alt="QR code Google Play" width="84" height="84" loading="lazy"><div><b>{e(H['qr_headline'])}</b><small>{e(H['qr_caption'])}</small></div></div></div>
<div class="avatars">{avatars}</div>
<div class="avatar" style="max-width:240px;margin:28px auto 0"><img src="{href('assets/shot-traguardi.webp')}" alt="{e(H['trophy_alt'])}" width="440" height="987" loading="lazy" decoding="async" style="max-width:100%;border-radius:12px"><small>{e(H['trophy_caption'])}</small></div>
<p style="text-align:center;margin-top:22px">{e(H['app_list'])}</p>
<div class="row" style="justify-content:center;margin-top:20px"><a class="btn btn-primary play-store-link" data-utm-campaign="{campaign}" href="{play_link}" rel="noopener">{C.UI[lang]['cta_button']}</a></div>
</div></section>
<section><div class="wrap"><div class="head"><h2>{e(H['print_title'])}</h2><p>{e(H['print_sub'])}</p></div><div class="cards">{print_cards}</div>
<p style="text-align:center;margin-top:20px"><a href="{href(C.PATHS[lang]['printable'])}">{e(H['print_all'])}</a> · <a href="{href(C.PATHS[lang]['guides'])}">{e(C.GUIDES_HUB[lang]['h1'])}</a></p></div></section>
<section class="alt"><div class="wrap"><div class="head"><h2>{e(H['shots_title'])}</h2><p>{e(H['shots_sub'])}</p></div><div class="shots">{shots}</div></div></section>
<section><div class="wrap" style="text-align:center"><div class="head"><h2>{e(H['demo_title'])}</h2><p>{e(H['demo_sub'])}</p></div>
<a class="btn btn-primary" href="{href('play/')}">{H['play']}</a>
<div class="demo-note">{H['demo_note']}</div></div></section>"""
    org = {'@type': 'Organization', 'name': 'GrafiteSoft', 'email': 'grafitesoft@gmail.com', 'url': SITE_URL}
    app = {'@context': 'https://schema.org', '@type': 'MobileApplication', 'name': 'Grafite Sudoku',
           'operatingSystem': 'ANDROID', 'applicationCategory': 'GameApplication', 'url': absolute(path),
           'downloadUrl': PLAY_BASE, 'installUrl': PLAY_BASE, 'image': absolute('assets/icon.png'),
           'description': H['description'], 'inLanguage': APP_LANGUAGES,
           'screenshot': [absolute(f'assets/{f}.jpg') for f, _ in H['shots']],
           'featureList': [t for _, t, _ in H['cards']],
           'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'EUR'},
           'publisher': org}
    site = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Grafite Sudoku', 'url': absolute(path), 'inLanguage': lang}
    org_ld = dict(org, **{'@context': 'https://schema.org', 'logo': absolute('assets/icon.png')})
    return page(lang=lang, path=path, title=H['title'], description=H['description'], body=body,
                alternates={l: C.PATHS[l]['home'] for l in C.LANGS}, campaign=campaign,
                ld=[site, org_ld, app], extra_css=HOME_CSS, extra_head=(VERIFY_META + '\n') if lang == 'it' else '',
                section='home')


# ---------------------------------------------------------------- diagrammi

def svg_grid(cells, marks=None, rows=9, cols=9, box=3, highlight=(), struck=(), shade=(), lines=()):
    """Griglia SVG per le guide. cells: {(r,c): numero}; marks: {(r,c): [(n, stato)]}
    con stato '' / 'key' (oro) / 'x' (da togliere)."""
    s = 40
    w, h = cols * s, rows * s
    out = [f'<svg viewBox="-2 -2 {w + 4} {h + 4}" role="img" xmlns="http://www.w3.org/2000/svg">',
           f'<rect width="{w}" height="{h}" fill="#fbf8ef"/>']
    for (r, c) in shade:
        out.append(f'<rect x="{c*s}" y="{r*s}" width="{s}" height="{s}" fill="#d9d0b8"/>')
    for (r, c) in highlight:
        out.append(f'<rect x="{c*s}" y="{r*s}" width="{s}" height="{s}" fill="#ecc96f"/>')
    for (r, c) in struck:
        out.append(f'<rect x="{c*s}" y="{r*s}" width="{s}" height="{s}" fill="#f1c9bd"/>')
    for x1, y1, x2, y2 in lines:
        out.append(f'<line x1="{x1*s+s/2}" y1="{y1*s+s/2}" x2="{x2*s+s/2}" y2="{y2*s+s/2}" stroke="#C99A3E" stroke-width="3" stroke-dasharray="6 4"/>')
    for k in range(rows + 1):
        sw = 3 if k % box == 0 or k == rows else 1
        out.append(f'<line x1="0" y1="{k*s}" x2="{w}" y2="{k*s}" stroke="#14181F" stroke-width="{sw}"/>')
    for k in range(cols + 1):
        sw = 3 if k % box == 0 or k == cols else 1
        out.append(f'<line x1="{k*s}" y1="0" x2="{k*s}" y2="{h}" stroke="#14181F" stroke-width="{sw}"/>')
    for (r, c), v in cells.items():
        out.append(f'<text x="{c*s+s/2}" y="{r*s+s*0.7}" text-anchor="middle" font-size="24" font-weight="700" font-family="Noto Sans, sans-serif" fill="#14181F">{v}</text>')
    for (r, c), ms in (marks or {}).items():
        for n, state in ms:
            mr, mc = divmod(n - 1, 3)
            x, y = c * s + 7 + mc * 13, r * s + 12 + mr * 12.5
            col = {'': '#4b556b', 'key': '#8a5a00', 'x': '#b0372b'}[state]
            fw = '700' if state else '400'
            out.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="11" font-weight="{fw}" font-family="Noto Sans, sans-serif" fill="{col}">{n}</text>')
            if state == 'x':
                out.append(f'<line x1="{x-5}" y1="{y-8}" x2="{x+5}" y2="{y+2}" stroke="#b0372b" stroke-width="1.5"/>')
    out.append('</svg>')
    return ''.join(out)


def diag_hidden_single(lang):
    # 7 nelle righe 2 e 3 e nelle colonne 2 e 3: nel riquadro resta solo r1c1.
    cells = {(1, 5): 7, (2, 8): 7, (5, 1): 7, (7, 2): 7, (0, 4): 2, (4, 6): 5}
    blocked = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    # linee: (colonna, riga) di partenza e di arrivo
    return svg_grid(cells, highlight=[(0, 0)], shade=blocked,
                    lines=[(5, 1, 0, 1), (8, 2, 0, 2), (1, 5, 1, 0), (2, 7, 2, 0)]).replace('</svg>', '<text x="20" y="28" text-anchor="middle" font-size="24" font-weight="700" fill="#8a5a00">7</text></svg>'), {}


def diag_locked(lang):
    cells = {(0, 0): 1, (0, 1): 5, (0, 2): 8, (2, 0): 3, (2, 1): 7, (2, 2): 6, (1, 2): 9, (0, 6): 2}
    marks = {(1, 0): [(2, ''), (4, 'key')], (1, 1): [(2, ''), (4, 'key')],
             (1, 4): [(3, ''), (4, 'x'), (6, '')], (1, 7): [(1, ''), (4, 'x'), (8, '')], (1, 5): [(1, ''), (3, '')]}
    return svg_grid(cells, marks, rows=3, highlight=[(1, 0), (1, 1)], struck=[(1, 4), (1, 7)]), {}


def diag_hidden_pair(lang):
    cells = {(0, 0): 4, (0, 2): 2, (0, 4): 9, (0, 8): 7}
    marks = {(0, 1): [(1, 'x'), (3, 'key'), (6, 'x'), (8, 'key')], (0, 3): [(1, ''), (5, ''), (6, '')],
             (0, 5): [(1, ''), (6, '')], (0, 6): [(3, 'key'), (5, 'x'), (8, 'key')], (0, 7): [(1, ''), (5, ''), (6, '')]}
    return svg_grid(cells, marks, rows=1, highlight=[(0, 1), (0, 6)]), {}


def diag_x_wing(lang):
    marks = {(1, 2): [(5, 'key')], (1, 7): [(5, 'key')], (6, 2): [(5, 'key')], (6, 7): [(5, 'key')],
             (3, 2): [(1, ''), (5, 'x')], (4, 7): [(5, 'x'), (9, '')], (8, 2): [(3, ''), (5, 'x')]}
    cells = {(0, 2): 7, (2, 8): 4, (3, 5): 8, (8, 0): 1, (5, 4): 6, (1, 0): 3}
    return svg_grid(cells, marks, highlight=[(1, 2), (1, 7), (6, 2), (6, 7)], struck=[(3, 2), (4, 7), (8, 2)],
                    lines=[(2, 1, 7, 1), (2, 6, 7, 6), (2, 1, 2, 6), (7, 1, 7, 6)]), {}


def diag_xy_wing(lang):
    marks = {(4, 4): [(2, 'key'), (7, 'key')], (4, 0): [(2, 'key'), (9, 'key')], (1, 4): [(7, 'key'), (9, 'key')],
             (1, 0): [(1, ''), (6, ''), (9, 'x')]}
    cells = {(0, 0): 5, (3, 2): 3, (7, 4): 8}
    return svg_grid(cells, marks, highlight=[(4, 4), (4, 0), (1, 4)], struck=[(1, 0)],
                    lines=[(4, 4, 0, 4), (4, 4, 4, 1)]), {}


CITY = [[1, 2, 3, 4], [2, 3, 4, 1], [4, 1, 2, 3], [3, 4, 1, 2]]


def visible(line):
    best, n = 0, 0
    for h in line:
        if h > best:
            best, n = h, n + 1
    return n


def diag_city(lang):
    n = len(CITY)
    s = 40
    size = (n + 2) * s
    out = [f'<svg viewBox="0 0 {size} {size}" role="img" xmlns="http://www.w3.org/2000/svg">',
           f'<rect x="{s}" y="{s}" width="{n*s}" height="{n*s}" fill="#fbf8ef"/>',
           f'<rect x="{s}" y="{s}" width="{n*s}" height="{s}" fill="#ecc96f"/>']
    cols = [[CITY[r][c] for r in range(n)] for c in range(n)]
    clues = {'top': [visible(cols[c]) for c in range(n)], 'bottom': [visible(cols[c][::-1]) for c in range(n)],
             'left': [visible(CITY[r]) for r in range(n)], 'right': [visible(CITY[r][::-1]) for r in range(n)]}
    for k in range(n + 1):
        out.append(f'<line x1="{s}" y1="{s+k*s}" x2="{s+n*s}" y2="{s+k*s}" stroke="#14181F" stroke-width="{3 if k in (0, n) else 1}"/>')
        out.append(f'<line x1="{s+k*s}" y1="{s}" x2="{s+k*s}" y2="{s+n*s}" stroke="#14181F" stroke-width="{3 if k in (0, n) else 1}"/>')
    t = '<text x="{x}" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="700" font-family="Noto Sans, sans-serif" fill="{fill}">{v}</text>'
    for r in range(n):
        for c in range(n):
            out.append(t.format(x=s + c * s + s / 2, y=s + r * s + s * .7, fs=22, fill='#14181F', v=CITY[r][c]))
    for i in range(n):
        out.append(t.format(x=s + i * s + s / 2, y=s * .7, fs=18, fill='#8a5a00', v=clues['top'][i]))
        out.append(t.format(x=s + i * s + s / 2, y=(n + 1) * s + s * .7, fs=18, fill='#8a5a00', v=clues['bottom'][i]))
        out.append(t.format(x=s / 2, y=s + i * s + s * .7, fs=18, fill='#8a5a00', v=clues['left'][i]))
        out.append(t.format(x=(n + 1) * s + s / 2, y=s + i * s + s * .7, fs=18, fill='#8a5a00', v=clues['right'][i]))
    out.append('</svg>')
    return ''.join(out), {'clue': clues['left'][0]}


DIAGRAMS = {'hidden-single': diag_hidden_single, 'locked': diag_locked, 'hidden-pair': diag_hidden_pair,
            'x-wing': diag_x_wing, 'xy-wing': diag_xy_wing, 'city': diag_city}


# ------------------------------------------------------- PDF e anteprime

def find_chrome():
    for c in (os.environ.get('CHROME'), r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
              shutil.which('chromium'), shutil.which('chromium-browser'), shutil.which('google-chrome')):
        if c and os.path.exists(c):
            return c
    return None


def chrome_run(chrome, args, profile):
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                    f'--user-data-dir={profile}', *args], check=True, capture_output=True, timeout=120)


PRINT_CSS = """
@page{size:A4;margin:14mm}
body{margin:0;font-family:"Noto Sans",sans-serif;color:#14181F}
.pg{height:269mm;display:flex;flex-direction:column;align-items:center;page-break-after:always}
.pg:last-child{page-break-after:auto}
.band{width:100%;display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #C99A3E;padding-bottom:3mm;margin-bottom:6mm}
.band b{font-family:"Shippori Mincho",serif;font-size:16pt}.band span{font-size:10pt;color:#5a5446}
h1{font-family:"Shippori Mincho",serif;font-size:20pt;margin:0 0 5mm;text-align:center}
table{border-collapse:collapse}
td{border:0.3mm solid #8d8470;text-align:center;font-weight:400;color:#14181F;padding:0}
td.g{font-weight:700}td.dg{background:#ece0c0}
td.br{border-right:0.9mm solid #14181F}td.bb{border-bottom:0.9mm solid #14181F}
tr:first-child td{border-top:0.9mm solid #14181F}tr:last-child td{border-bottom:0.9mm solid #14181F}
td:first-child{border-left:0.9mm solid #14181F}td:last-child{border-right:0.9mm solid #14181F}
.rules{font-size:10.5pt;max-width:170mm;margin-top:7mm;text-align:center;color:#2a3040}
.foot{margin-top:auto;font-size:9pt;color:#5a5446;text-align:center}
"""


def pdf_grid(p, values, cell_mm, font_pt):
    rows = []
    for r in range(9):
        tds = []
        for c in range(9):
            i = r * 9 + c
            cls = cell_classes(p, i)
            if values[i] and p['puzzle'][i]:
                cls.append('g')
            style = f'width:{cell_mm}mm;height:{cell_mm}mm;font-size:{font_pt}pt'
            if p['variant'] == 'jigsaw':
                style += f';background:{REGION_TINTS[p["regions"][i]]}'
            tds.append(f'<td class="{" ".join(cls)}" style="{style}">{values[i] or ""}</td>')
        rows.append('<tr>' + ''.join(tds) + '</tr>')
    return '<table>' + ''.join(rows) + '</table>'


def pdf_html(p, lang):
    T = C.PUZZLE[lang]
    name = puzzle_name(lang, p)
    big = p['category'] == 'large-print'
    title = T['h1'].format(name=name, n=p['number'])
    level = T['level'][p['level']]
    url = absolute(p[f'path_{lang}']).replace('https://', '')
    sol = 'Soluzione' if lang == 'it' else 'Solution'
    fonts = 'file:///' + os.path.join(ROOT, 'assets', 'fonts', 'fonts.css').replace('\\', '/')
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><link rel="stylesheet" href="{fonts}"><style>{PRINT_CSS}</style></head><body>
<div class="pg"><div class="band"><b>Grafite Sudoku</b><span>{e(name)} · {level} · {p['clues']} {'numeri' if lang == 'it' else 'clues'}</span></div>
<h1>{e(title)}</h1>{pdf_grid(p, p['puzzle'], 19.5 if big else 18, 30 if big else 22)}
<p class="rules">{e(C.RULES[lang][p['variant']])}</p>
<p class="foot">{'Soluzione a pagina 2' if lang == 'it' else 'Solution on page 2'} · {e(url)}</p></div>
<div class="pg"><div class="band"><b>Grafite Sudoku</b><span>{sol} · {e(title)}</span></div>
<h1>{sol}</h1>{pdf_grid(p, p['solution'], 13, 15)}
<p class="foot">{'Altri sudoku da stampare' if lang == 'it' else 'More printable sudoku'}: {e(absolute(C.PATHS[lang]['printable']).replace('https://', ''))} · {'App gratis su Google Play, senza pubblicità' if lang == 'it' else 'Free app on Google Play, no ads'}</p></div>
</body></html>"""


def og_html(p, lang):
    T = C.PUZZLE[lang]
    name = puzzle_name(lang, p)
    fonts = 'file:///' + os.path.join(ROOT, 'assets', 'fonts', 'fonts.css').replace('\\', '/')
    icon = 'file:///' + os.path.join(ROOT, 'assets', 'icon.png').replace('\\', '/')
    level = T['level'][p['level']]
    free = 'PDF gratis con soluzione' if lang == 'it' else 'Free PDF with answers'
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{fonts}"><style>
html,body{{margin:0;width:1200px;height:630px;overflow:hidden;background:#14181F;font-family:"Noto Sans",sans-serif}}
.wrap{{display:flex;align-items:center;gap:56px;padding:35px 60px;height:630px;box-sizing:border-box}}
.g{{background:#F0EAD9;padding:16px;border-radius:18px}}
table{{border-collapse:collapse}}td{{width:58px;height:58px;border:1px solid #b9ae92;text-align:center;font-size:30px;font-weight:700;color:#14181F;background:#fbf8ef;padding:0}}
td.dg{{background:#efe2c2}}td.br{{border-right:4px solid #14181F}}td.bb{{border-bottom:4px solid #14181F}}
tr:first-child td{{border-top:4px solid #14181F}}tr:last-child td{{border-bottom:4px solid #14181F}}td:first-child{{border-left:4px solid #14181F}}td:last-child{{border-right:4px solid #14181F}}
.t{{color:#f7f3e8}}.k{{color:#C99A3E;font-size:26px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}}
h1{{font-family:"Shippori Mincho",serif;font-size:58px;line-height:1.1;margin:14px 0 18px}}
.f{{font-size:28px;color:#e3c583}}.b{{display:flex;align-items:center;gap:14px;margin-top:40px;font-family:"Shippori Mincho",serif;font-size:30px;font-weight:700}}
.b img{{width:56px;height:56px;border-radius:12px}}
</style></head><body><div class="wrap"><div class="g">{og_grid(p)}</div>
<div class="t"><div class="k">{level}</div><h1>{e(name)}<br>{'n. ' if lang == 'it' else '#'}{p['number']}</h1><div class="f">{free}</div>
<div class="b"><img src="{icon}" alt="">Grafite Sudoku</div></div></div></body></html>"""


def og_grid(p):
    rows = []
    for r in range(9):
        tds = []
        for c in range(9):
            i = r * 9 + c
            cls = cell_classes(p, i)
            style = f' style="background:{REGION_TINTS[p["regions"][i]]}"' if p['variant'] == 'jigsaw' else ''
            tds.append(f'<td class="{" ".join(cls)}"{style}>{p["puzzle"][i] or ""}</td>')
        rows.append('<tr>' + ''.join(tds) + '</tr>')
    return '<table>' + ''.join(rows) + '</table>'


def build_media(puzzles, force):
    chrome = find_chrome()
    if not chrome:
        print('Chrome non trovato: PDF e anteprime non generati (imposta la variabile CHROME).')
        return
    os.makedirs(os.path.join(ROOT, 'pdf'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'assets', 'og'), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='grafite-build-')
    profile = os.path.join(tmp, 'profile')
    made = 0
    try:
        for p in puzzles:
            for lang in C.LANGS:
                pdf = os.path.join(ROOT, p[f'pdf_{lang}'])
                if force and p.get('serie3_slug') and lang == 'en':
                    pass  # i PDF della serie 3 sono quelli già promessi su Pinterest: non si rigenerano
                elif force or not os.path.exists(pdf):
                    src = os.path.join(tmp, 'pdf.html')
                    open(src, 'w', encoding='utf-8').write(pdf_html(p, lang))
                    chrome_run(chrome, ['--no-pdf-header-footer', f'--print-to-pdf={pdf}', 'file:///' + src.replace('\\', '/')], profile)
                    made += 1
                og = os.path.join(ROOT, p[f'og_{lang}'])
                if force or not os.path.exists(og):
                    src = os.path.join(tmp, 'og.html')
                    open(src, 'w', encoding='utf-8').write(og_html(p, lang))
                    chrome_run(chrome, ['--window-size=1200,630', f'--screenshot={og}', 'file:///' + src.replace('\\', '/')], profile)
                    made += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f'{made} file PDF/anteprima generati')


# ------------------------------------------------------------- sitemap

def git_date(rel):
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        return out or None
    except Exception:
        return None


def build_sitemap(groups):
    """groups: lista di {lingua: percorso} (una voce per lingua, con hreflang)."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for g in groups:
        for lang, path in g.items():
            file = path + 'index.html' if path.endswith('/') or path == '' else path
            out.append('  <url>')
            out.append(f'    <loc>{absolute(path)}</loc>')
            d = git_date(file)
            if d:
                out.append(f'    <lastmod>{d}</lastmod>')
            if len(g) > 1:
                for l2, p2 in g.items():
                    out.append(f'    <xhtml:link rel="alternate" hreflang="{l2}" href="{absolute(p2)}"/>')
                if 'en' in g:
                    out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{absolute(g["en"])}"/>')
            out.append('  </url>')
    out.append('</urlset>')
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')


# ---------------------------------------------------------------- main

def write(path, content):
    file = os.path.join(ROOT, path, 'index.html') if path.endswith('/') or path == '' else os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def main():
    force = '--force' in sys.argv
    puzzles = load_puzzles()
    groups = []
    for lang in C.LANGS:
        write(C.PATHS[lang]['home'], home_page(puzzles, lang))
        write(C.PATHS[lang]['printable'], hub_page(puzzles, lang))
        write(C.PATHS[lang]['guides'], guides_hub(lang))
        for cat in C.CATEGORY_ORDER:
            write(cat_path(lang, cat), category_page(puzzles, lang, cat))
        for p in puzzles:
            write(p[f'path_{lang}'], puzzle_page(puzzles, p, lang))
        for g in C.GUIDE_ORDER:
            write(guide_path(lang, g), guide_page(lang, g))
    groups.append({l: C.PATHS[l]['home'] for l in C.LANGS})
    groups.append({l: C.PATHS[l]['printable'] for l in C.LANGS})
    groups += [{l: cat_path(l, cat) for l in C.LANGS} for cat in C.CATEGORY_ORDER]
    groups += [{l: p[f'path_{l}'] for l in C.LANGS} for p in puzzles]
    groups.append({l: C.PATHS[l]['guides'] for l in C.LANGS})
    groups += [{l: guide_path(l, g) for l in C.LANGS} for g in C.GUIDE_ORDER]
    groups += [{'it': GENERATOR}, {'it': 'play/'}]
    build_sitemap(groups)
    print(f'{sum(len(g) for g in groups)} URL nella sitemap')
    if '--pages' not in sys.argv:
        build_media(puzzles, force)


if __name__ == '__main__':
    main()
