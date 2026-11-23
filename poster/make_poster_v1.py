"""Builds the 24x36 in portrait vector poster: python poster/make_poster.py (needs reportlab, pillow)."""
import math
import pathlib

from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE / "Group15_Poster.pdf"
REPO_URL = "https://github.com/sachinsss/night-out-curator"

FONTS = pathlib.Path("C:/Windows/Fonts")
for name, f in [("UI", "segoeui.ttf"), ("UI-B", "segoeuib.ttf"), ("UI-I", "segoeuii.ttf"), ("UI-BI", "segoeuiz.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / f)))
pdfmetrics.registerFontFamily("UI", normal="UI", bold="UI-B", italic="UI-I", boldItalic="UI-BI")

W, H = 24 * 72, 36 * 72
M, G = 48, 12
CW = W - 2 * M

GREEN = HexColor("#1F5F46")
GREEN_D = HexColor("#143D2E")
GREEN_L = HexColor("#E4EFE8")
TERRA = HexColor("#B4472F")
TERRA_L = HexColor("#F7E6E0")
TEAL = HexColor("#2B6C8F")
TEAL_L = HexColor("#E2EEF4")
AMBER = HexColor("#9A5F0E")
AMBER_L = HexColor("#F8EDD6")
INK = HexColor("#1D2A25")
MUTED = HexColor("#56615B")
BG = HexColor("#F4F2EA")
BORDER = HexColor("#D5D1C2")
GREY = HexColor("#9AA39E")
PALE = HexColor("#F6F5EF")
MINT = HexColor("#CFE5D8")


def st(size, color=INK, lead=None, align=0):
    return ParagraphStyle("s", fontName="UI", fontSize=size, leading=lead or size * 1.27, textColor=color, alignment=align)


def para(c, html, x, top, w, style):
    p = Paragraph(html, style)
    _, h = p.wrap(w, 10000)
    p.drawOn(c, x, H - top - h)
    return h


def bullets(c, items, x, top, w, style, gap=10, dot=GREEN):
    y = top
    for it in items:
        p = Paragraph(it, style)
        _, h = p.wrap(w - 28, 10000)
        c.setFillColor(dot)
        c.circle(x + 8, H - y - style.leading * 0.6, 5.5, fill=1, stroke=0)
        p.drawOn(c, x + 28, H - y - h)
        y += h + gap
    return y - top - gap


def card(c, x, top, w, h, title, size=40):
    c.setFillColor(white)
    c.setStrokeColor(BORDER)
    c.setLineWidth(2)
    c.roundRect(x, H - top - h, w, h, 16, fill=1, stroke=1)
    c.setFillColor(GREEN)
    c.setFont("UI-B", size)
    c.drawString(x + 28, H - top - 56, title)
    c.setFillColor(TERRA)
    c.rect(x + 28, H - top - 72, 96, 6, fill=1, stroke=0)
    return top + 90


def pill(c, x, top, text, fg, bg, size=20, padx=14, h=None, font="UI-B"):
    h = h or size * 1.7
    w = pdfmetrics.stringWidth(text, font, size) + 2 * padx
    c.setFillColor(bg)
    c.roundRect(x, H - top - h, w, h, h / 2, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont(font, size)
    c.drawString(x + padx, H - top - h + (h - size * 0.72) / 2, text)
    return w


def arrow(c, x1, y1, x2, y2, color=GREEN, width=5, head=16):
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


def mark(c, cx, cy, r, ok=True):
    c.setFillColor(GREEN if ok else TERRA)
    c.circle(cx, cy, r, fill=1, stroke=0)
    c.setStrokeColor(white)
    c.setLineWidth(r * 0.24)
    c.setLineCap(1)
    c.setLineJoin(1)
    if ok:
        p = c.beginPath()
        p.moveTo(cx - r * 0.5, cy)
        p.lineTo(cx - r * 0.1, cy - r * 0.42)
        p.lineTo(cx + r * 0.52, cy + r * 0.4)
        c.drawPath(p, fill=0, stroke=1)
    else:
        d = r * 0.42
        c.line(cx - d, cy - d, cx + d, cy + d)
        c.line(cx - d, cy + d, cx + d, cy - d)
    c.setLineCap(0)


def crop_screenshot():
    dst = ASSETS / "ui_results_crop.png"
    # css box x 340-1430, y 185-~740 at 3x; drops sidebar and page title
    Image.open(ASSETS / "ui_hires.png").crop((1020, 555, 4290, 2225)).save(dst)
    return dst


# ---------------------------------------------------------------- sections
def header(c):
    hh = 240
    c.setFillColor(GREEN_D)
    c.rect(0, H - hh, W, hh, fill=1, stroke=0)
    c.setFillColor(TERRA)
    c.rect(0, H - hh - 10, W, 10, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("UI-B", 104)
    c.drawString(M + 4, H - 108, "Night-Out Curator")
    c.setFont("UI", 34)
    c.setFillColor(MINT)
    c.drawString(M + 8, H - 164, "Evidence-grounded multi-agent outing planner · Phoenix / Tempe")
    c.setFont("UI-I", 27)
    c.setFillColor(white)
    c.drawString(M + 8, H - 214, "Describe your evening in plain English. Get a multi-stop plan where every claim is checked, sourced or marked unknown.")
    qsize = 132
    qr = QrCodeWidget(REPO_URL)
    b = qr.getBounds()
    d = Drawing(qsize, qsize, transform=[qsize / (b[2] - b[0]), 0, 0, qsize / (b[3] - b[1]), 0, 0])
    d.add(qr)
    c.setFillColor(white)
    c.roundRect(W - M - qsize - 12, H - 18 - qsize - 24, qsize + 24, qsize + 24, 10, fill=1, stroke=0)
    renderPDF.draw(d, c, W - M - qsize, H - 18 - qsize - 12)
    rx = W - M - qsize - 44
    c.setFillColor(white)
    c.setFont("UI-B", 30)
    c.drawRightString(rx, H - 50, "CSE 598 Agentic AI  |  Group 15")
    c.setFont("UI", 22)
    c.setFillColor(MINT)
    c.drawRightString(rx, H - 88, "Sachin Shankarikoppa · Sushanth Vasudeva")
    c.drawRightString(rx, H - 116, "Vivek Kamath · Srikar Vinjanampati")
    c.drawRightString(rx, H - 144, "Chetana Reddy Janagan")
    c.setFont("UI", 20)
    c.drawRightString(rx, H - 178, "Stakeholder: Mitul Krishna Balamurugan")
    c.setFont("UI", 17)
    c.drawCentredString(W - M - qsize / 2, H - 18 - qsize - 36, "Scan for code + reports")
    return hh + 10


def section_problem(c, top, h, w):
    ct = card(c, M, top, w, h, "The problem")
    x, iw = M + 28, w - 56
    ct += para(c, "Planning a night out means juggling maps, menus, venue sites, weather and transit, and still landing "
                  "somewhere <b>closed</b> or <b>over budget</b>.", x, ct, iw, st(23, lead=29)) + 8
    ct += para(c, "Free Tempe venue listings (Geoapify / OSM) that include:", x, ct, iw, st(21, MUTED, lead=26)) + 10
    tw = (iw - 2 * 14) / 3
    th = h - (ct - top) - 24
    for i, (big, small) in enumerate([("0%", "a price level"), ("~20%", "opening hours"), ("0%", "a mood or rating")]):
        xx = x + i * (tw + 14)
        c.setFillColor(TERRA_L)
        c.roundRect(xx, H - ct - th, tw, th, 12, fill=1, stroke=0)
        c.setFillColor(TERRA)
        c.setFont("UI-B", 50)
        c.drawCentredString(xx + tw / 2, H - ct - th + 56, big)
        c.setFillColor(INK)
        c.setFont("UI", 20)
        c.drawCentredString(xx + tw / 2, H - ct - th + 24, small)


def section_does(c, top, h, x0, w):
    ct = card(c, x0, top, w, h, "What the agent does")
    ix, iw = x0 + 28, w - 56
    c.setFillColor(GREEN_L)
    qh = 74
    c.roundRect(ix, H - ct - qh, iw, qh, 12, fill=1, stroke=0)
    para(c, "<i>\"Plan a night out for 4 friends near ASU Tempe this Friday around 7pm. About $40 per person, chill and "
            "walkable, one of us is vegan. Dinner plus one spot afterwards.\"</i>", ix + 18, ct + 9, iw - 36, st(22, lead=27))
    ct += qh + 14
    gap = 70
    bw = (iw - gap) / 2
    bh = h - (ct - top) - 46
    for i, (tag, col, bgc, txt) in enumerate([
        ("INPUT", TEAL, TEAL_L, "The request plus hard limits: party size, budget, diet, time, max walk, mood, area, 1 to 4 stops."),
        ("OUTPUT", GREEN, GREEN_L, "Ordered stops with a source per fact, travel hops, weather note, pass / fail per rule, JSON plan."),
    ]):
        x = ix + i * (bw + gap)
        c.setFillColor(bgc)
        c.roundRect(x, H - ct - bh, bw, bh, 12, fill=1, stroke=0)
        pill(c, x + 14, ct + 10, tag, white, col, size=19, h=32)
        para(c, txt, x + 16, ct + 50, bw - 32, st(20.5, lead=25))
    arrow(c, ix + bw + 8, H - ct - bh / 2, ix + bw + gap - 8, H - ct - bh / 2)
    para(c, "<b>Out of scope:</b> booking, payments, reservations, real-time table availability. It recommends; it does not book.",
         ix, ct + bh + 10, iw, st(20, MUTED, lead=25))


NODES = [
    ("1", "Discovery", "TOOL", TEAL, TEAL_L, "Searches Google Places, Geoapify or OpenStreetMap. Returns candidate IDs only, so no invented venues."),
    ("2", "Enrichment", "LLM + TOOLS", TERRA, TERRA_L, "Fetches approved venue pages. Claude Haiku 4.5 extracts price, hours, diet. Unsupported facts stay null."),
    ("3", "Weather", "TOOL", TEAL, TEAL_L, "Conditions for the outing hour (Open-Meteo; a bundled sample in the current build)."),
    ("4", "Planner", "LLM", TERRA, TERRA_L, "Proposes ordered venue IDs as a structured plan. On retry it sees failed checks and rejected plans."),
    ("5", "Transit", "TOOL", TEAL, TEAL_L, "Route legs between stops: Google Routes or a straight-line estimate, flagged verified or not."),
    ("6", "Critic", "RULES, NO LLM", GREEN, GREEN_L, "Checks stops, budget, diet, hours, travel. Ends as valid, provisional or unresolved."),
]


def section_pipeline(c, top, h):
    ct = card(c, M, top, CW, h, "How it works: specialist nodes plus a verify-and-replan loop")
    lx = M + CW - 28
    for tag, col in reversed([("TOOL call", TEAL), ("LLM call", TERRA), ("Rule-based verifier", GREEN)]):
        lx -= pdfmetrics.stringWidth(tag, "UI-B", 19) + 28
        pill(c, lx, top + 24, tag, white, col, size=19, h=34)
        lx -= 10
    nw, gap, nh = 240, 36, 284
    nx = M + 28 + (CW - 56 - (6 * nw + 5 * gap)) / 2
    nt = ct
    centers = {}
    for i, (num, name, tag, col, lt, desc) in enumerate(NODES):
        x = nx + i * (nw + gap)
        c.setFillColor(white)
        c.setStrokeColor(col)
        c.setLineWidth(4)
        c.roundRect(x, H - nt - nh, nw, nh, 14, fill=1, stroke=1)
        c.setFillColor(col)
        c.roundRect(x, H - nt - 66, nw, 66, 14, fill=1, stroke=0)
        c.rect(x, H - nt - 66, nw, 18, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("UI-B", 34)
        c.drawString(x + 16, H - nt - 46, f"{num}  {name}")
        pill(c, x + 16, nt + 78, tag, col, lt, size=17, h=28, padx=11)
        para(c, desc, x + 16, nt + 118, nw - 30, st(21.5, lead=26.5))
        centers[name] = x + nw / 2
        if i < 5:
            arrow(c, x + nw + 4, H - nt - nh / 2, x + nw + gap - 4, H - nt - nh / 2, width=5, head=16)
    by = H - nt - nh
    xc_, xp_ = centers["Critic"], centers["Planner"]
    c.setStrokeColor(TERRA)
    c.setLineWidth(5)
    c.line(xc_, by, xc_, by - 34)
    c.line(xc_, by - 34, xp_, by - 34)
    arrow(c, xp_, by - 34, xp_, by - 3, color=TERRA, width=5, head=16)
    c.setFillColor(TERRA)
    c.setFont("UI-B", 23)
    c.drawCentredString((xc_ + xp_) / 2, by - 70, "Retry with failed checks and rejected plans (max 8 attempts, 120 s)")
    # shared state under nodes 1-3
    sw = 3 * nw + 2 * gap
    sy = nt + nh + 20
    c.setFillColor(GREEN_L)
    c.roundRect(nx, H - sy - 80, sw, 80, 12, fill=1, stroke=0)
    para(c, "<b>Shared run state</b> for each request: validated constraints, candidates, evidence + sources, weather, plan, "
            "route legs, checks, rejected plans, attempts, trace.", nx + 16, sy + 8, sw - 32, st(21, lead=26))
    # labels strip
    ly = nt + nh + 20 + 80 + 20
    lh = top + h - 20 - ly
    half = (CW - 56 - 20) / 2
    for i, (title, items, blurb) in enumerate([
        ("Every fact is labelled", [("VERIFIED", GREEN, GREEN_L), ("ESTIMATED", AMBER, AMBER_L), ("UNKNOWN", TERRA, TERRA_L)],
         "Unknown diet never satisfies a vegan request; vegetarian is not vegan; price ranges are guidance, not a bill."),
        ("Outcomes stay honest", [("VALID", GREEN, GREEN_L), ("PROVISIONAL", AMBER, AMBER_L), ("UNRESOLVED", TERRA, TERRA_L)],
         "If no plan meets the limits it names the failed requirement instead of passing off an invalid plan as a success."),
    ]):
        x = M + 28 + i * (half + 20)
        c.setFillColor(PALE)
        c.roundRect(x, H - ly - lh, half, lh, 12, fill=1, stroke=0)
        c.setFillColor(GREEN)
        c.setFont("UI-B", 27)
        c.drawString(x + 18, H - ly - 38, title)
        px = x + 18 + pdfmetrics.stringWidth(title, "UI-B", 27) + 24
        for t, fg, bgc in items:
            px += pill(c, px, ly + 12, t, fg, bgc, size=19, h=36, padx=12) + 8
        para(c, blurb, x + 18, ly + 58, half - 36, st(20.5, lead=25))


def section_example(c, top, h, shot):
    sw = 700
    ct = card(c, M, top, sw, h, "Example: one real run")
    iw = sw - 56
    im = Image.open(shot)
    ih = iw * im.height / im.width
    c.drawImage(str(shot), M + 28, H - ct - ih, width=iw, height=ih)
    c.setStrokeColor(BORDER)
    c.setLineWidth(2)
    c.rect(M + 28, H - ct - ih, iw, ih, fill=0, stroke=1)
    para(c, "Localhost UI: saved <b>Claude Haiku 4.5 (AWS Bedrock)</b> run on bundled, annotated Tempe fixtures. "
            "The 58 m hop is a straight-line estimate.", M + 28, ct + ih + 10, iw, st(20, MUTED, lead=25))
    x0 = M + sw + G
    w = CW - sw - G
    ct = card(c, x0, top, w, h, "Behind the scenes")
    rows = [
        ("Request", GREEN, "<b>≤ $40</b> per person, vegan, 19:00, walk ≤ 1,200 m, 4 people."),
        ("Discovery", TEAL, "<b>13 candidates</b> for dinner and after-spots; planner limited to known IDs."),
        ("Enrichment", TERRA, "Pita Jungle <b>$18</b>, closes 22:00, vegan. Gelato Spot <b>$7</b>, closes 23:00, vegan."),
        ("Weather", TEAL, "19:00: 36.9 °C, clear (bundled sample, not a live forecast)."),
        ("Planner", TERRA, "<b>Pita Jungle, then The Gelato Spot.</b>"),
        ("Transit", TEAL, "58 m, about 1 min, <b>verified = false</b> (estimate)."),
        ("Critic", GREEN, "5 of 5 checks pass, $25 vs $40 cap: <b>valid on attempt 1</b>."),
    ]
    y = ct
    for name, col, txt in rows:
        pill(c, x0 + 28, y, name, white, col, size=19, h=32, padx=12)
        h2 = para(c, txt, x0 + 28 + 164, y - 2, w - 56 - 164, st(21.5, lead=26.5))
        y += max(h2, 34) + 10
    y += 6
    th = top + h - 24 - y
    c.setFillColor(GREEN_L)
    c.roundRect(x0 + 28, H - y - th, w - 56, th, 12, fill=1, stroke=0)
    sx = x0 + 28 + 24
    for big, small in [("14", "LLM calls"), ("15.4 s", "run time"), ("14.7k / 1.6k", "tokens in / out")]:
        c.setFillColor(GREEN)
        c.setFont("UI-B", 34)
        c.drawString(sx, H - y - th / 2 - 11, big)
        sx += pdfmetrics.stringWidth(big, "UI-B", 34) + 10
        c.setFillColor(INK)
        c.setFont("UI", 21)
        c.drawString(sx, H - y - th / 2 - 8, small)
        sx += pdfmetrics.stringWidth(small, "UI", 21) + 48


def bar_chart(c, x, top, w, h):
    px, pw = x + 64, w - 80
    ph = h - 100
    base = H - top - h + 36
    c.setStrokeColor(HexColor("#E3E0D3"))
    c.setLineWidth(1.5)
    c.setFont("UI", 17)
    c.setFillColor(MUTED)
    for v in (0, 0.5, 1.0):
        yy = base + ph * v
        c.line(px, yy, px + pw, yy)
        c.drawRightString(px - 10, yy - 6, f"{int(v * 100)}%")
    series = [("Graph + Critic", GREEN), ("B1 enriched", TEAL), ("B2 sparse", GREY)]
    groups = [("Standard set", [1, .25, .25], ["12/12", "3/12", "3/12"]), ("Stress set", [1, .5, .5], ["6/6", "3/6", "3/6"])]
    gw, bw = pw / 2, 74
    for gi, (gname, vals, labs) in enumerate(groups):
        gx = px + gi * gw + (gw - (3 * bw + 2 * 10)) / 2
        for si, v in enumerate(vals):
            bx = gx + si * (bw + 10)
            c.setFillColor(series[si][1])
            c.rect(bx, base, bw, max(ph * v, 2), fill=1, stroke=0)
            c.setFont("UI-B", 19)
            if v >= 0.9:
                c.setFillColor(white)
                c.drawCentredString(bx + bw / 2, base + ph * v - 26, labs[si])
            else:
                c.setFillColor(INK)
                c.drawCentredString(bx + bw / 2, base + ph * v + 7, labs[si])
        c.setFillColor(INK)
        c.setFont("UI-B", 21)
        c.drawCentredString(px + gi * gw + gw / 2, base - 28, gname)
    lx = px - 6
    for name, col in series:
        c.setFillColor(col)
        c.rect(lx, H - top - 20, 18, 18, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("UI", 19)
        c.drawString(lx + 26, H - top - 17, name)
        lx += pdfmetrics.stringWidth(name, "UI", 19) + 56


def section_results(c, top, h):
    wa, wb = 640, 470
    wc = CW - wa - wb - 2 * G
    ct = card(c, M, top, wa, h, "Pilot results (mock mode)")
    para(c, "Valid-plan rate on feasible requests; 72 runs, <b>0 LLM calls</b>.", M + 28, ct - 8, wa - 56, st(21, lead=26))
    cht = h - 232
    bar_chart(c, M + 28, ct + 28, wa - 56, cht)
    para(c, "B1 / B2: deterministic baselines with no Critic loop. Graph flagged <b>all 6 infeasible</b> requests unresolved; baselines none. "
            "Synthetic fixtures: a wiring check, not model quality.",
         M + 28, top + h - 106, wa - 56, st(20, MUTED, lead=24.5))
    # recovery
    xb = M + wa + G
    ct = card(c, xb, top, wb, h, "Replan in action")
    y = ct - 6
    bh = 118
    for i, (tag, txt, ok, verdict) in enumerate([
        ("Attempt 1", "Bad plan injected: <i>Snooze</i> only.", False, "Critic: all 5 checks fail"),
        ("Attempt 2", "<i>Chuckbox, Gelato Spot, Handlebar</i>", True, "Critic: all 5 pass, $31.50 / person"),
    ]):
        c.setFillColor(GREEN_L if ok else TERRA_L)
        c.roundRect(xb + 28, H - y - bh, wb - 56, bh, 12, fill=1, stroke=0)
        c.setFillColor(GREEN if ok else TERRA)
        c.setFont("UI-B", 23)
        c.drawString(xb + 46, H - y - 30, tag)
        para(c, txt, xb + 46, y + 40, wb - 92, st(20.5, lead=25))
        mark(c, xb + 58, H - y - bh + 24, 14, ok)
        c.setFillColor(INK)
        c.setFont("UI-B", 20)
        c.drawString(xb + 82, H - y - bh + 17, verdict)
        y += bh
        if i == 0:
            arrow(c, xb + wb / 2, H - y - 1, xb + wb / 2, H - y - 22, color=TERRA, width=4, head=12)
            y += 22
    y += 14
    para(c, "A page timeout leaves facts unknown, so another venue is chosen. A $5 budget ends <b>unresolved</b> after 8 attempts, never faked.",
         xb + 28, y, wb - 56, st(20, lead=24.5))
    # limitations
    xc = xb + wb + G
    ct = card(c, xc, top, wc, h, "Limitations found")
    bullets(c, [
        "<b>Unsupported prose:</b> the real run said both venues \"can accommodate 4 friends\" with no evidence. The Critic checks fields, not sentences.",
        "<b>Estimates:</b> non-Google walking is straight-line, arrivals use fixed 2 h slots, weather is a bundled sample, transit is unverified.",
        "<b>Synthetic pilot:</b> fixture pages and labels share one 13-venue catalog, so scores may be inflated.",
        "<b>Costly dead ends:</b> infeasible requests use all 8 retries before reporting unresolved.",
    ], xc + 28, ct - 6, wc - 56, st(20, lead=24.5), gap=9, dot=TERRA)


def section_bottom(c, top, h):
    ct = card(c, M, top, CW, h, "Where we are headed", size=38)
    tiles = [("95%+", "hard-constraint score, +0.10 over baseline"), ("85%+", "valid-plan rate"), ("100%", "dietary correctness"),
             ("95%+", "factual accuracy"), ("45 s / $0.10", "median latency / cost per request"), ("4.0 / 5", "mood and usefulness (human)")]
    gap = 14
    tw = (CW - 56 - 5 * gap) / 6
    th = 88
    c.setFillColor(MUTED)
    c.setFont("UI-B", 20)
    c.drawRightString(M + CW - 28, H - top - 46, "Stakeholder-approved final targets")
    for i, (big, small) in enumerate(tiles):
        x = M + 28 + i * (tw + gap)
        c.setFillColor(GREEN_L)
        c.roundRect(x, H - ct - th, tw, th, 12, fill=1, stroke=0)
        c.setFillColor(GREEN)
        c.setFont("UI-B", 34)
        c.drawCentredString(x + tw / 2, H - ct - 42, big)
        para(c, small, x + 10, ct + 52, tw - 20, st(17.5, INK, lead=21, align=1))
    y = ct + th + 20
    para(c, "<b>Next:</b> matched real-model runs (graph vs ReAct vs single call)  ·  independent venue annotations and blinded human ratings  ·  "
            "claim-level evidence audit and fetch retries  ·  live weather, verified transit, route-adjusted schedules  ·  "
            "show parsed constraints and ask about conflicts.  <b>Optional:</b> preference memory, other cities.",
         M + 28, y, CW - 56, st(21, lead=26))


def footer(c, top):
    fh = H - top
    c.setFillColor(GREEN_D)
    c.rect(0, 0, W, fh, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("UI-B", 24)
    c.drawString(M, fh - 42, "Built with")
    c.setFont("UI", 23)
    c.setFillColor(MINT)
    c.drawString(M + 132, fh - 42, "Python · LangGraph · LangChain · Pydantic · AWS Bedrock (Claude Haiku 4.5) · Google Places / Routes · Geoapify · OpenStreetMap · Open-Meteo")
    c.setFont("UI", 19)
    c.drawString(M, fh - 74, "Pilot figures come from mock runs on fixture data: integration checks, not model-performance claims. Map data: OpenStreetMap contributors.")
    c.setFont("UI-B", 19)
    c.setFillColor(white)
    c.drawRightString(W - M, fh - 74, REPO_URL.replace("https://", ""))


HEIGHTS = dict(r1=355, r2=628, r3=480, r4=450, r5=258)


def build():
    shot = crop_screenshot()
    c = canvas.Canvas(str(OUT), pagesize=(W, H), initialFontName="UI")
    c.setTitle("Night-Out Curator - Group 15 Poster")
    c.setAuthor("CSE 598 Group 15")
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    y = header(c) + G

    pw = 600
    section_problem(c, y, HEIGHTS["r1"], pw)
    section_does(c, y, HEIGHTS["r1"], M + pw + G, CW - pw - G)
    y += HEIGHTS["r1"] + G
    section_pipeline(c, y, HEIGHTS["r2"])
    y += HEIGHTS["r2"] + G
    section_example(c, y, HEIGHTS["r3"], shot)
    y += HEIGHTS["r3"] + G
    section_results(c, y, HEIGHTS["r4"])
    y += HEIGHTS["r4"] + G
    section_bottom(c, y, HEIGHTS["r5"])
    y += HEIGHTS["r5"] + G
    footer(c, y)
    c.showPage()
    c.save()
    print(f"wrote {OUT}; footer height = {H - y:.0f} pt")


if __name__ == "__main__":
    build()
