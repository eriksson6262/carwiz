#!/usr/bin/env python3
"""Nahradí všechny výskyty "RX Auto ..." za "Carnetto RX, s.r.o." v PDF.
Používá PyMuPDF redact anotace, aby původní text byl skutečně smazán."""

import pymupdf as fitz
import os
import sys
import glob

# Od nejdelší po nejkratší (důležité pro správné matching)
REPLACEMENTS = [
    ("RX Auto, s.r.o. (Carwiz)", "Carnetto RX, s.r.o. (Carwiz)"),
    ("RX Auto, s.r.o (Carwiz)", "Carnetto RX, s.r.o. (Carwiz)"),
    ("RX Auto SK, s.r.o.", "Carnetto RX, s.r.o."),
    ("RX Auto SK s.r.o.", "Carnetto RX, s.r.o."),
    ("RX Auto, s.r.o.", "Carnetto RX, s.r.o."),
    ("RX Auto s.r.o.", "Carnetto RX, s.r.o."),
    ("RX Auto, s.r.o", "Carnetto RX, s.r.o"),
    ("RX Auto", "Carnetto RX, s.r.o."),
]

def replace_in_pdf(src, dst):
    doc = fitz.open(src)
    total = 0
    for page in doc:
        # Projdeme patterns od nejdelší - najdeme rects + font info ze spans
        # Pro každý výskyt uložíme (rect, new_text, font, size, color)
        replacements_to_do = []
        covered_rects = []

        # Zjistíme font+size per span
        blocks = page.get_text("dict")["blocks"]
        all_spans = []
        for b in blocks:
            if "lines" not in b: continue
            for l in b["lines"]:
                for s in l["spans"]:
                    all_spans.append(s)

        for old, new in REPLACEMENTS:
            rects = page.search_for(old)
            for rect in rects:
                # Přeskočit překryvy s delším matchem
                skip = any(rect.intersects(cr) for cr in covered_rects)
                if skip: continue

                # Najdi span co obsahuje tento rect (pro font)
                font = "Helvetica"
                size = 7
                color = 0
                for s in all_spans:
                    sb = fitz.Rect(s["bbox"])
                    if sb.contains(rect) or sb.intersects(rect):
                        font = s["font"]
                        size = s["size"]
                        color = s["color"]
                        break

                covered_rects.append(rect)
                replacements_to_do.append({
                    "rect": rect, "new": new,
                    "font": font, "size": size, "color": color
                })

        # 1. Přidáme redact annots (bílé pozadí, text bude smazán)
        for r in replacements_to_do:
            page.add_redact_annot(r["rect"], fill=(1, 1, 1))

        # 2. Aplikujeme redactions (smaže původní text)
        page.apply_redactions()

        # 3. Napíšeme nový text na místo
        for r in replacements_to_do:
            rect = r["rect"]
            is_bold = "Bold" in r["font"] or "-B" in r["font"] or r["font"].endswith("B")
            pdf_font = "Helvetica-Bold" if is_bold else "Helvetica"
            c = r["color"]
            rgb = (((c >> 16) & 0xFF) / 255, ((c >> 8) & 0xFF) / 255, (c & 0xFF) / 255)
            # Pokud je nový text delší, zobrazíme celý tím že rozšíříme oblast (jen draw text - nemusí se vlézt do bboxu)
            page.insert_text(
                (rect.x0, rect.y1 - 1.5),
                r["new"],
                fontsize=r["size"],
                fontname=pdf_font,
                color=rgb,
            )
            total += 1

    doc.save(dst, garbage=4, deflate=True, clean=True)
    doc.close()
    return total


if __name__ == "__main__":
    src_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/Trimmed"
    dst_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/renamed"
    os.makedirs(dst_dir, exist_ok=True)

    files = sorted(glob.glob(f"{src_dir}/Smlouva_*.pdf"))
    total = 0
    errs = 0
    for src in files:
        name = os.path.basename(src)
        dst = os.path.join(dst_dir, name)
        try:
            n = replace_in_pdf(src, dst)
            total += n
            print(f"  {name}: {n}")
        except Exception as e:
            errs += 1
            print(f"ERR {name}: {e}")
    print(f"\n=== Celkem {total} nahrazení, {errs} chyb, ve {len(files)} souborech ===")
