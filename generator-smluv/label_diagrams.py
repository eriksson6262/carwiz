# -*- coding: utf-8 -*-
"""Přidá do rohů nákresů vozidel (diagrams/sablony/*.png) malé šedé popisky
LEVÝ BOK / PRAVÝ BOK / PŘEDEK / ZADEK / POHLED SHORA.
Spouštět po každém přegenerování šablon (make_body_types.py je přepíše bez popisků)."""
import os
from PIL import Image, ImageDraw, ImageFont

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams", "sablony")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if not os.path.exists(FONT):  # macOS fallback
    for c in ("/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(c): FONT = c; break
S = 1.4  # šablony jsou 2800x1980 = 1.4x layout 2000x1414
# (x, y) levého horního rohu panelu v souřadnicích 2000x1414 + text
LABELS = [
    (62, 53, "LEVÝ BOK"),
    (1327, 53, "PŘEDEK"),
    (62, 497, "PRAVÝ BOK"),
    (1327, 497, "ZADEK"),
    (62, 940, "POHLED SHORA · PŘEDEK VLEVO"),
]

def label(path):
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, int(21 * S))
    for x, y, t in LABELS:
        d.text((int((x + 14) * S), int((y + 9) * S)), t, fill=(150, 150, 150), font=f)
    im.save(path)
    print("labeled", os.path.basename(path))

if __name__ == "__main__":
    for k in ("car", "hatchback", "kombi", "suv", "coupe", "kabriolet", "van", "trailer", "moto"):
        p = os.path.join(D, k + ".png")
        if os.path.exists(p): label(p)
