// Kód pro všechny stránky (hlavička)
// Tlačítko „Flexibilní pronájem →“ vedle loga: na mobilu bez šipky, aby se vešlo.
import wixWindow from 'wix-window';

$w.onReady(function () {
  if (wixWindow.formFactor === 'Mobile') {
    try { $w('#button11').label = 'Flexibilní pronájem'; } catch (e) { /* tlačítko na stránce není */ }
  }
});
