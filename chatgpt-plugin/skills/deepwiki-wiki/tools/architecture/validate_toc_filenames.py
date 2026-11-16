#!/usr/bin/env python3
"""Validate locale-aware Markdown filenames declared by a DeepWiki TOC (stdlib only)."""
from __future__ import annotations
import argparse, json, re, unicodedata
from pathlib import Path

LANG_RE = re.compile(r"(?m)^\s*(?:filename_language|language):\s*['\"]?([^'\"#\s]+)")
FILENAME_RE = re.compile(r"(?m)^\s*filename:\s*(?:['\"]([^'\"]+\.md)['\"]|([^\s#]+\.md))\s*$")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
JAPANESE_RE = re.compile(r"[\u3040-\u30ff]")
KOREAN_RE = re.compile(r"[\uac00-\ud7af]")

def validate_text(text: str) -> dict:
    match = LANG_RE.search(text)
    locale = match.group(1) if match else ""
    names = [m.group(1) or m.group(2) for m in FILENAME_RE.finditer(text)]
    errors = []
    if not locale: errors.append({"code":"locale_missing","message":"TOC must declare project.language or project.filename_language"})
    if not names: errors.append({"code":"filenames_missing","message":"TOC contains no filename entries"})
    seen=set()
    for name in names:
        if name.casefold() in seen: errors.append({"code":"duplicate_filename","filename":name})
        seen.add(name.casefold())
        human=re.sub(r"^\d+[_-]*","",Path(name).stem)
        lang=locale.lower().replace("_","-").split("-")[0]
        mismatch = ((lang=="zh" and not CJK_RE.search(human)) or
                    (lang=="ja" and not (JAPANESE_RE.search(human) or CJK_RE.search(human))) or
                    (lang=="ko" and not KOREAN_RE.search(human)) or
                    (lang=="en" and any(ord(ch)>127 for ch in human)))
        if mismatch: errors.append({"code":"filename_locale_mismatch","filename":name,"locale":locale})
        if any(unicodedata.category(ch) in {"Cc","Cf"} for ch in name):
            errors.append({"code":"filename_control_character","filename":name})
        if name.startswith("/") or ".." in Path(name).parts:
            errors.append({"code":"filename_path_escape","filename":name})
    return {"status":"passed" if not errors else "failed","locale":locale,"filename_count":len(names),"errors":errors}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("toc",type=Path); args=parser.parse_args()
    try: report=validate_text(args.toc.read_text(encoding="utf-8"))
    except OSError as exc:
        print(json.dumps({"status":"failed","errors":[{"code":"toc_read_error","message":str(exc)}]},ensure_ascii=False,indent=2)); return 2
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if report["status"]=="passed" else 1
if __name__=="__main__": raise SystemExit(main())
