#!/usr/bin/env python3
"""Protokol o poškození vozidla při vrácení (podklad k přefakturaci spoluúčasti OSEK).
Použití: python3 protokol_poskozeni.py vstup.json vystup.pdf
vstup.json: {"rz","vuz","najemce","prohlidka","km","palivo","polozky":[[oblast,nalez,kategorie]],"pu":[[cislo,popis]]}
"""
import json, sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

def build(d, out):
    ss = getSampleStyleSheet()
    for s in ss.byName.values():
        s.fontName = "DV"
    h = ss["Title"]; h.fontName = "DVB"; h.fontSize = 14
    n = ss["Normal"]; n.fontSize = 9.5; n.leading = 13
    el = [Paragraph(f"Protokol o poškození vozidla při vrácení – {d['rz']}", h),
          Paragraph("RX Auto, s.r.o., IČO 06044310, Aviatická 1092/8, 161 00 Praha 6", n), Spacer(1, 8)]
    info = [["Vozidlo", d["vuz"]], ["RZ", d["rz"]], ["Nájemce", d["najemce"]],
            ["Prohlídka při vrácení", d["prohlidka"]], ["Stav tachometru", f"{d['km']} km"], ["Palivo", d["palivo"]]]
    t = Table(info, colWidths=[130, 360])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DV", 9.5), ("FONT", (0, 0), (0, -1), "DVB", 9.5),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey)]))
    el += [t, Spacer(1, 10), Paragraph("Zjištěné poškození", ss["Heading3"])]
    rows = [["Oblast / díl", "Nález", "Kategorie"]] + d["polozky"]
    t = Table(rows, colWidths=[140, 230, 120])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DV", 9), ("FONT", (0, 0), (-1, 0), "DVB", 9),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey)]))
    el += [t, Spacer(1, 10), Paragraph("Pojistné události (Kooperativa)", ss["Heading3"])]
    sm = ss["BodyText"]; sm.fontSize = 9; sm.leading = 11
    rows = [["Číslo PU", "Rozsah škody"]] + [[a, Paragraph(b, sm)] for a, b in d["pu"]]
    t = Table(rows, colWidths=[110, 380])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DV", 9), ("FONT", (0, 0), (-1, 0), "DVB", 9),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey)]))
    el += [t, Spacer(1, 10), Paragraph(d.get("pozn", ""), n)]
    SimpleDocTemplate(out, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=45).build(el)

if __name__ == "__main__":
    build(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
