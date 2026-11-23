"""Google Maps runtime adapters. Do not persist raw Places content."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from discovery import CUISINES, DiscoveryError
from tools import _haversine

PHOENIX = timezone(timedelta(hours=-7))
PLACE_FIELDS = "places.id,places.displayName,places.formattedAddress,places.location,places.primaryType,places.types,places.googleMapsUri,places.websiteUri,places.regularOpeningHours,places.currentOpeningHours,places.businessStatus,places.priceLevel,places.priceRange,places.servesVegetarianFood,nextPageToken"


def google_request(endpoint, body, fields):
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        raise DiscoveryError("Configure GOOGLE_MAPS_API_KEY for Google Maps.")
    request = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": fields})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read(3_000_001)
        if len(data) > 3_000_000:
            raise DiscoveryError("Google response is too large; narrow the search.")
        return json.loads(data)
    except urllib.error.HTTPError as error:
        raise DiscoveryError(f"Google returned HTTP {error.code}. Check enabled APIs, demo quotas and key restrictions.") from None
    except (OSError, ValueError):
        raise DiscoveryError("Google request unavailable; no fixture fallback was used.") from None


def money_value(value):
    if not value or value.get("currencyCode") != "USD":
        return None
    try:
        amount = int(value.get("units", 0)) + int(value.get("nanos", 0)) / 1_000_000_000
        return amount if amount >= 0 else None
    except (TypeError, ValueError):
        return None


def normalize_place(place, kind, cuisine, retrieved):
    location = place.get("location", {})
    if not place.get("id") or not place.get("displayName", {}).get("text") or location.get("latitude") is None or location.get("longitude") is None:
        return None
    if place.get("businessStatus") in {"CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"}:
        return None
    types = place.get("types", [])
    category = {"dinner": "restaurant", "dessert": "dessert", "cafe": "cafe", "bar": "bar"}.get(kind)
    if kind == "after":
        category = "bar" if "bar" in types else "dessert" if "ice_cream_shop" in types or "dessert_shop" in types else "cafe" if "cafe" in types or "coffee_shop" in types else None
    if category is None:
        return None
    if kind == "dessert" and not set(types).intersection({"dessert_shop", "ice_cream_shop", "bakery"}):
        return None
    raw_range = place.get("priceRange", {})
    low, high = money_value(raw_range.get("startPrice")), money_value(raw_range.get("endPrice"))
    price_range = {"low": low, "high": high} if low is not None or high is not None else None
    cuisine_value = cuisine if kind == "dinner" and cuisine and (cuisine + "_restaurant") in types else ""
    regular = place.get("regularOpeningHours", {})
    return {"id": "google:" + place["id"], "google_place_id": place["id"],
            "name": place["displayName"]["text"], "category": category,
            "lat": location["latitude"], "lon": location["longitude"], "cuisine": cuisine_value,
            "address": place.get("formattedAddress", ""), "website": place.get("websiteUri"),
            "source": "Google Maps", "provider": "google", "source_url": place.get("googleMapsUri", "https://maps.google.com"),
            "retrieved_at": retrieved, "business_status": place.get("businessStatus"),
            "opening_hours": " / ".join(regular.get("weekdayDescriptions", [])),
            "google_regular_hours": regular, "google_current_hours": place.get("currentOpeningHours", {}),
            "price_level": place.get("priceLevel"), "price_range_pp": price_range,
            "vegetarian_indicator": place.get("servesVegetarianFood"),
            "verification": "Google listing; price guidance is not a menu quote; vegan suitability not confirmed"}


def google_discovery(kinds, lat, lon, radius_m=5000, limit=60, cuisine="", area_name="Tempe"):
    if cuisine and cuisine not in CUISINES:
        raise ValueError("Unsupported cuisine")
    mapping = {"dinner": (f"{cuisine} restaurants", "restaurant"), "dessert": ("dessert places", ""),
               "cafe": ("cafes", "cafe"), "bar": ("bars", "bar"), "after": ("cafes bars and dessert places", "")}
    if not kinds or any(kind not in mapping for kind in kinds):
        raise ValueError("Unsupported Google search category")
    retrieved = datetime.now(timezone.utc).isoformat()
    venues = {}
    request_count = 0
    more_possible = False
    for kind in dict.fromkeys(kinds):
        text, place_type = mapping[kind]
        body = {"textQuery": f"{text.strip()} in {area_name}, Arizona", "pageSize": min(20, limit),
                "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": radius_m}}}
        if place_type:
            body.update(includedType=place_type, strictTypeFiltering=True)
        result = google_request("https://places.googleapis.com/v1/places:searchText", body, PLACE_FIELDS)
        more_possible = more_possible or bool(result.get("nextPageToken"))
        request_count += 1
        for place in result.get("places", []):
            venue = normalize_place(place, kind, cuisine, retrieved)
            if not venue:
                continue
            distance = _haversine(lat, lon, venue["lat"], venue["lon"])
            if distance <= radius_m:
                venue["distance_m"] = round(distance)
                venues.setdefault(venue["id"], venue)
    values = sorted(venues.values(), key=lambda venue: venue["distance_m"])
    return {"venues": values[:limit], "source": "Google Maps", "provider": "google",
            "retrieved_at": retrieved, "returned_count": min(len(values), limit), "matching_count": None,
            "truncated": more_possible or len(values) > limit, "request_count": request_count, "radius_m": radius_m,
            "coverage_note": "At most one 20-result page per requested category; not exhaustive. Google Maps attribution applies."}


def google_open_at(venue, moment):
    if venue.get("business_status") != "OPERATIONAL":
        return None
    retrieved_date = datetime.fromisoformat(venue["retrieved_at"]).astimezone(PHOENIX).date()
    hours = venue.get("google_current_hours") if retrieved_date <= moment.date() < retrieved_date + timedelta(days=7) else None
    periods = (hours or venue.get("google_regular_hours", {})).get("periods")
    if not periods:
        return None
    target = ((moment.weekday() + 1) % 7) * 1440 + moment.hour * 60 + moment.minute
    for period in periods:
        opening = period.get("open", {})
        closing = period.get("close")
        if not closing and opening.get("day") == 0 and opening.get("hour", 0) == 0 and opening.get("minute", 0) == 0:
            return True
        if not closing or "day" not in opening or "day" not in closing:
            continue
        start = opening["day"] * 1440 + opening.get("hour", 0) * 60 + opening.get("minute", 0)
        end = closing["day"] * 1440 + closing.get("hour", 0) * 60 + closing.get("minute", 0)
        if end <= start:
            end += 7 * 1440
        if start <= target < end or start <= target + 7 * 1440 < end:
            return True
    return False


ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
TRANSIT_FIELDS = ("routes.distanceMeters,routes.duration,routes.legs.steps.travelMode,routes.legs.steps.staticDuration,"
                  "routes.legs.steps.distanceMeters,routes.legs.steps.transitDetails")
RAIL_VEHICLES = {"LIGHT_RAIL", "TRAM", "SUBWAY", "RAIL", "HEAVY_RAIL", "COMMUTER_TRAIN", "METRO_RAIL", "MONORAIL"}
ORBIT_NAMES = {"mercury", "venus", "earth", "mars", "jupiter", "saturn", "neptune", "uranus"}


def _seconds(value):
    return float(str(value).removesuffix("s"))


def _route_body(origin, destination, mode, departure=None):
    body = {"origin": {"location": {"latLng": {"latitude": origin["lat"], "longitude": origin["lon"]}}},
            "destination": {"location": {"latLng": {"latitude": destination["lat"], "longitude": destination["lon"]}}},
            "travelMode": mode, "units": "METRIC"}
    if departure:
        body["departureTime"] = departure.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return body


def classify_transit_step(details):
    """Map a Routes API transitDetails block to bus / orbit / light_rail."""
    line = details.get("transitLine", {})
    vehicle = line.get("vehicle", {}).get("type", "")
    name, short = line.get("name", ""), line.get("nameShort", "")
    label = (short or name).strip()
    agencies = " ".join(agency.get("name", "") for agency in line.get("agencies", [])).lower()
    words = {name.lower().replace("orbit", "").strip(), short.lower().replace("orbit", "").strip()}
    if "orbit" in f"{name} {short}".lower() or ("valley metro" in agencies and words & ORBIT_NAMES):
        mode = "orbit"
    elif vehicle in RAIL_VEHICLES:
        mode = "light_rail"
    else:
        mode = "bus"
    return mode, label


def _transit_steps(route):
    steps = []
    for step in (route.get("legs") or [{}])[0].get("steps", []):
        minutes = _seconds(step.get("staticDuration", "0s")) / 60
        details = step.get("transitDetails")
        if step.get("travelMode") == "TRANSIT" and details:
            mode, label = classify_transit_step(details)
            stops = details.get("stopDetails", {})
            line = details.get("transitLine", {})
            steps.append({"mode": mode, "line": label, "line_name": line.get("name", ""), "color": line.get("color", ""),
                          "headsign": details.get("headsign", ""), "stop_count": details.get("stopCount"),
                          "from_stop": stops.get("departureStop", {}).get("name", ""),
                          "to_stop": stops.get("arrivalStop", {}).get("name", ""),
                          "departs": stops.get("departureTime", ""), "arrives": stops.get("arrivalTime", ""),
                          "minutes": round(minutes, 1)})
        elif steps and steps[-1]["mode"] == "walk":
            steps[-1]["minutes"] += minutes
            steps[-1]["distance_m"] += round(step.get("distanceMeters", 0))
        else:
            steps.append({"mode": "walk", "minutes": minutes, "distance_m": round(step.get("distanceMeters", 0))})
    for step in steps:
        step["minutes"] = round(step["minutes"], 1)
    return [step for step in steps if step["mode"] != "walk" or step["minutes"] >= 0.5]


def describe_steps(steps):
    names = {"orbit": "ORBIT", "light_rail": "Light rail", "bus": "Bus"}
    parts = []
    for step in steps:
        if step["mode"] == "walk":
            parts.append(f"Walk {round(step['minutes'])} min")
        else:
            parts.append(f"{names[step['mode']]} {step['line']} from {step['from_stop']} to {step['to_stop']}".strip())
    return " > ".join(parts)


def _trip_times(steps):
    """Door-to-door departure and arrival, from the first and last vehicle times plus walks around them."""
    rides = [index for index, step in enumerate(steps) if step["mode"] != "walk"]
    if not rides or not steps[rides[0]]["departs"] or not steps[rides[-1]]["arrives"]:
        return "", ""
    parse = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
    lead = sum(step["minutes"] for step in steps[:rides[0]])
    tail = sum(step["minutes"] for step in steps[rides[-1] + 1:])
    return ((parse(steps[rides[0]]["departs"]) - timedelta(minutes=lead)).isoformat(),
            (parse(steps[rides[-1]]["arrives"]) + timedelta(minutes=tail)).isoformat())


def google_transit(origin, destination, departure=None):
    response = google_request(ROUTES_URL, _route_body(origin, destination, "TRANSIT", departure), TRANSIT_FIELDS)
    routes = response.get("routes", [])
    if not routes:
        raise DiscoveryError("Google returned no transit route.")
    try:
        steps = _transit_steps(routes[0])
        seconds = _seconds(routes[0]["duration"])
        distance = float(routes[0]["distanceMeters"])
        departs, arrives = _trip_times(steps)
    except (KeyError, ValueError, AttributeError):
        raise DiscoveryError("Google transit route is missing duration or steps.") from None
    if not any(step["mode"] != "walk" for step in steps):
        raise DiscoveryError("Google transit route has no transit vehicle.")
    return {"from_id": origin["id"], "to_id": destination["id"], "mode": "transit", "verified": True,
            "distance_m": round(distance), "minutes": round(seconds / 60, 1), "steps": steps,
            "departs": departs, "arrives": arrives,
            "summary": describe_steps(steps), "source": "Google Routes"}


def google_best_leg(origin, destination, departure=None, max_walk_m=1200, allow_transit=True):
    """Fastest verified option between two venues: walking, or transit when it is quicker."""
    walk = google_walk(origin, destination)
    if not allow_transit:
        return walk
    try:
        transit_leg = google_transit(origin, destination, departure)
    except DiscoveryError:
        return walk
    candidates = [transit_leg] + ([walk] if walk["distance_m"] <= max_walk_m else [])
    best = min(candidates, key=lambda leg: leg["minutes"])
    best["alternative"] = {"mode": "walk" if best is transit_leg else "transit",
                           "minutes": (walk if best is transit_leg else transit_leg)["minutes"]}
    return best


def google_walk(origin, destination):
    body = _route_body(origin, destination, "WALK")
    response = google_request(ROUTES_URL, body, "routes.distanceMeters,routes.duration")
    routes = response.get("routes", [])
    if not routes:
        raise DiscoveryError("Google returned no walking route.")
    route = routes[0]
    try:
        seconds = float(route["duration"].removesuffix("s"))
        distance = float(route["distanceMeters"])
    except (KeyError, ValueError, AttributeError):
        raise DiscoveryError("Google walking route is missing distance or duration.") from None
    return {"from_id": origin["id"], "to_id": destination["id"], "mode": "walk", "verified": True,
            "distance_m": round(distance), "minutes": round(seconds / 60, 1), "source": "Google Routes"}