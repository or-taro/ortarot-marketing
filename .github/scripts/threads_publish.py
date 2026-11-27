"""Threads 자동 게시 (공식 Threads API, 오르타로 계정 전용).

  python threads_publish.py validate         대기열 파일 형식 검사 (토큰 불필요)
  python threads_publish.py check            토큰·계정·게시 한도 확인 (게시 안 함)
  python threads_publish.py due              게시 시각이 지난 대기열 글을 올린다
  python threads_publish.py next             다음 게시·답 공개 시각(epoch 초, 없으면 빈 줄). 워크플로 대기용
  python threads_publish.py insights         올린 글별 조회·좋아요·댓글 수와 팔로워 수(숫자만)
  python threads_publish.py refresh          장기 토큰 갱신 → 새 토큰을 파일로만 남김(출력 안 함)

대기열: threads/queue/*.json
  {"publish_at": "2026-11-19T12:00:00+09:00",
   "text": "본글 (500자 이내)",
   "replies": ["이어 쓰는 답글 1", "..."],      # 선택, 최대 5개, 각 500자 이내
   "image": "threads/img/파일.jpg",            # 선택, 공개 저장소 raw 주소로 Meta가 가져감
   "reveal_after_h": 6}                        # 선택: 답글을 본글 N시간 뒤에 올린다(픽어카드 답 미리 보임 방지)
기록: threads/published.json  {파일이름: {"id": 게시물ID, "at": 시각, "status": "posted|expired"}}
토큰은 환경변수 TH_TOKEN 으로만 받고 출력하지 않는다.
"""
import datetime as dt, glob, json, os, sys, time, urllib.parse, urllib.request

BASE = os.environ.get("TH_BASE", "https://graph.threads.net")  # 시험용으로만 바꿈
API = f"{BASE}/v1.0"
TOKEN = os.environ.get("TH_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "or-taro/ortarot-marketing")
REF = os.environ.get("GITHUB_SHA", "main")
QDIR, STATE = "threads/queue", "threads/published.json"
MAX_PER_RUN, LATE_LIMIT_H, MAX_LEN, MAX_REPLIES = 2, 24, 500, 5
KST = dt.timezone(dt.timedelta(hours=9))


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = path if path.startswith("http") else f"{API}/{path}"
    req = urllib.request.Request(url + "?" + data.decode()) if method == "GET" else urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if TOKEN:
            body = body.replace(TOKEN, "***")
        sys.exit(f"Threads API error {e.code} on {url.split('?')[0].replace(API, '')}: {body[:600]}")


def load_queue():
    items, errs = [], []
    for p in sorted(glob.glob(f"{QDIR}/*.json")):
        name = os.path.basename(p)
        try:
            q = json.load(open(p, encoding="utf-8"))
            at = dt.datetime.fromisoformat(q["publish_at"])
            if at.tzinfo is None:
                raise ValueError("publish_at 에 시간대(+09:00)가 없음")
            text, reps = q["text"], q.get("replies", [])
            if not text.strip():
                raise ValueError("text 비어 있음")
            if len(text) > MAX_LEN:
                raise ValueError(f"text {len(text)}자 > {MAX_LEN}")
            if not isinstance(reps, list) or len(reps) > MAX_REPLIES:
                raise ValueError(f"replies 는 {MAX_REPLIES}개 이하 목록")
            for i, r in enumerate(reps):
                if not r.strip() or len(r) > MAX_LEN:
                    raise ValueError(f"replies[{i}] 비었거나 {MAX_LEN}자 초과")
            img = q.get("image")
            if img and not (img.lower().endswith((".jpg", ".jpeg", ".png")) and os.path.isfile(img)):
                raise ValueError(f"image 파일 없음/형식 오류: {img}")
            rv = float(q.get("reveal_after_h", 0))
            if not 0 <= rv <= 24:
                raise ValueError("reveal_after_h 는 0~24")
            items.append({"name": name, "at": at, "text": text, "replies": reps, "image": img, "reveal": rv})
        except Exception as e:  # noqa: BLE001
            errs.append(f"{name}: {e}")
    return items, errs


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.isfile(STATE) else {}


def wait_ready(cid):
    for _ in range(36):
        st = call("GET", cid, fields="status,error_message")
        if st.get("status") == "FINISHED":
            return
        if st.get("status") in ("ERROR", "EXPIRED"):
            sys.exit(f"container {cid} status {st.get('status')}: {st.get('error_message', '')}")
        time.sleep(5)
    sys.exit(f"container {cid} not ready in time")


def post_one(text, reply_to=None, image=None):
    p = {"text": text}
    if image:
        p.update(media_type="IMAGE", image_url=f"https://raw.githubusercontent.com/{REPO}/{REF}/{image}")
    else:
        p["media_type"] = "TEXT"
    if reply_to:
        p["reply_to_id"] = reply_to
    cid = call("POST", "me/threads", **p)["id"]
    wait_ready(cid)
    # 2026-11-21 run 44938194801: FINISHED 직후 publish 가 "Media Not Found"(code 24) 로 한 번 실패 → 잠시 뒤 다시 시도
    for i in range(3):
        try:
            return call("POST", "me/threads_publish", creation_id=cid)["id"]
        except SystemExit as e:
            if i == 2 or "4279009" not in str(e):
                raise
            print("publish retry", i + 1, "(media not found yet)")
            time.sleep(15)


def cmd_validate():
    items, errs = load_queue()
    for e in errs:
        print("FAIL", e)
    st = load_state()
    for it in items:
        print(("done " if it["name"] in st else "wait ") + it["at"].astimezone(KST).strftime("%m-%d %H:%M") + "  " + it["name"])
    if errs:
        sys.exit(1)
    print(f"PASS: {len(items)} items")


def cmd_check():
    me = call("GET", "me", fields="id,username")
    lim = call("GET", "me/threads_publishing_limit", fields="quota_usage,config")
    print(f"PASS: token works for @{me.get('username')}")
    print("publishing limit:", json.dumps(lim.get("data", lim), ensure_ascii=False))
    # 답글(이어 쓰기) 권한 확인: threads_manage_replies 가 없으면 여기서 오류
    real = call
    def soft(*a, **k):
        try:
            return real(*a, **k)
        except SystemExit as e:
            return {"error": str(e)}
    r = soft("GET", "me/threads_publishing_limit", fields="reply_quota_usage,reply_config")
    print("REPLY permission:", "PASS" if "error" not in r else "FAIL " + r["error"][:300])
    # 댓글 읽기 권한(threads_read_replies) 확인: 최근 게시물의 댓글 수만 센다(내용·아이디는 출력 안 함)
    st = load_state()
    posted = [v for k, v in sorted(st.items()) if v.get("status") == "posted" and v.get("id")]
    if posted:
        rr = soft("GET", f"{posted[-1]['id']}/replies", fields="id")
        print("READ_REPLIES permission:", "PASS (%d replies on latest post)" % len(rr.get("data", [])) if "error" not in rr else "FAIL " + rr["error"][:300])


def cmd_due():
    items, errs = load_queue()
    if errs:
        sys.exit("queue invalid:\n" + "\n".join(errs))
    st, now, n = load_state(), dt.datetime.now(dt.timezone.utc), 0
    save = lambda: json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 1) 이미 올린 본글 중 답 공개 시각이 지난 것: 남은 답글을 이어 붙인다
    for it in sorted(items, key=lambda x: x["at"]):
        rec = st.get(it["name"])
        if not rec or rec.get("status") != "posted" or rec.get("replies_done", len(it["replies"])) >= len(it["replies"]):
            continue
        if it["at"] + dt.timedelta(hours=it["reveal"]) > now:
            continue
        prev = rec.get("last_id", rec["id"])
        for r in it["replies"][rec.get("replies_done", 0):]:
            time.sleep(3)
            prev = post_one(r, reply_to=prev)
            rec["replies_done"] = rec.get("replies_done", 0) + 1
            rec["last_id"] = prev
            save()
        print("revealed:", it["name"])
    # 2) 새 본글
    for it in sorted(items, key=lambda x: x["at"]):
        if it["name"] in st or it["at"] > now:
            continue
        if now - it["at"] > dt.timedelta(hours=LATE_LIMIT_H):
            st[it["name"]] = {"status": "expired", "at": now.isoformat()}
            print("expired (too late, not posted):", it["name"])
            continue
        if n >= MAX_PER_RUN:
            break
        root = post_one(it["text"], image=it["image"])
        rec = st[it["name"]] = {"status": "posted", "id": root, "at": now.isoformat(), "replies": len(it["replies"]), "replies_done": 0, "last_id": root}
        save()
        if it["reveal"] == 0:
            prev = root
            for r in it["replies"]:
                time.sleep(3)
                prev = post_one(r, reply_to=prev)
                rec["replies_done"] += 1
                rec["last_id"] = prev
                save()
        print("posted:", it["name"], root, f"(answers +{it['reveal']}h)" if it["reveal"] else "")
        n += 1
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"done: {n} posted")


def cmd_next():
    """다음에 할 일(본글 게시 또는 답 공개)의 시각을 epoch 초로 출력. 없으면 아무것도 출력하지 않음. 토큰 불필요."""
    items, _ = load_queue()
    st, now, ts = load_state(), dt.datetime.now(dt.timezone.utc), []
    for it in items:
        rec = st.get(it["name"])
        if not rec:
            if now - it["at"] <= dt.timedelta(hours=LATE_LIMIT_H):
                ts.append(it["at"])
        elif rec.get("status") == "posted" and rec.get("replies_done", len(it["replies"])) < len(it["replies"]):
            ts.append(it["at"] + dt.timedelta(hours=it["reveal"]))
    if ts:
        print(int(min(ts).timestamp()))


def cmd_insights():
    """올린 글별 숫자(조회·좋아요·댓글·리포스트·인용·공유)와 계정 팔로워 수. 숫자만 출력, 남의 정보는 다루지 않음."""
    soft = lambda *a, **k: (lambda: call(*a, **k))
    try:
        acc = call("GET", "me/threads_insights", metric="followers_count")
        for d in acc.get("data", []):
            v = d.get("total_value", {}).get("value", (d.get("values") or [{}])[-1].get("value"))
            print(f"ACCOUNT {d.get('name')}: {v}")
    except SystemExit as e:
        print("ACCOUNT insights FAIL", str(e)[:200])
    st = load_state()
    for name, rec in sorted(st.items()):
        if rec.get("status") != "posted":
            continue
        try:
            r = call("GET", f"{rec['id']}/insights", metric="views,likes,replies,reposts,quotes,shares")
            nums = {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value")) for d in r.get("data", [])}
            print("POST", name, json.dumps(nums))
        except SystemExit as e:
            print("POST", name, "FAIL", str(e)[:200])


def cmd_refresh():
    r = call("GET", f"{BASE}/refresh_access_token", grant_type="th_refresh_token")
    tok = r.get("access_token", "")
    if not tok:
        sys.exit("refresh failed")
    with open(os.environ.get("TH_NEW_TOKEN_FILE", "/tmp/th_new_token"), "w") as f:
        f.write(tok)
    print(f"PASS: refreshed, valid {int(r.get('expires_in', 0)) // 86400} days")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if mode not in ("validate", "next") and not TOKEN:
        sys.exit("TH_TOKEN missing")
    {"validate": cmd_validate, "check": cmd_check, "due": cmd_due, "next": cmd_next, "refresh": cmd_refresh, "insights": cmd_insights}[mode]()
