import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_versions import check_repo


def make_repo(root: Path, plugin_version="2.0.9", apm_version="1.0.4"):
    def older_version(steps: int) -> str:
        major, minor, patch = plugin_version.split(".")
        return f"{major}.{minor}.{max(0, int(patch) - steps)}"

    (root / "chatgpt-plugin" / "skills" / "deepwiki-wiki").mkdir(parents=True)
    (root / "chatgpt-plugin").mkdir(exist_ok=True)
    (root / "apm.yml").write_text(
        f"name: deepwiki-skill\nversion: {apm_version}\n", encoding="utf-8"
    )
    for name in ("README.md", "README.zh-CN.md", "README.ja.md"):
        (root / name).write_text(
            f"![version](https://img.shields.io/badge/version-{apm_version}-blue.svg)\n",
            encoding="utf-8",
        )
    manifest = {"name": "deepwiki-codebase-wiki", "version": plugin_version}
    (root / "chatgpt-plugin" / "plugin.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    title = f"# DeepWiki Codebase Wiki {plugin_version}\n"
    (root / "chatgpt-plugin" / "README.md").write_text(title, encoding="utf-8")
    (root / "chatgpt-plugin" / "skills" / "deepwiki-wiki" / "README.md").write_text(
        title, encoding="utf-8"
    )
    return older_version


class VersionAuditTests(unittest.TestCase):
    def test_plugin_and_agent_skill_versions_are_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root, plugin_version="2.0.9", apm_version="1.0.4")
            report = check_repo(root)
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(report["plugin_version"], "2.0.9")
            self.assertEqual(report["upstream_apm_skill_version"], "1.0.4")
            self.assertTrue(report["versions_are_independent"])

    def test_plugin_readme_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older_version = make_repo(root)
            stale = older_version(1)
            (root / "chatgpt-plugin" / "README.md").write_text(
                f"# DeepWiki Codebase Wiki {stale}\n", encoding="utf-8"
            )
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("README.md title" in item for item in report["errors"]))

    def test_codex_overlay_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older_version = make_repo(root)
            overlay = root / "chatgpt-plugin" / ".codex-plugin"
            overlay.mkdir()
            (overlay / "plugin.json").write_text(
                json.dumps({"version": older_version(1)}), encoding="utf-8"
            )
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any(".codex-plugin/plugin.json" in item for item in report["errors"]))

    def test_old_release_heading_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older_version = make_repo(root)
            doc = root / "chatgpt-plugin" / "skills" / "deepwiki-wiki" / "README.md"
            doc.write_text(
                f"# DeepWiki Codebase Wiki 2.0.9\n\n## Mermaid rules ({older_version(2)})\n",
                encoding="utf-8",
            )
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("stale versioned heading" in item for item in report["errors"]))

    def test_old_plugin_version_in_body_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older_version = make_repo(root)
            stale = older_version(3)
            doc = root / "chatgpt-plugin" / "skills" / "deepwiki-wiki" / "README.md"
            doc.write_text(
                f"# DeepWiki Codebase Wiki 2.0.9\nPrevious release {stale}\n",
                encoding="utf-8",
            )
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(
                any(f"stale plugin release version {stale}" in item for item in report["errors"])
            )

    def test_agent_skill_badge_must_match_apm_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            (root / "README.zh-CN.md").write_text(
                "![version](https://img.shields.io/badge/version-2.0.9-blue.svg)\n",
                encoding="utf-8",
            )
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("README.zh-CN.md badge" in item for item in report["errors"]))


    def test_old_plugin_version_in_json_metadata_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            manifest_path = root / "chatgpt-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            stale = f"2.0.{6}"
            manifest["description"] = f"Adapter release {stale}"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any(f"plugin.json contains stale plugin release version {stale}" in item for item in report["errors"]))

    def test_old_plugin_version_in_python_asset_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            asset = root / "chatgpt-plugin" / "tools" / "release.py"
            asset.parent.mkdir(parents=True)
            stale = f"2.0.{6}"
            asset.write_text(f"PLUGIN_BASELINE = \"{stale}\"\n", encoding="utf-8")
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any(f"release.py contains stale plugin release version {stale}" in item for item in report["errors"]))

    def test_old_plugin_version_in_mdx_asset_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            asset = root / "chatgpt-plugin" / "docs" / "release.mdx"
            asset.parent.mkdir(parents=True)
            stale = f"2.0.{6}"
            asset.write_text(f"Release notes for {stale}", encoding="utf-8")
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("release.mdx contains stale plugin release version" in item for item in report["errors"]))

    def test_old_plugin_version_in_extensionless_text_asset_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            asset = root / "chatgpt-plugin" / "RELEASE_NOTES"
            stale = f"2.0.{6}"
            asset.write_text(f"Release notes for {stale}", encoding="utf-8")
            report = check_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("RELEASE_NOTES contains stale plugin release version" in item for item in report["errors"]))

if __name__ == "__main__":
    unittest.main(verbosity=2)
