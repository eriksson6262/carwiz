// Flexibilní pronájem (/dlouhodoby-pronajem) – kód stránky (Wix page code, q27nr.js)
// - výpis „Auta v nabídce“ (opakovač #carRepeater, dataset #dataset1): dataset v editoru zobrazuje jen omezený
//   počet položek – v kódu ho navýšíme, aby se ukázaly všechny vozy s landingPage = ano
// - tlačítko #button8 „Spočítat cenu“ (prostřední sloupec mezi fotkami, odkaz na /konfigurator):
//   výrazný styl, šipka, jemné pulzování a hover efekt, aby bylo jasné, že jde o tlačítko
import wixAnimations from 'wix-animations';

$w.onReady(function () {
  $w('#dataset1').onReady(() => {
    $w('#dataset1').setPageSize(30);
  });

  const btn = $w('#button8');
  btn.label = 'Spočítat cenu →';
  const zakladni = { backgroundColor: '#000000', color: '#FFFFFF', borderColor: '#000000' };
  const hover = { backgroundColor: '#FFFFFF', color: '#000000', borderColor: '#000000' };
  const nastav = (s) => { Object.keys(s).forEach((k) => { btn.style[k] = s[k]; }); };
  btn.style.borderWidth = '2px';
  btn.style.borderRadius = '26px';
  nastav(zakladni);

  const puls = wixAnimations.timeline({ repeat: -1, yoyo: true });
  puls.add(btn, { scale: 1.07, duration: 900, easing: 'easeInOutSine' });
  puls.play();

  btn.onMouseIn(() => { puls.pause(); nastav(hover); });
  btn.onMouseOut(() => { nastav(zakladni); puls.play(); });
});
