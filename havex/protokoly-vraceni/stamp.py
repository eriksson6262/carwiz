import sys, subprocess, re, pypdf
from pypdf import Transformation
stamp_pdf, src, dst = sys.argv[1:4]
# label position
bb = subprocess.run(['pdftotext','-bbox',src,'-'],capture_output=True,text=True).stdout
m = [w for w in re.finditer(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">předávajícího<', bb)]
x0,y0,x1,y1 = map(float, m[-1].groups())
r = pypdf.PdfReader(src); w = pypdf.PdfWriter(); w.append(r)
page = w.pages[-1]; H = float(page.mediabox.height)
sp = pypdf.PdfReader(stamp_pdf).pages[0]
sx0,sy0,sx1,sy1 = 220,611,345,651   # stamp bbox (pt)
s = 0.85
tw, th = (sx1-sx0)*s, (sy1-sy0)*s
cx = 458  # box centre
bottom = H - (y0 + 45)
tx = cx - tw/2 - sx0*s; ty = bottom - sy0*s
sp.mediabox = pypdf.generic.RectangleObject([sx0,sy0,sx1,sy1]); sp.cropbox = sp.mediabox
page.merge_transformed_page(sp, Transformation().scale(s,s).translate(tx,ty))
w.write(dst)
print(dst, 'label_y', y0)
