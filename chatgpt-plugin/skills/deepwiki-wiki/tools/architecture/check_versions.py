#!/usr/bin/env python3
"""Audit ChatGPT plugin release versions across package text files.

The ChatGPT adapter and root APM Agent Skill are separate deliverables.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
BADGE_RE = re.compile(r"version-([0-9]+\.[0-9]+\.[0-9]+)-blue\.svg")
VERSION_HEADING_RE = re.compile(r"^#{1,6}\s+.*?\((\d+\.\d+\.\d+)\)\s*$", re.MULTILINE)

# Scan package source, manifests, prompts, and docs rather than Markdown alone.
def _read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required file: {path.as_posix()}")
        return None
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot parse {path.as_posix()}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path.as_posix()} must contain a JSON object")
        return None
    return value


def _iter_package_text_files(package_root: Path):
    """Yield UTF-8 text files regardless of extension; ignore binary assets."""
    for path in sorted(package_root.rglob("*")):
        if not path.is_file():
            continue
        # Test fixtures intentionally contain old version literals to exercise
        # this checker; they are not release documentation or runtime assets.
        relative_parts = path.relative_to(package_root).parts
        if "tests" in relative_parts or "__pycache__" in relative_parts:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            # The caller will report read errors for files it attempts to audit.
            yield path, None
            continue
        if "\x00" in content:
            continue
        yield path, content


def check_repo(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    plugin_manifest_path = root / "chatgpt-plugin" / "plugin.json"
    plugin_manifest = _read_json(plugin_manifest_path, errors)
    plugin_version = str(plugin_manifest.get("version", "")) if plugin_manifest else ""
    if not SEMVER_RE.fullmatch(plugin_version):
        errors.append(f"chatgpt-plugin/plugin.json has invalid semantic version: {plugin_version!r}")

    plugin_docs = [
        root / "chatgpt-plugin" / "README.md",
        root / "chatgpt-plugin" / "skills" / "deepwiki-wiki" / "README.md",
    ]
    for path in plugin_docs:
        try:
            first_line = path.read_text(encoding="utf-8").splitlines()[0]
        except (OSError, IndexError) as exc:
            errors.append(f"cannot read plugin README {path.relative_to(root).as_posix()}: {exc}")
            continue
        expected = f"# DeepWiki Codebase Wiki {plugin_version}"
        if first_line != expected:
            errors.append(
                f"{path.relative_to(root).as_posix()} title must be {expected!r}, got {first_line!r}"
            )

    codex_manifest_path = root / "chatgpt-plugin" / ".codex-plugin" / "plugin.json"
    if codex_manifest_path.exists():
        codex_manifest = _read_json(codex_manifest_path, errors)
        if codex_manifest and codex_manifest.get("version") != plugin_version:
            errors.append(
                f".codex-plugin/plugin.json version {codex_manifest.get('version')!r} "
                f"does not match plugin.json {plugin_version!r}"
            )

    package_root = root / "chatgpt-plugin"
    if package_root.exists() and plugin_version:
        version_major = plugin_version.split(".")[0]
        version_literal_re = re.compile(
            rf"(?<![\d.]){re.escape(version_major)}\.\d+\.\d+(?![\d.])"
        )
        for path, content in _iter_package_text_files(package_root):
            if content is None:
                errors.append(f"cannot read {path.relative_to(root).as_posix()}")
                continue
            relative = path.relative_to(root).as_posix()
            for old_version in VERSION_HEADING_RE.findall(content):
                if old_version != plugin_version:
                    errors.append(
                        f"{relative} contains a stale versioned heading ({old_version}); "
                        "use an unversioned feature heading or current release"
                    )
            for seen_version in sorted(set(version_literal_re.findall(content))):
                if seen_version != plugin_version:
                    errors.append(
                        f"{relative} contains stale plugin release version {seen_version}; "
                        f"current plugin version is {plugin_version}"
                    )

    # The root APM package is the original Agent Skill, not the ChatGPT adapter.
    apm_path = root / "apm.yml"
    apm_version = ""
    try:
        apm_text = apm_path.read_text(encoding="utf-8")
        match = re.search(
            r"(?m)^version:\s*['\"]?([0-9]+\.[0-9]+\.[0-9]+)['\"]?\s*$",
            apm_text,
        )
        if not match:
            errors.append("apm.yml must declare a semantic version")
        else:
            apm_version = match.group(1)
    except OSError as exc:
        errors.append(f"cannot read apm.yml: {exc}")

    root_readmes = [root / "README.md", root / "README.zh-CN.md", root / "README.ja.md"]
    for path in root_readmes:
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot read {path.relative_to(root).as_posix()}: {exc}")
            continue
        badge_versions = BADGE_RE.findall(text)
        if not badge_versions:
            errors.append(f"{path.relative_to(root).as_posix()} is missing the Agent Skill version badge")
        elif any(version != apm_version for version in badge_versions):
            errors.append(
                f"{path.relative_to(root).as_posix()} badge version(s) {badge_versions!r} "
                f"do not match apm.yml {apm_version!r}"
            )

    if plugin_version and apm_version and plugin_version == apm_version:
        warnings.append(
            "Plugin and APM versions currently match numerically; keep them independently managed. "
            "They describe different deliverables."
        )

    return {
        "status": "passed" if not errors else "failed",
        "plugin_version": plugin_version,
        "upstream_apm_skill_version": apm_version,
        "versions_are_independent": True,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", type=Path, default=Path("."))
    args = parser.parse_args()
    report = check_repo(args.repo_root.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
