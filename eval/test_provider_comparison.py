import json
import os
import unittest
from unittest.mock import patch

from scripts.compare_places import DiscoveryError, coverage, google_places


class ProviderComparisonTests(unittest.TestCase):
    def test_missing_key_blocks_request(self):
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": ""}):
            with self.assertRaises(DiscoveryError):
                google_places({"name": "Tempe", "lat": 33.4255, "lon": -111.94}, "indian", 5000, 10)

    def test_false_vegetarian_value_counts_as_known(self):
        summary = coverage([{"servesVegetarianFood": False}, {}], "google")
        self.assertEqual(summary["fields_present"]["vegetarian_indicator"], 1)
        self.assertEqual(summary["returned_count"], 2)

    def test_google_radius_and_field_mask(self):
        payload = {"places": [{"id": "near", "location": {"latitude": 33.4255, "longitude": -111.94}},
                              {"id": "far", "location": {"latitude": 34, "longitude": -112}}]}
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return json.dumps(payload).encode()

        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-not-real"}), patch("scripts.compare_places.urllib.request.urlopen", return_value=Response()) as call:
            places, _ = google_places({"name": "Tempe", "lat": 33.4255, "lon": -111.94}, "indian", 5000, 10)
        self.assertEqual([place["id"] for place in places], ["near"])
        request = call.call_args.args[0]
        self.assertNotIn("reviews", request.get_header("X-goog-fieldmask"))
        self.assertEqual(json.loads(request.data)["textQuery"], "indian restaurants in Tempe, Arizona")
