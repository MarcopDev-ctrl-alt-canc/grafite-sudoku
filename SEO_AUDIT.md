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
