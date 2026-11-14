# Grafite Sudoku — sito, sudoku da stampare e demo web

Sito statico su GitHub Pages: https://marcopdev-ctrl-alt-canc.github.io/grafite-sudoku/

Porta pubblico alla scheda Google Play dell'app con pagine che rispondono a
ricerche vere: sudoku da stampare (uno per pagina, con PDF), guide alle
tecniche, demo giocabile. Italiano e inglese, con hreflang.

## Struttura

```
index.html                    home italiana            (generata)
en/                           home e pagine inglesi    (generate)
sudoku-da-stampare/           hub, categorie e schemi  (generati)
en/printable-sudoku/          idem in inglese          (generati)
tecniche-sudoku/              guide alle tecniche      (generate)
en/sudoku-techniques/         idem in inglese          (generate)
sudoku-da-stampare.html       generatore di fogli A4 nel browser (scritto a mano)
play/                         demo Flutter compilata (non si modifica a mano,
                              tranne index.html: vedi PUBBLICAZIONE.md)
pdf/                          PDF degli schemi (pagina 1 schema, pagina 2 soluzione)
assets/                       immagini, font self-hosted, QR, play-links.js
assets/og/                    anteprime social 1200×630 di ogni schema
data/puzzles.json             gli schemi delle pagine
data/serie3.json              i 5 schemi della serie 3 di Pinterest
tools/                        motore, generatore di schemi, build e controlli
sitemap.xml                   generata dal build
SEO_AUDIT.md                  audit prima e dopo il rinnovo
```

Le pagine generate non si modificano a mano: si cambiano i testi in
`tools/site_content.py` (o la logica in `tools/build_site.py`) e si rilancia il
build.

## Comandi

```
python tools/make_puzzles.py         # rigenera data/puzzles.json (stessi seed: stesso risultato)
python tools/build_site.py           # pagine, PDF e anteprime mancanti, sitemap
python tools/build_site.py --pages   # solo HTML e sitemap
python tools/build_site.py --force   # rigenera anche PDF e anteprime
python tools/check_site.py           # griglie, link interni, JSON-LD, hreflang
```

Serve Python 3 con la sola libreria standard. Per PDF e anteprime serve Google
Chrome (o Chromium: variabile `CHROME`).

## Aggiungere schemi

1. In `tools/make_puzzles.py`, aggiungi slot in fondo alla categoria in `PLAN`
   (i vecchi schemi non cambiano).
2. `python tools/make_puzzles.py`, poi `python tools/build_site.py` e
   `python tools/check_site.py`.
3. Commit, poi di nuovo `python tools/build_site.py --pages` per avere nella
   sitemap le date dei file appena committati, e commit della sitemap.

Le pagine vanno aggiunte solo se hanno valore proprio: centinaia di pagine
quasi uguali sono viste come contenuto sottile.

## Killer

Gli schemi Killer (pagine `killer`/`killer-sudoku` e la raccolta del generatore,
`assets/killer-bank.json`) non si generano qui: vengono dal motore dell'app,
verificati uno per uno (soluzione unica, chiusura a logica, nessuna gabbia da
una cella). Per rifarli, dalla cartella dell'app:

    dart run tool/killer_export.dart <cartella di questo repository>

Scrive `data/killer.json` (gli schemi fissi delle pagine) e
`assets/killer-bank.json`. Seed fissi: rilanciarlo dà gli stessi file.

## Regole del sito

- Nessuno script di analytics, nessun CDN di terze parti, nessun cookie. Font
  in `assets/fonts/` (OFL).
  Unica eccezione: il badge live di PixelPicked nel piè di pagina (immagine
  da `api.pixelpicked.com`, caricata in modo pigro e senza referer).
- Sulla privacy dell'app solo le frasi ammesse: "l'app non chiede il permesso
  Internet e non contiene librerie Google" e "0 tracker secondo Exodus
  Privacy" con il report Exodus della versione indicata (oggi 2.9.3, report
  792199); quando ne esce uno nuovo si aggiornano link e versione in
  `tools/site_content.py`.
- Niente valutazioni, download o recensioni inventati.
- I fatti sull'app (varianti, lingue, Academy) vanno presi dal sorgente
  dell'app (`sudoku_test`), non a memoria.

## Link utili

- Scheda Google Play: link e campagne in `assets/play-links.js`; le pagine
  generate hanno già l'href con `referrer=utm_source=site&utm_medium=web&utm_campaign=<pagina>`.
- Informativa privacy (repo separato): https://marcopdev-ctrl-alt-canc.github.io/-grafite-sudoku-privacy/
- Contatti: grafitesoft@gmail.com
