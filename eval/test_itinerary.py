import unittest

from eval.itinerary import verify


class ItineraryTests(unittest.TestCase):
    def setUp(self):
        self.constraints = {"stop_types": ["dinner", "dessert", "bar"],
                            "target_hour": 19, "budget_pp": 50, "max_walk_m": 1200}
        self.plan = {"stops": [{"venue_id": name} for name in
                               ["pita_jungle", "gelato_spot", "caseys"]]}

    def test_three_stops(self):
        self.assertTrue(verify(self.plan, self.constraints)["valid"])

    def test_requested_cuisine_is_checked(self):
        self.constraints["cuisine"] = "indian"
        self.assertFalse(verify(self.plan, self.constraints)["checks"]["cuisine"])

    def test_missing_stop(self):
        self.plan["stops"].pop()
        self.assertFalse(verify(self.plan, self.constraints)["valid"])

    def test_all_legs_checked(self):
        self.constraints["max_walk_m"] = 100
        self.assertFalse(verify(self.plan, self.constraints)["checks"]["travel"])

    def test_later_arrival_checked(self):
        self.constraints["target_hour"] = 22
        self.assertFalse(verify(self.plan, self.constraints)["checks"]["hours"])

    def test_diet_applies_to_all_stops(self):
        self.constraints["vegan_required"] = True
        self.assertFalse(verify(self.plan, self.constraints)["checks"]["dietary"])

    def test_estimated_transit_not_verified(self):
        self.constraints.update(max_walk_m=0, allow_transit=True)
        self.plan["legs"] = [{"mode": "transit", "minutes": 1, "verified": False}]
        self.assertFalse(verify(self.plan, self.constraints)["checks"]["travel"])


if __name__ == "__main__":
    unittest.main()
