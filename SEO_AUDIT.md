# Audit SEO — sito di Grafite Sudoku

Stato del sito prima del rinnovo (branch `seo-refresh`, partito da `main` @ `e8db8e5`). Misure prese in locale con `python -m http.server`, servendo il repo sotto `/grafite-sudoku/` come su GitHub Pages.

## Pagine

### `index.html` (home, italiano)
- Peso 17,5 KB. `lang="it"`, canonical assoluta corretta, nessun hreflang.
- Title (44 car.): "Grafite Sudoku — sudoku con anima giapponese". Non contiene nessuna query cercata ("sudoku", "app", "gratis", "senza pubblicità").
- Description (222 car.): troppo lunga, Google la taglia intorno a 155-160.
- Titoli: h1 "Grafite Sudoku"; h2 "Perché Grafite Sudoku", "Nell'app completa ti aspettano", "Uno sguardo al gioco", "Prova subito, senza installare nulla"; 7 h3 nelle card.
- Immagini: 13, tutte con `alt` (l'icona nel logo ha `alt=""`, decorativa: corretto). **Nessuna ha `width`/`height`**. Avatar PNG 512×512 pesanti (monaco 467 KB, samurai 291 KB, kitsune 235 KB): circa 1,3 MB di immagini, quasi tutte sotto la piega e senza `loading="lazy"`.
- Risorse esterne: Google Fonts (CSS + font) e `qrcodejs` da cdnjs. Entrambi bloccano o ritardano la pagina e contraddicono "zero tracciamento".
- Dati strutturati: `SoftwareApplication` valido, senza `inLanguage`, `screenshot`, `featureList`.
- Link interni rotti: nessuno.
- Testi da correggere rispetto all'app attuale: "45 trofei" (numero fisso), "Cinque texture di carta", "Quattro sudoku in uno" (l'app ha anche la Città), "Nessun tracciamento. Mai." (formula non ammessa).

### `sudoku-da-stampare.html` (generatore di schemi)
- Peso 77,8 KB, di cui gran parte JavaScript che genera gli schemi nel browser: **il contenuto degli schemi non esiste nell'HTML** che legge Google.
- `lang="it"`, canonical a se stessa, nessun hreflang. Le 5 lingue (it/en/es/pt/id) cambiano il testo via JavaScript sulla stessa URL: Google ne indicizza una sola, l'italiano.
- Title (82 car.) e description (195 car.) un po' lunghi; buone parole chiave.
- Titoli: un solo h1 ("Sudoku da stampare gratis, carta e matita"), **nessun h2**.
- Risorse esterne: Google Fonts e `qrcodejs` da cdnjs.
- Dati strutturati: `WebApplication`.
- Lighthouse: contrasto insufficiente in qualche testo, bersagli di tocco troppo piccoli, una tabella senza intestazioni (`td-has-header`), CLS 0,236 (il layout salta mentre il JS costruisce la pagina), DOM di 1.777 elementi.

### `play/` (demo Flutter)
- `index.html` di 6,2 KB generato dalla build della demo; 41 MB di file compilati.
- Nessun h1, nessun testo indicizzabile, nessuna canonical: per Google è una pagina vuota.
- `play/flutter_bootstrap.js` risulta modificato in `git status`: non va nei commit di questo lavoro.

### File tecnici
- `sitemap.xml`: 2 URL, `lastmod` 2026-09-12 (le pagine sono cambiate dopo: home 2026-10-01, stampa 2026-09-30); manca `/play/`.
- `robots.txt`: sta in `/grafite-sudoku/robots.txt`, ma i crawler leggono solo quello alla radice del dominio (`marcopdev-ctrl-alt-canc.github.io/robots.txt`). Innocuo; la sitemap va inviata a mano in Search Console.
- Verifica Search Console: meta tag `google-site-verification` in `index.html` (va mantenuto in ogni versione della home).
- `og-image.png` 1200×630 unica per tutte le pagine.

## Lighthouse (mobile, prima del rinnovo)

| Pagina | Performance | Accessibilità | Best practices | SEO | LCP | CLS |
|---|---|---|---|---|---|---|
| Home | 69 | 100 | 96 | 100 | 8,8 s | 0,009 |
| Stampa | 73 | 91 | 100 | 100 | 3,4 s | 0,236 |

Il server locale non comprime e non mette cache: su GitHub Pages (gzip) i numeri reali sono un po' migliori, ma le cause restano. Principali: risorse che bloccano il rendering (circa 2,2 s, i font di Google), immagini non ottimizzate (circa 1 MB risparmiabile in WebP), immagini senza dimensioni, CLS della pagina di stampa.

Il punteggio SEO 100 di Lighthouse misura solo l'igiene tecnica della pagina: non dice niente sul fatto che le pagine rispondano a ricerche reali, che è il problema vero.

## Interventi, dal più al meno importante

1. **Pagine di schemi statiche**, una per schema, con la griglia in HTML: oggi non esiste nessuna pagina che Google possa associare a "printable sudoku" o "sudoku facili da stampare". Le pin Pinterest della serie 3 puntano già a 5 di queste URL.
2. **Versione inglese con URL proprie** (`/en/`), con hreflang it/en: il pubblico che cerca "printable sudoku" è molto più grande di quello italiano, e oggi l'inglese esiste solo via JavaScript sulla URL italiana.
3. **Hub di categoria** (`/sudoku-da-stampare/`, `/en/printable-sudoku/`) con testo utile e link a tutti gli schemi.
4. **Guide alle tecniche** (hidden single, locked candidates, X-Wing…): query informative ad alto volume, legate alle lezioni dell'Accademia.
5. **Font self-hosted** al posto di Google Fonts: tolgono circa 2 s di rendering bloccato e una richiesta a Google.
6. **Immagini**: WebP, `width`/`height`, `loading="lazy"` sotto la piega (circa 1 MB in meno sulla home).
7. **Sitemap completa** con `lastmod` da `git log`, hreflang e `/play/`, da inviare a Search Console.
8. **Title e description** della home con parole cercate, sotto i 60/155 caratteri; testi allineati all'app attuale (Città, 7 lingue, niente numeri fissi, frasi sulla privacy ammesse).
9. **Dati strutturati**: `MobileApplication` completa, `WebSite`, `Organization`, `BreadcrumbList`.
10. **Testo HTML sopra la demo in `/play/`** e QR code generato senza CDN (o tolto), per chiudere le ultime risorse esterne.

## Parere

Il sito è pulito ma quasi invisibile: tecnicamente a posto, non ha pagine che corrispondano a quello che la gente cerca, e tutto il contenuto utile (schemi, inglese) vive in JavaScript. Il guadagno vero sta nei punti 1-4: pagine statiche in inglese e italiano, con testo proprio e non ripetuto. Le prestazioni (5-6) sono lavoro rapido e sicuro, da fare insieme.

---

# Dopo il rinnovo (branch `seo-refresh`)

## Cosa è cambiato

| Intervento | Stato |
|---|---|
| 1. Pagine di schemi statiche | 24 schemi × 2 lingue = 48 pagine, griglia in `<table>` con `<caption>` e `scope`, PDF A4 (schema + soluzione), soluzione in `<details>`, suggerimento sul primo passo calcolato dallo schema, consigli per categoria, schema precedente/successivo, `BreadcrumbList`, `og:image` 1200×630 dedicata. I 5 URL della serie 3 di Pinterest sono online con gli slug esatti. |
| 2. Inglese con URL proprie | `/en/` e tutte le pagine nuove in coppia it/en con hreflang reciproco e `x-default` verso l'inglese. |
| 3. Hub e categorie | Hub `/sudoku-da-stampare/` e `/en/printable-sudoku/` (testo originale, FAQ visibile + `FAQPage`) e 6 pagine di categoria per lingua (facili, medi, difficili, caratteri grandi, X, jigsaw): una query principale per pagina, così gli schemi singoli non si contendono la stessa ricerca. |
| 4. Guide alle tecniche | 6 guide per lingua con diagramma SVG (singolo nascosto, candidato bloccato, coppia nascosta, X-Wing, XY-Wing, grattacieli/Città), più l'indice delle guide. Ognuna rimanda alla lezione della Sudoku Academy e al Play Store. |
| 5. Font self-hosted | Noto Sans (variabile) e Shippori Mincho 500/700, solo latino e latino esteso, `preload` e `font-display: swap`. Nessuna richiesta a Google Fonts. |
| 6. Immagini | Avatar e screenshot in WebP ridimensionati (circa 1,3 MB → 210 KB), con `width`/`height` e `loading="lazy"` sotto la piega. |
| 7. Sitemap | 80 URL con `lastmod` da `git log` e `xhtml:link` hreflang, compresi generatore e `/play/`. |
| 8. Title e description | Con le query della pagina, entro 60/160 caratteri circa. Testi della home allineati all'app 2.9.3 (5 modi di giocare, 7 lingue, decine di lezioni e trofei, frasi sulla privacy ammesse). |
| 9. Dati strutturati | Home: `MobileApplication` completa, `WebSite`, `Organization`. Altre pagine: `BreadcrumbList`; hub: `FAQPage`. Validati da `tools/check_site.py`. |
| 10. `/play/` e QR | Riquadro di testo con h1 sopra la demo, canonical. QR come SVG statici: niente più qrcodejs da CDN. |
| Link al Play Store | `referrer` con la campagna della pagina (`utm_campaign=<slug-pagina>`), anche senza JavaScript. |

## Lighthouse (mobile, dopo)

| Pagina | Performance | Accessibilità | Best practices | SEO | LCP | CLS |
|---|---|---|---|---|---|---|
| Home it | 99 | 100 | 100 | 100 | 2,0 s | 0,003 |
| Home en | 99 | 100 | 100 | 100 | 2,0 s | 0,014 |
| Hub en | 99 | 100 | 100 | 100 | 1,9 s | 0 |
| Schema (jigsaw-sudoku-easy) | 100 | 100 | 100 | 100 | 1,6 s | 0 |
| Guida (x-wing) | 100 | 100 | 100 | 100 | 1,6 s | 0 |
| Generatore | 99 | 92 | 100 | 100 | 1,9 s | 0 |

Il generatore (`sudoku-da-stampare.html`) è rimasto com'era a parte font, QR e link agli hub: restano i difetti di accessibilità che aveva (contrasto di qualche testo, bersagli piccoli, tabelle senza intestazioni).

## Controlli

- `python tools/check_site.py`: 78 pagine, nessun link interno rotto, JSON-LD valido, hreflang reciproci, griglie di tutte le 48 pagine schema uguali a `data/puzzles.json`.
- Testo dei 48 PDF confrontato con `data/puzzles.json` (pagina 1 schema, pagina 2 soluzione): nessuna differenza.
- Nessuna risorsa esterna nelle pagine del sito, esclusa la demo compilata in `play/`.

## Cosa resta

- Fase 3 (schema del giorno con GitHub Action): non fatta, da valutare dopo che le fasi 1-2 sono online e indicizzate.
- Volumi delle query da verificare in Search Console dopo l'indicizzazione.
- Accessibilità del generatore, se si decide di rimetterci mano.
