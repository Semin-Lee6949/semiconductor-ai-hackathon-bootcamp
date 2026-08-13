import json
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CoursePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.schema = json.loads((ROOT / "datasets/schema.json").read_text(encoding="utf-8"))

    def test_public_page_has_ten_challenges_and_eight_step_workflow(self):
        self.assertEqual(self.page.count('class="topic" type="button"'), 10)
        for step in range(1, 9):
            self.assertIn(f"STEP {step}", self.page)
        self.assertIn("1회 · 2시간", self.page)
        self.assertIn("8월 20일부터", self.page)

    def test_every_student_download_pack_exists(self):
        for slug, challenge in self.schema.items():
            for variant in challenge["variants"]:
                base = ROOT / "datasets/student" / slug / variant
                self.assertTrue((base / "train.csv").exists(), f"missing train: {slug}/{variant}")
                self.assertTrue(
                    (base / "holdout_features.csv").exists(),
                    f"missing holdout: {slug}/{variant}",
                )

    def test_public_page_does_not_expose_briefing_notes(self):
        for forbidden in ("2026.08.13", "FIELD BRIEFING", "채용설명회 정리"):
            self.assertNotIn(forbidden, self.page)

    def test_key_explanations_use_one_sentence_per_line(self):
        self.assertIn(".sentence-line{display:block;white-space:nowrap}", self.page)
        self.assertIn('class="lead sentence-lines"', self.page)
        self.assertIn('class="recruit-lead sentence-lines"', self.page)
        self.assertIn(".section-head p:not(.sentence-lines)", self.page)

    def test_student_templates_compile(self):
        for name in ("streamlit_app.py", "build_standalone_report.py"):
            py_compile.compile(str(ROOT / "templates" / name), doraise=True)


if __name__ == "__main__":
    unittest.main()
