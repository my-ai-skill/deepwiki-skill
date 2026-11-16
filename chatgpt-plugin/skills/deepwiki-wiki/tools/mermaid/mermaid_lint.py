#!/usr/bin/env python3
"""Deterministic static lint/repair for quoted pipe-delimited Mermaid flowchart labels."""
from __future__ import annotations
import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

FENCE_RE = re.compile(r"(?P<open>^[ \t]*\x60\x60\x60mermaid[ \t]*\r?\n)(?P<body>.*?)(?P<close>^[ \t]*\x60\x60\x60[ \t]*$)", re.I | re.M | re.S)
FLOWCHART_RE = re.compile(r"^\s*(?:graph|flowchart)\s+(?:TD|TB|BT|RL|LR)\b", re.I | re.M)
EDGE_RE = r"(?:---->|--->|-->|==>|-.->|---)"
QUOTED_PIPE_LABEL_RE = re.compile(rf"(?P<edge>{EDGE_RE})(?P<before>\s*)\|\s*\"(?P<label>[^\"\r\n]*)\"\s*\|")

@dataclass(frozen=True)
class Finding:
    line: int
    message: str

def is_flowchart(body: str) -> bool:
    return bool(FLOWCHART_RE.search(body))

def lint_block(body: str) -> list[Finding]:
    if not is_flowchart(body):
        return []
    findings = []
    for match in QUOTED_PIPE_LABEL_RE.finditer(body):
        findings.append(Finding(body.count("\n", 0, match.start()) + 1,
                                "quoted pipe-delimited flowchart edge label; remove quotes"))
    return findings

def repair_block(body: str) -> tuple[str, int]:
    if not is_flowchart(body):
        return body, 0
    def replace(match: re.Match[str]) -> str:
        return f"{match.group('edge')}{match.group('before')}|{match.group('label')}|"
    return QUOTED_PIPE_LABEL_RE.subn(replace, body)

def lint_markdown(markdown: str) -> list[tuple[int, int, Finding]]:
    results = []
    for block_index, match in enumerate(FENCE_RE.finditer(markdown), start=1):
        for finding in lint_block(match.group("body")):
            line = markdown.count("\n", 0, match.start("body")) + finding.line
            results.append((block_index, line, finding))
    return results

def repair_markdown(markdown: str) -> tuple[str, int]:
    total = 0
    def replace_block(match: re.Match[str]) -> str:
        nonlocal total
        body, count = repair_block(match.group("body"))
        total += count
        return f"{match.group('open')}{body}{match.group('close')}"
    return FENCE_RE.sub(replace_block, markdown), total

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Markdown file containing Mermaid fences")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="lint only; never modify input")
    mode.add_argument("--repair", action="store_true", help="write repaired output to --output")
    parser.add_argument("--output", type=Path, help="required output path for --repair; input is never overwritten")
    args = parser.parse_args(argv)
    if args.repair and args.output is None:
        parser.error("--repair requires --output; input is never overwritten in place")
    source = args.input.read_text(encoding="utf-8")
    if args.check:
        findings = lint_markdown(source)
        for block, line, finding in findings:
            print(f"block {block}, line {line}: {finding.message}")
        print(f"static lint: {'failed' if findings else 'passed'} ({len(findings)} finding(s)); Mermaid.js parse/render was not run")
        return 1 if findings else 0
    repaired, count = repair_markdown(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(repaired, encoding="utf-8", newline="")
    remaining = lint_markdown(repaired)
    print(f"repaired {count} quoted pipe-edge label(s); remaining findings: {len(remaining)}")
    print("static normalization only; Mermaid.js parse/render was not run")
    return 1 if remaining else 0

if __name__ == "__main__":
    raise SystemExit(main())
