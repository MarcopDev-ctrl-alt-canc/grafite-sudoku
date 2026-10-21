// Link alla scheda Google Play, per tutto il sito e per la demo in play/.
//
// Play Console (Crescita → Acquisizione utenti) attribuisce gli installi solo
// tramite il parametro `referrer`: ogni pulsante `.play-store-link` porta la
// campagna della sua pagina in `data-utm-campaign` (le pagine generate da
// tools/build_site.py hanno già l'href completo, che funziona anche senza
// JavaScript). Le pagine più vecchie dichiarano anche `data-utm-source`: la
// sorgente finisce davanti alla campagna, così resta distinguibile.
var PLAY_STORE_BASE_URL = "https://play.google.com/store/apps/details?id=com.grafitesoft.grafitesudoku";

function buildPlayStoreUrl(source, campaign) {
  var name = [source, campaign].filter(Boolean).join('-') || 'home';
  var ref = 'utm_source=site&utm_medium=web&utm_campaign=' + name;
  return PLAY_STORE_BASE_URL + '&referrer=' + encodeURIComponent(ref);
}

// Usata da pagine che leggono direttamente la costante (demo in play/).
var PLAY_STORE_URL = buildPlayStoreUrl(null, 'home');

(function () {
  document.querySelectorAll('.play-store-link').forEach(function (el) {
    var source = el.getAttribute('data-utm-source');
    var campaign = el.getAttribute('data-utm-campaign');
    if (source || campaign) el.href = buildPlayStoreUrl(source, campaign);
  });

  // Banner "sei su Android?": solo su browser Android, richiudibile; la
  // chiusura resta salvata in questo browser.
  var KEY = 'grafite_android_banner_dismissed';
  var isAndroid = /Android/i.test(navigator.userAgent || '');
  var dismissed = false;
  try {
    dismissed = localStorage.getItem(KEY) === '1';
  } catch (e) {
    // Storage non disponibile: il banner si comporta come mai chiuso.
  }
  var banner = document.getElementById('androidAppBanner');
  if (banner && isAndroid && !dismissed) banner.style.display = 'flex';

  window.dismissAndroidBanner = function () {
    if (banner) banner.style.display = 'none';
    try {
      localStorage.setItem(KEY, '1');
    } catch (e) {
      // Non salvabile: tornerà alla prossima visita.
    }
  };
})();
