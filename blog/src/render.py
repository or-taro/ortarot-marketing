import asyncio,base64,json,sys,importlib.util
from playwright.async_api import async_playwright
SRC='/home/claude/balhaeng/index.html'
s=open(SRC,encoding='utf-8').read().replace('const toBlob=c=>','window.__T={bPair,bTable,bBacks,bPick,cardName};const toBlob=c=>',1)
open('/home/claude/balhaeng/_render.html','w',encoding='utf-8').write(s)
async def main(jobs):
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto('http://127.0.0.1:8811/_render.html');await pg.wait_for_timeout(1200)
    for out,fn,args in jobs:
      u=await pg.evaluate(f"async a=>(await __T.{fn}(...a)).toDataURL('image/jpeg',0.9)",args)
      open(out,'wb').write(base64.b64decode(u.split(',')[1]))
    print('rendered',len(jobs),'errors',errs[:2]);await b.close()
if __name__=='__main__':
  jobs=json.load(open(sys.argv[1]));asyncio.run(main(jobs))
