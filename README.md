# Grafite Sudoku — sito e demo web

Repository pubblico con la pagina di presentazione di **Grafite Sudoku** e una
demo giocabile nel browser, pensati per portare pubblico verso la scheda
Google Play dell'app.

Il codice sorgente Dart del gioco **non** vive qui: questo repo contiene solo
la pagina statica e l'output già compilato (`flutter build web`) della demo.
Il sorgente della demo resta sul PC, in una cartella separata
(`grafite_sudoku_web_demo`, a fianco del progetto principale `sudoku_test`).

## Struttura

```
index.html      → pagina di presentazione (root, così GitHub Pages la serve
                   direttamente senza configurazioni particolari)
assets/         → icona, immagine di anteprima social, illustrazioni avatar
play/           → qui va copiato l'output di `flutter build web` della demo
                   (vuoto finché non lo generi la prima volta, vedi sotto)
PUBBLICAZIONE.md → guida passo-passo per la messa online e per ogni
                   aggiornamento successivo
```

## Cosa contiene la demo (e cosa no)

Inclusi: griglia sudoku giocabile, tutte le difficoltà, matite/note, i 5 temi
carta, livelli/XP e titoli, Time Attack, sfide tra amici (codice
condivisibile).

Esclusi apposta, per tenere la demo leggera e per lasciare un motivo in più
per scaricare l'app vera: i 30 trofei, gli avatar da sbloccare e
l'Accademia (le lezioni guidate di tecniche di risoluzione) — restano
un'esclusiva dell'app Android (la sezione "Nell'app completa" della pagina
li mostra come anticipazione). In tutti e tre i casi i punti d'accesso sono
stati nascosti nel codice, non cancellata la logica sottostante — solo il
modo per raggiungerla.

La demo salva i progressi solo nel browser di chi gioca (stesso meccanismo di
`shared_preferences` dell'app, ma è uno spazio di salvataggio separato: non si
sincronizza con l'app Android).

## Link utili

- Informativa privacy (repo separato, non toccarlo): https://marcopdev-ctrl-alt-canc.github.io/-grafite-sudoku-privacy/
- Scheda Google Play: https://play.google.com/store/apps/details?id=com.grafitesoft.grafitesudoku — definita in un solo punto, `assets/play-links.js` (`PLAY_STORE_URL`), da cui la leggono sia i pulsanti "Scarica su Google Play" sia il banner per chi arriva da Android; vedi `PUBBLICAZIONE.md` punto 5 per come sostituirla con un link tracciato da Play Console.
- Contatti: grafitesoft@gmail.com

## Banner "vieni da Android?"

Chi apre il sito (o la demo giocabile) da un browser Android vede un
banner richiudibile in cima con un pulsante verso la scheda Play Store —
chi è già sul telefono è a un tap dall'installare l'app vera, niente
motivo di trattenerlo sulla demo. Non è un redirect forzato: chi lo chiude
non lo rivede più su quel browser. Dettagli in `PUBBLICAZIONE.md`, punto 7.

## Aggiornare la demo in futuro

Vedi `PUBBLICAZIONE.md` — in breve: si modifica il sorgente in
`grafite_sudoku_web_demo`, si rilancia `flutter build web`, si ricopia
l'output in `play/`, si fa commit e push.
