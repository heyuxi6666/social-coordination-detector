from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_release


class ReleaseHygieneTests(unittest.TestCase):
    def test_release_tree_is_clean(self):
        self.assertEqual(check_release.scan(ROOT), [])

    def test_checker_catches_secrets_personal_data_and_private_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fake_key = "API_" + 'KEY = "abcd1234efgh"'                 # built from pieces so this file stays clean
            fake_mail = "someone" + "@" + "example.org"
            (root / "config.py").write_text(f'{fake_key}\nowner = "{fake_mail}"\n', encoding="utf-8")
            (root / "notes.md").write_text("see " + "C:" + "\\" + "Users\\me\\file and ProjectCodename\n", encoding="utf-8")
            (root / "run.log").write_text("x", encoding="utf-8")
            found = "\n".join(check_release.scan(root, ["projectcodename"]))
            for label in ("credential assignment", "e-mail address", "home-directory path", "run.log", "deny-listed term"):
                self.assertIn(label, found)


if __name__ == "__main__":
    unittest.main()
