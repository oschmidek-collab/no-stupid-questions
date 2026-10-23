"""Render a carousel post (JSON) into 1080x1350 PNG slides in the brand style.

Usage:  python engine/render.py content/posts/<id>.json  [out_dir]
Output: out_dir/<id>/01.png, 02.png, ...  plus preview.html (all slides on one page)

Slide layouts (each slide is a dict with "layout"):
  cover   – series, question, subtitle, optional "drawing": "bike"
  stat    – kicker, big number + unit, body, optional "geek" box (the pro layer)
  text    – kicker, heading, body (list of paragraphs), optional "geek" box
  verdict – kicker, stamp word, body
  end     – closing stamp + call to send questions
"""
import html, json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
FONTS = ROOT / "node_modules" / "@fontsource"
HANDLE = "@no.dumb.questions.cycling"


def font_faces():
    faces = []
    for fam, pkg, weights in [("Heebo", "heebo", [800, 900]), ("Assistant", "assistant", [400, 600, 700])]:
        for w in weights:
            faces.append(f"""@font-face{{font-family:"{fam}";font-weight:{w};src:url("{(FONTS/pkg/'files'/f'{pkg}-hebrew-{w}-normal.woff2').as_uri()}") format("woff2");unicode-range:U+0590-05FF,U+200C-2010,U+20AA,U+25CC,U+FB1D-FB4F;}}""")
            faces.append(f"""@font-face{{font-family:"{fam}";font-weight:{w};src:url("{(FONTS/pkg/'files'/f'{pkg}-latin-{w}-normal.woff2').as_uri()}") format("woff2");}}""")
    for w in [400, 500]:
        faces.append(f"""@font-face{{font-family:"Plex";font-weight:{w};src:url("{(FONTS/'ibm-plex-mono'/'files'/f'ibm-plex-mono-latin-{w}-normal.woff2').as_uri()}") format("woff2");}}""")
    return "\n".join(faces)


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#888;font-family:"Assistant",sans-serif;color:#1A1A1A}
.slide{width:1080px;height:1350px;position:relative;overflow:hidden;direction:rtl;margin:0 auto 40px;
  background:#F5F1E8;
  background-image:linear-gradient(rgba(31,78,140,.08) 2px,transparent 2px),linear-gradient(90deg,rgba(31,78,140,.08) 2px,transparent 2px);
  background-size:54px 54px;background-position:-1px -1px;
  padding:96px 92px 150px;display:flex;flex-direction:column}
.top{position:absolute;top:44px;right:92px;left:92px;display:flex;justify-content:space-between;align-items:center;
  font:700 30px "Assistant";color:#1F4E8C}
.top .n{font:400 28px "Plex";color:#5A564E;direction:ltr}
.foot{position:absolute;bottom:52px;right:92px;left:92px;display:flex;justify-content:space-between;align-items:center;
  border-top:3px solid #1A1A1A;padding-top:22px;font:600 28px "Assistant";color:#5A564E}
.foot .h{font:400 26px "Plex";direction:ltr}
.kicker{font:700 34px "Assistant";color:#C2400F;margin-top:70px}
h1{font:900 106px/1.02 "Heebo";letter-spacing:-.01em;margin-top:28px}
h2{font:800 76px/1.08 "Heebo";margin-top:22px}
p{font:400 44px/1.42 "Assistant";margin-top:34px;max-width:880px}
p b{font-weight:700}
.sub{font:600 46px/1.35 "Assistant";color:#5A564E;margin-top:40px;max-width:820px}
.big{display:flex;align-items:baseline;gap:26px;margin-top:54px;direction:rtl}
.big .num{font:900 260px/0.9 "Heebo";color:#FF5A1F;letter-spacing:-.03em}
.big .unit{font:800 74px "Heebo"}
.geek{margin-top:auto;border:3px solid #1F4E8C;background:rgba(245,241,232,.92);padding:30px 36px 34px;position:relative}
.geek .t{position:absolute;top:-26px;right:30px;background:#1F4E8C;color:#F5F1E8;font:700 30px "Assistant";padding:4px 18px}
.geek p{font-size:38px;margin-top:6px;color:#1A1A1A}
.stamp{display:inline-block;border:10px solid #FF5A1F;color:#FF5A1F;font:900 150px/1 "Heebo";padding:26px 46px 34px;
  transform:rotate(-7deg);mix-blend-mode:multiply;margin:80px auto 20px;align-self:center}
.stamp.small{font-size:58px;border-width:6px;padding:18px 30px 22px;line-height:1.15;text-align:center}
.drawing{margin-top:auto;align-self:center}
.slide.end{justify-content:center;padding-bottom:200px}
.cta{font:800 64px/1.15 "Heebo";margin-top:60px;text-align:center}
.cta2{font:400 42px/1.4 "Assistant";color:#5A564E;text-align:center;margin-top:24px}
"""


def bike_svg(color="#FF5A1F"):
    """Blueprint-style bike with a dimension line pointing at the paint."""
    ink, blue = "#1A1A1A", "#1F4E8C"
    return f"""<svg width="740" height="414" viewBox="0 0 840 470" xmlns="http://www.w3.org/2000/svg" font-family="Assistant">
  <g fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="190" cy="320" r="135" stroke="{ink}" stroke-width="6"/>
    <circle cx="190" cy="320" r="10" fill="{ink}"/>
    <circle cx="640" cy="320" r="135" stroke="{ink}" stroke-width="6"/>
    <circle cx="640" cy="320" r="10" fill="{ink}"/>
    <path d="M190 320 L330 175 L420 320 Z M330 175 L560 175 L420 320 M560 175 L640 320 M560 175 L545 140 M520 128 L590 128" stroke="{color}" stroke-width="16"/>
    <path d="M330 175 L315 130 M285 122 L355 122" stroke="{ink}" stroke-width="10"/>
    <circle cx="420" cy="320" r="26" stroke="{ink}" stroke-width="6"/>
  </g>
  <g stroke="{blue}" stroke-width="3" fill="none">
    <path d="M445 175 L445 70 L640 70"/>
    <path d="M436 186 L445 175 L454 186" />
  </g>
  <text x="652" y="62" fill="{blue}" font-size="34" font-weight="700" text-anchor="end" direction="rtl">שכבת צבע</text>
  <text x="652" y="100" fill="{blue}" font-size="28" text-anchor="end" direction="ltr" font-family="Plex">0.1-0.2 mm</text>
</svg>"""


def esc(s):
    return html.escape(str(s))


def rich(s):
    """Escape, then allow **bold**."""
    out, parts = "", esc(s).split("**")
    for i, part in enumerate(parts):
        out += f"<b>{part}</b>" if i % 2 else part
    return out


def slide_html(s, i, total, post):
    top = f'<div class="top"><span>{esc(post["series"])}</span><span class="n">{i}/{total}</span></div>'
    foot = f'<div class="foot"><span>אין שאלות טיפשיות</span><span class="h">{HANDLE}</span></div>'
    L = s["layout"]
    geek = ""
    if s.get("geek"):
        geek = f'<div class="geek"><span class="t">{esc(s.get("geek_title", "למי שרוצה לדעת יותר"))}</span><p>{rich(s["geek"])}</p></div>'
    body = "".join(f"<p>{rich(x)}</p>" for x in s.get("body", []))
    kicker = f'<div class="kicker">{esc(s["kicker"])}</div>' if s.get("kicker") else ""
    if L == "cover":
        inner = f'{kicker}<h1>{esc(s["title"])}</h1>' + (f'<div class="sub">{rich(s["sub"])}</div>' if s.get("sub") else "")
        if s.get("drawing") == "bike":
            inner += f'<div class="drawing">{bike_svg()}</div>'
    elif L == "stat":
        inner = f'{kicker}<div class="big"><span class="num">{esc(s["number"])}</span><span class="unit">{esc(s["unit"])}</span></div>{body}{geek}'
    elif L == "text":
        inner = f'{kicker}<h2>{esc(s["heading"])}</h2>{body}{geek}'
    elif L == "verdict":
        inner = f'{kicker}<div class="stamp">{esc(s["stamp"])}</div>{body}{geek}'
    elif L == "end":
        inner = (f'<div class="stamp small">נבדק. נחקר.<br>אין שאלות טיפשיות.</div>'
                 f'<div class="cta">{esc(s.get("cta", "יש לך שאלה טיפשית? שלח. אין כאן כאלה."))}</div>'
                 + (f'<div class="cta2">{rich(s["note"])}</div>' if s.get("note") else ""))
    else:
        raise ValueError(f"Unknown layout {L!r} on slide {i}")
    return f'<section class="slide {L}" id="s{i}">{top}{inner}{foot}</section>'


def build_html(post):
    total = len(post["slides"])
    slides = "".join(slide_html(s, i + 1, total, post) for i, s in enumerate(post["slides"]))
    return f'<!doctype html><html lang="he"><head><meta charset="utf-8"><style>{font_faces()}{CSS}</style></head><body>{slides}</body></html>'


def render(post_path, out_dir="out"):
    from playwright.sync_api import sync_playwright
    post = json.loads(pathlib.Path(post_path).read_text(encoding="utf-8"))
    out = pathlib.Path(out_dir) / post["id"]
    out.mkdir(parents=True, exist_ok=True)
    page_file = out / "preview.html"
    page_file.write_text(build_html(post), encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(page_file.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        files = []
        for i in range(1, len(post["slides"]) + 1):
            el = pg.locator(f"#s{i}")
            # Fail loudly if text overflows the slide instead of silently clipping it.
            over = el.evaluate("e => e.scrollHeight > e.clientHeight + 2")
            if over:
                raise SystemExit(f"Slide {i} overflows by {el.evaluate('e => e.scrollHeight - e.clientHeight')}px: shorten its text")
            f = out / f"{i:02d}.png"
            el.screenshot(path=str(f))
            files.append(f)
        b.close()
    return files


if __name__ == "__main__":
    for f in render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "out"):
        print(f)
