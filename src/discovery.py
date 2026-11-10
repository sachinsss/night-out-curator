"""Live POI discovery, separate from the reproducible Phase-0 fixtures."""
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from tools import _haversine

AREAS = {"tempe": {"name": "Tempe", "lat": 33.4255, "lon": -111.9400},
         "phoenix": {"name": "Downtown Phoenix", "lat": 33.4484, "lon": -112.0740},
         "metro": {"name": "Phoenix / Tempe metro", "lat": 33.4484, "lon": -112.0100}}
KINDS = {"dinner": {"restaurant", "fast_food"}, "dessert": {"ice_cream"},
         "cafe": {"cafe"}, "bar": {"bar", "pub"}, "after": {"ice_cream", "cafe", "bar", "pub"}}
CATEGORIES = {"restaurant": "restaurant", "fast_food": "restaurant", "ice_cream": "dessert",
              "cafe": "cafe", "bar": "bar", "pub": "bar"}
CUISINES = {"indian", "italian", "mexican", "chinese", "thai", "japanese", "mediterranean", "american"}


def requested_cuisine(text, explicit=""):
    if explicit:
        return explicit
    matches = [cuisine for cuisine in CUISINES if re.search(r"\b" + cuisine + r"\b", text.lower())]
    return matches[0] if len(matches) == 1 else ""


class DiscoveryError(RuntimeError):
    pass


def request_json(url, data=None):
    request = urllib.request.Request(url, data=data, headers={
        "User-Agent": "NightOutCurator-course-prototype/0.3",
        "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(5_000_001)
        if len(body) > 5_000_000:
            raise DiscoveryError("Venue response too large; narrow the search area.")
        return json.loads(body)
    except urllib.error.HTTPError as error:
        raise DiscoveryError(f"Venue service returned HTTP {error.code}; try a smaller area or retry later.") from None
    except (OSError, ValueError):
        raise DiscoveryError("Venue service unavailable; retry later. No fixture fallback was used.") from None


def normalize_osm(elements, lat, lon):
    venues = []
    for element in elements:
        tags = element.get("tags", {})
        amenity = tags.get("amenity")
        if amenity not in CATEGORIES or not tags.get("name"):
            continue
        if tags.get("disused") == "yes" or tags.get("opening_hours", "").strip().lower() == "closed":
            continue
        point = element.get("center", element)
        if not isinstance(point.get("lat"), (int, float)) or not isinstance(point.get("lon"), (int, float)):
            continue
        identity = f"{element['type']}/{element['id']}"
        address = " ".join(tags.get(key, "") for key in ["addr:housenumber", "addr:street", "addr:city"]).strip()
        website = tags.get("website") or tags.get("contact:website")
        venues.append({"id": "osm:" + identity, "name": tags["name"], "category": CATEGORIES[amenity],
                       "cuisine": tags.get("cuisine", ""), "lat": point["lat"], "lon": point["lon"],
                       "address": address, "website": website, "opening_hours": tags.get("opening_hours"),
                       "vegan_tag": tags.get("diet:vegan") in {"yes", "only"},
                       "source": "OpenStreetMap / Overpass", "source_url": "https://www.openstreetmap.org/" + identity,
                       "distance_m": round(_haversine(lat, lon, point["lat"], point["lon"])),
                       "verification": "Map listing; operating status and menu not independently verified"})
    return venues


def geoapify_venues(kinds, lat, lon, radius_m, limit, cuisine=""):
    mapping = {"dinner": "catering.restaurant", "dessert": "catering.ice_cream", "cafe": "catering.cafe",
               "bar": "catering.bar", "after": "catering.cafe,catering.bar,catering.ice_cream"}
    if cuisine:
        mapping["dinner"] = "catering.restaurant." + cuisine
    categories = sorted(set(",".join(mapping[kind] for kind in kinds).split(",")))
    parameters = {"categories": ",".join(categories), "filter": f"circle:{lon},{lat},{int(radius_m)}",
                  "bias": f"proximity:{lon},{lat}", "limit": int(limit), "apiKey": os.environ["GEOAPIFY_KEY"]}
    response = request_json("https://api.geoapify.com/v2/places?" + urllib.parse.urlencode(parameters))
    values = []
    retrieved = datetime.now(timezone.utc).isoformat()
    for feature in response.get("features", []):
        properties = feature.get("properties", {})
        identity = properties.get("place_id")
        if not identity or not properties.get("name") or properties.get("lat") is None or properties.get("lon") is None:
            continue
        category_tags = properties.get("categories", [])
        category = ("dessert" if "catering.ice_cream" in category_tags else "cafe" if "catering.cafe" in category_tags
                    else "bar" if "catering.bar" in category_tags else "restaurant")
        raw = properties.get("datasource", {}).get("raw", {})
        osm_type = raw.get("osm_type")
        osm_id = raw.get("osm_id")
        source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}" if osm_type in {"node", "way", "relation"} and osm_id else "https://www.geoapify.com/"
        values.append({"id": "geoapify:" + identity, "name": properties["name"], "category": category,
                       "lat": properties["lat"], "lon": properties["lon"], "cuisine": raw.get("cuisine") or (cuisine if category == "restaurant" else ""),
                       "address": properties.get("formatted", ""), "website": properties.get("website") or raw.get("website"),
                       "opening_hours": properties.get("opening_hours") or raw.get("opening_hours"),
                       "source": "Geoapify", "source_url": source_url, "retrieved_at": retrieved,
                       "distance_m": round(_haversine(lat, lon, properties["lat"], properties["lon"])),
                       "verification": "Provider listing; operating status and menu not independently verified"})
    values = list({venue["id"]: venue for venue in values}.values())
    return {"venues": values, "source": "Geoapify", "retrieved_at": retrieved,
            "matching_count": None, "returned_count": len(values), "truncated": len(response.get("features", [])) >= limit,
            "radius_m": radius_m, "coverage_note": "Bounded provider results; total matching count unavailable."}


def discover_venues(kinds, lat, lon, radius_m=5000, limit=60, cuisine=""):
    if cuisine and cuisine not in CUISINES:
        raise ValueError("Unsupported cuisine filter")
    if not kinds or any(kind not in KINDS for kind in kinds):
        raise ValueError("Unsupported venue categories")
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in [lat, lon, radius_m, limit]):
        raise ValueError("Search bounds must be finite numbers")
    if not 33.1 <= lat <= 33.9 or not -112.5 <= lon <= -111.5 or not 500 <= radius_m <= 30000 or not 1 <= limit <= 120:
        raise ValueError("Search must be within the Phoenix/Tempe region with radius 0.5-30 km and limit 1-120")
    if os.getenv("GEOAPIFY_KEY", "").strip():
        return geoapify_venues(kinds, lat, lon, radius_m, limit, cuisine)
    amenities = sorted(set().union(*(KINDS[kind] for kind in kinds)))
    pattern = "|".join(amenities)
    query = (f'[out:json][timeout:20];nwr(around:{int(radius_m)},{lat},{lon})'
             f'[amenity~"^({pattern})$"];out center tags;')
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    endpoints = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
    response = None
    endpoint = None
    for endpoint in endpoints:
        try:
            response = request_json(endpoint, data)
            break
        except DiscoveryError:
            continue
    if response is None:
        raise DiscoveryError("Public venue services unavailable; retry later. No fixture fallback was used.")
    if response.get("remark"):
        raise DiscoveryError("Venue query was incomplete; narrow the area and retry.")
    venues = normalize_osm(response.get("elements", []), lat, lon)
    if cuisine:
        venues = [venue for venue in venues if venue["category"] != "restaurant" or cuisine in venue["cuisine"].lower().split(";")]
    venues.sort(key=lambda venue: (venue["distance_m"], venue["id"]))
    unique = {venue["id"]: venue for venue in venues}
    values = list(unique.values())
    fetched_at = datetime.now(timezone.utc).isoformat()
    for venue in values:
        venue["retrieved_at"] = fetched_at
        return {"venues": values[:int(limit)], "source": "OpenStreetMap / Overpass", "retrieved_at": fetched_at,
            "endpoint": endpoint,
            "matching_count": len(values), "returned_count": min(len(values), int(limit)),
            "truncated": len(values) > limit, "radius_m": radius_m,
            "coverage_note": "Named mapped food/drink POIs within the selected radius; not an exhaustive business directory."}
