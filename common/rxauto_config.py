#!/usr/bin/env python3
"""
Sdílené přihlašovací údaje pro skripty RX Auto (Renteon, Vyfakturuj, ...).

Hodnoty se hledají v tomto pořadí:
  1. proměnná prostředí (např. VYFAKTURUJ_API_KEY)
  2. macOS Keychain (služba "rxauto", účet = název klíče)
  3. soubor ~/.rxauto.env (KLIC=hodnota, práva 600)

Nic z toho není v repu. Hesla se nikdy nevypisují.

Použití z jiného skriptu:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "common"))
    import rxauto_config as cfg

    email, key = cfg.vyfakturuj_auth()
    r = cfg.renteon("prod")   # r["url"], r["user"], r["password"]

CLI:
    python3 common/rxauto_config.py set VYFAKTURUJ_API_KEY   # zeptá se skrytě, uloží
    python3 common/rxauto_config.py check                    # co je nastavené (bez hodnot)
    python3 common/rxauto_config.py delete RENTEON_PASSWORD
"""

from __future__ import annotations

import getpass
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SERVICE = "rxauto"
ENV_FILE = Path.home() / ".rxauto.env"

KNOWN_KEYS = {
    "VYFAKTURUJ_EMAIL": "Přihlašovací e-mail do Vyfakturuj",
    "VYFAKTURUJ_API_KEY": "API klíč z Vyfakturuj (Nastavení → API)",
    "RENTEON_PROD_USER": "Renteon API uživatel – produkce (rxauto.s3)",
    "RENTEON_PROD_PASSWORD": "Renteon API heslo – produkce",
    "RENTEON_DEMO_USER": "Renteon API uživatel – demo (demo.s2)",
    "RENTEON_DEMO_PASSWORD": "Renteon API heslo – demo",
}

RENTEON_URLS = {
    "prod": "https://rxauto.s3.renteon.com",
    "demo": "https://demo.s2.renteon.com",
}
VYFAKTURUJ_API_URL = "https://api.vyfakturuj.cz/2.0"


# ---------- úložiště ----------

def _has_keychain() -> bool:
    return platform.system() == "Darwin" and shutil.which("security") is not None


def _keychain_get(name: str) -> str | None:
    if not _has_keychain():
        return None
    res = subprocess.run(
        ["security", "find-generic-password", "-s", SERVICE, "-a", name, "-w"],
        capture_output=True, text=True,
    )
    return res.stdout.rstrip("\n") if res.returncode == 0 else None


def _keychain_set(name: str, value: str) -> None:
    # -U = přepsat existující položku
    subprocess.run(
        ["security", "add-generic-password", "-U", "-s", SERVICE, "-a", name, "-w", value],
        check=True, capture_output=True,
    )


def _keychain_delete(name: str) -> bool:
    if not _has_keychain():
        return False
    res = subprocess.run(
        ["security", "delete-generic-password", "-s", SERVICE, "-a", name],
        capture_output=True,
    )
    return res.returncode == 0


def _envfile_read() -> dict[str, str]:
    data: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def _envfile_write(data: dict[str, str]) -> None:
    ENV_FILE.write_text(
        "".join(f"{k}={v}\n" for k, v in sorted(data.items())), encoding="utf-8"
    )
    os.chmod(ENV_FILE, 0o600)


# ---------- veřejné API ----------

def get(name: str, required: bool = True) -> str | None:
    value = os.environ.get(name) or _keychain_get(name) or _envfile_read().get(name)
    if value:
        return value
    if required:
        hint = KNOWN_KEYS.get(name, "")
        sys.exit(
            f"Chybí údaj {name}{' (' + hint + ')' if hint else ''}.\n"
            f"Nastav ho:  python3 common/rxauto_config.py set {name}"
        )
    return None


def set_value(name: str, value: str) -> str:
    if _has_keychain():
        _keychain_set(name, value)
        return "macOS Keychain"
    data = _envfile_read()
    data[name] = value
    _envfile_write(data)
    return str(ENV_FILE)


def delete(name: str) -> None:
    removed = _keychain_delete(name)
    data = _envfile_read()
    if name in data:
        del data[name]
        _envfile_write(data)
        removed = True
    print(f"{name}: {'smazáno' if removed else 'nenalezeno'}")


def vyfakturuj_auth() -> tuple[str, str]:
    """(email, api_klic) pro HTTP Basic auth do Vyfakturuj API."""
    return get("VYFAKTURUJ_EMAIL"), get("VYFAKTURUJ_API_KEY")


def renteon(env: str = "prod") -> dict[str, str]:
    """Údaje pro Renteon API: {'url', 'user', 'password'}; env = 'prod' | 'demo'."""
    env = env.lower()
    if env not in RENTEON_URLS:
        raise ValueError("env musí být 'prod' nebo 'demo'")
    p = f"RENTEON_{env.upper()}_"
    return {
        "url": os.environ.get(p + "URL", RENTEON_URLS[env]),
        "user": get(p + "USER"),
        "password": get(p + "PASSWORD"),
    }


# ---------- CLI ----------

def _source(name: str) -> str | None:
    if os.environ.get(name):
        return "prostředí"
    if _keychain_get(name):
        return "Keychain"
    if name in _envfile_read():
        return str(ENV_FILE)
    return None


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] not in {"set", "check", "delete"}:
        print(__doc__)
        return
    cmd = argv[1]
    if cmd == "check":
        for k, desc in KNOWN_KEYS.items():
            src = _source(k)
            print(f"{'OK ' if src else '-- '} {k:<24} {src or 'nenastaveno'}   ({desc})")
        return
    if len(argv) < 3:
        sys.exit(f"Použití: rxauto_config.py {cmd} NAZEV_KLICE")
    name = argv[2]
    if cmd == "delete":
        delete(name)
        return
    prompt = f"{name}{' – ' + KNOWN_KEYS[name] if name in KNOWN_KEYS else ''}: "
    secret = "PASSWORD" in name or "KEY" in name or "TOKEN" in name
    value = getpass.getpass(prompt) if secret else input(prompt)
    if not value.strip():
        sys.exit("Prázdná hodnota, nic neuloženo.")
    where = set_value(name, value.strip())
    print(f"{name} uloženo → {where}")


if __name__ == "__main__":
    main(sys.argv)
