import pathlib
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from google_maps import PHOENIX, google_best_leg, google_discovery, google_open_at, google_transit, google_walk, normalize_place
from eval.itinerary import verify


class GoogleMapsTests(unittest.TestCase):
    def place(self):
        return {"id": "new-branch", "displayName": {"text": "Indian restaurant"},
                "location": {"latitude": 33.4255, "longitude": -111.94},
                "types": ["restaurant", "indian_restaurant"], "businessStatus": "OPERATIONAL",
                "priceRange": {"startPrice": {"currencyCode": "USD", "units": "10"},
                               "endPrice": {"currencyCode": "USD", "units": "20"}},
                "servesVegetarianFood": True,
                "regularOpeningHours": {"periods": [{"open": {"day": 0, "hour": 11}, "close": {"day": 0, "hour": 22}}]}}

    def test_price_and_vegetarian_are_not_exact_cost_or_vegan(self):
        venue = normalize_place(self.place(), "dinner", "indian", "2026-11-08T12:00:00+00:00")
        self.assertEqual(venue["price_range_pp"], {"low": 10, "high": 20})
        self.assertNotIn("price_per_person", venue)
        self.assertNotIn("vegan", venue)

    def test_closed_business_not_selected(self):
        place = self.place()
        place["businessStatus"] = "CLOSED_PERMANENTLY"
        self.assertIsNone(normalize_place(place, "dinner", "indian", "2026-11-08T12:00:00+00:00"))

    def test_sunday_hours_at_target_time(self):
        venue = normalize_place(self.place(), "dinner", "indian", "2026-11-08T12:00:00+00:00")
        self.assertTrue(google_open_at(venue, datetime(2026, 11, 8, 19, tzinfo=PHOENIX)))
        self.assertFalse(google_open_at(venue, datetime(2026, 11, 8, 22, tzinfo=PHOENIX)))

    def test_new_provider_id_and_no_photos_or_reviews(self):
        with patch("google_maps.google_request", return_value={"places": [self.place()]}) as call:
            result = google_discovery(["dinner"], 33.4255, -111.94, cuisine="indian")
        self.assertEqual(result["venues"][0]["id"], "google:new-branch")
        self.assertNotIn("reviews", call.call_args.args[2])

    def test_real_route_metadata(self):
        with patch("google_maps.google_request", return_value={"routes": [{"distanceMeters": 800, "duration": "600s"}]}):
            leg = google_walk({"id": "first", "lat": 33.42, "lon": -111.94}, {"id": "second", "lat": 33.43, "lon": -111.94})
        self.assertEqual(leg["minutes"], 10)
        self.assertTrue(leg["verified"])

    def test_budget_guidance_does_not_pass_exact_budget_check(self):
        venue = normalize_place(self.place(), "dinner", "indian", "2026-11-08T12:00:00+00:00")
        constraints = {"stop_types": ["dinner"], "target_hour": 19, "budget_pp": 40,
                       "outing_date": "2026-11-08", "cuisine": "indian"}
        report = verify({"stops": [{"venue_id": venue["id"]}]}, constraints, {venue["id"]: venue})
        self.assertTrue(report["checks"]["hours"])
        self.assertTrue(report["details"]["estimated_within_budget"])
        self.assertFalse(report["checks"]["budget"])

    def test_unverified_google_walking_does_not_pass(self):
        venue = normalize_place(self.place(), "dinner", "indian", "2026-11-08T12:00:00+00:00")
        other = {**venue, "id": "google:other", "category": "cafe"}
        constraints = {"stop_types": ["dinner", "cafe"], "target_hour": 17, "budget_pp": 100,
                       "outing_date": "2026-11-08"}
        report = verify({"stops": [{"venue_id": venue["id"]}, {"venue_id": other["id"]}]}, constraints,
                        {venue["id"]: venue, other["id"]: other})
        self.assertFalse(report["checks"]["travel"])

    def transit_response(self, seconds=1500, line=None):
        line = line or {"name": "ORBIT Mars", "nameShort": "MARS", "vehicle": {"type": "BUS"},
                        "agencies": [{"name": "Valley Metro"}]}
        return {"routes": [{"distanceMeters": 4000, "duration": f"{seconds}s", "legs": [{"steps": [
            {"travelMode": "WALK", "staticDuration": "420s", "distanceMeters": 500},
            {"travelMode": "TRANSIT", "staticDuration": "900s", "distanceMeters": 3400, "transitDetails": {
                "stopDetails": {"departureStop": {"name": "University Dr & College Av"},
                                "arrivalStop": {"name": "Dorsey & Vista Del Cero"}},
                "transitLine": line}}]}]}]}

    def endpoints(self):
        return ({"id": "google:a", "lat": 33.42, "lon": -111.93}, {"id": "google:b", "lat": 33.40, "lon": -111.90})

    def test_transit_steps_classify_orbit_bus_and_rail(self):
        origin, destination = self.endpoints()
        with patch("google_maps.google_request", return_value=self.transit_response()):
            leg = google_transit(origin, destination)
        self.assertEqual([step["mode"] for step in leg["steps"]], ["walk", "orbit"])
        self.assertEqual(leg["steps"][1]["line"], "MARS")
        self.assertEqual(leg["minutes"], 25)
        for vehicle, line, mode in (("BUS", {"name": "Rural/Scottsdale", "nameShort": "72"}, "bus"),
                                    ("LIGHT_RAIL", {"name": "Valley Metro Rail", "nameShort": "A Line"}, "light_rail")):
            with patch("google_maps.google_request",
                       return_value=self.transit_response(line={**line, "vehicle": {"type": vehicle}})):
                self.assertEqual(google_transit(origin, destination)["steps"][1]["mode"], mode)

    def test_walk_steps_merge_and_trip_times(self):
        origin, destination = self.endpoints()
        walk = lambda seconds, meters: {"travelMode": "WALK", "staticDuration": f"{seconds}s", "distanceMeters": meters}
        ride = {"travelMode": "TRANSIT", "staticDuration": "420s", "transitDetails": {
            "stopCount": 4, "headsign": "Marina Heights/Rio Salado",
            "stopDetails": {"departureStop": {"name": "Paseo Del Saber/Apache"}, "arrivalStop": {"name": "Sixth St/Mill"},
                            "departureTime": "2026-11-23T23:39:00Z", "arrivalTime": "2026-11-23T23:46:00Z"},
            "transitLine": {"name": "Marina Heights/Rio Salado", "nameShort": "S", "color": "#6b8e23",
                            "vehicle": {"type": "LIGHT_RAIL"}}}}
        response = {"routes": [{"distanceMeters": 1000, "duration": "720s",
                                "legs": [{"steps": [walk(0, 0), walk(180, 250), ride, walk(60, 80), walk(60, 80)]}]}]}
        with patch("google_maps.google_request", return_value=response):
            leg = google_transit(origin, destination)
        self.assertEqual([step["mode"] for step in leg["steps"]], ["walk", "light_rail", "walk"])
        self.assertEqual(leg["steps"][2]["minutes"], 2)
        self.assertEqual(leg["steps"][1]["stop_count"], 4)
        self.assertTrue(leg["departs"].startswith("2026-11-23T23:36"))
        self.assertTrue(leg["arrives"].startswith("2026-11-23T23:48"))

    def test_best_leg_prefers_faster_transit_else_walk(self):
        origin, destination = self.endpoints()
        walk = {"routes": [{"distanceMeters": 3800, "duration": "2700s"}]}
        with patch("google_maps.google_request", side_effect=[walk, self.transit_response()]):
            leg = google_best_leg(origin, destination, max_walk_m=5000)
        self.assertEqual(leg["mode"], "transit")
        self.assertEqual(leg["alternative"], {"mode": "walk", "minutes": 45})
        quick_walk = {"routes": [{"distanceMeters": 300, "duration": "240s"}]}
        with patch("google_maps.google_request", side_effect=[quick_walk, self.transit_response()]):
            self.assertEqual(google_best_leg(origin, destination, max_walk_m=1200)["mode"], "walk")
        with patch("google_maps.google_request", side_effect=[walk, {}]):
            self.assertEqual(google_best_leg(origin, destination, max_walk_m=5000)["mode"], "walk")

    def test_verified_transit_leg_passes_travel_check(self):
        venue = normalize_place(self.place(), "dinner", "indian", "2026-11-08T12:00:00+00:00")
        other = {**venue, "id": "google:other", "category": "cafe", "lat": 33.40}
        constraints = {"stop_types": ["dinner", "cafe"], "target_hour": 17, "budget_pp": 100,
                       "outing_date": "2026-11-08", "max_walk_m": 500}
        plan = {"stops": [{"venue_id": venue["id"]}, {"venue_id": other["id"]}]}
        leg = {"from_id": venue["id"], "to_id": other["id"], "mode": "transit", "verified": True, "minutes": 25}
        report = verify({**plan, "legs": [leg]}, constraints, {venue["id"]: venue, other["id"]: other})
        self.assertTrue(report["checks"]["travel"])