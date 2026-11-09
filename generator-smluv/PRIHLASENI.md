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
