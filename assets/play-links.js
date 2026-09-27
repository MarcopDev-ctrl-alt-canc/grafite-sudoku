// Un solo posto da aggiornare per il link alla scheda Google Play — sia
// per i pulsanti "Scarica su Google Play" di questa pagina, sia per il
// banner mostrato a chi arriva da telefono Android (qui e nella demo
// giocabile in play/, che importa questo stesso file con un percorso
// relativo).
//
// Tracciamento per sorgente (26-27/09/2026, richiesta del progetto
// Marketing): ogni punto del sito da cui si può arrivare alla scheda Play
// aggiunge il proprio utm_source/utm_campaign, così Play Console (Crescita
// → Acquisizione utenti) dice davvero da dove arrivano gli installi, non
// solo "dal sito" in generale. Un elemento `.play-store-link` dichiara la
// sua sorgente con `data-utm-source`/`data-utm-campaign` nell'HTML — se non
// li dichiara, prende il default sotto (sorgente "sito", campagna "home").
// Un solo posto da aggiornare quando arriverà un link Play Console vero
// (vedi PUBBLICAZIONE.md): la costante `PLAY_STORE_BASE_URL` qui sotto.
const PLAY_STORE_BASE_URL = "https://play.google.com/store/apps/details?id=com.grafitesoft.grafitesudoku";

function buildPlayStoreUrl(source, campaign) {
  if (!source) return PLAY_STORE_BASE_URL;
  var params = new URLSearchParams({ utm_source: source, utm_campaign: campaign || 'link' });
  return PLAY_STORE_BASE_URL + '&' + params.toString();
}

// Retro-compatibilità: qualunque punto del sito non ancora aggiornato con
// i data-attribute (o che importa questo file aspettandosi la vecchia
// costante) continua a funzionare, con sorgente "sito"/campagna "home".
const PLAY_STORE_URL = buildPlayStoreUrl('sito', 'home');

(function () {
  document.querySelectorAll('.play-store-link').forEach(function (el) {
    var source = el.getAttribute('data-utm-source');
    var campaign = el.getAttribute('data-utm-campaign');
    el.href = source ? buildPlayStoreUrl(source, campaign) : PLAY_STORE_URL;
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
    // L'href del link dentro il banner è già stato impostato dal forEach
    // sopra, in base ai suoi data-utm-source/data-utm-campaign — qui si
    // decide solo se il banner va mostrato.
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
