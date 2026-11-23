# 노출 부위를 불투명 문양 패널로 가린 카드 그림 (2026-11-23 주인님 결정)
import math
from PIL import Image, ImageDraw, ImageFilter
SRC='/home/claude/ortarot-app/mobile/www/assets/cards/'
R={15:[(80,820,295,1235),(655,820,875,1235)],17:[(375,690,660,860)]}
GOLD=(214,175,96); NAVY=(28,30,66)
def star(d,cx,cy,r,fill):
    pts=[]
    for k in range(16):
        a=math.pi/8*k-math.pi/2; rr=r if k%2==0 else r*0.38
        pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
    d.polygon(pts,fill=fill)
for i,boxes in R.items():
    im=Image.open(f'{SRC}{i:02d}.webp').convert('RGB')
    sh=Image.new('L',im.size,0); ds=ImageDraw.Draw(sh)
    for b in boxes: ds.rounded_rectangle((b[0]+8,b[1]+10,b[2]+8,b[3]+10),40,fill=140)
    im.paste((0,0,0),(0,0),sh.filter(ImageFilter.GaussianBlur(12)))
    d=ImageDraw.Draw(im)
    for x0,y0,x1,y1 in boxes:
        d.rounded_rectangle((x0,y0,x1,y1),40,fill=NAVY,outline=GOLD,width=7)
        d.rounded_rectangle((x0+16,y0+16,x1-16,y1-16),28,outline=GOLD+(0,),width=2)
        cx,cy=(x0+x1)/2,(y0+y1)/2; star(d,cx,cy,min(x1-x0,y1-y0)*0.28,GOLD)
        for dx,dy in ((-0.3,-0.3),(0.3,0.3),(0.3,-0.3),(-0.3,0.3)):
            star(d,cx+dx*(x1-x0),cy+dy*(y1-y0),9,GOLD)
    im.save(f'covered/{i:02d}.png')
print('ok')
