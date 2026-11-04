"""Konsolidace Wix CMS kolekce Auta (rxauto.cz): 1 záznam na model místo 1 na kus.
Vstup: data/auta_backup_YYYY-MM-DD.json (export kolekce). Výstup: data/plan.json
(keeper per model + sloučená pole + ID k odebrání)."""
import json, re, sys
from collections import OrderedDict

src = sys.argv[1] if len(sys.argv) > 1 else "data/auta_backup_2026-11-04.json"
items = json.load(open(src))

# sjednocení názvů modelů (varianty výbavy / generace -> jeden model)
ALIAS = {
    ("Škoda", "Karoq Ambition"): "Karoq", ("Škoda", "Karoq Scout"): "Karoq",
    ("Škoda", "Karoq Style"): "Karoq", ("Škoda", "Karoq SportLine"): "Karoq",
    ("Škoda", "Fabia III Combi"): "Fabia Combi",
}

def norm(s): return re.sub(r"\s+", " ", (s or "").strip())
def fix_fuel(s): return {"Beznín": "Benzín"}.get(s, s)
def uniq(vals):
    out = []
    for v in vals:
        if v and v not in out: out.append(v)
    return out

groups = OrderedDict()
for it in items:
    z, t = norm(it.get("znacka")), norm(it.get("title"))
    t = ALIAS.get((z, t), t)
    groups.setdefault((z, t), []).append(it)

def score(it):
    upd = (it.get("_updatedDate") or {}).get("$date", "")
    return ("ano" in (it.get("zobrazitNaWebu") or []), bool(it.get("cena")),
            "ano" in (it.get("landingPage") or []), bool(it.get("mediagallery")), upd)

POB = ["Praha", "Ostrava", "Bratislava"]
plan = []
for (z, t), its in groups.items():
    keep = max(its, key=score)
    pob = [p for p in POB if any(norm(i.get("msto")) == p for i in its)]
    kw = sorted(uniq(norm(i.get("vykonMotoru")).replace("kW", " kW").replace("  ", " ") for i in its),
                key=lambda s: float(re.sub(r"[^\d.]", "", s) or 0))
    plan.append({
        "keepId": keep["_id"],
        "znacka": z, "title": t, "kusu": len(its),
        "set": {
            "znacka": z, "title": t,
            "msto": ", ".join(pob),
            "pobocky": pob,
            "palivo": " / ".join(uniq(fix_fuel(norm(i.get("palivo"))) for i in its)),
            "typPrevodovky": " / ".join(uniq(norm(i.get("typPrevodovky")) for i in its)),
            "vykonMotoru": " / ".join(kw),
        },
        "removeIds": [i["_id"] for i in its if i["_id"] != keep["_id"]],
    })

json.dump(plan, open("data/plan.json", "w"), ensure_ascii=False, indent=1)
for p in plan:
    s = p["set"]
    print(f'{p["znacka"]} {p["title"]} | {p["kusu"]}× | {s["msto"]} | {s["palivo"]} | {s["typPrevodovky"]} | {s["vykonMotoru"]}')
print(len(plan), "modelů,", sum(len(p["removeIds"]) for p in plan), "záznamů k odebrání")
