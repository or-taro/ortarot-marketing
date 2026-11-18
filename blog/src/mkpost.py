import json,sys,importlib
sys.path.insert(0,'.')
from build import card_html
HUB=76
RAW='https://raw.githubusercontent.com/or-taro/ortarot-marketing/main/blog/img/'
def card_post(cid,c,at):
    nm=c['title'].split('｜')[0].replace('타로 ','')
    return {"title":c['title'],"tags":c['tags'][:10],"html":card_html(c,HUB),
            "images":[RAW+f"c{cid:02d}_pair.jpg",RAW+f"c{cid:02d}_table.jpg"],
            "alts":[f"{nm} 정방향 역방향",f"{nm} 한눈에 보기"],"at":at,"card":cid}
