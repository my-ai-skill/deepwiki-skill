import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_toc_filenames import validate_text


class LocalizedFilenameTests(unittest.TestCase):
    def test_chinese_filenames_pass(self):
        text = """project:
  language: "zh-CN"
pages:
  - filename: "01_项目总览.md"
"""
        self.assertEqual(validate_text(text)["status"], "passed")

    def test_chinese_locale_rejects_english_filename(self):
        text = """project:
  language: "zh-CN"
pages:
  - filename: "01_project_overview.md"
"""
        report = validate_text(text)
        self.assertEqual(report["status"], "failed")
        self.assertIn("filename_locale_mismatch", {e["code"] for e in report["errors"]})

    def test_english_filenames_pass(self):
        text = """project:
  language: "en"
pages:
  - filename: "01_project_overview.md"
"""
        self.assertEqual(validate_text(text)["status"], "passed")

    def test_english_locale_rejects_chinese_filename(self):
        text = """project:
  language: "en"
pages:
  - filename: "01_项目总览.md"
"""
        self.assertEqual(validate_text(text)["status"], "failed")

    def test_japanese_and_korean_locales(self):
        ja = """project:
  language: "ja-JP"
pages:
  - filename: "01_概要.md"
"""
        ko = """project:
  language: "ko-KR"
pages:
  - filename: "01_개요.md"
"""
        self.assertEqual(validate_text(ja)["status"], "passed")
        self.assertEqual(validate_text(ko)["status"], "passed")

    def test_duplicate_filename_rejected(self):
        text = """project:
  language: "zh"
pages:
  - filename: "01_项目.md"
  - filename: "01_项目.md"
"""
        self.assertIn("duplicate_filename", {e["code"] for e in validate_text(text)["errors"]})

    def test_missing_locale_rejected(self):
        text = """pages:
  - filename: "01_项目.md"
"""
        self.assertIn("locale_missing", {e["code"] for e in validate_text(text)["errors"]})

    def test_path_traversal_rejected(self):
        text = """project:
  language: "zh"
pages:
  - filename: "../01_项目.md"
"""
        self.assertIn("filename_path_escape", {e["code"] for e in validate_text(text)["errors"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
