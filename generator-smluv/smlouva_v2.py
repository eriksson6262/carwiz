# -*- coding: utf-8 -*-
"""
Generátor nájemní smlouvy — verze 2.0 (PDF, moderní tabulkový design).

Na rozdíl od v1 (vyplnit_smlouvu v server.py, excelová šablona) tato verze
staví dokument od nuly přes reportlab. Podporuje nájemce fyzickou osobu i
firmu (IČO/DIČ/sídlo/zástupce), volitelnou korespondenční adresu, a u
firemního nájemce navíc pole pro řidiče (pokud je odlišný od zástupce
společnosti) včetně zmocnění. Předávací protokol je stručné záhlaví
(nájemce, vozidlo, místo a datum předání) a pod ním natvrdo vložený celý
nákres vozidla (protokol o stavu a poškození, pro vyznačení poškození) —
žádný další text/rozpis na stránce. Obrázek se mění pouze podle pole
"typ_vozidla" (osobní vozidlo / dodávka-obytný vůz / přívěs / motorka).

Nákres je statický obrázek (Erikova vlastní předloha) —
diagrams/sablony/<klíč>.png, vkládá se beze změny/oříznutí. Políčka
RZ/VIN/datum/stav km i "Příloha č. / ke smlouvě č." jsou v obrázku prázdná,
vyplňují se ručně stejně jako ostatní pole protokolu.
"""
import os


def _ensure_package(import_name, pip_name=None):
    """Auto-instaluje chybějící balíček (stejný vzor jako u lxml/svglib jinde
    v appce) — první spuštění po instalaci v1→v2 tak nevyžaduje ruční pip."""
    try:
        __import__(import_name)
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install",
                         pip_name or import_name, "--break-system-packages", "-q"])


_ensure_package("reportlab")

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, Image, HRFlowable, PageBreak, Frame, PageTemplate,
                                 Flowable, KeepTogether)
try:
    from reportlab.platypus.flowables import BalancedColumns
except ImportError:  # velmi starý reportlab — VOP pak poběží v jednom sloupci
    BalancedColumns = None
from reportlab.lib.enums import TA_LEFT
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vop_cz import VOP_CLANKY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(SCRIPT_DIR, "RX_logo.jpg")
FONT_DIR = os.path.join(SCRIPT_DIR, "fonts")
DIAGRAM_DIR = os.path.join(SCRIPT_DIR, "diagrams")
DIAGRAM_IMG_DIR = os.path.join(DIAGRAM_DIR, "sablony")

VEHICLE_DIAGRAMS = {
    "osobni": ("car", "Sedan"),
    "hatchback": ("hatchback", "Hatchback"),
    "kombi": ("kombi", "Kombi"),
    "suv": ("suv", "SUV"),
    "coupe": ("coupe", "Coupé"),
    "kabriolet": ("kabriolet", "Kabriolet"),
    "dodavka": ("van", "Dodávka / karavan"),
    "prives": ("trailer", "Přívěs"),
    "motorka": ("moto", "Motorka"),
}


def _find_diagram_image(key):
    """Statický nákres (protokol o stavu a poškození) pro daný typ vozidla —
    první nalezený formát v diagrams/sablony/<key>.*."""
    for ext in (".png", ".jpg", ".jpeg", ".pdf"):
        p = os.path.join(DIAGRAM_IMG_DIR, key + ext)
        if os.path.exists(p):
            return p
    return None


def _datum_cas(datum, cas):
    """'07.10.2026, 14:30' — čas jen pokud je vyplněn."""
    d = _cz_datum(datum)
    c = (cas or "").strip()
    return f"{d}, {c}" if (d and c) else d


def _vydan_platnost(vydan, platnost):
    """'vydáno / platnost' — chybějící hodnota se nahradí pomlčkou, nikdy 'None'."""
    v = str(vydan).strip() if vydan not in (None, "None") else ""
    p = str(platnost).strip() if platnost not in (None, "None") else ""
    if not v and not p:
        return ""
    return f"{v or '—'} / {p or '—'}"


def _cz_datum(hodnota):
    """Datum musí být ve smlouvě vždy ve formátu dd.mm.rrrr. Formulář (input
    type=\"date\") posílá ISO tvar rrrr-mm-dd — ten sem převedeme; hodnoty,
    které už jsou v jiném/česk tvaru (nebo prázdné), necháme beze změny."""
    s = (hodnota or "").strip()
    if not s:
        return s
    import re
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if not m:
        return s
    rok, mesic, den = m.groups()
    return f"{den}.{mesic}.{rok}"


class _PosMarker(Flowable):
    """Neviditelný 0×0 flowable — při vykreslení zaznamená svou absolutní
    pozici na stránce (a číslo stránky) do předaného slovníku. Používá se
    k přesnému umístění podpisového pole (DocuSeal) na vygenerovaném PDF,
    aniž by bylo nutné cokoliv v layoutu smlouvy natvrdo počítat ručně."""

    def __init__(self, sink, key):
        Flowable.__init__(self)
        self.width = 0
        self.height = 0
        self._sink = sink
        self._key = key

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        x, y = self.canv.absolutePosition(0, 0)
        self._sink[self._key] = {"page": self.canv.getPageNumber(), "x": x, "y": y}

INK = colors.HexColor("#111111")
GRAY = colors.HexColor("#6b6b6b")
LIGHT = colors.HexColor("#e6e6e6")

# --- Unicode font (základních 14 PDF fontů/Helvetica neumí českou diakritiku
#     typu ř/ě/ď/ť/ň). Liberation Sans je rozměrově kompatibilní s Arial a
#     obsahuje celou českou znakovou sadu. Fonty jsou nabalené ve fonts/,
#     aby fungovalo i na strojích bez systémového Liberation Sans (macOS).
_FONTS_READY = False


def _ensure_fonts():
    global _FONTS_READY
    if _FONTS_READY:
        return
    pdfmetrics.registerFont(TTFont("LibSans", os.path.join(FONT_DIR, "LiberationSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("LibSans-Bold", os.path.join(FONT_DIR, "LiberationSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("LibSans-Italic", os.path.join(FONT_DIR, "LiberationSans-Italic.ttf")))
    pdfmetrics.registerFont(TTFont("LibSans-BoldItalic", os.path.join(FONT_DIR, "LiberationSans-BoldItalic.ttf")))
    pdfmetrics.registerFontFamily("LibSans", normal="LibSans", bold="LibSans-Bold",
                                   italic="LibSans-Italic", boldItalic="LibSans-BoldItalic")
    _FONTS_READY = True


def _build_styles():
    _ensure_fonts()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Eyebrow", fontName="LibSans-Bold", fontSize=8.5, leading=11,
                               textColor=GRAY, spaceAfter=2))
    styles.add(ParagraphStyle("DocTitle", fontName="LibSans-Bold", fontSize=22, leading=26,
                               textColor=INK, spaceAfter=2))
    styles.add(ParagraphStyle("SectionTitle", fontName="LibSans-Bold", fontSize=10.5, leading=13,
                               textColor=INK, spaceBefore=14, spaceAfter=6))
    styles.add(ParagraphStyle("Body", fontName="LibSans", fontSize=9, leading=13, textColor=INK,
                               alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle("BodySmall", fontName="LibSans", fontSize=8, leading=11.5, textColor=GRAY,
                               alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle("Label", fontName="LibSans", fontSize=7.5, leading=10, textColor=GRAY))
    styles.add(ParagraphStyle("Value", fontName="LibSans-Bold", fontSize=9.5, leading=12, textColor=INK))
    styles.add(ParagraphStyle("FooterNote", fontName="LibSans", fontSize=7.3, leading=10.5, textColor=GRAY,
                               alignment=TA_JUSTIFY))
    return styles


def generate_smlouva_v2(osobni_data, smlouva_data, firma_data, output_path,
                         cislo_smlouvy, typ_vozidla="osobni", protokol=True, podpis_png=None,
                         vraceni=None, jen_protokol=False):
    """Vygeneruje smlouvu (str. 1) + VOP s podpisem (str. 2) + volitelně protokol.
    VOP se musí vejít na 2. stranu i s podpisovým blokem — podpis nesmí zůstat
    osamocený na další stránce. Proto zkoušíme postupně menší písmo VOP, dokud
    podpis nesedí na stejné straně, kde VOP začínají."""
    if jen_protokol:
        výsledek = _generate_smlouva_v2(osobni_data, smlouva_data, firma_data, output_path,
                                        cislo_smlouvy, typ_vozidla, True, 6.5, podpis_png,
                                        vraceni, True)
        return výsledek[0], výsledek[1]
    výsledek = None
    for vop_pt in (7.0, 6.8, 6.6, 6.5, 6.4, 6.3, 6.2, 6.1, 6.0, 5.9, 5.8, 5.7, 5.6, 5.5):
        výsledek = _generate_smlouva_v2(osobni_data, smlouva_data, firma_data, output_path,
                                        cislo_smlouvy, typ_vozidla, protokol, vop_pt, podpis_png, vraceni)
        if výsledek[2]:
            break
    return výsledek[0], výsledek[1]


from reportlab.pdfgen import canvas as _rl_canvas


class _NumberedCanvas(_rl_canvas.Canvas):
    """Canvas, který na každou stranu dopíše „Strana X / Y“ a na 1. stranu
    rámeček pro paraf nájemce (jen nájemce — pronajímatel podepisuje jinde)."""

    def __init__(self, *args, **kwargs):
        _rl_canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            _rl_canvas.Canvas.showPage(self)
        _rl_canvas.Canvas.save(self)

    def _draw_footer(self, total):
        page_w, _ = A4
        self.saveState()
        self.setFont("LibSans", 8)
        self.setFillColor(colors.HexColor("#6b6b6b"))
        self.drawCentredString(page_w / 2, 8 * mm, f"Strana {self._pageNumber} / {total}")
        if self._pageNumber == 1 and getattr(self, "_paraf", True):
            bw, bh = 34 * mm, 10 * mm
            x1 = page_w - 20 * mm
            x0 = x1 - bw
            self.setStrokeColor(colors.HexColor("#3a3a3a"))
            self.setLineWidth(0.7)
            self.rect(x0, 3.5 * mm, bw, bh, stroke=1, fill=0)
            self.setFont("LibSans", 6.5)
            self.drawString(x0 + 1.5 * mm, 3.5 * mm + bh - 3 * mm, "Paraf nájemce")
            reader = getattr(self, "_paraf_reader", None)
            if reader is not None:
                try:
                    iw, ih = reader.getSize()
                    h = 6.2 * mm
                    w = min(26 * mm, h * iw / ih)
                    self.drawImage(reader, x1 - w - 2 * mm, 4.1 * mm, width=w, height=h,
                                   mask="auto", preserveAspectRatio=True)
                except Exception:
                    pass
        self.restoreState()



def _generate_smlouva_v2(osobni_data, smlouva_data, firma_data, output_path,
                         cislo_smlouvy, typ_vozidla, protokol, vop_pt, podpis_png=None,
                         vraceni=None, jen_protokol=False):
    styles = _build_styles()
    styles.add(ParagraphStyle("VopH", fontName="LibSans-Bold", fontSize=vop_pt + 0.8, leading=(vop_pt + 0.8) * 1.25,
                               textColor=INK, spaceBefore=vop_pt * 0.9, spaceAfter=1.5))
    styles.add(ParagraphStyle("VopP", fontName="LibSans", fontSize=vop_pt, leading=vop_pt * 1.27, textColor=GRAY,
                               alignment=TA_LEFT, spaceAfter=vop_pt * 0.35))

    def field(label, value):
        return [Paragraph(label, styles["Label"]), Paragraph(value or "&nbsp;", styles["Value"])]

    def field_row(pairs, col_widths=None):
        n = len(pairs)
        cells = [[Paragraph(l, styles["Label"]), Paragraph(v or "&nbsp;", styles["Value"])] for l, v in pairs]
        tbl_data = [[c[0] for c in cells], [c[1] for c in cells]]
        if not col_widths:
            col_widths = [(170 * mm) / n] * n
        t = Table(tbl_data, colWidths=col_widths)
        t.hAlign = "LEFT"
        t.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return t

    def section_title(text):
        return Paragraph(text.upper(), styles["SectionTitle"])

    def hr(color=LIGHT, thickness=0.75, space_before=2, space_after=8):
        return HRFlowable(width="100%", thickness=thickness, color=color,
                           spaceBefore=space_before, spaceAfter=space_after)

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=18 * mm, bottomMargin=16 * mm,
                             leftMargin=20 * mm, rightMargin=20 * mm)
    # Rámec stránky má v reportlabu ve výchozím stavu vlastní vnitřní odsazení
    # (6 bodů ~ 2,3 mm) navíc k topMargin/leftMargin atd. Tabulky (field_row,
    # parties_tbl) mají šířku sloupců napevno na 170 mm (= celá šířka obsahu
    # bez marginů), takže je reportlab kreslí přesně od leftMargin — ale
    # samostatné odstavce/nadpisy (Paragraph mimo tabulku) se navíc posouvaly
    # o těch ~2,3 mm doprava kvůli onomu vnitřnímu paddingu rámce. Výsledkem
    # bylo, že text na stránce nezačínal pokaždé ze stejné pozice. Vynulováním
    # paddingu rámce (odsazení řídíme výhradně přes top/bottom/left/rightMargin
    # výše) se vše sjednotí na jednu společnou levou hranu.
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                   id="normal", leftPadding=0, rightPadding=0,
                   topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="RX", frames=[frame])])
    story = []
    _sign_pos_sink = {}

    is_firma = bool(firma_data and firma_data.get("ico"))
    cele_jmeno = (osobni_data.get("jmeno", "") + " " + osobni_data.get("prijmeni", "")).strip()
    mena = smlouva_data.get("mena", "CZK")

    # ---------- HEADER ----------
    logo_img = Image(LOGO_PATH, width=17 * mm, height=11 * mm) if os.path.exists(LOGO_PATH) else Paragraph("RX", styles["DocTitle"])
    header_tbl = Table([[logo_img, Paragraph("RX AUTO, S.R.O.", styles["Eyebrow"])]], colWidths=[20 * mm, 150 * mm])
    header_tbl.hAlign = "LEFT"
    header_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(header_tbl)
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Nájemní smlouva", styles["DocTitle"]))
    story.append(Paragraph(f"č. {cislo_smlouvy}", styles["BodySmall"]))
    story.append(hr(color=INK, thickness=1.2, space_before=8, space_after=10))

    # ---------- SMLUVNI STRANY ----------
    story.append(section_title("Smluvní strany"))
    pron_lines = [
        "<b>RX Auto, s.r.o.</b>",
        "Aviatická 1092/8, 161 00 Praha 6",
        "IČO: 06044310&nbsp;&nbsp; DIČ: CZ06044310",
        "info@rxauto.cz&nbsp;&nbsp; www.rxauto.cz",
    ]
    zastupce_jmeno = (firma_data.get("zastupce", "") or cele_jmeno) if is_firma else ""
    ridic_je_zastupce = is_firma and firma_data.get("ridic_je_zastupce", True)
    nahradni_firma = is_firma and bool(smlouva_data.get("nahradni_vozidlo"))
    if is_firma:
        dic_val = firma_data.get("dic", "") or ""
        ico_dic_line = f"IČO: {firma_data.get('ico','')}"
        if dic_val:
            ico_dic_line += f"&nbsp;&nbsp; DIČ: {dic_val}"
        naj_lines = [
            f"<b>{firma_data.get('nazev','')}</b>",
            firma_data.get("sidlo", "") or "",
            ico_dic_line,
            f"Zastoupena: {zastupce_jmeno}" if zastupce_jmeno else "",
        ]
    else:
        adresa_radek = osobni_data.get("adresa", "") or ""
        koresp = osobni_data.get("korespondencni_adresa", "") or ""
        if koresp and koresp.strip() != adresa_radek.strip():
            adresa_radek += f"<br/><font size=7 color='#6b6b6b'>Koresp. adresa: {koresp}</font>"
        datum_nar = osobni_data.get("datum_narozeni", "") or ""
        misto_nar = osobni_data.get("misto_narozeni", "") or ""
        if datum_nar and misto_nar:
            nar_radek = f"nar. {datum_nar}, {misto_nar}"
        elif datum_nar or misto_nar:
            nar_radek = f"nar. {datum_nar or misto_nar}"
        else:
            nar_radek = ""
        naj_lines = [
            f"<b>{cele_jmeno}</b>",
            nar_radek,
            adresa_radek,
            f"{smlouva_data.get('email','')}&nbsp;&nbsp; {smlouva_data.get('telefon','')}",
        ]
    parties_data = [
        [Paragraph("PRONAJÍMATEL", styles["Label"]), Paragraph("NÁJEMCE", styles["Label"])],
        [Paragraph("<br/>".join(x for x in pron_lines if x), styles["Body"]),
         Paragraph("<br/>".join(x for x in naj_lines if x), styles["Body"])],
    ]
    parties_tbl = Table(parties_data, colWidths=[85 * mm, 85 * mm])
    parties_tbl.hAlign = "LEFT"
    parties_tbl.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 0), ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(parties_tbl)

    # Řidič / držitel dokladů (OP + ŘP) — vždy zobrazeno: u fyzické osoby je to
    # přímo nájemce, u firmy je to osoba fyzicky přebírající vozidlo (může,
    # ale nemusí, být zástupce společnosti).
    story.append(Spacer(1, 6))
    if is_firma:
        story.append(Paragraph(
            "ŘIDIČ" if (ridic_je_zastupce or nahradni_firma) else "ŘIDIČ (odlišný od zástupce společnosti)",
            styles["Label"]))
        story.append(Paragraph(f"<b>{cele_jmeno}</b>", styles["Body"]))
        story.append(Spacer(1, 3))
    story.append(field_row([
        ("ČÍSLO OP / PASU", osobni_data.get("cislo_op", "")),
        ("VYDÁN / PLATNOST", _vydan_platnost(osobni_data.get("datum_vydani_op"), osobni_data.get("platnost_op"))),
        ("ČÍSLO ŘP", osobni_data.get("cislo_rp", "")),
        ("VYDÁN / PLATNOST", _vydan_platnost(osobni_data.get("datum_vydani_rp"), osobni_data.get("platnost_rp"))),
    ]))
    nahradni = bool(smlouva_data.get("nahradni_vozidlo"))
    if is_firma and not ridic_je_zastupce and not nahradni:
        story.append(field_row([
            ("ZMOCNĚN JEDNAT NA ZÁKLADĚ", firma_data.get("zmocneni", "")),
        ], col_widths=[170 * mm]))

    story.append(hr())

    # ---------- VOZIDLO + DOBA NAJMU ----------
    story.append(section_title("Předmět nájmu a doba trvání"))
    najezd = smlouva_data.get("sjednany_najezd", "")
    interval_n = smlouva_data.get("interval_najezdu", "rok")
    story.append(field_row([
        ("VOZIDLO", smlouva_data.get("vozidlo", "")),
        ("PALIVO", smlouva_data.get("palivo", "") or ""),
        ("SJEDNANÝ NÁJEZD", (f"{najezd} km / {interval_n}" if str(najezd).replace(" ", "").isdigit() else str(najezd)) if najezd else ""),
    ], col_widths=[88 * mm, 26 * mm, 56 * mm]))
    flexi = bool(smlouva_data.get("flexi"))
    po_dnech = smlouva_data.get("interval_ceny") == "denně"
    if flexi:
        konec_txt, delka_txt = "FLEXI — neurčeno", f"Flexi (po {'dnech' if po_dnech else 'měsících'})"
    else:
        konec_txt = _cz_datum(smlouva_data.get("datum_konce", ""))
        delka_txt = f"{smlouva_data.get('pocet_intervalu','')} {'dní' if po_dnech else 'měsíců'}"
    story.append(field_row([
        ("DATUM ZAČÁTKU", _datum_cas(smlouva_data.get("datum_zacatku", ""), smlouva_data.get("cas_predani", ""))),
        ("DATUM KONCE", konec_txt),
        ("DÉLKA", delka_txt),
    ], col_widths=[56 * mm] * 3))
    if flexi:
        story.append(Paragraph(
            "Flexi: doba nájmu není předem stanovena, datum vrácení vozidla není známo. "
            f"Nájemné se účtuje po jednotkách ({'za každý den' if po_dnech else 'za každý měsíc'}) "
            "až do skutečného vrácení vozidla.", styles["BodySmall"]))
    if nahradni:
        if is_firma:
            story.append(Paragraph(
                "<b>NÁHRADNÍ VOZIDLO.</b> Jedná se o náhradní vozidlo. Zplnomocnění zástupce společnosti "
                "se nevyžaduje — smlouvu i předávací protokol podepisuje pouze řidič "
                f"(<b>{cele_jmeno}</b>); podpis zástupce společnosti není potřeba.", styles["Body"]))
        else:
            story.append(Paragraph("<b>NÁHRADNÍ VOZIDLO.</b> Jedná se o náhradní vozidlo.", styles["Body"]))
    story.append(hr())

    # ---------- CENA / PLATBY ----------
    story.append(section_title("Nájemné a platební podmínky"))
    cena_raw = smlouva_data.get("cena", "")
    cena_dph_mode = (smlouva_data.get("cena_dph") or "bez_dph").strip().lower()
    try:
        cena_num = float(str(cena_raw).replace(",", ".").replace(" ", ""))
    except (ValueError, TypeError):
        cena_num = None
    if cena_num is not None:
        if cena_dph_mode == "s_dph":
            cena_s_dph_num = cena_num
            cena_bez_dph_num = cena_num / 1.21
        else:
            cena_bez_dph_num = cena_num
            cena_s_dph_num = cena_num * 1.21
        cena_bez_dph = f"{cena_bez_dph_num:,.0f}".replace(",", " ")
        cena_s_dph = f"{cena_s_dph_num:,.0f}".replace(",", " ")
    else:
        cena_bez_dph = ""
        cena_s_dph = ""
    interval_txt = "měsíčně" if smlouva_data.get("interval_ceny") == "měsíčně" else "denně"
    jistina = smlouva_data.get("jistina", "")
    story.append(field_row([
        ("NÁJEMNÉ BEZ DPH", f"{cena_bez_dph} {mena} / {interval_txt}" if cena_bez_dph else ""),
        ("NÁJEMNÉ VČ. DPH 21%", f"{cena_s_dph} {mena} / {interval_txt}" if cena_s_dph else ""),
        ("JISTINA", f"{jistina} {mena}" if jistina else ""),
    ], col_widths=[56 * mm] * 3))
    story.append(Paragraph(
        "V ceně nájmu je zahrnuto: daň silniční, rozhlasový poplatek, zákonné pojištění, "
        "havarijní pojištění se spoluúčastí 10&nbsp;% min.&nbsp;10&nbsp;000&nbsp;Kč, pojištění "
        "čelního skla se spoluúčastí 1&nbsp;000&nbsp;Kč, sezónní pneumatiky, nonstop silniční asistence (tel.&nbsp;1224).",
        styles["BodySmall"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Cena za kilometr nad sjednaný rámec: 9,- Kč + 21 % DPH.", styles["BodySmall"]))
    story.append(hr())

    # ---------- PROHLASENI ----------
    story.append(section_title("Ujednání"))
    story.append(Paragraph(
        "Nájemce potvrzuje, že obdržel kopii této Smlouvy, že si Smlouvu a Všeobecné obchodní "
        "podmínky přečetl, a že s nimi souhlasí. Nájemce potvrzuje stav vozidla, uvedený ve Smlouvě "
        "a předávacím protokolu. V případě platby kreditní kartou Nájemce potvrzuje svým podpisem "
        "souhlas s inkasem celé částky, včetně všech škod, způsobených na vozidle během doby trvání "
        "Pronájmu a dále správních poplatků, pokut a dodatečných poplatků. Nájemce přebírá "
        "odpovědnost za všechny dopravní přestupky, způsobené s vozidlem po dobu trvání Pronájmu.",
        styles["BodySmall"]))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Všeobecné obchodní podmínky (VOP) jsou nedílnou součástí nájemní smlouvy uzavřené mezi "
        "RX Auto, s.r.o. se sídlem Aviatická 8, 161 00 Praha 6, IČO: 06044310 DIČ: CZ06044310, "
        "(dále jen pronajímatel) a nájemcem o pronájmu vozidla.",
        styles["FooterNote"]))

    # ---------- VOP (2. strana) ----------
    story.append(PageBreak())
    story.append(_PosMarker(_sign_pos_sink, "vop"))
    story.append(Paragraph(f"Všeobecné obchodní podmínky <font size=8 color='#6b6b6b'>· k nájemní smlouvě č. {cislo_smlouvy}</font>",
                           styles["SectionTitle"]))
    vop_flow = []
    for nadpis, odstavce in VOP_CLANKY:
        vop_flow.append(Paragraph(nadpis, styles["VopH"]))
        for o in odstavce:
            vop_flow.append(Paragraph(o, styles["VopP"]))
    if BalancedColumns is not None:
        story.append(BalancedColumns(vop_flow, nCols=2, innerPadding=5 * mm, needed=40 * mm))
    else:
        story.extend(vop_flow)

    # ---------- PODPISY ----------
    story.append(Spacer(1, 3 * mm))
    najemce_podpis_label = (f"Nájemce — řidič: {cele_jmeno}"
                            if (is_firma and nahradni) else "Nájemce")
    import base64 as _b64
    from io import BytesIO as _BytesIO
    _raz_path = os.path.join(SCRIPT_DIR, "razitko_podpis.png")
    _podpis_raw = None
    if podpis_png:
        try:
            _podpis_raw = _b64.b64decode(podpis_png.split(",", 1)[-1])
        except Exception:
            _podpis_raw = None

    def _mk_razitko(h_mm, maxw_mm=55):
        if not os.path.exists(_raz_path):
            return ""
        try:
            _pr = Image(_raz_path)
            w = min(maxw_mm * mm, h_mm * mm * _pr.imageWidth / _pr.imageHeight)
            img = Image(_raz_path, width=w, height=h_mm * mm)
            img.hAlign = "LEFT"
            return img
        except Exception:
            return ""

    def _mk_podpis(h_mm, maxw_mm=70):
        if not _podpis_raw:
            return ""
        try:
            _pr = Image(_BytesIO(_podpis_raw))
            w = min(maxw_mm * mm, h_mm * mm * _pr.imageWidth / _pr.imageHeight)
            img = Image(_BytesIO(_podpis_raw), width=w, height=h_mm * mm)
            img.hAlign = "LEFT"
            return img
        except Exception:
            return ""

    razitko_img = _mk_razitko(15)
    podpis_img = _mk_podpis(14)
    sign_tbl = Table([
        [razitko_img, podpis_img],
        [f"V Praze dne {_cz_datum(smlouva_data.get('datum_zacatku',''))}", ""],
        [hr(space_before=0, space_after=0), hr(space_before=0, space_after=0)],
        [Paragraph("Pronajímatel", styles["Label"]), Paragraph(najemce_podpis_label, styles["Label"])],
    ], colWidths=[85 * mm, 85 * mm], rowHeights=[15 * mm if (podpis_img or razitko_img) else 10 * mm, 6 * mm, None, 6 * mm])
    sign_tbl.hAlign = "LEFT"
    sign_tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                  ("VALIGN", (0, 0), (1, 0), "BOTTOM")]))
    # _sign_pos_sink["top"] zachytí přesnou absolutní pozici (stránka, x, y)
    # horního okraje této tabulky na vykresleném PDF — z ní níže dopočítáme
    # umístění podpisového pole DocuSeal přímo nad podpisovou čárou nájemce.
    # KeepTogether zajistí, že marker a tabulka vždy skončí na stejné
    # stránce (pokud by se tabulka celá nevešla, přesune se na další
    # stránku i s markerem, takže zachycené číslo stránky zůstane správné).
    story.append(KeepTogether([_PosMarker(_sign_pos_sink, "top"), sign_tbl]))

    # ---------- PROTOKOL ----------
    _protokol_start = len(story) + 1   # +1 = přeskočit PageBreak při jen_protokol
    if protokol:
        story.append(PageBreak())
        story.append(header_tbl)
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Předávací protokol", styles["DocTitle"]))
        story.append(Paragraph(f"ke smlouvě č. {cislo_smlouvy}", styles["BodySmall"]))
        story.append(hr(color=INK, thickness=1.2, space_before=4, space_after=6))

        story.append(field_row([
            ("NÁJEMCE", firma_data.get("nazev") if is_firma else cele_jmeno),
            ("VOZIDLO", smlouva_data.get("vozidlo", "")),
        ], col_widths=[85 * mm, 85 * mm]))
        if is_firma and nahradni:
            story.append(Paragraph(f"Náhradní vozidlo — protokol podepisuje pouze řidič ({cele_jmeno}).", styles["BodySmall"]))
        story.append(hr(space_before=2, space_after=4))

        # ---- Nákres vozidla (protokol o stavu a poškození) — natvrdo vložený
        # obrázek předlohy (celý list beze změny), v každé sekci (předání /
        # vrácení) napravo; nalevo od něj údaje té sekce, poznámky a
        # podpisový řádek. Obrázek se mění pouze podle typu vozidla
        # (VEHICLE_DIAGRAMS níže).
        diagram_key, diagram_label = VEHICLE_DIAGRAMS.get(typ_vozidla, VEHICLE_DIAGRAMS["osobni"])
        diagram_path = _find_diagram_image(diagram_key)

        LEFT_W, RIGHT_W = 74 * mm, 96 * mm

        def _nakres_raw(data_url):
            if not data_url:
                return None
            try:
                return _b64.b64decode(data_url.split(",", 1)[-1])
            except Exception:
                return None

        def _diagram_cell(custom_raw=None):
            if custom_raw:
                try:
                    probe = Image(_BytesIO(custom_raw))
                    w = RIGHT_W
                    h = w * probe.imageHeight / probe.imageWidth
                    return [Image(_BytesIO(custom_raw), width=w, height=h)]
                except Exception:
                    pass
            if not diagram_path:
                return [Paragraph("(obrázek nenalezen)", styles["BodySmall"])]
            probe = Image(diagram_path)
            w = RIGHT_W
            h = w * probe.imageHeight / probe.imageWidth
            return [Image(diagram_path, width=w, height=h)]

        def _section(title, fields, sign_labels=None, poskozeni_text="", sign_imgs=None, diagram_raw=None):
            sign_labels = sign_labels or ("Za nájemce", "Za pronajímatele")
            left = []
            for label, value in fields:
                left.append(Paragraph(label, styles["Label"]))
                left.append(Paragraph(value or "&nbsp;", styles["Value"]))
                left.append(Spacer(1, 2))
            left.append(Spacer(1, 2))
            left.append(Paragraph("POŠKOZENÍ", styles["Label"]))
            if poskozeni_text:
                left.append(Paragraph(poskozeni_text, styles["Value"]))
            for _ in range(1 if poskozeni_text else 2):
                left.append(Spacer(1, 5.5 * mm))
                left.append(hr(color=LIGHT, thickness=0.6, space_before=0, space_after=0))
            for i, lbl in enumerate(sign_labels):
                img = (sign_imgs[i] if sign_imgs and i < len(sign_imgs) else "") or ""
                if img:
                    left.append(Spacer(1, 1 * mm))
                    left.append(img)
                else:
                    left.append(Spacer(1, 4.5 * mm))
                left.append(hr(color=INK, thickness=0.8, space_before=0, space_after=2))
                left.append(Paragraph(lbl, styles["Label"]))

            tbl = Table([[left, _diagram_cell(diagram_raw)]], colWidths=[LEFT_W, RIGHT_W])
            tbl.hAlign = "LEFT"
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 10),
                ("LEFTPADDING", (1, 0), (1, -1), 0), ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            return [section_title(title), tbl]

        stav_tachometru_predani = smlouva_data.get("stav_tachometru_predani", "")
        _predani_imgs = (_mk_podpis(8, 44), _mk_razitko(9, 44))
        story.extend(_section("Předání vozidla", [
            ("MÍSTO PŘEDÁNÍ", smlouva_data.get("misto_predani", "")),
            ("DATUM A ČAS PŘEDÁNÍ", _datum_cas(smlouva_data.get("datum_zacatku", ""), smlouva_data.get("cas_predani", ""))),
            ("PALIVO", smlouva_data.get("palivo", "") or ""),
            ("STAV KILOMETRŮ", f"{stav_tachometru_predani} km" if stav_tachometru_predani else ""),
            ("STAV NÁDRŽE", smlouva_data.get("stav_nadrze", "") or ""),
        ], sign_imgs=_predani_imgs, poskozeni_text=smlouva_data.get("poskozeni_predani", "") or "",
           diagram_raw=_nakres_raw(smlouva_data.get("poskozeni_nakres"))))
        story.append(Spacer(1, 4 * mm))
        vr = vraceni or {}
        vr_km = vr.get("km_vraceni")
        story.extend(_section("Vrácení vozidla", [
            ("KDO VRACÍ", vr.get("kdo_vraci", "") or ""),
            ("MÍSTO VRÁCENÍ", vr.get("misto_vraceni") or smlouva_data.get("misto_vraceni", "")),
            ("DATUM VRÁCENÍ", _cz_datum(vr.get("datum_vraceni", "")) if vr.get("datum_vraceni") else ""),
            ("STAV KILOMETRŮ", f"{vr_km} km" if vr_km else ""),
            ("STAV NÁDRŽE", vr.get("nadrz_vraceni", "") or ""),
        ], poskozeni_text=vr.get("poskozeni_text", ""),
           diagram_raw=_nakres_raw(vr.get("poskozeni_nakres"))))

    if jen_protokol:
        story = story[_protokol_start:]
        canvas_cls = type("_NCBezParafu", (_NumberedCanvas,), {"_paraf": False})
    elif _podpis_raw:
        from reportlab.lib.utils import ImageReader
        try:
            _reader = ImageReader(_BytesIO(_podpis_raw))
        except Exception:
            _reader = None
        canvas_cls = type("_NCParaf", (_NumberedCanvas,), {"_paraf_reader": _reader})
    else:
        canvas_cls = _NumberedCanvas
    doc.build(story, canvasmaker=canvas_cls)

    # Umístění podpisového pole nájemce (pro DocuSeal) — odvozeno z reálné
    # vykreslené pozice horního okraje podpisové tabulky (_sign_pos_sink).
    # Prázdné místo pro podpis je v pravém sloupci (Nájemce) řádky 0+1
    # (10 mm + 6 mm) nad podpisovou čárou a popiskem "Nájemce".
    podpis_pozice = None
    pos = _sign_pos_sink.get("top")
    if pos:
        page_w, page_h = A4
        col2_x = doc.leftMargin + 85 * mm
        col_w = 85 * mm
        blank_h = 16 * mm  # 10 mm (prázdný řádek) + 6 mm (řádek s datem)
        top_y = pos["y"]
        podpis_pozice = {
            "page": pos["page"],
            "x": col2_x / page_w,
            "y": (page_h - top_y) / page_h,
            "w": col_w / page_w,
            "h": blank_h / page_h,
        }

    # podpis nesmí být osamocený: musí být na téže straně, kde začínají VOP
    vop_pos = _sign_pos_sink.get("vop")
    podpis_ok = bool(pos and vop_pos and pos["page"] == vop_pos["page"])
    return output_path, podpis_pozice, podpis_ok


def generate_vyuctovani(data, output_path):
    """Jednostránkové PDF 'Vyúčtování vrácení vozidla'.

    data: dict s klíči jmeno, vozidlo, cislo_smlouvy, datum_zacatku, datum_vraceni,
    kdo_vraci, km_predani, km_vraceni, najeto, povoleno_km, prekroceni_km,
    doplatek_bez, doplatek_s, nadrz_predani, nadrz_vraceni, poznamky (list textů).
    Číselné hodnoty mohou být None — řádek se pak vynechá/nechá prázdný.
    """
    _ensure_fonts()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=18 * mm, bottomMargin=16 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm)
    styles = {
        "T": ParagraphStyle("T", fontName="LibSans-Bold", fontSize=16, leading=20, spaceAfter=2),
        "S": ParagraphStyle("S", fontName="LibSans", fontSize=8, leading=11, textColor=colors.HexColor("#6b6b6b")),
        "L": ParagraphStyle("L", fontName="LibSans-Bold", fontSize=6.5, leading=9,
                            textColor=colors.HexColor("#8a8a8a")),
        "V": ParagraphStyle("V", fontName="LibSans", fontSize=9.5, leading=13),
        "B": ParagraphStyle("B", fontName="LibSans", fontSize=8.5, leading=12),
        "H": ParagraphStyle("H", fontName="LibSans-Bold", fontSize=10, leading=13,
                            spaceBefore=8, spaceAfter=3),
    }

    def _fmt(x, suff=""):
        if x is None or x == "":
            return ""
        if isinstance(x, float) and x == int(x):
            x = int(x)
        if isinstance(x, (int, float)):
            return f"{x:,.0f}".replace(",", " ") + suff
        return f"{x}{suff}"

    story = [
        Paragraph("Vyúčtování vrácení vozidla", styles["T"]),
        Paragraph(f"ke smlouvě č. {data.get('cislo_smlouvy','')} · vygenerováno {data.get('vygenerovano','')}",
                  styles["S"]),
        HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#1a1a1a"), spaceBefore=4, spaceAfter=8),
    ]

    def row(pairs):
        cells = []
        for lbl, val in pairs:
            cells.append([Paragraph(lbl, styles["L"]), Paragraph(str(val) or "&nbsp;", styles["V"])])
        t = Table([[c for c in cells]], colWidths=[170 * mm / len(cells)] * len(cells))
        t.hAlign = "LEFT"
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        inner = []
        for lbl, val in pairs:
            inner.append(Table([[Paragraph(lbl, styles["L"])], [Paragraph(str(val) if val not in (None, "") else "&nbsp;", styles["V"])]],
                               colWidths=[170 * mm / len(pairs)],
                               style=TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 0)])))
        t = Table([inner], colWidths=[170 * mm / len(pairs)] * len(pairs))
        t.hAlign = "LEFT"
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                               ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    story.append(row([("NÁJEMCE", data.get("jmeno", "")), ("VOZIDLO", data.get("vozidlo", ""))]))
    story.append(row([("DATUM PŘEDÁNÍ", data.get("datum_zacatku", "")),
                      ("DATUM VRÁCENÍ", data.get("datum_vraceni", "")),
                      ("VOZIDLO VRACÍ", data.get("kdo_vraci", "") or "")]))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#d9d9d9"), spaceBefore=4, spaceAfter=6))

    story.append(Paragraph("Kilometry", styles["H"]))
    story.append(row([("STAV PŘI PŘEDÁNÍ", _fmt(data.get("km_predani"), " km")),
                      ("STAV PŘI VRÁCENÍ", _fmt(data.get("km_vraceni"), " km")),
                      ("NAJETO", _fmt(data.get("najeto"), " km"))]))
    story.append(row([("POVOLENÝ NÁJEZD ZA DOBU NÁJMU", _fmt(data.get("povoleno_km"), " km")),
                      ("PŘEKROČENÍ", _fmt(data.get("prekroceni_km"), " km")),
                      ("SAZBA", "9 Kč/km + 21 % DPH")]))
    if data.get("doplatek_bez") is not None:
        story.append(row([("DOPLATEK ZA KILOMETRY BEZ DPH", _fmt(round(data["doplatek_bez"]), " Kč")),
                          ("DOPLATEK ZA KILOMETRY VČ. DPH", _fmt(round(data["doplatek_s"]), " Kč")), ("", "")]))

    story.append(Paragraph("Palivo", styles["H"]))
    story.append(row([("NÁDRŽ PŘI PŘEDÁNÍ", data.get("nadrz_predani", "") or "—"),
                      ("NÁDRŽ PŘI VRÁCENÍ", data.get("nadrz_vraceni", "") or "—"), ("", "")]))

    mena = data.get("mena") or "Kč"
    if data.get("poskozeni"):
        story.append(Paragraph("Poškození", styles["H"]))
        story.append(row([("POPIS", data.get("poskozeni_popis", "") or "dle předávacího protokolu"),
                          ("NÁHRADA ŠKODY", _fmt(round(data["poskozeni"]), f" {mena}"))]))
    if data.get("celkem_k_uhrade"):
        story.append(Spacer(1, 3 * mm))
        story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor("#1a1a1a"), spaceBefore=2, spaceAfter=4))
        story.append(Paragraph(f"<b>CELKEM K ÚHRADĚ: {_fmt(round(data['celkem_k_uhrade']), ' ' + mena)}</b>", styles["V"]))

    for t in data.get("poznamky", []):
        story.append(Paragraph("• " + t, styles["B"]))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "Toto vyúčtování je podkladem pro konečnou fakturaci. Případné škody, pokuty a poplatky dle "
        "smlouvy a VOP se účtují samostatně.", styles["S"]))
    story.append(Spacer(1, 14 * mm))
    sign = Table([
        [HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#1a1a1a")),
         HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#1a1a1a"))],
        [Paragraph("Za nájemce", styles["L"]), Paragraph("Za pronajímatele", styles["L"])],
    ], colWidths=[80 * mm, 80 * mm])
    sign.hAlign = "LEFT"
    sign.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 10)]))
    story.append(sign)

    doc.build(story)
    return output_path
