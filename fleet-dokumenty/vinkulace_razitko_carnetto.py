#!/usr/bin/env python3
"""Orazítkování žádostí o vinkulaci (VWFS/ŠkoFIN, Autocentrum Jičín) pro flotilu Carnetto u Generali.

Doplní do pole "žádá tímto" údaje Generali České pojišťovny a vloží razítko+podpis Carnetto RX
vlevo dole (stejná pozice jako dříve odeslané vinkulace Herrmannovi).

Použití: python3 vinkulace_razitko_carnetto.py <razitko.png> <out_dir> <in1.pdf> [in2.pdf ...]
Razítko (obsahuje podpis) se NEcommituje – drží se v data/razitko_carnetto.png.
"""
import io
import os
import sys

from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
POJISTOVNA = [
    "Generali Česká pojišťovna a.s.",
    "Spálená 75/16, 110 00 Praha 1",
    "IČO: 45272956",
]
TEXT_X, TEXT_Y, TEXT_STEP = 200, 494, 13
# Pozice/velikost razítka v bodech (lze přepsat env STAMP_X/STAMP_Y/STAMP_H podle ořezu razítka)
STAMP_X = float(os.environ.get("STAMP_X", 3))
STAMP_Y = float(os.environ.get("STAMP_Y", 65))
STAMP_H = float(os.environ.get("STAMP_H", 89.05))


def overlay(w, h, stamp):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setFont("DejaVu", 8)
    for i, line in enumerate(POJISTOVNA):
        c.drawString(TEXT_X, TEXT_Y - i * TEXT_STEP, line)
    img = ImageReader(stamp)
    iw, ih = img.getSize()
    c.drawImage(img, STAMP_X, STAMP_Y, width=STAMP_H * iw / ih, height=STAMP_H, mask="auto")
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def main():
    stamp, out_dir, *files = sys.argv[1:]
    pdfmetrics.registerFont(TTFont("DejaVu", FONT))
    os.makedirs(out_dir, exist_ok=True)
    for f in files:
        r = PdfReader(f)
        w = PdfWriter()
        for n, p in enumerate(r.pages):
            if n == 0:
                box = p.mediabox
                p.merge_page(overlay(float(box.width), float(box.height), stamp))
            w.add_page(p)
        out = os.path.join(out_dir, os.path.basename(f))
        with open(out, "wb") as fh:
            w.write(fh)
        print(out)


if __name__ == "__main__":
    main()
