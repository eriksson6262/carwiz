#!/usr/bin/env python3
"""RX Auto - Lustrace a nájemní smlouva"""

import os, re, json, base64, requests, shutil, zipfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
import anthropic
from smlouva_v2 import generate_smlouva_v2

ARES_API_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"

ISPIS_USERNAME = "info@rxuauto.cz"
ISPIS_PASSWORD = "RXAuto2021"
ISPIS_API_URL = "https://ispis.cz/api/lustraceSearchSubject"
SMLOUVA_FILENAME = "NS RX Retail Osobni Claude.xlsx"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
def _nacti_anthropic_key():
    """Klíč k Anthropic API: přednostně ze souboru 'anthropic_config.json'
    ({"api_key": "sk-ant-..."}), jinak z proměnné prostředí ANTHROPIC_API_KEY,
    jinak starý zabudovaný klíč (doporučeno přejít na config a starý klíč zrušit)."""
    cesta = os.path.join(SCRIPT_DIR, "anthropic_config.json")
    try:
        if os.path.exists(cesta):
            with open(cesta, encoding="utf-8") as f:
                k = (json.load(f).get("api_key") or "").strip()
            if k:
                return k
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY") or ""


anthropic_client = anthropic.Anthropic(api_key=_nacti_anthropic_key())

DEMO_RP = {"jmeno":"Jan","prijmeni":"Novák","datum_narozeni":"15.06.1985","cislo_rp":"E123456","datum_vydani_rp":"10.03.2020","platnost_rp":"10.03.2030","adresa":None,"typ_dokladu":"ridicsky_prukaz","chybi_udaje":[]}
DEMO_OP = {"jmeno":"Jan","prijmeni":"Novák","datum_narozeni":"15.06.1985","rodne_cislo":"850615/1234","cislo_op":"123456789","datum_vydani_op":"10.03.2020","platnost_op":"10.03.2030","adresa":"Václavské náměstí 1, Praha 1","je_pas":False,"chybi_udaje":[]}
DEMO_LUSTRACE = {"pocet_exekuci":0,"ma_exekuce":False,"cena_halerov":0,"kredit_halerov":0,"pdf_name":None}

HISTORY_FILE = os.path.join(SCRIPT_DIR, "historie_smluv.json")

VYFAKTURUJ_CONFIG_FILE = os.path.join(SCRIPT_DIR, "vyfakturuj_config.json")
VYFAKTURUJ_API_BASE = "https://api.vyfakturuj.cz/2.0"
DOCUSEAL_CONFIG_FILE = os.path.join(SCRIPT_DIR, "docuseal_config.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_to_history(osobni_data, smlouva_data, filename, firma_data=None, typ_vozidla="osobni"):
    history = load_history()
    from datetime import datetime
    entry = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "jmeno": f"{osobni_data.get('jmeno','')} {osobni_data.get('prijmeni','')}".strip(),
        "datum_narozeni": osobni_data.get('datum_narozeni',''),
        "cislo_rp": osobni_data.get('cislo_rp',''),
        "misto_narozeni": osobni_data.get('misto_narozeni',''),
        "zeme_op": osobni_data.get('zeme_op',''),
        "zeme_rp": osobni_data.get('zeme_rp',''),
        "cislo_op": osobni_data.get('cislo_op',''),
        "adresa": osobni_data.get('adresa',''),
        "vozidlo": smlouva_data.get('vozidlo',''),
        "datum_zacatku": smlouva_data.get('datum_zacatku',''),
        "datum_konce": smlouva_data.get('datum_konce',''),
        "cena": smlouva_data.get('cena',''),
        "interval_ceny": smlouva_data.get('interval_ceny',''),
        "jistina": smlouva_data.get('jistina',''),
        "mena": smlouva_data.get('mena','CZK'),
        "email": smlouva_data.get('email',''),
        "telefon": smlouva_data.get('telefon',''),
        "sjednany_najezd": smlouva_data.get('sjednany_najezd',''),
        "interval_najezdu": smlouva_data.get('interval_najezdu',''),
        "pocet_intervalu": smlouva_data.get('pocet_intervalu',''),
        "flexi": bool(smlouva_data.get('flexi')),
        "nahradni_vozidlo": bool(smlouva_data.get('nahradni_vozidlo')),
        "datum_vydani_op": osobni_data.get('datum_vydani_op') or '',
        "platnost_op": osobni_data.get('platnost_op') or '',
        "datum_vydani_rp": osobni_data.get('datum_vydani_rp') or '',
        "platnost_rp": osobni_data.get('platnost_rp') or '',
        "rodne_cislo": osobni_data.get('rodne_cislo') or '',
        "cena_dph": smlouva_data.get('cena_dph', '') or '',
        "korespondencni_adresa": smlouva_data.get('korespondencni_adresa', '') or '',
        "misto_predani": smlouva_data.get('misto_predani', '') or '',
        "misto_vraceni": smlouva_data.get('misto_vraceni', '') or '',
        "stav_tachometru_predani": smlouva_data.get('stav_tachometru_predani', '') or '',
        "stav_nadrze": smlouva_data.get('stav_nadrze', '') or '',
        "palivo": smlouva_data.get('palivo', '') or '',
        "poskozeni_predani": smlouva_data.get('poskozeni_predani', '') or '',
        "cislo_smlouvy": smlouva_data.get('cislo_smlouvy', '') or '',
        "cas_predani": smlouva_data.get('cas_predani', '') or '',
        "typ_vozidla": typ_vozidla or 'osobni',
        "firma": firma_data or None,
        "filename": filename,
    }
    cislo = entry.get("cislo_smlouvy") or ""
    if cislo and "TEST" not in cislo:
        history = [h for h in history if (h.get("cislo_smlouvy") or "") != cislo]
    history.insert(0, entry)
    # Zachovej max 200 záznamů
    history = history[:200]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return entry



def normalize_media_type(mt):
    """Normalizuje MIME type na hodnoty akceptované Claude API."""
    if not mt: return 'image/jpeg'
    mt = mt.lower().strip()
    mapping = {
        'image/jpg': 'image/jpeg',
        'image/jfif': 'image/jpeg',
        'image/pjpeg': 'image/jpeg',
        'image/x-png': 'image/png',
        'image/tiff': 'image/jpeg',
        'image/bmp': 'image/jpeg',
        'image/heic': 'image/jpeg',
        'image/heif': 'image/jpeg',
    }
    if mt in mapping: return mapping[mt]
    if mt in ('image/jpeg', 'image/png', 'image/gif', 'image/webp'): return mt
    return 'image/jpeg'  # fallback


def _img_block(img):
    """Obrázkový blok pro Claude API — fotku vždy překóduje přes PIL:
    zmenší na max 2000 px, převede na JPEG (API odmítá fotky nad 8000 px,
    nad ~5 MB a formáty, které neumí dekódovat — např. HEIC přejmenované na .JPEG)."""
    if (img.get("media_type") or "").lower() == "application/pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": img["data"]}}
    data, mt = img["data"], normalize_media_type(img.get("media_type"))
    try:
        from io import BytesIO
        from PIL import Image as _PILImage
        raw = base64.b64decode(data)
        im = _PILImage.open(BytesIO(raw))
        im.load()
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        m = max(im.size)
        if m > 2000:
            k = 2000.0 / m
            im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))))
        out = BytesIO()
        im.convert("RGB").save(out, "JPEG", quality=88)
        data, mt = base64.b64encode(out.getvalue()).decode(), "image/jpeg"
    except Exception:
        pass  # nedekódovatelné necháme projít beze změny — API vrátí srozumitelnou chybu
    return {"type": "image", "source": {"type": "base64", "media_type": mt, "data": data}}


def classify_images(images):
    """Pošle Claude všechny nahrané obrázky najednou a určí pro každý: typ dokladu + stranu (přední/zadní)."""
    content = [_img_block(img) for img in images]
    content.append({"type":"text","text":f"""Toto je {len(images)} fotek dokladů totožnosti nahraných najednou (mohou to být různé strany řidičského průkazu, OP, pasu nebo jiného ID — v libovolném pořadí, klidně i duplicitně).

Pro KAŽDÝ obrázek, v pořadí v jakém byl nahrán (indexováno od 0), urči:
- "typ": "ridicsky_prukaz" NEBO "doklad_totoznosti" (občanský průkaz, pas, jiné ID)
- "strana": "predni" NEBO "zadni"
- "je_pas": true pokud jde o cestovní pas, jinak false

Pozn.: řidičský průkaz má obvykle fotku, kategorie řízení (A,B,C...) a nápis jako "Řidičský průkaz" / "Driving Licence" / "Führerschein". Občanský průkaz/ID má fotku a národní znak/erb. Pas má fotostránku s MRZ kódem (řádky s <<<).

Vrať POUZE JSON pole, přesně {len(images)} položek, např.:
[{{"index":0,"typ":"ridicsky_prukaz","strana":"predni","je_pas":false}}, {{"index":1,"typ":"doklad_totoznosti","strana":"predni","je_pas":false}}]"""})

    msg = anthropic_client.messages.create(model="claude-opus-4-5", max_tokens=600,
        messages=[{"role":"user","content":content}])
    text = msg.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return json.loads(text.strip())


def extract_doc(images, doc_type):
    content = [_img_block(img) for img in images]
    if doc_type == "rp":
        content.append({"type":"text","text":"""Řidičský průkaz (může být z jakékoliv země — nepředpokládej že je český). Vrať POUZE JSON:
{"jmeno":null,"prijmeni":null,"datum_narozeni":null,"misto_narozeni":null,"cislo_rp":null,"datum_vydani_rp":null,"platnost_rp":null,"adresa":null,"zeme_vydani":null,"typ_dokladu":"ridicsky_prukaz","chybi_udaje":[]}
zeme_vydani = dvoupísmenný ISO kód země která doklad vydala, urči ho podle vzhledu dokladu, jazyka, znaků nebo nápisů (např. "Führerschein"=DE, "Permis de conduire"=FR, "Driving Licence"=GB, "Řidičský průkaz"=CZ, "Vodičský preukaz"=SK) — NIKDY nepředpokládej CZ jako výchozí, urči ho vždy z reálných znaků na dokladu.
chybi_udaje = seznam z: cislo_rp, datum_vydani_rp, platnost_rp — pokud nejsou čitelné."""})
    else:
        content.append({"type":"text","text":"""Doklad totožnosti (OP/pas/ID, může být z jakékoliv země — nepředpokládej že je český). Vrať POUZE JSON:
{"jmeno":null,"prijmeni":null,"datum_narozeni":null,"misto_narozeni":null,"rodne_cislo":null,"cislo_op":null,"datum_vydani_op":null,"platnost_op":null,"adresa":null,"zeme_vydani":null,"je_pas":false,"chybi_udaje":[]}
zeme_vydani = dvoupísmenný ISO kód země která doklad vydala, urči ho podle vzhledu dokladu, jazyka, nápisů, MRZ kódu na pasu nebo erbu (např. "Personalausweis"=DE, "Eigentumsausweis"=AT, "Občanský průkaz"=CZ, "Reisepass"=DE) — NIKDY nepředpokládej CZ jako výchozí, urči ho vždy z reálných znaků na dokladu.
chybi_udaje = seznam z: cislo_op, datum_vydani_op, platnost_op, adresa — pokud nejsou čitelné."""})
    msg = anthropic_client.messages.create(model="claude-opus-4-5", max_tokens=800,
        messages=[{"role":"user","content":content}])
    text = msg.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    return json.loads(text.strip())


def _pridej_mesice(d, n):
    """Přičte n kalendářních měsíců k datu (konec měsíce ořízne, např. 31.8. + 6 m → 28./29.2.)."""
    import calendar, datetime
    m0 = d.month - 1 + n
    rok, mesic = d.year + m0 // 12, m0 % 12 + 1
    den = min(d.day, calendar.monthrange(rok, mesic)[1])
    return datetime.date(rok, mesic, den)


_POLE_SCHEMA = ('{"spz":null,"znacka_model":null,"typ_vozidla":null,"cena":null,"cena_dph":null,"mena":null,'
    '"interval_ceny":null,"jistina":null,"sjednany_najezd":null,"interval_najezdu":null,"datum_zacatku":null,'
    '"datum_konce":null,"delka_mesicu":null,"delka_dnu":null,"email":null,"telefon":null,"misto_predani":null,'
    '"misto_vraceni":null,"flexi":false,"nahradni_vozidlo":false,"ico":null,"firma_nazev":null,"ridic":null,'
    '"neomezeny_najezd":false,"bez_kauce":false}')

_POLE_PRAVIDLA = """Pravidla:
- spz: poznávací značka velkými písmeny bez mezer (např. "1ALB766"). znacka_model: zbytek popisu vozidla pěkně zapsaný (např. "BMW 2" z "bmw 2", "Škoda Octavia").
- typ_vozidla: "osobni" (sedan, výchozí pro auta), "hatchback" (vč. liftbacku), "coupe", "kabriolet" (cabrio/roadster), "kombi" (Combi/Touring/Variant/Avant), "suv" (SUV/crossover, např. Kodiaq, Tiguan, X5), "dodavka" (dodávka/karavan), "prives", "motorka" — jen pokud je z podkladu zřejmé, jinak null.
- cena: číslo (10000 z "10000", "10 tis", "10k"); cena_dph: "bez_dph" pokud je řečeno bez DPH, "s_dph" pokud s DPH, jinak null. mena: "CZK" nebo "EUR" (jen pokud zmíněno, Kč/korun = CZK). interval_ceny: "měsíčně" nebo "denně" (cena za jeden den / za měsíc).
- jistina = kauce / záloha / depozit, číslo (15tis = 15000).
- sjednany_najezd: číslo km (2500). interval_najezdu: "měsíc", "rok", "den" nebo "pronájem" (za celou dobu pronájmu).
- datum_zacatku / datum_konce: ISO rrrr-mm-dd, relativní výrazy (dneska, zítra, od pondělí, 1. listopadu) přepočítej podle dnešního data. Pokud je konec vyjádřen délkou ("na půl roku", "za 3 měsíce", "na 14 dní"), dej datum_konce null a vyplň delka_mesicu (půl roku = 6) nebo delka_dnu.
- flexi: true pokud je řečeno "flexi" / bez pevného konce / vrácení není známo (pak datum_konce i délka null). nahradni_vozidlo: true pokud jde o náhradní vozidlo. ico: 8místné IČO firmy (nájemce), pokud je uvedeno (jen číslice) — NE IČO RX Auto / pronajímatele. firma_nazev: název firmy-nájemce. ridic: jméno řidiče, pokud je uvedeno. neomezeny_najezd: true při "neomezené km". bez_kauce: true při "bez kauce".
- email, telefon, místa předání/vrácení jen pokud jsou výslovně uvedena."""


def _llm_pole(content):
    """Zavolá Claude (content = bloky obrázků/PDF + textový prompt) a vrátí JSON s poli smlouvy."""
    msg = anthropic_client.messages.create(model="claude-opus-4-5", max_tokens=700,
        messages=[{"role": "user", "content": content}])
    out = msg.content[0].text.strip()
    if "```" in out:
        out = out.split("```")[1]
        if out.startswith("json"): out = out[4:]
    return json.loads(out.strip())


def _dnes_text():
    import datetime
    dnes = datetime.date.today()
    dny_cz = ["pondělí", "úterý", "středa", "čtvrtek", "pátek", "sobota", "neděle"]
    return f"{dny_cz[dnes.weekday()]} {dnes.isoformat()}"


def _normalizuj_pole(d):
    """Z odpovědi LLM udělá čistá pole formuláře (neplatné hodnoty zahodí, konec nájmu spočte z délky)."""
    import datetime

    def _iso(v):
        try:
            return datetime.date.fromisoformat(v) if v else None
        except Exception:
            return None
    zac, kon = _iso(d.get("datum_zacatku")), _iso(d.get("datum_konce"))
    if zac and not kon:
        if d.get("delka_mesicu"):
            kon = _pridej_mesice(zac, int(d["delka_mesicu"]))
        elif d.get("delka_dnu"):
            kon = zac + datetime.timedelta(days=int(d["delka_dnu"]))

    spz = re.sub(r"\s+", "", (d.get("spz") or "")).upper()
    zm = (d.get("znacka_model") or "").strip()
    vozidlo = " — ".join(x for x in (spz, zm) if x) or None

    def _cislo(v):
        if v in (None, ""): return None
        try:
            f = float(str(v).replace(" ", "").replace(",", "."))
            return str(int(f)) if f == int(f) else str(f)
        except Exception:
            return None

    ico = re.sub(r"\D", "", str(d.get("ico") or ""))
    flexi = bool(d.get("flexi"))
    if flexi:
        kon = None
    jistina = "0" if d.get("bez_kauce") and not d.get("jistina") else _cislo(d.get("jistina"))
    najezd = "Neomezený" if d.get("neomezeny_najezd") else _cislo(d.get("sjednany_najezd"))

    return {
        "flexi": flexi,
        "nahradni_vozidlo": bool(d.get("nahradni_vozidlo")),
        "ico": ico if len(ico) == 8 else None,
        "firma_nazev": (d.get("firma_nazev") or None),
        "ridic": (d.get("ridic") or None),
        "vozidlo": vozidlo,
        "typ_vozidla": d.get("typ_vozidla") if d.get("typ_vozidla") in ("osobni", "hatchback", "kombi", "suv", "coupe", "kabriolet", "dodavka", "prives", "motorka") else None,
        "cena": _cislo(d.get("cena")),
        "cena_dph": d.get("cena_dph") if d.get("cena_dph") in ("bez_dph", "s_dph") else None,
        "mena": d.get("mena") if d.get("mena") in ("CZK", "EUR") else None,
        "interval_ceny": d.get("interval_ceny") if d.get("interval_ceny") in ("měsíčně", "denně") else None,
        "jistina": jistina,
        "sjednany_najezd": najezd,
        "interval_najezdu": d.get("interval_najezdu") if d.get("interval_najezdu") in ("měsíc", "rok", "den", "pronájem") else None,
        "datum_zacatku": zac.isoformat() if zac else None,
        "datum_konce": kon.isoformat() if kon else None,
        "email": (d.get("email") or None),
        "telefon": (d.get("telefon") or None),
        "misto_predani": (d.get("misto_predani") or None),
        "misto_vraceni": (d.get("misto_vraceni") or None),
    }


def parse_popis_najmu(text):
    """Z volného českého popisu pronájmu (např. '10000 měsíčně bez dph, kauce 15tis,
    nájezd 2500 km měsíčně, začátek dneska, konec za půl roku, auto bmw 2 1ALB766')
    vytáhne hodnoty pro předvyplnění formuláře smlouvy. Vrací jen to, co v textu
    skutečně je — chybějící údaje jsou None (formulář je nechá prázdné)."""
    text = (text or "").strip()
    if not text:
        raise RuntimeError("Napiš nejdřív základní údaje o pronájmu.")
    prompt = f"""Dnes je {_dnes_text()}. Z krátkého popisu pronájmu vozidla vytáhni údaje pro formulář nájemní smlouvy.
Popis: \"\"\"{text}\"\"\"

Vrať POUZE JSON přesně v tomto tvaru (co v popisu není, dej null/false — nic si nevymýšlej):
{_POLE_SCHEMA}

{_POLE_PRAVIDLA}"""
    return _normalizuj_pole(_llm_pole([{"type": "text", "text": prompt}]))


def parse_dokument_najmu(files):
    """Z fotky / PDF libovolného dokumentu (faktura, objednávka, e-mail, nabídka, stará smlouva…)
    vytáhne údaje pro předvyplnění smlouvy: vozidlo, dobu nájmu, cenu, firmu, řidiče…"""
    if not files:
        raise RuntimeError("Nebyl nahrán žádný dokument.")
    content = []
    for f in files[:4]:
        mt = normalize_media_type(f.get("media_type"))
        if (f.get("media_type") or "").lower() == "application/pdf":
            content.append({"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": f["data"]}})
        else:
            content.append(_img_block(f))
    content.append({"type": "text", "text": f"""Dnes je {_dnes_text()}. Na přiloženém dokumentu (faktura, objednávka, e-mail, nabídka, potvrzení, jiná smlouva…) najdi údaje o pronájmu vozidla pro formulář nájemní smlouvy RX Auto, s.r.o. (RX Auto je pronajímatel, ne nájemce).
Vrať POUZE JSON přesně v tomto tvaru (co v dokumentu není, dej null/false — nic si nevymýšlej):
{_POLE_SCHEMA}

{_POLE_PRAVIDLA}
- U faktury: cena = cena nájmu za jednotku (den/měsíc), ne celková částka za období, pokud lze rozlišit; DPH urči podle toho, zda je uvedená cena bez DPH nebo s DPH. Období na dokladu (např. 2.8.–7.9.2026) = datum_zacatku/datum_konce."""})
    return _normalizuj_pole(_llm_pole(content))


def lustrace_cee(jmeno, prijmeni, datum):
    params = {"username":ISPIS_USERNAME,"password":ISPIS_PASSWORD,"profile":"CEE",
              "Jmeno":jmeno,"Prijmeni":prijmeni,"Narozen":datum}
    r = requests.get(ISPIS_API_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    pdf_path = None
    if data.get("files"):
        for f in data["files"]:
            if f.get("contentBase64"):
                pdf_bytes = base64.b64decode(f["contentBase64"])
                pdf_path = os.path.join(SCRIPT_DIR, f.get("name","lustrace.pdf"))
                with open(pdf_path,"wb") as fp: fp.write(pdf_bytes)
                break
    pocet = data.get("detail",{}).get("CEE_Pocet",0)
    return {"pocet_exekuci":pocet,"ma_exekuce":pocet>0,
            "cena_halerov":data.get("costCents",0),"kredit_halerov":data.get("balanceCents",0),
            "pdf_name":os.path.basename(pdf_path) if pdf_path else None}


def cislo_smlouvy_z_data(datum_zacatku):
    """Číslo smlouvy ve formátu ddmmrrrr z data začátku (podporuje ISO i dd.mm.rrrr)."""
    import re as re_c
    if not datum_zacatku:
        return ''
    mc = re_c.match(r'([0-9]{4})-([0-9]{2})-([0-9]{2})', datum_zacatku)
    if mc:
        return mc.group(3) + mc.group(2) + mc.group(1)
    mc2 = re_c.match(r'([0-9]{1,2})[.]([0-9]{1,2})[.]([0-9]{4})', datum_zacatku)
    if mc2:
        return mc2.group(1).zfill(2) + mc2.group(2).zfill(2) + mc2.group(3)
    return ''


CISELNA_RADA_FILE = os.path.join(SCRIPT_DIR, "ciselna_rada.json")


def dalsi_cislo_smlouvy(datum_zacatku, demo=False):
    """Číselná řada smluv RX_<rok>_<pořadové číslo>, počítadlo v 'ciselna_rada.json'
    (každý rok začíná od 001). Demo režim číslo nespotřebuje — vrací RX_<rok>_TEST."""
    import re as re_r
    from datetime import datetime as _dt
    rok = None
    d = (datum_zacatku or "").strip()
    m = re_r.match(r"([0-9]{4})-", d) or re_r.search(r"[.]([0-9]{4})$", d)
    if m:
        rok = int(m.group(1))
    if not rok:
        rok = _dt.now().year
    if demo:
        return f"RX_{rok}_TEST"
    stav = {"rok": rok, "posledni": 0}
    try:
        if os.path.exists(CISELNA_RADA_FILE):
            with open(CISELNA_RADA_FILE, encoding="utf-8") as f:
                nact = json.load(f)
            if int(nact.get("rok", 0)) == rok:
                stav = {"rok": rok, "posledni": int(nact.get("posledni", 0))}
    except Exception:
        pass
    stav["posledni"] += 1
    with open(CISELNA_RADA_FILE, "w", encoding="utf-8") as f:
        json.dump(stav, f)
    return f"RX_{rok}_{stav['posledni']:03d}"


def ares_lookup(ico):
    """Dotaz na veřejný registr ARES podle IČO. Bez potřeby API klíče."""
    ico = (ico or '').strip()
    if not ico or not ico.isdigit():
        return {"error": "Neplatné IČO — musí být číselné."}
    try:
        r = requests.get(f"{ARES_API_URL}/{ico}", timeout=10)
        if r.status_code == 404:
            return {"error": "IČO nebylo v ARES nalezeno."}
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"error": f"Chyba při dotazu na ARES: {e}"}
    sidlo = data.get("sidlo", {}) or {}
    return {
        "ico": data.get("ico", ico),
        "nazev": data.get("obchodniJmeno", ""),
        "dic": data.get("dic", ""),
        "sidlo": sidlo.get("textovaAdresa", ""),
        "pravni_forma": data.get("pravniForma", ""),
    }


def load_vyfakturuj_config():
    """Načte přihlašovací údaje k Vyfakturuj z lokálního souboru (nikdy z chatu/kódu)."""
    if not os.path.exists(VYFAKTURUJ_CONFIG_FILE):
        return None, (
            "Soubor 'vyfakturuj_config.json' nebyl nalezen ve složce generátoru. "
            "Vytvoř ho podle přiloženého 'vyfakturuj_config.example.json' a doplň "
            "svůj e-mail a API klíč z https://app.vyfakturuj.cz/nastaveni/propojeni/api/."
        )
    try:
        with open(VYFAKTURUJ_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        return None, f"Soubor 'vyfakturuj_config.json' se nepodařilo načíst: {e}"
    email = (cfg.get("email") or "").strip()
    api_key = (cfg.get("api_key") or "").strip()
    if not email or not api_key:
        return None, "V souboru 'vyfakturuj_config.json' chybí 'email' nebo 'api_key'."
    return {"email": email, "api_key": api_key}, None


def vyfakturuj_request(method, path, cfg, json_body=None, params=None):
    """Nízkoúrovňové volání Vyfakturuj REST API (v2) s HTTP Basic Auth."""
    url = f"{VYFAKTURUJ_API_BASE}{path}"
    r = requests.request(method, url, auth=(cfg["email"], cfg["api_key"]),
                          json=json_body, params=params, timeout=20)
    try:
        data = r.json()
    except Exception:
        r.raise_for_status()
        raise RuntimeError(f"Vyfakturuj vrátil neočekávanou odpověď (HTTP {r.status_code}).")
    if r.status_code >= 400 or (isinstance(data, dict) and data.get("status") == "error"):
        msg = data.get("message", f"HTTP {r.status_code}") if isinstance(data, dict) else f"HTTP {r.status_code}"
        input_error = data.get("inputError") if isinstance(data, dict) else None
        if input_error:
            details = "; ".join(f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in input_error.items())
            msg = f"{msg} ({details})"
        raise RuntimeError(f"Vyfakturuj API chyba: {msg}")
    return data


def vyfakturuj_split_spz(vozidlo):
    """Z pole 'vozidlo' (např. '1AB2345 — BMW 320d') vytáhne SPZ (část před pomlčkou)."""
    import re as re_v
    if not vozidlo:
        return ""
    parts = re_v.split(r"\s*[—–-]\s*", vozidlo.strip(), maxsplit=1)
    return (parts[0].strip() if parts and parts[0].strip() else vozidlo.strip())


def _rozdel_adresu(adresa):
    """'Václavské náměstí 1, 110 00 Praha 1' → (ulice, PSČ, město). Best effort."""
    import re as re_a
    a = (adresa or "").strip()
    if not a:
        return "", "", ""
    casti = [c.strip() for c in a.split(",") if c.strip()]
    ulice = casti[0] if casti else a
    zbytek = ", ".join(casti[1:]) if len(casti) > 1 else ""
    m = re_a.search(r"(\d{3}\s?\d{2})\s*(.*)$", zbytek)
    if m:
        return ulice, m.group(1).replace(" ", ""), (m.group(2) or "").strip(" ,")
    return ulice, "", zbytek


def vyfakturuj_find_or_create_contact(cfg, name, email, phone, ico=None, dic=None, adresa=None):
    """Dohledá kontakt podle přesné shody názvu (a doplní mu naše aktuální údaje),
    jinak založí nový — vždy s e-mailem, telefonem a rozdělenou adresou."""
    name = (name or "").strip()
    if not name:
        raise RuntimeError("Chybí jméno/název zákazníka pro Vyfakturuj.")
    ulice, psc, mesto = _rozdel_adresu(adresa)
    payload = {"name": name}
    if email: payload["mail_to"] = email
    if phone: payload["tel"] = phone
    if ulice: payload["street"] = ulice
    if psc: payload["zip"] = psc
    if mesto: payload["city"] = mesto
    if ico: payload["IC"] = ico
    if dic: payload["DIC"] = dic
    existing_id = None
    try:
        search = vyfakturuj_request("GET", "/contact/", cfg, params={"q": name, "rows_limit": 5})
        if isinstance(search, list):
            candidates = search
        elif isinstance(search, dict):
            candidates = search.get("data") or search.get("items") or search.get("contacts") or []
        else:
            candidates = []
        for c in candidates:
            if isinstance(c, dict) and (c.get("name") or "").strip().lower() == name.lower():
                existing_id = c.get("id")
                break
    except Exception:
        pass  # vyhledání se nezdařilo — bezpečně pokračujeme založením nového kontaktu
    if existing_id:
        try:
            if len(payload) > 1:
                vyfakturuj_request("PUT", f"/contact/{existing_id}/", cfg, json_body=payload)
        except Exception:
            pass  # doplnění údajů je best-effort, faktura se vystaví i tak
        return existing_id
    created = vyfakturuj_request("POST", "/contact/", cfg, json_body=payload)
    return created.get("id")


def _datum_plus_mesice(datum, mesice=1):
    """'2026-10-13' (+1) → date(2026,11,13); den se ořízne na konec měsíce. Umí ISO i dd.mm.rrrr."""
    from datetime import date
    import calendar, re as re_d
    m = re_d.match(r"(\d{4})-(\d{2})-(\d{2})", datum or "")
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m2 = re_d.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", datum or "")
        if not m2:
            return None
        d, mo, y = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
    mo += mesice
    y += (mo - 1) // 12
    mo = (mo - 1) % 12 + 1
    return date(y, mo, min(d, calendar.monthrange(y, mo)[1]))


def vyfakturuj_import(osobni_data, smlouva_data, firma_data, vcetne_najmu=False, typ_dokladu="zalohova"):
    """
    Založí (nebo dohledá) zákazníka ve Vyfakturuj a vystaví:
      1. zálohovou fakturu na jistinu (je-li sjednána) — lze hned odeslat
         z Vyfakturuj (e-mail s QR kódem platby),
      2. volitelně (vcetne_najmu=True) i nájemné: u měsíční sazby pravidelnou
         fakturu "{SPZ} {jméno řidiče}", u denní sazby jednorázovou fakturu
         za celou sjednanou dobu.
    """
    cfg, err = load_vyfakturuj_config()
    if err:
        raise RuntimeError(err)

    vozidlo = smlouva_data.get("vozidlo", "")
    spz = vyfakturuj_split_spz(vozidlo)
    ridic = f"{osobni_data.get('jmeno','')} {osobni_data.get('prijmeni','')}".strip()
    nazev_faktury = f"{spz} {ridic}".strip()
    if not nazev_faktury:
        raise RuntimeError("Nepodařilo se sestavit název faktury (chybí SPZ i jméno řidiče).")

    if firma_data and firma_data.get("nazev"):
        contact_name = firma_data.get("nazev")
        contact_ico = firma_data.get("ico")
        contact_dic = firma_data.get("dic")
    else:
        contact_name = ridic
        contact_ico = None
        contact_dic = None
    contact_email = smlouva_data.get("email", "")
    contact_phone = smlouva_data.get("telefon", "")

    if firma_data and firma_data.get("nazev"):
        contact_adresa = firma_data.get("sidlo", "")
    else:
        contact_adresa = (osobni_data.get("adresa") or "")
    contact_id = vyfakturuj_find_or_create_contact(
        cfg, contact_name, contact_email, contact_phone, contact_ico, contact_dic, contact_adresa)

    def _cislo(x):
        try:
            return float(str(x).replace(",", ".").replace(" ", "")) if str(x).strip() else 0
        except ValueError:
            return 0

    cena_num = _cislo(smlouva_data.get("cena", ""))
    cena_dph_mode = (smlouva_data.get("cena_dph") or "bez_dph").strip().lower()
    cena_bez_dph_num = cena_num / 1.21 if cena_dph_mode == "s_dph" else cena_num
    jistina_num = _cislo(smlouva_data.get("jistina", ""))
    mena = smlouva_data.get("mena", "CZK")
    datum_zacatku = smlouva_data.get("datum_zacatku", "")
    datum_konce = smlouva_data.get("datum_konce", "")
    interval_ceny = (smlouva_data.get("interval_ceny") or "").strip().lower()
    denne = interval_ceny in ("denně", "denne", "daily", "den")
    flexi = bool(smlouva_data.get("flexi"))
    cislo_sml = smlouva_data.get("cislo_smlouvy") or cislo_smlouvy_z_data(datum_zacatku)

    zpravy = []
    typ_cislo = 1 if typ_dokladu == "ostra" else 2   # 1 = běžná faktura, 2 = zálohová
    typ_text = "běžná faktura" if typ_cislo == 1 else "zálohová faktura"

    def _fmt_kc(x):
        return f"{x:,.0f}".replace(",", " ")

    def _fmt_d(d):
        return d.strftime("%d.%m.%Y") if d else ""

    from datetime import timedelta
    start2 = _datum_plus_mesice(datum_zacatku, 1)          # začátek 2. měsíce
    konec_d = None
    if datum_konce:
        konec_d = _datum_plus_mesice(datum_konce, 0)

    # ---- 1. faktura: jistina + (volitelně) nájemné za 1. období ----
    polozky, popis = [], []
    if jistina_num > 0:
        polozky.append({"text": f"Vratná jistina (kauce) — nájem vozidla {vozidlo}, smlouva č. {cislo_sml}".strip(),
                        "quantity": 1, "unit_price": jistina_num, "vat_rate": 0})
        popis.append(f"jistina {_fmt_kc(jistina_num)} {mena}")
    if vcetne_najmu:
        if denne:
            if flexi or not str(smlouva_data.get("pocet_intervalu", "")).strip():
                raise RuntimeError(
                    "U denní sazby s Flexi (bez známého konce) nelze nájemné vystavit předem — "
                    "fakturu založ ručně ve Vyfakturuj podle skutečných dní.")
            dny = _cislo(smlouva_data.get("pocet_intervalu", ""))
            polozky.append({"text": f"Nájem vozidla {vozidlo}, {dny:.0f} dní "
                                    f"({datum_zacatku} – {datum_konce}), smlouva č. {cislo_sml}".strip(),
                            "quantity": dny, "unit_price": cena_bez_dph_num, "vat_rate": 21})
            popis.append(f"nájemné {dny:.0f} dní")
        elif cena_bez_dph_num > 0 and start2:
            d1 = _datum_plus_mesice(datum_zacatku, 0)
            polozky.append({"text": f"Nájem vozidla {vozidlo} — 1. měsíc "
                                    f"({_fmt_d(d1)} – {_fmt_d(start2 - timedelta(days=1))}), smlouva č. {cislo_sml}".strip(),
                            "quantity": 1, "unit_price": cena_bez_dph_num, "vat_rate": 21})
            popis.append(f"nájemné za 1. měsíc {_fmt_kc(cena_bez_dph_num)} {mena} bez DPH")
    if not polozky:
        raise RuntimeError("Jistina není sjednána a nájemné není zatrženo — není co vystavit.")

    inv = vyfakturuj_request("POST", "/invoice/", cfg, json_body={
        "id_customer": contact_id, "type": typ_cislo,
        "doc_currency": mena, "doc_calculate_vat": 1, "items": polozky})
    cislo_f = inv.get("number") if isinstance(inv, dict) else None
    zpravy.append(f"První {typ_text}" + (f" č. {cislo_f}" if cislo_f else "")
                  + ": " + " + ".join(popis))

    # ---- 2. pravidelná měsíční faktura od 2. měsíce dále ----
    if vcetne_najmu and not denne:
        if konec_d and start2 and konec_d <= start2:
            zpravy.append("Smlouva jen na 1 měsíc — pravidelná faktura není potřeba.")
        else:
            payload = {
                "id_customer": contact_id,
                "name": nazev_faktury,
                "type": 2,             # 2 = pravidelná faktura
                "start_type": 1,       # 1 = přesné datum
                "date_start": start2.isoformat() if start2 else datum_zacatku,
                "repeat_period": 1,    # opakovat po 1 měsíci
                "end_type": 2 if (datum_konce and not flexi) else 1,
                "doc_currency": mena,
                "doc_calculate_vat": 1,
                "items": [{
                    "text": f"Nájem vozidla {vozidlo}".strip(),
                    "quantity": 1,
                    "unit_price": cena_bez_dph_num,
                    "vat_rate": 21,
                }],
            }
            if datum_konce and not flexi:
                payload["date_end"] = datum_konce
            vyfakturuj_request("POST", "/template/", cfg, json_body=payload)
            zpravy.append(f"Pravidelná měsíční faktura „{nazev_faktury}“ od {_fmt_d(start2)} (2. měsíc dále)")

    return {"contact_id": contact_id, "name": nazev_faktury, "zpravy": zpravy}


def load_docuseal_config():
    """Načte přihlašovací údaje k DocuSeal z lokálního souboru (nikdy z chatu/kódu)."""
    if not os.path.exists(DOCUSEAL_CONFIG_FILE):
        return None, (
            "Soubor 'docuseal_config.json' nebyl nalezen ve složce generátoru. "
            "Vytvoř ho podle přiloženého 'docuseal_config.example.json' a doplň "
            "svůj API klíč z DocuSeal (Nastavení → API)."
        )
    try:
        with open(DOCUSEAL_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        return None, f"Soubor 'docuseal_config.json' se nepodařilo načíst: {e}"
    api_key = (cfg.get("api_key") or "").strip()
    if not api_key:
        return None, "V souboru 'docuseal_config.json' chybí 'api_key'."
    base_url = (cfg.get("base_url") or "").strip() or "https://api.docuseal.com"
    return {"api_key": api_key, "base_url": base_url.rstrip("/")}, None


def docuseal_request(method, path, cfg, json_body=None):
    """Nízkoúrovňové volání DocuSeal REST API s autentizací přes X-Auth-Token."""
    url = f"{cfg['base_url']}{path}"
    headers = {"X-Auth-Token": cfg["api_key"], "Content-Type": "application/json"}
    r = requests.request(method, url, headers=headers, json=json_body, timeout=60)
    try:
        data = r.json()
    except Exception:
        r.raise_for_status()
        raise RuntimeError(f"DocuSeal vrátil neočekávanou odpověď (HTTP {r.status_code}).")
    if r.status_code >= 400:
        msg = None
        if isinstance(data, dict):
            msg = data.get("error") or data.get("message")
        elif isinstance(data, list) and data:
            msg = str(data[0])
        raise RuntimeError(f"DocuSeal API chyba (HTTP {r.status_code}): {msg or r.text[:300]}")
    return data


def _normalizuj_telefon_e164(raw):
    """Převede telefonní číslo z formuláře (např. '+420 601 234 567' nebo
    '601234567') na tvar E.164 vyžadovaný DocuSeal pro SMS ('+420601234567').
    Vrátí None, pokud číslo chybí nebo nejde rozumně normalizovat."""
    s = (raw or "").strip()
    if not s:
        return None
    s = re.sub(r"[\s\-\.\(\)]", "", s)
    if s.startswith("00"):
        s = "+" + s[2:]
    if not s.startswith("+"):
        digits = re.sub(r"\D", "", s)
        if len(digits) == 9:  # české číslo bez předvolby
            s = "+420" + digits
        else:
            s = "+" + digits
    return s if re.match(r"^\+\d{8,15}$", s) else None


def docuseal_send_for_signature(osobni_data, smlouva_data, pdf_path, podpis_pozice=None, send_sms=False):
    """Pošle vygenerovanou smlouvu (PDF) do DocuSeal k elektronickému podpisu —
    signatářem je pouze nájemce, RX Auto podepisuje mimo DocuSeal (razítko/fyzicky).

    podpis_pozice: volitelný dict {page, x, y, w, h} (normalizované zlomky
    0-1 rozměrů stránky, y odshora) — pozice, kam se má v dokumentu umístit
    podpisové pole nájemce. Spočítá se přímo při generování smlouvy
    (smlouva_v2.generate_smlouva_v2) z reálně vykreslené pozice podpisové
    čáry, takže signatář hned vidí, kam se má podepsat.

    send_sms: pokud True, pošle nájemci odkaz k podpisu i SMS zprávou (na
    telefon vyplněný ve formuláři smlouvy) — u DocuSeal to navíc stojí
    cca 0,20 USD za zprávu."""
    cfg, err = load_docuseal_config()
    if err:
        raise RuntimeError(err)

    if not pdf_path or not os.path.exists(pdf_path):
        raise RuntimeError("Vygenerovaná smlouva (PDF) nebyla nalezena na disku — nejdřív ji vygeneruj.")

    email = (smlouva_data.get("email") or "").strip()
    if not email:
        raise RuntimeError("Nájemce nemá v datech smlouvy vyplněný e-mail — bez něj nelze poslat k podpisu.")

    jmeno = f"{osobni_data.get('jmeno','')} {osobni_data.get('prijmeni','')}".strip()
    vozidlo = smlouva_data.get("vozidlo", "")
    doc_name = f"Nájemní smlouva — {vozidlo}".strip(" —") or "Nájemní smlouva"

    with open(pdf_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    document = {
        "name": os.path.basename(pdf_path),
        "file": f"data:application/pdf;base64,{b64}",
    }
    if podpis_pozice and podpis_pozice.get("page"):
        document["fields"] = [{
            "name": "Podpis nájemce",
            "type": "signature",
            "role": "Nájemce",
            "required": True,
            "areas": [{
                "x": podpis_pozice["x"],
                "y": podpis_pozice["y"],
                "w": podpis_pozice["w"],
                "h": podpis_pozice["h"],
                "page": podpis_pozice["page"],
            }],
        }]

    submitter = {
        "role": "Nájemce",
        "email": email,
        "name": jmeno or email,
    }
    sms_bez_telefonu = False
    if send_sms:
        phone_e164 = _normalizuj_telefon_e164(smlouva_data.get("telefon", ""))
        if phone_e164:
            submitter["phone"] = phone_e164
            submitter["send_sms"] = True
        else:
            sms_bez_telefonu = True  # SMS požadována, ale nájemce nemá vyplněný telefon

    payload = {
        "name": doc_name,
        "documents": [document],
        "submitters": [submitter],
        "send_email": True,
    }
    result = docuseal_request("POST", "/submissions/pdf", cfg, json_body=payload)

    submission_id = None
    if isinstance(result, list) and result:
        submission_id = result[0].get("submission_id")
    elif isinstance(result, dict):
        submission_id = result.get("id") or result.get("submission_id")

    return {
        "submission_id": submission_id,
        "email": email,
        "sms_sent": bool(send_sms and not sms_bez_telefonu),
        "sms_skipped_no_phone": sms_bez_telefonu,
    }


def vyplnit_smlouvu(osobni_data, smlouva_data, output_path):
    """
    Vyplní smlouvu přes lxml (přesný XML parser) + zachová všechny soubory v ZIP.
    Nevyužívá openpyxl save ani regex — zaručeně validní XML.
    """
    import zipfile
    try:
        from lxml import etree
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'lxml', '--break-system-packages', '-q'])
        from lxml import etree

    smlouva_path = os.path.join(SCRIPT_DIR, SMLOUVA_FILENAME)
    if not os.path.exists(smlouva_path):
        for fname in os.listdir(SCRIPT_DIR):
            if fname.endswith(".xlsx"):
                smlouva_path = os.path.join(SCRIPT_DIR, fname)
                break
        else:
            return None, f"Soubor '{SMLOUVA_FILENAME}' nebyl nalezen."

    try:
        NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        cele_jmeno = (osobni_data.get('jmeno','') + ' ' + osobni_data.get('prijmeni','')).strip()

        def set_cell(tree, ref, value):
            if value is None:
                value = ''
            value = str(value).strip()
            row_num = int(''.join(c for c in ref if c.isdigit()))
            rows = tree.findall(f'.//{{{NS}}}row[@r="{row_num}"]')
            if not rows:
                return
            row = rows[0]
            cells = row.findall(f'{{{NS}}}c[@r="{ref}"]')
            if cells:
                cell = cells[0]
            else:
                cell = etree.SubElement(row, f'{{{NS}}}c')
                cell.set('r', ref)
            # Odstraň t atribut a všechny child elementy
            if 't' in cell.attrib:
                del cell.attrib['t']
            for child in list(cell):
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if tag in ('v', 'f', 'is'):
                    cell.remove(child)
            if value:
                cell.set('t', 'str')
                v_el = etree.SubElement(cell, f'{{{NS}}}v')
                v_el.text = value

        # Načti ZIP
        with zipfile.ZipFile(smlouva_path, 'r') as zin:
            all_files = {name: zin.read(name) for name in zin.namelist()}
            orig_compress = {info.filename: info.compress_type for info in zin.infolist()}

        # === SHEET1 (Vzor) ===
        def fmt_datum(d):
            """Prevede datum do formatu dd.mm.rr"""
            if not d: return ''
            d = str(d).strip()
            import re as re_d
            # ISO 2024-01-15 -> 15.01.24
            m = re_d.match('([0-9]{4})-([0-9]{2})-([0-9]{2})', d)
            if m:
                return m.group(3) + '.' + m.group(2) + '.' + m.group(1)[2:]
            # dd.mm.yyyy -> dd.mm.yy
            m2 = re_d.match('([0-9]{1,2})[.]([0-9]{1,2})[.]([0-9]{4})', d)
            if m2:
                return m2.group(1).zfill(2) + '.' + m2.group(2).zfill(2) + '.' + m2.group(3)[2:]
            return d

        # === SHEET1 (Vzor) ===
        # Zapisujeme přímo i do buněk které jsou formule (=Data!xx)
        # aby Excel nemusel přepočítávat — hodnoty tam budou ihned
        tree1 = etree.fromstring(all_files['xl/worksheets/sheet1.xml'])

        # Buňky s formulemi — zapíšeme hodnotu přímo (formuli zachováme, přidáme cached value)
        najezd = smlouva_data.get('sjednany_najezd','')
        interval_n = smlouva_data.get('interval_najezdu','rok')

        # Číslo smlouvy — z číselné řady (předáno v smlouva_data), fallback ddmmrrrr
        cislo_smlouvy = smlouva_data.get('cislo_smlouvy') or cislo_smlouvy_z_data(smlouva_data.get('datum_zacatku',''))

        # Interval texty
        mena_pre = smlouva_data.get('mena', 'CZK')
        interval_ceny_text = f'{mena_pre} za měsíc' if smlouva_data.get('interval_ceny','') == 'měsíčně' else f'{mena_pre} za den'

        set_cell(tree1, 'G1', cislo_smlouvy)                         # Číslo smlouvy

        set_cell(tree1, 'A14', cele_jmeno)
        set_cell(tree1, 'A16', osobni_data.get('datum_narozeni',''))
        set_cell(tree1, 'E12', fmt_datum(smlouva_data.get('datum_zacatku','')))
        set_cell(tree1, 'F12', fmt_datum(smlouva_data.get('datum_konce','')))
        set_cell(tree1, 'A34', smlouva_data.get('vozidlo',''))
        set_cell(tree1, 'B38', (najezd + ' km/' + interval_n) if najezd else '')
        # G24 se nevyplňuje, F31 se nevyplňuje množstvím
        mena = smlouva_data.get('mena', 'CZK')
        cena_hodnota = smlouva_data.get('cena','')
        set_cell(tree1, 'F31', cena_hodnota)  # cena přesunuta z G31 na F31
        set_cell(tree1, 'G31', mena)          # měna do G31
        set_cell(tree1, 'A26', smlouva_data.get('email',''))
        set_cell(tree1, 'D47', fmt_datum(smlouva_data.get('datum_zacatku','')))
        set_cell(tree1, 'D98', fmt_datum(smlouva_data.get('datum_zacatku','')))
        set_cell(tree1, 'G23', interval_ceny_text)                   # "Kč za měsíc" / "Kč za den"

        mena_celkem = mena
        interval_g33 = 'měsíčně' if smlouva_data.get('interval_ceny','') == 'měsíčně' else 'denně'
        set_cell(tree1, 'G33', f"{mena_celkem} {interval_g33} včetně DPH")

        # Osobní doklady
        set_cell(tree1, 'A18', osobni_data.get('cislo_op',''))
        set_cell(tree1, 'B18', osobni_data.get('datum_vydani_op',''))
        set_cell(tree1, 'C18', osobni_data.get('platnost_op',''))
        set_cell(tree1, 'D18', osobni_data.get('zeme_op', 'CZ'))
        set_cell(tree1, 'A20', osobni_data.get('cislo_rp',''))
        set_cell(tree1, 'B20', osobni_data.get('datum_vydani_rp',''))
        set_cell(tree1, 'C20', osobni_data.get('platnost_rp',''))
        set_cell(tree1, 'D20', osobni_data.get('zeme_rp', 'CZ'))
        set_cell(tree1, 'A22', osobni_data.get('adresa',''))
        set_cell(tree1, 'C16', osobni_data.get('misto_narozeni',''))  # místo narození
        set_cell(tree1, 'C26', smlouva_data.get('telefon',''))
        jistina_hodnota = smlouva_data.get('jistina','')
        jistina_text = f"{jistina_hodnota} {mena}" if jistina_hodnota else ''
        set_cell(tree1, 'E20', jistina_text)
        set_cell(tree1, 'F23', smlouva_data.get('cena',''))

        # Délka pronájmu do G12
        pocet = smlouva_data.get('pocet_intervalu','')
        interval_ceny = smlouva_data.get('interval_ceny','')
        if smlouva_data.get('flexi'):
            set_cell(tree1, 'G12', 'Flexi (dle skutečného vrácení)')
        elif pocet:
            delka_text = pocet + (' dní' if interval_ceny == 'denně' else ' měsíců')
            set_cell(tree1, 'G12', delka_text)

        # Předávací protokol (str. 3)
        set_cell(tree1, 'E100', cislo_smlouvy)                       # č. smlouvy v protokolu
        set_cell(tree1, 'A102', cele_jmeno)                          # jméno nájemce
        set_cell(tree1, 'D102', smlouva_data.get('vozidlo',''))      # vozidlo
        set_cell(tree1, 'A103', osobni_data.get('adresa',''))        # adresa
        set_cell(tree1, 'A105', smlouva_data.get('email','') + '  ' + smlouva_data.get('telefon',''))  # kontakt
        set_cell(tree1, 'B107', fmt_datum(smlouva_data.get('datum_zacatku','')))  # datum předání

        all_files['xl/worksheets/sheet1.xml'] = etree.tostring(
            tree1, xml_declaration=True, encoding='UTF-8', standalone=True)

        # === SHEET2 (Data) — sem míří všechny formule z Vzoru ===
        # =Data!A4 -> jméno řidiče (Vzor A14)
        # =Data!B4 -> datum narozeni (Vzor A16)
        # =Data!A6 -> datum začátku (Vzor E12)
        # =Data!B6 -> datum konce (Vzor F12)
        # =Data!F6 -> vozidlo (Vzor A34)
        # =Data!I6 -> nájezd (Vzor B38)
        # =Data!K6 -> cena (Vzor G24, G31, G33 přes DPH)
        # =Data!L6 -> počet (Vzor F24)
        # =Data!E17 -> email (Vzor A26)
        tree2 = etree.fromstring(all_files['xl/worksheets/sheet2.xml'])

        set_cell(tree2, 'A4', cele_jmeno)
        set_cell(tree2, 'B4', osobni_data.get('datum_narozeni',''))
        set_cell(tree2, 'C4', osobni_data.get('misto_narozeni',''))
        set_cell(tree2, 'A6', fmt_datum(smlouva_data.get('datum_zacatku','')))
        set_cell(tree2, 'B6', fmt_datum(smlouva_data.get('datum_konce','')))
        set_cell(tree2, 'F6', smlouva_data.get('vozidlo',''))
        najezd = smlouva_data.get('sjednany_najezd','')
        interval_n = smlouva_data.get('interval_najezdu','rok')
        set_cell(tree2, 'I6', (najezd + ' km/' + interval_n) if najezd else '')
        set_cell(tree2, 'K6', smlouva_data.get('cena',''))
        set_cell(tree2, 'L6', smlouva_data.get('pocet_intervalu',''))
        set_cell(tree2, 'E17', smlouva_data.get('email',''))

        all_files['xl/worksheets/sheet2.xml'] = etree.tostring(
            tree2, xml_declaration=True, encoding='UTF-8', standalone=True)

        # Odstraň calcChain (přegeneruje se automaticky)
        all_files.pop('xl/calcChain.xml', None)

        # Zapiš ZIP se zachováním compress_type
        with zipfile.ZipFile(output_path, 'w') as zout:
            for name, data in all_files.items():
                zi = zipfile.ZipInfo(name)
                zi.compress_type = orig_compress.get(name, 8)
                zout.writestr(zi, data)

        print("OK Smlouva vyplnena: " + cele_jmeno)
        return output_path, None

    except Exception as e:
        import traceback
        print("CHYBA:\n" + traceback.format_exc())
        return None, str(e)

class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"→ {self.command} {self.path}")

    def do_GET(self):
        if self.path in ("/","/index.html"):
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Cache-Control","no-store, must-revalidate"); self.end_headers()
            with open(os.path.join(SCRIPT_DIR,"index.html"),"rb") as f: self.wfile.write(f.read())
        elif self.path == "/api/history":
            history = load_history()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(history, ensure_ascii=False).encode())
        elif self.path.startswith("/diagram/"):
            key = unquote(self.path[9:]).replace(".png", "")
            if key in ("car", "hatchback", "kombi", "suv", "coupe", "kabriolet", "van", "trailer", "moto"):
                fp = os.path.join(SCRIPT_DIR, "diagrams", "sablony", key + ".png")
                if os.path.exists(fp):
                    self.send_response(200); self.send_header("Content-Type", "image/png"); self.end_headers()
                    with open(fp, "rb") as f: self.wfile.write(f.read())
                    return
            self.send_response(404); self.end_headers()
        elif self.path.startswith("/download/"):
            filename = unquote(self.path[10:])
            filepath = os.path.join(SCRIPT_DIR, filename)
            if os.path.exists(filepath):
                self.send_response(200)
                ct = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                self.send_header("Content-Type", ct)
                # RFC 5987 - bezpečné kódování pro diakritiku v hlavičce
                import unicodedata
                ascii_name = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
                from urllib.parse import quote
                utf8_name = quote(filename, safe='')
                self.send_header("Content-Disposition", f'attachment; filename="{ascii_name}"; filename*=UTF-8''{utf8_name}')
                self.end_headers()
                with open(filepath,"rb") as f: self.wfile.write(f.read())
            else:
                self.send_response(404); self.end_headers()
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/check": result = self.check_doc(body)
        elif self.path == "/api/classify": result = self.classify(body)
        elif self.path == "/api/ares": result = self.ares(body)
        elif self.path == "/api/process": result = self.process(body)
        elif self.path == "/api/vyfakturuj-import": result = self.vyfakturuj_import_route(body)
        elif self.path == "/api/docuseal-send": result = self.docuseal_send_route(body)
        elif self.path == "/api/parse-popis": result = self.parse_popis_route(body)
        elif self.path == "/api/extract-doc": result = self.extract_doc_route(body)
        elif self.path == "/api/vyuctovani": result = self.vyuctovani_route(body)
        elif self.path == "/api/podpis-vlozit": result = self.podpis_vlozit_route(body)
        elif self.path == "/api/docuseal-stazeni": result = self.docuseal_stazeni_route(body)
        elif self.path == "/api/restart":
            import threading, sys as _sys
            _srv = os.path.join(SCRIPT_DIR, "server.py")
            threading.Timer(0.5, lambda: os.execv(_sys.executable, [_sys.executable, _srv])).start()
            print("🔄 Restartuji generátor (požadavek z aplikace)...")
            result = {"success": True}
        elif self.path == "/api/shutdown":
            import threading
            threading.Timer(0.4, lambda: os._exit(0)).start()
            print("⏻ Vypínám generátor (požadavek z aplikace)...")
            result = {"success": True}
        elif self.path == "/api/history/delete":
            try:
                entry_id = body.get("id")
                history = load_history()
                history = [e for e in history if e.get("id") != entry_id]
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                result = {"success": True}
            except Exception as e:
                result = {"error": str(e)}
        else: self.send_response(404); self.end_headers(); return
        self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

    def check_doc(self, data):
        try:
            result = extract_doc(data.get("images",[]), data.get("doc_type"))
            chybi = result.get("chybi_udaje",[])
            je_pas = result.get("je_pas", False)
            return {"potrebuje_zadi":(not je_pas) and len(chybi)>0,"chybi":chybi,"data":result,"je_pas":je_pas}
        except Exception as e:
            import traceback; return {"error":str(e),"traceback":traceback.format_exc()}

    def ares(self, data):
        try:
            return ares_lookup(data.get("ico", ""))
        except Exception as e:
            import traceback; return {"error": str(e), "traceback": traceback.format_exc()}

    def classify(self, data):
        """Přijme libovolný počet obrázků (1-4), rozpozná typ+stranu, seskupí na RP/OP a rovnou extrahuje data pro oba."""
        try:
            images = data.get("images", [])
            if not images:
                return {"error": "Nebyly nahrány žádné obrázky."}

            classification = classify_images(images)

            rp_imgs, op_imgs = [], []
            for c in classification:
                idx = c.get("index")
                if idx is None or idx >= len(images):
                    continue
                img = images[idx]
                strana = c.get("strana", "predni")
                entry = (img, strana, c.get("je_pas", False))
                if c.get("typ") == "ridicsky_prukaz":
                    rp_imgs.append(entry)
                else:
                    op_imgs.append(entry)

            def sort_front_first(group):
                return sorted(group, key=lambda x: 0 if x[1] == "predni" else 1)

            rp_imgs = sort_front_first(rp_imgs)
            op_imgs = sort_front_first(op_imgs)

            result = {"rp": None, "op": None, "classification": classification}

            if rp_imgs:
                imgs_for_extract = [e[0] for e in rp_imgs[:2]]
                rp_data = extract_doc(imgs_for_extract, "rp")
                chybi = rp_data.get("chybi_udaje", [])
                result["rp"] = {
                    "data": rp_data, "chybi": chybi,
                    "potrebuje_zadi": len(chybi) > 0 and len(rp_imgs) < 2,
                    "pocet_fotek": len(rp_imgs),
                }

            if op_imgs:
                imgs_for_extract = [e[0] for e in op_imgs[:2]]
                op_data = extract_doc(imgs_for_extract, "op")
                chybi = op_data.get("chybi_udaje", [])
                je_pas = op_data.get("je_pas", False)
                result["op"] = {
                    "data": op_data, "chybi": chybi,
                    "potrebuje_zadi": (not je_pas) and len(chybi) > 0 and len(op_imgs) < 2,
                    "je_pas": je_pas, "pocet_fotek": len(op_imgs),
                }

            return result
        except Exception as e:
            import traceback; return {"error": str(e), "traceback": traceback.format_exc()}

    def vyfakturuj_import_route(self, data):
        try:
            osobni_data = data.get("osobni_data", {})
            smlouva_data = data.get("smlouva_data", {})
            firma_data = data.get("firma_data") or None
            result = vyfakturuj_import(osobni_data, smlouva_data, firma_data,
                                        vcetne_najmu=bool(data.get("vcetne_najmu")),
                                        typ_dokladu=(data.get("typ_dokladu") or "zalohova"))
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def parse_popis_route(self, data):
        try:
            return {"success": True, "pole": parse_popis_najmu(data.get("text", ""))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def vyuctovani_route(self, data):
        try:
            from datetime import datetime, date
            import math
            history = load_history()
            entry = next((e for e in history if e.get("id") == data.get("id")), None)
            if not entry:
                raise RuntimeError("Záznam v historii nenalezen.")

            def _parse_datum(d):
                d = (d or "").strip()
                for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                    try:
                        return datetime.strptime(d, fmt).date()
                    except ValueError:
                        continue
                return None

            def _cislo(x):
                try:
                    return float(str(x).replace(" ", "").replace(",", "."))
                except (ValueError, TypeError):
                    return None

            zac = _parse_datum(entry.get("datum_zacatku"))
            vra = _parse_datum(data.get("datum_vraceni")) or date.today()
            dny = max(1, (vra - zac).days) if zac else None

            km0 = _cislo(entry.get("stav_tachometru_predani"))
            km1 = _cislo(data.get("km_vraceni"))
            najeto = (km1 - km0) if (km0 is not None and km1 is not None) else None

            poznamky = []
            najezd = _cislo(entry.get("sjednany_najezd"))
            interval = entry.get("interval_najezdu") or "rok"
            povoleno = prekroceni = dopl_bez = dopl_s = None
            if najezd is None:
                poznamky.append(f"Sjednaný nájezd: {entry.get('sjednany_najezd') or 'neuveden'} — překročení se nepočítá.")
            elif dny is None:
                poznamky.append("Nelze určit délku nájmu (chybí datum začátku) — překročení se nepočítá.")
            else:
                if interval == "den":
                    povoleno = najezd * dny
                elif interval == "měsíc":
                    povoleno = najezd * max(1, math.ceil(dny / 30))
                else:
                    povoleno = najezd * dny / 365.0
                povoleno = round(povoleno)
                if najeto is not None:
                    prekroceni = max(0, round(najeto - povoleno))
                    dopl_bez = prekroceni * 9.0
                    dopl_s = dopl_bez * 1.21
                else:
                    poznamky.append("Chybí stav kilometrů při předání nebo vrácení — doplatek za km se nepočítá.")

            STUPNE = {"Plná": 8, "7/8": 7, "3/4": 6, "5/8": 5, "1/2": 4, "3/8": 3, "1/4": 2, "1/8": 1, "Prázdná": 0}
            n0, n1 = entry.get("stav_nadrze") or "", data.get("nadrz_vraceni") or ""
            if n0 in STUPNE and n1 in STUPNE and STUPNE[n1] < STUPNE[n0]:
                poznamky.append(f"Chybějící palivo ({n0} → {n1}): doúčtuje se dle skutečnosti "
                                "+ poplatek za dotankování 300 Kč bez DPH (čl. 6.4 VOP).")

            posk = _cislo(data.get("poskozeni_castka")) or 0
            posk_popis = (data.get("poskozeni_popis") or "").strip()
            mena = entry.get("mena", "CZK") or "CZK"
            celkem = None
            if mena == "CZK":
                celkem = (dopl_s or 0) + posk
                if not celkem:
                    celkem = None
            elif posk and dopl_s:
                poznamky.append("Doplatek za km je v Kč, poškození v " + mena + " — částky se nesčítají.")

            import unicodedata
            def _ascii(x):
                return unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode("ascii")

            vys = {
                "jmeno": entry.get("jmeno", ""), "vozidlo": entry.get("vozidlo", ""),
                "cislo_smlouvy": entry.get("cislo_smlouvy") or cislo_smlouvy_z_data(entry.get("datum_zacatku", "")),
                "vygenerovano": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "datum_zacatku": zac.strftime("%d.%m.%Y") if zac else entry.get("datum_zacatku", ""),
                "datum_vraceni": vra.strftime("%d.%m.%Y"),
                "kdo_vraci": data.get("kdo_vraci", ""),
                "km_predani": km0, "km_vraceni": km1, "najeto": najeto,
                "povoleno_km": povoleno, "prekroceni_km": prekroceni,
                "doplatek_bez": dopl_bez, "doplatek_s": dopl_s,
                "nadrz_predani": n0, "nadrz_vraceni": n1,
                "poskozeni": posk or None, "poskozeni_popis": posk_popis,
                "mena": "Kč" if mena == "CZK" else mena,
                "celkem_k_uhrade": celkem, "poznamky": poznamky,
            }
            # Volitelně faktura ve Vyfakturuj (km doplatek 21 % DPH, náhrada škody bez DPH)
            if data.get("vystavit_fakturu"):
                try:
                    cfg, cfg_err = load_vyfakturuj_config()
                    if cfg_err:
                        raise RuntimeError(cfg_err)
                    firma = entry.get("firma") or None
                    if firma and firma.get("nazev"):
                        c_name, c_ico, c_dic = firma.get("nazev"), firma.get("ico"), firma.get("dic")
                    else:
                        c_name, c_ico, c_dic = entry.get("jmeno", ""), None, None
                    c_adr = (firma.get("sidlo") if firma else entry.get("adresa")) or ""
                    contact_id = vyfakturuj_find_or_create_contact(
                        cfg, c_name, entry.get("email", ""), entry.get("telefon", ""), c_ico, c_dic, c_adr)
                    items = []
                    if prekroceni and prekroceni > 0:
                        if mena == "CZK":
                            items.append({"text": f"Překročení sjednaného nájezdu o {prekroceni} km × 9 Kč — "
                                                   f"vozidlo {entry.get('vozidlo','')}, smlouva č. {vys['cislo_smlouvy']}",
                                          "quantity": prekroceni, "unit_price": 9.0, "vat_rate": 21})
                        else:
                            poznamky.append("Sazba za km je v Kč — fakturu za překročení nájezdu u smlouvy v "
                                            + mena + " vystav ručně.")
                    if posk > 0:
                        items.append({"text": f"Náhrada škody — {posk_popis or 'poškození vozidla'} — "
                                               f"vozidlo {entry.get('vozidlo','')}, smlouva č. {vys['cislo_smlouvy']}",
                                      "quantity": 1, "unit_price": posk, "vat_rate": 0})
                    if items:
                        inv = vyfakturuj_request("POST", "/invoice/", cfg, json_body={
                            "id_customer": contact_id, "type": 1, "doc_currency": mena,
                            "doc_calculate_vat": 1, "items": items})
                        cislo_f = inv.get("number") if isinstance(inv, dict) else None
                        vys["faktura"] = f"Faktura vystavena ve Vyfakturuj" + (f" (č. {cislo_f})" if cislo_f else "")
                    else:
                        vys["faktura"] = "Není co fakturovat (žádné překročení ani poškození)."
                except Exception as fe:
                    vys["faktura_chyba"] = str(fe)

            fname = ("vyuctovani_" + _ascii(entry.get("jmeno", "najemce")).replace(" ", "_") + ".pdf")
            from smlouva_v2 import generate_vyuctovani, generate_smlouva_v2
            generate_vyuctovani(vys, os.path.join(SCRIPT_DIR, fname))

            # Předávací protokol s vyplněnou sekcí Vrácení (samostatné PDF,
            # podepsaná smlouva zůstává nedotčená)
            fname_protokol = None
            try:
                jm = (entry.get("jmeno") or "").split(" ", 1)
                osobni_p = {"jmeno": jm[0] if jm else "", "prijmeni": jm[1] if len(jm) > 1 else "",
                            "adresa": entry.get("adresa", "")}
                smlouva_p = {k: entry.get(k, "") for k in (
                    "vozidlo", "datum_zacatku", "cas_predani", "palivo", "misto_predani", "poskozeni_predani",
                    "misto_vraceni", "stav_tachometru_predani", "stav_nadrze", "nahradni_vozidlo")}
                smlouva_p["cislo_smlouvy"] = vys["cislo_smlouvy"]
                posk_text = ""
                if posk or posk_popis:
                    posk_text = posk_popis or "poškození vozidla"
                    if posk:
                        posk_text += f" — náhrada škody {posk:,.0f} {vys['mena']}".replace(",", " ")
                vraceni = {"poskozeni_nakres": data.get("poskozeni_nakres") or "",
                           "kdo_vraci": data.get("kdo_vraci", ""),
                           "datum_vraceni": vra.strftime("%d.%m.%Y"),
                           "km_vraceni": (f"{km1:,.0f}".replace(",", " ") if km1 is not None else ""),
                           "nadrz_vraceni": n1, "poskozeni_text": posk_text}
                fname_protokol = ("protokol_vraceni_" + _ascii(entry.get("jmeno", "najemce")).replace(" ", "_") + ".pdf")
                generate_smlouva_v2(osobni_p, smlouva_p, entry.get("firma") or None,
                                    os.path.join(SCRIPT_DIR, fname_protokol),
                                    vys["cislo_smlouvy"], typ_vozidla=entry.get("typ_vozidla", "osobni"),
                                    vraceni=vraceni, jen_protokol=True)
            except Exception:
                import traceback
                print("CHYBA (protokol vrácení):\n" + traceback.format_exc())
                fname_protokol = None

            return {"success": True, "filename": fname, "filename_protokol": fname_protokol, "vysledek": vys}
        except Exception as e:
            import traceback
            print("CHYBA (vyuctovani):\n" + traceback.format_exc())
            return {"success": False, "error": str(e)}

    def podpis_vlozit_route(self, data):
        """Vloží vlastnoruční podpis (PNG z canvas) do již vygenerované smlouvy —
        PDF se vygeneruje znovu se stejnými daty a stejným číslem smlouvy."""
        try:
            import re as re_p
            filename = data.get("smlouva_filename") or ""
            if not re_p.match(r"^smlouva_[A-Za-z0-9_.-]+\.pdf$", filename):
                raise RuntimeError("Neplatný název souboru smlouvy.")
            podpis_png = data.get("podpis_png") or ""
            if not podpis_png.startswith("data:image/png"):
                raise RuntimeError("Chybí podpis.")
            osobni_data = data.get("osobni_data") or {}
            smlouva_data = data.get("smlouva_data") or {}
            firma_data = data.get("firma_data") or None
            typ_vozidla = data.get("typ_vozidla", "osobni")
            cislo_smlouvy = smlouva_data.get("cislo_smlouvy") or cislo_smlouvy_z_data(smlouva_data.get("datum_zacatku", ""))
            if not osobni_data.get("jmeno"):
                raise RuntimeError("Chybí údaje smlouvy — nejdřív smlouvu vygeneruj.")
            output_path = os.path.join(SCRIPT_DIR, filename)
            _, podpis_pozice = generate_smlouva_v2(
                osobni_data, smlouva_data, firma_data, output_path,
                cislo_smlouvy, typ_vozidla=typ_vozidla, podpis_png=podpis_png)
            return {"success": True, "filename": filename}
        except Exception as e:
            import traceback
            print("CHYBA (podpis):\n" + traceback.format_exc())
            return {"success": False, "error": str(e)}

    def docuseal_stazeni_route(self, data):
        """Zjistí stav podpisu v DocuSeal a po dokončení stáhne podepsané PDF
        do složky generátoru jako <smlouva>_podepsana.pdf."""
        try:
            import re as re_s
            cfg, err = load_docuseal_config()
            if err:
                raise RuntimeError(err)
            sub_id = data.get("submission_id")
            if not sub_id:
                raise RuntimeError("Chybí ID odeslání — smlouvu nejdřív odešli k podpisu.")
            filename = data.get("smlouva_filename") or "smlouva.pdf"
            if not re_s.match(r"^[A-Za-z0-9_.-]+\.pdf$", filename):
                raise RuntimeError("Neplatný název souboru.")

            sub = docuseal_request("GET", f"/submissions/{sub_id}", cfg)
            stav = (sub.get("status") or "").lower() if isinstance(sub, dict) else ""
            if stav != "completed":
                podrobnosti = {"pending": "čeká na podepsání", "opened": "nájemce si smlouvu otevřel",
                               "sent": "odesláno, zatím nepodepsáno", "declined": "nájemce podpis ODMÍTL",
                               "expired": "platnost odkazu vypršela"}.get(stav, stav or "neznámý stav")
                return {"success": True, "stav": stav or "pending", "hotovo": False,
                        "zprava": f"Zatím nepodepsáno ({podrobnosti})."}

            # dokončeno — najdi URL podepsaných dokumentů
            urls = []
            for d in (sub.get("documents") or []):
                if isinstance(d, dict) and d.get("url"):
                    urls.append(d["url"])
            if not urls:
                for sm in (sub.get("submitters") or []):
                    for d in (sm.get("documents") or []):
                        if isinstance(d, dict) and d.get("url"):
                            urls.append(d["url"])
            if not urls:
                raise RuntimeError("Podepsaný dokument se v DocuSeal nepodařilo najít.")
            r = requests.get(urls[0], timeout=60)
            r.raise_for_status()
            out_name = filename[:-4] + "_podepsana.pdf"
            with open(os.path.join(SCRIPT_DIR, out_name), "wb") as f:
                f.write(r.content)
            audit = sub.get("audit_log_url")
            return {"success": True, "stav": "completed", "hotovo": True, "filename": out_name,
                    "zprava": "Podepsáno — podepsaná smlouva je uložena ve složce generátoru.",
                    "audit_url": audit}
        except Exception as e:
            import traceback
            print("CHYBA (docuseal stažení):\n" + traceback.format_exc())
            return {"success": False, "error": str(e)}

    def extract_doc_route(self, data):
        try:
            return {"success": True, "pole": parse_dokument_najmu(data.get("files") or [])}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def docuseal_send_route(self, data):
        try:
            osobni_data = data.get("osobni_data", {})
            smlouva_data = data.get("smlouva_data", {})
            filename = data.get("smlouva_filename", "")
            podpis_pozice = data.get("podpis_pozice") or None
            send_sms = bool(data.get("send_sms"))
            if not filename:
                raise RuntimeError("Chybí název souboru vygenerované smlouvy — nejdřív ji vygeneruj.")
            pdf_path = os.path.join(SCRIPT_DIR, filename)
            result = docuseal_send_for_signature(osobni_data, smlouva_data, pdf_path, podpis_pozice, send_sms)
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def process(self, data):
        try:
            rp_data = data.get("rp_data",{})
            op_data = data.get("op_data",{})
            smlouva_data = data.get("smlouva_data",{})
            firma_data = data.get("firma_data") or None
            typ_vozidla = data.get("typ_vozidla", "osobni")
            demo = data.get("demo", False)

            if demo:
                rp_data = DEMO_RP
                op_data = DEMO_OP

            osobni_data = {
                "jmeno": rp_data.get("jmeno") or op_data.get("jmeno",""),
                "prijmeni": rp_data.get("prijmeni") or op_data.get("prijmeni",""),
                "datum_narozeni": rp_data.get("datum_narozeni") or op_data.get("datum_narozeni",""),
                "misto_narozeni": op_data.get("misto_narozeni") or rp_data.get("misto_narozeni",""),
                "rodne_cislo": op_data.get("rodne_cislo"),
                "cislo_rp": rp_data.get("cislo_rp"), "datum_vydani_rp": rp_data.get("datum_vydani_rp"),
                "platnost_rp": rp_data.get("platnost_rp"), "cislo_op": op_data.get("cislo_op"),
                "datum_vydani_op": op_data.get("datum_vydani_op"), "platnost_op": op_data.get("platnost_op"),
                "adresa": op_data.get("adresa") or rp_data.get("adresa"),
                "korespondencni_adresa": smlouva_data.get("korespondencni_adresa", ""),
                "zeme_op": (op_data.get("zeme_vydani") or "").upper()[:2] or "CZ",
                "zeme_rp": (rp_data.get("zeme_vydani") or "").upper()[:2] or "CZ",
            }
            jmeno = osobni_data["jmeno"]; prijmeni = osobni_data["prijmeni"]
            datum = osobni_data["datum_narozeni"]
            admin = bool(data.get("admin"))
            if (not jmeno or not prijmeni) and not admin:
                return {"error":"Nepodařilo se přečíst jméno z dokladů."}
            if admin and (not jmeno or not prijmeni or not datum):
                data["skip_lustrace"] = True   # bez úplných údajů nelze lustrovat

            if demo:
                lus = DEMO_LUSTRACE
                print("🧪 DEMO — lustrace přeskočena")
            elif data.get("skip_lustrace"):
                lus = {"pocet_exekuci": None, "ma_exekuce": False,
                       "cena_halerov": 0, "kredit_halerov": 0, "pdf_name": None}
                print("⏭️  Lustrace přeskočena uživatelem")
            else:
                print(f"🔍 Lustruji {jmeno} {prijmeni} ({datum})...")
                lus = lustrace_cee(jmeno, prijmeni, datum)
                print(f"✅ Lustrace: {lus['pocet_exekuci']} exekucí")

            import unicodedata
            def odstran_diakritiku(s):
                return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

            # Vždy vygenerujeme obě verze — která se stáhne, se vybírá až v posledním kroku.
            # V2 (PDF) je hlavní (jde z ní odeslání k podpisu i podpisové pole); V1 (Excel) je doplňková.
            podpis_pozice = None
            if prijmeni or jmeno:
                base = f"smlouva_{odstran_diakritiku(prijmeni)}_{odstran_diakritiku(jmeno)}".replace(" ","_")
            else:
                from datetime import datetime as _dt_b
                base = "smlouva_ADMIN_" + _dt_b.now().strftime("%H%M%S")
            if demo:
                base += "_test"
            output_filename = base + ".pdf"
            output_path = os.path.join(SCRIPT_DIR, output_filename)
            # Při opravě z výsledkové stránky už klient číslo smlouvy posílá —
            # znovu se nepřiděluje, ať oprava překlepu nespálí číslo z řady.
            cislo_smlouvy = (smlouva_data.get("cislo_smlouvy") or "").strip()
            if not cislo_smlouvy or demo:
                cislo_smlouvy = dalsi_cislo_smlouvy(smlouva_data.get('datum_zacatku',''), demo=demo)
            smlouva_data = dict(smlouva_data)
            smlouva_data["cislo_smlouvy"] = cislo_smlouvy
            try:
                _, podpis_pozice = generate_smlouva_v2(osobni_data, smlouva_data, firma_data, output_path,
                                     cislo_smlouvy, typ_vozidla=typ_vozidla)
                sp, se = output_path, None
            except Exception as e:
                import traceback
                print("CHYBA (v2):\n" + traceback.format_exc())
                sp, se = None, str(e)

            output_filename_v1 = base + ".xlsx"
            smlouva_v1 = dict(smlouva_data)
            if smlouva_v1.get("flexi"):
                smlouva_v1["datum_konce"] = "FLEXI"
            try:
                sp1, se1 = vyplnit_smlouvu(osobni_data, smlouva_v1, os.path.join(SCRIPT_DIR, output_filename_v1))
            except Exception as e:
                import traceback
                print("CHYBA (v1):\n" + traceback.format_exc())
                sp1, se1 = None, str(e)

            if sp:
                save_to_history(osobni_data, smlouva_data, output_filename, firma_data, typ_vozidla)
            return {
                "success":True,"osobni_data":osobni_data,"demo":demo,
                "lustrace":{"pocet_exekuci":lus["pocet_exekuci"],"ma_exekuce":lus["ma_exekuce"],
                            "cena_kc":lus["cena_halerov"]/100,"kredit_kc":lus["kredit_halerov"]/100,
                            "pdf_name":lus["pdf_name"]},
                "cislo_smlouvy": cislo_smlouvy,
                "smlouva":{"filename":output_filename if sp else None,"error":se,
                           "filename_v1":output_filename_v1 if sp1 else None,"error_v1":se1,
                           "podpis_pozice":podpis_pozice if sp else None}
            }
        except Exception as e:
            import traceback; return {"error":str(e),"traceback":traceback.format_exc()}


if __name__ == "__main__":
    port = 8765
    print(f"\n🚗 RX Auto — Lustrace & Smlouvy\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ Server spuštěn na http://localhost:{port}")
    print(f"📁 {SCRIPT_DIR}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    lan = os.path.exists(os.path.join(SCRIPT_DIR, "lan_mode.txt"))
    host = "0.0.0.0" if lan else "localhost"
    if lan:
        import socket
        try:
            _s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); _s.connect(("8.8.8.8", 80)); ip = _s.getsockname()[0]; _s.close()
        except Exception:
            ip = "IP-tohoto-počítače"
        print(f"📱 LAN režim ZAPNUTÝ (soubor lan_mode.txt) — z mobilu ve stejné Wi-Fi otevři http://{ip}:{port}")
        print("⚠️  Aplikace je pak dostupná komukoli ve stejné síti. Vypneš smazáním lan_mode.txt a restartem.\n")
    HTTPServer((host, port), AppHandler).serve_forever()
