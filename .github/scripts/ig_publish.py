"""인스타그램 릴스 자동 게시 (공식 Instagram API with Instagram Login, 오르타로 계정 전용).

  python ig_publish.py validate     대기열 형식 검사 (토큰 불필요)
  python ig_publish.py check        두 계정 토큰·게시 한도 확인 (게시 안 함)
  python ig_publish.py next         다음 게시 시각(epoch 초) 출력, 없으면 빈 출력 (토큰 불필요)
  python ig_publish.py due          게시 시각이 지난 릴스를 올린다
  python ig_publish.py insights     올린 릴스별 숫자(조회·도달·좋아요·댓글·공유·저장)
  python ig_publish.py refresh      장기 토큰 갱신 → 새 토큰은 파일로만 남김(출력 안 함)

대기열: instagram/queue/*.json
  {"publish_at": "2026-11-30T07:00:00+09:00",
   "account": "ko" | "ja",
   "video": "instagram/media/파일.mp4",          # 공개 저장소 raw 주소로 Meta가 가져감(9:16, H.264)
   "caption": "캡션(해시태그 포함, 2,200자 이내)",
   "cover": "instagram/media/파일.jpg"}          # 선택
기록: instagram/published.json  {파일이름: {"status": "posted|expired", "id": 미디어ID, "at": 시각}}
토큰은 환경변수 IG_TOKEN_KO / IG_TOKEN_JA 로만 받고 출력하지 않는다.
"""
import datetime as dt, glob, json, os, sys, time, urllib.parse, urllib.request

TOKENS = {"ko": os.environ.get("IG_TOKEN_KO", ""), "ja": os.environ.get("IG_TOKEN_JA", "")}
# 2026-11-23: 새 Meta 앱은 '통합 로그인' 구성 → 시스템 사용자 토큰(EAA…, 만료 없음, graph.facebook.com).
# 예전 방식 인스타 토큰(IG…)이면 graph.instagram.com. 토큰 앞글자로 자동 선택.
IG_USER = {"ko": os.environ.get("IG_USER_KO", "17841466421160514"), "ja": os.environ.get("IG_USER_JA", "17841423713287381")}
VER = os.environ.get("IG_VER", "v23.0")
def host(acc):
    if os.environ.get("IG_BASE"):
        return os.environ["IG_BASE"]
    return "https://graph.facebook.com" if TOKENS[acc].startswith("EAA") else "https://graph.instagram.com"
def api(acc):
    return f"{host(acc)}/{VER}" if VER else host(acc)
BASE = "https://graph.instagram.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "or-taro/ortarot-marketing")
REF = os.environ.get("GITHUB_SHA", "main")
QDIR, STATE = "instagram/queue", "instagram/published.json"
MAX_PER_RUN, LATE_LIMIT_H, MAX_CAP = 2, 24, 2200
KST = dt.timezone(dt.timedelta(hours=9))


def call(acc, method, path, **params):
    tok = TOKENS[acc]
    params["access_token"] = tok
    data = urllib.parse.urlencode(params).encode()
    API = api(acc)
    url = path if path.startswith("http") else f"{API}/{path}"
    req = urllib.request.Request(url + "?" + data.decode()) if method == "GET" else urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        for t in TOKENS.values():
            if t:
                body = body.replace(t, "***")
        raise RuntimeError(f"Instagram API error {e.code} on {url.split('?')[0].replace(API, '')}: {body[:600]}")


def load_queue():
    items, errs = [], []
    for p in sorted(glob.glob(f"{QDIR}/*.json")):
        name = os.path.basename(p)
        try:
            q = json.load(open(p, encoding="utf-8"))
            at = dt.datetime.fromisoformat(q["publish_at"])
            if at.tzinfo is None:
                raise ValueError("publish_at 에 시간대(+09:00)가 없음")
            acc = q.get("account")
            if acc not in TOKENS:
                raise ValueError("account 는 ko 또는 ja")
            vid, cap, cov = q.get("video", ""), q.get("caption", ""), q.get("cover")
            if not (vid.lower().endswith(".mp4") and os.path.isfile(vid)):
                raise ValueError(f"video 파일 없음/형식 오류: {vid}")
            if not cap.strip() or len(cap) > MAX_CAP:
                raise ValueError(f"caption 비었거나 {MAX_CAP}자 초과")
            if cap.count("#") > 5:
                raise ValueError("해시태그 5개 초과")
            if cov and not (cov.lower().endswith((".jpg", ".jpeg")) and os.path.isfile(cov)):
                raise ValueError(f"cover 파일 없음/형식 오류: {cov}")
            items.append({"name": name, "at": at, "acc": acc, "video": vid, "caption": cap, "cover": cov})
        except Exception as e:  # noqa: BLE001
            errs.append(f"{name}: {e}")
    return items, errs


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.isfile(STATE) else {}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def raw(path):
    return f"https://raw.githubusercontent.com/{REPO}/{REF}/{urllib.parse.quote(path)}"


_uid = {}
def uid(acc):
    if acc not in _uid:
        if TOKENS[acc].startswith("EAA") or (os.environ.get("IG_BASE") and os.environ.get("IG_SUAT")):
            me = call(acc, "GET", IG_USER[acc], fields="id,username")
            _uid[acc] = (me.get("id") or IG_USER[acc], me.get("username"))
        else:
            me = call(acc, "GET", "me", fields="user_id,username")
            _uid[acc] = (me.get("user_id") or me.get("id"), me.get("username"))
    return _uid[acc]


def post_reel(it):
    acc, (user, _) = it["acc"], uid(it["acc"])
    p = {"media_type": "REELS", "video_url": raw(it["video"]), "caption": it["caption"], "share_to_feed": "true"}
    if it["cover"]:
        p["cover_url"] = raw(it["cover"])
    cid = call(acc, "POST", f"{user}/media", **p)["id"]
    for _ in range(60):  # 영상 처리 최대 약 10분
        st = call(acc, "GET", cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {st.get('status_code')}: {st.get('status', '')}")
        time.sleep(10)
    else:
        raise RuntimeError("container not ready in 10 min")
    for k in range(3):
        try:
            return call(acc, "POST", f"{user}/media_publish", creation_id=cid)["id"]
        except RuntimeError as e:
            if k == 2:
                raise
            print("publish retry:", str(e)[:200]); time.sleep(20)


def cmd_validate():
    items, errs = load_queue()
    for e in errs:
        print("FAIL", e)
    st = load_state()
    for it in items:
        print(("done " if it["name"] in st else "wait ") + it["at"].astimezone(KST).strftime("%m-%d %H:%M") + f"  {it['acc']}  " + it["name"])
    if errs:
        sys.exit(1)
    print(f"PASS: {len(items)} items")


def cmd_check():
    bad = 0
    for acc, tok in TOKENS.items():
        if not tok:
            print(f"{acc}: token missing"); bad += 1; continue
        try:
            user, name = uid(acc)
            lim = call(acc, "GET", f"{user}/content_publishing_limit", fields="quota_usage,config")
            print(f"PASS {acc}: @{name}  limit {json.dumps(lim.get('data', lim), ensure_ascii=False)}")
        except RuntimeError as e:
            print(f"FAIL {acc}: {str(e)[:300]}"); bad += 1
    if bad:
        sys.exit(1)


def cmd_next():
    items, _ = load_queue()
    st, now = load_state(), dt.datetime.now(dt.timezone.utc)
    ts = [it["at"] for it in items if it["name"] not in st and now - it["at"] <= dt.timedelta(hours=LATE_LIMIT_H)]
    if ts:
        print(int(min(ts).timestamp()))


def cmd_due():
    items, errs = load_queue()
    if errs:
        sys.exit("queue invalid:\n" + "\n".join(errs))
    st, now, n, failed = load_state(), dt.datetime.now(dt.timezone.utc), 0, 0
    for it in sorted(items, key=lambda x: x["at"]):
        if it["name"] in st or it["at"] > now:
            continue
        if now - it["at"] > dt.timedelta(hours=LATE_LIMIT_H):
            st[it["name"]] = {"status": "expired", "at": now.isoformat()}
            print("expired (too late, not posted):", it["name"]); save_state(st); continue
        if n >= MAX_PER_RUN:
            break
        if not TOKENS[it["acc"]]:
            print(f"skip {it['name']}: IG_TOKEN_{it['acc'].upper()} not set"); continue
        try:
            mid = post_reel(it)
        except RuntimeError as e:
            print("FAIL", it["name"], str(e)[:400]); failed += 1; continue
        st[it["name"]] = {"status": "posted", "id": mid, "at": now.isoformat(), "account": it["acc"]}
        save_state(st)
        print("posted:", it["name"], mid)
        n += 1
    save_state(st)
    print(f"done: {n} posted, {failed} failed")
    if failed:
        sys.exit(1)


def cmd_insights():
    st = load_state()
    for name, rec in sorted(st.items()):
        if rec.get("status") != "posted":
            continue
        acc = rec.get("account", "ko")
        try:
            r = call(acc, "GET", f"{rec['id']}/insights", metric="views,reach,likes,comments,shares,saved")
            nums = {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value")) for d in r.get("data", [])}
            print("POST", acc, name, json.dumps(nums))
        except RuntimeError as e:
            print("POST", acc, name, "FAIL", str(e)[:200])
    for acc in TOKENS:
        if TOKENS[acc]:
            try:
                user, nm = uid(acc)
                me = call(acc, "GET", user, fields="followers_count,media_count")
                print(f"ACCOUNT {acc} @{nm}: followers {me.get('followers_count')} media {me.get('media_count')}")
            except RuntimeError as e:
                print(f"ACCOUNT {acc} FAIL", str(e)[:200])


def cmd_refresh():
    outdir = os.environ.get("IG_NEW_TOKEN_DIR", "/tmp/ig_new")
    os.makedirs(outdir, exist_ok=True)
    ok = 0
    for acc, tok in TOKENS.items():
        if not tok:
            continue
        if tok.startswith("EAA"):
            print(f"PASS {acc}: system user token, no refresh needed"); ok += 1; continue
        try:
            r = call(acc, "GET", f"{BASE}/refresh_access_token", grant_type="ig_refresh_token")
        except RuntimeError as e:
            print(f"FAIL {acc}: {str(e)[:200]}"); continue
        if r.get("access_token"):
            open(f"{outdir}/{acc}", "w").write(r["access_token"])
            print(f"PASS {acc}: refreshed, valid {int(r.get('expires_in', 0)) // 86400} days"); ok += 1
    if not ok:
        sys.exit("refresh failed")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    {"validate": cmd_validate, "check": cmd_check, "next": cmd_next, "due": cmd_due,
     "insights": cmd_insights, "refresh": cmd_refresh}[mode]()
