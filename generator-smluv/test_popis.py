"""Testy předvyplnění z textového popisu (LLM mockované)."""
import os, sys, json, datetime
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server as srv

def fake_llm(payload):
    msg = MagicMock(); msg.content = [MagicMock(text="```json\n"+json.dumps(payload)+"\n```")]
    return patch.object(srv.anthropic_client.messages, "create", return_value=msg)

def test_priklad_od_erika():
    dnes = datetime.date.today()
    llm = dict(spz="1alb766", znacka_model="BMW 2", typ_vozidla=None, cena=10000, cena_dph="bez_dph", mena=None,
               interval_ceny="měsíčně", jistina=15000, sjednany_najezd=2500, interval_najezdu="měsíc",
               datum_zacatku=dnes.isoformat(), datum_konce=None, delka_mesicu=6, delka_dnu=None,
               email=None, telefon=None, misto_predani=None, misto_vraceni=None)
    with fake_llm(llm):
        r = srv.parse_popis_najmu("10000 měsíčně bez dph, kauce 15tis, nájezd 2500km měsíčně, začátek dneska konec za půl roku, auto bmw 2 1ALB766")
    assert r["vozidlo"] == "1ALB766 — BMW 2"
    assert r["cena"] == "10000" and r["cena_dph"] == "bez_dph" and r["jistina"] == "15000"
    assert r["sjednany_najezd"] == "2500" and r["interval_najezdu"] == "měsíc"
    assert r["datum_konce"] == srv._pridej_mesice(dnes, 6).isoformat()
    assert r["email"] is None
    print("OK test_priklad_od_erika")

def test_flexi_a_firma():
    llm = dict(spz="9H06380", znacka_model="Škoda Kodiaq", cena=1400, cena_dph="bez_dph", interval_ceny="denně",
               jistina=None, bez_kauce=True, neomezeny_najezd=True, sjednany_najezd=None, flexi=True, nahradni_vozidlo=True,
               ico="08330401", datum_zacatku="2026-08-02", datum_konce="2026-09-07", delka_mesicu=None)
    with fake_llm(llm):
        r = srv.parse_popis_najmu("x")
    assert r["flexi"] and r["nahradni_vozidlo"] and r["ico"] == "08330401"
    assert r["datum_konce"] is None and r["jistina"] == "0" and r["sjednany_najezd"] == "Neomezený"
    assert r["interval_ceny"] == "denně"
    print("OK test_flexi_a_firma")

def test_dokument_pdf_a_foto():
    llm = dict(spz="9H06380", znacka_model="Škoda Kodiaq", cena=1400, cena_dph="bez_dph", interval_ceny="denně",
               datum_zacatku="2026-08-02", datum_konce="2026-09-07", ico="08330401", firma_nazev="Firma s.r.o.", ridic="Jiří Štědroň")
    msg = MagicMock(); msg.content = [MagicMock(text=json.dumps(llm))]
    with patch.object(srv.anthropic_client.messages, "create", return_value=msg) as c:
        r = srv.parse_dokument_najmu([{"data": "QUJD", "media_type": "application/pdf"}, {"data": "QUJD", "media_type": "image/jpg"}])
    blocks = c.call_args.kwargs["messages"][0]["content"]
    assert blocks[0]["type"] == "document" and blocks[1]["type"] == "image" and blocks[1]["source"]["media_type"] == "image/jpeg"
    assert r["firma_nazev"] == "Firma s.r.o." and r["ridic"] == "Jiří Štědroň" and r["vozidlo"] == "9H06380 — Škoda Kodiaq"
    try: srv.parse_dokument_najmu([]); assert False
    except RuntimeError: pass
    print("OK test_dokument_pdf_a_foto")

def test_pridej_mesice():
    d = datetime.date
    assert srv._pridej_mesice(d(2026,10,7), 6) == d(2027,4,7)
    assert srv._pridej_mesice(d(2026,8,31), 6) == d(2027,2,28)
    assert srv._pridej_mesice(d(2026,12,15), 1) == d(2027,1,15)
    print("OK test_pridej_mesice")

def test_prazdny_text():
    try: srv.parse_popis_najmu("  "); assert False
    except RuntimeError: pass
    print("OK test_prazdny_text")

def test_nesmysly_se_zahodi():
    llm = dict(spz=None, znacka_model=None, typ_vozidla="tank", cena="abc", cena_dph="x", mena="USD", interval_ceny="ročně",
               jistina=None, sjednany_najezd=None, interval_najezdu="hodina", datum_zacatku="blbost", datum_konce=None,
               delka_mesicu=None, delka_dnu=None, email=None, telefon=None, misto_predani=None, misto_vraceni=None)
    with fake_llm(llm):
        r = srv.parse_popis_najmu("cokoliv")
    assert all(v in (None, False) for v in r.values()), r
    print("OK test_nesmysly_se_zahodi")

if __name__ == "__main__":
    test_dokument_pdf_a_foto(); test_flexi_a_firma(); test_priklad_od_erika(); test_pridej_mesice(); test_prazdny_text(); test_nesmysly_se_zahodi()
    print("\nVŠECHNY TESTY PROŠLY ✅")
