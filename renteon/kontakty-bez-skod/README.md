# Kontakty klientů bez účtované škody a pokuty (Renteon CZ + SK)

Postup (4.11.2026):
1. V obou Renteonech (vestavěný prohlížeč, přihlášený) spustit `collect_renteon.js` – CZ ~15 min, SK ~3 min.
2. Vyloučení: smlouva s vybranou službou typu 16 „Poškození“ / 5 „Zpracování poškození“ s částkou > 0, nebo `DamageAmount` > 0,
   nebo dopravní pokuta `IsCharged=true` (BookingId) – vyloučí se nájemce i všichni řidiči té smlouvy (podle ID v adresáři i e-mailu),
   plus řidiči přeúčtovaných pokut. Vyloučení platí napříč CZ i SK.
3. Kontakty = nájemce + řidiči uzavřených smluv (C, IsClosed), e-mail/telefon z adresáře, jinak z rezervace. Bez zaměstnanců, agentur, anonymizovaných a blacklistu.
4. Data stáhnout z prohlížeče jako TSV (`renteon_kontakty_{CZ|SK}_raw.tsv`, `renteon_vyloucene_{CZ|SK}.txt`) a spustit `build.py` → xlsx.
   Data i výstup jsou osobní údaje → NEcommitovat (ukládat do ~/Downloads/Claude pracovní/<případ>/).

Pozn.: škoda zapsaná v Poškození, ale nevyúčtovaná na smlouvě, klienta nevylučuje.
