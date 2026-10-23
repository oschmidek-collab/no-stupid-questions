"""Publish a carousel post to Instagram (Instagram API with Instagram Login).

Two steps, so the images are public before Instagram tries to fetch them:

  python engine/publish_ig.py prepare <post_id>   # render, convert to JPEG under media/<id>/ (commit + push after)
  python engine/publish_ig.py publish <post_id>   # wait for the public URLs, create containers, publish, record it

  python engine/publish_ig.py next                # print the id of the next post due (status ready/scheduled, date <= today)

Env: IG_ACCESS_TOKEN (secret), MEDIA_BASE_URL (e.g. https://<worker>.workers.dev/media)
"""
import datetime as dt, json, os, pathlib, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://graph.instagram.com/v24.0"
AI_LINE = "\n\nנכתב ועוצב על ידי AI, כחלק מניסוי."


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(path, obj):
    (ROOT / path).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def call(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    req = urllib.request.Request(url + ("?" + data.decode() if method == "GET" else ""), data=None if method == "GET" else data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        # never echo the token
        raise SystemExit(f"Instagram API error on {method} {path}: {e.code} {body}")


def next_due():
    today = dt.date.today().isoformat()
    for item in sorted(load("data/queue.json"), key=lambda x: x["date"]):
        if item.get("platform") == "ig" and item["status"] in ("ready", "scheduled") and item["date"] <= today \
                and (ROOT / "content" / "posts" / f"{item['id']}.json").exists():
            return item["id"]
    return ""


def prepare(post_id):
    sys.path.insert(0, str(ROOT / "engine"))
    import render
    from PIL import Image
    files = render.render(ROOT / "content" / "posts" / f"{post_id}.json", ROOT / "out")
    if not 2 <= len(files) <= 10:
        raise SystemExit(f"A carousel needs 2–10 slides, got {len(files)}")
    dest = ROOT / "media" / post_id
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        Image.open(f).convert("RGB").save(dest / (f.stem + ".jpg"), "JPEG", quality=92, optimize=True)
    print(f"{len(files)} slides ready in media/{post_id}/")


def wait_public(urls, minutes=10):
    deadline = time.time() + minutes * 60
    for u in urls:
        while True:
            try:
                with urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=20) as r:
                    if r.status == 200 and r.headers.get("Content-Type", "").startswith("image/jpeg"):
                        break
            except Exception:
                pass
            if time.time() > deadline:
                raise SystemExit(f"Image is not public yet: {u}\nCheck the Cloudflare Access bypass for /media/*.")
            time.sleep(15)


def publish(post_id):
    post = load(f"content/posts/{post_id}.json")
    base = os.environ["MEDIA_BASE_URL"].rstrip("/")
    slides = sorted((ROOT / "media" / post_id).glob("*.jpg"))
    urls = [f"{base}/{post_id}/{f.name}" for f in slides]
    wait_public(urls)

    me = call("GET", "me", fields="user_id,username")
    ig = me["user_id"]
    children = [call("POST", f"{ig}/media", image_url=u, is_carousel_item="true")["id"] for u in urls]
    caption = post["caption"] + AI_LINE
    carousel = call("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    for _ in range(10):                       # Meta: check about once a minute, up to ~5–10 minutes
        status = call("GET", carousel, fields="status_code").get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise SystemExit(f"Instagram could not process the carousel: {status}")
        time.sleep(30)
    media_id = call("POST", f"{ig}/media_publish", creation_id=carousel)["id"]
    permalink = call("GET", media_id, fields="permalink").get("permalink", "")

    queue = load("data/queue.json")
    for item in queue:
        if item["id"] == post_id:
            item.update(status="posted", permalink=permalink, posted_at=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", ig_media_id=media_id)
    save("data/queue.json", queue)
    print(f"Published @{me.get('username')}: {permalink}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "next":
        print(next_due())
    elif cmd == "prepare":
        prepare(sys.argv[2])
    elif cmd == "publish":
        publish(sys.argv[2])
    else:
        raise SystemExit(__doc__)
