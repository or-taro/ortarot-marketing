import html,json
C='style="text-align: center;" data-ke-size="size16"'
def P(t): return f'<p {C}>{t}</p>'
SP=P('&nbsp;')
def lines(a): return ''.join(P(html.escape(l))+SP for l in a)
def H(t): return f'<h3 style="text-align: center;" data-ke-size="size23">{html.escape(t)}</h3>'
HR='<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style6" />'
END=P('직접 뽑아 보고 싶다면 오르타로 앱에서 바로 해 볼 수 있습니다.')+SP+P('<a href="https://ororstory.com/{hub}">타로 카드 78장 의미 모아 보기</a>')+SP+'<p style="text-align: center;" data-ke-size="size14"><span style="color: #888888;">타로 운세는 재미와 자기 성찰을 위한 참고용입니다. 중요한 결정은 전문가와 상의해 주세요.</span></p>'
def card_html(c,hub=None):
    o=[f'<blockquote data-ke-style="style2"><b>{html.escape(c["quote"])}</b></blockquote>',SP,lines(c['intro']),'{{IMG1}}',SP]
    secs=c['sections']
    for i,s in enumerate(secs):
        o+= [HR,H(s['heading']),SP,lines(s['lines']),P('<b>'+html.escape(s['bold'])+'</b>'),SP]
        if i==len(secs)-1: o.append('{{IMG2}}');o.append(SP)
    pre=['첫째로,','둘째로,','마지막으로,']
    o.append(HR)
    o+= [P(f'{pre[i]} <b>{html.escape(t)}</b>')+SP for i,t in enumerate(c['tips'][:3])]
    o.append(lines(c['closing']))
    end=END if hub else END.replace(P('<a href="https://ororstory.com/{hub}">타로 카드 78장 의미 모아 보기</a>')+SP,'')
    o.append(end.replace('{hub}',str(hub)) if hub else end)
    return ''.join(o)

def pick_html(c,hub=None):
    import datetime
    o=[f'<blockquote data-ke-style="style2"><b>{html.escape(c["quote"])}</b></blockquote>',SP,lines(c['intro']),'{{IMG1}}',SP,
       P('골랐다면, 천천히 아래로 내려가 주세요.'),SP*10,P('· · ·'),SP*10,
       '<blockquote data-ke-style="style1">78장 카드를 섞어 무작위로 세 장을 뽑았습니다. 정방향과 역방향도 무작위입니다.</blockquote>',SP]
    for i,p in enumerate(c['picks']):
        o+=[HR,H(f'{i+1}번을 고른 당신. {p["title"]}.'),SP,'{{IMG%d}}'%(i+2),SP,lines(p['lines']),P('<b>'+html.escape(p['bold'])+'</b>'),SP]
    pre=['첫째로,','둘째로,','마지막으로,'];o.append(HR)
    o+=[P(f'{pre[i]} <b>{html.escape(t)}</b>')+SP for i,t in enumerate(c['tips'][:3])]
    o.append(lines(c['closing']))
    o.append(END.replace(P('<a href="https://ororstory.com/{hub}">타로 카드 78장 의미 모아 보기</a>')+SP,''))
    return ''.join(o)
