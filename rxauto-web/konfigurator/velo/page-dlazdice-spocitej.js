// Dlaždice vozů – tlačítko #button1 v opakovači #carRepeater:
//  - Flotila (ie56l.js): vloženo do existujícího onItemReady (za nastavRok); bez konfiguratorVuz zůstává „Poptat“.
//  - Flexibilní pronájem (q27nr.js): nový onItemReady + po načtení #dataset1 ještě forEachItem (600 ms).
//    Na této stránce bylo tlačítko „Více“ napojené na dataset (odkaz na Auta (Title)) – napojení v editoru zrušeno,
//    jinak dataset přepisoval odkaz z kódu. Bez konfiguratorVuz → „Více“ s odkazem na detail (pole link-auta-1-title).
$w('#carRepeater').onItemReady(($item, itemData) => {
  const nastavOdkaz = () => {
    const b = $item('#button1');
    if (!itemData.konfiguratorVuz) { /* q27nr: */ b.label = 'Více'; b.link = itemData['link-auta-1-title']; b.target = '_self'; return; }
    b.label = 'Spočítej';
    b.link = '/konfigurator?vuz=' + encodeURIComponent(itemData.konfiguratorVuz);
    b.target = '_self';
  };
  nastavOdkaz();
  setTimeout(nastavOdkaz, 0);
  setTimeout(nastavOdkaz, 400);   // q27nr
  setTimeout(nastavOdkaz, 1500);  // q27nr
});
