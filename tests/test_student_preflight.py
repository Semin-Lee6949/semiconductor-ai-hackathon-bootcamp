import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.student_preflight import check_environment


class StudentPreflightTests(unittest.TestCase):
    def test_claude_track_does_not_require_another_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("rules", encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            (root / ".env").write_text("AI_PROVIDER=claude\n", encoding="utf-8")

            def find_command(command):
                return f"/mock/{command}" if command in {"git", "claude"} else None

            def run_command(command, timeout=10):
                if "config" in command:
                    return True, "configured"
                if "rev-parse" in command:
                    return True, "true"
                return True, "test-version"

            with patch("tools.student_preflight.shutil.which", side_effect=find_command):
                with patch("tools.student_preflight.run", side_effect=run_command):
                    passes, failures = check_environment(root)

        self.assertIn("AI provider selected: claude", passes)
        self.assertTrue(any(item.startswith("Claude Code:") for item in passes))
        self.assertFalse(any("AI_PROVIDER" in item for item in failures))

    def test_all_three_provider_tracks_are_valid_without_cli(self):
        for provider in ("claude", "openai", "gemini"):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "AGENTS.md").write_text("rules", encoding="utf-8")
                (root / "README.md").write_text("readme", encoding="utf-8")
                (root / ".env").write_text(f"AI_PROVIDER={provider}\n", encoding="utf-8")

                def find_command(command):
                    return "/mock/git" if command == "git" else None

                def run_command(command, timeout=10):
                    if "config" in command:
                        return True, "configured"
                    if "rev-parse" in command:
                        return True, "true"
                    return True, "test-version"

                with patch("tools.student_preflight.shutil.which", side_effect=find_command):
                    with patch("tools.student_preflight.run", side_effect=run_command):
                        passes, failures = check_environment(root)

                self.assertIn(f"AI provider selected: {provider}", passes)
                self.assertFalse(any("AI_PROVIDER" in item for item in failures))

    def test_missing_repo_files_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("tools.student_preflight.shutil.which", return_value=None):
                _, failures = check_environment(Path(directory))
        self.assertIn("Missing AGENTS.md", failures)
        self.assertIn("Missing README.md", failures)

    def test_required_files_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("rules", encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            with patch("tools.student_preflight.shutil.which", return_value=None):
                passes, failures = check_environment(root)
        self.assertIn("Found AGENTS.md", passes)
        self.assertIn("Found README.md", passes)
        self.assertNotIn("Missing AGENTS.md", failures)
        self.assertNotIn("Missing README.md", failures)

    def test_missing_provider_selection_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("rules", encoding="utf-8")
            (root / "README.md").write_text("readme", encoding="utf-8")
            with patch("tools.student_preflight.shutil.which", return_value=None):
                _, failures = check_environment(root)
        self.assertIn("Set AI_PROVIDER in .env: claude, openai, or gemini", failures)


if __name__ == "__main__":
    unittest.main()
