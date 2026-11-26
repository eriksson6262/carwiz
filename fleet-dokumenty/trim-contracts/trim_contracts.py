#!/usr/bin/env python3
"""Ořízne PDF smlouvu: zachová podpisové stránky + předávací protokol,
vyhodí VOP a marketingový souhlas."""

import pymupdf as fitz
import unicodedata
import os
import sys
import glob
import hashlib

def norm(s):
    return unicodedata.normalize("NFC", s)

# Patterny pro klasifikaci stránek
DROP_PATTERNS = [
    "General Terms and Conditions",
    "Marketing consent",
    "souhlas se zpracováním osobních údajů pro marketingové",
]

KEEP_PATTERNS = [
    "Nájemní smlouva",
    "Nájomná zmluva",
    "Rental contract",
    "Nájemce byl informován",
    "Nájomca bol informovaný",
    "Poškození před pronájmem",
    "Škody pred prenájmom",
    "Pre rental damages",
    "Poškození způsobená během pronájmu",
    "Nové škody počas prenájmu",
    "New damages during rent",
]

def classify_page(text):
    t = norm(text)
    # DROP má přednost - VOP a marketing jsou jasně identifikovatelné
    for p in DROP_PATTERNS:
        if p in t:
            return "DROP"
    for p in KEEP_PATTERNS:
        if p in t:
            return "KEEP"
    return "UNKNOWN"

def trim_pdf(src_path, dst_path):
    doc = fitz.open(src_path)
    keep_pages = []
    unknowns = []
    for i, page in enumerate(doc):
        text = page.get_text()
        cls = classify_page(text)
        if cls == "KEEP":
            keep_pages.append(i)
        elif cls == "UNKNOWN":
            unknowns.append((i, text[:100].replace('\n', ' ')))
            # Defaultně zachováme UNKNOWN (bezpečnější) - lepší zbytečná stránka než chybějící podpis
            keep_pages.append(i)

    if not keep_pages:
        doc.close()
        return None, f"ŽÁDNÉ stránky k zachování! {len(doc)} stran celkem"

    # Nový PDF s jen keep_pages
    out = fitz.open()
    for p in keep_pages:
        out.insert_pdf(doc, from_page=p, to_page=p)
    out.save(dst_path, garbage=4, deflate=True, clean=True)
    out.close()
    doc.close()

    return (len(doc) if False else None, keep_pages, unknowns)

if __name__ == "__main__":
    src_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/Downloads"
    dst_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/trimmed"
    os.makedirs(dst_dir, exist_ok=True)

    files = sorted(glob.glob(f"{src_dir}/Smlouva_*.pdf"))
    results = []
    for src in files:
        name = os.path.basename(src)
        dst = os.path.join(dst_dir, name)
        try:
            doc = fitz.open(src)
            orig_pages = len(doc)
            doc.close()

            r = trim_pdf(src, dst)
            if r[0] is None and isinstance(r[1], list):
                keep_pages, unknowns = r[1], r[2]
                results.append((name, orig_pages, len(keep_pages), unknowns))
            else:
                print(f"ERR {name}: {r[1]}")
        except Exception as e:
            print(f"EXC {name}: {e}")

    # Summary
    print(f"\n=== Zpracováno {len(results)} PDF ===")
    for name, o, n, unk in results:
        marker = "" if not unk else f" [UNKNOWN pages: {len(unk)}]"
        print(f"  {name}: {o} → {n} stran{marker}")
        for idx, snippet in unk:
            print(f"      [p{idx+1}] {snippet[:80]}")
