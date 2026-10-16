import sys, json, re, subprocess, pypdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from pypdf import Transformation

pdfmetrics.registerFont(TTFont('DV', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
registerFontFamily('DV', normal='DV', bold='DVB', italic='DV', boldItalic='DVB')

DATUM = "11.10.2026"
SPU_PCT, SPU_MIN, KM_RATE = 0.10, 10000, 7.0
PU_MARKUP = 1.21  # skutečná cena opravy PU + 21 %
DMG_MARKUP = 1.21  # škody (oddíl A) = cena opravy dle HAVEX + 21 %
SPU_FLAT = 10000  # PU Fabian: skutečná cena opravy, max. 10 000 Kč za každou pojistnou událost

def fmt(x): return f"{x:,.2f}".replace(",", " ").replace(".", ",")
def nice(s): return s.replace(' - ', ' – ')
def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def spu_for(cost):
    return cost if cost < SPU_MIN else max(cost * SPU_PCT, SPU_MIN)

N = ParagraphStyle('n', fontName='DV', fontSize=8.5, leading=11)
S = ParagraphStyle('s', parent=N, fontSize=7.5, leading=9.5, textColor=colors.HexColor('#444444'))
B = ParagraphStyle('b', parent=N, fontName='DVB')
H = ParagraphStyle('h', fontName='DVB', fontSize=13, leading=16, spaceAfter=2)
SEC = ParagraphStyle('sec', fontName='DVB', fontSize=9, leading=12, spaceBefore=8, spaceAfter=3)
R = ParagraphStyle('r', parent=N, alignment=2)
RB = ParagraphStyle('rb', parent=B, alignment=2)

def table(rows, widths, total_row=True):
    t = Table(rows, colWidths=widths)
    st = [('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('LINEBELOW',(0,0),(-1,0),0.5,colors.grey),
          ('BOX',(0,0),(-1,-1),0.5,colors.grey),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
          ('TOPPADDING',(0,0),(-1,-1),2.5),('BOTTOMPADDING',(0,0),(-1,-1),2.5)]
    if total_row:
        st += [('LINEABOVE',(0,-1),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#f6f6f6'))]
    t.setStyle(TableStyle(st)); return t

def build(d, out, stamp):
    DATUM = d['dat_protokolu']
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=15*mm,
                            title=f"Vyúčtování škod {d['rz']}", author="RX Auto, s.r.o.")
    W = A4[0] - 36*mm
    cislo = f"VŠ-2026/{d['rz']}"
    el = []
    hdr = Table([[Paragraph("<b>RX Auto, s.r.o.</b><br/>Aviatická 1092/8, 161 00 Praha 6 – Ruzyně<br/>IČO: 06044310, DIČ: CZ06044310", N),
                  Paragraph(f"Číslo dokladu: <b>{cislo}</b><br/>Datum vystavení: {DATUM}", R)]], colWidths=[W*0.6, W*0.4])
    hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.8,colors.black),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    el += [hdr, Spacer(1, 8), Paragraph("VYÚČTOVÁNÍ ŠKOD PŘI VRÁCENÍ VOZIDLA", H), Spacer(1, 4)]
    info = Table([[Paragraph("<b>Odběratel</b>", N), Paragraph("<b>Vozidlo</b>", N)],
        [Paragraph("Fábián Automotive Kft<br/>Garibaldi u. 1, 2040 Budaörs, Maďarsko<br/>Company ID: 1309213900<br/>VAT: HU29316476", N),
         Paragraph(f"{esc(d['vuz'])}<br/>RZ: <b>{d['rz']}</b>, VIN: {d['vin']}<br/>Datum vrácení: {d['vraceno']}<br/>Stav km při vrácení: {int(d['km']):,}".replace(",", " "), N)]],
        colWidths=[W/2, W/2])
    info.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.5,colors.grey),('INNERGRID',(0,0),(-1,-1),0.5,colors.grey),
                              ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('VALIGN',(0,0),(-1,-1),'TOP')]))
    el += [info, Spacer(1, 4),
           Paragraph(f"Podklad: protokol o vrácení vozidla HAVEX Mobility s.r.o. č. {d['cislo']} ze dne {d['dat_protokolu']}.", S)]

    total = 0; letters = []
    # A
    if d['A']:
        sumA = round(sum(round(a * DMG_MARKUP, 2) for _, a in d['A'] if a), 2)
        rows = [[Paragraph("<b>Položka</b>", N), Paragraph("<b>Kč bez DPH</b>", R)]]
        rows += [[Paragraph(esc(nice(n)), N), Paragraph(fmt(round(a * DMG_MARKUP, 2)) if a else "–", R)] for n, a in d['A']]
        rows += [[Paragraph("<b>Celkem škody hrazené nájemcem</b>", N), Paragraph(f"<b>{fmt(sumA)}</b>", R)]]
        el += [Paragraph("A. Neakceptovatelné poškození – hradí nájemce", SEC), table(rows, [W*0.78, W*0.22])]
        total += sumA; letters.append('A')
    # B
    sumB = 0
    n = d['pu_count']; P = d['PU']
    if n:
        pol = f"Spoluúčast dle smluvních podmínek: za každou pojistnou událost skutečná cena opravy navýšená o 21 %, nejvýše {fmt(SPU_FLAT)} Kč."
        rows = [[Paragraph("<b>Pojistná událost</b>", N), Paragraph("<b>Orientační cena</b>", R), Paragraph("<b>Spoluúčast</b>", R)]]
        if n == len(P):
            for desc, c in P:
                sp = SPU_FLAT if c >= SPU_FLAT else min(round(c * PU_MARKUP, 2), SPU_FLAT); sumB += sp
                rows.append([Paragraph(esc(nice(desc)), N), Paragraph(fmt(c), R), Paragraph(fmt(sp), R)])
        else:
            tc = sum(c for _, c in P); sumB = SPU_FLAT * n if tc >= SPU_FLAT * n else min(round(tc * PU_MARKUP, 2), SPU_FLAT * n)
            for desc, c in P:
                rows.append([Paragraph(esc(nice(desc)), N), Paragraph(fmt(c), R), Paragraph("", R)])
            rows.append([Paragraph(f"Spoluúčast za {n} pojistn{'ou událost' if n == 1 else 'é události'} (max. {fmt(SPU_FLAT)} Kč / PU)", N), Paragraph("", R), Paragraph(fmt(sumB), R)])
        rows.append([Paragraph(f"<b>Celkem spoluúčast ({n} × PU)</b>", N), Paragraph("", R), Paragraph(f"<b>{fmt(sumB)}</b>", R)])
        LB = chr(ord('A') + len(letters))
        el += [Paragraph(f"{LB}. Poškození řešená jako pojistná událost – spoluúčast nájemce", SEC),
               Paragraph(pol, S), Spacer(1, 3), table(rows, [W*0.56, W*0.22, W*0.22])]
        total += sumB; letters.append(LB)
    # C
    sumC = 0
    if d['km_over']:
        sumC = int(d['km_over'] * KM_RATE + 0.5)
        L = chr(ord('A') + len(letters))
        rows = [[Paragraph("<b>Položka</b>", N), Paragraph("<b>Kč bez DPH</b>", R)],
                [Paragraph(f"Ujeté nadlimitní km – {d['km_over']:,} km".replace(",", " ") + f" × {fmt(KM_RATE)} Kč", N), Paragraph(fmt(sumC), R)]]
        el += [Paragraph(f"{L}. Nadlimitní kilometry", SEC), table(rows, [W*0.78, W*0.22], total_row=False)]
        total += sumC; letters.append(L)
    lbl = " + ".join(chr(ord('A') + i) for i in range(len(letters)))
    tot = Table([[Paragraph(f"<b>CELKEM K ÚHRADĚ BEZ DPH{' (' + lbl + ')' if len(letters) > 1 else ''}</b>", B), Paragraph(f"<b>{fmt(total)} Kč</b>", RB)]],
                colWidths=[W*0.70, W*0.30])
    tot.setStyle(TableStyle([('BOX',(0,0),(-1,-1),1,colors.black),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e8eef7')),
                             ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    el += [Spacer(1, 10), tot, Spacer(1, 4),
           Paragraph("Částka bude vyúčtována fakturou. DPH bude uplatněna dle platných předpisů.", S), Spacer(1, 14)]
    sig = Table([[Paragraph(f"V Praze dne {DATUM}", N), Paragraph("Za RX Auto, s.r.o.", R)], ["", ""],
                 [Paragraph("", N), Paragraph("razítko a podpis", ParagraphStyle('c', parent=S, alignment=2))]],
                colWidths=[W/2, W/2], rowHeights=[None, 18*mm, None])
    sig.setStyle(TableStyle([('LINEABOVE',(1,2),(1,2),0.5,colors.grey)]))
    el.append(sig)
    doc.build(el)
    # stamp
    bb = subprocess.run(['pdftotext', '-bbox', out, '-'], capture_output=True, text=True).stdout
    m = list(re.finditer(r'yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">razítko<', bb))[-1]
    y0 = float(m.group(1))
    r = pypdf.PdfReader(out); w = pypdf.PdfWriter(); w.append(r)
    pg = w.pages[-1]; Hh = float(pg.mediabox.height)
    sp = pypdf.PdfReader(stamp).pages[0]
    sx0, sy0, sx1, sy1 = 220, 611, 345, 651
    sp.mediabox = pypdf.generic.RectangleObject([sx0, sy0, sx1, sy1]); sp.cropbox = sp.mediabox
    tx = A4[0] - 18*mm - (sx1 - sx0) - sx0 - 5
    ty = (Hh - y0) + 6 - sy0
    pg.merge_transformed_page(sp, Transformation().translate(tx, ty))
    w.write(out)
    return dict(rz=d['rz'], A=sum(a for _, a in d['A'] if a), B=sumB, C=sumC, total=total, havex=d['havex_total'], pages=len(r.pages))

if __name__ == '__main__':
    D = json.load(open(sys.argv[1])); outdir = sys.argv[2]; stamp = sys.argv[3]
    res = [build(d, f"{outdir}/Vyuctovani skod {d['rz']} - Fabian.pdf", stamp) for d in D]
    json.dump(res, open(f"{outdir}/summary.json", 'w'), indent=1)
    for x in res: print(x)
    print('TOTAL', sum(x['total'] for x in res), 'HAVEX', sum(x['havex'] for x in res))
