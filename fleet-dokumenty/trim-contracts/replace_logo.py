#!/usr/bin/env python3
"""Nahradí logo v záhlaví PDF smluv za jiné logo (zachová pozici a výšku).

Použití:
    python3 replace_logo.py <src_dir> <dst_dir> <path_to_new_logo.png>

Detekce starého loga: obrázek v levém horním rohu (x<40, y<40), širší než 100px,
nižší než 100px. Zachová výšku, šířka dopočítána podle poměru stran nového loga.
"""

import pymupdf as fitz
import os
import sys
import glob


def get_logo_ratio(logo_path):
    """Vrátí poměr šířka/výška obrázku."""
    doc = fitz.open(logo_path)
    page = doc[0] if doc.page_count else None
    if page is None:
        pix = fitz.Pixmap(logo_path)
        ratio = pix.width / pix.height
        pix = None
        doc.close()
        return ratio
    rect = page.rect
    doc.close()
    return rect.width / rect.height


def replace_logo(src, dst, new_logo_path, ratio):
    doc = fitz.open(src)
    replacements = 0
    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            try:
                bbox = page.get_image_bbox(img)
            except Exception:
                continue
            # Logo v záhlaví: levý horní roh, šířka >100px, výška <100px
            if bbox.x0 < 40 and bbox.y0 < 40 and bbox.width > 100 and bbox.height < 100:
                # Vymaž staré logo bílým obdélníkem
                page.draw_rect(bbox, color=None, fill=(1, 1, 1))
                # Vlož nové logo, zachovej výšku, šířku dopočítej
                target_h = bbox.height
                target_w = target_h * ratio
                new_rect = fitz.Rect(bbox.x0, bbox.y0, bbox.x0 + target_w, bbox.y0 + target_h)
                page.insert_image(new_rect, filename=new_logo_path, keep_proportion=True)
                replacements += 1
    doc.save(dst, garbage=4, deflate=True, clean=True)
    doc.close()
    return replacements


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]
    new_logo = sys.argv[3]

    if not os.path.isfile(new_logo):
        print(f"Logo nenalezeno: {new_logo}")
        sys.exit(1)

    os.makedirs(dst_dir, exist_ok=True)
    ratio = get_logo_ratio(new_logo)
    print(f"Poměr nového loga (š/v): {ratio:.3f}")

    files = sorted(glob.glob(f"{src_dir}/*.pdf"))
    total = 0
    errs = 0
    for src in files:
        name = os.path.basename(src)
        dst = os.path.join(dst_dir, name)
        try:
            n = replace_logo(src, dst, new_logo, ratio)
            total += n
            print(f"  {name}: {n}")
        except Exception as e:
            errs += 1
            print(f"ERR {name}: {e}")
    print(f"\n=== Celkem {total} log nahrazeno, {errs} chyb, ve {len(files)} souborech ===")
