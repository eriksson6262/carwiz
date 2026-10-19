# Ceníky Carwiz CW-PP (Praha + Ostrava, Bratislava)

Přeceňování CW-PP podle konkurence (DiscoverCars, CarTrawler easyJet + Wizz Air) a obsazenosti flotily v Renteonu.
Výstupem jsou soubory k ručnímu importu do Renteonu – nic se do Renteonu nezapisuje automaticky.

- Spouští se naplánovanou úlohou „Ceníky Carwiz – mapování cen“ (pondělí ráno, pátek odpoledne) na Mac mini.
- Pracovní složka na Macu: `~/Downloads/Claude pracovní/Ceníky/` (IMPORT_*, KONTROLA_*, KONKURENCE_*),
  nástroje i surová data běhu v `Ceníky/_nastroje/` (`nastroje_*.tar.gz`, `dc_*.json`, `ct_*.json`, `wizz_*.json`, `renteon_*.json`).
- Výchozí šablona importu = poslední export z Renteonu v `Ceníky/_exporty/`.
- Podrobný postup a pravidla: `tools/README.md`; cíle a minima jsou okomentované přímo v `tools/reprice.py` a `tools/build.py`.

Spuštění (data v `data/`, výstupy v `out/` – obojí se necommituje):

```
python3 tools/reprice.py && python3 tools/build.py && \
RUN_DATE=YYYY-MM-DD TEMPLATE_CZ=…/export_CW-PP_CZ.xlsx TEMPLATE_SK=…/export_CW-PP_SK.xlsx python3 tools/export_xlsx.py
```

Renteon se čte jen přes přihlášenou relaci v prohlížeči (`collect_renteon.js` přes angular `$http`) – žádná hesla v kódu.
