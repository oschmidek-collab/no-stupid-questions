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


def label(x, y, title, value=None, anchor="end", color=BLUE, halo=False):
    """Two-line annotation label: Hebrew title (bold) above a mono value. anchor is LTR semantics."""
    h = f' paint-order="stroke" stroke="{PAPER}" stroke-width="10" stroke-linejoin="round"' if halo else ""
    out = f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Assistant" font-weight="700" font-size="27" fill="{color}"{h}>{esc(title)}</text>'
    if value is not None:
        out += f'<text x="{x}" y="{y + 38}" text-anchor="{anchor}" font-family="Plex" font-size="24" fill="{color}"{h}>{esc(value)}</text>'
    return out


def leader(points, title, value=None, side="right", shelf=230, color=BLUE, halo=False):
    """Leader from an anchor dot through elbow points, ending in a horizontal shelf carrying the label.
    side='right': shelf extends right from the last point, label right-aligned at its end.
    side='left' : shelf extends left, label left-aligned at its end."""
    (ax, ay), *rest = points
    ex, ey = rest[-1] if rest else (ax, ay)
    sx = ex + shelf if side == "right" else ex - shelf
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points) + f" L{sx:.1f} {ey:.1f}"
    under = ""
    if halo:
        under = f'<path d="{d}" fill="none" stroke="{PAPER}" stroke-width="6" stroke-opacity=".85" stroke-linejoin="round"/>'
    out = under + f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.4" stroke-linejoin="round"/>'
    out += f'<circle cx="{ax}" cy="{ay}" r="5.5" fill="{color}"/><circle cx="{ax}" cy="{ay}" r="10" fill="none" stroke="{color}" stroke-width="1"/>'
    lx, anchor = (sx, "end") if side == "right" else (sx, "start")
    out += label(lx, ey - 14, title, None, anchor, color, halo)
    if value is not None:
        out += f'<text x="{lx}" y="{ey + 32}" text-anchor="{anchor}" font-family="Plex" font-size="24" fill="{color}"' + (f' paint-order="stroke" stroke="{PAPER}" stroke-width="10"' if halo else "") + f'>{esc(value)}</text>'
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
