// Flotila (/vypis-auta) – úryvek vložený na začátek $w.onReady v kódu stránky (public/pages/ie56l.js).
// Štítek na kartě (#statusBox / #statusText, v editoru navázaný na pole palivo) ukazuje modelový rok z pole modelovyRok.
// Napojení na CMS v editoru nejde přepojit (panel se nenačte), proto se text přepíše kódem; bez roku se štítek skryje.
$w('#carRepeater').onItemReady(($item, itemData) => {
	const nastavRok = () => {
		const rok = itemData.modelovyRok;
		if (rok) { $item('#statusText').text = String(rok); $item('#statusBox').show(); }
		else { $item('#statusBox').hide(); }
	};
	nastavRok();
	setTimeout(nastavRok, 0);
});
