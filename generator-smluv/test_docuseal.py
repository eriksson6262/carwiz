"""
Testy pro integraci s DocuSeal — bez reálných přihlašovacích údajů,
veškerá HTTP komunikace je mockovaná (unittest.mock).
"""
import os, sys, json, base64
from unittest.mock import patch, MagicMock

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import server as srv

CONFIG_PATH = srv.DOCUSEAL_CONFIG_FILE
TEST_PDF_PATH = os.path.join(SCRIPT_DIR, "_test_docuseal_smlouva.pdf")


def with_temp_config(fn):
    def wrapper():
        existed = os.path.exists(CONFIG_PATH)
        backup = None
        if existed:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                backup = f.read()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"api_key": "TESTKEY", "base_url": "https://api.docuseal.com"}, f)
        try:
            fn()
        finally:
            if backup is not None:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    f.write(backup)
            else:
                os.remove(CONFIG_PATH)
    return wrapper


def with_temp_pdf(fn):
    def wrapper():
        with open(TEST_PDF_PATH, "wb") as f:
            f.write(b"%PDF-1.4 fake test pdf content")
        try:
            fn()
        finally:
            if os.path.exists(TEST_PDF_PATH):
                os.remove(TEST_PDF_PATH)
    return wrapper


def test_config_missing():
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
    cfg, err = srv.load_docuseal_config()
    assert cfg is None
    assert "nebyl nalezen" in err
    print("OK test_config_missing")


def test_config_incomplete():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"api_key": ""}, f)
    try:
        cfg, err = srv.load_docuseal_config()
        assert cfg is None
        assert "chybí" in err
    finally:
        os.remove(CONFIG_PATH)
    print("OK test_config_incomplete")


@with_temp_config
def test_missing_pdf():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"email": "jan.novak@example.com"}
    try:
        srv.docuseal_send_for_signature(osobni, smlouva, os.path.join(SCRIPT_DIR, "neexistuje.pdf"))
        assert False, "mělo vyhodit výjimku"
    except RuntimeError as e:
        assert "nebyla nalezena" in str(e)
    print("OK test_missing_pdf")


@with_temp_config
@with_temp_pdf
def test_missing_email():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {}  # bez e-mailu
    try:
        srv.docuseal_send_for_signature(osobni, smlouva, TEST_PDF_PATH)
        assert False, "mělo vyhodit výjimku"
    except RuntimeError as e:
        assert "e-mail" in str(e)
    print("OK test_missing_email")


@with_temp_config
@with_temp_pdf
def test_full_flow_success():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"email": "jan.novak@example.com", "vozidlo": "1AB2345 — BMW 320d"}

    calls = []

    def fake_request(method, url, headers=None, json=None, timeout=None):
        calls.append((method, url, headers, json))
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{
            "id": 1, "submission_id": 555, "email": "jan.novak@example.com",
            "role": "Nájemce", "status": "pending",
        }]
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.docuseal_send_for_signature(osobni, smlouva, TEST_PDF_PATH)

    assert result["submission_id"] == 555
    assert result["email"] == "jan.novak@example.com"

    assert len(calls) == 1
    method, url, headers, payload = calls[0]
    assert method == "POST"
    assert url.endswith("/submissions/pdf")
    assert headers["X-Auth-Token"] == "TESTKEY"
    assert payload["submitters"][0]["email"] == "jan.novak@example.com"
    assert payload["submitters"][0]["role"] == "Nájemce"
    assert payload["documents"][0]["file"].startswith("data:application/pdf;base64,")
    # ověř, že base64 obsah opravdu odpovídá souboru
    b64_part = payload["documents"][0]["file"].split(",", 1)[1]
    with open(TEST_PDF_PATH, "rb") as f:
        assert base64.b64decode(b64_part) == f.read()
    print("OK test_full_flow_success")


@with_temp_config
@with_temp_pdf
def test_podpis_pozice_adds_signature_field():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"email": "jan.novak@example.com"}
    podpis_pozice = {"page": 1, "x": 0.5, "y": 0.81, "w": 0.4, "h": 0.05}

    calls = []

    def fake_request(method, url, headers=None, json=None, timeout=None):
        calls.append((method, url, headers, json))
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": 1, "submission_id": 556, "email": smlouva["email"]}]
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.docuseal_send_for_signature(osobni, smlouva, TEST_PDF_PATH, podpis_pozice=podpis_pozice)

    assert result["submission_id"] == 556
    payload = calls[0][3]
    fields = payload["documents"][0]["fields"]
    assert len(fields) == 1
    assert fields[0]["type"] == "signature"
    assert fields[0]["role"] == "Nájemce"
    area = fields[0]["areas"][0]
    assert area == {"x": 0.5, "y": 0.81, "w": 0.4, "h": 0.05, "page": 1}
    print("OK test_podpis_pozice_adds_signature_field")


@with_temp_config
@with_temp_pdf
def test_no_podpis_pozice_omits_fields():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"email": "jan.novak@example.com"}

    calls = []

    def fake_request(method, url, headers=None, json=None, timeout=None):
        calls.append((method, url, headers, json))
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": 1, "submission_id": 557, "email": smlouva["email"]}]
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        srv.docuseal_send_for_signature(osobni, smlouva, TEST_PDF_PATH, podpis_pozice=None)

    payload = calls[0][3]
    assert "fields" not in payload["documents"][0]
    print("OK test_no_podpis_pozice_omits_fields")


@with_temp_config
@with_temp_pdf
def test_send_sms_with_phone():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"email": "jan.novak@example.com", "telefon": "+420 777 123 456"}

    calls = []

    def fake_request(method, url, headers=None, json=None, timeout=None):
        calls.append((method, url, headers, json))
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": 1, "submission_id": 558, "email": smlouva["email"]}]
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.docuseal_send_for_signature(osobni, smlouva, TEST_PDF_PATH, send_sms=True)

    assert result["sms_sent"] is True
    assert result["sms_skipped_no_phone"] is False
    submitter = calls[0][3]["submitters"][0]
    assert submitter["phone"] == "+420777123456"
    assert submitter["send_sms"] is True
    print("OK test_send_sms_with_phone")


@with_temp_config
@with_temp_pdf
def test_send_sms_without_phone_number():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"email": "jan.novak@example.com"}  # bez telefonu

    calls = []

    def fake_request(method, url, headers=None, json=None, timeout=None):
        calls.append((method, url, headers, json))
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": 1, "submission_id": 559, "email": smlouva["email"]}]
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        result = srv.docuseal_send_for_signature(osobni, smlouva, TEST_PDF_PATH, send_sms=True)

    assert result["sms_sent"] is False
    assert result["sms_skipped_no_phone"] is True
    submitter = calls[0][3]["submitters"][0]
    assert "phone" not in submitter
    assert "send_sms" not in submitter
    print("OK test_send_sms_without_phone_number")


def test_normalizuj_telefon_e164():
    assert srv._normalizuj_telefon_e164("+420 777 123 456") == "+420777123456"
    assert srv._normalizuj_telefon_e164("777123456") == "+420777123456"
    assert srv._normalizuj_telefon_e164("00420777123456") == "+420777123456"
    assert srv._normalizuj_telefon_e164("") is None
    assert srv._normalizuj_telefon_e164(None) is None
    print("OK test_normalizuj_telefon_e164")


@with_temp_config
@with_temp_pdf
def test_api_error_surfaces_message():
    osobni = {"jmeno": "Jan", "prijmeni": "Novák"}
    smlouva = {"email": "jan.novak@example.com"}

    def fake_request(method, url, headers=None, json=None, timeout=None):
        resp = MagicMock()
        resp.status_code = 422
        resp.json.return_value = {"error": "Invalid submitter email"}
        resp.text = '{"error": "Invalid submitter email"}'
        return resp

    with patch("server.requests.request", side_effect=fake_request):
        try:
            srv.docuseal_send_for_signature(osobni, smlouva, TEST_PDF_PATH)
            assert False, "mělo vyhodit výjimku"
        except RuntimeError as e:
            assert "Invalid submitter email" in str(e)
    print("OK test_api_error_surfaces_message")


if __name__ == "__main__":
    test_config_missing()
    test_config_incomplete()
    test_missing_pdf()
    test_missing_email()
    test_full_flow_success()
    test_podpis_pozice_adds_signature_field()
    test_no_podpis_pozice_omits_fields()
    test_send_sms_with_phone()
    test_send_sms_without_phone_number()
    test_normalizuj_telefon_e164()
    test_api_error_surfaces_message()
    print("\nVŠECHNY TESTY PROŠLY ✅")
