# Pubblicazione su GitHub Pages

Comandi per PowerShell su Windows, dalla cartella del repo.

## Pubblicare un aggiornamento del sito

```powershell
python tools/build_site.py
python tools/check_site.py          # deve dire "Nessun problema."
git add -A
git reset play/flutter_bootstrap.js # solo se è modificato e non va pubblicato
git commit -m "Descrizione della modifica"
python tools/build_site.py --pages  # sitemap con le date del commit appena fatto
git add sitemap.xml
git commit -m "Sitemap aggiornata"
git push
```

GitHub Pages pubblica `main` dalla radice (Settings → Pages → Deploy from a
branch → main, /(root)). Dopo un paio di minuti il sito è online.

## Search Console

1. La proprietà è verificata con il meta tag `google-site-verification` nella
   home italiana (lo scrive `tools/build_site.py`: non toglierlo).
2. Dopo ogni pubblicazione con pagine nuove: Search Console → Sitemap →
   invia `https://marcopdev-ctrl-alt-canc.github.io/grafite-sudoku/sitemap.xml`.
   `robots.txt` sta in un sottopercorso e i crawler non lo leggono: la sitemap
   va inviata a mano.
3. Per controllare la sitemap pubblicata:

   ```powershell
   curl.exe -s https://marcopdev-ctrl-alt-canc.github.io/grafite-sudoku/sitemap.xml | Select-String "<loc>" | Measure-Object
   ```

## Rigenerare gli schemi

Vedi README.md, "Aggiungere schemi". I 5 schemi e i PDF della serie 3 di
Pinterest (`data/serie3.json`, `pdf/grafite-sudoku-<slug>.pdf` con gli slug
inglesi della serie) non si rigenerano mai: le pin puntano a quelle URL.

## Cambiare dominio

Tutte le URL delle pagine generate partono da `SITE_URL` in
`tools/build_site.py` (o dalla variabile d'ambiente `SITE_URL`). Con un dominio
proprio: si cambia quella riga, si rilancia il build, si aggiungono a mano gli
indirizzi scritti nei file non generati (`sudoku-da-stampare.html`,
`play/index.html`, `robots.txt`) e si configura il dominio in Settings →
Pages. GitHub reindirizza dal vecchio indirizzo.

## Demo in `play/`

Si aggiorna ricompilando il sorgente della demo e copiando `build/web` in
`play/`:

```powershell
flutter build web --release --base-href "/grafite-sudoku/play/"
Remove-Item -Recurse -Force <repo>\play\*
Copy-Item -Recurse build\web\* <repo>\play\
```

Attenzione: `play/index.html` contiene il riquadro di testo introduttivo
(`#playIntro`, quello che Google legge) e la canonical. Prima di ricompilare,
riporta le stesse righe nel `web/index.html` del sorgente della demo,
altrimenti la build le cancella.

## Link al Play Store

Le pagine generate hanno già l'href completo con la campagna della pagina:
`...&referrer=utm_source%3Dsite%26utm_medium%3Dweb%26utm_campaign%3D<pagina>`.
`assets/play-links.js` fa lo stesso per le pagine scritte a mano
(`data-utm-campaign`) e mostra il banner "sei su Android?". Gli installi per
campagna si vedono in Play Console → Crescita → Acquisizione utenti.

## Informativa privacy

`marcopdev-ctrl-alt-canc.github.io/-grafite-sudoku-privacy` è un repository
separato, linkato dalla Play Console: non si tocca da qui.
