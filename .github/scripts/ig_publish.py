"""Instagram 게시 (공식 Graph API, 통합 로그인 시스템 사용자 토큰).

  python ig_publish.py check                 토큰·계정 확인만 (게시 안 함)
  python ig_publish.py publish <post_dir>    <post_dir>/post.json 의 이미지·캡션으로 게시

post.json: {"caption": "...", "images": ["01.jpg", "02.jpg", ...]}  (JPEG, 1~10장)
이미지는 이 공개 저장소의 raw 주소로 Meta가 직접 가져간다.
토큰은 환경변수 IG_TOKEN 으로만 받고 출력하지 않는다.
"""
import json, os, sys, time, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v25.0"
IG_ID = os.environ.get("IG_USER_ID", "17841466421160514")
TOKEN = os.environ.get("IG_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "or-taro/ortarot-marketing")
REF = os.environ.get("GITHUB_SHA", "main")


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace").replace(TOKEN, "***") if TOKEN else ""
        sys.exit(f"Graph API error {e.code} on {path.split('?')[0]}: {body[:600]}")


def wait_ready(cid):
    for _ in range(30):
        st = call("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"container {cid} status {st}")
        time.sleep(5)
    sys.exit(f"container {cid} not ready in time")


def check():
    me = call("GET", IG_ID, fields="username,media_count")
    lim = call("GET", f"{IG_ID}/content_publishing_limit", fields="quota_usage,config")
    print(f"PASS: token works for @{me.get('username')} (posts {me.get('media_count')})")
    print(f"publishing limit: {json.dumps(lim.get('data', lim))}")


def publish(post_dir):
    meta = json.load(open(os.path.join(post_dir, "post.json"), encoding="utf-8"))
    imgs, caption = meta["images"], meta.get("caption", "")
    if not 1 <= len(imgs) <= 10:
        sys.exit("images must be 1..10")
    for f in imgs:
        p = os.path.join(post_dir, f)
        if not (f.lower().endswith((".jpg", ".jpeg")) and os.path.isfile(p)):
            sys.exit(f"missing or non-JPEG image: {p}")
    base = f"https://raw.githubusercontent.com/{REPO}/{REF}/{post_dir.strip('/')}"
    urls = [f"{base}/{urllib.parse.quote(f)}" for f in imgs]
    if len(urls) == 1:
        cid = call("POST", f"{IG_ID}/media", image_url=urls[0], caption=caption)["id"]
    else:
        children = []
        for u in urls:
            c = call("POST", f"{IG_ID}/media", image_url=u, is_carousel_item="true")["id"]
            wait_ready(c)
            children.append(c)
            print(f"item ready: {u.rsplit('/', 1)[-1]}")
        cid = call("POST", f"{IG_ID}/media", media_type="CAROUSEL",
                   children=",".join(children), caption=caption)["id"]
    wait_ready(cid)
    mid = call("POST", f"{IG_ID}/media_publish", creation_id=cid)["id"]
    link = call("GET", mid, fields="permalink").get("permalink")
    print(f"PUBLISHED: {link}")
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        open(out, "a").write(f"Published {post_dir}: {link}\n")


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("IG_TOKEN is empty (secret INSTAGRAM_ACCESS_TOKEN missing)")
    if len(sys.argv) >= 2 and sys.argv[1] == "check":
        check()
    elif len(sys.argv) >= 3 and sys.argv[1] == "publish":
        publish(sys.argv[2])
    else:
        sys.exit(__doc__)
