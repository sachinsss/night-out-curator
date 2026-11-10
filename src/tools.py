"""Baseline tools for the Night-Out Curator agent.

Four tools are exposed to the BASELINE agent:
    search_venues, walk_route, transit, weather

Each runs OFFLINE by default (bundled data in data/) and can call the real
free APIs when live mode is enabled (set_live(True)):
    - venues/routes -> Geoapify        (GEOAPIFY_KEY)
    - transit       -> Transitland      (TRANSITLAND_KEY)
    - weather       -> Open-Meteo        (no key)

IMPORTANT (the honest data gap): the free structured APIs do NOT return price
or "vibe", and return hours only ~20% of the time. So search_venues deliberately
exposes only that subset. Recovering price/vibe/menus is the job of the Phase-2
enrichment tools (web_search / fetch_webpage) — intentionally NOT in the baseline.
"""
import json, math, os, pathlib, urllib.request, urllib.parse
from langchain_core.tools import tool

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
_VENUES = json.loads((DATA / "venues.json").read_text())["venues"]
_WEATHER = json.loads((DATA / "weather_sample.json").read_text())
try:
    _TRANSIT = json.loads((DATA / "transit_sample.json").read_text())
except FileNotFoundError:
    _TRANSIT = {}

_LIVE = False
def set_live(live: bool):
    global _LIVE
    _LIVE = live

def _get(url):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "night-out-curator/0.1"}), timeout=40).read())

def _haversine(a_lat, a_lon, b_lat, b_lon):
    R = 6371000
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


_CAT = {"dinner": "restaurant", "restaurant": "restaurant", "food": "restaurant",
        "bar": "bar", "drinks": "bar", "cafe": "cafe", "coffee": "cafe",
        "dessert": "dessert", "after": None}


@tool
def search_venues(category: str, vegan_required: bool = False,
                  near_lat: float = 33.4255, near_lon: float = -111.9400,
                  radius_m: int = 1500) -> list:
    """Find candidate venues near a point in Tempe/Phoenix.

    category: one of 'dinner'/'restaurant', 'bar', 'cafe', 'dessert' (or 'after' for any non-restaurant).
    vegan_required: if True, keep only venues flagged vegan-friendly in the data (note: this flag is
        sparse in real open data, so it may miss vegan-friendly spots that aren't tagged).
    Returns basic fields only: id, name, category, cuisine, lat, lon, website, opening_hours.
    NOTE: price and 'vibe' are NOT available from this data source — estimate them if you need them.
    """
    if _LIVE and os.getenv("GEOAPIFY_KEY"):
        try:
            cat_map = {"restaurant": "catering.restaurant", "bar": "catering.bar",
                       "cafe": "catering.cafe", "dessert": "catering.ice_cream"}
            gcat = cat_map.get(_CAT.get(category, "restaurant") or "catering.restaurant", "catering.restaurant")
            p = {"categories": gcat, "filter": f"circle:{near_lon},{near_lat},{radius_m}",
                 "bias": f"proximity:{near_lon},{near_lat}", "limit": 15, "apiKey": os.getenv("GEOAPIFY_KEY")}
            if vegan_required:
                p["conditions"] = "vegan"
            r = _get("https://api.geoapify.com/v2/places?" + urllib.parse.urlencode(p))
            out = []
            for f in r.get("features", []):
                pr = f["properties"]
                out.append({"id": pr.get("place_id", "")[:12], "name": pr.get("name"),
                            "category": category, "cuisine": (pr.get("catering", {}) or {}).get("cuisine"),
                            "lat": pr.get("lat"), "lon": pr.get("lon"),
                            "website": pr.get("website"), "opening_hours": pr.get("opening_hours")})
            return [v for v in out if v["name"]][:12]
        except Exception as e:
            return [{"error": f"geoapify live call failed: {e}; falling back offline"}]

    target = _CAT.get(category, "restaurant")
    out = []
    for v in _VENUES:
        if target is not None and v["category"] != target:
            continue
        if target is None and v["category"] == "restaurant":
            continue
        if _haversine(near_lat, near_lon, v["lat"], v["lon"]) > radius_m:
            continue
        if vegan_required and not v.get("vegan_tag", False):
            continue
        out.append({"id": v["id"], "name": v["name"], "category": v["category"],
                    "cuisine": v["cuisine"], "lat": v["lat"], "lon": v["lon"],
                    "website": v["website"], "opening_hours": v.get("opening_hours_public")})
    return out


@tool
def walk_route(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> dict:
    """Walking distance (meters) and time (minutes) between two points."""
    if _LIVE and os.getenv("GEOAPIFY_KEY"):
        try:
            p = {"waypoints": f"{from_lat},{from_lon}|{to_lat},{to_lon}", "mode": "walk",
                 "apiKey": os.getenv("GEOAPIFY_KEY")}
            r = _get("https://api.geoapify.com/v1/routing?" + urllib.parse.urlencode(p))
            pr = r["features"][0]["properties"]
            return {"distance_m": round(pr["distance"]), "minutes": round(pr["time"] / 60)}
        except Exception:
            pass
    d = _haversine(from_lat, from_lon, to_lat, to_lon)
    return {"distance_m": round(d), "minutes": round(d / 1.4 / 60)}


@tool
def transit(from_lat: float, from_lon: float, to_lat: float, to_lon: float,
            time: str = "19:00") -> dict:
    """Public-transit trip (Valley Metro) between two points. Returns total minutes and legs."""
    if _LIVE and os.getenv("TRANSITLAND_KEY"):
        try:
            p = {"fromPlace": f"{from_lat},{from_lon}", "toPlace": f"{to_lat},{to_lon}",
                 "date": _WEATHER.get("date", "2026-09-11"), "time": time + ":00",
                 "maxItineraries": 1, "api_key": os.getenv("TRANSITLAND_KEY")}
            r = _get("https://transit.land/api/v2/routing/otp/plan?" + urllib.parse.urlencode(p))
            it = (r.get("plan") or {}).get("itineraries", [])
            if it:
                i = it[0]
                return {"total_min": round(i["duration"] / 60),
                        "legs": [f"{l.get('mode')} {l.get('route') or ''}".strip() for l in i["legs"]]}
        except Exception:
            pass

    for s in _TRANSIT.values():
        if _haversine(from_lat, from_lon, *s["from"]) < 600 and _haversine(to_lat, to_lon, *s["to"]) < 600:
            return {"total_min": s["total_min"], "legs": [f"{l['mode']} {l['route']}".strip() for l in s["legs"]]}
    d = _haversine(from_lat, from_lon, to_lat, to_lon)
    return {"total_min": round(d / 1000 / 25 * 60) + 8, "legs": ["estimate (bus/rail)"]}


@tool
def weather(hour: int = 19) -> dict:
    """Weather for the outing date at a given hour (24h). Returns temp_c, precip_prob, condition."""
    if _LIVE:
        try:
            wq = urllib.parse.urlencode({"latitude": _WEATHER["lat"], "longitude": _WEATHER["lon"],
                                         "hourly": "temperature_2m,precipitation_probability,weather_code",
                                         "timezone": "America/Phoenix", "forecast_days": 1})
            w = _get("https://api.open-meteo.com/v1/forecast?" + wq)
            idx = [t[11:13] for t in w["hourly"]["time"]].index(f"{hour:02d}")
            tc, pp = w["hourly"]["temperature_2m"][idx], w["hourly"]["precipitation_probability"][idx]
            return {"temp_c": tc, "precip_prob": pp, "condition": "rain" if pp > 40 else "clear"}
        except Exception:
            pass
    for t, vals in _WEATHER["hourly"].items():
        if t[11:13] == f"{hour:02d}":
            return {"temp_c": vals["temp_c"], "precip_prob": vals["precip_prob"],
                    "condition": "rain" if vals["precip_prob"] > 40 else "clear"}
    return {"temp_c": None, "precip_prob": None, "condition": "unknown"}


BASELINE_TOOLS = [search_venues, walk_route, transit, weather]
