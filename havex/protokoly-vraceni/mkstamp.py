import pypdf, sys
from pypdf.generic import NameObject, DictionaryObject, StreamObject
r=pypdf.PdfReader(sys.argv[1]); im=r.pages[0]['/Resources']['/XObject']['/Im0']
w=pypdf.PdfWriter(); p=w.add_blank_page(595.28,841.89)
imref=w._add_object(im.get_object().clone(w)) if False else im.get_object().clone(w).indirect_reference
res=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im0'):imref})})
p[NameObject('/Resources')]=res
s=StreamObject(); s.set_data(b'q 125 0 0 39.82 218 611 cm /Im0 Do Q'); p[NameObject('/Contents')]=w._add_object(s)
w.write(sys.argv[2])
