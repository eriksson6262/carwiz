import sys
sys.path.insert(0, "/tmp/gensmluv")
from smlouva_v2 import generate_smlouva_v2

osobni_data = dict(
    jmeno="Jan", prijmeni="Novák",
    datum_narozeni="12.3.1985", misto_narozeni="Praha",
    adresa="Václavské náměstí 1, 110 00 Praha 1",
    cislo_op="123456789", datum_vydani_op="1.1.2020", platnost_op="1.1.2030",
    cislo_rp="987654321", datum_vydani_rp="1.1.2015", platnost_rp="1.1.2035",
)
smlouva_data = dict(
    email="jan.novak@example.cz", telefon="+420 777 123 456",
    vozidlo="Škoda Octavia, 8A2 1234", sjednany_najezd="1500", interval_najezdu="měsíc",
    datum_zacatku="22.9.2026", datum_konce="22.10.2026", pocet_intervalu="1",
    interval_ceny="měsíčně", cena="15000", mena="CZK", jistina="20000",
)

for typ in ("osobni", "dodavka", "prives", "motorka"):
    out = f"/tmp/gensmluv/diagrams/protokoly/test_smlouva_{typ}.pdf"
    generate_smlouva_v2(osobni_data, smlouva_data, {}, out, "2026-0042", typ_vozidla=typ, protokol=True)
    print("wrote", out)
