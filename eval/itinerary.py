"""Independent pilot evaluator for variable-length itineraries."""
from eval.evaluate import GT, _haversine


def requested_types(constraints):
    return constraints.get("stop_types", ["dinner", "after"])


def verify(plan, constraints, facts=None):
    facts = GT if facts is None else facts
    stops = plan.get("stops", [])
    types = requested_types(constraints)
    venues = [facts.get(stop.get("venue_id")) for stop in stops]
    complete = len(stops) == len(types) and bool(stops) and all(venues)
    categories = {"dinner": {"restaurant"}, "after": {"bar", "dessert", "cafe"},
                  "bar": {"bar"}, "dessert": {"dessert"}, "cafe": {"cafe"}}
    structure = bool(complete and len({stop.get("venue_id") for stop in stops}) == len(stops)
                     and all(venue["category"] in categories.get(kind, {kind})
                             for venue, kind in zip(venues, types)))
    checks = {"structure": structure, "budget": False, "dietary": False,
              "hours": False, "travel": False}
    cuisine = constraints.get("cuisine", "")
    if cuisine:
        checks["cuisine"] = bool(complete and all(
            cuisine in venue.get("cuisine", "").lower().split(";")
            for venue, kind in zip(venues, types) if kind == "dinner"))
    details = {}
    if complete:
        total = sum(venue.get("price_per_person", float("inf")) for venue in venues)
        checks["budget"] = total <= constraints["budget_pp"]
        details["total_pp"] = total if total != float("inf") else None
        checks["dietary"] = not constraints.get("vegan_required") or all(
            venue.get("vegan") is True for venue in venues)
        interval = constraints.get("stop_interval_hours", 2)
        hours = [constraints["target_hour"] + index * interval for index in range(len(stops))]
        hours_ok = []
        for venue, hour in zip(venues, hours):
            if venue.get("provider") == "google":
                from datetime import datetime, timedelta
                from google_maps import PHOENIX, google_open_at

                outing_date = constraints.get("outing_date") or datetime.now(PHOENIX).date().isoformat()
                moment = datetime.fromisoformat(outing_date).replace(tzinfo=PHOENIX) + timedelta(hours=hour)
                hours_ok.append(google_open_at(venue, moment) is True)
            else:
                hours_ok.append(venue.get("close_hour", -1) > hour)
        checks["hours"] = all(hours_ok)
        ranges = [venue.get("price_range_pp") for venue in venues]
        if all(price and price.get("low") is not None and price.get("high") is not None for price in ranges):
            details["estimated_range_pp"] = {"low": sum(price["low"] for price in ranges),
                                             "high": sum(price["high"] for price in ranges)}
            details["estimated_within_budget"] = details["estimated_range_pp"]["high"] <= constraints["budget_pp"]
        legs = plan.get("legs", [])
        travel = []
        for index, (origin, destination) in enumerate(zip(venues, venues[1:])):
            distance = _haversine((origin["lat"], origin["lon"]),
                                  (destination["lat"], destination["lon"]))
            walk_ok = distance <= constraints.get("max_walk_m", 1200)
            leg = legs[index] if index < len(legs) else {}
            if origin.get("provider") == "google" or destination.get("provider") == "google":
                walk_ok = bool(leg.get("mode") == "walk" and leg.get("verified") is True
                               and leg.get("from_id") == stops[index]["venue_id"]
                               and leg.get("to_id") == stops[index + 1]["venue_id"]
                               and 0 <= leg.get("distance_m", float("inf")) <= constraints.get("max_walk_m", 1200))
            transit_ok = (constraints.get("allow_transit", False)
                          and leg.get("mode") == "transit" and leg.get("verified") is True
                          and leg.get("from_id") == stops[index]["venue_id"]
                          and leg.get("to_id") == stops[index + 1]["venue_id"]
                          and 0 <= leg.get("minutes", float("inf"))
                          <= constraints.get("max_transit_min", 20))
            travel.append(bool(walk_ok or transit_ok))
        checks["travel"] = all(travel)
        details["arrival_hours"] = hours
    return {"checks": checks, "details": details,
            "score": sum(checks.values()) / len(checks), "valid": all(checks.values())}
