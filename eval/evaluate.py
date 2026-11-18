"""Objective constraint-satisfaction scoring against GROUND TRUTH (data/venues.json).

The baseline agent only sees the sparse 'free-API' fields (no price/vibe), so it
will often miss constraints here — that low score is the target the full Phase-2+
system improves on. Metrics are fully objective and reproducible.
"""
import json, math, pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
GT = {v["id"]: v for v in json.loads((DATA / "venues.json").read_text())["venues"]}


def _haversine(a, b):
    R = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def check_plan(plan: dict, c: dict) -> dict:
    """Return per-constraint pass/fail + a 0..1 score, using ground-truth fields."""
    stops = plan.get("stops", [])
    vids = [s.get("venue_id") for s in stops]
    venues = [GT.get(v) for v in vids]
    known = [v for v in venues if v]
    checks, details = {}, {}


    if len(stops) >= 2 and all(venues):
        total = sum(v["price_per_person"] for v in venues)
        checks["budget"] = total <= c["budget_pp"]
        details["budget"] = f"${total}/pp vs cap ${c['budget_pp']}"
    else:
        checks["budget"] = False
        details["budget"] = f"incomplete/unresolved plan ({len(known)}/{len(stops)} known, need 2)"


    if c.get("vegan_required"):
        dinner = next((GT.get(s["venue_id"]) for s in stops if s.get("type") == "dinner"), None)
        checks["vegan"] = bool(dinner and dinner["vegan"])
        details["vegan"] = f"dinner={dinner['name'] if dinner else '?'} vegan={dinner['vegan'] if dinner else '?'}"
    else:
        checks["vegan"] = True
        details["vegan"] = "not required"


    th = c["target_hour"]
    ok = len(stops) >= 2
    for s in stops:
        v = GT.get(s["venue_id"])
        need = th if s.get("type") == "dinner" else th + 2
        if not v or v["close_hour"] <= need:
            ok = False
            details.setdefault("open", []).append(f"{v['name'] if v else s.get('venue_id')} closes {v['close_hour'] if v else '?'} (need >{need})")
    checks["open"] = ok
    details["open"] = details.get("open", "all open")


    if len(known) >= 2:
        d = _haversine((known[0]["lat"], known[0]["lon"]), (known[1]["lat"], known[1]["lon"]))
        checks["walkable"] = d <= c.get("max_walk_m", 1200)
        details["walkable"] = f"{round(d)} m between stops vs {c.get('max_walk_m', 1200)} m"
    else:
        checks["walkable"] = False
        details["walkable"] = "need two known venues"

    score = sum(checks.values()) / len(checks)
    return {"checks": checks, "details": details, "score": round(score, 2),
            "valid": all(checks.values())}
