import subprocess, math, json, sys
from PIL import Image, ImageDraw, ImageFont
S=json.load(open(sys.argv[1],encoding="utf-8")); OUT=sys.argv[2]
JA=S["lang"]=="ja"
W,H,FPS=1080,1920,30
BG=(30,18,52); BG2=(58,32,100); GOLD=(243,200,107); WHITE=(240,235,255); DIM=(190,180,220)
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FD="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
F=lambda p,s: ImageFont.truetype(p,s,index=0 if JA else 1)
CARDS=S.get("cards_dir","/home/claude/ortarot-app/mobile/www/assets/cards/")
NO=(lambda n:f"{n}番") if JA else (lambda n:f"{n}번")
HEAD=(lambda n:f"{n}番を選んだあなた") if JA else (lambda n:f"{n}번을 고른 당신")
DIR=(lambda r:"逆位置" if r else "正位置") if JA else (lambda r:"역방향" if r else "정방향")
SEP="・" if JA else " · "
def bg():
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        k=y/H; d.line([(0,y),(W,y)],fill=tuple(int(BG[i]*(1-k)+BG2[i]*k) for i in range(3)))
    return im
BASE=bg()
def card(n,w): return Image.open(CARDS+n).convert("RGB").resize((w,int(w*1.5)),Image.LANCZOS)
BACK={w:card("card-back.webp",w) for w in (280,520)}
FRONT={p["id"]:(card(f'{p["id"]:02d}.webp',520).rotate(180) if p["rev"] else card(f'{p["id"]:02d}.webp',520)) for p in S["picks"]}
def ctext(d,y,txt,font,fill,a=255,sp=12):
    for line in txt.split("\n"):
        d.text((W//2,y),line,font=font,fill=fill+(a,),anchor="ma"); bb=d.textbbox((0,0),line,font=font); y+=bb[3]-bb[1]+sp+font.size//3
    return y
def paste(im,c,cx,cy,sx=1.0,alpha=1.0):
    w=max(2,int(c.width*sx)); c2=c.resize((w,c.height))
    m=Image.new("L",c2.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,w,c2.height),16,fill=int(255*alpha))
    im.paste(c2,(cx-w//2,cy-c2.height//2),m)
def fb(): return BASE.copy(), Image.new("RGBA",(W,H),(0,0,0,0))
def fin(im,o):
    ImageDraw.Draw(o).text((W//2,150),S["handle"],font=F(FD,32),fill=DIM+(255,),anchor="ma"); im.paste(o,(0,0),o); return im
ease=lambda t: 0.5-0.5*math.cos(math.pi*max(0,min(1,t)))
def s1(f,n):
    t=f/n; im,o=fb(); d=ImageDraw.Draw(o); a=int(255*ease(t*3))
    ctext(d,300,"PICK A CARD",F(FD,44),GOLD,a); ctext(d,380,S["title"],F(FB,96),WHITE,a,8)
    for i,x in enumerate([230,540,850]):
        al=ease(t*3-0.6-i*0.25)
        if al>0: paste(im,BACK[280],x,1060+int(40*(1-al)),1,al); d.text((x,1300),NO(i+1),font=F(FB,60),fill=GOLD+(int(255*al),),anchor="ma")
    return fin(im,o)
def s2(f,n):
    im,o=fb(); d=ImageDraw.Draw(o); ctext(d,300,S["countdown"],F(FB,64),WHITE)
    for i,x in enumerate([230,540,850]): paste(im,BACK[280],x,1060); d.text((x,1300),NO(i+1),font=F(FB,60),fill=GOLD+(255,),anchor="ma")
    k=f//FPS; t=(f%FPS)/FPS
    d.text((W//2,560),str(3-k),font=F(FB,int(200-60*t)),fill=GOLD+(int(255*(1-t*0.7)),),anchor="ma"); return fin(im,o)
def mk(i):
    p=S["picks"][i]
    def s(f,N):
        im,o=fb(); d=ImageDraw.Draw(o); ctext(d,250,HEAD(i+1),F(FB,70),GOLD); ft=f/(0.6*FPS)
        if ft<0.5: paste(im,BACK[520],W//2,830,1-ease(ft*2))
        else: paste(im,FRONT[p["id"]],W//2,830,ease(min(1,(ft-0.5)*2)))
        if ft>=1:
            a=int(255*ease((f-0.6*FPS)/(0.5*FPS)))
            y=ctext(d,1250,p["name"]+SEP+DIR(p["rev"]),F(FD,42),DIM,a); y=ctext(d,y+6,p["title"],F(FB,76),WHITE,a); ctext(d,y+10,p["line"],F(FD,48),GOLD,a,6)
        return fin(im,o)
    return s
def se(f,n):
    t=f/n; im,o=fb(); d=ImageDraw.Draw(o); a=int(255*ease(t*3))
    y=ctext(d,520,S["end_title"],F(FB,76),WHITE,a); y=ctext(d,y+60,S["end_gold"],F(FD,50),GOLD,a,8); ctext(d,y+80,S["end_dim"],F(FR,36),DIM,a,6); return fin(im,o)
scenes=[(3.6,s1),(3.0,s2)]+[(5.6,mk(i)) for i in range(3)]+[(4.4,se)]  # 2026-11-23 조금 느리게
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
