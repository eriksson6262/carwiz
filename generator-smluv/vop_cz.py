# -*- coding: utf-8 -*-
"""Všeobecné obchodní podmínky (VOP) RX Auto — text pro 2. stranu nájemní smlouvy.

Text je záměrně v samostatném souboru: úpravy VOP (částky, pokuty, země…) se dělají
tady a nemusí se sahat do generátoru smlouvy. Odstavce mohou obsahovat jednoduché
značky <b>…</b>. Číslování odstavců je součástí textu.
"""

# Nonstop asistenční linka (čl. 7.1) — případnou změnu stačí přepsat tady.
ASISTENCE_TEL = "1224"

_TEL = f" Nonstop asistenční služba: tel. {ASISTENCE_TEL}." if ASISTENCE_TEL else ""

VOP_CLANKY = [
    ("1. Předmět a doba nájmu", [
        "<b>1.1</b> Pronajímatel přenechává nájemci vozidlo uvedené v nájemní smlouvě k dočasnému "
        "užívání a nájemce se zavazuje platit nájemné a další sjednané platby. Tyto všeobecné obchodní "
        "podmínky (dále jen „VOP“) jsou nedílnou součástí nájemní smlouvy.",
        "<b>1.2</b> Smlouva se uzavírá na dobu určitou; je-li sjednána varianta Flexi, na dobu neurčitou. "
        "Nájem začíná dnem a hodinou uvedenými ve smlouvě a končí uplynutím sjednané doby, u varianty "
        "Flexi vrácením vozidla. Nájemné se platí až do skutečného vrácení vozidla.",
        "<b>1.3</b> Dobu nájmu lze prodloužit, požádá-li nájemce o prodloužení nejpozději 48 hodin před "
        "jejím uplynutím a pronajímatel prodloužení potvrdí (postačí e-mail). Ostatní sjednané podmínky "
        "zůstávají zachovány.",
        "<b>1.4</b> Nevrátí-li nájemce vozidlo ve sjednané době a nebyl-li nájem prodloužen, jde o "
        "podstatné porušení smlouvy. Nájemce je povinen zaplatit smluvní pokutu 60 000 Kč a nájemné "
        "i všechny poplatky až do skutečného vrácení vozidla. Pronajímatel může domáhat se vydání vozidla "
        "soudně a oznámit jeho neoprávněné užívání Policii ČR; následky nese nájemce. Ode dne, kdy měl "
        "vozidlo vrátit, ztrácí nárok na omezení odpovědnosti podle čl. 6.",
        "<b>1.5</b> Při krádeži nebo havárii vozidla platí nájemce nájemné a poplatky až do opravy "
        "vozidla v servisu, resp. do ukončení šetření krádeže příslušnými orgány.",
        "<b>1.6</b> Vozidlo může být ve vlastnictví třetí osoby (financující společnosti). Nájemce je "
        "nesmí zcizit, zastavit ani jinak zatížit právy třetích osob.",
    ]),
    ("2. Předání a vrácení vozidla", [
        "<b>2.1</b> Pronajímatel předá vozidlo v dobrém technickém stavu, v čase a na místě uvedeném "
        "ve smlouvě. Stav vozidla, kilometry a palivo se zapíší do předávacího protokolu. Zjevné vady "
        "a připomínky musí nájemce uplatnit nejpozději při převzetí a nechat je do protokolu zapsat.",
        "<b>2.2</b> Nájemce vrátí vozidlo včetně klíčů, dokladů a příslušenství v čase a na místě "
        "uvedeném ve smlouvě, ve stavu, v jakém je převzal (s přihlédnutím k obvyklému opotřebení), "
        "a s palivem alespoň ve stavu zapsaném v protokolu. Chybějící palivo hradí nájemce spolu "
        "s poplatkem za dotankování (čl. 6.4).",
        "<b>2.3</b> Vozidlo, doklady a klíče převezme pověřený zaměstnanec pronajímatele; do té doby "
        "odpovídá nájemce za vozidlo i za veškeré škody na něm. Vrátí-li nájemce vozidlo na jiném místě "
        "než sjednaném, hradí náklady na jeho dopravu.",
        "<b>2.4</b> Při vrácení vozidla před uplynutím sjednané doby bez předchozí dohody nemá nájemce "
        "nárok na vrácení nájemného za nevyčerpanou dobu, nedohodnou-li se strany písemně jinak.",
    ]),
    ("3. Užívání vozidla", [
        "<b>3.1</b> Nájemce je povinen užívat vozidlo řádně a jen k obvyklým účelům (osobní potřeba, "
        "u firmy běžná provozní potřeba), dodržovat dopravní i jiné právní předpisy, pečovat o vozidlo "
        "tak, aby na něm nevznikla škoda, a řídit se pokyny pronajímatele.",
        "<b>3.2</b> Nájemce je povinen vozidlo zabezpečit proti odcizení, zneužití a poškození: po "
        "zaparkování vozidlo uzamknout a nenechávat v něm klíče ani doklady k vozidlu.",
        "<b>3.3</b> Nájemce nesmí: a) přenechat vozidlo jiné osobě, než která je uvedena ve smlouvě; "
        "b) účastnit se s vozidlem závodů, soutěží a podobných akcí; c) používat vozidlo k úplatné "
        "přepravě osob či věcí; d) vozidlem tlačit nebo vléci jiná vozidla, přívěsy či předměty; "
        "e) provádět na vozidle změny a úpravy; f) řídit vozidlo, ani je přenechat k řízení, po požití "
        "alkoholu, omamných látek, léků či jiných látek ovlivňujících vnímání a reakce; g) kouřit ve "
        "vozidle (včetně elektronických cigaret).",
        "<b>3.4</b> Porušení čl. 3.2 a 3.3 je podstatným porušením smlouvy. Při porušení čl. 3.3 f) "
        "hradí nájemce všechny vzniklé škody v plné výši. Za kouření ve vozidle zaplatí smluvní pokutu "
        "5 000 Kč a náklady na vyčištění; při vrácení nadměrně znečištěného vozidla hradí čištění, "
        "nejméně 1 500 Kč.",
        "<b>3.5</b> Pronajímatel je oprávněn požadovat přístup k vozidlu za účelem kontroly jeho řádného "
        "užívání; nájemce je povinen kontrolu neprodleně umožnit.",
        "<b>3.6</b> Do zahraničí lze vozidlo vyvézt pouze s předchozím souhlasem pronajímatele, a to "
        "výhradně na území členských států EU s výjimkou Rumunska, Bulharska, Estonska, Litvy a Lotyšska. "
        "Vjezd do ostatních zemí, zejména do Severní Makedonie, Černé Hory, Srbska, Albánie, Bosny "
        "a Hercegoviny a Kosova, je zakázán. Při porušení zákazu bude vozidlo oznámeno jako "
        "neoprávněně užívané a hrozí jeho zadržení. Nájemce odpovídá za veškerou škodu z porušení této "
        "povinnosti; bude-li vozidlo v zahraničí zadrženo či zabaveno, učiní vše potřebné k jeho uvolnění, "
        "platí nájemné až do vrácení vozidla pronajímateli a uhradí náklady dopravy na místo vrácení.",
    ]),
    ("4. Nájemné, jistina a platby", [
        "<b>4.1</b> Nájemce je povinen platit nájemné a další poplatky sjednané ve smlouvě řádně a včas. "
        "Není-li uvedeno jinak, jsou ceny a poplatky uvedeny bez DPH, které se připočítá v zákonné výši "
        "(21 %).",
        "<b>4.2</b> U nájmu delšího než jeden měsíc se nájemné fakturuje průběžně. Měsíční nájemné je "
        "splatné předem, vždy na následující měsíc (nebo jeho poměrnou část).",
        "<b>4.3</b> Při prodlení s jakoukoli platbou zaplatí nájemce úrok z prodlení 0,05 % z dlužné "
        "částky za každý započatý den prodlení.",
        "<b>4.4</b> Při podpisu smlouvy nájemce složí jistinu (zálohu) ve výši uvedené ve smlouvě, "
        "předautorizací na platební kartě nebo převodem na účet pronajímatele. Pronajímatel z ní po "
        "skončení nájmu uhradí nájemné, škody, pokuty a poplatky z nájmu a zbytek vrátí bez zbytečného "
        "odkladu po vyúčtování. Jistina může být v průběhu nájmu navýšena podle skutečných nákladů. "
        "Nezbavuje nájemce povinnosti platit nájemné.",
        "<b>4.5</b> Ukončí-li nájemce nájem předčasně, použije pronajímatel jistinu na úhradu škody "
        "z ušlého zisku.",
        "<b>4.6</b> Kilometry nad sjednaný rámec se doplácejí podle ceny uvedené ve smlouvě.",
    ]),
    ("5. Servis a údržba", [
        "<b>5.1</b> Běžné opravy, údržbu a pravidelné servisní prohlídky zajišťuje na své náklady "
        "pronajímatel. To neplatí, vznikla-li potřeba opravy nesprávným používáním vozidla, používáním "
        "v rozporu s obvyklým způsobem nebo porušením smlouvy; v takovém případě hradí opravu i související "
        "škodu v plném rozsahu nájemce.",
        "<b>5.2</b> Nájemce umožní opravy, údržbu a servisní prohlídky a strpí s nimi související omezení užívání.",
        "<b>5.3</b> Nepřistaví-li nájemce vozidlo k pravidelné servisní prohlídce (upozornění se zobrazí "
        "na displeji vozidla) nebo ji zmešká o více než 500 km, zaplatí smluvní pokutu 10 % pořizovací "
        "ceny vozidla a všechny náklady spojené s prohlídkou.",
        "<b>5.4</b> Nájemce tankuje výhradně palivo předepsané pro vozidlo (uvedeno ve smlouvě a v "
        "dokladech). Natankování nesprávného paliva je podstatné porušení smlouvy; nájemce hradí v plné "
        "výši vyčištění palivové soustavy, opravu, odtah i další vzniklé škody.",
    ]),
    ("6. Pojištění a odpovědnost za škodu", [
        "<b>6.1</b> Pronajímatel zajišťuje osobám oprávněným vozidlo řídit zákonné pojištění odpovědnosti "
        "za škodu způsobenou provozem vozidla a další pojištění v rozsahu uvedeném ve smlouvě.",
        "<b>6.2</b> Není-li dohodnuto jinak, hradí nájemce při každé pojistné události spoluúčast 10 % "
        "z celkové škody, nejméně 10 000 Kč (u čelního skla 1 000 Kč). Spoluúčast hradí vždy, když škodu "
        "způsobí on nebo když viník není znám, spolu s náklady na dopravu vozidla zpět k pronajímateli. "
        "Škodu na příslušenství hradí v plné výši.",
        "<b>6.3</b> K tíži nájemce jdou vždy pokuty za dopravní přestupky, škody vzniklé ztrátou dokladů, "
        "klíčů či příslušenství a náklady a poplatky vynaložené na nápravu takových škod. Nájemce bere na "
        "vědomí, že pronajímatel je povinen sdělit jeho údaje orgánům řešícím dopravní přestupky.",
        "<b>6.4</b> Administrativní poplatky (bez DPH): vyřízení dopravního přestupku 400 Kč, vyřízení "
        "pojistné události 1 000 Kč, dotankování vozidla 300 Kč.",
    ]),
    ("7. Nehoda, poškození a odcizení", [
        "<b>7.1</b> Při dopravní nehodě, poškození nebo odcizení vozidla či jeho části a při zranění nebo "
        "usmrcení osob (bez ohledu na zavinění) je nájemce povinen to neprodleně oznámit pronajímateli "
        "i Policii ČR, vyžádat si potvrzení o šetření a to neprodleně předat pronajímateli." + _TEL,
        "<b>7.2</b> Při každé škodní události nájemce vyplní všechny údaje ve formuláři „Oznámení "
        "o dopravní nehodě“ (záznam o nehodě lze vyplnit i online na www.bouracky.cz). Nepojízdné vozidlo zabezpečí před dalším poškozením nebo odcizením.",
        "<b>7.3</b> Nájemce poskytne Policii, pronajímateli a pojišťovně veškerou součinnost potřebnou k prošetření "
        "a likvidaci škodní události, včetně případného soudního řízení.",
    ]),
    ("8. Osobní údaje", [
        "<b>8.1</b> Správcem osobních údajů je RX Auto, s.r.o., IČO 06044310, Aviatická 1092/8, 161 00 "
        "Praha 6, info@rxauto.cz. Údaje nájemce (identifikační, kontaktní, údaje z dokladů a o průběhu "
        "nájmu) zpracovává podle nařízení (EU) 2016/679 (GDPR) a zákona č. 110/2019 Sb. za účelem plnění "
        "smlouvy, ověření spolehlivosti nájemce (i nahlédnutím do veřejných evidencí, např. exekucí), "
        "ochrany a vymáhání nároků, vyřízení přestupků a pojistných událostí a plnění zákonných povinností.",
        "<b>8.2</b> Údaje se uchovávají po dobu trvání smlouvy a poté po dobu, kterou vyžadují právní "
        "předpisy a promlčecí lhůty. Nájemce má práva podle GDPR, zejména na přístup, opravu, výmaz, "
        "omezení zpracování a vznesení námitky, a může podat stížnost u Úřadu pro ochranu osobních údajů.",
    ]),
    ("9. Ukončení smlouvy", [
        "<b>9.1</b> Užívá-li nájemce vozidlo v rozporu se sjednanými podmínkami nebo způsobem, který "
        "pronajímateli působí škodu či ji hrozí, nebo neplatí-li nájemné ve sjednaných částkách a "
        "termínech, může pronajímatel smlouvu vypovědět s okamžitou účinností. Nájemce je pak povinen "
        "vozidlo neprodleně vrátit.",
    ]),
    ("10. Závěrečná ustanovení", [
        "<b>10.1</b> Vztahy, které smlouva a VOP výslovně neupravují, se řídí právním řádem České "
        "republiky, zejména zákonem č. 89/2012 Sb., občanský zákoník.",
        "<b>10.2</b> Smlouvu lze měnit pouze písemně (dodatkem nebo potvrzením pronajímatele e-mailem). "
        "Smlouvu lze uzavřít a podepsat i elektronicky; strany sjednávají, že elektronický podpis je "
        "pro účely smlouvy dostačující. Oznámení se doručují na adresy a e-maily uvedené ve smlouvě.",
        "<b>10.3</b> Je-li nájemce spotřebitelem, je k mimosoudnímu řešení spotřebitelských sporů "
        "příslušná Česká obchodní inspekce, Štěpánská 567/15, 120 00 Praha 2, www.coi.cz (adr.coi.cz).",
        "<b>10.4</b> Nájemce svým podpisem potvrzuje, že se s VOP seznámil, porozuměl jim a souhlasí s nimi.",
    ]),
]
