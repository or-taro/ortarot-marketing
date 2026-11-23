import subprocess, math, json, sys
from PIL import Image, ImageDraw, ImageFont
S=json.load(open(sys.argv[1],encoding="utf-8")); OUT=sys.argv[2]; JA=S["lang"]=="ja"
W,H,FPS=1080,1920,30
BG=(30,18,52); BG2=(58,32,100); GOLD=(243,200,107); WHITE=(240,235,255); DIM=(190,180,220)
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FD="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
F=lambda p,s: ImageFont.truetype(p,s,index=0 if JA else 1)
CARDS=S.get("cards_dir","/home/claude/ortarot-app/mobile/www/assets/cards/")
UP,RV=("正位置","逆位置") if JA else ("정방향","역방향")
def bg():
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        k=y/H; d.line([(0,y),(W,y)],fill=tuple(int(BG[i]*(1-k)+BG2[i]*k) for i in range(3)))
    return im
BASE=bg()
def load(n,w): return Image.open(CARDS+n).convert("RGBA").resize((w,int(w*1.5)),Image.LANCZOS)
def rounded(c,r=18):
    m=Image.new("L",c.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,c.width,c.height),r,fill=255); c=c.copy(); c.putalpha(m); return c
BACK=rounded(load("card-back.webp",440)); FRONT=rounded(load(f'{S["id"]:02d}.webp',440))
CX,CY=W//2,800
ease=lambda t: 0.5-0.5*math.cos(math.pi*max(0,min(1,t)))
def ctext(d,y,txt,font,fill,a=255,sp=12):
    for line in txt.split("\n"):
        d.text((W//2,y),line,font=font,fill=fill+(a,),anchor="ma"); bb=d.textbbox((0,0),line,font=font); y+=bb[3]-bb[1]+sp+font.size//3
    return y
def put(im,c,sx=1.0,ang=0.0):
    w=max(2,int(c.width*sx)); c2=c.resize((w,c.height))
    if ang: c2=c2.rotate(ang,resample=Image.BICUBIC,expand=True)
    im.paste(c2,(CX-c2.width//2,CY-c2.height//2),c2)
def frame(): return BASE.copy(), Image.new("RGBA",(W,H),(0,0,0,0))
def fin(im,o):
    ImageDraw.Draw(o).text((W//2,150),S["handle"],font=F(FD,32),fill=DIM+(255,),anchor="ma"); im.paste(o,(0,0),o); return im
def kw_block(d,label,kws,t,y0=1165):
    a=int(255*ease(t*4)); d.text((W//2,y0),label,font=F(FB,64),fill=GOLD+(a,),anchor="ma")
    for i,k in enumerate(kws):
        ak=int(255*ease(t*4-1-i*0.7)); d.text((W//2,y0+105+i*80),k,font=F(FB,58),fill=WHITE+(ak,),anchor="ma")
def s_hook(f,n):
    t=f/n; im,o=frame(); d=ImageDraw.Draw(o); a=int(255*ease(t*3))
    ctext(d,215,S["hook"],F(FB,72),WHITE,a,4); put(im,BACK); return fin(im,o)
def s_flip(f,n):
    t=f/n; im,o=frame(); d=ImageDraw.Draw(o); ctext(d,270,S["name"],F(FB,84),GOLD)
    if t<0.5: put(im,BACK,1-ease(t*2))
    else: put(im,FRONT,ease((t-0.5)*2))
    return fin(im,o)
def s_up(f,n):
    im,o=frame(); d=ImageDraw.Draw(o); ctext(d,270,S["name"],F(FB,84),GOLD); put(im,FRONT); kw_block(d,UP,S["up"],f/n); return fin(im,o)
def s_rot(f,n):
    t=ease(f/n); im,o=frame(); d=ImageDraw.Draw(o); ctext(d,270,S["name"],F(FB,84),GOLD); put(im,FRONT,1,180*t); return fin(im,o)
def s_rv(f,n):
    im,o=frame(); d=ImageDraw.Draw(o); ctext(d,270,S["name"],F(FB,84),GOLD); put(im,FRONT,1,180); kw_block(d,RV,S["rev"],f/n); return fin(im,o)
def s_end(f,n):
    t=f/n; im,o=frame(); d=ImageDraw.Draw(o); a=int(255*ease(t*3))
    y=ctext(d,420,S["love_label"],F(FD,48),GOLD,a); y=ctext(d,y+10,S["love"],F(FB,68),WHITE,a,8)
    y=ctext(d,y+90,S["save"],F(FD,46),GOLD,a,6); ctext(d,y+70,S["dim"],F(FR,34),DIM,a,6); return fin(im,o)
scenes=[(3.0,s_hook),(1.2,s_flip),(4.2,s_up),(1.2,s_rot),(4.2,s_rv),(4.4,s_end)]  # 2026-11-23 조금 느리게
TMP=OUT+".v.mp4"
p=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
  "-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p",TMP],stdin=subprocess.PIPE)
tot = 0; XF = int(0.6*FPS); prev = None; _ease = lambda t: 0.5-0.5*math.cos(math.pi*max(0,min(1,t)))
for sec,fn in scenes:
    n=int(sec*FPS)
    for f in range(n):
        fr=fn(f,n).convert("RGB")
        if prev is not None and f < XF: fr=Image.blend(prev, fr, _ease((f+1)/XF))
        p.stdin.write(fr.tobytes()); tot+=1
    prev=fr
p.stdin.close(); p.wait()
import os
mus=S.get("music")
if mus and os.path.exists(mus):
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",TMP,"-i",mus,"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",OUT],check=True); os.remove(TMP)
else: os.replace(TMP,OUT)
print("ok",OUT,tot/FPS,"s")
