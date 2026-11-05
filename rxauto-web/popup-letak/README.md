# Popup s letákem + stránka Galerie (2026-11-05)

## Popup „Leták Škoda“
- Wix popup, auto-zobrazení na stránce Domů po 2 s, tmavý overlay 65 %, klik na leták → stránka Flexibilní pronájem.
- Desktop: popup 460×650, obrázek 420×594; mobil: obrázek 260×359, popup 280×421 (mobilní rozvržení se ladí zvlášť).
- Leták = CZ verze z Design artefaktu „RX Auto – Monthly Rental Offer“ (project/Main_CZ.dc.html): šablonu převést na statické HTML
  (smyčka {{cars}} → karty, /_blob/<hash> → lokální soubory z artefaktu), vyrenderovat `shot.js` (Playwright, 794×1123 @2x)
  → webp q86 (~240 kB). Bez čísla stránky „1 / 2“.
- Upload do Wixu: soubor nejde nahrát z Chromu (file_upload nepovolí soubory sezení ani Macu, nativní dialog nejde ovládat)
  → soubor uložen do ~/rxauto/web/ na Macu, Erik ho nahrál v editoru přes „Upload Media“.

## Stránka Galerie
- Nová stránka „Galerie“ v menu před Kontaktem, Wix Pro Gallery (mřížka, 5 fotek na řádek, 4:3, přes celou šířku, bez „Load More“).
- 69 vlastních fotek ze složky Media Manageru „real květen fotky“ (karavan Hobby, Audi, BMW 3 Touring…).
