"""RX Auto – Reel Mercedes-Benz GLC Coupé (1080x1920, 30 fps, 12 s).
Použití: python3 render.py preview | python3 render.py render
"""
import os, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 12.0
FONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
GOLD = (184, 148, 80)
INK = (17, 17, 17)
PANEL = (10, 10, 10)

_fc = {}
def font(size, weight="Bold"):
    k = (size, weight)
    if k not in _fc:
        f = ImageFont.truetype(FONT, size)
        f.set_variation_by_name(weight)
        _fc[k] = f
    return _fc[k]

def clamp(x): return max(0.0, min(1.0, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def seg(t, a, b): return clamp((t - a) / (b - a))
def lerp(a, b, x): return a + (b - a) * x

# ---------- podklady ----------
src = Image.open(os.path.join(HERE, "src", "glc.png")).convert("RGB")
# podlaha studiové fotky má ostré okraje -> plynule ji vytratit do bílé
_w = Image.new("L", src.size, 255)
_px = _w.load()
for _y in range(src.height):
    fb = clamp((594 - _y) / 22.0) if _y > 572 else 1.0
    k = clamp((_y - 470) / 60.0)          # boční vytrácení nabíhá postupně
    for _x in range(src.width):
        fs = min(clamp((_x - 336) / 40.0), clamp((944 - _x) / 40.0))
        fs = 1 - k * (1 - fs)
        fe = min(clamp((_x - 334) / 6.0), clamp((947 - _x) / 6.0))   # tenká linka na okraji fotky
        _px[_x, _y] = int(255 * min(fb, fs, fe))
src = Image.composite(src, Image.new("RGB", src.size, "white"), _w)
car_src = src.crop((300, 215, 985, 615))                      # 685x400
CAR_W0 = 1060
car_big = car_src.resize((1272, int(1272 * 400 / 685)), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
logo = ImageOps.invert(Image.open(os.path.join(HERE, "src", "RX_logo.jpg")).convert("L"))
logo = logo.resize((300, int(300 * logo.height / logo.width)), Image.LANCZOS)

bg = Image.new("RGB", (W, H))
bd = ImageDraw.Draw(bg)
for y in range(H):
    v = int(lerp(246, 228, y / H))
    bd.line([(0, y), (W, y)], fill=(v, v, v - 2))

def text_tracked(d, xy, s, f, fill, track=0, anchor_center=True):
    widths = [d.textlength(c, font=f) for c in s]
    total = sum(widths) + track * (len(s) - 1)
    x = xy[0] - total / 2 if anchor_center else xy[0]
    for c, w in zip(s, widths):
        d.text((x, xy[1]), c, font=f, fill=fill)
        x += w + track

def rgba(c, a): return (c[0], c[1], c[2], int(255 * clamp(a)))

def frame(t):
    im = bg.copy()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # --- pohyb auta ---
    cy = 930
    cy = lerp(cy, 800, ease(seg(t, 4.0, 4.9)))
    cy = lerp(cy, 540, ease(seg(t, 8.0, 8.9)))
    scale = (1 + 0.05 * t / DUR) * lerp(1.0, 0.92, ease(seg(t, 8.0, 8.9)))
    cx = lerp(W + 700, 540, ease(seg(t, 0.15, 1.5)))

    # --- "GLC" v pozadí ---
    ga = ease(seg(t, 0.0, 0.8)) * (1 - seg(t, 8.0, 8.5))
    if ga > 0:
        gf = font(560, "Black")
        gx = lerp(60, -70, t / DUR)
        d.text((gx, cy - 660), "GLC", font=gf, fill=rgba((214, 214, 210), ga))
    im.paste(ov, (0, 0), ov)

    # --- auto (multiply: bílé pozadí fotky zmizí) ---
    cw = int(CAR_W0 * scale); ch = int(cw * 400 / 685)
    car = car_big.resize((cw, ch), Image.BILINEAR)
    x0, y0 = int(cx - cw / 2), int(cy - ch / 2)
    bx0, by0, bx1, by1 = max(0, x0), max(0, y0), min(W, x0 + cw), min(H, y0 + ch)
    if bx1 > bx0 and by1 > by0:
        reg = im.crop((bx0, by0, bx1, by1))
        cc = car.crop((bx0 - x0, by0 - y0, bx1 - x0, by1 - y0))
        im.paste(ImageChops.multiply(reg, cc), (bx0, by0))

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # --- titulek ---
    ta = ease(seg(t, 0.9, 1.7)) * (1 - seg(t, 7.9, 8.3))
    if ta > 0:
        dy = (1 - ease(seg(t, 0.9, 1.7))) * 40
        text_tracked(d, (540, 250 + dy), "MERCEDES-BENZ", font(34, "SemiBold"), rgba((90, 90, 90), ta), track=14)
        d.text((540, 372 + dy), "GLC Coupé", font=font(124, "ExtraBold"), fill=rgba(INK, ta), anchor="mm")
        lw = 220 * ease(seg(t, 1.3, 2.2))
        d.rectangle([540 - lw / 2, 462, 540 + lw / 2, 466], fill=rgba(GOLD, ta))

    # --- scéna B: claimy ---
    out_b = 1 - seg(t, 7.5, 7.9)
    for i, (s, y) in enumerate([("Elegance kupé.", 1265), ("Prostor SUV.", 1375)]):
        a = ease(seg(t, 4.7 + i * 0.55, 5.4 + i * 0.55))
        if a > 0:
            d.text((540 + (1 - a) * -60, y), s, font=font(88, "ExtraBold"),
                   fill=rgba(INK if i == 0 else GOLD, a * out_b), anchor="mm")
    a = ease(seg(t, 6.0, 6.6))
    if a > 0:
        for s, x in [("AUTOMAT", 330), ("CENA NA DOTAZ", 700)]:
            f = font(32, "SemiBold")
            tw = sum(d.textlength(c, font=f) for c in s) + 5 * (len(s) - 1)
            px = tw / 2 + 34
            yy = 1510 + (1 - a) * 30
            d.rounded_rectangle([x - px, yy - 36, x + px, yy + 36], radius=36,
                                outline=rgba(INK, a * out_b), width=3)
            text_tracked(d, (x, yy - 21), s, f, rgba(INK, a * out_b), track=5)

    # --- scéna C: černý panel ---
    p = ease(seg(t, 8.0, 8.8))
    if p > 0:
        top = int(lerp(H, 900, p))
        d.rectangle([0, top, W, H], fill=PANEL + (255,))
        d.rectangle([0, top, W, top + 6], fill=GOLD + (255,))
    im.paste(ov, (0, 0), ov)

    if p > 0:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        a = ease(seg(t, 8.7, 9.4))
        if a > 0:
            lg = Image.new("RGB", logo.size, PANEL)
            lg = ImageChops.lighter(lg, Image.merge("RGB", [logo] * 3))
            lgl = Image.blend(Image.new("RGB", logo.size, PANEL), lg, a)
            im.paste(lgl, (540 - logo.width // 2, 1010))
            d.text((540, 1300), "K pronájmu u RX Auto", font=font(64, "Bold"), fill=rgba((255, 255, 255), a), anchor="mm")
        a2 = ease(seg(t, 9.1, 9.8))
        if a2 > 0:
            text_tracked(d, (540, 1368), "PRAHA · OSTRAVA · BRATISLAVA", font(30, "Medium"), rgba((170, 170, 170), a2), track=6)
        a3 = ease(seg(t, 9.5, 10.2))
        if a3 > 0:
            yy = 1520 + (1 - a3) * 30
            d.rounded_rectangle([540 - 200, yy - 48, 540 + 200, yy + 48], radius=48, fill=rgba(GOLD, a3))
            d.text((540, yy), "rxauto.cz", font=font(46, "Bold"), fill=rgba(PANEL, a3), anchor="mm")
        im.paste(ov, (0, 0), ov)
    return im

SCENES = [(0.0, 4.0), (4.0, 8.0), (8.0, 12.0)]

def render():
    out = os.path.join(HERE, "output"); os.makedirs(out, exist_ok=True)
    parts = []
    for i, (a, b) in enumerate(SCENES):
        tmp = os.path.join(out, f"scene{i}.tmp.mp4"); fin = os.path.join(out, f"scene{i}.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17",
                              "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for n in range(int(round(a * FPS)), int(round(b * FPS))):
            p.stdin.write(frame(n / FPS).tobytes())
        p.stdin.close()
        assert p.wait() == 0
        os.replace(tmp, fin); parts.append(fin); print("scene", i, "ok", flush=True)
    lst = os.path.join(out, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = os.path.join(out, "silent.mp4"); final = os.path.join(out, "rxauto-glc-coupe-reel.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i",
                           "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                           "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", final])
    print(final)

if __name__ == "__main__":
    if sys.argv[1:] == ["render"]:
        render()
    else:
        out = os.path.join(HERE, "output"); os.makedirs(out, exist_ok=True)
        ts = [0.8, 3.0, 7.0, 11.0]
        sheet = Image.new("RGB", (W // 2 * len(ts), H // 2))
        for i, t in enumerate(ts):
            sheet.paste(frame(t).resize((W // 2, H // 2), Image.LANCZOS), (i * W // 2, 0))
        sheet.save(os.path.join(out, "preview.jpg"), quality=88)
        frame(7.0).save(os.path.join(out, "f7.jpg"), quality=92)
