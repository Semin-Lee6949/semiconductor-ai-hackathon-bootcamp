import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.student_preflight import check_environment


class StudentPreflightTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
