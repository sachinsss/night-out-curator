"""Vector illustration primitives for the poster (PDF coordinates, y up)."""
import math
import random

from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics

NAVY = HexColor("#141B34")
INDIGO = HexColor("#22305E")
DUSK = HexColor("#3A2D5F")
PLUM = HexColor("#52305F")
DEEP_TEAL = HexColor("#0E3B43")
WARM = HexColor("#FFC857")
ORANGE = HexColor("#F2A541")
TERRA = HexColor("#E4572E")
MINT = HexColor("#7FD6A8")
GREEN = HexColor("#2E9A6B")
SKY = HexColor("#3A8FB7")
CREAM = HexColor("#F7F3E8")
RED = HexColor("#E0453A")
INK = HexColor("#1D2A25")
PANTS = HexColor("#28324F")

SKINS = [HexColor("#F2C9A0"), HexColor("#D9A06F"), HexColor("#8D5A3B"), HexColor("#F5D6B8")]
HAIRS = [HexColor("#2B1B12"), HexColor("#1B1B1B"), HexColor("#5A3A22"), HexColor("#B5651D")]


def rr(c, x, y, w, h, r, fill=None, stroke=None, lw=2):
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r, stroke=0 if stroke is None else 1, fill=0 if fill is None else 1)


def circ(c, x, y, r, fill=None, stroke=None, lw=2):
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.circle(x, y, r, stroke=0 if stroke is None else 1, fill=0 if fill is None else 1)


def poly(c, pts, fill=None, stroke=None, lw=2):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    c.drawPath(p, stroke=0 if stroke is None else 1, fill=0 if fill is None else 1)


def line(c, x1, y1, x2, y2, color, lw=3, cap=1, dash=None):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.setLineCap(cap)
    if dash:
        c.setDash(*dash)
    c.line(x1, y1, x2, y2)
    c.setDash()
    c.setLineCap(0)


def alpha(c, a):
    c.setFillAlpha(a)
    c.setStrokeAlpha(a)


def sparkle(c, x, y, r, color=WARM):
    k = r * 0.28
    poly(c, [(x, y + r), (x + k, y + k), (x + r, y), (x + k, y - k), (x, y - r), (x - k, y - k), (x - r, y), (x - k, y + k)], fill=color)


# ------------------------------------------------------------ characters
def person(c, x, y, h, shirt, skin, hair, mood="happy", hair_style=0, leaf=False, phone=False, arm_up=False):
    s = h / 200.0
    c.saveState()
    c.translate(x, y)
    c.scale(s, s)
    c.setFillColor(black)
    alpha(c, 0.28)
    c.ellipse(-38, -6, 38, 9, stroke=0, fill=1)
    alpha(c, 1)
    rr(c, -22, 8, 18, 64, 8, PANTS)
    rr(c, 4, 8, 18, 64, 8, PANTS)
    rr(c, -28, 0, 27, 13, 6, HexColor("#F4F1EA"))
    rr(c, 1, 0, 27, 13, 6, HexColor("#F4F1EA"))
    if hair_style == 1:
        rr(c, -33, 116, 66, 62, 18, hair)
    rr(c, -32, 66, 64, 76, 20, shirt)
    c.setStrokeColor(shirt)
    c.setLineWidth(15)
    c.setLineCap(1)
    c.line(-32, 128, -50, 88)
    if arm_up:
        c.line(32, 128, 54, 172)
        hand = (54, 176)
    else:
        c.line(32, 128, 50, 88)
        hand = (50, 84)
    c.setLineCap(0)
    circ(c, -50, 84, 8.5, skin)
    circ(c, hand[0], hand[1], 8.5, skin)
    if phone:
        rr(c, hand[0] - 4, hand[1] - 4, 18, 30, 4, HexColor("#101424"))
        rr(c, hand[0] - 1, hand[1], 12, 22, 2, HexColor("#7FD6FF"))
    circ(c, -29, 164, 5.5, skin)
    circ(c, 29, 164, 5.5, skin)
    circ(c, 0, 164, 29, skin)
    c.setFillColor(hair)
    p = c.beginPath()
    p.moveTo(-30, 164)
    p.curveTo(-37, 214, 37, 214, 30, 164)
    p.curveTo(16, 184, -16, 184, -30, 164)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    if hair_style == 3:
        circ(c, 0, 207, 13, hair)
    ink = HexColor("#2A1A14")
    if mood == "dizzy":
        c.setStrokeColor(ink)
        c.setLineWidth(3)
        for ex in (-11, 11):
            c.line(ex - 5, 159, ex + 5, 169)
            c.line(ex - 5, 169, ex + 5, 159)
    else:
        circ(c, -11, 164, 3.8, ink)
        circ(c, 11, 164, 3.8, ink)
    c.setStrokeColor(ink)
    c.setLineWidth(3.2)
    c.setLineCap(1)
    p = c.beginPath()
    if mood == "happy":
        p.moveTo(-10, 150)
        p.curveTo(-5, 140, 5, 140, 10, 150)
    elif mood == "sad":
        p.moveTo(-9, 144)
        p.curveTo(-4, 153, 4, 153, 9, 144)
    else:
        p.moveTo(-9, 146)
        p.curveTo(-4, 152, 4, 140, 9, 146)
    c.drawPath(p, stroke=1, fill=0)
    if mood in ("sad", "dizzy"):
        c.line(-17, 177, -6, 173)
        c.line(17, 177, 6, 173)
    c.setLineCap(0)
    if leaf:
        c.setFillColor(HexColor("#2E9A6B"))
        p = c.beginPath()
        p.moveTo(6, 92)
        p.curveTo(8, 114, 28, 118, 34, 116)
        p.curveTo(32, 98, 20, 88, 6, 92)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        line(c, 9, 94, 28, 112, white, lw=2)
    c.restoreState()


def robot(c, x, y, h, body=GREEN, glow=False, mood="happy", wave=False, tool=None):
    s = h / 200.0
    c.saveState()
    c.translate(x, y)
    c.scale(s, s)
    if glow:
        for r, a in ((135, 0.07), (112, 0.09), (90, 0.12)):
            c.setFillColor(MINT)
            alpha(c, a)
            c.circle(0, 110, r, stroke=0, fill=1)
        alpha(c, 1)
    c.setFillColor(black)
    alpha(c, 0.28)
    c.ellipse(-40, -6, 40, 9, stroke=0, fill=1)
    alpha(c, 1)
    dark = HexColor("#143D2E") if body == GREEN else HexColor("#7A2A18")
    rr(c, -32, 0, 28, 20, 9, dark)
    rr(c, 4, 0, 28, 20, 9, dark)
    rr(c, -40, 16, 80, 82, 22, body)
    rr(c, -26, 28, 52, 46, 12, HexColor("#E8F5EC") if body == GREEN else HexColor("#FBE3DB"))
    pin(c, 0, 34, 30, body)
    c.setStrokeColor(body)
    c.setLineWidth(15)
    c.setLineCap(1)
    c.line(-40, 84, -72, 58)
    if wave:
        c.line(40, 84, 74, 118)
        hand = (74, 122)
    else:
        c.line(40, 84, 72, 62)
        hand = (72, 58)
    c.setLineCap(0)
    circ(c, -72, 55, 9.5, white)
    circ(c, hand[0], hand[1], 9.5, white)
    if tool == "magnifier":
        magnifier(c, hand[0] + 14, hand[1] + 22, 24, WARM)
    rr(c, -10, 96, 20, 12, 3, dark)
    rr(c, -62, 128, 12, 28, 5, body)
    rr(c, 50, 128, 12, 28, 5, body)
    rr(c, -50, 104, 100, 76, 26, white, body, 4)
    rr(c, -38, 114, 76, 54, 18, NAVY)
    eye = MINT if body == GREEN else HexColor("#FFB4A0")
    circ(c, -17, 142, 9, eye)
    circ(c, 17, 142, 9, eye)
    circ(c, -14, 146, 3, white)
    circ(c, 20, 146, 3, white)
    c.setStrokeColor(eye)
    c.setLineWidth(4)
    c.setLineCap(1)
    p = c.beginPath()
    if mood == "happy":
        p.moveTo(-13, 127)
        p.curveTo(-6, 118, 6, 118, 13, 127)
    elif mood == "worried":
        p.moveTo(-12, 122)
        p.curveTo(-5, 128, 5, 116, 12, 122)
    else:
        p.moveTo(-12, 123)
        p.lineTo(12, 123)
    c.drawPath(p, stroke=1, fill=0)
    if mood == "stern":
        c.line(-27, 160, -8, 154)
        c.line(27, 160, 8, 154)
    c.setLineCap(0)
    c.setStrokeColor(body)
    c.setLineWidth(5)
    c.line(0, 180, 0, 198)
    circ(c, 0, 206, 10, WARM)
    c.restoreState()


# ------------------------------------------------------------ icons
def pin(c, x, y, s, color=TERRA, hole=white):
    k = s / 40.0
    c.saveState()
    c.translate(x, y)
    c.scale(k, k)
    poly(c, [(-12, 22), (12, 22), (0, 0)], fill=color)
    circ(c, 0, 28, 14, color)
    circ(c, 0, 28, 6, hole)
    c.restoreState()


def magnifier(c, x, y, r, color=WARM):
    line(c, x - r * 0.7, y - r * 0.7, x - r * 1.5, y - r * 1.5, HexColor("#8A5A2B"), lw=r * 0.45)
    circ(c, x, y, r, fill=None, stroke=color, lw=r * 0.3)
    c.setFillColor(white)
    alpha(c, 0.25)
    c.circle(x, y, r * 0.85, stroke=0, fill=1)
    alpha(c, 1)


def cloud(c, x, y, s, color=white):
    c.setFillColor(color)
    c.circle(x - s * 0.28, y, s * 0.26, stroke=0, fill=1)
    c.circle(x + s * 0.02, y + s * 0.1, s * 0.34, stroke=0, fill=1)
    c.circle(x + s * 0.32, y, s * 0.24, stroke=0, fill=1)
    c.roundRect(x - s * 0.5, y - s * 0.26, s * 1.0, s * 0.3, s * 0.15, stroke=0, fill=1)


def sun(c, x, y, r, color=WARM):
    for i in range(8):
        a = i * math.pi / 4
        line(c, x + math.cos(a) * r * 1.3, y + math.sin(a) * r * 1.3, x + math.cos(a) * r * 1.75, y + math.sin(a) * r * 1.75, color, lw=r * 0.28)
    circ(c, x, y, r, color)


def clock(c, x, y, r):
    circ(c, x, y, r, white, NAVY, 4)
    line(c, x, y, x, y + r * 0.62, NAVY, lw=r * 0.12)
    line(c, x, y, x + r * 0.45, y - r * 0.15, TERRA, lw=r * 0.12)
    circ(c, x, y, r * 0.08, NAVY)


def bus(c, x, y, w):
    h = w * 0.55
    rr(c, x - w / 2, y - h / 2, w, h, w * 0.1, ORANGE)
    for i in range(3):
        rr(c, x - w / 2 + w * 0.08 + i * w * 0.29, y + h * 0.02, w * 0.24, h * 0.32, 4, HexColor("#DFF3FF"))
    rr(c, x - w / 2, y - h * 0.14, w, h * 0.1, 0, HexColor("#C77F1F"))
    circ(c, x - w * 0.28, y - h / 2, w * 0.1, NAVY)
    circ(c, x + w * 0.28, y - h / 2, w * 0.1, NAVY)
    circ(c, x - w * 0.28, y - h / 2, w * 0.04, white)
    circ(c, x + w * 0.28, y - h / 2, w * 0.04, white)


def coin(c, x, y, r, text="$", font="UI-B"):
    circ(c, x, y, r, WARM, HexColor("#C98B1A"), r * 0.12)
    c.setFillColor(HexColor("#8A5A0E"))
    c.setFont(font, r * 1.25)
    c.drawCentredString(x, y - r * 0.42, text)


def doc(c, x, y, w, h, lines=3, accent=MINT):
    rr(c, x - w / 2, y - h / 2, w, h, 6, white, HexColor("#C9C4B2"), 2)
    for i in range(lines):
        yy = y + h / 2 - h * (0.2 + i * (0.6 / max(lines, 1)))
        col = accent if i == 1 else HexColor("#B9B5A5")
        line(c, x - w * 0.34, yy, x + w * (0.34 if i != lines - 1 else 0.1), yy, col, lw=max(3, h * 0.06))


def footsteps(c, x, y, s, color=WARM):
    for dx, dy, a in ((-0.28, -0.2, -20), (0.28, 0.25, -20)):
        c.saveState()
        c.translate(x + dx * s, y + dy * s)
        c.rotate(a)
        c.setFillColor(color)
        c.ellipse(-s * 0.14, -s * 0.26, s * 0.14, s * 0.26, stroke=0, fill=1)
        c.restoreState()


def shield_check(c, x, y, s, color=GREEN, mark=white):
    k = s / 40.0
    c.saveState()
    c.translate(x, y)
    c.scale(k, k)
    p = c.beginPath()
    p.moveTo(0, 22)
    p.curveTo(8, 20, 16, 20, 18, 18)
    p.curveTo(18, 4, 12, -12, 0, -22)
    p.curveTo(-12, -12, -18, 4, -18, 18)
    p.curveTo(-16, 20, -8, 20, 0, 22)
    p.close()
    c.setFillColor(color)
    c.drawPath(p, stroke=0, fill=1)
    c.setStrokeColor(mark)
    c.setLineWidth(5)
    c.setLineCap(1)
    c.setLineJoin(1)
    q = c.beginPath()
    q.moveTo(-8, 0)
    q.lineTo(-2, -7)
    q.lineTo(9, 8)
    c.drawPath(q, stroke=1, fill=0)
    c.restoreState()
    c.setLineCap(0)


def check_dot(c, x, y, r, ok=True):
    circ(c, x, y, r, GREEN if ok else RED)
    c.setStrokeColor(white)
    c.setLineWidth(r * 0.24)
    c.setLineCap(1)
    c.setLineJoin(1)
    if ok:
        p = c.beginPath()
        p.moveTo(x - r * 0.5, y)
        p.lineTo(x - r * 0.1, y - r * 0.42)
        p.lineTo(x + r * 0.52, y + r * 0.4)
        c.drawPath(p, stroke=1, fill=0)
    else:
        d = r * 0.42
        c.line(x - d, y - d, x + d, y + d)
        c.line(x - d, y + d, x + d, y - d)
    c.setLineCap(0)


def plate(c, x, y, r):
    circ(c, x, y, r, white, HexColor("#C9C4B2"), 3)
    circ(c, x, y, r * 0.62, None, HexColor("#E3DFD0"), 2)
    line(c, x - r * 1.45, y - r * 0.8, x - r * 1.45, y + r * 0.9, HexColor("#DAD6C8"), lw=r * 0.12)
    line(c, x + r * 1.45, y - r * 0.8, x + r * 1.45, y + r * 0.9, HexColor("#DAD6C8"), lw=r * 0.12)


def cone(c, x, y, s):
    poly(c, [(x - s * 0.28, y + s * 0.1), (x + s * 0.28, y + s * 0.1), (x, y - s * 0.55)], fill=HexColor("#E0A458"))
    circ(c, x, y + s * 0.2, s * 0.32, HexColor("#F7B7C8"))
    circ(c, x - s * 0.12, y + s * 0.5, s * 0.2, HexColor("#FFF0C9"))
    circ(c, x + s * 0.02, y + s * 0.72, s * 0.08, RED)


def closed_sign(c, x, y, w):
    h = w * 0.42
    line(c, x - w * 0.3, y + h / 2, x - w * 0.1, y + h / 2 + w * 0.3, HexColor("#D8D2BF"), lw=2.5)
    line(c, x + w * 0.3, y + h / 2, x + w * 0.1, y + h / 2 + w * 0.3, HexColor("#D8D2BF"), lw=2.5)
    rr(c, x - w / 2, y - h / 2, w, h, 8, RED, white, 3)
    c.setFillColor(white)
    c.setFont("UI-B", w * 0.22)
    c.drawCentredString(x, y - w * 0.075, "CLOSED")


def building(c, x, y, w, h, color, rng, lit=0.35):
    rr(c, x, y, w, h, 0, color)
    cols = max(int(w // 18), 1)
    rows = max(int(h // 26), 1)
    for i in range(cols):
        for j in range(rows):
            if rng.random() < lit:
                c.setFillColor(WARM)
                alpha(c, 0.8)
                c.rect(x + 8 + i * (w - 16) / cols, y + 10 + j * (h - 20) / rows, 8, 11, stroke=0, fill=1)
                alpha(c, 1)


def palm(c, x, y, h, color=HexColor("#1D4A3B")):
    c.setStrokeColor(HexColor("#4A3A32"))
    c.setLineWidth(h * 0.06)
    c.setLineCap(1)
    p = c.beginPath()
    p.moveTo(x, y)
    p.curveTo(x + h * 0.08, y + h * 0.35, x - h * 0.06, y + h * 0.7, x + h * 0.04, y + h)
    c.drawPath(p, stroke=1, fill=0)
    c.setLineCap(0)
    tx, ty = x + h * 0.04, y + h
    for a in (20, 55, 90, 125, 160):
        c.saveState()
        c.translate(tx, ty)
        c.rotate(a - 90)
        c.setFillColor(color)
        q = c.beginPath()
        q.moveTo(0, 0)
        q.curveTo(h * 0.12, h * 0.3, h * 0.3, h * 0.3, h * 0.42, h * 0.1)
        q.curveTo(h * 0.28, h * 0.18, h * 0.12, h * 0.12, 0, 0)
        c.drawPath(q, stroke=0, fill=1)
        c.restoreState()


def streetlamp(c, x, y, h):
    c.setFillColor(WARM)
    for r, a in ((70, 0.06), (48, 0.1), (28, 0.18)):
        alpha(c, a)
        c.circle(x, y + h, r, stroke=0, fill=1)
    alpha(c, 1)
    line(c, x, y, x, y + h - 8, HexColor("#0F1428"), lw=7)
    circ(c, x, y + h, 11, WARM)


def night_backdrop(c, x, yb, w, h, seed, ground=62, moon=True, bg_hex="#22305E"):
    rng = random.Random(seed)
    c.setFillColor(white)
    for _ in range(26):
        alpha(c, rng.uniform(0.3, 0.9))
        c.circle(x + rng.uniform(10, w - 10), yb + rng.uniform(h * 0.45, h - 8), rng.uniform(1, 2.6), stroke=0, fill=1)
    alpha(c, 1)
    if moon:
        circ(c, x + w - 62, yb + h - 52, 26, HexColor("#FFE9A8"))
        circ(c, x + w - 52, yb + h - 44, 24, HexColor(bg_hex))
    cx = x - 10
    while cx < x + w:
        bw = rng.randint(42, 78)
        bh = rng.randint(50, 118)
        building(c, cx, yb + ground - 4, bw, bh, HexColor("#161E3E"), rng)
        cx += bw + rng.randint(2, 10)
    rr(c, x - 4, yb - 4, w + 8, ground + 4, 0, HexColor("#262C4E"))
    c.setFillColor(HexColor("#3A4272"))
    c.rect(x - 4, yb + ground - 4, w + 8, 5, stroke=0, fill=1)


def bubble(c, x, y, w, h, tip, fill=white, stroke=NAVY, tail_x=None, lw=3.5):
    tx = tail_x if tail_x is not None else min(max(tip[0], x + 30), x + w - 30)
    poly(c, [(tx - 14, y + 2), (tx + 14, y + 2), tip], fill=fill, stroke=stroke, lw=lw)
    rr(c, x, y, w, h, 20, fill, stroke, lw)
    c.setFillColor(fill)
    c.rect(tx - 12, y - 1, 24, lw + 3, stroke=0, fill=1)


def stamp(c, x, y, text, color, w, h, size, rot=-10):
    c.saveState()
    c.translate(x, y)
    c.rotate(rot)
    rr(c, -w / 2, -h / 2, w, h, 10, None, color, 7)
    rr(c, -w / 2 + 9, -h / 2 + 9, w - 18, h - 18, 6, None, color, 2.5)
    c.setFillColor(color)
    c.setFont("UI-B", size)
    c.drawCentredString(0, -size * 0.34, text)
    c.restoreState()


def sticky(c, x, y, w, h, rot=-5):
    c.saveState()
    c.translate(x, y)
    c.rotate(rot)
    c.setFillColor(black)
    alpha(c, 0.25)
    c.rect(-w / 2 + 5, -h / 2 - 5, w, h, stroke=0, fill=1)
    alpha(c, 1)
    rr(c, -w / 2, -h / 2, w, h, 4, HexColor("#FFE27A"))
    c.restoreState()


def lightbulb(c, x, y, r):
    for rr_, a in ((r * 2.2, 0.08), (r * 1.7, 0.12)):
        c.setFillColor(WARM)
        alpha(c, a)
        c.circle(x, y, rr_, stroke=0, fill=1)
    alpha(c, 1)
    circ(c, x, y, r, WARM)
    rr(c, x - r * 0.45, y - r * 1.5, r * 0.9, r * 0.6, 3, HexColor("#8F95A8"))
    for a in (30, 90, 150):
        ang = math.radians(a)
        line(c, x + math.cos(ang) * r * 1.35, y + math.sin(ang) * r * 1.35, x + math.cos(ang) * r * 1.8, y + math.sin(ang) * r * 1.8, WARM, lw=3)


def dashed_curve(c, p0, p1, p2, p3, color=WARM, lw=5, dash=(2, 12), head=True):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.setLineCap(1)
    c.setDash(*dash)
    p = c.beginPath()
    p.moveTo(*p0)
    p.curveTo(*p1, *p2, *p3)
    c.drawPath(p, stroke=1, fill=0)
    c.setDash()
    c.setLineCap(0)
    if head:
        a = math.atan2(p3[1] - p2[1], p3[0] - p2[0])
        hl = lw * 3.2
        poly(c, [p3, (p3[0] - hl * math.cos(a) + hl * 0.55 * math.sin(a), p3[1] - hl * math.sin(a) - hl * 0.55 * math.cos(a)),
                 (p3[0] - hl * math.cos(a) - hl * 0.55 * math.sin(a), p3[1] - hl * math.sin(a) + hl * 0.55 * math.cos(a))], fill=color)


def glyph(c, kind, x, y, bg):
    """White glyph on a coloured badge; about 44 pt across."""
    c.saveState()
    c.translate(x, y)
    if kind == "pin":
        poly(c, [(-11, 2), (11, 2), (0, -20)], fill=white)
        circ(c, 0, 8, 13, white)
        circ(c, 0, 8, 5, bg)
    elif kind == "doc":
        rr(c, -14, -18, 28, 36, 4, white)
        for i, yy in enumerate((8, 0, -8)):
            line(c, -8, yy, 8 if i < 2 else 2, yy, bg, lw=3.5)
    elif kind == "sun":
        sun(c, 0, 0, 9, white)
    elif kind == "plan":
        line(c, -14, -8, 0, 8, white, lw=4)
        line(c, 0, 8, 14, -8, white, lw=4)
        for px, py in ((-14, -8), (0, 8), (14, -8)):
            circ(c, px, py, 6, white)
    elif kind == "steps":
        footsteps(c, 0, 0, 44, white)
    elif kind == "shield":
        shield_check(c, 0, 0, 44, white, bg)
    c.restoreState()
