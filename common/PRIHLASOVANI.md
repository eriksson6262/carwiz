# Přihlašovací údaje – Renteon a Vyfakturuj bez zadávání hesel

Skripty berou údaje z `common/rxauto_config.py`: proměnná prostředí → macOS Keychain → `~/.rxauto.env`.
V repu nikdy nic tajného není.

## Jednorázové nastavení (na Macu)

1. **Vyfakturuj API klíč** – vyfakturuj.cz → Nastavení → API → vygenerovat klíč.
2. **Renteon API uživatel** – pro produkci (rxauto.s3) ideálně samostatný API uživatel jen pro skripty
   (jako `AI.ExAPI` na demu), ne tvůj osobní účet.
3. Ulož údaje (ptá se skrytě, ukládá do Keychainu):

   ```bash
   cd ~/carwiz   # nebo kde máš repo
   python3 common/rxauto_config.py set VYFAKTURUJ_EMAIL
   python3 common/rxauto_config.py set VYFAKTURUJ_API_KEY
   python3 common/rxauto_config.py set RENTEON_PROD_USER
   python3 common/rxauto_config.py set RENTEON_PROD_PASSWORD
   python3 common/rxauto_config.py set RENTEON_DEMO_USER
   python3 common/rxauto_config.py set RENTEON_DEMO_PASSWORD
   python3 common/rxauto_config.py check
   ```

   Při prvním čtení z Keychainu se macOS zeptá – dej **Vždy povolit**.

## Ve skriptech

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "common"))
import rxauto_config as cfg

# Vyfakturuj – HTTP Basic auth
import requests
email, key = cfg.vyfakturuj_auth()
r = requests.get(f"{cfg.VYFAKTURUJ_API_URL}/invoice/", auth=(email, key))

# Renteon
rt = cfg.renteon("prod")      # nebo "demo"
# rt["url"], rt["user"], rt["password"]
```

## Prohlížeč (co API neumí)

- V built-in prohlížeči Claude desktop appky se přihlas sám a zaškrtni „zapamatovat“ – přihlášení drží mezi konverzacemi.
  Claude hesla do formulářů nezadává, ale přihlášenou session použít může.
- Když tě to i tak odhlašuje: zkontroluj, jestli prohlížeč nemaže cookies při zavření, případně dobu platnosti session v Renteonu.

## Cloud / jiný počítač

Bez Keychainu se údaje ukládají do `~/.rxauto.env` (práva 600). Šablona: `common/.env.example`.
