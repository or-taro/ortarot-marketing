import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/home/claude/w2")
from content import *
T = "/home/claude/ortarot-marketing/reels/tools"
REPO = "/home/claude/ortarot-marketing"
MED = f"{REPO}/instagram/media"; Q = f"{REPO}/instagram/queue"; OUT = "/home/claude/w2/out"
os.makedirs(OUT, exist_ok=True); os.makedirs(MED, exist_ok=True)
cards = json.load(open("/home/claude/w2/cards.json"))
NAMES=["바보","마법사","여사제","여황제","황제","교황","연인","전차","힘","은둔자","운명의 수레바퀴","정의","매달린 사람","죽음","절제","악마","탑","별","달","태양","심판","세계"]
S=["완드","컵","소드","펜타클"];R=["에이스","2","3","4","5","6","7","8","9","10","페이지","기사","여왕","왕"]
JA=["愚者","魔術師","女教皇","女帝","皇帝","教皇","恋人","戦車","力","隠者","運命の輪","正義","吊るされた男","死神","節制","悪魔","塔","星","月","太陽","審判","世界"]
JS=["ワンド","カップ","ソード","ペンタクル"];JR=["エース","2","3","4","5","6","7","8","9","10","ペイジ","ナイト","クイーン","キング"]
ko=lambda i:NAMES[i] if i<22 else f"{S[(i-22)//14]} {R[(i-22)%14]}"
ja=lambda i:JA[i] if i<22 else f"{JS[(i-22)//14]}の{JR[(i-22)%14]}"
WD = {"1124":"화","1125":"수","1126":"목","1127":"금","1128":"토","1129":"일","1130":"월","1201":"화","1202":"수","1203":"목","1204":"금","1205":"토","1206":"일","1207":"월"}
jobs = []  # (script, spec, out_mp4, dur)
queue = []  # (date, acc, file, caption)
seed = [0]
def add(script, spec, name, dur, date, acc, cap):
    seed[0] += 1
    spec["music"] = f"{OUT}/{name}.wav"; jobs.append((script, spec, f"{MED}/{name}.mp4", dur, seed[0]))
    if acc: queue.append((date, acc, name, cap))
for d, P in PICKS.items():
    day = d[:4]; c = cards["picks"][d]
    for lang in ("ko", "ja"):
        J = lang == "ja"
        picks = [{"id": cid, "rev": rv, "name": (ja if J else ko)(cid), "title": P["picks"][i][2 if J else 0], "line": P["picks"][i][3 if J else 1]} for i, (cid, rv) in enumerate(c)]
        if P["kind"] == "week":
            cd = (P["label_ja"] + "\n止めて直感で1枚選んで") if J else (P["label_ko"] + "\n멈추고 한 장을 골라 보세요")
        else:
            cd = "止めて直感で\n1枚選んでください" if J else "멈추고 직감으로\n한 장을 골라 보세요"
        spec = {"lang": lang, "handle": "@or._tarot.jp" if J else "@or._tarot", "title": P["ja_title" if J else "ko_title"], "countdown": cd,
                "picks": picks, "end_title": P["ja_end" if J else "ko_end"], "end_gold": END_JA if J else END_KO, "end_dim": DIM_JA if J else DIM_KO}
        cap = P["ja_cap" if J else "ko_cap"] + "\n\n" + P["ja_tags" if J else "ko_tags"]
        add("reel.py", spec, f"2026{day}_{lang}_{P['kind']}", 29, day, lang, cap)
for d, X in TODAY.items():
    cid, rv = cards["today"][d]
    spec = {"lang": "ko", "handle": "@or._tarot", "id": cid, "rev": rv, "date": X["date_ko"], "hook": "오늘 당신에게 온 카드", "name": ko(cid),
            "dir": "역방향" if rv else "정방향", "title": X["title"], "line": X["line"], "end": END_KO, "dim": DIM_KO}
    add("today_reel.py", spec, f"2026{d}_ko_today", 19, d, "ko", TODAY_CAP_KO + "\n\n" + TODAY_TAGS_KO)
    if "ja_title" in X:
        spec = {"lang": "ja", "handle": "@or._tarot.jp", "id": cid, "rev": rv, "date": X["date_ja"], "hook": "今日あなたに届いたカード", "name": ja(cid),
                "dir": "逆位置" if rv else "正位置", "title": X["ja_title"], "line": X["ja_line"], "end": END_JA, "dim": DIM_JA}
        add("today_reel.py", spec, f"2026{d}_ja_today", 19, d, "ja", TODAY_CAP_JA + "\n\n" + TODAY_TAGS_JA)
for d, M in MEANING.items():
    spec = {"lang": "ja", "id": M["id"], "name": M["name"], "hook": "このカード、\n意味知ってる？", "up": M["up"], "rev": M["rev"], "love_label": "恋愛では",
            "love": M["love"], "save": "迷った日のために\n保存しておいてね", "dim": DIM_JA, "handle": "@or._tarot.jp"}
    add("meaning_reel.py", spec, f"2026{d}_ja_meaning", 19, d, "ja", MEANING_CAP[d] + "\n\n" + CAP_END_JA + "\n\n" + MEANING_TAGS[d])
def run(j):
    script, spec, out, dur, sd = j
    if os.path.exists(out) and "--force" not in sys.argv: return out + " (skip)"
    subprocess.run(["python3", f"{T}/bgm.py", spec["music"], str(dur), str(sd)], check=True, capture_output=True)
    sp = out.replace(".mp4", ".json").replace(MED, OUT); json.dump(spec, open(sp, "w"), ensure_ascii=False)
    r = subprocess.run(["python3", f"{T}/{script}", sp, out], capture_output=True, text=True)
    return out + " " + (r.stdout.strip() or r.stderr[-300:])
if "--queue" in sys.argv:
    for day, acc, name, cap in queue:
        q = {"publish_at": f"2026-{day[:2]}-{day[2:]}T07:00:00+09:00", "account": acc, "video": f"instagram/media/{name}.mp4", "caption": cap}
        json.dump(q, open(f"{Q}/2026-{day[:2]}-{day[2:]}_0700_{acc}_{name.split('_')[-1]}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(queue), "queued")
else:
    print(len(jobs), "jobs")
    with ThreadPoolExecutor(2) as ex:
        for r in ex.map(run, jobs): print(r, flush=True)
