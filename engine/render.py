"""Render a carousel post (JSON) into 1080x1350 PNG slides in the 'everything is measured' system.

Usage:  python engine/render.py content/posts/<id>.json  [out_dir]
Output: out_dir/<id>/01.png ...  plus preview.html

Every slide sits on a drawing sheet: double frame, rulers, title block. Layouts:
  cover   – fig, kicker, title, optional drawing {"type":"bike","notes":[...],"dim":"..."}
  stat    – kicker, number + unit (dimensioned), body, optional note
  text    – kicker, heading, body, optional note
  verdict – kicker, stamp, body, optional note
  end     – closing stamp + call to send questions

Layout QA runs on every render and FAILS the build if anything leaves the frame, a drawing is
clipped by its own canvas, or two labels collide. Nothing is published that 'escapes the lines'.
"""
import html, json, sys, pathlib
import draw

ROOT = pathlib.Path(__file__).resolve().parent
FONTS = ROOT / "node_modules" / "@fontsource"
HANDLE = "@no.dumb.questions.cycling"
PAGE = "אין שאלות טיפשיות"


def font_faces():
    sets = [("Frank", "frank-ruhl-libre", [700, 900], False), ("Heebo", "heebo", [800], True),
            ("Pencil", "gveret-levin", [400], False),
            ("Assistant", "assistant", [400, 600, 700], True)]
    faces = []
    for fam, pkg, weights, has_latin in sets:
        for w in weights:
            heb = (FONTS / pkg / "files" / f"{pkg}-hebrew-{w}-normal.woff2").as_uri()
            faces.append(f'@font-face{{font-family:"{fam}";font-weight:{w};src:url("{heb}") format("woff2");unicode-range:U+0590-05FF,U+200C-2010,U+20AA,U+25CC,U+FB1D-FB4F;}}')
            lat = FONTS / pkg / "files" / f"{pkg}-latin-{w}-normal.woff2"
            if lat.exists():
                faces.append(f'@font-face{{font-family:"{fam}";font-weight:{w};src:url("{lat.as_uri()}") format("woff2");}}')
    for w in [400, 500]:
        faces.append(f'@font-face{{font-family:"Plex";font-weight:{w};src:url("{(FONTS / "ibm-plex-mono" / "files" / f"ibm-plex-mono-latin-{w}-normal.woff2").as_uri()}") format("woff2");}}')
    return "\n".join(faces)


CSS = """
:root{--paper:#F5F1E8;--ink:#1A1A1A;--ink2:#6B665C;--orange:#FF5A1F;--blue:#1F4E8C;--blue-soft:rgba(31,78,140,.5)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#7d7a73;font-family:"Assistant",sans-serif;color:var(--ink)}
.s{width:1080px;height:1350px;position:relative;overflow:hidden;direction:rtl;margin:0 auto 40px;background:var(--paper)}
.s::before{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:radial-gradient(rgba(31,78,140,.13) 1.2px,transparent 1.4px);background-size:27px 27px;background-position:13px 13px}
.frame{position:absolute;inset:40px;border:2px solid var(--ink);pointer-events:none}
.frame::after{content:"";position:absolute;inset:7px;border:.8px solid var(--ink)}
.reg{position:absolute;width:26px;height:26px;pointer-events:none}
.reg::before,.reg::after{content:"";position:absolute;background:var(--ink)}
.reg::before{left:12px;top:0;width:1.2px;height:26px}.reg::after{top:12px;left:0;height:1.2px;width:26px}
.reg.a{top:7px;left:7px}.reg.b{top:7px;right:7px}.reg.c{bottom:7px;left:7px}.reg.d{bottom:7px;right:7px}
.rt,.rr{position:absolute;pointer-events:none}
.rt{top:49px;left:120px;right:120px;height:18px;
  background:repeating-linear-gradient(270deg,var(--blue) 0 1.6px,transparent 1.6px 135px) top/100% 18px no-repeat,
             repeating-linear-gradient(270deg,var(--blue-soft) 0 1px,transparent 1px 27px) top/100% 9px no-repeat}
.rr{top:120px;bottom:240px;right:49px;width:18px;
  background:repeating-linear-gradient(180deg,var(--blue) 0 1.6px,transparent 1.6px 135px) right/18px 100% no-repeat,
             repeating-linear-gradient(180deg,var(--blue-soft) 0 1px,transparent 1px 27px) right/9px 100% no-repeat}
.tb{position:absolute;left:47px;right:47px;bottom:47px;height:96px;border-top:2px solid var(--ink);
  display:grid;grid-template-columns:1.35fr 1.3fr .55fr 1.8fr}
.tb>div{padding:12px 20px;border-left:.8px solid var(--ink);display:flex;flex-direction:column;justify-content:center;gap:1px}
.tb>div:last-child{border-left:0}
.tb small{font:600 19px "Assistant";color:var(--ink2)}
.tb b{font:700 27px "Assistant";white-space:nowrap}
.tb .m{font:400 25px "Plex";direction:ltr;text-align:right;white-space:nowrap}
.in{position:absolute;top:47px;left:47px;right:47px;bottom:143px;padding:78px 66px 34px;display:flex;flex-direction:column}
.fig{font:500 24px "Plex";color:var(--blue);direction:ltr;text-align:right;letter-spacing:.04em}
.kick{font:700 31px "Assistant";color:var(--ink2);margin-top:8px}
h1{font:700 100px/1.06 "Frank";letter-spacing:-.01em;margin-top:18px}
h2{font:700 78px/1.1 "Frank";margin-top:16px}
p{font:400 40px/1.45 "Assistant";margin-top:26px;max-width:860px}
p b{font-weight:700}
.sub{font:600 42px/1.38 "Assistant";color:var(--ink2);margin-top:30px;max-width:820px}
.drawing{margin-top:auto;width:100%}
svg{direction:ltr;overflow:visible}
.num{display:inline-flex;flex-direction:column;align-items:stretch;margin-top:46px;align-self:flex-start}
.num b{font:900 250px/.86 "Frank";color:var(--orange);letter-spacing:-.02em;direction:ltr;text-align:right}
.num svg{height:64px;width:100%;margin-top:14px}
.note{margin-top:auto;padding-top:22px;border-top:2px solid var(--ink);position:relative}
.note::before{content:"";position:absolute;top:4px;left:0;right:0;border-top:.8px solid var(--ink)}
.note .h{display:flex;justify-content:space-between;align-items:baseline}
.note .h b{font:700 30px "Assistant";color:var(--blue)}
.note .h span{font:400 22px "Plex";color:var(--blue);direction:ltr}
.note p{font-size:36px;margin-top:8px}
.stamp{align-self:center;margin:70px 0 30px;color:var(--orange);border:6px solid var(--orange);padding:10px;transform:rotate(-6deg);mix-blend-mode:multiply}
.stamp>div{border:2px solid var(--orange);padding:18px 46px 26px;font:900 140px/1 "Frank";text-align:center}
.stamp small{display:block;font:500 24px "Plex";letter-spacing:.2em;margin-bottom:10px;direction:ltr}
.stamp.sm>div{font-size:56px;line-height:1.2;padding:18px 34px 22px}
/* the pencil layer: unofficial, unverified scribbles in the margin */
.pencil{align-self:flex-end;max-width:640px;margin-top:34px;transform:rotate(-2.5deg);transform-origin:left top;color:#4E4B45;position:relative;padding-left:4px}
.pencil .t{font:400 44px/1.25 "Pencil";display:block}
.pencil .tag{display:inline-block;font:500 18px "Plex";letter-spacing:.14em;color:#4E4B45;border:1.4px solid #4E4B45;padding:2px 9px 1px;margin-bottom:8px;direction:ltr}
.pencil svg{display:block;width:180px;height:26px;margin-top:4px}
.s.end .in{justify-content:center;padding-bottom:120px}
.cta{font:700 66px/1.18 "Frank";text-align:center;margin-top:40px}
.cta2{font:400 40px/1.4 "Assistant";color:var(--ink2);text-align:center;margin-top:20px}
"""


def esc(s):
    return html.escape(str(s))


def rich(s):
    out, parts = "", esc(s).split("**")
    for i, part in enumerate(parts):
        out += f"<b>{part}</b>" if i % 2 else part
    return out


def bike_figure(spec):
    inner, anchors = draw.road_bike(accent_frame=True)
    notes = ""
    for n in spec.get("notes", []):
        ax, ay = anchors[n["at"]]
        side = n.get("side", "right")
        ex, ey = n.get("elbow") or ((ax + 70, 62) if side == "right" else (ax - 90, 62))
        notes += draw.leader([(ax, ay), (ex, ey)], n["title"], n.get("value"), side=side, shelf=n.get("shelf", 240))
    if spec.get("dim"):
        R, F = anchors["rear_axle"], anchors["front_axle"]
        notes += draw.dim(R[0], R[1], F[0], F[1], spec["dim"], offset=210)
    return f'<svg class="drawing" viewBox="0 0 950 640">{draw.DEFS}{inner}{notes}</svg>'


def number_block(s):
    unit = s.get("unit", "")
    dimsvg = ""
    if unit:
        # a dimension line that measures the number itself
        dimsvg = (f'<svg viewBox="0 0 400 64" preserveAspectRatio="none">{draw.DEFS}'
                  f'<line x1="2" y1="6" x2="2" y2="40" stroke="#1F4E8C" stroke-width="1"/><line x1="398" y1="6" x2="398" y2="40" stroke="#1F4E8C" stroke-width="1"/>'
                  f'<line x1="4" y1="24" x2="396" y2="24" stroke="#1F4E8C" stroke-width="1.4" marker-start="url(#arw)" marker-end="url(#arw)"/></svg>'
                  f'<div style="font:400 26px Plex;color:#1F4E8C;text-align:center;margin-top:-6px">{esc(unit)}</div>')
    return f'<div class="num"><b>{esc(s["number"])}</b>{dimsvg}</div>'


def note_block(s):
    if not s.get("note"):
        return ""
    return (f'<div class="note"><div class="h"><b>{esc(s.get("note_title", "לחנונים"))}</b><span>NOTE</span></div>'
            f'<p>{rich(s["note"])}</p></div>')


def pencil_block(s):
    if not s.get("pencil"):
        return ""
    squiggle = ('<svg viewBox="0 0 180 26"><path d="M2 14 C20 4 34 22 52 12 S86 4 104 14 S140 22 178 9" fill="none" '
                'stroke="#4E4B45" stroke-width="2" stroke-linecap="round"/></svg>')
    return f'<div class="pencil"><span class="tag">UNVERIFIED</span><span class="t">{esc(s["pencil"])}</span>{squiggle}</div>'


def slide_html(s, i, total, post):
    L = s["layout"]
    fig = f'<div class="fig">FIG. {esc(post["fig"])}.{i}</div>'
    kicker = f'<div class="kick">{esc(s["kicker"])}</div>' if s.get("kicker") else ""
    body = "".join(f"<p>{rich(x)}</p>" for x in s.get("body", []))
    if L == "cover":
        inner = fig + kicker + f'<h1>{esc(s["title"])}</h1>' + (f'<div class="sub">{rich(s["sub"])}</div>' if s.get("sub") else "") + pencil_block(s)
        d = s.get("drawing")
        if d and d.get("type") == "bike":
            inner += bike_figure(d)
    elif L == "stat":
        inner = fig + kicker + number_block(s) + body + pencil_block(s) + note_block(s)
    elif L == "text":
        inner = fig + kicker + f'<h2>{esc(s["heading"])}</h2>' + body + pencil_block(s) + note_block(s)
    elif L == "verdict":
        inner = fig + kicker + f'<div class="stamp"><div><small>VERDICT</small>{esc(s["stamp"])}</div></div>' + body + pencil_block(s) + note_block(s)
    elif L == "end":
        inner = (f'<div class="stamp sm"><div><small>CASE CLOSED</small>נבדק. נחקר.<br>אין שאלות טיפשיות.</div></div>'
                 f'<div class="cta">{esc(s.get("cta", "יש לך שאלה טיפשית? שלח.\nאין כאן כאלה.")).replace(chr(10), "<br>")}</div>'
                 + (f'<div class="cta2">{rich(s["note"])}</div>' if s.get("note") else ""))
    else:
        raise ValueError(f"Unknown layout {L!r} on slide {i}")
    tb = (f'<div class="tb"><div><small>עמוד</small><b>{PAGE}</b></div><div><small>סדרה</small><b>{esc(post["series"])}</b></div>'
          f'<div><small>שקף</small><span class="m">{i}/{total}</span></div><div><small>&nbsp;</small><span class="m">{HANDLE}</span></div></div>')
    chrome = ('<div class="frame"><span class="reg a"></span><span class="reg b"></span><span class="reg c"></span><span class="reg d"></span></div>'
              '<div class="rt"></div><div class="rr"></div>')
    return f'<section class="s {L}" id="s{i}">{chrome}<div class="in">{inner}</div>{tb}</section>'


def build_html(post):
    total = len(post["slides"])
    slides = "".join(slide_html(s, i + 1, total, post) for i, s in enumerate(post["slides"]))
    return f'<!doctype html><html lang="he"><head><meta charset="utf-8"><style>{font_faces()}{CSS}</style></head><body>{slides}</body></html>'


# Runs in the page. Returns a list of problems for one slide.
QA_JS = r"""
(slide) => {
  const problems = [];
  const r = e => e.getBoundingClientRect();
  const s = r(slide), inBox = r(slide.querySelector('.in')), tb = r(slide.querySelector('.tb'));
  const safe = {left: s.left + 62, right: s.right - 62, top: s.top + 70, bottom: tb.top - 6};
  const outside = (b) => b.width > 0 && (b.left < safe.left - .5 || b.right > safe.right + .5 || b.top < safe.top - .5 || b.bottom > safe.bottom + .5);
  const name = e => (e.textContent || e.tagName).trim().slice(0, 30);
  // 1. every text run and every drawing inside the content area stays in the safe zone
  const texts = [];
  const walker = document.createTreeWalker(slide.querySelector('.in'), NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    if (n.parentElement.closest('svg')) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    for (const b of range.getClientRects()) { texts.push({b, who: n.textContent.trim().slice(0, 30), el: n.parentElement}); if (outside(b)) problems.push(`text leaves the frame: "${n.textContent.trim().slice(0,30)}"`); }
  }
  for (const t of slide.querySelectorAll('.in svg text')) { const b = r(t); texts.push({b, who: name(t), el: t}); if (outside(b)) problems.push(`label leaves the frame: "${name(t)}"`); }
  for (const svg of slide.querySelectorAll('.in svg')) {
    if (outside(r(svg))) problems.push('drawing leaves the frame');
    const vb = svg.viewBox.baseVal, bb = svg.getBBox();
    if (vb && vb.width && (bb.x < vb.x - 2 || bb.y < vb.y - 2 || bb.x + bb.width > vb.x + vb.width + 2 || bb.y + bb.height > vb.y + vb.height + 2))
      problems.push(`drawing spills past its canvas (${Math.round(bb.x)},${Math.round(bb.y)} ${Math.round(bb.width)}x${Math.round(bb.height)})`);
  }
  // 2. no two separate pieces of text overlap
  for (let a = 0; a < texts.length; a++) for (let b = a + 1; b < texts.length; b++) {
    const A = texts[a], B = texts[b]; if (A.el === B.el) continue;
    // line boxes include the font's ascent/descent; compare the inner ~60% where glyphs actually sit
    const ink = x => ({left: x.left, right: x.right, top: x.top + x.height * .2, bottom: x.bottom - x.height * .2});
    const P = ink(A.b), Q = ink(B.b);
    const w = Math.min(P.right, Q.right) - Math.max(P.left, Q.left), h = Math.min(P.bottom, Q.bottom) - Math.max(P.top, Q.top);
    if (w > 3 && h > 3) problems.push(`text collides: "${A.who}" / "${B.who}"`);
  }
  // 3. content box itself must not overflow
  const inn = slide.querySelector('.in'); if (inn.scrollHeight > inn.clientHeight + 2) problems.push('content is taller than the sheet');
  return [...new Set(problems)];
}
"""


def render(post_path, out_dir="out"):
    from playwright.sync_api import sync_playwright
    post = json.loads(pathlib.Path(post_path).read_text(encoding="utf-8"))
    post.setdefault("fig", 1)
    out = pathlib.Path(out_dir) / post["id"]
    out.mkdir(parents=True, exist_ok=True)
    page_file = out / "preview.html"
    page_file.write_text(build_html(post), encoding="utf-8")
    files, failures = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(page_file.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        for i in range(1, len(post["slides"]) + 1):
            el = pg.locator(f"#s{i}")
            for prob in el.evaluate(QA_JS):
                failures.append(f"slide {i}: {prob}")
            f = out / f"{i:02d}.png"
            el.screenshot(path=str(f))
            files.append(f)
        b.close()
    if failures:
        raise SystemExit("Layout QA failed:\n  " + "\n  ".join(failures))
    return files


if __name__ == "__main__":
    for f in render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "out"):
        print(f)
