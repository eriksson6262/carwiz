# Přihlášení, uživatelé a audit

Generátor je od 11/2026 přístupný jen po přihlášení.

## První spuštění
1. Spusť generátor (`Spustit_generator.command`).
2. **Na tomto počítači** otevři http://localhost:8765/login – zobrazí se „První spuštění“, založ administrátora.
   (Z internetu / přes tunel první účet založit nejde.)
3. Vpravo nahoře **👥 Uživatelé** → založ ostatní (login, jméno, role, heslo).

Alternativa z Terminálu: `python3 auth.py pridat erik "Erik Rajohnson" admin`

## Role
- **admin** – vše + správa uživatelů, audit, mazání z historie, restart/vypnutí serveru
- **obsluha** – tvorba smluv, protokolů, podpisy, faktury

## Co se zaznamenává
- U každé smlouvy v historii: kdo ji vytvořil, kdo a kdy ji naposledy změnil, seznam změn
  (oprava, protokol o vrácení, podpis, DocuSeal, faktura).
- `👥 Uživatelé → Kdo co dělal`: kompletní auditní log (přihlášení, neúspěšná přihlášení,
  smlouvy, protokoly, stažení souborů, správa uživatelů, restarty) s IP adresou.

## Soubory (v gitu nejsou)
- `users.json` – uživatelé, hesla jen jako PBKDF2 hash
- `sessions.json` – aktivní přihlášení (přežijí restart, odhlášení po 12 h nečinnosti)
- `audit_log.jsonl` – auditní log

Zapomenuté heslo: admin nastaví nové v Uživatelích, nebo `python3 auth.py heslo <login>`.

## Přístup z internetu – Tailscale Funnel (Mac mini)
Generátor běží na Mac mini na `localhost:8765`, ven ho pouští Tailscale Funnel
(HTTPS adresa typu `https://<jmeno-pocitace>.<tailnet>.ts.net`, bez úprav DNS a routeru).

1. Nainstaluj Tailscale (tailscale.com/download/mac nebo App Store) a přihlas se.
2. Admin konzole Tailscale → DNS: zapnout **MagicDNS** a **HTTPS Certificates**.
3. Terminál na Mac mini:
   `/Applications/Tailscale.app/Contents/MacOS/Tailscale funnel --bg 8765`
   (při prvním spuštění vypíše odkaz na povolení Funnelu – otevřít a potvrdit).
4. Adresu zjistíš: `/Applications/Tailscale.app/Contents/MacOS/Tailscale funnel status`
5. Vypnutí: `/Applications/Tailscale.app/Contents/MacOS/Tailscale funnel --https=443 off`

Administrátora zakládej **před** zapnutím Funnelu, lokálně na http://localhost:8765/login.
