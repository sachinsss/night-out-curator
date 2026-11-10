import unittest
import json
import threading
import urllib.error
import urllib.request
from unittest.mock import patch

from pydantic import ValidationError
from run_ui import UIHandler, UIRequest, ThreadingHTTPServer, browse_request, run_request


class UITests(unittest.TestCase):
    def setUp(self):
        self.payload = {"request": "Vegan dinner and dessert", "stop_types": ["dinner", "dessert"],
                        "budget_pp": 40, "party_size": 4, "target_hour": 19,
                        "max_walk_m": 1200, "vegan_required": True, "mock": True}

    def test_mock_ui_run(self):
        result = run_request(self.payload)
        self.assertTrue(result["report"]["valid"])
        self.assertEqual(result["scenario"]["constraints"]["stop_types"], ["dinner", "dessert"])
        self.assertEqual(result["metrics"]["llm_calls"], 0)

    def test_four_stop_limit(self):
        self.payload["stop_types"] = ["dinner"] * 5
        with self.assertRaises(ValidationError):
            UIRequest.model_validate(self.payload)

    def test_invalid_budget(self):
        self.payload["budget_pp"] = -1
        with self.assertRaises(ValidationError):
            UIRequest.model_validate(self.payload)

    def test_real_mode_is_forwarded(self):
        self.payload["mock"] = False
        with patch("run_ui.MultiAgentRunner") as runner:
            runner.return_value.run.return_value = {}
            run_request(self.payload)
        runner.assert_called_once_with(mock=False, max_attempts=2, live_discovery=False)

    def test_live_area_passed_to_provider(self):
        self.payload.update(data_mode="live", search_area="phoenix", radius_m=12000)
        with patch("run_ui.discover_venues", return_value={"venues": [], "source": "test"}) as discover:
            result = browse_request(self.payload)
        self.assertEqual(result["area"]["name"], "Downtown Phoenix")
        self.assertEqual(discover.call_args.args[1:4], (33.4484, -112.0740, 12000))

    def test_fixture_browse_has_explicit_source(self):
        result = browse_request(self.payload)
        self.assertEqual(result["data_mode"], "fixture")
        self.assertTrue(all(venue["source"] == "Fixture catalog" for venue in result["venues"]))


class HTTPBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), UIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_env_file_not_served(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(self.url + "/.env")
        self.assertEqual(caught.exception.code, 404)

    def test_foreign_origin_rejected(self):
        request = urllib.request.Request(self.url + "/api/run", data=b"{}",
                                         headers={"Content-Type": "application/json", "Origin": "https://example.com"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 403)

    def test_config_has_no_credentials(self):
        with urllib.request.urlopen(self.url + "/api/config") as response:
            config = json.load(response)
        self.assertEqual(set(config), {"provider", "model", "region", "stop_limit", "discovery_provider"})

    def test_stream_returns_progress_and_result(self):
        payload = {"request": "Dinner", "stop_types": ["dinner"], "budget_pp": 40,
                   "party_size": 2, "target_hour": 19, "max_walk_m": 1200, "mock": True}
        request = urllib.request.Request(self.url + "/api/run", data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json", "Accept": "application/x-ndjson"})
        with urllib.request.urlopen(request) as response:
            events = [json.loads(line) for line in response]
        self.assertEqual(events[0]["type"], "progress")
        self.assertEqual(events[-1]["type"], "result")
        self.assertTrue(events[-1]["result"]["report"]["valid"])
