# -*- coding: utf-8 -*-
"""Vlastní čárové nákresy karoserií (hatchback, kombi, SUV) pro předávací protokol.
Stejné rozložení listu (2000x1414) a styl čar jako šablona osobního vozu:
bok pravý, čelo, bok levý, zadek, pohled shora. Výstup: diagrams/sablony/<klíč>.png (2800x1980)."""
import os, math, sys
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams", "sablony")
INK, GREY, SW = "#1a1a1a", "#c4c4c4", 4.2

# Typy: rozměry v px (bok 207 px/m). Souřadnice x od přídě (0) k zádi (L), výšky od země.
TYPES = {
 "hatchback": dict(L=860, wb=520, fo=165, r=58, sill=64, hf=150, hb=188, xc=280, x1=455, H=292, x2=715, x3=815, hr=214,
                   belt=205, rails=False, tailgate=True, quarter=False, W_top=282, L_top=640, front=dict(H=292,hf=180,wb=200,W=388)),
 "kombi":     dict(L=1010, wb=605, fo=180, r=60, sill=66, hf=152, hb=192, xc=310, x1=495, H=300, x2=880, x3=985, hr=232,
                   belt=208, rails=True, tailgate=True, quarter=True, W_top=292, L_top=765, front=dict(H=302,hf=185,wb=205,W=412)),
 "suv":       dict(L=985, wb=590, fo=175, r=74, sill=80, hf=200, hb=238, xc=315, x1=470, H=352, x2=880, x3=958, hr=268,
                   belt=255, rails=True, tailgate=True, quarter=True, W_top=305, L_top=740, front=dict(H=358,hf=225,wb=238,W=426)),

 "coupe":     dict(L=895, wb=545, fo=162, r=62, sill=62, hf=146, hb=182, xc=300, x1=480, H=268, x2=630, x3=745, hr=200,
                   belt=192, rails=False, tailgate=True, quarter=False, doors2=True, W_top=288, L_top=690, front=dict(H=268,hf=172,wb=190,W=410)),
 "kabriolet": dict(L=880, wb=530, fo=162, r=60, sill=62, hf=146, hb=182, xc=300, x1=440, H=252, x2=660, x3=745, hr=190,
                   belt=190, rails=False, tailgate=False, quarter=False, doors2=True, open=True, W_top=285, L_top=675, front=dict(H=252,hf=172,wb=188,W=406)),
}

def rpath(pts, r=18, closed=False):
    """Polyline se zaoblenými rohy (kvadratické křivky)."""
    n = len(pts); d = ""
    def lerp(a, b, t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
    def dist(a, b): return math.hypot(b[0]-a[0], b[1]-a[1])
    idx = range(n) if closed else range(1, n-1)
    segs = []
    for i in idx:
        p0, p1, p2 = pts[(i-1) % n], pts[i], pts[(i+1) % n]
        t1 = min(r/dist(p1, p0), .5); t2 = min(r/dist(p1, p2), .5)
        segs.append((lerp(p1, p0, t1), p1, lerp(p1, p2, t2)))
    if closed:
        d = f"M{segs[0][2][0]:.1f},{segs[0][2][1]:.1f} "
        for k in range(1, len(segs)):
            a, c, b = segs[k]; d += f"L{a[0]:.1f},{a[1]:.1f} Q{c[0]:.1f},{c[1]:.1f} {b[0]:.1f},{b[1]:.1f} "
        a, c, b = segs[0]; d += f"L{a[0]:.1f},{a[1]:.1f} Q{c[0]:.1f},{c[1]:.1f} {b[0]:.1f},{b[1]:.1f} Z"
    else:
        d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f} "
        for a, c, b in segs:
            d += f"L{a[0]:.1f},{a[1]:.1f} Q{c[0]:.1f},{c[1]:.1f} {b[0]:.1f},{b[1]:.1f} "
        d += f"L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"
    return d

def P(d, stroke=INK, sw=SW, fill="none"):
    return f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}" stroke-linecap="round" stroke-linejoin="round"/>'
def L(x1, y1, x2, y2, stroke=INK, sw=SW):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>'
def C(cx, cy, r, stroke=INK, sw=SW):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" stroke="{stroke}" stroke-width="{sw}" fill="none"/>'
def R(x, y, w, h, rx=8, stroke=INK, sw=SW):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" stroke="{stroke}" stroke-width="{sw}" fill="none"/>'

def wheel(cx, cy, r):
    s = C(cx, cy, r) + C(cx, cy, r*.42) + C(cx, cy, r*.08, sw=3)
    for k in range(5):
        a = math.radians(-90+72*k)
        s += L(cx+r*.42*math.cos(a), cy+r*.42*math.sin(a), cx+r*.8*math.cos(a), cy+r*.8*math.sin(a), GREY, 3)
    return s

def side(t, ox, gy, flip, ground_x=(174, 1194)):
    """Boční pohled. ox = x začátku přídě, gy = y země. flip=True zrcadlí (zadek vlevo)."""
    T = TYPES[t]; Lw = T["L"]; wb = T["wb"]; fo = T["fo"]; r = T["r"]; sill = T["sill"]
    # lokální souřadnice: X = x od přídě, Y = výška nad zemí; převod na plátno
    def tx(x): return (ox + (Lw - x if flip else x))
    def ty(y): return gy - y
    def pt(x, y): return (tx(x), ty(y))
    out = []
    wc1, wc2 = fo, fo + wb
    arch_r = r + 14
    # horní obrys: příď -> kapota -> A sloupek -> střecha -> zadní okno -> záď
    top = [pt(0, sill+10), pt(0, T["hf"]-30), pt(8, T["hf"]), pt(T["xc"], T["hb"]), pt(T["x1"], T["H"]-6),
           pt(T["x1"]+45, T["H"]), pt((T["x1"]+T["x2"])/2, T["H"]), pt(T["x2"], T["H"]-12),
           pt(T["x3"], T["hr"]+8), pt(Lw-4, T["hr"]-2), pt(Lw, T["hr"]-50), pt(Lw, sill+10)]
    if T.get("open"):
        top = [pt(0, sill+10), pt(0, T["hf"]-30), pt(8, T["hf"]), pt(T["xc"], T["hb"]), pt(T["x1"], T["H"]),
               pt(T["x1"]+14, T["H"]), pt(T["x1"]+40, T["belt"]+8), pt(T["x2"], T["belt"]+8),
               pt(Lw-30, T["hr"]+4), pt(Lw-4, T["hr"]-2), pt(Lw, T["hr"]-50), pt(Lw, sill+10)]
    d = rpath(top, r=22)
    # spodek s oblouky kol (od zádě k přídi)
    def arch(xc):
        return (pt(xc+arch_r, sill), pt(xc-arch_r, sill))
    a2s, a2e = arch(wc2); a1s, a1e = arch(wc1)
    cur = pt(Lw, sill+10)
    sweep = 0 if flip else 1  # směr oblouku nahoru
    # pozn.: jdeme zprava doleva v lokálních souřadnicích
    def seg_to(p): return f" L{p[0]:.1f},{p[1]:.1f}"
    def arc_to(p): return f" A{arch_r},{arch_r} 0 0 {1 if flip else 0} {p[0]:.1f},{p[1]:.1f}"
    # směr projití: lokálně zadní -> přední (x klesá)
    d += seg_to(pt(Lw-12, sill)) 
    d += seg_to(a2s) + arc_to(a2e) + seg_to(a1s) + arc_to(a1e) + seg_to(pt(12, sill)) + seg_to(pt(0, sill+10))
    out.append(P(d))
    # kola
    out.append(wheel(*pt(wc1, sill-6), r)); out.append(wheel(*pt(wc2, sill-6), r))
    # zeď oken (greenhouse)
    bw = T["belt"]
    gh = [pt(T["xc"]+22, bw), pt(T["x1"]-2, T["H"]-16), pt(T["x1"]+52, T["H"]-16), pt((T["x1"]+T["x2"])/2, T["H"]-16),
          pt(T["x2"]-8, T["H"]-26), pt(T["x3"]-16, T["hr"]+24), pt(T["x3"]-26, bw)]
    if T.get("open"):
        gh = [pt(T["xc"]+22, bw+4), pt(T["x1"]-4, T["H"]-12), pt(T["x1"]+8, T["H"]-12), pt(T["x1"]+30, bw+4)]
    out.append(P(rpath(gh, r=10 if T.get("open") else 14, closed=True), sw=3.4))
    if T.get("open"):
        # zadní opěrky hlavy / sedadla v otevřeném interiéru
        for hx0 in (T['x1'] + 120,):
            a = pt(hx0, bw+8)
            out.append(R(a[0] - (30 if flip else 0), a[1]-44, 30, 44, 12, sw=3.2))
            # sloupky / dveře
    xB = fo + wb*0.40
    def gtop(x):
        xa, ya, xb2, yb = T["xc"]+22, bw, T["x1"]-2, T["H"]-16
        if x >= xb2: return yb
        return ya + (yb-ya)*(x-xa)/(xb2-xa)
    if T.get("doors2"):
        xR = fo + wb - arch_r - 8
        if not T.get("open"):
            out.append(L(*pt(xR, bw), *pt(xR, gtop(xR)-4)))        # zadní hrana okna / sloupek
        out.append(L(*pt(T["xc"]+14, bw), *pt(T["xc"]+4, sill)))   # přední hrana dveří
        out.append(L(*pt(xR, bw), *pt(xR, sill)))                  # zadní hrana dveří
        out.append(L(*pt(T["xc"]+14, bw), *pt(xR, bw)))            # horní hrana dveří (beltline)
        hxs = [xR-120]
    else:
        out.append(L(*pt(xB, bw), *pt(xB, gtop(xB))))          # B sloupek
        out.append(L(*pt(xB, bw), *pt(xB, sill)))                      # dveře střed
        out.append(L(*pt(T["xc"]+14, bw), *pt(T["xc"]+4, sill)))       # přední hrana dveří
        xR = fo + wb - arch_r - 26
        if T["quarter"]:
            out.append(L(*pt(xR, bw), *pt(xR, gtop(xR))))             # C sloupek
        out.append(L(*pt(xR, bw), *pt(xR, sill)))                      # zadní hrana dveří
        hxs = None
    # kliky, zrcátko, světla
    if hxs:
        for hx0 in hxs:
            a = pt(hx0, bw-24); out.append(R(a[0] - (52 if flip else 0), a[1], 52, 12, 6, sw=3))
    else:
        out.append(R(*pt(xB-90, bw-24) if not flip else (pt(xB-90, bw-24)[0]-52, pt(xB-90, bw-24)[1]), 52, 12, 6, sw=3))
        out.append(R(*pt(xB+70, bw-24) if not flip else (pt(xB+70, bw-24)[0]-46, pt(xB+70, bw-24)[1]), 46, 11, 5, sw=3))
    mx, my = pt(T["xc"]+16, bw-4)
    out.append(P(f"M{mx:.1f},{my:.1f} l{-26 if not flip else 26},-6 l{-2 if not flip else 2},-20 l{30 if not flip else -30},2 z", sw=3))
    hx, hy = pt(10, T["hf"]-10)
    wdir = 1 if not flip else -1
    out.append(P(f"M{hx:.1f},{hy:.1f} l{70*wdir},6 l{-4*wdir},24 l{-62*wdir},-4 z", sw=3.2))
    tx0, ty0 = pt(Lw-8, T["hr"]-6)
    out.append(P(f"M{tx0:.1f},{ty0:.1f} l{-14*wdir},0 l0,{46} l{14*wdir},0 z", sw=3.2))
    # spodní lišta (šedá), linie sillu
    # střešní ližiny
    if T["rails"]:
        out.append(L(*pt(T["x1"]+60, T["H"]+8), *pt(T["x2"]-40, T["H"]+8), INK, 4))
        for xx in (T["x1"]+110, T["x2"]-90): out.append(L(*pt(xx, T["H"]), *pt(xx, T["H"]+8), INK, 3))
    # linie země
    out.append(L(ground_x[0], gy+10, ground_x[1], gy+10, GREY, 3))
    return "\n".join(out)

def front_rear(t, cx, gy, rear):
    T = TYPES[t]; F = T["front"]; W = F["W"]; H = F["H"]; hf = F["hf"]; wb_ = F["wb"]
    def X(x): return cx + x
    def Y(y): return gy - y
    o = []
    hw = W/2
    # karoserie spodní (nárazník) 
    o.append(R(X(-hw), Y(hf), W, hf-46, 22))
    # střecha/okna: lichoběžník
    top_w = W*(0.74 if T.get('open') else 0.62); base_w = W*0.86
    o.append(P(rpath([(X(-base_w/2), Y(wb_)), (X(-top_w/2), Y(H-22)), (X(-top_w/2+16), Y(H)), (X(top_w/2-16), Y(H)), (X(top_w/2), Y(H-22)), (X(base_w/2), Y(wb_))], r=16)))
    # sklo
    gl_w0 = base_w*0.82; gl_w1 = top_w*0.78
    if not rear:
        o.append(P(rpath([(X(-gl_w0/2), Y(wb_+4)), (X(-gl_w1/2), Y(H-34)), (X(gl_w1/2), Y(H-34)), (X(gl_w0/2), Y(wb_+4))], r=10, closed=True), sw=3.6))
    elif T.get('open'):
        for sg in (-1, 1):
            o.append(R(X(sg*62 - 17), Y(wb_+4+46), 34, 46, 12, sw=3.4))   # opěrky hlav
    else:
        o.append(P(rpath([(X(-gl_w0/2), Y(wb_+14)), (X(-gl_w1/2-4), Y(H-34)), (X(gl_w1/2+4), Y(H-34)), (X(gl_w0/2), Y(wb_+14))], r=10, closed=True), sw=3.6))
    # zrcátka
    for s in (-1, 1):
        mx = X(s*base_w/2); my = Y(wb_-2)
        o.append(P(f"M{mx:.1f},{my:.1f} l{s*34},-8 l{s*8},-22 l{-s*34},6 z", sw=3.2))
    if T["rails"]:
        for s in (-1, 1): o.append(L(X(s*top_w/2), Y(H+4), X(s*top_w/2-2), Y(H-18), INK, 5))
    # světla, znak, spz
    if not rear:
        for s in (-1, 1):
            o.append(P(f"M{X(s*(hw-12)):.1f},{Y(hf-18):.1f} l{-s*84},-3 l{-s*6},-30 l{s*78},-2 z".replace("-3","3").replace("-30","30").replace("-2 z","2 z"), sw=3.4))
        o.append(R(X(-52), Y(hf-18), 104, 46, 10))
        o.append(L(X(-44), Y(hf-40), X(44), Y(hf-40), GREY, 3))
        o.append(R(X(-40), Y(hf-76), 80, 24, 4, sw=3.4))
        for s in (-1, 1): o.append(C(X(s*(hw-34)), Y(76), 11, sw=3.4))
        o.append(R(X(-70), Y(70), 140, 12, 6, sw=3.4))
    else:
        for s in (-1, 1):
            o.append(R(X(s*(hw-14) - (0 if s < 0 else 76)), Y(hf-8), 76, 40, 8, sw=3.4))
        o.append(R(X(-40), Y(hf-60), 80, 24, 4, sw=3.4))
        o.append(L(X(-110), Y(64), X(110), Y(64), GREY, 4))
        o.append(L(X(-hw+24), Y(wb_-2), X(hw-24), Y(wb_-2), GREY, 3))
    # kola
    for s in (-1, 1):
        o.append(R(X(s*(hw-36) - 30), Y(52), 60, 52, 12))
    o.append(L(cx-245, gy+10, cx+245, gy+10, GREY, 3))
    return "\n".join(o)

def top(t, cx, cy):
    T = TYPES[t]; Lt = T["L_top"]; W = T["W_top"]
    x0 = cx - Lt/2; y0 = cy - W/2
    o = []
    hw = W/2
    # obrys: zaoblený se zúženou přídí/zádí
    pts = [(x0, cy-hw*.62), (x0+Lt*.06, cy-hw*.92), (x0+Lt*.35, cy-hw), (x0+Lt*.75, cy-hw), (x0+Lt*.94, cy-hw*.9), (x0+Lt, cy-hw*.55),
           (x0+Lt, cy+hw*.55), (x0+Lt*.94, cy+hw*.9), (x0+Lt*.75, cy+hw), (x0+Lt*.35, cy+hw), (x0+Lt*.06, cy+hw*.92), (x0, cy+hw*.62)]
    o.append(P(rpath(pts, r=60, closed=True)))
    k = Lt/ T["L"]   # měřítko bok -> shora
    xs = lambda x: x0 + x*k
    # čelní sklo, střecha, zadní sklo
    xc, x1, x2, x3 = xs(T["xc"]), xs(T["x1"]), xs(T["x2"]), xs(T["x3"]-(0 if T["tailgate"] else 40))
    wsh = hw*0.82
    o.append(P(rpath([(xc, cy-wsh), (x1, cy-wsh*0.8), (x1, cy+wsh*0.8), (xc, cy+wsh)], r=6, closed=True)))
    if T.get("open"):
        xe = x2 + (x3-x2)*0.4
        o.append(R(x1+10, cy-wsh*0.78, xe-x1-10, wsh*1.56, 34))
        for sg in (-1, 1):
            sy = cy + sg*wsh*0.42
            o.append(R(x1+60, sy-30, 78, 60, 16, sw=3.4))     # sedadlo (sedák)
            o.append(R(x1+140, sy-26, 30, 52, 12, sw=3.4))    # opěradlo/opěrka
        o.append(L(xe+30, cy-wsh*0.7, xe+30, cy+wsh*0.7, GREY, 3))
    else:
        o.append(R(x1+6, cy-wsh*0.8, x2-x1-12, wsh*1.6, 18))
        o.append(P(rpath([(x2, cy-wsh*0.8), (x3, cy-wsh*0.9), (x3, cy+wsh*0.9), (x2, cy+wsh*0.8)], r=6, closed=True)))
    # kapota/víko linie, zrcátka, světla
    for s in (-1, 1):
        o.append(P(f"M{xc:.1f},{cy+s*wsh:.1f} l-14,{s*22} l16,{s*10} l16,{-s*8}", sw=3.2))
        o.append(P(f"M{x0+6:.1f},{cy+s*hw*.42:.1f} l{Lt*.07:.1f},{s*hw*.18:.1f} l-4,{s*22} l-{Lt*.06:.1f},-6 z".replace("l-4,","l-4,"), sw=3.2))
        o.append(L(x0+Lt*.14, cy+s*hw*.5, xc-14, cy+s*hw*.6, GREY, 3))
        o.append(P(f"M{x0+Lt-8:.1f},{cy+s*hw*.30:.1f} l-{Lt*.045:.1f},{s*hw*.12:.1f} l-3,{s*16} l{Lt*.04:.1f},-2 z", sw=3.2))
    for xx in (T["xc"]+ (T["x1"]-T["xc"])/2, ):
        pass
    if T["rails"]:
        for s in (-1, 1): o.append(L(x1+30, cy+s*wsh*.74, x2-30, cy+s*wsh*.74, INK, 4))
    return "\n".join(o)

def sheet(t):
    f = '<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="#dedede" stroke-width="2"/>'
    s = '<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="1414" viewBox="0 0 2000 1414"><rect width="2000" height="1414" fill="#fff"/>'
    s += '<rect x="1" y="1" width="1998" height="1412" fill="none" stroke="#d6d6d6" stroke-width="2"/>'
    for (x, y, w, h) in [(62, 53, 1243, 422), (1327, 53, 611, 422), (62, 497, 1243, 421), (1327, 497, 611, 421), (62, 940, 1876, 420)]:
        s += f.format(x, y, w, h)
    T = TYPES[t]
    ox1 = 62 + (1243 - T["L"])/2
    s += f'<g>{side(t, ox1, 420, False, (ox1-16, ox1+T["L"]+14))}</g>'
    s += f'<g>{side(t, ox1, 862, True, (ox1-16, ox1+T["L"]+14))}</g>'
    s += f'<g>{front_rear(t, 1632, 440, False)}</g>'
    s += f'<g>{front_rear(t, 1632, 884, True)}</g>'
    s += f'<g>{top(t, 1000, 1150)}</g>'
    return s + '</svg>'

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    keys = sys.argv[1:] or list(TYPES)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = b.new_page(viewport={"width": 2000, "height": 1414}, device_scale_factor=1.4)
        for k in keys:
            pg.set_content(f'<html><body style="margin:0">{sheet(k)}</body></html>')
            pg.screenshot(path=os.path.join(OUT, k + ".png"))
            print("wrote", k)
        b.close()
