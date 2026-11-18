import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1200,700
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc";FD="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc";FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
F=lambda p,s:ImageFont.truetype(p,s,index=1)
GOLD=(243,200,107);WHITE=(240,235,255);SOFT=(207,196,236)
bg=Image.new('RGB',(W,H));d=ImageDraw.Draw(bg)
for y in range(H):
    k=y/H;d.line([(0,y),(W,y)],fill=(int(26+(52-26)*k),int(14+(28-14)*k),int(46+(92-46)*k)))
# 은은한 빛
glow=Image.new('L',(W,H),0);ImageDraw.Draw(glow).ellipse((W/2-420,H-560,W/2+420,H+240),fill=90);glow=glow.filter(ImageFilter.GaussianBlur(120))
bg=Image.composite(Image.new('RGB',(W,H),(120,80,170)),bg,glow)
back=Image.open('/home/claude/balhaeng/cards/card-back.webp').convert('RGBA')
cw=150;ch=int(cw*back.height/back.width);back=back.resize((cw,ch),Image.LANCZOS)
m=Image.new('L',back.size,0);ImageDraw.Draw(m).rounded_rectangle((0,0,cw,ch),10,fill=255);back.putalpha(m)
# 그림자용
N=17;R=760;cx,cy=W/2,H+520
for i in range(N):
    a=-46+92*i/(N-1)
    rad=math.radians(a)
    x=cx+R*math.sin(rad);y=cy-R*math.cos(rad)
    sh=Image.new('RGBA',(cw+40,ch+40),(0,0,0,0));ImageDraw.Draw(sh).rounded_rectangle((20,24,cw+20,ch+24),12,fill=(0,0,0,110));sh=sh.filter(ImageFilter.GaussianBlur(8))
    for im,dx,dy in ((sh,-20,-20),(back,0,0)):
        r=im.rotate(-a,resample=Image.BICUBIC,expand=True)
        bg.paste(r,(int(x-r.width/2+dx*0),int(y-r.height/2)),r)
d=ImageDraw.Draw(bg)
# 로고: 카드 뒷면 가운데 문양을 원형으로
src=Image.open('/home/claude/balhaeng/cards/card-back.webp').convert('RGBA');sw,shh=src.size
crop=src.crop((int(sw*0.18),int(shh*0.30),int(sw*0.82),int(shh*0.30)+int(sw*0.64))).resize((92,92),Image.LANCZOS)
cm=Image.new('L',(92,92),0);ImageDraw.Draw(cm).ellipse((0,0,91,91),fill=255);crop.putalpha(cm)
lx=W//2-150;ly=52
bg.paste(crop,(lx,ly),crop);d.ellipse((lx-2,ly-2,lx+94,ly+94),outline=GOLD,width=3)
d.text((lx+112,ly+8),"OR TAROT",font=F(FB,40),fill=GOLD)
d.text((lx+114,ly+56),"오르타로",font=F(FD,26),fill=SOFT)
def ct(y,t,f,c): d.text((W//2,y),t,font=f,fill=c,anchor="ma")
ct(190,"타로 카드 78장 의미 총정리",F(FB,64),WHITE)
ct(282,"메이저 · 마이너 아르카나  정방향 · 역방향",F(FD,30),GOLD)
bg.save('img/hub_cover.jpg',quality=92)
