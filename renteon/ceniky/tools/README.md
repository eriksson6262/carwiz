# Nástroje ceníky Carwiz – v3.1 (10.10.2026)
Data se čtou živě z prohlížeče (DiscoverCars API + Renteon $http), uloží se jako data/CZ.json, data/SK.json, data/DC.json
(assemble.py skládá části výstupu javascript_tool – 200k znaků/část, bridge uřízne ~260k).
- CZ.json/SK.json: PL = živý CW-PP z `GET /api/pricelist/listprices/?officeId=-1&pricelistId=1051|351&serviceId=..&from=..&to=..`
  (ceny/den bez DPH), RA = CW-POA availability (1828/352), RULES, FA (fleetAvailability zjednodušeně).
- reprice.py  – vzorky, fit DC = k·R + b, cíle (PRG 3. místo, OSR Budget−10 % a ≤97 % nejlevnějšího, BTS −5 %), faktory.
- build.py    – faktory → období × pásmo (medián vzorků), nové ceny, 21- = 3×7-7, SK Vánoce split, kontrola spojitosti.
- export_xlsx.py – IMPORT (list Ceník + Ceny) a KONTROLA xlsx. TEMPLATE_CZ/TEMPLATE_SK=cesta k exportu Renteonu → převezme hlavičku a pořadí sloupců.
Spuštění: python3 tools/reprice.py && python3 tools/build.py && RUN_DATE=YYYY-MM-DD TEMPLATE_CZ=…export_CZ.xlsx TEMPLATE_SK=…export_SK.xlsx python3 tools/export_xlsx.py
IMPORT obsahuje řádky od TODAY (jako export s "Datum od"), hlavička z posledního exportu.
- 12.10.2026: SK21_DONE=True (SK 21- už ×3 v Renteonu); SK Vánoce – řádky už rozdělené (25.–27./28.–29.12.) se nedělí znovu. Pozor: export_xlsx.py zapisuje out/stage3_samples.json.
- 12.10.2026 (2): nové skupiny Praha – GFAR+LFAR proti premium (P/U/G automaty), PVAR/SVAR proti automatickým vanům, SVMR proti všem vanům; PGAR = IGAR × 1,10 (build.pgar_from_igar). Ostrava/BTS tyto SIPP nemění. DC sběr pro Prahu potřebuje i skupiny PREM/VANA/VANM (data/DC_prem_raw.json).
- 12.10.2026 (3): SVMR = SVAR × 0,95 (DERIVED v build.py); GFAR minimum 65 €/den bez DPH ve všech pásmech (MIN_SIPP).
- 19.10.2026: DC sběr v prohlížeči ukládá rovnou formát reprice (res[L,p,du,cw,comp]) komprimovaný přes tabulku dodavatelů; assemble.py PREFIX výstup.json (části X19P1/3#…#END).
  fallback_data.py = nouzový režim bez Renteonu (PL z posledního importu, pravidla 12.10., R=(DC−b)/k z kalibrace, u=None; reprice nezlevňuje vyzvednutí do 14 dnů).
  konkurence_xlsx.py = KONKURENCE xlsx.
- 19.10.2026 (odpoledne, Erik): CZ minima po slevě E 5 / C 5,5 / I 6,5 (F 13, GFAR 65; SK beze změny) – build.MIN_AFTER_C.
  Praha: levnější smí být jen RENT PLUS a NUCarrentals → cíl = 0,97 × nejlevnější ostatní (PRG_MODE=excl, PRG_UNDER).
  Ostrava: nejlevnější všude, ale ne o moc → cíl = 0,97 × nejlevnější konkurent (OSR_MODE=target; 'flat' = dřívější plošně −10 %).
  Kanály: data/DC.json + data/CT.json (CarTrawler easyJet) + data/WZ.json (Wizz Air); každý kanál vlastní kalibrace, bere se nejnižší faktor (CHANNELS=DC,CT,WZ).
  Komprimovaný sběr (sup + res[L,p,du,cw,comp]) rozbaluje reprice.expand / expand_dc.py. Opraveno: živý PL bez pole 'O' (build/export).
- 19.10.2026 (večer): přidán kanál Rentalcars.com (data/RC.json, stejný komprimovaný formát jako DC; sběr přes /api/search-results v prohlížeči,
  dodavatel = suppliers[depots[route.pickUpDepotId].supplierId], cena vehicle.price.amount EUR celkem s DPH). Aurum/CHECK24 nezařazen (CAPTCHA).
- 20.10.2026 (Erik): Vánoce – blokují se jen vyzvednutí 24.–27.12. (pravidla +500 % CZ / +300 % SK), od 28.12. normálně konkurenceschopné (řádky 28.–29.12. už jsou v Renteonu oddělené).
  Mini MBMR/MDMR/MTMR = cena EDMR na stejné pobočce (build.mini_from_edmr, CZ i SK). Import do Renteonu: CZ CW-PP 1051 + CW Web 1850 + Aurum 1768/1769/1790/1810;
  SK CW-PP 351 + WEB 585 + Aurum 361/778/822 (POST api/pricelist/importFromExcelCheckPrices → importFromExcel, ceny bez DPH).
