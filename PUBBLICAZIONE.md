# Pubblicazione su GitHub Pages — guida passo passo

Comandi pensati per PowerShell su Windows. Presuppongo che tu riceva due
cartelle da Claude:

- `grafite-sudoku` (questa cartella: sito + spazio per la demo compilata) →
  da mettere sul repository GitHub pubblico
- `grafite_sudoku_web_demo` (sorgente Flutter della sola demo web) → resta
  **solo sul tuo PC**, non va su GitHub

## 1. Creare il repository su GitHub

Sul sito github.com, con il tuo account `marcopdev-ctrl-alt-canc`:

1. New repository → nome **`grafite-sudoku`** → Public → NON aggiungere
   README/.gitignore/licenza (li portiamo già noi) → Create repository.

(In alternativa, se hai GitHub CLI installato: `gh repo create grafite-sudoku --public --source=. --remote=origin`.)

## 2. Primo push del sito

Apri PowerShell nella cartella `grafite-sudoku` che hai ricevuto e lancia:

```powershell
cd percorso\della\cartella\grafite-sudoku
git init
git add -A
git commit -m "Sito e demo web di Grafite Sudoku"
git branch -M main
git remote add origin https://github.com/marcopdev-ctrl-alt-canc/grafite-sudoku.git
git push -u origin main
```

A questo punto su GitHub c'è già la pagina di presentazione, ma la cartella
`play/` è vuota: il pulsante "Gioca ora nel browser" non funziona ancora.
Si sistema al punto 3.

## 3. Compilare la demo e pubblicarla in `play/`

Nella cartella `grafite_sudoku_web_demo` (il sorgente Flutter della demo):

```powershell
cd percorso\della\cartella\grafite_sudoku_web_demo
flutter pub get
flutter build web --release --base-href "/grafite-sudoku/play/"
```

Poi copia il contenuto generato dentro il repository del sito (sovrascrivendo
il contenuto attuale di `play/`):

```powershell
Remove-Item -Recurse -Force percorso\della\cartella\grafite-sudoku\play\*
Copy-Item -Recurse build\web\* percorso\della\cartella\grafite-sudoku\play\
```

E pubblica:

```powershell
cd percorso\della\cartella\grafite-sudoku
git add -A
git commit -m "Aggiunge la demo web compilata"
git push
```

## 4. Attivare GitHub Pages

Sul repository, su GitHub: Settings → Pages → sotto "Build and deployment",
Source: **Deploy from a branch** → Branch: **main**, cartella **/(root)** →
Save.

Dopo un minuto o due il sito è live su:

**https://marcopdev-ctrl-alt-canc.github.io/grafite-sudoku/**

## 5. Collegare la scheda Google Play

Fatto: la scheda vera
(`https://play.google.com/store/apps/details?id=com.grafitesoft.grafitesudoku`)
è già collegata ovunque — i due pulsanti "Scarica su Google Play" in
`index.html`, il banner per chi arriva da Android (punto 7) e lo stesso
banner dentro la demo giocabile. **Non è più scritta a mano in ogni punto**:
tutti la leggono da un'unica riga in `assets/play-links.js`
(`PLAY_STORE_URL = "..."`). Se in futuro vuoi cambiarla, modifica solo
quella riga, poi:

```powershell
git add assets\play-links.js
git commit -m "Aggiorna il link alla scheda Google Play"
git push
```

**Consigliato appena hai un momento**: quel link oggi non porta nessun
tracciamento — un `?utm_source=...` scritto a mano sull'URL della Play
Store, come quello che avevi inizialmente, **Google Play lo ignora**: non
è così che funziona l'attribuzione lì. Per sapere davvero quanti installi
arrivano da questo sito, genera il link giusto da Play Console: **Crescita
→ Acquisizione utenti → Acquisizione tramite URL personalizzati → Crea URL
per campagna personalizzata** — dai un nome tipo "sito-github-pages",
sorgente "sito web", e Play Console ti dà un link con un parametro
`referrer=...` che quello sì viene letto. Incolla quel link al posto del
valore in `PLAY_STORE_URL` (dentro `assets/play-links.js`) e da quel
momento avrai un numero vero in Play Console, non solo un click count.

## 6. Aggiornare la demo in futuro

Ogni volta che vuoi aggiornare la demo (nuova funzione, correzione), ripeti
solo il punto 3: build in `grafite_sudoku_web_demo`, copia in `play/`, commit,
push. La pagina di presentazione (`index.html`) puoi modificarla e pubblicarla
in qualsiasi momento allo stesso modo, senza toccare la demo.

## 7. Banner "vieni da Android?"

Chi apre il sito (o la demo in `play/`) da un browser Android vede comparire
in cima un piccolo banner richiudibile: "Sei su Android? L'app vera ha
salvataggio permanente, trofei e avatar da sbloccare" con un pulsante
"Installa" verso la scheda Play Store. L'idea: chi è già sul telefono è a
un tap dall'installare l'app vera, ha poco senso tenerlo su una demo
ridotta pensata soprattutto per chi è al computer. Non è un redirect
forzato — chi non è interessato lo chiude con la ✕ e non lo rivede più
(fino a quando non cancella i dati del sito da quel browser). Su iPhone o
computer il banner non compare mai, dato che l'app oggi è solo su Android:
mostrarlo lì manderebbe verso un link inutile.

La logica vive tutta in `assets/play-links.js`, condivisa fra `index.html`
e la demo — cambiare il testo del banner si fa in due punti (l'HTML del
banner è duplicato in `index.html` e in `grafite_sudoku_web_demo/web/index.html`,
dato che sono due pagine HTML distinte), ma il link e la logica di
rilevamento/promemoria restano in un solo file.

## Nota sul repository della privacy policy

`marcopdev-ctrl-alt-canc.github.io/-grafite-sudoku-privacy` resta un
repository separato e non va toccato da questa procedura: è quello linkato
(probabilmente) nella Play Console, meglio non rischiare di romperlo.
