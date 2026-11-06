"""Sjednocení dlaždic aut pro web (stejná velikost jako fotky Škoda).

Dlaždice 1280×744, bílé pozadí; auto (bbox nebílých pixelů) zmenšené/zvětšené tak, aby mělo
57 % šířky, max. 48 % výšky, vodorovně na střed, spodek kol v 80 % výšky.
Použití: python3 normalizuj_dlazdici.py vstup.webp vystup.webp
"""
import sys
from PIL import Image, ImageChops

TW, TH = 1280, 744
SIRKA, VYSKA, SPODEK, PRAH = 0.57, 0.48, 0.80, 238


def normalizuj(src, dst):
    im = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im).convert("RGB")
    # pixel je „auto“, když aspoň jeden kanál <= PRAH
    r, g, b = [c.point(lambda v: 255 if v <= PRAH else 0) for c in im.split()]
    maska = ImageChops.lighter(ImageChops.lighter(r, g), b)
    box = maska.getbbox()
    auto = im.crop(box)
    bw, bh = auto.size
    s = min(SIRKA * TW / bw, VYSKA * TH / bh)
    dw, dh = round(bw * s), round(bh * s)
    auto = auto.resize((dw, dh), Image.LANCZOS)
    out = Image.new("RGB", (TW, TH), (255, 255, 255))
    out.paste(auto, ((TW - dw) // 2, round(SPODEK * TH - dh)))
    out.save(dst, "WEBP", quality=95)
    return box, (dw, dh)


if __name__ == "__main__":
    print(normalizuj(sys.argv[1], sys.argv[2]))
