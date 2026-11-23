"""Builds the 24x36 in portrait vector poster: python poster/make_poster.py (needs reportlab, pillow)."""
import math
import pathlib
import random

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

import art as A

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE / "Group15_Poster.pdf"
REPO_URL = "https://github.com/sachinsss/night-out-curator"

FONTS = pathlib.Path("C:/Windows/Fonts")
for name, f in [("UI", "segoeui.ttf"), ("UI-B", "segoeuib.ttf"), ("UI-I", "segoeuii.ttf"), ("UI-BI", "segoeuiz.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / f)))
pdfmetrics.registerFontFamily("UI", normal="UI", bold="UI-B", italic="UI-I", boldItalic="UI-BI")

W, H = 24 * 72, 36 * 72
M, G = 48, 30
CW = W - 2 * M

NAVY = HexColor("#1B2142")
BODY = HexColor("#2B2F45")
AMBER = HexColor("#F5B83D")
AMBER_L = HexColor("#FCEFCF")
AMBER_T = HexColor("#6B4300")
BLUE = HexColor("#2F6F9F")
BLUE_L = HexColor("#DCE9F4")
BLUE_T = HexColor("#1B4A70")
CORAL = HexColor("#E0533F")
CORAL_L = HexColor("#FBE3DE")
CORAL_T = HexColor("#8A2416")
GREEN = HexColor("#2E9E6B")
GREEN_L = HexColor("#DDF1E6")
GREEN_T = HexColor("#14573A")
INK = BODY
MUTED = HexColor("#3B4058")
BG = HexColor("#F6F3EC")
BORDER = HexColor("#CBD0E0")
PALE = HexColor("#EEF0F7")
SUB = HexColor("#D9DEEE")

PH, CAP, GROUND, PGAP = 348, 58, 62, 18


def st(size, color=INK, lead=None, align=0, font="UI"):
    return ParagraphStyle("s", fontName=font, fontSize=size, leading=lead or size * 1.27, textColor=color, alignment=align)


def para(c, html, x, top, w, style):
    p = Paragraph(html, style)
    _, h = p.wrap(w, 10000)
    p.drawOn(c, x, H - top - h)
    return h


def tbox(c, html, x, ytop, w, style):
    """Paragraph whose top edge is at PDF-y ytop; returns its height."""
    p = Paragraph(html, style)
    _, h = p.wrap(w, 10000)
    p.drawOn(c, x, ytop - h)
    return h


def card(c, x, top, w, h, title, size=40):
    c.setFillColor(white)
    c.setStrokeColor(BORDER)
    c.setLineWidth(2)
    c.roundRect(x, H - top - h, w, h, 16, fill=1, stroke=1)
    c.setFillColor(AMBER)
    c.roundRect(x + 24, H - top - 68, 10, 48, 4, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("UI-B", size)
    c.drawString(x + 50, H - top - 56, title)
    return top + 90


def pill(c, x, top, text, fg, bg, size=22, padx=14, h=None, font="UI-B"):
    h = h or size * 1.7
    w = pdfmetrics.stringWidth(text, font, size) + 2 * padx
    c.setFillColor(bg)
    c.roundRect(x, H - top - h, w, h, h / 2, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont(font, size)
    c.drawString(x + padx, H - top - h + (h - size * 0.72) / 2, text)
    return w


def arrow(c, x1, y1, x2, y2, color=BODY, width=5, head=16):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(width)
    c.setLineCap(0)
    a = math.atan2(y2 - y1, x2 - x1)
    c.line(x1, y1, x2 - head * 0.8 * math.cos(a), y2 - head * 0.8 * math.sin(a))
    p = c.beginPath()
    p.moveTo(x2, y2)
    for s in (1, -1):
        p.lineTo(x2 - head * math.cos(a) + s * head * 0.55 * math.sin(a), y2 - head * math.sin(a) - s * head * 0.55 * math.cos(a))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


# ------------------------------------------------------------------ header / footer
def header(c):
    hh = 232
    c.setFillColor(NAVY)
    c.rect(0, H - hh, W, hh, fill=1, stroke=0)
    c.setFillColor(AMBER)
    c.rect(0, H - hh - 10, W, 10, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("UI-B", 92)
    c.drawString(M + 4, H - 110, "Night-Out Curator")
    c.setFont("UI", 34)
    c.setFillColor(SUB)
    c.drawString(M + 8, H - 166, "Evidence-grounded multi-agent outing planner \u00b7 Phoenix / Tempe")
    c.setFont("UI-I", 29)
    c.setFillColor(white)
    c.drawString(M + 8, H - 214, "Plain-English request in. Checked, sourced, multi-stop plan out.")
    rx = W - M
    c.setFillColor(white)
    c.setFont("UI-B", 32)
    c.drawRightString(rx, H - 58, "CSE 598 Capstone  |  Group 15")
    c.setFont("UI", 22)
    c.setFillColor(SUB)
    c.drawRightString(rx, H - 98, "Sachin Shivanand Shankarikoppa \u00b7 Sushanth Urubailu Vasudeva")
    c.drawRightString(rx, H - 126, "Vivek Vidyadhar Kamath \u00b7 Naga Sai Rama Srikar Vinjanampati")
    c.drawRightString(rx, H - 154, "Sri Sai Chetana Reddy Janagan")
    c.setFont("UI", 22)
    c.setFillColor(white)
    c.drawRightString(rx, H - 192, "Stakeholder: Mitul Krishna Balamurugan")
    return hh + 10


def footer(c, top):
    fh = H - top
    c.setFillColor(NAVY)
    c.rect(0, 0, W, fh, fill=1, stroke=0)
    y1, y3 = fh - 40, 36
    c.setFillColor(white)
    c.setFont("UI-B", 26)
    c.drawString(M, y1, "Built with")
    c.setFont("UI", 23)
    c.setFillColor(SUB)
    c.drawString(M + 144, y1, "Python \u00b7 LangGraph \u00b7 LangChain \u00b7 Pydantic \u00b7 AWS Bedrock (LLM) \u00b7 Google Maps \u00b7 Geoapify \u00b7 OpenStreetMap \u00b7 Open-Meteo")
    c.setFont("UI-B", 22)
    c.setFillColor(white)
    c.drawString(M, y3, REPO_URL.replace("https://", ""))


# ------------------------------------------------------------------ illustrated strips
def ribbon(c, top, title, sub):
    base = H - top - 46
    c.setFillColor(AMBER)
    c.roundRect(M + 2, base - 8, 10, 58, 4, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("UI-B", 52)
    c.drawString(M + 28, base, title)
    c.setFillColor(MUTED)
    c.setFont("UI-I", 28)
    c.drawRightString(W - M, base + 2, sub)
    return top + 62


def strip(c, top, panels):
    pw = (CW - 2 * PGAP) / 3
    yb = H - top - PH
    for i, (draw, c1, c2, cap) in enumerate(panels):
        x = M + i * (pw + PGAP)
        c.saveState()
        p = c.beginPath()
        p.roundRect(x, yb, pw, PH, 24)
        c.clipPath(p, stroke=0, fill=0)
        c.linearGradient(x, yb + PH, x, yb, (c1, c2))
        draw(c, x, yb, pw, PH)
        c.setFillColor(black)
        A.alpha(c, 0.55)
        c.rect(x, yb, pw, CAP, stroke=0, fill=1)
        A.alpha(c, 1)
        c.restoreState()
        fs = 29
        while pdfmetrics.stringWidth(cap, "UI-B", fs) > pw - 40:
            fs -= 1
        c.setFillColor(white)
        c.setFont("UI-B", fs)
        c.drawCentredString(x + pw / 2, yb + CAP / 2 - fs * 0.3, cap)
        c.setStrokeColor(white)
        c.setLineWidth(5)
        c.roundRect(x, yb, pw, PH, 24, stroke=1, fill=0)
    for i in range(2):
        gx = M + (i + 1) * pw + i * PGAP + PGAP / 2
        A.circ(c, gx, yb + PH / 2, 22, AMBER, white, 4)
        A.line(c, gx - 7, yb + PH / 2 + 10, gx + 5, yb + PH / 2, NAVY, lw=5)
        A.line(c, gx + 5, yb + PH / 2, gx - 7, yb + PH / 2 - 10, NAVY, lw=5)
    return top + PH


def tilt(c, x, y, rot, fn):
    c.saveState()
    c.translate(x, y)
    c.rotate(rot)
    fn()
    c.restoreState()


F = [A.SKY, A.ORANGE, HexColor("#7FB069"), A.TERRA]


def friends(c, x, y, h, picks, moods="happy", **kw):
    for i, (dx, shirt, sk, hr, style, extra) in enumerate(picks):
        opts = dict(mood=moods, hair_style=style)
        opts.update(extra)
        A.person(c, x + dx, y, h, shirt, A.SKINS[sk], A.HAIRS[hr], **opts)


def tilt_s(c, x, y, rot, scale, fn):
    c.saveState()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(scale, scale)
    fn()
    c.restoreState()


def sc_plan(c, x, yb, w, h):
    A.night_backdrop(c, x, yb, w, h, 11)
    A.palm(c, x + 30, yb + GROUND, 140)
    A.streetlamp(c, x + w - 40, yb + GROUND, 185)
    friends(c, x, yb + GROUND - 4, 166, [
        (92, F[0], 0, 0, 0, {}),
        (190, F[1], 1, 1, 1, {}),
        (288, F[2], 2, 1, 3, dict(leaf=True)),
        (386, F[3], 3, 3, 0, dict(arm_up=True)),
    ])
    A.bubble(c, x + 20, yb + 246, 400, 96, tip=(x + 250, yb + 232))
    tbox(c, "Dinner + dessert, chill, <b>$40 each</b>, <b>one vegan!</b>", x + 38, yb + 330, 366, st(30, A.NAVY, 36))


def sc_chaos(c, x, yb, w, h):
    A.night_backdrop(c, x, yb, w, h, 12, moon=False)
    cx = x + w / 2

    def mapcard():
        A.rr(c, -62, -44, 124, 88, 8, white)
        A.line(c, -52, -12, 50, 10, HexColor("#CFCABA"), lw=8)
        A.line(c, -10, -40, 6, 40, HexColor("#CFCABA"), lw=8)
        A.pin(c, 18, -6, 40, A.TERRA)

    def menucard():
        A.rr(c, -52, -48, 104, 96, 8, HexColor("#FFF6DC"))
        c.setFillColor(A.INK)
        c.setFont("UI-B", 19)
        c.drawCentredString(0, 24, "MENU")
        A.line(c, -34, 10, 34, 10, HexColor("#CFC6A5"), lw=3)
        c.setFillColor(A.TERRA)
        c.setFont("UI-B", 38)
        c.drawCentredString(0, -28, "$$$")

    tilt_s(c, x + 112, yb + 272, 8, 1.15, mapcard)
    tilt_s(c, x + 430, yb + 270, -8, 1.15, menucard)
    A.clock(c, x + 62, yb + 160, 38)
    A.bus(c, x + 150, yb + 138, 104)
    A.cloud(c, x + 462, yb + 172, 104)
    for dx in (-26, 0, 26):
        A.line(c, x + 462 + dx, yb + 138, x + 454 + dx, yb + 116, A.SKY, lw=5)
    tilt(c, x + 372, yb + 104, 6, lambda: A.closed_sign(c, 0, 0, 104))
    A.person(c, cx, yb + GROUND - 4, 170, A.SKY, A.SKINS[0], A.HAIRS[0], mood="dizzy", phone=True)
    for sx, sy, sr in ((cx - 36, yb + 238, 12), (cx + 38, yb + 246, 15), (cx + 2, yb + 264, 11)):
        A.sparkle(c, sx, sy, sr)
    c.setFillColor(A.WARM)
    c.setFont("UI-B", 52)
    for qx, qy in ((x + 206, yb + 246), (x + 338, yb + 232), (x + 40, yb + 214)):
        c.drawCentredString(qx, qy, "?")


def sc_closed(c, x, yb, w, h):
    A.night_backdrop(c, x, yb, w, h, 13, moon=False)
    bx, by, bw_, bh_ = x + 14, yb + GROUND - 4, 226, 214
    A.rr(c, bx, by, bw_, bh_, 6, HexColor("#4A3B63"))
    sw_ = (bw_ + 16) / 7
    for i in range(7):
        col = A.RED if i % 2 == 0 else A.CREAM
        A.rr(c, bx - 8 + i * sw_, by + bh_ - 70, sw_, 58, 0, col)
        A.circ(c, bx - 8 + i * sw_ + sw_ / 2, by + bh_ - 70, sw_ / 2, col)
    A.rr(c, bx + 16, by + 30, 84, 90, 6, A.NAVY)
    A.rr(c, bx + 128, by, 82, 132, 6, HexColor("#1F1B33"))
    A.closed_sign(c, bx + 169, by + 72, 76)
    friends(c, x, yb + GROUND - 4, 150, [
        (296, F[0], 0, 0, 0, {}),
        (374, F[2], 2, 1, 3, dict(leaf=True)),
        (452, F[1], 1, 1, 1, {}),
    ], moods="sad")

    def receipt():
        A.poly(c, [(-44, 46), (44, 46), (44, -46), (30, -38), (16, -46), (2, -38), (-12, -46), (-28, -38), (-44, -46)], fill=white)
        c.setFillColor(A.TERRA)
        c.setFont("UI-B", 38)
        c.drawCentredString(0, 6, "$$$")
        A.line(c, -28, 30, 28, 30, HexColor("#CFC6A5"), lw=3)
        A.line(c, -28, -18, 20, -18, HexColor("#CFC6A5"), lw=3)

    tilt_s(c, x + 312, yb + 296, 8, 1.0, receipt)
    c.saveState()
    c.translate(x + 452, yb + 300)
    c.scale(1.15, 1.15)
    A.circ(c, 0, 0, 34, white)
    A.circ(c, -30, -44, 7, white)
    A.circ(c, -42, -56, 4, white)
    A.poly(c, [(-14, -12), (0, -22), (14, -6), (2, 14)], fill=A.GREEN)
    A.line(c, -24, -22, 24, 22, A.RED, lw=6)
    c.restoreState()


def sc_ask(c, x, yb, w, h):
    A.night_backdrop(c, x, yb, w, h, 14, bg_hex="#0E3B43")
    friends(c, x, yb + GROUND - 4, 160, [(70, F[0], 0, 0, 0, dict(phone=True, arm_up=True)), (160, F[2], 2, 1, 3, dict(leaf=True))])
    A.robot(c, x + 424, yb + GROUND - 4, 205, glow=True, wave=True)
    A.bubble(c, x + 20, yb + 238, 312, 106, tip=(x + 90, yb + 222))
    tbox(c, "4 of us, $40 each, one vegan. Dinner + dessert?", x + 36, yb + 338, 282, st(26, A.NAVY, 31))
    A.sparkle(c, x + 352, yb + 300, 16)
    A.sparkle(c, x + 505, yb + 280, 12)
    A.sparkle(c, x + 372, yb + 236, 10, A.MINT)


def sc_work(c, x, yb, w, h):
    A.night_backdrop(c, x, yb, w, h, 15, moon=False)
    cx = x + w / 2
    lab = st(26, white, 30, 1, "UI-B")
    for sx, sy, ex, ey in ((cx - 44, yb + 232, x + 166, yb + 290), (cx + 44, yb + 232, x + 386, yb + 290),
                           (cx - 62, yb + 150, x + 140, yb + 168), (cx + 62, yb + 150, x + 398, yb + 166)):
        A.line(c, sx, sy, ex, ey, A.MINT, lw=3, dash=(1, 9))
    A.robot(c, cx, yb + GROUND - 4, 190, glow=True)
    A.rr(c, x + 34, yb + 262, 124, 70, 8, white)
    A.line(c, x + 46, yb + 284, x + 148, yb + 306, HexColor("#CFCABA"), lw=8)
    A.pin(c, x + 98, yb + 278, 36, A.TERRA)
    A.magnifier(c, x + 128, yb + 292, 21)
    tbox(c, "Find venues", x + 10, yb + 252, 176, lab)
    A.doc(c, x + 432, yb + 296, 76, 92, lines=4, accent=A.TERRA)
    tbox(c, "Read pages", x + 332, yb + 246, 200, lab)
    A.sun(c, x + 62, yb + 172, 16)
    A.cloud(c, x + 94, yb + 158, 70)
    tbox(c, "Check weather", x + 0, yb + 124, 184, st(24, white, 29, 1, "UI-B"))
    A.footsteps(c, x + 428, yb + 166, 54)
    tbox(c, "Measure walks", x + 330, yb + 124, 196, st(23, white, 28, 1, "UI-B"))


def sc_plan_ok(c, x, yb, w, h):
    A.night_backdrop(c, x, yb, w, h, 16, ground=0, moon=False)
    c.setFillColor(HexColor("#1A2B52"))
    c.rect(x, yb, w, h, stroke=0, fill=1)
    c.setStrokeColor(white)
    A.alpha(c, 0.1)
    c.setLineWidth(14)
    for gx in (80, 190, 330, 450):
        c.line(x + gx, yb, x + gx + 20, yb + h)
    for gy in (120, 210, 280):
        c.line(x, yb + gy, x + w, yb + gy + 12)
    A.alpha(c, 1)
    A.dashed_curve(c, (x + 124, yb + 186), (x + 190, yb + 270), (x + 320, yb + 140), (x + 392, yb + 196), A.WARM, 6)
    lab = st(25, white, 29, 1, "UI-B")
    A.pin(c, x + 92, yb + 150, 90, A.TERRA)
    A.circ(c, x + 92, yb + 213, 14, HexColor("#F4F1EA"), HexColor("#C9C4B2"), 3)
    tbox(c, "Pita Jungle<br/><font size=23 color='#CFE5D8'>7:00 pm</font>", x + 4, yb + 132, 176, lab)
    A.pin(c, x + 424, yb + 162, 90, A.TERRA)
    A.cone(c, x + 424, yb + 222, 30)
    tbox(c, "The Gelato Spot<br/><font size=23 color='#CFE5D8'>9:00 pm</font>", x + 304, yb + 144, 220, st(24, white, 29, 1, "UI-B"))
    A.person(c, x + 232, yb + 176, 70, A.SKY, A.SKINS[0], A.HAIRS[0])
    A.person(c, x + 272, yb + 170, 70, A.ORANGE, A.SKINS[1], A.HAIRS[1], hair_style=1)
    A.rr(c, x + 186, yb + 250, 140, 38, 19, white)
    c.setFillColor(A.NAVY)
    c.setFont("UI-B", 24)
    c.drawCentredString(x + 256, yb + 260, "58 m walk")
    xx = x + 18
    for icon, text, wd in (("coin", "$25 each", 170), ("leaf", "Vegan", 138), ("shield", "5 / 5 pass", 166)):
        A.rr(c, xx, yb + 298, wd, 40, 20, A.GREEN)
        if icon == "coin":
            A.coin(c, xx + 24, yb + 318, 14)
        elif icon == "leaf":
            A.poly(c, [(xx + 12, yb + 308), (xx + 26, yb + 328), (xx + 36, yb + 317)], fill=white)
        else:
            A.shield_check(c, xx + 24, yb + 318, 28, white, A.GREEN)
        c.setFillColor(white)
        c.setFont("UI-B", 22)
        c.drawString(xx + 48, yb + 310, text)
        xx += wd + 12


# ------------------------------------------------------------------ informative sections
NODES = [
    ("1", "Discovery", "TOOL", BLUE, BLUE_L, BLUE_T, "Finds venues. Real IDs only, nothing invented."),
    ("2", "Enrichment", "LLM + TOOLS", CORAL, CORAL_L, CORAL_T, "An LLM reads venue pages. Gaps stay unknown."),
    ("3", "Weather", "TOOL", BLUE, BLUE_L, BLUE_T, "Weather for the outing hour."),
    ("4", "Planner", "LLM", CORAL, CORAL_L, CORAL_T, "Plans the stops. Sees failed checks on retry."),
    ("5", "Transit", "TOOL", BLUE, BLUE_L, BLUE_T, "Walk legs between stops, flagged verified or not."),
    ("6", "Critic", "RULES, NO LLM", GREEN, GREEN_L, GREEN_T, "Checks stops, budget, diet, hours and travel."),
]


def section_pipeline(c, top, h):
    ct = card(c, M, top, CW, h, "How it works: six nodes and a replan loop", size=44)
    lx = M + CW - 28
    for tag, fg, bg in reversed([("TOOL call", BLUE_T, BLUE_L), ("LLM call", CORAL_T, CORAL_L), ("Rule-based verifier", GREEN_T, GREEN_L)]):
        lx -= pdfmetrics.stringWidth(tag, "UI-B", 22) + 28
        pill(c, lx, top + 22, tag, fg, bg, size=22, h=38)
        lx -= 10
    nw, gap, nh = 235, 30, 262
    nx = M + 28 + (CW - 56 - (6 * nw + 5 * gap)) / 2
    nt = ct
    centers = {}
    for i, (num, name, tag, col, lt, tx, desc) in enumerate(NODES):
        x = nx + i * (nw + gap)
        c.setFillColor(white)
        c.setStrokeColor(col)
        c.setLineWidth(4)
        c.roundRect(x, H - nt - nh, nw, nh, 14, fill=1, stroke=1)
        c.setFillColor(lt)
        c.roundRect(x + 2, H - nt - 66, nw - 4, 64, 12, fill=1, stroke=0)
        c.rect(x + 2, H - nt - 66, nw - 4, 18, fill=1, stroke=0)
        c.setStrokeColor(col)
        c.setLineWidth(3)
        c.line(x + 2, H - nt - 66, x + nw - 2, H - nt - 66)
        c.setFillColor(NAVY)
        c.setFont("UI-B", 31)
        c.drawString(x + 14, H - nt - 45, f"{num}  {name}")
        pill(c, x + 14, nt + 78, tag, tx, lt, size=22, h=34, padx=11)
        para(c, desc, x + 14, nt + 124, nw - 26, st(24, lead=29.5))
        centers[name] = x + nw / 2
        if i < 5:
            arrow(c, x + nw + 3, H - nt - nh / 2, x + nw + gap - 3, H - nt - nh / 2, width=5, head=15)
    by = H - nt - nh
    xc_, xp_ = centers["Critic"], centers["Planner"]
    c.setStrokeColor(CORAL)
    c.setLineWidth(5)
    c.line(xc_, by, xc_, by - 30)
    c.line(xc_, by - 30, xp_, by - 30)
    arrow(c, xp_, by - 30, xp_, by - 3, color=CORAL, width=5, head=16)
    c.setFillColor(CORAL_T)
    c.setFont("UI-B", 26)
    c.drawCentredString((xc_ + xp_) / 2, by - 62, "Retry with failed checks (max 8 attempts)")
    sw = 3 * nw + 2 * gap
    para(c, "All nodes share <b>one run state</b>: constraints, evidence, plan, checks.",
         nx, nt + nh + 18, sw, st(24, MUTED, lead=29))
    ly = nt + nh + 82
    lh = top + h - 20 - ly
    half = (CW - 56 - 20) / 2
    for i, (title, items, blurb) in enumerate([
        ("Every fact is labelled", [("VERIFIED", GREEN_T, GREEN_L), ("ESTIMATED", AMBER_T, AMBER_L), ("UNKNOWN", CORAL_T, CORAL_L)],
         "Unknown never counts as vegan. Price ranges are guidance, not a bill."),
        ("Outcomes stay honest", [("VALID", GREEN_T, GREEN_L), ("PROVISIONAL", AMBER_T, AMBER_L), ("UNRESOLVED", CORAL_T, CORAL_L)],
         "No valid plan? It names the failed requirement instead of faking one."),
    ]):
        x = M + 28 + i * (half + 20)
        c.setFillColor(PALE)
        c.roundRect(x, H - ly - lh, half, lh, 12, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("UI-B", 26)
        c.drawString(x + 18, H - ly - 40, title)
        px = x + 18 + pdfmetrics.stringWidth(title, "UI-B", 26) + 20
        for t, fg, bgc in items:
            px += pill(c, px, ly + 10, t, fg, bgc, size=22, h=38, padx=9) + 6
        para(c, blurb, x + 18, ly + 62, half - 36, st(24, lead=29))


STATIONS = [
    ("1", "Discovery", "pin", BLUE, "13 venues found around Tempe"),
    ("2", "Enrichment", "doc", CORAL, "Pita Jungle $18, Gelato Spot $7, both vegan"),
    ("3", "Weather", "sun", BLUE, "7 pm: 36.9 \u00b0C, clear (sample)"),
    ("4", "Planner", "plan", CORAL, "Dinner Pita Jungle, dessert Gelato Spot"),
    ("5", "Transit", "steps", BLUE, "58 m walk between them (estimate)"),
    ("6", "Critic", "shield", GREEN, "All 5 checks pass; $25 vs $40 budget"),
]


def ticket(c, x, ymid, w, h, tag, col, light, tx, html):
    top_ = ymid - h / 2
    c.setFillColor(light)
    c.setStrokeColor(col)
    c.setLineWidth(3)
    c.roundRect(x, H - top_ - h, w, h, 16, fill=1, stroke=1)
    pill(c, x + 16, top_ + 14, tag, tx, white, size=22, h=36, padx=14)
    para(c, html, x + 18, top_ + 60, w - 36, st(23, INK, 29))


def section_scenes(c, top, h):
    ct = card(c, M, top, CW, h, "Behind the scenes: one real run", size=44)
    rx = M + CW - 28
    for t in reversed(["14 LLM calls", "15.4 s run time", "14.7k in / 1.6k out tokens"]):
        rx -= pdfmetrics.stringWidth(t, "UI-B", 22) + 32
        pill(c, rx, top + 18, t, NAVY, AMBER_L, size=22, padx=16, h=42)
        rx -= 12
    tw = 300
    ly = ct + 125
    lx0, rx0 = M + 28, M + CW - 28 - tw
    ticket(c, lx0, ly, tw, 176, "THE REQUEST", BLUE, BLUE_L, BLUE_T,
           "4 friends \u00b7 Fri 7 pm<br/>\u2264 $40 each \u00b7 one vegan<br/>Dinner + dessert \u00b7 Tempe")
    ticket(c, rx0, ly, tw, 176, "THE PLAN", GREEN, GREEN_L, GREEN_T,
           "Pita Jungle, then<br/>The Gelato Spot<br/>$25 each \u00b7 58 m walk")
    x1, x2 = lx0 + tw + 10, rx0 - 10
    arrow(c, x1, H - ly, x2, H - ly, color=BODY, width=10, head=28)
    n, margin = 6, 125
    for i, (num, name, kind, col, val) in enumerate(STATIONS):
        xi = x1 + margin + i * (x2 - x1 - 2 * margin) / (n - 1)
        A.circ(c, xi, H - ly, 29, col, white, 5)
        A.glyph(c, kind, xi, H - ly, col)
        vs = st(22, MUTED, 26.5, 1)
        pv = Paragraph(val, vs)
        _, hv = pv.wrap(250, 500)
        c.setFillColor(INK)
        c.setFont("UI-B", 27)
        if i % 2 == 0:
            base = H - (ly - 40)
            pv.drawOn(c, xi - 125, base)
            c.drawCentredString(xi, base + hv + 8, f"{num}  {name}")
        else:
            c.drawCentredString(xi, H - (ly + 40 + 22), f"{num}  {name}")
            pv.drawOn(c, xi - 125, H - (ly + 40 + 32) - hv)


def section_replan(c, top):
    top = ribbon(c, top, "Replan in action", "")
    wA, wZ, wB, gC = 550, 240, 550, 20
    wC = CW - wA - wZ - wB - gC
    s_t = st(26, NAVY, 32, font="UI-B")
    s_b = st(25, INK, 31)
    s_r = st(25, CORAL_T, 31, font="UI-B")
    s_g = st(25, GREEN_T, 31, font="UI-B")
    s_s = st(22, MUTED, 27)
    pad, gi, ind = 20, 9, 36
    A_items = [("Attempt 1: Planner's first plan", s_t, 0),
               ("Only one stop: Snooze (a breakfast cafe)", s_b, 0),
               ("Critic: 0 of 5 checks pass", s_r, 1),
               ("<b>Why it failed:</b> the request needs 3 stops (dinner, dessert, bar), and Snooze closes at 14:30, before 7 pm.", s_s, 0)]
    B_items = [("Attempt 2: Planner fixes the plan", s_t, 0),
               ("Chuckbox, then Gelato Spot, then Handlebar", s_b, 0),
               ("All 5 checks pass \u00b7 $31.50 per person \u00b7 VALID", s_g, 2)]

    def measure(items, w):
        out, tot = [], 0
        for html, sty, mk in items:
            p = Paragraph(html, sty)
            _, hh_ = p.wrap(w - 2 * pad - (ind if mk else 0), 10000)
            out.append((p, hh_, sty, mk))
            tot += hh_ + gi
        return out, tot - gi

    mA, hA = measure(A_items, wA)
    mB, hB = measure(B_items, wB)
    pc = Paragraph("Impossible request, like a $5 budget? It ends <b>UNRESOLVED</b>. Never faked.", st(26, NAVY, 33, font="UI-B"))
    _, hC = pc.wrap(wC - 2 * pad, 10000)
    rh = max(hA, hB, hC) + 2 * pad
    rh = max(rh, 230)

    def draw_box(bx, w, meas, col):
        c.setFillColor(white)
        c.setStrokeColor(col)
        c.setLineWidth(3)
        c.roundRect(bx, H - top - rh, w, rh, 16, fill=1, stroke=1)
        yy = top + pad
        for p, hp, sty, mk in meas:
            p.drawOn(c, bx + pad + (ind if mk else 0), H - yy - hp)
            if mk:
                A.check_dot(c, bx + pad + 14, H - yy - sty.leading * 0.5, 14, ok=(mk == 2))
            yy += hp + gi

    xA, xB = M, M + wA + wZ
    draw_box(xA, wA, mA, CORAL)
    draw_box(xB, wB, mB, GREEN)
    xC = xB + wB + gC
    c.setFillColor(AMBER)
    c.setStrokeColor(HexColor("#D9A01E"))
    c.setLineWidth(3)
    c.roundRect(xC, H - top - rh, wC, rh, 16, fill=1, stroke=1)
    pc.drawOn(c, xC + pad, H - top - rh / 2 - hC / 2)
    ymid = H - top - rh / 2
    lab = Paragraph("Critic sends the failed checks back to the Planner (retry, max 8)", st(22, BODY, 27, 1, "UI-B"))
    _, hl = lab.wrap(wZ - 20, 1000)
    lab.drawOn(c, xA + wA + 10, ymid - 22 + 0)
    arrow(c, xA + wA + 14, ymid - 40, xB - 14, ymid - 40, color=BODY, width=7, head=22)
    return top + rh


HEIGHTS = dict(pipe=576, scenes=352)


def build():
    out = OUT
    for n in range(2, 20):
        try:
            out.open("ab").close()
            break
        except PermissionError:
            out = OUT.with_name(f"{OUT.stem}_v{n}.pdf")
    c = canvas.Canvas(str(out), pagesize=(W, H), initialFontName="UI")
    c.setTitle("Night-Out Curator - Group 15 Poster")
    c.setAuthor("CSE 598 Group 15")
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    y = header(c) + G

    y = strip(c, ribbon(c, y, "The problem", "A night out should not take ten browser tabs."), [
        (sc_plan, A.INDIGO, A.NAVY, "Four friends, one Friday night"),
        (sc_chaos, A.DUSK, A.NAVY, "Maps, menus, hours, weather\u2026"),
        (sc_closed, A.PLUM, A.NAVY, "Closed. Over budget. Nothing vegan."),
    ]) + G
    y = strip(c, ribbon(c, y, "What the agent does", "Say it once. It finds, reads, checks and explains."), [
        (sc_ask, A.DEEP_TEAL, A.NAVY, "Just say it in plain English"),
        (sc_work, A.DEEP_TEAL, A.NAVY, "It looks things up instead of guessing"),
        (sc_plan_ok, A.INDIGO, A.NAVY, "A checked plan, every fact labelled"),
    ]) + G
    section_pipeline(c, y, HEIGHTS["pipe"])
    y += HEIGHTS["pipe"] + G
    section_scenes(c, y, HEIGHTS["scenes"])
    y += HEIGHTS["scenes"] + G
    y = section_replan(c, y) + G
    footer(c, y)
    c.showPage()
    c.save()
    print(f"wrote {out}; footer height = {H - y:.0f} pt")


if __name__ == "__main__":
    build()
