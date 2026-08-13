import json
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CoursePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.preclass = (ROOT / "preclass_setup.html").read_text(encoding="utf-8")
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
        self.assertIn('class="recruit-lead"', self.page)
        self.assertIn(".section-head p:not(.sentence-lines)", self.page)

    def test_submission_intro_and_preclass_are_connected(self):
        self.assertIn("AI를 썼는지가 아니라", self.page)
        self.assertIn("지원서가 면접의 출발점", self.page)
        self.assertIn('href="preclass_setup.html"', self.page)

    def test_preclass_matches_beginner_windows_survey(self):
        for expected in (
            "Windows",
            "GitHub 가입",
            "Streamlit 가입",
            "구독 중인 AI 하나 선택",
            "Claude 구독자",
            "GPT 구독자",
            "Gemini 구독자",
            "Antigravity",
            "Claude Desktop",
            "ChatGPT Desktop",
            "AI_PROVIDER",
            "GITHUB_CLASS_TOKEN",
            "READY: core environment checks passed",
        ):
            self.assertIn(expected, self.preclass)
        self.assertNotIn("macOS", self.preclass)

    def test_preclass_protects_token(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", gitignore)
        self.assertIn("토큰은 제출하지 않습니다", self.preclass)
        self.assertTrue((ROOT / ".env.example").exists())

    def test_provider_neutral_prompt_exists(self):
        prompt = (ROOT / "templates" / "UNIVERSAL_AI_PROJECT_PROMPT.md").read_text(
            encoding="utf-8"
        )
        for expected in ("Claude", "ChatGPT", "Gemini", "PLAN.md", "Holdout"):
            self.assertIn(expected, prompt)

    def test_quota_fallback_plan_exists(self):
        plan = (ROOT / "student" / "AI_QUOTA_SAFETY_PLAN.md").read_text(encoding="utf-8")
        compact = (ROOT / "templates" / "COMPACT_AI_PROMPTS.md").read_text(
            encoding="utf-8"
        )
        for expected in ("14:00 이후", "Gemini", "로컬 스크립트", "추가 크레딧 구매는 필수가 아닙니다"):
            self.assertIn(expected, plan)
        for expected in ("1회 — 계획", "2회 — 구현", "3회 — 검수"):
            self.assertIn(expected, compact)

    def test_student_templates_compile(self):
        for name in ("streamlit_app.py", "build_standalone_report.py"):
            py_compile.compile(str(ROOT / "templates" / name), doraise=True)


if __name__ == "__main__":
    unittest.main()
