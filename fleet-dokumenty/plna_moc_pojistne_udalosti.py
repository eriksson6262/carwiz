#!/usr/bin/env python3
"""Plná moc RX Auto, s.r.o. k zastupování při řešení pojistných událostí (pojišťovna žádá PM od pojistníka).

Použití: python3 plna_moc_pojistne_udalosti.py <data.json> <out.pdf> [razitko.png]

data.json (fleet-dokumenty/data/ – necommitovat):
{
  "zmocnenci": [{"nazev": "HAVEX-auto s.r.o.", "ico": "60108151", "sidlo": "Na bělidle 503, 543 01 Vrchlabí",
                 "rejstrik": "Krajským soudem v Hradci Králové, oddíl C, vložka 5254"}],
  "pojistovna": "Kooperativa pojišťovna, a.s., Vienna Insurance Group, IČO 47116617",
  "udalost": {"cislo": "4262157879", "smlouva": "2283606632", "vznik": "11. 9. 2026",
              "vozidlo": "ŠKODA KAROQ", "rz": "8H84617"},      # volitelné – konkrétní škoda
  "misto": "Praze", "datum": "23. 11. 2026"
}
Razítko s podpisem (data/razitko_rx.png) se necommituje; zdroj viz havex/protokoly-vraceni/README.md.
"""
import json
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

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


class Podpis(Flowable):
    """Podpisová linka, nad ní volitelně razítko s podpisem."""

    def __init__(self, stamp=None, width=62 * mm):
        super().__init__()
        self.stamp, self.w, self.height = stamp, width, 24 * mm

    def wrap(self, aw, ah):
        return self.w, self.height

    def draw(self):
        c = self.canv
        if self.stamp:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(self.stamp)
            iw, ih = img.getSize()
            w = 56 * mm
            c.drawImage(img, 2 * mm, 1.5 * mm, width=w, height=w * ih / iw, mask="auto")
        c.setLineWidth(0.5)
        c.setDash(1, 2)
        c.line(0, 0, self.w, 0)


def build(d, out, stamp=None):
    n = ParagraphStyle("n", fontName="DV", fontSize=9.5, leading=12.8)
    j = ParagraphStyle("j", parent=n, alignment=4)
    h = ParagraphStyle("h", parent=n, fontName="DVB", fontSize=18, leading=24, alignment=1)
    s = ParagraphStyle("s", parent=n, fontName="DVB", fontSize=11, spaceBefore=8, spaceAfter=2)
    b = ParagraphStyle("b", parent=j, leftIndent=6 * mm, bulletIndent=1 * mm)
    zs = d["zmocnenci"]
    body = [Paragraph("PLNÁ MOC", h),
            Paragraph("k zastupování při řešení pojistných událostí", ParagraphStyle("c", parent=n, alignment=1)),
            Spacer(1, 4 * mm), Paragraph("Zmocnitel:", s), *[Paragraph(x, n) for x in ZMOCNITEL],
            Spacer(1, 3 * mm), Paragraph("tímto zmocňuje", n),
            Paragraph("Zmocněnce:" if len(zs) == 1 else "Zmocněnce (každého samostatně):", s)]
    for i, z in enumerate(zs):
        if i:
            body.append(Spacer(1, 2.5 * mm))
        body += [Paragraph(f"<b>{z['nazev']}</b>", n), Paragraph(f"IČO: {z['ico']}", n),
                 Paragraph(f"se sídlem {z['sidlo']}", n),
                 Paragraph(f"zapsaná v obchodním rejstříku vedeném {z['rejstrik']}", n)]
    u = d.get("udalost")
    body += [Spacer(1, 5 * mm),
             Paragraph(
                 f"aby zmocnitele jako pojistníka zastupoval{'i' if len(zs) > 1 else ''} vůči pojistiteli "
                 f"<b>{d['pojistovna']}</b>, při oznamování, šetření a likvidaci pojistných událostí na vozidlech, "
                 "která zmocnitel užívá na základě smluv se společností HAVEX Mobility s.r.o. a která jsou "
                 "u pojistitele pojištěna.", j)]
    if u:
        body += [Spacer(1, 2 * mm), Paragraph(
            f"Plná moc se vztahuje zejména na škodnou událost č. <b>{u['cislo']}</b> z pojistné smlouvy "
            f"č. <b>{u['smlouva']}</b>, datum vzniku {u['vznik']}, vozidlo {u['vozidlo']}, "
            f"RZ <b>{u['rz']}</b>.", j)]
    body += [Spacer(1, 3 * mm), Paragraph("Zmocněnec je oprávněn zejména:", n),
             Paragraph("oznamovat pojistné události a doplňovat k nim údaje a doklady,", b, bulletText="–"),
             Paragraph("jednat s pojistitelem, podávat vysvětlení, účastnit se prohlídek vozidla a přebírat "
                       "veškerou korespondenci k pojistným událostem,", b, bulletText="–"),
             Paragraph("činit úkony potřebné k opravě vozidla a k likvidaci pojistné události včetně určení "
                       "opravce a souhlasu s výplatou pojistného plnění vlastníku vozidla nebo opravci.",
                       b, bulletText="–"),
             Spacer(1, 3 * mm),
             Paragraph("Plná moc neopravňuje k uzavírání, změnám ani ukončování pojistných smluv a k přijetí "
                       "pojistného plnění náležejícího zmocniteli. Uděluje se na dobu neurčitou a zmocnitel "
                       "ji může kdykoli odvolat.", j),
             Spacer(1, 6 * mm),
             KeepTogether([Paragraph(f"V {d['misto']} dne {d['datum']}", n), Spacer(1, 3 * mm), Podpis(stamp),
                           Spacer(1, 1 * mm), Paragraph("RX Auto, s.r.o.<br/>Erik Rajohnson, jednatel", n)])]
    SimpleDocTemplate(out, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=15 * mm,
                      bottomMargin=14 * mm, title="Plná moc – pojistné události",
                      author="RX Auto, s.r.o.").build(body)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        build(json.load(f), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print(sys.argv[2])
