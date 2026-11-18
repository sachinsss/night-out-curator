import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from discovery import DiscoveryError, discover_venues, normalize_osm, requested_cuisine


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict("os.environ", {"GEOAPIFY_KEY": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def element(self, identity=100, amenity="restaurant"):
        return {"type": "node", "id": identity, "lat": 33.4255, "lon": -111.94,
                "tags": {"name": f"New venue {identity}", "amenity": amenity,
                         "addr:street": "Mill Avenue", "website": "https://example.com"}}

    def test_new_ids_not_fixture_bound(self):
        values = normalize_osm([self.element()], 33.4255, -111.94)
        self.assertEqual(values[0]["id"], "osm:node/100")
        self.assertIn("openstreetmap.org/node/100", values[0]["source_url"])
        self.assertNotIn("price_per_person", values[0])

    def test_pagination_metadata_and_full_ids(self):
        with patch("discovery.request_json", return_value={"elements": [self.element(index) for index in range(20)]}):
            result = discover_venues(["dinner"], 33.4255, -111.94, limit=15)
        self.assertEqual(len(result["venues"]), 15)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["matching_count"], 20)

    def test_way_center_and_closed_excluded(self):
        way = {"type": "way", "id": 8, "center": {"lat": 33.4255, "lon": -111.94},
               "tags": {"name": "Cafe", "amenity": "cafe"}}
        closed = self.element()
        closed["tags"]["opening_hours"] = "closed"
        self.assertEqual(len(normalize_osm([way, closed], 33.4255, -111.94)), 1)

    def test_failed_live_query_does_not_fall_back(self):
        with patch("discovery.request_json", side_effect=DiscoveryError("unavailable")):
            with self.assertRaises(DiscoveryError):
                discover_venues(["dinner"], 33.4255, -111.94)

    def test_outside_region_rejected(self):
        with self.assertRaises(ValueError):
            discover_venues(["dinner"], 0, 0)

    def test_indian_prompt_is_recognized(self):
        text = "make a plan for 2 people with budget of around $40. We'd like dinner, specifically indian cusine"
        self.assertEqual(requested_cuisine(text), "indian")

    def test_geoapify_receives_cuisine_category(self):
        with patch.dict("os.environ", {"GEOAPIFY_KEY": "test-not-real"}), patch("discovery.request_json", return_value={"features": []}) as query:
            discover_venues(["dinner"], 33.4255, -111.94, cuisine="indian")
        self.assertIn("catering.restaurant.indian", query.call_args.args[0])

    def test_geoapify_keeps_complete_branch_ids(self):
        identity = "branch-identity-1234567890-long"
        response = {"features": [{"properties": {"place_id": identity, "name": "New restaurant",
                     "lat": 33.4255, "lon": -111.94, "categories": ["catering.restaurant"],
                     "formatted": "123 Mill Avenue, Tempe", "datasource": {"raw": {}}}}]}
        with patch.dict("os.environ", {"GEOAPIFY_KEY": "test-not-real"}), patch("discovery.request_json", return_value=response):
            result = discover_venues(["dinner"], 33.4255, -111.94)
        self.assertEqual(result["venues"][0]["id"], "geoapify:" + identity)
        self.assertEqual(result["source"], "Geoapify")
