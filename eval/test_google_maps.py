import pathlib
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from google_maps import PHOENIX, google_discovery, google_open_at, google_walk, normalize_place
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
