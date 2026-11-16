import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validate_toc_filenames import validate_text

class LocalizedFilenameTests(unittest.TestCase):
 def test_zh_pass(self): self.assertEqual(validate_text('project:\\n  language: "zh-CN"\\npages:\\n - filename: "01_项目总览.md"\\n')['status'],"passed")
 def test_zh_rejects_english(self): self.assertEqual(validate_text('project:\\n  language: "zh-CN"\\npages:\\n - filename: "01_project_overview.md"\\n')['status'],"failed")
 def test_en_pass(self): self.assertEqual(validate_text('project:\\n  language: "en"\\npages:\\n - filename: "01_project_overview.md"\\n')['status'],"passed")
 def test_en_rejects_chinese(self): self.assertEqual(validate_text('project:\\n  language: "en"\\npages:\\n - filename: "01_项目.md"\\n')['status'],"failed")
 def test_ja_ko(self):
  self.assertEqual(validate_text('project:\\n  language: "ja"\\npages:\\n - filename: "01_概要.md"\\n')['status'],"passed")
  self.assertEqual(validate_text('project:\\n  language: "ko"\\npages:\\n - filename: "01_개요.md"\\n')['status'],"passed")
 def test_duplicate(self): self.assertIn("duplicate_filename",{x["code"] for x in validate_text('project:\\n  language: "zh"\\npages:\\n - filename: "01_项目.md"\\n - filename: "01_项目.md"\\n')["errors"]})
 def test_locale_required(self): self.assertIn("locale_missing",{x["code"] for x in validate_text('pages:\\n - filename: "01_项目.md"\\n')["errors"]})
 def test_path_traversal(self): self.assertIn("filename_path_escape",{x["code"] for x in validate_text('project:\\n  language: "zh"\\npages:\\n - filename: "../01_项目.md"\\n')["errors"]})
if __name__=="__main__": unittest.main(verbosity=2)
