import csv
import json
import unittest
from pathlib import Path

import numpy as np

from tools.generate_datasets import photo


ROOT = Path(__file__).resolve().parents[1]


class GeneratedDatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "datasets/schema.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((ROOT / "datasets/manifest.json").read_text(encoding="utf-8"))

    def test_has_20_student_packs_and_60_csv_files(self):
        self.assertEqual(len(self.schema), 10)
        self.assertEqual(sum(len(item["variants"]) for item in self.schema.values()), 20)
        self.assertEqual(len(self.manifest["files"]), 60)

    def test_train_is_noisy_and_holdout_labels_are_private(self):
        for slug, challenge in self.schema.items():
            for variant, info in challenge["variants"].items():
                base = ROOT / "datasets/student" / slug / variant
                with (base / "train.csv").open(encoding="utf-8", newline="") as handle:
                    train = list(csv.DictReader(handle))
                with (base / "holdout_features.csv").open(encoding="utf-8", newline="") as handle:
                    holdout = list(csv.DictReader(handle))
                self.assertGreaterEqual(len(train), 800)
                self.assertEqual(len(holdout), 200)
                self.assertTrue(any("" in row.values() for row in train), f"missing noise absent: {slug}/{variant}")
                ids = [row["sample_id"] for row in train]
                self.assertLess(len(set(ids)), len(ids), f"duplicate noise absent: {slug}/{variant}")
                for target in info["targets"]:
                    self.assertNotIn(target, holdout[0])
                labels = ROOT / "instructor/answer_keys" / slug / variant / "holdout_labels.csv"
                self.assertTrue(labels.exists())

    def test_manifest_files_exist(self):
        for item in self.manifest["files"]:
            self.assertTrue((ROOT / item["path"]).exists(), item["path"])

    def test_targets_have_variation_and_variants_differ(self):
        for slug, challenge in self.schema.items():
            hashes = []
            for variant, info in challenge["variants"].items():
                path = ROOT / "datasets/student" / slug / variant / "train.csv"
                hashes.append(next(item["sha256"] for item in self.manifest["files"] if item["path"] == str(path.relative_to(ROOT))))
                with path.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                for target in info["targets"]:
                    values = {row[target] for row in rows if row[target] != ""}
                    self.assertGreaterEqual(len(values), 2, f"target has no variation: {slug}/{variant}/{target}")
            self.assertEqual(len(set(hashes)), 2, f"A/B datasets are identical: {slug}")

    def test_photo_has_both_pr_tones_and_tone_dependent_cd_response(self):
        data, targets, _, _, _ = photo(np.random.default_rng(17), 5000, "A", False)
        self.assertIn("resist_line_cd_nm", targets)
        self.assertEqual(set(data["pr_tone"]), {"POSITIVE", "NEGATIVE"})

        positive = data["pr_tone"] == "POSITIVE"
        negative = data["pr_tone"] == "NEGATIVE"
        positive_slope = np.polyfit(
            data["normalized_dose_pct"][positive], data["resist_line_cd_nm"][positive], 1
        )[0]
        negative_slope = np.polyfit(
            data["normalized_dose_pct"][negative], data["resist_line_cd_nm"][negative], 1
        )[0]
        self.assertLess(positive_slope, 0)
        self.assertGreater(negative_slope, 0)


if __name__ == "__main__":
    unittest.main()
