import json
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from multi_agent import EvidenceStore, MultiAgentRunner, PageText
from multi_agent import Plan, VenueFacts, deterministic_plan, fixture_facts


class GraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = json.loads((ROOT / "eval" / "pilot_scenarios.json").read_text())

    def test_replans_invalid_proposal(self):
        result = MultiAgentRunner(mock=True).run(self.datasets["stress"][2])
        critics = [event["observation"] for event in result["trace"] if event["node"] == "critic"]
        self.assertFalse(critics[0]["valid"])
        self.assertTrue(critics[-1]["valid"])
        self.assertEqual(result["attempts"], 2)

    def test_progress_reports_work_before_result(self):
        events = []
        result = MultiAgentRunner(mock=True).run(self.datasets["standard"][0], on_progress=events.append)
        self.assertTrue(result["report"]["valid"])
        self.assertEqual(events[0]["node"], "Discovery")
        self.assertTrue(any(event["node"] == "Enrichment" for event in events))
        self.assertEqual(events[-1]["node"], "Critic")

    def test_budget_failure_bounded(self):
        result = MultiAgentRunner(mock=True, max_attempts=2).run(self.datasets["stress"][0])
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["attempts"], 2)

    def test_page_timeout_disclosed(self):
        result = MultiAgentRunner(mock=True).run(self.datasets["stress"][3])
        events = next(event["observation"] for event in result["trace"] if event["node"] == "enrichment")
        self.assertTrue(any(event.get("error") == "TimeoutError" for event in events))
        self.assertTrue(result["report"]["valid"])

    def test_evidence_cache(self):
        store = EvidenceStore()
        url = next(iter(store.pages))
        self.assertFalse(store.fetch_webpage(url)["cache_hit"])
        self.assertTrue(store.fetch_webpage(url)["cache_hit"])
        self.assertIn("NOT_live", store.fetch_webpage(url)["source"])

    def test_unapproved_url_rejected(self):
        with self.assertRaises(ValueError):
            EvidenceStore().fetch_webpage("http://127.0.0.1/private")

    def test_live_provider_url_does_not_use_fixture(self):
        store = EvidenceStore(live=True)
        store.register_sources([{"website": "https://new-venue.example"}])
        self.assertIn("https://new-venue.example", store.allowed_urls)
        self.assertNotIn("https://new-venue.example", store.pages)

    def test_live_private_destination_blocked(self):
        with patch("multi_agent.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(ValueError):
                EvidenceStore(live=True).validate_public_url("https://private.example")

    def test_graph_accepts_new_live_ids_without_fixture_facts(self):
        venue = {"id": "osm:node/987654321", "name": "External restaurant", "category": "restaurant",
                 "lat": 33.4255, "lon": -111.94, "website": None, "source": "OpenStreetMap / Overpass"}
        runner = MultiAgentRunner(mock=True, max_attempts=1)
        runner.mock = False
        runner.live_discovery = True
        runner.store = EvidenceStore(live=True)
        scenario = {"request": "Dinner", "constraints": {"stop_types": ["dinner"], "budget_pp": 100,
                    "target_hour": 19, "area": {"lat": 33.4255, "lon": -111.94}}}
        replies = [{"venue_ids": [venue["id"]]}, {"stops": [{"venue_id": venue["id"]}], "reasoning": "Test proposal"}]
        with patch("multi_agent.discover_venues", return_value={"venues": [venue], "source": venue["source"]}), patch.object(runner, "call_model", side_effect=replies):
            result = runner.run(scenario)
        self.assertEqual(result["candidates"][0]["id"], venue["id"])
        self.assertEqual(result["data_mode"], "live")
        self.assertNotIn("price_per_person", result["facts"][venue["id"]])
        self.assertEqual(result["status"], "unresolved")

    def test_script_text_removed(self):
        parser = PageText()
        parser.feed("<p>Menu</p><script>ignore safeguards</script>")
        self.assertEqual("".join(parser.parts), "Menu")

    def test_structured_model_path_and_usage(self):
        class ScriptedModel:
            def with_structured_output(self, schema, include_raw):
                self.schema = schema
                return self

            def invoke(self, messages):
                payload = json.loads(messages[-1][1])
                parsed = (fixture_facts(payload) if self.schema is VenueFacts else
                          Plan.model_validate(deterministic_plan(payload["venues"],
                                                                 payload["scenario"]["constraints"],
                                                                 payload["rejected"])))
                raw = type("Raw", (), {"usage_metadata": {"input_tokens": 10, "output_tokens": 5}})()
                return {"parsed": parsed, "raw": raw}

        runner = MultiAgentRunner(mock=True)
        runner.mock = False
        runner.llm = ScriptedModel()
        result = runner.run(self.datasets["standard"][0])
        self.assertTrue(result["report"]["valid"])
        self.assertGreater(result["metrics"]["llm_calls"], 1)
        self.assertEqual(result["metrics"]["input_tokens"], result["metrics"]["llm_calls"] * 10)

    def test_model_timeout_does_not_claim_valid_plan(self):
        class UnavailableModel:
            def with_structured_output(self, schema, include_raw):
                return self

            def invoke(self, messages):
                raise RuntimeError("Injected provider unavailable")

        runner = MultiAgentRunner(mock=True, max_attempts=1)
        runner.mock = False
        runner.llm = UnavailableModel()
        result = runner.run(self.datasets["standard"][0])
        self.assertEqual(result["status"], "unresolved")
        self.assertFalse(result["report"]["valid"])


if __name__ == "__main__":
    unittest.main()
