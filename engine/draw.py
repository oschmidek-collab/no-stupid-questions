"""Drafting primitives for the 'everything is measured' visual system.

Every drawing is built from the same line hierarchy, like a real engineering drawing:
  contour      3.2px ink        – the object itself
  detail       1.6px ink        – secondary parts (spokes' rim, saddle seams)
  hairline     0.9px ink 60%    – spokes, textures
  centre line  1px blue dash-dot – axles, symmetry
  annotation   1.4px blue        – leaders, dimension lines, with filled arrowheads
Only ONE element per slide is orange (ACCENT).

All functions return SVG fragments (strings). Coordinates are in the caller's viewBox.
"""
import math, html

INK, BLUE, PAPER, ACCENT, INK2 = "#1A1A1A", "#1F4E8C", "#F5F1E8", "#FF5A1F", "#6B665C"

DEFS = f"""<defs>
  <marker id="arw" viewBox="0 0 12 8" refX="11.5" refY="4" markerWidth="16" markerHeight="11" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
    <path d="M0 0.6 L12 4 L0 7.4 Z" fill="{BLUE}"/></marker>
  <pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="9" stroke="{INK}" stroke-width="1" stroke-opacity=".45"/></pattern>
  <pattern id="hatch-accent" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="10" stroke="{ACCENT}" stroke-width="2"/></pattern>
</defs>"""


def esc(s):
    return html.escape(str(s))


def line(x1, y1, x2, y2, kind="contour", color=None):
    style = {
        "contour": f'stroke="{color or INK}" stroke-width="3.2"',
        "detail": f'stroke="{color or INK}" stroke-width="1.6"',
        "hair": f'stroke="{color or INK}" stroke-width=".9" stroke-opacity=".6"',
        "centre": f'stroke="{color or BLUE}" stroke-width="1" stroke-dasharray="22 5 3 5"',
        "hidden": f'stroke="{color or INK}" stroke-width="1.4" stroke-dasharray="7 5"',
    }[kind]
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {style} stroke-linecap="round"/>'


def label(x, y, title, value=None, anchor="end", color=BLUE, halo=False, k=1.0):
    """Two-line annotation label: Hebrew title (bold) above a mono value. anchor is LTR semantics."""
    h = f' paint-order="stroke" stroke="{PAPER}" stroke-width="{10 * k:.0f}" stroke-linejoin="round"' if halo else ""
    out = f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Assistant" font-weight="700" font-size="{27 * k:.0f}" fill="{color}"{h}>{esc(title)}</text>'
    if value is not None:
        out += f'<text x="{x}" y="{y + 38 * k:.0f}" text-anchor="{anchor}" font-family="Plex" font-size="{24 * k:.0f}" fill="{color}"{h}>{esc(value)}</text>'
    return out


def leader(points, title, value=None, side="right", shelf=230, color=BLUE, halo=False, k=1.0):
    """Leader from an anchor dot through elbow points, ending in a horizontal shelf carrying the label.
    side='right': shelf extends right from the last point, label right-aligned at its end.
    side='left' : shelf extends left, label left-aligned at its end.  k scales text, dots and line weight."""
    (ax, ay), *rest = points
    ex, ey = rest[-1] if rest else (ax, ay)
    sx = ex + shelf if side == "right" else ex - shelf
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points) + f" L{sx:.1f} {ey:.1f}"
    under = ""
    if halo:
        under = f'<path d="{d}" fill="none" stroke="{PAPER}" stroke-width="{6 * k:.1f}" stroke-opacity=".85" stroke-linejoin="round"/>'
    out = under + f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{1.4 * k:.1f}" stroke-linejoin="round"/>'
    out += f'<circle cx="{ax}" cy="{ay}" r="{5.5 * k:.1f}" fill="{color}"/><circle cx="{ax}" cy="{ay}" r="{10 * k:.1f}" fill="none" stroke="{color}" stroke-width="{k:.1f}"/>'
    anchor = "end" if side == "right" else "start"
    out += label(sx, ey - 14 * k, title, None, anchor, color, halo, k)
    if value is not None:
        out += f'<text x="{sx}" y="{ey + 34 * k:.0f}" text-anchor="{anchor}" font-family="Plex" font-size="{24 * k:.0f}" fill="{color}"' + (f' paint-order="stroke" stroke="{PAPER}" stroke-width="{10 * k:.0f}"' if halo else "") + f'>{esc(value)}</text>'
    return out


def dim(x1, y1, x2, y2, text, offset=0, ext=True):
    """Dimension line between two points (drawn offset perpendicular), extension lines, value in a gap."""
    ang = math.atan2(y2 - y1, x2 - x1)
    nx, ny = -math.sin(ang) * offset, math.cos(ang) * offset
    a = (x1 + nx, y1 + ny); b = (x2 + nx, y2 + ny)
    out = ""
    if ext and offset:
        g = 8 if offset > 0 else -8
        for (px, py), (qx, qy) in [((x1, y1), a), ((x2, y2), b)]:
            ux, uy = -math.sin(ang), math.cos(ang)
            out += f'<line x1="{px + ux * g:.1f}" y1="{py + uy * g:.1f}" x2="{qx + ux * g * 1.6:.1f}" y2="{qy + uy * g * 1.6:.1f}" stroke="{BLUE}" stroke-width="1"/>'
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    w = 16 * len(text) + 24
    deg = math.degrees(ang)
    out += f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{BLUE}" stroke-width="1.4" marker-start="url(#arw)" marker-end="url(#arw)"/>'
    out += (f'<g transform="translate({mx:.1f} {my:.1f}) rotate({deg:.1f})">'
            f'<rect x="{-w / 2:.1f}" y="-17" width="{w:.1f}" height="34" fill="{PAPER}"/>'
            f'<text x="0" y="8" text-anchor="middle" font-family="Plex" font-size="24" fill="{BLUE}">{esc(text)}</text></g>')
    return out


def callout(x, y, n, r=22):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="1.8"/>'
            f'<text x="{x}" y="{y + 8}" text-anchor="middle" font-family="Plex" font-size="22" fill="{INK}">{n}</text>')


def wheel(cx, cy, r, spokes=24):
    out = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="3.2"/>'           # tyre
    out += f'<circle cx="{cx}" cy="{cy}" r="{r - 9}" fill="none" stroke="{INK}" stroke-width=".9" stroke-opacity=".6" stroke-dasharray="2 5"/>'  # tread
    out += f'<circle cx="{cx}" cy="{cy}" r="{r - 20}" fill="none" stroke="{INK}" stroke-width="1.6"/>'      # rim outer
    out += f'<circle cx="{cx}" cy="{cy}" r="{r - 30}" fill="none" stroke="{INK}" stroke-width="1.6"/>'      # rim inner
    for i in range(spokes):
        a = 2 * math.pi * i / spokes
        hx, hy = cx + 14 * math.cos(a + .25), cy + 14 * math.sin(a + .25)
        out += f'<line x1="{hx:.1f}" y1="{hy:.1f}" x2="{cx + (r - 30) * math.cos(a):.1f}" y2="{cy + (r - 30) * math.sin(a):.1f}" stroke="{INK}" stroke-width=".9" stroke-opacity=".55"/>'
    out += f'<circle cx="{cx}" cy="{cy}" r="16" fill="{PAPER}" stroke="{INK}" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="5" fill="{INK}"/>'
    return out


def tube(p, q, w, fill=PAPER, stroke=INK):
    """A frame tube drawn as a real outline (two edges + rounded ends), not a single stroke."""
    (x1, y1), (x2, y2) = p, q
    ang = math.atan2(y2 - y1, x2 - x1)
    nx, ny = -math.sin(ang) * w / 2, math.cos(ang) * w / 2
    pts = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="2.2" stroke-linejoin="round"/>'


def road_bike(accent_frame=True):
    """Side-view road bike in drafting style. viewBox 0 0 950 600. Returns (svg_inner, anchors)."""
    R, F = (215, 400), (735, 400)            # rear / front axle
    BB, ST, HT_T, HT_B = (455, 420), (392, 190), (668, 196), (682, 250)
    fill = ACCENT if accent_frame else PAPER
    out = ""
    # centre lines through axles and BB
    for x, y in (R, F, BB):
        out += line(x - 40, y, x + 40, y, "centre") + line(x, y - 40, x, y + 40, "centre")
    out += line(R[0], R[1], F[0], F[1], "centre")
    out += wheel(*R, 175) + wheel(*F, 175)
    # chainring + chain
    out += f'<circle cx="{BB[0]}" cy="{BB[1]}" r="46" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
    out += f'<circle cx="{BB[0]}" cy="{BB[1]}" r="52" fill="none" stroke="{INK}" stroke-width="3" stroke-dasharray="3 3"/>'
    out += f'<path d="M{BB[0]} {BB[1] - 52} L{R[0]} {R[1] - 22} M{BB[0]} {BB[1] + 52} L{R[0]} {R[1] + 22}" stroke="{INK}" stroke-width="1.6" stroke-dasharray="6 4" fill="none"/>'
    out += f'<circle cx="{R[0]}" cy="{R[1]}" r="24" fill="none" stroke="{INK}" stroke-width="1.6" stroke-dasharray="3 3"/>'
    # frame: drawn as one welded piece. A wider ink stroke under every tube, then the fill on top,
    # so joints merge cleanly instead of showing overlapping rectangles.
    tubes = [(R, BB, 14), (R, ST, 12), (BB, ST, 22), (BB, HT_B, 30), (ST, HT_T, 22), (HT_T, HT_B, 26)]
    seg = lambda p, q: f"M{p[0]:.1f} {p[1]:.1f} L{q[0]:.1f} {q[1]:.1f}"
    out += "".join(f'<path d="{seg(p, q)}" stroke="{INK}" stroke-width="{w + 5}" stroke-linecap="round"/>' for p, q, w in tubes)
    out += "".join(f'<path d="{seg(p, q)}" stroke="{fill}" stroke-width="{w}" stroke-linecap="round"/>' for p, q, w in tubes)
    # a hairline highlight along the big tubes gives them volume
    for p, q, w in tubes[2:5]:
        import math as _m
        a_ = _m.atan2(q[1] - p[1], q[0] - p[0]); ox, oy = -_m.sin(a_) * w * .22, _m.cos(a_) * w * .22
        out += f'<path d="M{p[0] + ox:.1f} {p[1] + oy:.1f} L{q[0] + ox:.1f} {q[1] + oy:.1f}" stroke="{PAPER}" stroke-opacity=".55" stroke-width="1.6" stroke-linecap="round"/>'
    out += f'<circle cx="{BB[0]}" cy="{BB[1]}" r="17" fill="{PAPER}" stroke="{INK}" stroke-width="2.2"/>'
    # fork (curved), stem, bars, seatpost, saddle, crank, pedal
    out += f'<path d="M{HT_B[0] - 6} {HT_B[1]} C{HT_B[0] + 14} 320 {F[0] - 24} 360 {F[0]} {F[1]}" fill="none" stroke="{INK}" stroke-width="3.2"/>'
    out += f'<path d="M{HT_B[0] + 8} {HT_B[1]} C{HT_B[0] + 30} 320 {F[0] - 6} 360 {F[0] + 6} {F[1]}" fill="none" stroke="{INK}" stroke-width="1.6"/>'
    out += f'<path d="M{HT_T[0]} {HT_T[1]} L{HT_T[0] + 8} 160 L{HT_T[0] + 72} 150" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>'
    out += f'<path d="M{HT_T[0] + 72} 150 C{HT_T[0] + 108} 148 {HT_T[0] + 112} 196 {HT_T[0] + 88} 214 C{HT_T[0] + 74} 224 {HT_T[0] + 58} 218 {HT_T[0] + 56} 206" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>'
    out += f'<path d="M{ST[0]} {ST[1]} L{ST[0] - 12} 132" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    out += f'<path d="M{ST[0] - 74} 128 C{ST[0] - 40} 116 {ST[0] + 20} 116 {ST[0] + 48} 124 L{ST[0] + 44} 136 C{ST[0] + 10} 132 {ST[0] - 40} 136 {ST[0] - 74} 138 Z" fill="{PAPER}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>'
    out += f'<path d="M{BB[0]} {BB[1]} L{BB[0] + 44} {BB[1] + 78}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
    out += f'<rect x="{BB[0] + 24}" y="{BB[1] + 74}" width="42" height="11" rx="3" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
    anchors = {"top_tube": ((ST[0] + HT_T[0]) / 2, (ST[1] + HT_T[1]) / 2 + 2),
               "down_tube": ((BB[0] + HT_B[0]) / 2, (BB[1] + HT_B[1]) / 2),
               "seat_tube": ((BB[0] + ST[0]) / 2, (BB[1] + ST[1]) / 2),
               "rear_axle": R, "front_axle": F, "bb": BB}
    return out, anchors


def sprocket(cx, cy, teeth, k=4.2, fill=PAPER, stroke=INK, sw=2.2, inner=None):
    """Front view of a sprocket with real teeth. Pitch radius scales with tooth count."""
    R = teeth * k / 2
    h = 5.5
    pts = []
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        step = math.pi / teeth
        for da, r in ((-step, R - h * .7), (-step * .38, R + h), (step * .38, R + h)):
            pts.append((cx + r * math.cos(a + da), cy + r * math.sin(a + da)))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
    out = f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
    out += f'<circle cx="{cx}" cy="{cy}" r="{R - h * 2.2:.1f}" fill="none" stroke="{stroke}" stroke-width=".9" stroke-opacity=".6"/>'
    if inner:
        out += f'<circle cx="{cx}" cy="{cy}" r="{inner}" fill="{PAPER}" stroke="{stroke}" stroke-width="1.6"/>'
    return out, R


def cassette(teeth=(11, 12, 13, 14, 15, 17, 19, 21, 24, 27, 30, 34), accent_largest=True):
    """Cassette: front view (left) and edge view (right). viewBox 0 0 950 560. Returns (svg, anchors)."""
    out = ""
    cx, cy, k = 250, 290, 6.4
    # front view: every sprocket, largest first, each outline visible
    # draw a readable subset with real teeth; the rest as hairline pitch circles (like a real exploded view)
    shown = [t for t in sorted(teeth, reverse=True)][::3] + [min(teeth)]
    for t in sorted(teeth, reverse=True):
        is_acc = accent_largest and t == max(teeth)
        if t in shown:
            s, R = sprocket(cx, cy, t, k=k, fill=ACCENT if is_acc else PAPER, sw=2.4 if is_acc else 1.6)
            out += s
        else:
            out += f'<circle cx="{cx}" cy="{cy}" r="{t * k / 2:.1f}" fill="none" stroke="{INK}" stroke-width=".9" stroke-opacity=".55" stroke-dasharray="3 3"/>'

    # splined freehub + lockring
    out += f'<circle cx="{cx}" cy="{cy}" r="30" fill="{PAPER}" stroke="{INK}" stroke-width="2.4"/>'
    for i in range(12):
        a = 2 * math.pi * i / 12
        out += f'<line x1="{cx + 22 * math.cos(a):.1f}" y1="{cy + 22 * math.sin(a):.1f}" x2="{cx + 30 * math.cos(a):.1f}" y2="{cy + 30 * math.sin(a):.1f}" stroke="{INK}" stroke-width="1.6"/>'
    out += f'<circle cx="{cx}" cy="{cy}" r="9" fill="{INK}"/>'
    out += line(cx - 140, cy, cx + 140, cy, "centre") + line(cx, cy - 140, cx, cy + 140, "centre")
    # edge view: sprockets as plates, tallest = most teeth, axle centre line through
    ex, gap = 600, 19
    out += line(ex - 60, cy, ex + gap * len(teeth) + 70, cy, "centre")
    out += f'<rect x="{ex - 24}" y="{cy - 36}" width="{gap * len(teeth) + 34}" height="72" fill="url(#hatch)" stroke="{INK}" stroke-width="1.6"/>'
    plates = sorted(teeth, reverse=True)  # largest nearest the spokes
    for i, t in enumerate(plates):
        h = t * k / 2 + 5
        x = ex + i * gap
        is_acc = accent_largest and t == max(teeth)
        out += f'<rect x="{x:.1f}" y="{cy - h:.1f}" width="6" height="{2 * h:.1f}" rx="1.5" fill="{ACCENT if is_acc else PAPER}" stroke="{INK}" stroke-width="1.6"/>'
    lx = ex + len(teeth) * gap + 2
    out += f'<rect x="{lx}" y="{cy - 40}" width="14" height="80" rx="2" fill="{PAPER}" stroke="{INK}" stroke-width="2.4"/>'
    big_h = max(teeth) * k / 2 + 5
    small_h = min(teeth) * k / 2 + 5
    anchors = {"largest_front": (cx + max(teeth) * k / 2 * math.cos(-.9), cy + max(teeth) * k / 2 * math.sin(-.9)),
               "smallest_front": (cx + min(teeth) * k / 2 * .7, cy - min(teeth) * k / 2 * .7),
               "largest_edge": (ex + 3, cy - big_h), "smallest_edge": (ex + (len(teeth) - 1) * gap + 3, cy - small_h),
               "lockring": (lx + 7, cy - 40), "freehub": (ex - 10, cy + 36), "centre": (cx, cy)}
    return out, anchors


def drivetrain(front=(50, 34), cog=17, accent="chain"):
    """Side view: rear cassette (left), chainrings (right), chain on the chosen cog. viewBox 0 0 950 560."""
    out = ""
    k = 5.6
    rx, ry, fx, fy = 210, 300, 690, 330
    for t in (34, 27, 21, 15, 11):
        s, _ = sprocket(rx, ry, t, k=k, sw=1.2)
        out += s
    s, Rc = sprocket(rx, ry, cog, k=k, sw=2.4)
    out += s
    for t in sorted(front, reverse=True):
        s, _ = sprocket(fx, fy, t, k=k, sw=2.2 if t == max(front) else 1.6)
        out += s
    Rf = max(front) * k / 2
    out += f'<circle cx="{fx}" cy="{fy}" r="22" fill="{PAPER}" stroke="{INK}" stroke-width="2.2"/>'
    out += f'<path d="M{fx} {fy} L{fx - 70} {fy + 150}" stroke="{INK}" stroke-width="12" stroke-linecap="round"/><path d="M{fx} {fy} L{fx - 70} {fy + 150}" stroke="{PAPER}" stroke-width="6" stroke-linecap="round"/>'
    # chain: top run from top of chainring to top of cog; bottom run via derailleur pulleys
    p1, p2 = (rx + 60, ry + Rc + 70), (rx + 20, ry + Rc + 120)
    col = ACCENT if accent == "chain" else INK
    chain = (f"M{fx} {fy - Rf} L{rx} {ry - Rc} A{Rc} {Rc} 0 0 0 {rx - Rc} {ry} A{Rc} {Rc} 0 0 0 {rx + Rc * .6:.1f} {ry + Rc * .8:.1f} "
             f"L{p1[0]} {p1[1] - 14} A14 14 0 0 1 {p1[0] + 4} {p1[1] + 13} L{p2[0]} {p2[1] - 14} A14 14 0 0 0 {p2[0] + 2} {p2[1] + 14} L{fx} {fy + Rf}")
    out += f'<path d="{chain}" fill="none" stroke="{INK}" stroke-width="7.5" stroke-linejoin="round"/>'
    out += f'<path d="{chain}" fill="none" stroke="{col}" stroke-width="3.6" stroke-linejoin="round" stroke-dasharray="10 2.5"/>'
    for (x, y) in (p1, p2):
        out += f'<circle cx="{x}" cy="{y}" r="14" fill="{PAPER}" stroke="{INK}" stroke-width="2"/><circle cx="{x}" cy="{y}" r="3" fill="{INK}"/>'
    out += line(rx - 120, ry, fx + 150, ry, "centre") + line(rx, ry - 120, rx, ry + 120, "centre") + line(fx, fy - 170, fx, fy + 170, "centre")
    anchors = {"chainring": (fx + Rf * .7, fy - Rf * .7), "cog": (rx - Rc * .7, ry - Rc * .7), "cassette": (rx - 34 * k / 2 * .7, ry + 34 * k / 2 * .7),
               "chain_top": ((fx + rx) / 2, (fy - Rf + ry - Rc) / 2), "rear": (rx, ry), "front": (fx, fy), "pulley": p2}
    return out, anchors


def logo_mark():
    """The page mark: a question mark whose dot is a wheel, drafted. viewBox ~ 0 0 950 760."""
    ox, oy = 475 - 548, -150   # shift avatar geometry into view
    q = f"M{368+ox} {400+oy} C{368+ox} {262+oy} {452+ox} {188+oy} {548+ox} {188+oy} C{652+ox} {188+oy} {724+ox} {258+oy} {724+ox} {352+oy} C{724+ox} {430+oy} {680+ox} {474+oy} {616+ox} {512+oy} C{566+ox} {542+oy} {548+ox} {572+oy} {548+ox} {628+oy} L{548+ox} {668+oy}"
    out = f'<path d="{q}" fill="none" stroke="{INK}" stroke-width="104" stroke-linecap="round" stroke-linejoin="round"/>'
    out += f'<path d="{q}" fill="none" stroke="{ACCENT}" stroke-width="96" stroke-linecap="round" stroke-linejoin="round"/>'
    out += f'<path d="{q}" fill="none" stroke="{BLUE}" stroke-width="1" stroke-dasharray="22 5 3 5"/>'
    out += wheel(548 + ox, 838 + oy, 92, spokes=16)
    cx = 548 + ox
    out += line(cx, 120 + oy, cx, 950 + oy, "centre")
    anchors = {"hook": (724 + ox - 48, 300 + oy), "dot": (548 + ox + 66, 838 + oy - 64), "stem": (548 + ox, 600 + oy)}
    return out, anchors
