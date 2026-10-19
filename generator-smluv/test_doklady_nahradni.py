"""Test: vydání/platnost dokladů, náhradní vozidlo (firma) a protokol (km + nádrž) v PDF smlouvy."""
import os, subprocess, tempfile, unittest
from smlouva_v2 import generate_smlouva_v2

OS = {"jmeno": "Jiří", "prijmeni": "Štědroň", "datum_narozeni": "01.01.1980", "cislo_op": "218656575",
      "datum_vydani_op": "01.02.2020", "platnost_op": "01.02.2030", "cislo_rp": "EN 394272",
      "datum_vydani_rp": "03.04.2019", "platnost_rp": "03.04.2034", "adresa": "Praha"}
SM = {"vozidlo": "BMW 2 1ALB766", "datum_zacatku": "07.10.2026", "datum_konce": "12.11.2026", "cena": "1500",
      "interval_ceny": "denně", "pocet_intervalu": "36", "sjednany_najezd": "neomezený", "jistina": "",
      "email": "a@b.cz", "telefon": "+420777123456", "misto_predani": "Praha",
      "stav_tachometru_predani": "45120", "stav_nadrze": "3/4", "nahradni_vozidlo": True}
FIRMA = {"ico": "12345678", "nazev": "Firma s.r.o.", "sidlo": "Praha", "zastupce": "Jan Novák",
         "ridic_je_zastupce": True, "zmocneni": ""}

def txt(os_, sm, fi):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.pdf")
        generate_smlouva_v2(os_, sm, fi, p, "2026/1")
        return subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True).stdout

class T(unittest.TestCase):
    def test_doklady_a_protokol(self):
        t = txt(OS, SM, FIRMA)
        self.assertIn("01.02.2020 / 01.02.2030", t)
        self.assertIn("03.04.2019 / 03.04.2034", t)
        self.assertIn("45120 km", t)
        self.assertIn("3/4", t)
        self.assertIn("podepisuje pouze řidič", t)
        self.assertIn("Nájemce — řidič: Jiří Štědroň", t)
        self.assertIn("Za nájemce", t)
        self.assertIn("Za pronajímatele", t)
        self.assertNotIn("Předal", t)
        self.assertNotIn("Převzal", t)

    def test_none_se_netiskne(self):
        o = dict(OS, datum_vydani_op=None, platnost_op=None, datum_vydani_rp="03.04.2019", platnost_rp=None)
        t = txt(o, dict(SM, nahradni_vozidlo=False), None)
        self.assertNotIn("None", t)
        self.assertIn("03.04.2019 / —", t)
        self.assertNotIn("podepisuje pouze řidič", t)

if __name__ == "__main__":
    unittest.main()
