"""
Testy pro integraci s Vyfakturuj — bez reálných přihlašovacích údajů,
veškerá HTTP komunikace je mockovaná (unittest.mock).
"""
import os, sys, json
from unittest.mock import patch, MagicMock

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import server as srv

CONFIG_PATH = srv.VYFAKTURUJ_CONFIG_FILE


def with_temp_config(fn):
    def wrapper():
        # zajisti čistý config soubor pro test, po testu ho smaž
        existed = os.path.exists(CONFIG_PATH)
        backup = None
        if existed:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                backup = f.read()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"email": "test@example.com", "api_key": "TESTKEY"}, f)
        try:
            fn()
        finally:
            if backup is not None:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    f.write(backup)
            else:
                os.remove(CONFIG_PATH)
    return wrapper


def test_split_spz():
    assert srv.vyfakturuj_split_spz("1AB2345 — BMW 320d") == "1AB2345"
    assert srv.vyfakturuj_split_spz("1AB2345 – BMW 320d") == "1AB2345"
    assert srv.vyfakturuj_split_spz("1AB2345 - BMW 320d") == "1AB2345"
    assert srv.vyfakturuj_split_spz("1AB2345") == "1AB2345"
    assert srv.vyfakturuj_split_spz("") == ""
    print("OK test_split_spz")


def test_config_missing():
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
    cfg, err = srv.load_vyfakturuj_config()
    assert cfg is None
    assert "nebyl nalezen" in err
    print("OK test_config_missing")


def test_config_incomplete():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"email": "x@example.com", "api_key": ""}, f)
    try:
        cfg, err = srv.load_vyfakturuj_config()
        assert cfg is None
        assert "chybí" in err
    finally:
        os.remove(CONFIG_PATH)
    print("OK test_config_incomplete")


@with_temp_config
def test_denni_najem_jednorazova_faktura():
    """Denní sazba + nájemné → JEDNA faktura: kauce + celá doba (dny × sazba)."""
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"vozidlo": "1AB2345 — BMW 320d", "interval_ceny": "denně", "cena": "1500",
               "pocet_intervalu": "36", "jistina": "15000", "mena": "CZK",
               "datum_zacatku": "2026-10-07", "datum_konce": "2026-11-12"}
    calls = []

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        calls.append((method, url, json))
        resp = MagicMock(); resp.status_code = 200
        if method == "GET" and url.endswith("/contact/"):
            resp.json.return_value = {"data": []}
        elif method == "POST" and url.endswith("/contact/"):
            resp.json.return_value = {"id": 7}
        elif method == "POST" and url.endswith("/invoice/"):
            resp.json.return_value = {"id": 100, "number": "20260042"}
        else:
            resp.status_code = 404; resp.json.return_value = {"status": "error", "message": "not found"}
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.vyfakturuj_import(osobni, smlouva, None, vcetne_najmu=True)

    inv_calls = [c for c in calls if c[1].endswith("/invoice/")]
    assert len(inv_calls) == 1, inv_calls          # kauce + nájem na JEDNÉ faktuře
    items = inv_calls[0][2]["items"]
    assert len(items) == 2
    assert items[0]["vat_rate"] == 0 and items[0]["unit_price"] == 15000.0
    assert items[1]["vat_rate"] == 21 and items[1]["quantity"] == 36.0 and items[1]["unit_price"] == 1500.0
    assert inv_calls[0][2]["type"] == 2            # default = zálohová
    assert not [c for c in calls if c[1].endswith("/template/")]
    print("OK test_denni_najem_jednorazova_faktura")


@with_temp_config
def test_mesicni_kauce_plus_prvni_mesic():
    """Měsíčně: 1. faktura = kauce + 1. měsíc, pravidelná od 2. měsíce, ostrá na přání."""
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"vozidlo": "1AB2345 — BMW 320d", "interval_ceny": "měsíčně", "cena": "12000",
               "jistina": "20000", "mena": "CZK",
               "datum_zacatku": "2026-10-13", "datum_konce": "2027-10-12"}
    calls = []

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        calls.append((method, url, json))
        resp = MagicMock(); resp.status_code = 200
        if method == "GET" and url.endswith("/contact/"):
            resp.json.return_value = {"data": []}
        elif method == "POST" and url.endswith("/contact/"):
            resp.json.return_value = {"id": 7}
        elif method == "POST" and url.endswith("/invoice/"):
            resp.json.return_value = {"id": 100, "number": "20260042"}
        elif method == "POST" and url.endswith("/template/"):
            resp.json.return_value = {"id": 999}
        else:
            resp.status_code = 404; resp.json.return_value = {"status": "error", "message": "not found"}
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.vyfakturuj_import(osobni, smlouva, None, vcetne_najmu=True, typ_dokladu="ostra")

    inv = [c for c in calls if c[1].endswith("/invoice/")][0][2]
    assert inv["type"] == 1                        # ostrá
    assert len(inv["items"]) == 2                  # kauce + 1. měsíc
    assert inv["items"][0]["vat_rate"] == 0 and inv["items"][0]["unit_price"] == 20000.0
    assert inv["items"][1]["vat_rate"] == 21 and inv["items"][1]["unit_price"] == 12000.0
    assert "1. měsíc" in inv["items"][1]["text"] and "13.10.2026" in inv["items"][1]["text"]
    tmpl = [c for c in calls if c[1].endswith("/template/")][0][2]
    assert tmpl["date_start"] == "2026-11-13"      # pravidelná od 2. měsíce
    assert tmpl["date_end"] == "2027-10-12"
    assert len(result["zpravy"]) == 2
    print("OK test_mesicni_kauce_plus_prvni_mesic")


@with_temp_config
def test_jen_jistina():
    """Bez zatrženého nájemného se vystaví jen zálohová faktura na jistinu."""
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"vozidlo": "1AB2345 — BMW 320d", "interval_ceny": "měsíčně", "cena": "12000",
               "jistina": "20000", "mena": "CZK", "datum_zacatku": "2026-10-01", "datum_konce": ""}
    calls = []

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        calls.append((method, url, json))
        resp = MagicMock(); resp.status_code = 200
        if method == "GET" and url.endswith("/contact/"):
            resp.json.return_value = {"data": []}
        elif method == "POST" and url.endswith("/contact/"):
            resp.json.return_value = {"id": 7}
        elif method == "POST" and url.endswith("/invoice/"):
            resp.json.return_value = {"id": 101}
        else:
            resp.status_code = 404; resp.json.return_value = {"status": "error", "message": "not found"}
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.vyfakturuj_import(osobni, smlouva, None, vcetne_najmu=False)

    assert not [c for c in calls if c[1].endswith("/template/")]
    assert len([c for c in calls if c[1].endswith("/invoice/")]) == 1
    print("OK test_jen_jistina")


@with_temp_config
def test_bez_jistiny_bez_najmu_chyba():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"vozidlo": "1AB2345 — BMW 320d", "interval_ceny": "měsíčně", "cena": "12000",
               "datum_zacatku": "2026-10-01"}

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        resp = MagicMock(); resp.status_code = 200
        if method == "GET": resp.json.return_value = {"data": []}
        else: resp.json.return_value = {"id": 7}
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        try:
            srv.vyfakturuj_import(osobni, smlouva, None, vcetne_najmu=False)
            assert False, "mělo vyhodit výjimku"
        except RuntimeError as e:
            assert "Jistina" in str(e)
    print("OK test_bez_jistiny_bez_najmu_chyba")


@with_temp_config
def test_full_flow_new_contact():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {
        "vozidlo": "1AB2345 — BMW 320d", "interval_ceny": "měsíčně",
        "cena": "12000", "mena": "CZK",
        "datum_zacatku": "2026-10-01", "datum_konce": "2027-09-30",
        "email": "jan.novak@example.com", "telefon": "+420777123456",
    }

    calls = []

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        calls.append((method, url, params, json))
        resp = MagicMock()
        resp.status_code = 200
        if method == "GET" and url.endswith("/contact/"):
            resp.json.return_value = {"data": []}   # žádný existující kontakt
        elif method == "POST" and url.endswith("/contact/"):
            resp.json.return_value = {"id": 555, "name": params_or_json_name(json)}
        elif method == "POST" and url.endswith("/invoice/"):
            resp.json.return_value = {"id": 100, "number": "X1"}
        elif method == "POST" and url.endswith("/template/"):
            resp.json.return_value = {"id": 999, "name": json.get("name")}
        else:
            resp.status_code = 404
            resp.json.return_value = {"status": "error", "message": "not found"}
        return resp

    def params_or_json_name(j):
        return (j or {}).get("name")

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.vyfakturuj_import(osobni, smlouva, None, vcetne_najmu=True)

    assert result["contact_id"] == 555
    assert result["name"] == "1AB2345 Jan Novák", result["name"]

    # ověř, že se skutečně zavolal GET (search), POST /contact/ (vytvoření) a POST /template/
    methods_urls = [(m, u.split("/2.0")[-1]) for m, u, p, j in calls]
    assert ("GET", "/contact/") in methods_urls
    assert ("POST", "/contact/") in methods_urls
    assert ("POST", "/template/") in methods_urls

    # ověř payload pravidelné faktury
    tmpl_call = [c for c in calls if c[1].endswith("/template/") and c[0] == "POST"][0]
    payload = tmpl_call[3]
    assert payload["type"] == 2
    assert payload["id_customer"] == 555
    assert payload["name"] == "1AB2345 Jan Novák"
    assert payload["repeat_period"] == 1
    assert payload["date_start"] == "2026-11-01"
    assert payload["date_end"] == "2027-09-30"
    assert payload["end_type"] == 2
    assert payload["items"][0]["unit_price"] == 12000.0
    assert payload["items"][0]["vat_rate"] == 21
    print("OK test_full_flow_new_contact")


@with_temp_config
def test_full_flow_existing_contact_and_firma():
    osobni = {"jmeno": "Petr", "prijmeni": "Svoboda"}
    firma = {"nazev": "ACME s.r.o.", "ico": "12345678", "dic": "CZ12345678"}
    smlouva = {
        "vozidlo": "2CD9999 — Škoda Octavia", "interval_ceny": "měsíčně",
        "cena": "9500", "mena": "CZK",
        "datum_zacatku": "2026-11-01", "datum_konce": "",
        "email": "fakturace@acme.cz", "telefon": "",
    }

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        resp = MagicMock()
        resp.status_code = 200
        if method == "GET" and url.endswith("/contact/"):
            # existující kontakt se shoduje přesně podle názvu
            resp.json.return_value = {"data": [{"id": 42, "name": "ACME s.r.o."}]}
        elif method == "PUT" and "/contact/" in url:
            resp.json.return_value = {"id": 42}
        elif method == "POST" and url.endswith("/invoice/"):
            resp.json.return_value = {"id": 101, "number": "X2"}
        elif method == "POST" and url.endswith("/template/"):
            resp.json.return_value = {"id": 1001, "name": json.get("name")}
        else:
            resp.status_code = 500
            resp.json.return_value = {"status": "error", "message": "neočekávané volání"}
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.vyfakturuj_import(osobni, smlouva, firma, vcetne_najmu=True)

    assert result["contact_id"] == 42          # nalezen existující kontakt, žádné POST /contact/
    assert result["name"] == "2CD9999 Petr Svoboda"
    print("OK test_full_flow_existing_contact_and_firma")


@with_temp_config
def test_full_flow_s_dph_price():
    # cena zadaná VČETNĚ DPH musí být do Vyfakturuj (doc_calculate_vat=1)
    # poslána přepočtená na základ daně (bez DPH)
    osobni = {"jmeno": "Eva", "prijmeni": "Malá"}
    smlouva = {
        "vozidlo": "3EF7777 — Hyundai i30", "interval_ceny": "měsíčně",
        "cena": "12100", "cena_dph": "s_dph", "mena": "CZK",
        "datum_zacatku": "2026-12-01", "datum_konce": "",
        "email": "eva.mala@example.com", "telefon": "",
    }

    calls = []

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        calls.append((method, url, json))
        resp = MagicMock()
        resp.status_code = 200
        if method == "GET" and url.endswith("/contact/"):
            resp.json.return_value = {"data": []}
        elif method == "POST" and url.endswith("/contact/"):
            resp.json.return_value = {"id": 77, "name": (json or {}).get("name")}
        elif method == "POST" and url.endswith("/invoice/"):
            resp.json.return_value = {"id": 102, "number": "X3"}
        elif method == "POST" and url.endswith("/template/"):
            resp.json.return_value = {"id": 88, "name": json.get("name")}
        else:
            resp.status_code = 404
            resp.json.return_value = {"status": "error", "message": "not found"}
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.vyfakturuj_import(osobni, smlouva, None, vcetne_najmu=True)

    assert result["zpravy"]
    tmpl_call = [c for c in calls if c[1].endswith("/template/") and c[0] == "POST"][0]
    unit_price = tmpl_call[2]["items"][0]["unit_price"]
    # 12100 vč. DPH / 1.21 = 10000 bez DPH
    assert abs(unit_price - 10000.0) < 0.01, unit_price
    print("OK test_full_flow_s_dph_price")


@with_temp_config
def test_api_error_surfaces_message():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"vozidlo": "1AB2345 — BMW 320d", "interval_ceny": "měsíčně", "cena": "1000",
               "datum_zacatku": "2026-10-01", "datum_konce": ""}

    def fake_request(method, url, auth=None, json=None, params=None, timeout=None):
        resp = MagicMock()
        if method == "GET":
            resp.status_code = 200
            resp.json.return_value = {"data": []}
        elif method == "POST" and url.endswith("/contact/"):
            resp.status_code = 200
            resp.json.return_value = {"id": 1}
        else:
            resp.status_code = 400
            resp.json.return_value = {"status": "error", "message": "Validation failed",
                                       "inputError": {"id_payment_method": ["Neplatná hodnota."]}}
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        try:
            srv.vyfakturuj_import(osobni, smlouva, None, vcetne_najmu=True)
            assert False, "mělo vyhodit výjimku"
        except RuntimeError as e:
            assert "Validation failed" in str(e)
            assert "id_payment_method" in str(e)
    print("OK test_api_error_surfaces_message")


if __name__ == "__main__":
    test_split_spz()
    test_config_missing()
    test_config_incomplete()
    test_denni_najem_jednorazova_faktura()
    test_mesicni_kauce_plus_prvni_mesic()
    test_jen_jistina()
    test_bez_jistiny_bez_najmu_chyba()
    test_full_flow_new_contact()
    test_full_flow_existing_contact_and_firma()
    test_full_flow_s_dph_price()
    test_api_error_surfaces_message()
    print("\nVŠECHNY TESTY PROŠLY ✅")
