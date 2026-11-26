#!/usr/bin/env python3
"""Generátor předávacího protokolu k dlouhodobé nájemní smlouvě (B2B)
pod Carnetto RX s.r.o.

Použití (parametry načte z vedle ležícího JSON souboru – stejné schéma
jako nájemní smlouva, pouze přidáno pole 'protokol'):

    python3 gen_predavaci_protokol.py smlouva.json vystup.docx

Protokol obsahuje dvě sekce:
  A) Předání vozidla při zahájení nájmu
  B) Vrácení vozidla při ukončení nájmu
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH


def cz_mesic(datum_iso: str) -> str:
    from datetime import date
    d = date.fromisoformat(datum_iso)
    mesice = ["ledna", "února", "března", "dubna", "května", "června",
              "července", "srpna", "září", "října", "listopadu", "prosince"]
    return f"{d.day}. {mesice[d.month-1]} {d.year}"


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

    def kv_table(radky):
        tbl = doc.add_table(rows=len(radky), cols=2)
        tbl.style = 'Light Grid Accent 1'
        for i, (k, v) in enumerate(radky):
            tbl.cell(i, 0).text = k
            tbl.cell(i, 1).text = v
            for pp in tbl.cell(i, 0).paragraphs:
                for r in pp.runs:
                    r.bold = True
        return tbl

    p_ = cfg["pronajimatel"]
    n_ = cfg["najemce"]
    v_ = cfg["vozidlo"]
    s_ = cfg["smlouva"]
    pr = cfg.get("protokol", {})

    # Hlavička
    heading("PŘEDÁVACÍ PROTOKOL", level=0, center=True)
    para(f"k Nájemní smlouvě o nájmu dopravního prostředku ze dne {cz_mesic(s_['od'])}",
         center=True, size=10)
    doc.add_paragraph()

    # I. Smluvní strany
    heading("I. Smluvní strany")
    para("Pronajímatel:", bold=True)
    para(f"{p_['nazev']}, IČO: {p_['ico']}, sídlo: {p_['sidlo']}, "
         f"zastoupen: {p_['zastoupena']}, {p_['funkce']}")
    doc.add_paragraph()
    para("Nájemce:", bold=True)
    dic = f", DIČ: {n_.get('dic')}" if n_.get('dic') else ""
    para(f"{n_['nazev']}, IČO: {n_['ico']}{dic}, sídlo: {n_['sidlo']}, "
         f"zastoupen: {n_['zastoupena']}, {n_['funkce']}")
    doc.add_paragraph()

    # II. Vozidlo
    heading("II. Předmět předání – vozidlo")
    kv_table([
        ("Tovární značka a model:", v_["model"]),
        ("Registrační značka (SPZ):", v_["spz"]),
        ("Identifikační číslo (VIN):", v_["vin"]),
        ("Druh paliva:", v_["palivo"]),
        ("Barva vozidla:", v_.get("barva", "……………………………………")),
        ("Rok výroby / datum 1. registrace:", v_.get("rok_registrace", "……………………………………")),
    ])
    doc.add_paragraph()

    # A. PŘEDÁNÍ
    heading("A. Předání vozidla při zahájení nájmu")

    predani = pr.get("predani", {})
    kv_table([
        ("Datum a čas předání:", predani.get("datum", cz_mesic(s_['od'])) + ", čas: ……………"),
        ("Místo předání:", predani.get("misto", p_.get("sidlo", "……………………………………"))),
        ("Stav tachometru při předání (km):", predani.get("km", "……………………")),
        ("Stav paliva při předání:", predani.get("palivo_proc", "…………… %") ),
    ])
    doc.add_paragraph()

    para("Předané doklady a příslušenství:", bold=True)
    doklady = [
        "Osvědčení o registraci vozidla (OTP) – část II.",
        "Doklad o pojištění odpovědnosti z provozu vozidla (zelená karta)",
        "Servisní knížka vozidla",
        "Klíče od vozidla (počet ks):",
        "Rezervní / dojezdové kolo",
        "Zvedák",
        "Klíč na kola",
        "Lékárnička",
        "Reflexní vesta",
        "Výstražný trojúhelník",
        "Elektronická dálniční známka (ČR)",
        "Palivová karta (CCS / OMV / jiná)",
        "Dálkové ovládání centrálního zamykání (počet ks):",
    ]
    tbl = doc.add_table(rows=len(doklady), cols=2)
    tbl.style = 'Light Grid Accent 1'
    for i, d in enumerate(doklady):
        tbl.cell(i, 0).text = d
        tbl.cell(i, 1).text = "ANO / NE / počet: ……"
    doc.add_paragraph()

    para("Stav vozidla při předání:", bold=True)
    para("Exteriér (popis stavu, zjevná poškození, škrábance, promáčkliny):")
    para("……………………………………………………………………………………………………………………")
    para("……………………………………………………………………………………………………………………")
    para("……………………………………………………………………………………………………………………")
    doc.add_paragraph()
    para("Interiér (popis stavu, čistota, poškození):")
    para("……………………………………………………………………………………………………………………")
    para("……………………………………………………………………………………………………………………")
    doc.add_paragraph()
    para("Další poznámky k předání:")
    para("……………………………………………………………………………………………………………………")
    para("……………………………………………………………………………………………………………………")
    doc.add_paragraph()

    para("Osoby oprávněné řídit vozidlo (jméno, č. ŘP, platnost):", bold=True)
    tbl = doc.add_table(rows=4, cols=4)
    tbl.style = 'Light Grid Accent 1'
    tbl.cell(0, 0).text = "Jméno a příjmení"
    tbl.cell(0, 1).text = "Číslo ŘP"
    tbl.cell(0, 2).text = "Kategorie"
    tbl.cell(0, 3).text = "Platnost do"
    for i in (1, 2, 3):
        for j in range(4):
            tbl.cell(i, j).text = "……………………"
    for pp in tbl.rows[0].cells:
        for par in pp.paragraphs:
            for r in par.runs:
                r.bold = True
    doc.add_paragraph()

    para("Nájemce svým podpisem potvrzuje, že výše uvedené vozidlo, doklady a "
         "příslušenství převzal v popsaném stavu, že se s vozidlem seznámil, "
         "vyzkoušel jeho funkčnost a nemá vůči jeho stavu výhrad kromě těch, "
         "které jsou v tomto protokolu výslovně uvedeny.")
    doc.add_paragraph()
    doc.add_paragraph()

    # Podpisy – předání
    tbl = doc.add_table(rows=4, cols=2)
    tbl.cell(0, 0).text = "V ………………………… dne ……………………"
    tbl.cell(0, 1).text = "V ………………………… dne ……………………"
    tbl.cell(2, 0).text = "…………………………………………"
    tbl.cell(2, 1).text = "…………………………………………"
    tbl.cell(3, 0).text = f"{p_['nazev']}\n{p_['zastoupena']}, {p_['funkce']}\nPronajímatel – předal"
    tbl.cell(3, 1).text = f"{n_['nazev']}\n{n_['zastoupena']}, {n_['funkce']}\nNájemce – převzal"
    for row in tbl.rows:
        for cell in row.cells:
            for pp in cell.paragraphs:
                pp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    # B. VRÁCENÍ
    heading("B. Vrácení vozidla při ukončení nájmu")

    vraceni = pr.get("vraceni", {})
    kv_table([
        ("Datum a čas vrácení:", vraceni.get("datum", cz_mesic(s_['do'])) + ", čas: ……………"),
        ("Místo vrácení:", vraceni.get("misto", p_.get("sidlo", "……………………………………"))),
        ("Stav tachometru při vrácení (km):", "……………………"),
        ("Celkem najeto za dobu nájmu (km):", "……………………"),
        ("Stav paliva při vrácení:", "…………… %"),
    ])
    doc.add_paragraph()

    para("Vrácené doklady a příslušenství:", bold=True)
    tbl = doc.add_table(rows=len(doklady), cols=2)
    tbl.style = 'Light Grid Accent 1'
    for i, d in enumerate(doklady):
        tbl.cell(i, 0).text = d
        tbl.cell(i, 1).text = "ANO / NE / počet: ……"
    doc.add_paragraph()

    para("Zjištěná poškození nad rámec běžného opotřebení:", bold=True)
    para("(popis, lokalizace na vozidle, odhad nákladů na opravu)")
    para("……………………………………………………………………………………………………………………")
    para("……………………………………………………………………………………………………………………")
    para("……………………………………………………………………………………………………………………")
    doc.add_paragraph()

    para("Další poznámky k vrácení (čistota, technický stav, provozní kapaliny):")
    para("……………………………………………………………………………………………………………………")
    para("……………………………………………………………………………………………………………………")
    doc.add_paragraph()

    para("Vyrovnání k datu vrácení:", bold=True)
    kv_table([
        ("Doplatek za rozdíl ve stavu paliva:", "…………… Kč"),
        ("Doplatek za škody nekryté pojištěním / spoluúčast:", "…………… Kč"),
        ("Nedoplatek nájemného / jiné pohledávky:", "…………… Kč"),
        ("Celkem k úhradě Nájemcem:", "…………… Kč"),
    ])
    doc.add_paragraph()

    para("Smluvní strany svými podpisy potvrzují, že vozidlo bylo vráceno v "
         "popsaném stavu a že případné vzájemné nároky budou vypořádány dle "
         "nájemní smlouvy.")
    doc.add_paragraph()
    doc.add_paragraph()

    # Podpisy – vrácení
    tbl = doc.add_table(rows=4, cols=2)
    tbl.cell(0, 0).text = "V ………………………… dne ……………………"
    tbl.cell(0, 1).text = "V ………………………… dne ……………………"
    tbl.cell(2, 0).text = "…………………………………………"
    tbl.cell(2, 1).text = "…………………………………………"
    tbl.cell(3, 0).text = f"{p_['nazev']}\n{p_['zastoupena']}, {p_['funkce']}\nPronajímatel – převzal zpět"
    tbl.cell(3, 1).text = f"{n_['nazev']}\n{n_['zastoupena']}, {n_['funkce']}\nNájemce – vrátil"
    for row in tbl.rows:
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
