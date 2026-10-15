#!/usr/bin/env python3
"""Plná moc RX Auto, s.r.o. k přepisu vozidla (změna vlastníka/provozovatele v registru silničních vozidel).

Použití: python3 plna_moc_prepis.py <data.json> <out.pdf>

data.json (drží se v fleet-dokumenty/data/ – necommitovat, obsahuje osobní údaje):
{
  "zmocnenec": {"jmeno": "Jan Novák", "narozen": "1. 1. 1980", "ico": "12345678",
                "adresa": "Ulice 1, 110 00 Praha"},
  "vozidlo": {"popis": "BMW 218i Active Tourer", "spz": "1AB2345", "vin": "WBA..."},
  "misto": "Praze", "datum": "15. 10. 2026"
}
Dokument je určen k odeslání z datové schránky RX Auto (podpis nahrazen odesláním z DS, § 18 odst. 2 z. 300/2008 Sb.).
"""
import json
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping  # noqa: F401
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

ZMOCNITEL = [
    "<b>RX Auto, s.r.o.</b>",
    "IČO: 06044310, DIČ: CZ06044310",
    "se sídlem Aviatická 1092/8, Ruzyně, 161 00 Praha 6",
    "zapsaná v obchodním rejstříku vedeném Městským soudem v Praze, oddíl C, vložka 275114",
    "zastoupená Erikem Rajohnsonem, jednatelem",
]


def build(d, out):
    n = ParagraphStyle("n", fontName="DV", fontSize=10, leading=13.5, boldFontName="DVB")
    h = ParagraphStyle("h", parent=n, fontName="DVB", fontSize=18, leading=24, alignment=1)
    s = ParagraphStyle("s", parent=n, fontName="DVB", fontSize=11, spaceBefore=8)
    z, v = d["zmocnenec"], d["vozidlo"]
    zm = [f"<b>{z['jmeno']}</b>"]
    if z.get("narozen"):
        zm.append(f"narozen: {z['narozen']}")
    if z.get("ico"):
        zm.append(f"IČO: {z['ico']}")
    zm.append(f"bytem {z['adresa']}")
    body = [Paragraph("PLNÁ MOC", h), Spacer(1, 6 * mm),
            Paragraph("Zmocnitel:", s), *[Paragraph(x, n) for x in ZMOCNITEL],
            Spacer(1, 4 * mm), Paragraph("tímto zmocňuje", n),
            Paragraph("Zmocněnce:", s), *[Paragraph(x, n) for x in zm],
            Spacer(1, 6 * mm),
            Paragraph(
                "k zastupování zmocnitele ve všech úkonech souvisejících se zápisem změny vlastníka "
                "a provozovatele níže uvedeného silničního vozidla v registru silničních vozidel, "
                "zejména k podání žádosti o zápis změny vlastníka a provozovatele, podpisu všech "
                "potřebných listin, předložení a převzetí technického průkazu, osvědčení o registraci "
                "vozidla a tabulek s registrační značkou, jakož i k dalším úkonům s tím spojeným "
                "před příslušným obecním úřadem obce s rozšířenou působností.", n),
            Paragraph("Vozidlo:", s),
            Paragraph(f"Tovární značka a typ: <b>{v['popis']}</b>", n),
            Paragraph(f"Registrační značka (SPZ): <b>{v['spz']}</b>", n),
            Paragraph(f"VIN: <b>{v['vin']}</b>", n),
            Spacer(1, 6 * mm),
            Paragraph("Zmocněnec je oprávněn udělit substituční plnou moc další osobě.", n),
            Spacer(1, 8 * mm),
            Paragraph(f"V {d['misto']} dne {d['datum']}", n),
            Spacer(1, 14 * mm),
            Paragraph("………………………………………………", n),
            Paragraph("RX Auto, s.r.o.<br/>Erik Rajohnson, jednatel", n),
            Spacer(1, 10 * mm),
            Paragraph("Plnou moc v plném rozsahu přijímám.", n),
            Spacer(1, 12 * mm),
            Paragraph("………………………………………………", n),
            Paragraph(z["jmeno"], n),
            Spacer(1, 8 * mm),
            Paragraph("<font size=8>Dokument je odeslán z datové schránky zmocnitele; odeslání z datové "
                      "schránky právnické osoby má podle § 18 odst. 2 zákona č. 300/2008 Sb. stejné "
                      "účinky jako úkon učiněný písemně a podepsaný.</font>", n)]
    SimpleDocTemplate(out, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm,
                      topMargin=16 * mm, bottomMargin=14 * mm,
                      title="Plná moc – přepis vozidla", author="RX Auto, s.r.o.").build(body)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        build(json.load(f), sys.argv[2])
    print(sys.argv[2])
