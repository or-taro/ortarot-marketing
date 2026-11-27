"""'오늘의 한 장' 릴스(약 12초). python3 today_reel.py spec.json out.mp4
spec: {"lang":"ko|ja","handle":"@or._tarot","id":12,"rev":false,"date":"11/24 (화)","hook":"오늘 당신에게 온 카드","name":"매달린 사람","dir":"정방향",
       "title":"잠시 멈춰 보는 하루","line":"서두르지 않아도 괜찮아요\\n다른 각도에서 보면 답이 보여요","end":"내 질문으로 직접 뽑아 보고 싶다면\\n프로필 링크의 오르타로에서","dim":"재미와 자기 성찰을 위한 참고용입니다",
       "music":"bgm.wav"}"""
import subprocess, math, json, sys, os
from PIL import Image, ImageDraw, ImageFont
S = json.load(open(sys.argv[1], encoding="utf-8")); OUT = sys.argv[2]; JA = S["lang"] == "ja"
W, H, FPS = 1080, 1920, 30
BG = (30, 18, 52); BG2 = (58, 32, 100); GOLD = (243, 200, 107); WHITE = (240, 235, 255); DIM = (190, 180, 220)
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"; FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
F = lambda p, s: ImageFont.truetype(p, s, index=0 if JA else 1)
CARDS = S.get("cards_dir", "/home/claude/ortarot-app/mobile/cards-original/")
def bg():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(BG[i]*(1-k)+BG2[i]*k) for i in range(3)))
    return im
BASE = bg()
def load(n, w):
    c = Image.open(CARDS + n).convert("RGBA").resize((w, int(w*1.5)), Image.LANCZOS)
    m = Image.new("L", c.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *c.size), 18, fill=255); c.putalpha(m); return c
BACK = load("card-back.webp", 500); FRONT = load(f'{S["id"]:02d}.webp', 500)
if S.get("rev"): FRONT = FRONT.rotate(180)
CX, CY = W//2, 820
ease = lambda t: 0.5 - 0.5*math.cos(math.pi*max(0, min(1, t)))
def ctext(d, y, txt, font, fill, a=255, sp=12):
    for line in txt.split("\n"):
        d.text((W//2, y), line, font=font, fill=fill+(a,), anchor="ma"); bb = d.textbbox((0, 0), line, font=font); y += bb[3]-bb[1]+sp+font.size//3
    return y
def put(im, c, sx=1.0, dy=0):
    w = max(2, int(c.width*sx)); c2 = c.resize((w, c.height)); im.paste(c2, (CX-w//2, CY-c2.height//2+dy), c2)
def frame(): return BASE.copy(), Image.new("RGBA", (W, H), (0, 0, 0, 0))
def fin(im, o):
    ImageDraw.Draw(o).text((W//2, 150), S["handle"], font=F(FD, 32), fill=DIM+(255,), anchor="ma"); im.paste(o, (0, 0), o); return im
def s_hook(f, n):
    t = f/n; im, o = frame(); d = ImageDraw.Draw(o); a = int(255*ease(t*3))
    ctext(d, 230, S["date"], F(FD, 40), DIM, a); ctext(d, 300, S["hook"], F(FB, 76), WHITE, a, 6)
    put(im, BACK, 1, int(8*math.sin(t*6))); return fin(im, o)
def s_flip(f, n):
    t = f/n; im, o = frame(); d = ImageDraw.Draw(o); ctext(d, 300, S["hook"], F(FB, 76), WHITE)
    put(im, BACK, 1-ease(t*2)) if t < 0.5 else put(im, FRONT, ease((t-0.5)*2)); return fin(im, o)
def s_msg(f, n):
    t = f/n; im, o = frame(); d = ImageDraw.Draw(o)
    ctext(d, 240, f'{S["name"]} · {S["dir"]}', F(FD, 46), GOLD, int(255*ease(t*5))); put(im, FRONT, 1, 0)
    a = int(255*ease(t*4)); y = ctext(d, 1270, S["title"], F(FB, 74), WHITE, a); ctext(d, y+14, S["line"], F(FD, 46), GOLD, int(255*ease(t*4-1.2)), 8)
    return fin(im, o)
def s_end(f, n):
    t = f/n; im, o = frame(); d = ImageDraw.Draw(o); a = int(255*ease(t*3))
    y = ctext(d, 640, S["title"], F(FB, 72), WHITE, a); y = ctext(d, y+70, S["end"], F(FD, 48), GOLD, a, 8); ctext(d, y+80, S["dim"], F(FR, 34), DIM, a, 6)
    return fin(im, o)
scenes = [(3.2, s_hook), (1.4, s_flip), (8.5, s_msg), (4.4, s_end)]  # 2026-11-23 주인님 "빠르다" → 12초→17.5초
tmp = OUT + ".v.mp4"
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
  "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
tot = 0; XF = int(0.6*FPS); prev = None
for sec, fn in scenes:
    n = int(sec*FPS)
    for f in range(n):
        fr = fn(f, n).convert("RGB")
        if prev is not None and f < XF:
            fr = Image.blend(prev, fr, ease((f+1)/XF))
        p.stdin.write(fr.tobytes()); tot += 1
    prev = fr
p.stdin.close(); p.wait()
mus = S.get("music")
if mus and os.path.exists(mus):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", mus, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    os.remove(tmp)
else:
    os.replace(tmp, OUT)
print("ok", OUT, tot/FPS, "s")
