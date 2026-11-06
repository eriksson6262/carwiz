"""Vytvoří ceník konfigurátoru pronájmu (rxauto.cz) – cenik_konfigurator.xlsx.
Ceny a pravidla zadal Erik 6. 11. 2026; základní měsíční ceny = nabídka na webu (CMS Auta)."""
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1] if len(sys.argv) > 1 else "cenik_konfigurator.xlsx"
F = "Arial"
H = Font(name=F, bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="0B0F17")
T = Font(name=F, size=14, bold=True); N = Font(name=F); B = Font(name=F, bold=True)
INP = Font(name=F, color="0000FF"); NOTE = Font(name=F, italic=True, color="666666", size=9)
Y = PatternFill("solid", fgColor="FFFF00"); THIN = Border(*(Side(style="thin", color="BBBBBB"),) * 4)
KC = '#,##0 "Kč";-#,##0 "Kč";"-"'; PCT = "0%"

wb = Workbook()

def hdr(ws, row, cols, widths):
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        x = ws.cell(row, i, c); x.font = H; x.fill = HF; x.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[x.column_letter].width = w
    ws.row_dimensions[row].height = 30

# ---------- Návod ----------
ws = wb.active; ws.title = "Návod"
ws["A1"] = "Ceník konfigurátoru pronájmu – rxauto.cz"; ws["A1"].font = T
rows = [
    "Z tohoto souboru se plní konfigurátor na webu. Po úpravě ho pošlete Claudovi, nahraje ceny do webu (CMS).",
    "Modré písmo = hodnoty, které upravujete. Žluté pole = zatím chybí, je potřeba doplnit.",
    "Černé písmo = vzorce, neměnit.",
    "Všechny ceny jsou v Kč bez DPH.",
    "List Vozy: jeden řádek = jeden model na webu. SIPP = kategorie v Renteonu, podle ní se ověřuje dostupnost.",
    "Pobočky: ano = vůz je na pobočce v nabídce. Když na zvolené pobočce volný není, web nabídne vůz z jiné pobočky s přistavením po dohodě.",
    "List Nájezd: příplatek za každých dalších 1 000 km měsíčně nad nájezd v ceně.",
    "List Služby: druhý řidič, spoluúčast. Příplatky za spoluúčast 5 % a 0 % se zadávají po kategoriích (list Spoluúčast).",
    "List Kalkulace: vyzkoušení výpočtu – stejný postup počítá web.",
]
for i, t in enumerate(rows, 3):
    ws.cell(i, 1, t).font = N
ws.column_dimensions["A"].width = 120

# ---------- Parametry ----------
wp = wb.create_sheet("Parametry")
wp["A1"] = "Obecné parametry"; wp["A1"].font = T
hdr(wp, 3, ["Parametr", "Hodnota", "Poznámka"], [44, 14, 70])
params = [
    ("Dní v měsíci pro přepočet ceny", 30, "Cena za den = měsíční cena / tato hodnota (předpoklad, upravte dle potřeby)."),
    ("Minimální délka pronájmu (dny)", 30, "Předpoklad – flexibilní pronájem od 1 měsíce. Doplňte/upravte."),
    ("Nájezd v ceně (km / měsíc)", 2500, "Standard dle nabídky; u modelu lze přepsat v listu Vozy."),
    ("Krok navýšení nájezdu (km)", 1000, "Zadal Erik 6. 11. 2026."),
    ("Cena za krok (Kč / měsíc bez DPH)", 6000, "Zadal Erik 6. 11. 2026: každých 1 000 km = 6 000 Kč bez DPH."),
    ("Druhý řidič – cena za den (Kč)", 120, "Zadal Erik 6. 11. 2026."),
    ("Druhý řidič zdarma od (dní pronájmu)", 31, "Zadal Erik: u pronájmu nad 30 dní zdarma."),
    ("DPH", 0.21, "Pro zobrazení ceny s DPH."),
]
for i, (a, b, c) in enumerate(params, 4):
    wp.cell(i, 1, a).font = N; x = wp.cell(i, 2, b); x.font = INP; wp.cell(i, 3, c).font = NOTE
    x.number_format = PCT if isinstance(b, float) else ("#,##0" if b >= 1000 else "0")
    for cc in range(1, 4): wp.cell(i, cc).border = THIN
P = {k: f"Parametry!$B${i}" for i, (k, _, _) in enumerate(params, 4)}
P_DNI, P_MIN, P_KM, P_KROK, P_CENAKROK, P_RIDIC, P_RIDIC_ZDARMA, P_DPH = (P[k] for k, _, _ in params)

# ---------- Spoluúčast ----------
wsp = wb.create_sheet("Spoluúčast")
wsp["A1"] = "Spoluúčast podle kategorie vozu"; wsp["A1"].font = T
wsp["A2"] = "Standard v ceně: 10 %, min. 10 000 Kč. Příplatky za 5 % (min. 5 000 Kč) a 0 % doplňte po kategoriích (Erik: nadefinujeme později)."; wsp["A2"].font = NOTE
hdr(wsp, 4, ["Kategorie", "Popis", "Standard (v ceně)", "Příplatek 5 % / měsíc", "Příplatek 0 % / měsíc"], [12, 40, 22, 22, 22])
cats = [("A", "Malé a kompaktní (Fabia, Kamiq)"), ("B", "Střední (Karoq, Octavia, 3008)"), ("C", "Vyšší (Superb, Kodiaq, Tonale)"), ("P", "Prémiové (Mercedes GLE, CLE)"), ("D", "Dodávky (Boxer)"), ("O", "Obytné vozy")]
for i, (k, d) in enumerate(cats, 5):
    wsp.cell(i, 1, k).font = INP; wsp.cell(i, 2, d).font = INP; wsp.cell(i, 3, "10 %, min. 10 000 Kč").font = N
    for cc in (4, 5):
        x = wsp.cell(i, cc); x.fill = Y; x.font = INP; x.number_format = KC
    for cc in range(1, 6): wsp.cell(i, cc).border = THIN
wsp.cell(5, 4).comment = Comment("Doplňte příplatek v Kč bez DPH za měsíc. Prázdné = web nabídne volbu „na dotaz“.", "Claude")

# ---------- Vozy ----------
wv = wb.create_sheet("Vozy")
wv["A1"] = "Vozy v konfigurátoru"; wv["A1"].font = T
cols = ["Model na webu", "Značka", "Cena / měsíc bez DPH", "Nájezd v ceně (km/měs.)", "Kategorie spoluúčasti",
        "SIPP Renteon CZ", "SIPP Renteon SK", "Praha", "Ostrava", "Bratislava", "Max. doba (měsíce)", "Aktivní", "Poznámka (interní)", "Text pro web", "Servis v ceně", "Skupina", "Modelový rok", "Neomezený nájezd – příplatek / měs."]
hdr(wv, 3, cols, [30, 14, 16, 14, 12, 12, 12, 9, 9, 11, 12, 9, 46, 46, 11, 14, 11, 16])
cars = [
    ("Fabia Monte Carlo", "Škoda", 9900, 2500, "A", "EDAR", "EDAR", "ano", "ano", "ne", 6, "ano", "", "", "ano", "Osobní auta", None, None),
    ("Kamiq Selection", "Škoda", 10900, 2500, "A", "CFAR", "CFAR", "ano", "ano", "ano", 6, "ano", "", "", "ano", "Osobní auta", None, None),
    ("Kamiq Monte Carlo", "Škoda", 11900, 2500, "A", "CFAR", "CFAR", "ano", "ano", "ano", 6, "ano", "Renteon nerozlišuje Kamiq Selection a MC (obojí CFAR).", "", "ano", "Osobní auta", None, None),
    ("Karoq Sportline", "Škoda", 12900, 2500, "B", "IGAR", "IGAR", "ano", "ano", "ano", 6, "ano", "IGAR v CZ sdílí s Peugeot 3008.", "", "ano", "Osobní auta", None, None),
    ("Octavia", "Škoda", 12900, 2500, "B", "IDAR", "IDAR", "ano", "ne", "ne", 6, "ano", "", "", "ano", "Osobní auta", None, None),
    ("Octavia Combi Sportline", "Škoda", 13900, 2500, "B", "IWAR", "IWAR", "ano", "ano", "ano", 6, "ano", "", "", "ano", "Osobní auta", None, None),
    ("Superb Sportline", "Škoda", 14900, 2500, "C", "FDAR", "FDAR", "ano", "ne", "ne", 6, "ano", "", "", "ano", "Osobní auta", None, None),
    ("Superb Combi Sportline", "Škoda", 14900, 2500, "C", "FWAR", "FWAR", "ano", "ano", "ne", 6, "ano", "", "", "ano", "Osobní auta", None, None),
    ("Superb Combi L&K", "Škoda", 16900, 2500, "C", "FWAR", "FWAR", "ano", "ano", "ne", 6, "ano", "Renteon nerozlišuje Sportline a L&K (obojí FWAR).", "", "ano", "Osobní auta", None, None),
    ("Kodiaq Sportline", "Škoda", 16900, 2500, "C", "FFAR", "FFAR", "ano", "ano", "ano", 6, "ano", "", "", "ano", "Osobní auta", None, None),
    ("Kodiaq RS 4×4", "Škoda", 18900, 2500, "C", "FFAR", "FFAR", "ano", "ano", "ano", 6, "ano", "FFAR = všechny Kodiaqy (+ Peugeot 5008).", "", "ano", "Osobní auta", None, None),
    ("Alfa Romeo Tonale PHEV Q4", "Alfa Romeo", 19900, 2500, "C", "", "", "ano", "ne", "ne", "", "ano", "Není v Renteonu – dostupnost ověříme ručně.", "Plug-in hybrid 4×4, bez omezení doby pronájmu, nabíjení zdarma. Servis není v ceně.", "ne", "Osobní auta", 2024, None),
    ("Peugeot 3008", "Peugeot", 13900, 2500, "B", "IGAR", "CFAR", "ano", "ano", "ano", "", "ano", "IGAR v CZ sdílí s Karoq.", "Bez omezení doby pronájmu. Možnost neomezeného nájezdu za pevný příplatek.", "ano", "Osobní auta", 2022, 6000),
    ("Mercedes-Benz GLE", "Mercedes-Benz", None, 2500, "P", "GFAR", "", "ano", "ne", "ne", "", "ano", "Cena zatím na dotaz – doplnit.", "Prémiové SUV 4MATIC. Cenu pošleme v nabídce.", "ano", "Osobní auta", 2025, None),
    ("Mercedes-Benz CLE 300 4MATIC", "Mercedes-Benz", None, 2500, "P", "UEAR", "", "ano", "ne", "ne", "", "ano", "Cena zatím na dotaz – doplnit (týdenní nabídka 9 990 Kč/týden vč. DPH).", "Kupé s pohonem 4MATIC. Cenu pošleme v nabídce.", "ano", "Osobní auta", 2025, None),
    ("Peugeot Boxer 3500 L3H2", "Peugeot", 20700, 2500, "D", "FKMR", "", "ano", "ne", "ne", "", "ano", "690 Kč/den bez DPH × 30 (dle webu „od 690 Kč/den“) – ověřit.", "Dodávka L3H2, manuál, 3 místa.", "ano", "Dodávky", None, None),
    ("Roller Team Livingstone 2 Sport", "Fiat", None, 2500, "O", "", "", "ano", "ne", "ne", "", "ano", "Není v Renteonu – dostupnost ověříme ručně. Cena doplnit.", "Obytná dodávka 5,99 m, 4 místa ke spaní. Cenu pošleme v nabídce.", "ano", "Obytné vozy", None, None),
    ("Hobby Optima T65 HFL Premium", "Fiat", None, 2500, "O", "", "", "ano", "ne", "ne", "", "ano", "Není v Renteonu – dostupnost ověříme ručně. Cena doplnit.", "Obytný vůz 7,02 m, 4 místa ke spaní. Cenu pošleme v nabídce.", "ano", "Obytné vozy", None, None),
]
r0 = 4
for i, c in enumerate(cars, r0):
    for j, v in enumerate(c, 1):
        x = wv.cell(i, j, v); x.font = NOTE if j == 13 else INP; x.border = THIN
        if j == 3: x.number_format = KC
        if j == 4: x.number_format = "#,##0"
        if j == 18: x.number_format = KC
    if c[2] is None:
        wv.cell(i, 3).fill = Y; wv.cell(i, 3).comment = Comment("Prázdné = web ukáže „cena na dotaz“.", "Claude")
LAST = r0 + len(cars) - 1
wv.cell(LAST + 2, 1, "Zdroj cen: nabídka na rxauto.cz (CMS Auta, CZ ceny Kč/měsíc bez DPH dle IG nabídky 27. 10. 2026). SIPP podle flotily v Renteonu 6. 11. 2026.").font = NOTE
dv = DataValidation(type="list", formula1='"ano,ne"', allow_blank=True); wv.add_data_validation(dv)
dv.add(f"H{r0}:J{LAST}"); dv.add(f"L{r0}:L{LAST}"); dv.add(f"O{r0}:O{LAST}")
dvk = DataValidation(type="list", formula1="=Spoluúčast!$A$5:$A$10", allow_blank=True); wv.add_data_validation(dvk); dvk.add(f"E{r0}:E{LAST}")
wv.freeze_panes = "B4"

# ---------- Nájezd ----------
wn = wb.create_sheet("Nájezd")
wn["A1"] = "Nabízené nájezdy (km / měsíc)"; wn["A1"].font = T
wn["A2"] = "Příplatek = (nájezd − nájezd v ceně) / krok × cena za kroku. Nájezdy upravte v modrém sloupci."; wn["A2"].font = NOTE
hdr(wn, 4, ["Nájezd (km / měsíc)", "Příplatek / měsíc bez DPH"], [22, 26])
for i, km in enumerate([2500, 3500, 4500, 5500, 6500], 5):
    x = wn.cell(i, 1, km); x.font = INP; x.number_format = "#,##0"
    y = wn.cell(i, 2, f"=MAX(0,(A{i}-{P_KM})/{P_KROK})*{P_CENAKROK}"); y.font = N; y.number_format = KC
    for cc in (1, 2): wn.cell(i, cc).border = THIN

# ---------- Kalkulace ----------
wk = wb.create_sheet("Kalkulace")
wk["A1"] = "Zkušební kalkulace (stejný výpočet jako web)"; wk["A1"].font = T
hdr(wk, 3, ["Vstup / položka", "Hodnota", "Poznámka"], [36, 22, 60])
inputs = [("Model", "Kodiaq RS 4×4"), ("Počet dní pronájmu", 60), ("Nájezd (km / měsíc)", 3500),
          ("Druhý řidič (ano/ne)", "ano"), ("Spoluúčast (10 % / 5 % / 0 %)", "10 %")]
for i, (a, b) in enumerate(inputs, 4):
    wk.cell(i, 1, a).font = B; x = wk.cell(i, 2, b); x.font = INP; x.fill = PatternFill("solid", fgColor="FFF7D6")
dvm = DataValidation(type="list", formula1=f"=Vozy!$A${r0}:$A${LAST}"); wk.add_data_validation(dvm); dvm.add("B4")
dvs = DataValidation(type="list", formula1='"10 %,5 %,0 %"'); wk.add_data_validation(dvs); dvs.add("B8")
dva = DataValidation(type="list", formula1='"ano,ne"'); wk.add_data_validation(dva); dva.add("B7")
calc = [
    ("Měsíční cena vozu", f"=INDEX(Vozy!$C${r0}:$C${LAST},MATCH(B4,Vozy!$A${r0}:$A${LAST},0))", "z listu Vozy"),
    ("Počet měsíců (přepočet)", f"=B5/{P_DNI}", "dny / dní v měsíci"),
    ("Pronájem vozu", "=B10*B11", ""),
    ("Příplatek za nájezd / měsíc", f'=IF(B6="neomezeně",IFERROR(INDEX(Vozy!$R${r0}:$R${LAST},MATCH(B4,Vozy!$A${r0}:$A${LAST},0))*1,0),MAX(0,(B6-{P_KM})/{P_KROK})*{P_CENAKROK})', "každých 1 000 km nad nájezd v ceně = 6 000 Kč; „neomezeně“ = pevný příplatek z listu Vozy (3008: 6 000 Kč)"),
    ("Příplatek za nájezd celkem", "=B13*B11", ""),
    ("Druhý řidič", f'=IF(B7="ano",IF(B5>={P_RIDIC_ZDARMA},0,B5*{P_RIDIC}),0)', "nad 30 dní zdarma, jinak 120 Kč/den"),
    ("Kategorie spoluúčasti", f"=INDEX(Vozy!$E${r0}:$E${LAST},MATCH(B4,Vozy!$A${r0}:$A${LAST},0))", ""),
    ("Příplatek spoluúčast / měsíc", f'=IF(B8="5 %",INDEX(Spoluúčast!$D$5:$D$10,MATCH(B16,Spoluúčast!$A$5:$A$10,0)),IF(B8="0 %",INDEX(Spoluúčast!$E$5:$E$10,MATCH(B16,Spoluúčast!$A$5:$A$10,0)),0))', "prázdné v listu Spoluúčast = 0 / na dotaz"),
    ("Příplatek spoluúčast celkem", "=B17*B11", ""),
    ("CELKEM bez DPH", "=B12+B14+B15+B18", ""),
    ("CELKEM s DPH", f"=B19*(1+{P_DPH})", ""),
    ("Průměrně za měsíc bez DPH", "=IFERROR(B19/B11,0)", ""),
]
for i, (a, f, n) in enumerate(calc, 10):
    wk.cell(i, 1, a).font = B if a.startswith("CELKEM") else N
    x = wk.cell(i, 2, f); x.font = B if a.startswith("CELKEM") else N
    x.number_format = "0.00" if i == 11 else ("@" if i == 16 else KC)
    wk.cell(i, 3, n).font = NOTE
    for cc in range(1, 4): wk.cell(i, cc).border = THIN

wb.save(OUT)
print("ok", OUT)
