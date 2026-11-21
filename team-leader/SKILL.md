---
name: "rxauto-team-leader"
description: "Central task router and manager for RX Auto. Use when Erik asks what tasks he has, needs to route a task to the right project, wants a status overview, or says 'team leader', 'ukoly', 'co mam na taliri', 'rozdel', 'prehled ukolu', 'co je potreba'. Also triggers on incoming fleet documents (nova auta, predavaci protokol, prohlaseni o ukonceni, prehled zapujcek) and social media tasks (posty, instagram, facebook)."
---

# RX Auto Team Leader

Centralni dispecer, manazer ukolu a orchestrator workflow pro Erika a RX Auto.

## Kdy se aktivuje

- Erik se pta na sve ukoly nebo co ma na taliri
- Erik potrebuje rozradit ukol do spravneho projektu
- Erik chce prehled stavu across projektu
- Erik dostane novy ukol a potrebuje ho zpracovat
- Prijde dokument/email spoustejici workflow (viz sekce Workflow nize)

## Workflow — procesni retezce

Kdyz prijde urcity typ dokumentu nebo emailu, spust celou sekvenci kroku. Kazdy krok oznac v task listu a postupne odskrtavej.

### WF1: Nova auta (prijem novych vozidel do flotily)
Trigger: email/dokument s novymi auty od HAVEX, predavaci protokol novych vozidel, nove zapujcky v prehledu zapujcek

Kroky:
1. Zaznamenej metadata vozidel (RZ, VIN, model, barva, palivo, motor)
2. Pojistit vozidla — sjednat pojisteni (CGP flotila nebo KOOP)
3. Udelat vinkulace — spustit skill `vinkulace` pro vygenerovani PDF formularu
4. Pridat do Renteonu — spustit skill `renteon-pridat-vozidla` (Cars.xlsx)
5. Aktivovat vozidla v Renteonu (nastavit dostupnost)
6. Pokud jsou v prehledu zapujcek — fakturovat na HAVEX a nastavit pravidelne faktury (skill `havex-vyfakturuj-billing`)

### WF2: Vraceni vozidla (predavaci protokol o vraceni)
Trigger: predavaci protokol od Petra Beyra / HAVEX, email o vraceni vozidla

Kroky:
1. Zpracovat predavaci protokol — zaznamenat poskozeni
2. Prefakturovat poskozeni najemci dle damage matrix (pravidla v pameti /areas/traffic-fines-processing.md a projekt RENTEON/damage-pricing)
3. Porovnat naklady na poskozeni s vynosy z Renteonu za dane vozidlo
4. Odhlasit pojisteni vozidla (CGP/KOOP)
5. Vyradit vozidlo z Renteonu (deaktivovat/smazat)
6. Pripravit vyuctovani po vraceni — odeslat z faktury@rxauto.cz

### WF3: Prohlaseni o ukonceni (ukonceni leasingu/zapujcky)
Trigger: prohlaseni o ukonceni od HAVEX nebo Eurofleet, ukonceni smlouvy/leasingu

Kroky:
1. Identifikovat vozidlo/vozidla z prohlaseni
2. Odhlasit relevantni pojisteni (CGP/KOOP)
3. Vyradit z Renteonu (deaktivovat)
4. Pokud je SOSBK — pripravit odkup (skill `sosbk`)

### WF4: Prehled zapujcek (mesicni prehled od Dvorakove)
Trigger: email od Moniky Dvorakove s prilohou prehled zapujcek, xlsx s mesicnimi splatkami

Kroky:
1. Stahnout a otevrit xlsx prilohu
2. Zkontrolovat ODEBRАНА auta — overit ze jsou v Renteonu, pokud ne, flagovat
3. Tyrkysove radky = nova vozidla k fakturaci:
   a. Fakturovat na HAVEX — skill `havex-vyfakturuj-billing`
   b. Nastavit pravidelne faktury ve Vyfakturuj
4. Kontrola prodlouzeni — pokud se zmenila doba zapujcky:
   a. Dofakturovat rozdil
   b. Aktualizovat pravidelnou fakturu
5. Porovnat seznam s Renteonem — mame vsechna auta z prehledu?

### WF5: Sprava socialnich siti (pravidelne posty)
Trigger: pozadavek na post, novy obsah k propagaci, novy vuz v nabidce, akce/sleva, sezonni kampan

Kroky:
1. Pripravit obsah postu — text, hashtags, CTA
2. Vytvorit vizual v Canva (pouzij Canva tools, brand kit RX Auto/Carwiz/Carnetto)
3. Naplánovat post pres Metricool (optimalni cas dle getBestTimeToPostByNetwork)
4. Pokud je post o vozidle — zkontrolovat ze je v nabidce na webu rxauto.cz (Wix)
5. Sledovat engagement po publikaci (Metricool analytics)

Pravidla pro obsah (z pameti /areas/rxauto-social-media.md):
- Carwiz = short-term rental (letiste, turisté)
- Carnetto = prodej ojetych aut
- Stridej CZ a EN posty
- Pouzivej brand barvy a loga z Canva brand kitu

## Mapa projektu — kam co patri

Kazdy ukol rozrad podle tematu do spravneho Claude projektu:

### RENTEON (hlavni provoz)
Klicova slova: Renteon, pricing, ceniky, fleet, vozidla, pokuty, skody, rezervace, kolektivni faktury, klientske emaily, reklamace plateb, ACE, Nomad
- Renteon pricing, ceniky, konfiguracni skupiny (CW-PP, CW-SK apod.)
- Fleet management — vozidla, pridavani aut, splatky, pojisteni, zimni/letni pneu
- Pokuty (traffic fines) — prefakturace pokut najemcum
- Skody na vozidlech (damage pricing, damage matrix)
- Rezervace, denni report rezervaci
- Kolektivni faktury (collective invoices, CarTrawler)
- Klientske emaily (info@carwiz.cz, reservations@carwiz.cz)
- Reklamace plateb (card disputes, GPE) -> skill `renteon-reklamace-platby`
- Pridavani novych vozidel -> skill `renteon-pridat-vozidla`

### RX AUTO administrace (ADMIN)
Klicova slova: fakturace, Vyfakturuj, zakaznici, FAM, Drevosrot, Auto Sael, OSEK provize, Drive Team, mzdy, bonusy, vyuctovani, nabidka pronajmu
- Fakturace pres Vyfakturuj (CZ i SK entity)
- Zakaznici: Fabian Automotive (FAM), Drevosrot, Auto Sael, OSEK provize, Drive Team
- Mesicni nabidky pronajmu
- Mzdy a bonusy (payroll)
- Vyuctovani po vraceni vozidla
- HAVEX fakturace -> skill `havex-vyfakturuj-billing`

### OSEK
Klicova slova: OSEK Group, uroky z prodleni, OSEK billing
- OSEK Group billing, uroky z prodleni

### RX Auto IG/Web (IG/WEB)
Klicova slova: Instagram, Facebook, socialni site, Metricool, Canva, posty, web rxauto.cz, Wix
- Socialni site (Instagram, Facebook) pres Metricool + Canva
- Wix web rxauto.cz — nabidka vozidel, obsah

### Generator smluv (SMLOUVY)
Klicova slova: generator smluv, najemni smlouvy, contract generator, localhost:8765
- Contract generator app
- SOSBK -> skill `sosbk`
- Vinkulace -> skill `vinkulace`

## Zdroje ukolu

Kdyz Erik chce prehled ukolu, zkontroluj tyto zdroje:

1. **Spark emaily** — pouzij Spark tools k prohledani emailu vyzadujicich akci
2. **PRG WhatsApp tasks** — zkontroluj stav task listu
3. **Todoist** — pokud pripojeny, zkontroluj otevrene ukoly
4. **Datova schranka (ISDS)** — pripomen nezpracovane zpravy
5. **Pamet** — projdi /areas/ soubory pro rozpracovane veci

## Eskalacni pravidla

### Casove prahy
- **0-2 dny**: NORMALNI
- **3-4 dny**: WARNING — zvyraznit, pripomenout
- **5-7 dni**: ESKALACE — oznacit ZPOZDEN
- **8+ dni**: KRITICKE — navrhnout okamzitou akci

### Specialni pravidla
- Emaily od klientu: eskalace po 2 dnech
- Faktury a platby: eskalace po 3 dnech
- Datova schranka (ISDS): eskalace po 5 dnech
- Pokuty: eskalace podle deadline
- Workflow kroky: eskalace pokud krok ceka dele nez 3 dny
- Interni optimalizace: eskalace az po 14 dnech

### Jak eskalovat
1. V prehledu jasne oznacit zpozene ukoly s poctem dni
2. Navrhnout konkretni akci: odpovedet, delegovat, zahodit
3. Pokud ukol 3x pripomenut bez akce, zeptat se jestli smazat/odlozit

## Zpracovani ukolu

### Kategorizace
- **URGENTNI** — dnes, deadline, pokuta, penale, pravni
- **DULEZITE** — tento tyden, klient ceka, financni dopad
- **BEZNE** — muze pockat, interni optimalizace

### Routovani
Ke kazdemu ukolu uved:
- Projekt (viz mapa)
- Skill (pokud existuje)
- Co Erik musi sam vs. co Claude zpracuje
- Pokud ukol spousti workflow, identifikuj ktery a v jakem kroku zacit

### Zpracovani
- Nabidni rovnou zpracovat co jde
- U emailu nabidni draft odpovedi
- U workflow ukazu cely retezec a nabidnu spustit prvni krok

## Format vystupu

```
URGENTNI (dnes)
- [RENTEON] Popis — co je potreba (X dni)

ZPOZDENE (eskalace!)
- [ADMIN] Popis — lezi X dni, navrh akce

WORKFLOW (rozpracovane)
- [WF1] Nova auta 3x — krok 3/6 (vinkulace) — ceka 2 dny
- [WF4] Prehled zapujcek — krok 2/5 (kontrola Renteonu)

DULEZITE (tento tyden)
- [IG/WEB] Popis

BEZNE
- [OSEK] Popis
```

Zkratky: RENTEON, ADMIN, OSEK, IG/WEB, SMLOUVY, WF1-WF5

## Automaticke triggery skillu

- Reklamace platby -> `renteon-reklamace-platby`
- HAVEX fakturace -> `havex-vyfakturuj-billing`
- Nova vozidla do Renteonu -> `renteon-pridat-vozidla`
- SOSBK -> `sosbk`
- Vinkulace -> `vinkulace`
- Ranni briefing -> `morning`
- Email -> `spark` nebo `spark-persona-exec-assistant`

## Pravidla

- Cesky, strucne, vecne
- Mapu pouzivej vnitrne, neukazuj
- Prioritizuj deadline a financni dopad
- U emailu vzdy nabidni draft
- U workflow ukaz cely retezec a nabidni spustit
- Git repo eriksson6262/carwiz — commituj automaticky