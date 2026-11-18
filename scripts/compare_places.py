"""Bounded provider comparison; save metrics only, never raw Google Places content."""
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from discovery import AREAS, CUISINES, DiscoveryError, geoapify_venues
from tools import _haversine

FIELDS = "places.id,places.displayName,places.formattedAddress,places.location,places.websiteUri,places.regularOpeningHours,places.currentOpeningHours,places.businessStatus,places.priceLevel,places.priceRange,places.servesVegetarianFood,nextPageToken"


def google_places(area, cuisine, radius_m, limit):
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        raise DiscoveryError("GOOGLE_MAPS_API_KEY is missing; add it privately to .env.")
    body = {"textQuery": f"{cuisine} restaurants in {area['name']}, Arizona",
            "includedType": "restaurant", "strictTypeFiltering": True, "pageSize": limit,
            "locationBias": {"circle": {"center": {"latitude": area["lat"], "longitude": area["lon"]},
                                        "radius": radius_m}}}
    request = urllib.request.Request("https://places.googleapis.com/v1/places:searchText",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "X-Goog-Api-Key": key,
                                              "X-Goog-FieldMask": FIELDS})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read(2_000_001)
        if len(content) > 2_000_000:
            raise DiscoveryError("Google response exceeds the comparison size limit.")
        data = json.loads(content)
    except urllib.error.HTTPError as error:
        raise DiscoveryError(f"Google HTTP {error.code}; check key access, demo quota and supported fields.") from None
    except (OSError, ValueError):
        raise DiscoveryError("Google Places request failed; check connectivity.") from None
    places = []
    for place in data.get("places", []):
        point = place.get("location", {})
        if point.get("latitude") is None or point.get("longitude") is None:
            continue
        if _haversine(area["lat"], area["lon"], point["latitude"], point["longitude"]) <= radius_m:
            places.append(place)
    return places, bool(data.get("nextPageToken"))


def coverage(records, provider):
    if provider == "google":
        predicates = {"address": lambda venue: bool(venue.get("formattedAddress")),
                      "website": lambda venue: bool(venue.get("websiteUri")),
                      "regular_hours": lambda venue: bool(venue.get("regularOpeningHours")),
                      "current_hours": lambda venue: bool(venue.get("currentOpeningHours")),
                      "business_status": lambda venue: bool(venue.get("businessStatus")),
                      "price_guidance": lambda venue: bool(venue.get("priceLevel") or venue.get("priceRange")),
                      "vegetarian_indicator": lambda venue: isinstance(venue.get("servesVegetarianFood"), bool)}
    else:
        predicates = {"address": lambda venue: bool(venue.get("address")),
                      "website": lambda venue: bool(venue.get("website")),
                      "regular_hours": lambda venue: bool(venue.get("opening_hours")),
                      "current_hours": lambda venue: False,
                      "business_status": lambda venue: False,
                      "price_guidance": lambda venue: False,
                      "vegetarian_indicator": lambda venue: False}
    return {"returned_count": len(records), "fields_present": {
        name: sum(predicate(record) for record in records) for name, predicate in predicates.items()}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", choices=["tempe", "phoenix"], default="tempe")
    parser.add_argument("--cuisine", choices=sorted(CUISINES), default="indian")
    parser.add_argument("--radius-m", type=int, default=5000)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--party-size", type=int, default=2)
    parser.add_argument("--budget-pp", type=float, default=40)
    parser.add_argument("--output", default="artifacts/provider_comparison.json")
    args = parser.parse_args()
    if not 500 <= args.radius_m <= 30000 or not 1 <= args.limit <= 20 or args.party_size < 1 or args.budget_pp <= 0:
        parser.error("Use a radius of 500-30000m, limit 1-20 and positive party size/budget.")
    load_dotenv(ROOT / ".env")
    missing = [name for name in ["GEOAPIFY_KEY", "GOOGLE_MAPS_API_KEY"] if not os.getenv(name, "").strip()]
    if missing:
        parser.exit(1, "Missing configuration: " + ", ".join(missing) + ". No API requests sent.\n")
    area = AREAS[args.area]
    comparisons = []
    for provider in ["geoapify", "google"]:
        started = time.perf_counter()
        try:
            if provider == "geoapify":
                data = geoapify_venues(["dinner"], area["lat"], area["lon"], args.radius_m, args.limit, args.cuisine)
                records, truncated = data["venues"], data["truncated"]
            else:
                records, truncated = google_places(area, args.cuisine, args.radius_m, args.limit)
            result = {"provider": provider, "status": "ok", **coverage(records, provider),
                      "more_results_possible": truncated}
            del records
        except DiscoveryError as error:
            result = {"provider": provider, "status": "error", "error": str(error)}
        result["latency_seconds"] = round(time.perf_counter() - started, 3)
        comparisons.append(result)
    artifact = {"tested_at": datetime.now(timezone.utc).isoformat(),
                "requirement": {"area": args.area, "cuisine": args.cuisine, "radius_m": args.radius_m,
                                "limit": args.limit, "party_size": args.party_size, "budget_pp": args.budget_pp},
                "comparisons": comparisons,
                "limitations": ["One search per provider; no LLM or itinerary generation.",
                                "Geoapify category search vs Google text search with post-filtered radius; ranking differs.",
                                "Counts measure field availability, not correctness, completeness or business freshness.",
                                "Geoapify metrics describe our normalized adapter, not every possible provider field.",
                                "Price guidance is not an exact meal quote; vegetarian does not establish vegan suitability.",
                                "Budget and party size are recorded requirements, not guaranteed provider filters.",
                                "Raw Google place records are not saved or sent to the LLM; no photos/reviews requested."]}
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(json.dumps(artifact, indent=2))


if __name__ == "__main__":
    main()
