import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_demo import build_payload, load_rows  # noqa: E402


class BuildDemoTest(unittest.TestCase):
    def test_pipeline_has_holdout_and_improves_baseline(self):
        rows = load_rows(ROOT / "data/raw/cmp_demo.csv")
        model, metrics = build_payload(rows)
        self.assertGreaterEqual(metrics["holdout_rows"], 5)
        self.assertLess(metrics["improved_rmse"], metrics["baseline_rmse"])
        self.assertTrue(model["educational_only"])

    def test_audit_has_no_missing_or_duplicates(self):
        rows = load_rows(ROOT / "data/raw/cmp_demo.csv")
        _, metrics = build_payload(rows)
        self.assertEqual(metrics["audit"]["missing"], 0)
        self.assertEqual(metrics["audit"]["duplicates"], 0)


if __name__ == "__main__":
    unittest.main()
