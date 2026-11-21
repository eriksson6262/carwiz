"""RX Auto – Reel "Dvě mise" (ukrást vs. pronajmout), retro-neon herní stylizace.
1080x1920, 30 fps, 15 s.  python3 render_mise.py preview | render
"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 15.0
HOR = 1060                                   # horizont
FONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
FONT_I = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat-Italic[wght].ttf"
PINK, CYAN, YEL, RED, GREEN = (255, 61, 154), (53, 224, 255), (255, 210, 63), (255, 45, 60), (60, 230, 140)
WHITE, DARK = (255, 255, 255), (10, 8, 20)
T1, T2, T3 = 2.6, 7.2, 12.0                  # střihy

_fc = {}
def font(size, weight="Black", italic=True):
    k = (size, weight, italic)
    if k not in _fc:
        f = ImageFont.truetype(FONT_I if italic else FONT, size)
        f.set_variation_by_name(weight + (" Italic" if italic else ""))
        _fc[k] = f
    return _fc[k]

def clamp(x): return max(0.0, min(1.0, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def seg(t, a, b): return clamp((t - a) / (b - a))
def lerp(a, b, x): return a + (b - a) * x
def rgba(c, a=1.0): return (c[0], c[1], c[2], int(255 * clamp(a)))

def vgrad(stops, h=H, w=W):
    arr = np.zeros((h, w, 3), dtype=np.float32)
    ys = np.arange(h) / (h - 1)
    for i in range(3):
        arr[:, :, i] = np.interp(ys, [s[0] for s in stops], [s[1][i] for s in stops])[:, None]
    return Image.fromarray(arr.astype(np.uint8))

rnd = random.Random(7)

# ---------- pozadí: západ slunce ----------
def make_sunset():
    im = vgrad([(0, (38, 10, 92)), (0.30, (150, 28, 140)), (0.47, (255, 80, 120)), (HOR / H, (255, 170, 80)), (1, (255, 170, 80))])
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sg = vgrad([(0, (255, 236, 120)), (1, (255, 70, 150))], h=640, w=640)
    m = Image.new("L", (640, 640), 0)
    md = ImageDraw.Draw(m); md.ellipse([0, 0, 639, 639], fill=255)
    for i in range(7):                                    # pruhy
        y = 330 + i * 46; md.rectangle([0, y, 640, y + 8 + i * 4], fill=0)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([540 - 380, 760 - 380, 540 + 380, 760 + 380], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    im.paste(Image.new("RGB", (W, H), (255, 200, 150)), (0, 0), glow)
    im.paste(sg, (220, 440), m)
    d = ImageDraw.Draw(im)
    x = -20
    while x < W:                                          # silueta města
        bw = rnd.randint(50, 130); bh = rnd.randint(40, 230)
        if 380 < x < 640: bh = rnd.randint(30, 90)
        d.rectangle([x, HOR - bh, x + bw, HOR], fill=(60, 16, 90))
        x += bw + rnd.randint(-6, 14)
    return im

def make_night():
    im = vgrad([(0, (4, 3, 16)), (0.35, (18, 10, 52)), (HOR / H, (70, 20, 96)), (1, (70, 20, 96))])
    d = ImageDraw.Draw(im)
    for _ in range(140):
        x, y = rnd.randint(0, W), rnd.randint(0, HOR - 250); v = rnd.randint(120, 255)
        d.point((x, y), fill=(v, v, v))
    x = -20
    while x < W:
        bw = rnd.randint(60, 140); bh = rnd.randint(80, 330)
        d.rectangle([x, HOR - bh, x + bw, HOR], fill=(12, 8, 30))
        for wy in range(HOR - bh + 14, HOR - 10, 26):
            for wx in range(x + 10, x + bw - 14, 22):
                if rnd.random() < 0.35:
                    d.rectangle([wx, wy, wx + 9, wy + 12], fill=rnd.choice([(255, 210, 120), (120, 220, 255), (255, 120, 190)]))
        x += bw + rnd.randint(-6, 12)
    return im

def make_palm(h=900, flip=False):
    im = Image.new("RGBA", (700, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (24, 8, 44, 255)
    pts = [(330 + 60 * math.sin(i / 20 * 1.6), h - i * (h - 200) / 20) for i in range(21)]
    for i in range(20):
        wdt = lerp(26, 12, i / 20)
        d.line([pts[i], pts[i + 1]], fill=col, width=int(wdt))
    cx, cy = pts[-1]
    for ang in (-170, -140, -110, -75, -40, -10, 20, 200):
        a = math.radians(ang); L = 300
        prev = None
        for k in range(1, 15):
            u = k / 14
            px = cx + math.cos(a) * L * u
            py = cy + math.sin(a) * L * u + 190 * u * u
            if prev: d.line([prev, (px, py)], fill=col, width=10)
            fl = 80 * math.sin(math.pi * u) + 12
            d.line([(px, py), (px - 14, py + fl)], fill=col, width=7)
            d.line([(px, py), (px + 14, py + fl * 0.8)], fill=col, width=6)
            prev = (px, py)
    return ImageOps.mirror(im) if flip else im

SUNSET, NIGHT = make_sunset(), make_night()
GROUND_D = vgrad([(0, (150, 40, 120)), (0.25, (88, 22, 100)), (1, (40, 12, 66))], h=H - HOR)
GROUND_N = vgrad([(0, (40, 14, 70)), (1, (10, 6, 26))], h=H - HOR)
PALM_L, PALM_R = make_palm(), make_palm(flip=True)

# ---------- auto ----------
cut = Image.open(os.path.join(HERE, "src", "car_cut.png")).convert("RGBA")
bb = cut.getbbox(); cut = cut.crop(bb)
CAR_W = 860
cut = cut.resize((CAR_W, int(CAR_W * cut.height / cut.width)), Image.LANCZOS)
def tint(im, c):
    r, g, b, a = im.split()
    rgb = ImageChops.multiply(Image.merge("RGB", (r, g, b)), Image.new("RGB", im.size, c))
    rgb.putalpha(a); return rgb
CAR_DAY, CAR_NIGHT = tint(cut, (255, 238, 228)), tint(cut, (150, 160, 215))
shadow = Image.new("L", (CAR_W + 200, 240), 0)
ImageDraw.Draw(shadow).ellipse([60, 60, CAR_W + 140, 190], fill=190)
shadow = shadow.filter(ImageFilter.GaussianBlur(28))

def glow_sprite(c, r=260):
    m = Image.new("L", (r * 2, r * 2), 0)
    ImageDraw.Draw(m).ellipse([r * 0.55, r * 0.55, r * 1.45, r * 1.45], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.22))
    im = Image.new("RGBA", (r * 2, r * 2), c + (0,)); im.putalpha(m); return im
G_RED, G_BLUE, G_WHITE = glow_sprite((255, 30, 50)), glow_sprite((40, 90, 255)), glow_sprite((255, 245, 210), 120)

def stamp(text, col, size=118):
    f = font(size)
    tw = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=f))
    im = Image.new("RGBA", (tw + 120, size + 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, im.width - 7, im.height - 7], radius=18, fill=(8, 6, 18, 215), outline=col + (255,), width=10)
    d.text((im.width / 2, im.height / 2 - 4), text, font=f, fill=col + (255,), anchor="mm")
    return im.rotate(7, expand=True, resample=Image.BICUBIC)
ST_FAIL, ST_OK = stamp("BUSTED", RED, 190), stamp("MISE SPLNĚNA", GREEN, 104)
logo = ImageOps.invert(Image.open(os.path.join(HERE, "src", "RX_logo.jpg")).convert("L")).resize((260, 171), Image.LANCZOS)

# ---------- prvky scény ----------
def road(d, t, speed, night):
    d.polygon([(540 - 30, HOR), (540 + 30, HOR), (W + 520, H), (-520, H)], fill=(22, 16, 40) if night else (44, 22, 66))
    edge = CYAN if night else PINK
    d.line([(540 - 30, HOR), (-520, H)], fill=edge, width=8)
    d.line([(540 + 30, HOR), (W + 520, H)], fill=edge, width=8)
    def pt(off, p):                                       # p: 0 horizont .. 1 dole
        y = HOR + (H - HOR) * p
        half = 30 + (1050 - 30) * p
        return 540 + off * half, y
    for off in (-0.36, 0.36):
        for k in range(9):
            p0 = ((k / 9 - t * speed) % 1.0)
            pa, pb = p0 ** 2.2, min(1.0, p0 + 0.05) ** 2.2
            (xa, ya), (xb, yb) = pt(off, pa), pt(off, pb)
            w = 2 + 16 * pb
            d.polygon([(xa - w * 0.5 * pa / max(pb, 1e-3), ya), (xa + w * 0.5 * pa / max(pb, 1e-3), ya), (xb + w / 2, yb), (xb - w / 2, yb)],
                      fill=(240, 240, 255) if night else (255, 225, 170))

def cop(im, x, y, s, t, k):
    d = ImageDraw.Draw(im)
    w, h = 330 * s, 190 * s
    on = int(t * 7 + k) % 2
    for g, dx in ((G_RED, -0.25), (G_BLUE, 0.25)):
        act = (dx < 0) == bool(on)
        gs = int(520 * s * (1.25 if act else 0.5))
        gg = g.resize((gs, gs), Image.BILINEAR)
        if not act: gg.putalpha(gg.getchannel("A").point(lambda v: v // 3))
        im.alpha_composite(gg, (int(x + dx * w - gs / 2), int(y - h * 0.62 - gs / 2)))
    d.rounded_rectangle([x - w / 2, y - h * 0.5, x + w / 2, y + h * 0.5], radius=int(26 * s), fill=(14, 14, 30, 255))
    d.rounded_rectangle([x - w * 0.36, y - h * 0.84, x + w * 0.36, y - h * 0.4], radius=int(14 * s), fill=(22, 24, 52, 255))
    d.rectangle([x - w * 0.5, y - h * 0.02, x + w * 0.5, y + h * 0.12], fill=(235, 235, 245, 255))
    d.rectangle([x - w * 0.26, y - h * 0.9, x - 2, y - h * 0.8], fill=(255, 40, 60, 255) if on else (90, 10, 20, 255))
    d.rectangle([x + 2, y - h * 0.9, x + w * 0.26, y - h * 0.8], fill=(60, 110, 255, 255) if not on else (12, 24, 90, 255))
    for sx in (-0.36, 0.36):
        hs = int(150 * s); hg = G_WHITE.resize((hs, hs), Image.BILINEAR)
        im.alpha_composite(hg, (int(x + sx * w - hs / 2), int(y + h * 0.05 - hs / 2)))

def world(t, night, speed, shake=0.0, cops=0.0, drift=0.0):
    im = (NIGHT if night else SUNSET).copy().convert("RGBA")
    im.paste(GROUND_N if night else GROUND_D, (0, HOR))
    d = ImageDraw.Draw(im)
    road(d, t, speed, night)
    if not night:
        for spr, x0 in ((PALM_L, -250), (PALM_R, 630)):
            im.alpha_composite(spr, (int(x0 + drift * (1 if x0 < 0 else -1)), HOR - 800))
    if cops > 0:
        s = lerp(0.42, 0.72, cops)
        yb = lerp(HOR + 40, HOR + 150, cops)
        cop(im, 205 + 14 * math.sin(t * 9), yb + 5 * math.sin(t * 23), s, t, 0)
        cop(im, 875 + 14 * math.sin(t * 8 + 2), yb + 10 + 5 * math.sin(t * 19), s * 0.94, t, 1)
    r = random.Random(int(t * FPS))
    dx = r.uniform(-1, 1) * 12 * shake + (40 * math.sin(t * 5.2) if shake else 0)
    dy = r.uniform(-1, 1) * 8 * shake + 5 * math.sin(t * (9 if shake else 2.2))
    car = CAR_NIGHT if night else CAR_DAY
    cx, cy = 540 + dx, 1520 + dy
    sh = Image.new("RGBA", shadow.size, (0, 0, 0, 0)); sh.putalpha(shadow)
    im.alpha_composite(sh, (int(cx - shadow.width / 2), int(cy + car.height / 2 - 150)))
    if shake:
        car = car.rotate(2.2 * math.sin(t * 5.2), resample=Image.BICUBIC)
    im.alpha_composite(car, (int(cx - car.width / 2), int(cy - car.height / 2)))
    if night:                                              # majáky zalévají scénu
        on = int(t * 7) % 2
        im.alpha_composite(Image.new("RGBA", (W, H), ((255, 20, 50) if on else (30, 70, 255)) + (int(46 * cops + 10),)))
    return im

def tracked(d, xy, s, f, fill, track=0):
    ws = [d.textlength(c, font=f) for c in s]
    x = xy[0] - (sum(ws) + track * (len(s) - 1)) / 2
    for c, w in zip(s, ws):
        d.text((x, xy[1]), c, font=f, fill=fill); x += w + track

def outlined(d, xy, s, f, fill, a=1.0, sw=8, anchor="mm"):
    d.text(xy, s, font=f, fill=rgba(fill, a), anchor=anchor, stroke_width=sw, stroke_fill=rgba(DARK, a))

def mission_header(d, t, t0, tag, title, col):
    a = ease(seg(t, t0, t0 + 0.35)); sl = (1 - a) * -260
    f = font(40, "ExtraBold")
    tw = d.textlength(tag, font=f)
    d.polygon([(90 + sl, 232), (90 + sl + tw + 70, 232), (90 + sl + tw + 50, 300), (70 + sl, 300)], fill=rgba(col, a))
    d.text((112 + sl, 266), tag, font=f, fill=rgba(DARK, a), anchor="lm")
    fs = 132
    while d.textlength(title, font=font(fs)) > 900: fs -= 4
    outlined(d, (84 + sl, 392), title, font(fs), WHITE, a, sw=10, anchor="lm")

def bar(d, y, label, val, col, a):
    d.text((90, y), label, font=font(34, "ExtraBold"), fill=rgba(WHITE, a), anchor="lm", stroke_width=5, stroke_fill=rgba(DARK, a))
    d.rounded_rectangle([300, y - 20, 760, y + 20], radius=20, fill=rgba(DARK, 0.75 * a), outline=rgba(WHITE, a), width=3)
    if val > 0.02:
        d.rounded_rectangle([306, y - 14, 306 + 448 * val, y + 14], radius=14, fill=rgba(col, a))
    d.text((782, y), f"{int(val * 100)} %", font=font(34, "ExtraBold"), fill=rgba(col, a), anchor="lm", stroke_width=5, stroke_fill=rgba(DARK, a))

def put_stamp(im, st, t, t0, cy=1010):
    if t < t0: return
    u = seg(t, t0, t0 + 0.22)
    s = lerp(2.3, 1.0, ease(u))
    sp = st.resize((int(st.width * s), int(st.height * s)), Image.BILINEAR)
    if u < 1: sp.putalpha(sp.getchannel("A").point(lambda v: int(v * (0.3 + 0.7 * u))))
    im.alpha_composite(sp, (int(540 - sp.width / 2), int(cy - sp.height / 2)))

def frame(t):
    if t < T1:                                             # ---- úvod
        im = world(t, False, 0.25)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.rectangle([0, 0, W, H], fill=(10, 4, 30, 70))
        a1, a2, a3 = ease(seg(t, 0.15, 0.6)), ease(seg(t, 0.5, 0.95)), ease(seg(t, 0.9, 1.35))
        outlined(d, (540, 300 - (1 - a1) * 40), "JEDNO AUTO.", font(104), WHITE, a1)
        outlined(d, (540, 430 - (1 - a2) * 40), "DVĚ MISE.", font(132), YEL, a2, sw=10)
        tracked(d, (540, 520), "MERCEDES-BENZ GLC COUPÉ", font(34, "Bold", False), rgba(WHITE, a3), track=6)
        if t > 1.5 and int(t * 4) % 2 == 0:
            outlined(d, (540, 1000), "VYBER SI ▼", font(60), CYAN, 1, sw=7)
        im.alpha_composite(ov)
    elif t < T2:                                           # ---- mise A: ukrást
        u = seg(t, T1, T2)
        fail = t >= 6.2
        im = world(t, True, 1.7 if not fail else 0.0, shake=0 if fail else 1.0, cops=ease(u * 1.25))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        mission_header(d, t, T1 + 0.05, "MISE A", "UKRÁST", RED)
        a = ease(seg(t, T1 + 0.5, T1 + 0.9))
        bar(d, 520, "STRES", ease(seg(t, T1 + 0.6, 5.4)), RED, a)
        bar(d, 590, "KLID", 1 - ease(seg(t, T1 + 0.6, 4.4)), CYAN, a)
        if not fail and t > 3.6 and int(t * 5) % 2 == 0:
            outlined(d, (540, 760), "POLICIE V PATÁCH!", font(70), YEL, 1, sw=8)
        if fail:
            d.rectangle([0, 0, W, H], fill=(60, 0, 10, 110))
        im.alpha_composite(ov)
        put_stamp(im, ST_FAIL, t, 6.2, cy=960)
        if t >= 6.45:                                      # řada majáků pod nápisem
            d2 = ImageDraw.Draw(im)
            for i in range(5):
                on = (int(t * 6) + i) % 2 == 0
                col = (RED if i % 2 == 0 else (60, 110, 255))
                x = 540 + (i - 2) * 120; y = 1215 - (i - 2) * 14
                if on:
                    g = (G_RED if i % 2 == 0 else G_BLUE).resize((200, 200), Image.BILINEAR)
                    im.alpha_composite(g, (x - 100, y - 110))
                d2.pieslice([x - 34, y - 44, x + 34, y + 24], 180, 360, fill=col + (255,) if on else tuple(c // 3 for c in col) + (255,), outline=DARK + (255,), width=5)
                d2.rounded_rectangle([x - 44, y - 12, x + 44, y + 8], radius=6, fill=(230, 230, 240, 255), outline=DARK + (255,), width=4)
    elif t < T3:                                           # ---- mise B: pronajmout
        im = world(t, False, 0.38, drift=(t - T2) * 9)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        mission_header(d, t, T2 + 0.05, "MISE B", "PRONAJMOUT", GREEN)
        a = ease(seg(t, T2 + 0.5, T2 + 0.9))
        bar(d, 520, "STRES", 0.0, RED, a)
        bar(d, 590, "KLID", ease(seg(t, T2 + 0.6, 9.4)), GREEN, a)
        for i, s in enumerate(["ŽÁDNÉ SIRÉNY", "ŽÁDNÝ ÚTĚK", "JEN TY A CESTA"]):
            b = ease(seg(t, 8.6 + i * 0.45, 9.0 + i * 0.45))
            if b > 0:
                x0, y0 = 90 - (1 - b) * 80, 700 + i * 78
                for wd, cl in ((22, DARK), (11, GREEN)):
                    d.line([(x0 + 4, y0 + 2), (x0 + 20, y0 + 18), (x0 + 50, y0 - 20)], fill=rgba(cl, b), width=wd, joint="curve")
                outlined(d, (x0 + 78, y0), s, font(50, "ExtraBold"), WHITE, b, sw=7, anchor="lm")
        im.alpha_composite(ov)
        put_stamp(im, ST_OK, t, 10.9, cy=1040)
    else:                                                  # ---- závěr
        im = world(t, False, 0.3, drift=(T3 - T2) * 9)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        p = ease(seg(t, T3, T3 + 0.5))
        d.rectangle([0, 0, W, int(lerp(0, 1110, p))], fill=(8, 6, 18, 240))
        d.rectangle([0, int(lerp(0, 1110, p)), W, int(lerp(0, 1110, p)) + 6], fill=YEL + (255,))
        a1, a2, a3, a4 = (ease(seg(t, T3 + 0.3 + i * 0.3, T3 + 0.75 + i * 0.3)) for i in range(4))
        d.text((540, 480), "NEKRAĎ.", font=font(120), fill=rgba(WHITE, a1), anchor="mm")
        d.text((540, 620), "PRONAJMI SI.", font=font(120), fill=rgba(YEL, a2), anchor="mm")
        tracked(d, (540, 720), "MERCEDES-BENZ GLC COUPÉ", font(34, "Bold", False), rgba((200, 200, 215), a3), track=6)
        d.rounded_rectangle([540 - 210, 830, 540 + 210, 930], radius=50, fill=rgba(YEL, a4))
        d.text((540, 880), "rxauto.cz", font=font(50, "Bold", False), fill=rgba(DARK, a4), anchor="mm")
        tracked(d, (540, 975), "PRAHA · OSTRAVA · BRATISLAVA", font(28, "SemiBold", False), rgba((170, 170, 190), a4), track=6)
        im.alpha_composite(ov)
        if a1 > 0:
            lg = Image.new("RGBA", logo.size, (255, 255, 255, 0)); lg.putalpha(logo.point(lambda v: int(v * a1)))
            im.alpha_composite(lg, (540 - 130, 215))
    for tc in (T1, T2, T3):                                # záblesk na střihu
        if tc <= t < tc + 0.18:
            im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(230 * (1 - (t - tc) / 0.18)))))
    return im.convert("RGB")

# ---------- zvuk (syntetický, bez cizí hudby) ----------
def audio(path, sr=44100):
    n = int(DUR * sr); t = np.arange(n) / sr
    out = np.zeros(n)
    def env(a, b, fi=0.15, fo=0.25):
        return np.clip((t - a) / fi, 0, 1) * np.clip((b - t) / fo, 0, 1)
    def pad(freqs, a, b, vol):
        s = sum(np.sin(2 * np.pi * f * t + i) + 0.4 * np.sin(2 * np.pi * f * 2.003 * t) for i, f in enumerate(freqs))
        return s / len(freqs) * env(a, b, 0.6, 0.8) * vol * (0.85 + 0.15 * np.sin(2 * np.pi * 0.4 * t))
    out += pad([110, 164.8, 220, 277.2], 0, T1 + 0.2, 0.16)                       # úvod A dur
    f = 760 + 240 * np.sin(2 * np.pi * 0.9 * t)                                   # siréna
    out += np.sin(2 * np.pi * np.cumsum(f) / sr) * env(T1 + 0.3, 6.25, 0.5, 0.1) * 0.13
    out += np.sign(np.sin(2 * np.pi * 55 * t)) * np.abs(np.sin(2 * np.pi * 4 * t)) * env(T1, 6.2, 0.05, 0.05) * 0.07   # napětí
    out += np.sin(2 * np.pi * 70 * np.exp(-(t - 6.2) * 3).clip(0, 1) * t) * env(6.2, 7.1, 0.01, 0.5) * 0.3             # "fail"
    out += pad([130.8, 196, 246.9, 329.6], T2, T3 + 0.3, 0.17)                    # klid Cmaj7
    for i, fq in enumerate([523.3, 659.3, 784.0, 1046.5]):                        # "splněno"
        a = 10.9 + i * 0.11
        out += np.sin(2 * np.pi * fq * t) * np.clip((t - a) / 0.01, 0, 1) * np.exp(-np.clip(t - a, 0, None) * 5) * 0.14
    out += pad([98, 146.8, 196, 246.9, 293.7], T3, DUR, 0.18)                     # závěr G
    out = np.tanh(out * 1.4) * 0.8
    out *= np.clip((DUR - t) / 0.6, 0, 1)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

SCENES = [(0.0, T1), (T1, T2), (T2, T3), (T3, DUR)]

def render():
    out = os.path.join(HERE, "output_mise"); os.makedirs(out, exist_ok=True)
    parts = []
    for i, (a, b) in enumerate(SCENES):
        tmp, fin = os.path.join(out, f"s{i}.tmp.mp4"), os.path.join(out, f"s{i}.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                              "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for n in range(int(round(a * FPS)), int(round(b * FPS))):
            p.stdin.write(frame(n / FPS).tobytes())
        p.stdin.close(); assert p.wait() == 0
        os.replace(tmp, fin); parts.append(fin); print("scene", i, flush=True)
    lst = os.path.join(out, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    sil, wav, fin = os.path.join(out, "video.mp4"), os.path.join(out, "audio.wav"), os.path.join(out, "rxauto-glc-dve-mise.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", sil])
    audio(wav)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", sil, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", fin])
    print(fin)

if __name__ == "__main__":
    if sys.argv[1:] == ["render"]:
        render()
    else:
        out = os.path.join(HERE, "output_mise"); os.makedirs(out, exist_ok=True)
        ts = [2.0, 4.6, 6.6, 10.2, 11.3, 14.0]
        sheet = Image.new("RGB", (360 * len(ts), 640))
        for i, t in enumerate(ts):
            sheet.paste(frame(t).resize((360, 640), Image.LANCZOS), (i * 360, 0))
        sheet.save(os.path.join(out, "preview.jpg"), quality=88)
        frame(4.6).save(os.path.join(out, "f_a.jpg"), quality=90)
        frame(10.2).save(os.path.join(out, "f_b.jpg"), quality=90)
