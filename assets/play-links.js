// Un solo posto da aggiornare per il link alla scheda Google Play — sia
// per i pulsanti "Scarica su Google Play" di questa pagina, sia per il
// banner mostrato a chi arriva da telefono Android (qui e nella demo
// giocabile in play/, che importa questo stesso file con un percorso
// relativo). Quando avrai un link con tracciamento vero — generato da
// Play Console, Crescita → Acquisizione utenti → URL per campagna
// personalizzata, vedi PUBBLICAZIONE.md — sostituiscilo qui sotto:
// aggiornare questa singola riga basta ovunque, non serve più toccare
// index.html a mano.
const PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.grafitesoft.grafitesudoku";

(function () {
  document.querySelectorAll('.play-store-link').forEach(function (el) {
    el.href = PLAY_STORE_URL;
  });

  // Banner "vieni da Android?" (03/09/2026, richiesta esplicita
  // dell'utente): mostrato solo a chi apre il sito da un browser Android
  // (rilevato dallo User-Agent — tecnica standard per questo scopo
  // specifico, nonostante i limiti generali dello User-Agent sniffing).
  // Chi è già sul telefono è a un tap dall'installare l'app vera: poco
  // senso trattenerlo in una landing/demo pensata soprattutto per chi è
  // al computer. Non forza nulla — nessun redirect automatico, scelta
  // esplicita dell'utente finale (Marco) durante la conversazione con
  // Claude — solo un banner in cima, richiudibile, che poi resta chiuso
  // (salvato nel browser di chi lo chiude) finché non cancella i dati
  // del sito.
  var KEY = 'grafite_android_banner_dismissed';
  var isAndroid = /Android/i.test(navigator.userAgent || '');
  var dismissed = false;
  try {
    dismissed = localStorage.getItem(KEY) === '1';
  } catch (e) {
    // Storage non disponibile (modalità privata restrittiva, ecc.): il
    // banner si comporta come se non fosse mai stato chiuso, nessun
    // errore bloccante.
  }

  var banner = document.getElementById('androidAppBanner');
  if (banner) {
    var link = banner.querySelector('.play-store-link');
    if (link) link.href = PLAY_STORE_URL;
    if (isAndroid && !dismissed) {
      banner.style.display = 'flex';
    }
  }

  window.dismissAndroidBanner = function () {
    if (banner) banner.style.display = 'none';
    try {
      localStorage.setItem(KEY, '1');
    } catch (e) {
      // Idem: se non si può salvare, il banner tornerà al prossimo giro,
      // ma intanto si chiude comunque per chi l'ha appena chiuso.
    }
  };
})();
