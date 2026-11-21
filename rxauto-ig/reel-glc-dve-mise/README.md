# Reel „Jedno auto. Dvě mise." – GLC Coupé (21. 11. 2026)

Herní retro-neon parodie: mise A „Ukrást" (noc, policie, mise selhala) vs. mise B „Pronajmout" (západ slunce, klid, mise splněna) → „Nekraď. Pronajmi si."
1080×1920, 30 fps, 15 s, syntetický zvuk (siréna, akordy) generovaný ve skriptu – žádná cizí hudba.

- `python3 render_mise.py preview` / `render` (→ `output_mise/`), potřebuje numpy + Pillow + ffmpeg.
- `src/car_cut.png` = fotka GLC Coupé z webu s odstraněným pozadím (rembg, isnet-general-use).
- Vlastní vizuál, bez log, písma a postav z GTA – jen obecná herní stylizace.

## Verze pro popup na webu (21. 11. 2026)
`VARIANT=web python3 render_mise.py render` → `output_mise/rxauto-dve-mise-web.mp4` (16 s). Rozdíly: bez zmínky o GLC
(obecné pro flotilu), vykání („Vyberte si“, „Jen vy a cesta“), závěr = webový banner „Nekraďte. Pronajměte si.“
v barvách západu slunce s tlačítkem „Prohlédnout flotilu“. Bez `VARIANT` vzniká původní Reel pro IG.
