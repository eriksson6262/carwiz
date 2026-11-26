#!/usr/bin/env python3
"""Generátor dlouhodobé nájemní smlouvy (B2B) pod Carnetto RX s.r.o.

Použití (parametry načte z vedle ležícího JSON souboru, kde jsou všechny
konkrétní údaje nájemce a vozidla - tím se zabrání commitu osobních údajů
do repa):

    python3 gen_najemni_smlouva.py smlouva.json vystup.docx

JSON schéma - viz najemni-smlouva.schema.json ve stejné složce.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH


def mesicne_cz(n: int) -> str:
    return {1: "jednoho", 2: "dvou", 3: "tří", 4: "čtyř", 5: "pěti",
            6: "šesti", 7: "sedmi", 8: "osmi", 9: "devíti", 10: "deseti",
            11: "jedenácti", 12: "dvanácti"}.get(n, str(n))


def cz_mesic(datum_iso: str) -> str:
    """Z data YYYY-MM-DD vrátí '27. listopadu 2026'."""
    from datetime import date
    d = date.fromisoformat(datum_iso)
    mesice = ["ledna", "února", "března", "dubna", "května", "června",
              "července", "srpna", "září", "října", "listopadu", "prosince"]
    return f"{d.day}. {mesice[d.month-1]} {d.year}"


def formatuj_castku(n: float) -> str:
    s = f"{n:,.2f}".replace(",", " ").replace(".", ",")
    return s


def gen(cfg: dict, out: str) -> None:
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    def heading(text, level=1, center=False):
        p = doc.add_paragraph()
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(14 if level == 0 else 12 if level == 1 else 11)

    def para(text, bold=False, center=False, size=None):
        p = doc.add_paragraph()
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.bold = bold
        if size:
            r.font.size = Pt(size)

    p = cfg["pronajimatel"]
    n = cfg["najemce"]
    v = cfg["vozidlo"]
    s = cfg["smlouva"]

    # Hlavička
    heading("NÁJEMNÍ SMLOUVA O NÁJMU DOPRAVNÍHO PROSTŘEDKU", level=0, center=True)
    para("uzavřená podle § 2321 a násl. zákona č. 89/2012 Sb., občanský zákoník, "
         "v platném znění (dále jen „Smlouva“)", center=True, size=10)
    doc.add_paragraph()

    # I. Smluvní strany
    heading("Článek I. – Smluvní strany")
    para("Pronajímatel:", bold=True)
    para(p["nazev"])
    para(f"IČO: {p['ico']}")
    if p.get("spisova_znacka"):
        para(f"Spisová značka: {p['spisova_znacka']}")
    para(f"Sídlo: {p['sidlo']}")
    para(f"Zastoupena: {p['zastoupena']}, {p['funkce']}")
    para("(dále jen „Pronajímatel“)")
    doc.add_paragraph()

    para("Nájemce:", bold=True)
    para(n["nazev"])
    para(f"IČO: {n['ico']}")
    if n.get("dic"):
        para(f"DIČ: {n['dic']}")
    para(f"Sídlo: {n['sidlo']}")
    para(f"Zastoupena: {n['zastoupena']}, {n['funkce']}")
    para("(dále jen „Nájemce“)")
    doc.add_paragraph()

    # II. Předmět nájmu
    heading("Článek II. – Předmět nájmu")
    para("1. Pronajímatel přenechává Nájemci do dočasného užívání níže specifikované "
         "motorové vozidlo (dále jen „Vozidlo“):")
    tbl = doc.add_table(rows=5, cols=2)
    tbl.style = 'Light Grid Accent 1'
    radky = [
        ("Tovární značka a model:", v["model"]),
        ("Registrační značka (SPZ):", v["spz"]),
        ("Identifikační číslo vozidla (VIN):", v["vin"]),
        ("Druh paliva:", v["palivo"]),
        ("Pronajímatel je oprávněným uživatelem Vozidla na základě:", v.get("titul", "leasingové smlouvy")),
    ]
    for i, (k, hodnota) in enumerate(radky):
        tbl.cell(i, 0).text = k
        tbl.cell(i, 1).text = hodnota
        for pp in tbl.cell(i, 0).paragraphs:
            for r in pp.runs:
                r.bold = True
    doc.add_paragraph()

    para("2. Nájemce prohlašuje, že se před podpisem této Smlouvy seznámil se stavem "
         "Vozidla, jeho technickým vybavením a dokumentací, že Vozidlo je ve stavu "
         "způsobilém k užívání ke smluvenému účelu a v tomto stavu je od Pronajímatele "
         "přejímá, což stvrdí podpisem předávacího protokolu.")
    para("3. Účelem nájmu je užívání Vozidla Nájemcem pro potřeby jeho podnikatelské "
         "činnosti, zejména k pracovním cestám.")

    # III. Doba nájmu
    heading("Článek III. – Doba nájmu")
    para(f"1. Tato Smlouva se uzavírá na dobu určitou v délce {s['mesicu']} "
         f"({mesicne_cz(s['mesicu'])}) měsíců, a to od {cz_mesic(s['od'])} "
         f"do {cz_mesic(s['do'])} včetně.")
    para("2. Smluvní strany se mohou písemně dohodnout na prodloužení doby nájmu, "
         "a to před uplynutím sjednané doby.")
    para("3. Nájem skončí uplynutím sjednané doby, dohodou smluvních stran, "
         "výpovědí nebo odstoupením od Smlouvy dle článku VIII.")

    # IV. Nájemné
    heading("Článek IV. – Nájemné a platební podmínky")
    cena_bez = s["cena_mesic_bez_dph"]
    cena_s = round(cena_bez * 1.21, 2)
    celkem_bez = cena_bez * s["mesicu"]
    celkem_s = round(celkem_bez * 1.21, 2)
    para(f"1. Smluvní strany se dohodly na nájemném ve výši "
         f"{formatuj_castku(cena_bez)} Kč bez DPH za jeden kalendářní měsíc užívání Vozidla.")
    para(f"2. K nájemnému bude účtována daň z přidané hodnoty v zákonné výši "
         f"(aktuálně 21 %). Celkové měsíční nájemné včetně DPH činí "
         f"{formatuj_castku(cena_s)} Kč.")
    para(f"3. Nájemné za celou dobu nájmu činí {formatuj_castku(celkem_bez)} Kč bez DPH, "
         f"resp. {formatuj_castku(celkem_s)} Kč včetně DPH.")
    para(f"4. Nájemné bude Pronajímatelem fakturováno Nájemci měsíčně, a to na základě "
         f"daňového dokladu – faktury se splatností {s.get('splatnost_dnu', 10)} dnů ode dne "
         f"jejího vystavení.")
    para("5. Platby nájemného budou prováděny bezhotovostním převodem na bankovní "
         "účet Pronajímatele uvedený na faktuře.")
    para("6. V případě prodlení Nájemce s úhradou jakékoli platby dle této Smlouvy "
         "je Pronajímatel oprávněn požadovat úrok z prodlení v zákonné výši.")

    # V. Předání a vrácení
    heading("Článek V. – Předání a vrácení vozidla")
    para("1. Pronajímatel předá Vozidlo Nájemci v den počátku nájmu v místě sídla "
         "Pronajímatele, nedohodnou-li se smluvní strany jinak.")
    para("2. O předání Vozidla bude sepsán předávací protokol obsahující mimo jiné "
         "stav tachometru, stav paliva, výbavu Vozidla a popis případných "
         "zjevných poškození. Předávací protokol je nedílnou součástí této Smlouvy.")
    para("3. Nájemce je povinen po skončení nájmu vrátit Vozidlo Pronajímateli "
         "ve stavu, v jakém mu bylo předáno, s přihlédnutím k obvyklému opotřebení "
         "odpovídajícímu době nájmu a sjednanému účelu užívání.")
    para("4. O vrácení Vozidla bude sepsán protokol o vrácení obdobným způsobem "
         "jako při předání.")

    # VI. Práva a povinnosti
    heading("Článek VI. – Práva a povinnosti Nájemce")
    para("1. Nájemce je povinen užívat Vozidlo řádně, s péčí řádného hospodáře a v "
         "souladu s jeho určením a technickými podmínkami stanovenými výrobcem.")
    para("2. Nájemce je povinen dodržovat platné předpisy upravující provoz na "
         "pozemních komunikacích a je plně odpovědný za všechny přestupky, pokuty "
         "a jiné sankce vzniklé v době trvání nájmu.")
    para("3. Nájemce zajistí na vlastní náklady běžnou údržbu Vozidla (zejména mytí, "
         "doplňování provozních kapalin, péči o interiér), hrazení nákladů na "
         "pohonné hmoty, mýtné, parkovné a obdobné provozní náklady.")
    para("4. Nájemce bez písemného souhlasu Pronajímatele nesmí:")
    for x in ("a) přenechat Vozidlo do užívání třetí osobě (podnájem),",
              "b) provádět jakékoli úpravy nebo technické změny Vozidla,",
              "c) používat Vozidlo k závodním nebo soutěžním účelům,",
              "d) používat Vozidlo pro přepravu nebezpečných látek nebo nákladů."):
        para(x)
    para("5. Nájemce je povinen bezodkladně oznámit Pronajímateli každou dopravní "
         "nehodu, poškození, odcizení nebo závadu na Vozidle a postupovat podle "
         "pokynů Pronajímatele a pojistitele.")
    para("6. Vozidlo smí řídit pouze osoby řádně určené Nájemcem, s platným "
         "řidičským oprávněním odpovídajícím kategorii Vozidla.")

    # VII. Pojištění
    heading("Článek VII. – Pojištění a odpovědnost za škodu")
    para("1. Vozidlo je po dobu nájmu pojištěno zákonným pojištěním odpovědnosti za "
         "škodu způsobenou provozem vozidla a havarijním pojištěním, které sjednává "
         "a hradí Pronajímatel.")
    para("2. Spoluúčast Nájemce v případě pojistné události (škody na Vozidle, "
         "odcizení) činí standardně 10 %, minimálně však 10 000 Kč, nedohodnou-li "
         "se smluvní strany jinak.")
    para("3. Za škody na Vozidle, které nejsou kryty pojištěním (např. škody "
         "způsobené hrubou nedbalostí, úmyslně, požitím alkoholu nebo jiných "
         "návykových látek, při nedodržení servisních intervalů), odpovídá "
         "Nájemce v plné výši.")
    para("4. Nájemce je povinen při vzniku škodné události postupovat v souladu s "
         "platnými právními předpisy, zejména přivolat Policii ČR v zákonem "
         "stanovených případech a sepsat záznam o dopravní nehodě.")

    # VIII. Ukončení
    heading("Článek VIII. – Ukončení smlouvy")
    para("1. Smlouva zaniká:")
    for x in ("a) uplynutím doby, na kterou byla sjednána,",
              "b) písemnou dohodou smluvních stran,",
              "c) odstoupením od Smlouvy v případech stanovených zákonem nebo touto Smlouvou,",
              "d) výpovědí s výpovědní dobou 1 (jednoho) měsíce, která počíná běžet "
              "prvním dnem kalendářního měsíce následujícího po doručení výpovědi druhé smluvní straně."):
        para(x)
    para("2. Pronajímatel je oprávněn odstoupit od Smlouvy s okamžitou účinností zejména v případě, že:")
    for x in ("a) Nájemce je v prodlení s úhradou nájemného o více než 30 dnů,",
              "b) Nájemce užívá Vozidlo v rozporu s touto Smlouvou nebo k jinému účelu, než pro který byla Smlouva uzavřena,",
              "c) Nájemce hrubě poruší povinnosti vyplývající z této Smlouvy nebo platných právních předpisů."):
        para(x)
    para("3. Po skončení nájmu je Nájemce povinen předat Vozidlo zpět Pronajímateli "
         "nejpozději v den skončení nájmu v místě sjednaném dle čl. V.")

    # IX. Závěr
    heading("Článek IX. – Závěrečná ustanovení")
    para("1. Tato Smlouva nabývá platnosti a účinnosti dnem jejího podpisu oběma smluvními stranami.")
    para("2. Jakékoli změny a doplňky této Smlouvy musí být učiněny písemnou formou "
         "ve formě vzestupně číslovaných dodatků, podepsaných oběma smluvními stranami.")
    para("3. Právní vztahy touto Smlouvou výslovně neupravené se řídí příslušnými "
         "ustanoveními zákona č. 89/2012 Sb., občanský zákoník, v platném znění.")
    para("4. Smluvní strany prohlašují, že si Smlouvu před jejím podpisem přečetly, "
         "že byla uzavřena po vzájemném projednání podle jejich pravé a svobodné vůle, "
         "určitě, vážně a srozumitelně, nikoliv v tísni a za nápadně nevýhodných "
         "podmínek, což stvrzují svými vlastnoručními podpisy.")
    para("5. Smlouva je vyhotovena ve dvou (2) stejnopisech, z nichž každá "
         "smluvní strana obdrží po jednom vyhotovení.")
    doc.add_paragraph()
    doc.add_paragraph()

    # Podpisy
    podpis = doc.add_table(rows=4, cols=2)
    podpis.cell(0, 0).text = f"V {p.get('misto_podpisu', 'Praze')} dne ……………………"
    podpis.cell(0, 1).text = f"V {n.get('misto_podpisu', '………………………')} dne ……………………"
    podpis.cell(2, 0).text = "…………………………………………"
    podpis.cell(2, 1).text = "…………………………………………"
    podpis.cell(3, 0).text = f"{p['nazev']}\n{p['zastoupena']}, {p['funkce']}\nPronajímatel"
    podpis.cell(3, 1).text = f"{n['nazev']}\n{n['zastoupena']}, {n['funkce']}\nNájemce"
    for row in podpis.rows:
        for cell in row.cells:
            for pp in cell.paragraphs:
                pp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(out)
    print(f"Vytvořeno: {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    cfg_path = Path(sys.argv[1])
    out_path = sys.argv[2]
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    gen(cfg, out_path)
