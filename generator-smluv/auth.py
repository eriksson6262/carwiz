#!/usr/bin/env python3
"""Přihlášení, uživatelé a auditní log generátoru smluv.

Data (nejsou v gitu):
  users.json       – uživatelé (hesla jen jako PBKDF2 hash)
  audit_log.jsonl  – kdo, kdy, co udělal (jeden JSON na řádek)

CLI:
  python3 auth.py pridat <login> "<Jméno Příjmení>" [admin|obsluha]   – založí uživatele (heslo se zeptá)
  python3 auth.py heslo <login>                                       – změní heslo
  python3 auth.py seznam                                              – vypíše uživatele
"""
import os, json, hashlib, secrets, threading, time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(SCRIPT_DIR, "users.json")
AUDIT_FILE = os.path.join(SCRIPT_DIR, "audit_log.jsonl")
SESSIONS_FILE = os.path.join(SCRIPT_DIR, "sessions.json")   # přihlášení přežijí restart serveru

ROLE = ("admin", "obsluha")
SESSION_TTL = 12 * 3600          # neaktivita, po které se odhlásí
COOKIE = "rxsess"
_PBKDF2_ITER = 240_000

_lock = threading.RLock()
_sessions = None                  # token -> {"login":..., "exp":...}, načte se ze SESSIONS_FILE
_fails = {}                       # klíč (ip|login) -> [časy neúspěšných pokusů]


# ---------- hesla ----------
def _hash(heslo, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", heslo.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITER).hex()
    return f"pbkdf2_sha256${_PBKDF2_ITER}${salt}${h}"


def _over(heslo, ulozeny):
    try:
        _, it, salt, h = ulozeny.split("$")
        h2 = hashlib.pbkdf2_hmac("sha256", heslo.encode("utf-8"), bytes.fromhex(salt), int(it)).hex()
        return secrets.compare_digest(h, h2)
    except Exception:
        return False


# ---------- uživatelé ----------
def _nacti():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _uloz(users):
    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_FILE)
    try:
        os.chmod(USERS_FILE, 0o600)
    except Exception:
        pass


def ma_uzivatele():
    return bool(_nacti())


def _verejny(login, u):
    return {"login": login, "jmeno": u.get("jmeno") or login, "role": u.get("role", "obsluha"),
            "aktivni": u.get("aktivni", True), "vytvoreno": u.get("vytvoreno"),
            "posledni_prihlaseni": u.get("posledni_prihlaseni")}


def seznam_uzivatelu():
    return [_verejny(l, u) for l, u in sorted(_nacti().items())]


def uzivatel(login):
    u = _nacti().get(login)
    return _verejny(login, u) if u else None


def _kontrola_hesla(heslo):
    if not heslo or len(heslo) < 8:
        raise ValueError("Heslo musí mít aspoň 8 znaků.")


def uloz_uzivatele(login, jmeno=None, role=None, heslo=None, aktivni=None, novy=False):
    """Založí nebo upraví uživatele. Vrací veřejný záznam."""
    login = (login or "").strip().lower()
    if not login or not all(c.isalnum() or c in "._-" for c in login):
        raise ValueError("Login smí obsahovat jen písmena, číslice a . _ -")
    with _lock:
        users = _nacti()
        if novy and login in users:
            raise ValueError("Uživatel s tímto loginem už existuje.")
        if not novy and login not in users:
            raise ValueError("Uživatel neexistuje.")
        u = users.get(login, {"vytvoreno": datetime.now().strftime("%d.%m.%Y %H:%M"), "aktivni": True})
        if jmeno is not None:
            u["jmeno"] = jmeno.strip() or login
        if role is not None:
            if role not in ROLE:
                raise ValueError("Neplatná role.")
            u["role"] = role
        u.setdefault("role", "obsluha")
        if heslo:
            _kontrola_hesla(heslo)
            u["heslo"] = _hash(heslo)
        elif novy:
            raise ValueError("Zadej heslo.")
        if aktivni is not None:
            u["aktivni"] = bool(aktivni)
        # vždy musí zůstat aspoň jeden aktivní admin
        users[login] = u
        if not any(x.get("role") == "admin" and x.get("aktivni", True) for x in users.values()):
            raise ValueError("Musí zůstat aspoň jeden aktivní administrátor.")
        _uloz(users)
        if u.get("aktivni") is False:
            odhlas_uzivatele(login)
        return _verejny(login, u)


# ---------- přihlášení / session ----------
def _sess():
    global _sessions
    if _sessions is None:
        _sessions = {}
        try:
            with open(SESSIONS_FILE, encoding="utf-8") as f:
                _sessions = {t: s for t, s in json.load(f).items() if s.get("exp", 0) > time.time()}
        except Exception:
            pass
    return _sessions


def _uloz_sessions():
    try:
        tmp = SESSIONS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_sess(), f)
        os.replace(tmp, SESSIONS_FILE)
        os.chmod(SESSIONS_FILE, 0o600)
    except Exception:
        pass


def _omezeni(klic):
    now = time.time()
    pokusy = [t for t in _fails.get(klic, []) if now - t < 900]
    _fails[klic] = pokusy
    return len(pokusy) >= 8


def prihlas(login, heslo, ip=""):
    """Vrací (token, uzivatel) nebo vyhodí ValueError s hláškou."""
    login = (login or "").strip().lower()
    with _lock:
        klic = f"{ip}|{login}"
        if _omezeni(klic) or _omezeni(ip):
            raise ValueError("Příliš mnoho neúspěšných pokusů. Zkus to za 15 minut.")
        users = _nacti()
        u = users.get(login)
        if not u or not u.get("aktivni", True) or not _over(heslo or "", u.get("heslo", "")):
            _fails.setdefault(klic, []).append(time.time())
            _fails.setdefault(ip, []).append(time.time())
            raise ValueError("Nesprávný login nebo heslo.")
        _fails.pop(klic, None)
        u["posledni_prihlaseni"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        _uloz(users)
        token = secrets.token_urlsafe(32)
        _sess()[token] = {"login": login, "exp": time.time() + SESSION_TTL}
        _uloz_sessions()
        return token, _verejny(login, u)


def token_z_cookie(cookie_header):
    for cast in (cookie_header or "").split(";"):
        k, _, v = cast.strip().partition("=")
        if k == COOKIE:
            return v
    return None


def uzivatel_ze_session(token):
    if not token:
        return None
    with _lock:
        s = _sess().get(token)
        if not s or s["exp"] < time.time():
            _sess().pop(token, None)
            return None
        u = _nacti().get(s["login"])
        if not u or not u.get("aktivni", True):
            _sess().pop(token, None)
            _uloz_sessions()
            return None
        stary = s["exp"]
        s["exp"] = time.time() + SESSION_TTL
        if s["exp"] - stary > 600:        # na disk nejvýš jednou za 10 min
            _uloz_sessions()
        return _verejny(s["login"], u)


def odhlas(token):
    with _lock:
        _sess().pop(token, None)
        _uloz_sessions()


def odhlas_uzivatele(login):
    with _lock:
        for t in [t for t, s in _sess().items() if s["login"] == login]:
            _sess().pop(t, None)
        _uloz_sessions()


# ---------- audit ----------
def audit(uzivatel_zaznam, akce, **detail):
    zaznam = {"cas": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "login": (uzivatel_zaznam or {}).get("login", ""),
              "jmeno": (uzivatel_zaznam or {}).get("jmeno", ""),
              "akce": akce}
    zaznam.update({k: v for k, v in detail.items() if v not in (None, "")})
    with _lock:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(zaznam, ensure_ascii=False) + "\n")
    return zaznam


def nacti_audit(limit=500, login=None, hledat=None):
    if not os.path.exists(AUDIT_FILE):
        return []
    with _lock:
        with open(AUDIT_FILE, encoding="utf-8") as f:
            radky = f.readlines()
    out = []
    q = (hledat or "").lower()
    for r in reversed(radky):
        try:
            z = json.loads(r)
        except Exception:
            continue
        if login and z.get("login") != login:
            continue
        if q and q not in json.dumps(z, ensure_ascii=False).lower():
            continue
        out.append(z)
        if len(out) >= limit:
            break
    return out


# ---------- CLI ----------
if __name__ == "__main__":
    import sys, getpass
    a = sys.argv[1:]
    try:
        if a[:1] == ["pridat"] and len(a) >= 3:
            h = getpass.getpass("Heslo: ")
            if h != getpass.getpass("Heslo znovu: "):
                sys.exit("Hesla se neshodují.")
            role = a[3] if len(a) > 3 else ("admin" if not ma_uzivatele() else "obsluha")
            print("Založeno:", uloz_uzivatele(a[1], jmeno=a[2], role=role, heslo=h, novy=True))
        elif a[:1] == ["heslo"] and len(a) == 2:
            h = getpass.getpass("Nové heslo: ")
            if h != getpass.getpass("Nové heslo znovu: "):
                sys.exit("Hesla se neshodují.")
            uloz_uzivatele(a[1], heslo=h)
            odhlas_uzivatele(a[1])
            print("Heslo změněno.")
        elif a[:1] == ["seznam"]:
            for u in seznam_uzivatelu():
                print(f"{u['login']:15} {u['jmeno']:25} {u['role']:8} {'aktivní' if u['aktivni'] else 'zablokovaný'}")
        else:
            print(__doc__)
    except ValueError as e:
        sys.exit(f"Chyba: {e}")
