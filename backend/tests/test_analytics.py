import unittest

from app.analytics import AnalyticsEngine
from app.config import load_config
from app.data_manager import DataManager
from app.question_parser import parse_question


class AnalyticsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = load_config()
        cls.manager = DataManager(config)
        cls.engine = AnalyticsEngine(cls.manager)

    def test_compare_rainfall_and_crops(self):
        result = self.engine.compare_rainfall_and_crops(
            "Karnataka", "Maharashtra", crop_filter="Maize", last_n_years=5, top_m=3
        )
        payload = result.to_dict()
        self.assertIn("Karnataka averaged", payload["answer"])
        self.assertEqual(len(payload["tables"]), 2)
        self.assertTrue(any(row[0] == 2018 for row in payload["tables"][0]["rows"]))

    def test_district_extremes_handles_missing(self):
        result = self.engine.district_extremes("Karnataka", "Maharashtra", "Maize", None)
        payload = result.to_dict()
        self.assertIn("did not report", payload["answer"])
        rows = payload["tables"][0]["rows"]
        self.assertEqual(rows[0][0], "Karnataka")
        self.assertEqual(rows[1][1], "No records")

    def test_production_trend_with_climate(self):
        result = self.engine.production_trend_with_climate("Karnataka", "Maize", 5)
        payload = result.to_dict()
        self.assertIn("strong positive association", payload["answer"])
        self.assertEqual(payload["tables"][0]["headers"], ["Year", "Production (tonnes)", "Rainfall (mm)"])

    def test_policy_arguments(self):
        result = self.engine.policy_arguments("Karnataka", "Maize", "Paddy", 5)
        payload = result.to_dict()
        self.assertIn("Supporting a shift towards Maize", payload["answer"])
        self.assertEqual(len(payload["tables"]), 3)

    def test_question_parser_variations(self):
        q = (
            "Identify the district in Karnataka with the highest production of Maize in the most recent year "
            "available and compare that with the district with the lowest production of Maize in Maharashtra."
        )
        parsed = parse_question(q)
        self.assertEqual(parsed.intent, "district_extremes")
        self.assertEqual(parsed.params["state_a"], "Karnataka")
        self.assertEqual(parsed.params["state_b"], "Maharashtra")

    def test_question_parser_fallback_compare(self):
        q = "How does rainfall between Karnataka and Maharashtra compare, and which crops dominate in recent years?"
        parsed = parse_question(q)
        self.assertEqual(parsed.intent, "compare_rainfall_and_crops")
        self.assertEqual(parsed.params["state_a"], "Karnataka")
        self.assertEqual(parsed.params["state_b"], "Maharashtra")

    def test_question_parser_trend_rainfall(self):
        q = "Show the production trend of Wheat in Punjab over the last 10 years and compare it with the rainfall trend."
        parsed = parse_question(q)
        self.assertEqual(parsed.intent, "production_trend_with_climate")
        self.assertEqual(parsed.params["region"], "Punjab")
        self.assertEqual(parsed.params["crop"], "Wheat")

    def test_question_parser_policy_promote(self):
        q = "Should we promote millet over sugarcane in Maharashtra? Give policy arguments using climate data."
        parsed = parse_question(q)
        self.assertEqual(parsed.intent, "policy_arguments")
        self.assertEqual(parsed.params["region"], "Maharashtra")
        self.assertEqual(parsed.params["crop_a"], "millet")
        self.assertEqual(parsed.params["crop_b"], "sugarcane")


if __name__ == "__main__":
    unittest.main()
