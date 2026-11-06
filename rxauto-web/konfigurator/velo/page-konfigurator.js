// Konfigurátor pronájmu – kód stránky „Konfigurátor“ (Wix page code)
// Na stránce je vlastní prvek (Custom Element, tag rx-konfigurator) s ID #rxKonfigurator.
// Volitelně ?vuz=Kodiaq v URL předvybere vůz.
import wixLocationFrontend from 'wix-location-frontend';
import { getKonfigurace, overDostupnost, odeslatPoptavku } from 'backend/konfigurator.web';

$w.onReady(async function () {
  const el = $w('#rxKonfigurator');
  el.on('check', async (e) => {
    const q = e.detail;
    let r;
    try { r = await overDostupnost(q); } catch (err) { r = { stav: 'neovereno', text: 'Dostupnost se teď nepodařilo ověřit automaticky – ověříme ji ručně.' }; }
    el.setAttribute('availability', JSON.stringify({ ...r, reqId: q.reqId }));
  });
  el.on('submit', async (e) => {
    let r;
    try { r = await odeslatPoptavku(e.detail); } catch (err) { r = { ok: false, chyba: 'Odeslání se nepodařilo. Zkuste to prosím znovu nebo nám napište na info@rxauto.cz.' }; }
    el.setAttribute('result', JSON.stringify({ ...r, t: Date.now() }));
  });
  const cfg = await getKonfigurace();
  const q = wixLocationFrontend.query || {};
  if (q.vuz) cfg.preselect = q.vuz;
  el.setAttribute('config', JSON.stringify(cfg));
});
