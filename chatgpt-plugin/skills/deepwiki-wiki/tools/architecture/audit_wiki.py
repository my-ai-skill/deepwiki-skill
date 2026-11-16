#!/usr/bin/env python3
"""Cross-file validation for DeepWiki source evidence, Markdown, citations, and diagrams."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

PAGE_ID_RE = re.compile(r"<!--\s*PAGE_ID:\s*([^\s]+)\s*-->")
DIAGRAM_BLOCK_RE = re.compile(
    r"^[ \t]*<!--\s*DIAGRAM_ID:\s*([^\s]+)\s*-->[ \t]*\r?\n"
    r"[ \t]*\x60\x60\x60mermaid[ \t]*\r?\n(?P<body>.*?)^[ \t]*\x60\x60\x60[ \t]*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
MERMAID_FENCE_RE = re.compile(
    r"^[ \t]*\x60\x60\x60mermaid[ \t]*\r?\n.*?^[ \t]*\x60\x60\x60[ \t]*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
SOURCE_LINK_RE = re.compile(r"https?://[^\s)]+?/blob/([0-9a-fA-F]{40})/([^\s)#)]+)#L(\d+)(?:-L(\d+))?")

def _add(bucket, code, message, page_id=""):
    item = {"code": code, "message": message}
    if page_id: item["page_id"] = page_id
    bucket.append(item)

def _load_json(path, errors, code):
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _add(errors, code, f"Cannot read {path}: {exc}")
        return None
    if not isinstance(value, dict):
        _add(errors, code, f"{path} must contain a JSON object")
        return None
    return value

def _report(errors, incomplete, warnings, pages, diagrams, relationships):
    status = "failed" if errors else ("incomplete" if incomplete else "passed")
    return {"status": status, "summary": {"pages_checked": pages, "diagrams_checked": diagrams,
            "relationships_checked": relationships, "errors": len(errors),
            "incomplete_items": len(incomplete), "warnings": len(warnings)},
            "errors": errors, "incomplete": incomplete, "warnings": warnings,
            "limitations": [
                "Checks cross-file references, line ranges, citation coverage, anchors, and declared diagram fragments.",
                "String/fragment checks do not prove semantic truth; Phase 4 must independently re-read source and review control flow."
            ]}

def _links(markdown):
    result = []
    for m in SOURCE_LINK_RE.finditer(markdown):
        result.append({"commit": m.group(1).lower(), "path": unquote(m.group(2)),
                       "start": int(m.group(3)), "end": int(m.group(4) or m.group(3))})
    return result

def _verify_evidence(repo_root, evidence, citations, source_ref, errors, incomplete, page_id, label):
    for ev in evidence:
        if not isinstance(ev, dict):
            _add(errors, "evidence_entry_invalid", f"{label} has malformed evidence", page_id); continue
        rel_path, start, end = str(ev.get("path") or ""), ev.get("start_line"), ev.get("end_line")
        if not rel_path or not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
            _add(errors, "evidence_range_invalid", f"{label} has invalid path or line range", page_id); continue
        source_path = (repo_root / rel_path).resolve()
        try: source_path.relative_to(repo_root)
        except ValueError:
            _add(errors, "evidence_path_escape", f"{label} evidence path escapes repository: {rel_path}", page_id); continue
        try: lines = source_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            _add(errors, "evidence_source_missing", f"{label} source {rel_path} cannot be read: {exc}", page_id); continue
        if end > len(lines):
            _add(errors, "evidence_range_out_of_bounds", f"{label} range {rel_path}:{start}-{end} exceeds {len(lines)} lines", page_id); continue
        expected, excerpt = str(ev.get("contains") or ""), "\n".join(lines[start-1:end])
        if not expected:
            _add(incomplete, "evidence_excerpt_missing", f"{label} evidence needs a literal contains excerpt: {rel_path}:{start}-{end}", page_id)
        elif expected not in excerpt:
            _add(errors, "evidence_excerpt_mismatch", f"{label} expected excerpt not found in {rel_path}:{start}-{end}", page_id)
        if not any(c["commit"] == source_ref and c["path"] == rel_path and c["start"] <= start and c["end"] >= end for c in citations):
            _add(errors, "source_citation_missing", f"{label} has no Markdown citation covering {rel_path}:{start}-{end} at source commit {source_ref}", page_id)

def audit_wiki(repo_root: Path, wiki_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    wiki_dir = (wiki_dir or Path("docs/wiki"))
    if not wiki_dir.is_absolute(): wiki_dir = repo_root / wiki_dir
    wiki_dir = wiki_dir.resolve()
    errors, incomplete, warnings = [], [], []
    amap = _load_json(wiki_dir / "_context/architecture_map.json", errors, "architecture_map_unreadable")
    cov = _load_json(wiki_dir / "_reports/architecture_coverage.json", errors, "coverage_report_unreadable")
    if amap is None or cov is None: return _report(errors, incomplete, warnings, 0, 0, 0)

    mr, cr = amap.get("repository") or {}, cov.get("repository") or {}
    source_ref = str(cr.get("source_ref") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{40}", source_ref):
        _add(errors, "source_ref_invalid", "coverage repository.source_ref must be a full 40-character commit SHA")
    if str(mr.get("full_name") or "") != str(cr.get("full_name") or ""):
        _add(errors, "repository_mismatch", "architecture_map and coverage report repository names differ")
    if str(mr.get("source_ref") or "").lower() != source_ref:
        _add(errors, "source_ref_mismatch", "architecture_map and coverage report source_ref values differ")
    toc = wiki_dir / "toc.yaml"
    if toc.exists():
        txt = toc.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?m)^\s*ref_commit_hash:\s*[\"']?([0-9a-fA-F]{40})", txt)
        if m and m.group(1).lower() != source_ref: _add(errors, "toc_source_ref_mismatch", "toc.yaml ref_commit_hash differs from coverage source_ref")
        elif not m: _add(incomplete, "toc_source_ref_missing", "toc.yaml does not declare a full ref_commit_hash")
    else: _add(incomplete, "toc_missing", "docs/wiki/toc.yaml is absent")

    map_pages, pages = amap.get("pages"), cov.get("pages")
    if not isinstance(map_pages, list) or not isinstance(pages, list):
        _add(errors, "pages_shape", "architecture_map.pages and coverage.pages must be arrays")
        return _report(errors, incomplete, warnings, 0, 0, 0)
    map_by_id = {str(p.get("page_id")): p for p in map_pages if isinstance(p, dict)}
    seen, n_pages, n_diagrams, n_rels = set(), 0, 0, 0

    for p in pages:
        if not isinstance(p, dict): _add(errors, "page_entry_type", "coverage page entries must be objects"); continue
        pid, filename = str(p.get("page_id") or ""), str(p.get("filename") or "")
        if not pid or not filename: _add(errors, "page_identity_missing", "each page needs page_id and filename"); continue
        if pid in seen: _add(errors, "duplicate_page_id", f"duplicate page_id: {pid}", pid); continue
        seen.add(pid); n_pages += 1
        mp = map_by_id.get(pid)
        if mp is None: _add(errors, "page_missing_from_architecture_map", f"{pid} is absent from architecture_map.pages", pid); continue
        md_path = (wiki_dir / filename).resolve()
        try: md_path.relative_to(wiki_dir)
        except ValueError: _add(errors, "markdown_path_escape", f"Page filename escapes docs/wiki: {filename}", pid); continue
        try: md = md_path.read_text(encoding="utf-8")
        except OSError as exc: _add(errors, "markdown_missing", f"Cannot read page {filename}: {exc}", pid); continue
        marker = PAGE_ID_RE.search(md)
        if not marker or marker.group(1) != pid: _add(errors, "page_id_marker_mismatch", f"{filename} PAGE_ID marker does not match {pid}", pid)

        fences = list(MERMAID_FENCE_RE.finditer(md))
        blocks = list(DIAGRAM_BLOCK_RE.finditer(md))
        count = p.get("diagram_count")
        if not isinstance(count, int) or count != len(fences):
            _add(errors, "diagram_count_mismatch", f"declared diagram_count={count!r}, actual Mermaid fences={len(fences)}", pid)
        if len(blocks) != len(fences): _add(errors, "diagram_marker_missing", "every Mermaid fence needs a preceding DIAGRAM_ID marker", pid)
        actual = {}
        for b in blocks:
            did = b.group(1)
            if did in actual: _add(errors, "duplicate_diagram_marker", f"duplicate DIAGRAM_ID: {did}", pid)
            actual[did] = b.group("body")

        rels, map_rels = p.get("relationships"), mp.get("relationships")
        if not isinstance(rels, list) or not isinstance(map_rels, list):
            _add(errors, "relationships_shape", "page relationships must be arrays in both manifests", pid); rels, map_rels = [], []
        ids = [str(r.get("id") or "") for r in rels if isinstance(r, dict)]
        mids = [str(r.get("id") or "") for r in map_rels if isinstance(r, dict)]
        if len(ids) != len(set(ids)): _add(errors, "duplicate_relationship_id", "coverage relationship IDs are not unique", pid)
        if set(ids) != set(mids):
            _add(errors, "architecture_coverage_relation_mismatch", f"architecture map / coverage relationship IDs differ; missing={sorted(set(mids)-set(ids))}, extra={sorted(set(ids)-set(mids))}", pid)
        n_rels += len(ids); rel_by_id = {str(r.get("id")): r for r in rels if isinstance(r, dict)}
        citations = _links(md)

        inventory = p.get("source_inventory")
        if not isinstance(inventory, list) or not inventory: _add(incomplete, "source_inventory_missing", "page has no source_inventory", pid); inventory = []
        for ent in inventory:
            if not isinstance(ent, dict): _add(errors, "source_inventory_entry_invalid", "source_inventory entries must be objects", pid); continue
            ip, disp = str(ent.get("path") or ""), ent.get("disposition")
            if not ip: _add(errors, "source_inventory_path_missing", "source_inventory entry has no path", pid); continue
            resolved = (repo_root / ip).resolve()
            try: resolved.relative_to(repo_root)
            except ValueError: _add(errors, "source_inventory_path_escape", f"source path escapes repository: {ip}", pid); continue
            if disp == "unreviewed": _add(incomplete, "source_inventory_unreviewed", f"source not reviewed: {ip}", pid)
            elif disp == "not_applicable":
                if not ent.get("reason"): _add(errors, "source_inventory_exclusion_reason", f"not_applicable source needs a reason: {ip}", pid)
            elif disp == "covered":
                if not resolved.is_file(): _add(errors, "source_inventory_file_missing", f"covered source file does not exist: {ip}", pid)
            else: _add(errors, "source_inventory_disposition_invalid", f"invalid source disposition for {ip}", pid)

        for claim in p.get("claims") or []:
            if not isinstance(claim, dict): _add(errors, "claim_entry_type", "claim entries must be objects", pid); continue
            if claim.get("status") != "covered": _add(incomplete, "claim_not_covered", f"claim {claim.get('id')} is not covered", pid); continue
            ev = claim.get("evidence")
            if not isinstance(ev, list) or not ev: _add(errors, "claim_evidence_missing", f"covered claim {claim.get('id')} has no evidence", pid)
            else: _verify_evidence(repo_root, ev, citations, source_ref, errors, incomplete, pid, f"claim {claim.get('id')}")
            anchor = str((claim.get("representation") or {}).get("anchor") or "")
            if not anchor: _add(incomplete, "claim_anchor_missing", f"claim {claim.get('id')} has no exact representation.anchor", pid)
            elif anchor not in md: _add(errors, "claim_anchor_not_found", f"claim {claim.get('id')} anchor not found in {filename}: {anchor}", pid)

        for rid, rel in rel_by_id.items():
            if rel.get("status") != "covered": _add(incomplete, "relationship_not_covered", f"relationship {rid} status is {rel.get('status')!r}", pid); continue
            ev = rel.get("evidence")
            if not isinstance(ev, list) or not ev: _add(errors, "relationship_evidence_missing", f"covered relationship {rid} has no evidence", pid)
            else: _verify_evidence(repo_root, ev, citations, source_ref, errors, incomplete, pid, f"relationship {rid}")
            rep = rel.get("representation") or {}
            if rep.get("kind") == "diagram":
                did, frag = str(rep.get("diagram_id") or ""), str(rep.get("diagram_fragment") or "")
                if not did or not frag: _add(incomplete, "diagram_representation_contract_missing", f"relationship {rid} needs representation.diagram_id and diagram_fragment", pid)
                elif did not in actual: _add(errors, "relationship_diagram_missing", f"relationship {rid} points to absent diagram {did}", pid)
                elif frag not in actual[did]: _add(errors, "diagram_relationship_fragment_missing", f"relationship {rid} fragment not found in diagram {did}: {frag}", pid)
            else:
                anchor = str(rep.get("anchor") or "")
                if not anchor: _add(incomplete, "relationship_anchor_missing", f"relationship {rid} needs exact representation.anchor", pid)
                elif anchor not in md: _add(errors, "relationship_anchor_not_found", f"relationship {rid} anchor not found in {filename}: {anchor}", pid)

        audits = p.get("diagram_audits")
        if not isinstance(audits, list): _add(errors, "diagram_audits_shape", "diagram_audits must be an array", pid); audits = []
        audit_ids = [str(a.get("diagram_id") or "") for a in audits if isinstance(a, dict)]
        if len(audit_ids) != len(set(audit_ids)): _add(errors, "duplicate_diagram_audit", "diagram audit IDs are not unique", pid)
        if set(audit_ids) != set(actual): _add(errors, "diagram_audit_marker_mismatch", f"coverage diagram audits {sorted(audit_ids)} differ from Markdown DIAGRAM_IDs {sorted(actual)}", pid)
        for audit in audits:
            if not isinstance(audit, dict): continue
            n_diagrams += 1; did = str(audit.get("diagram_id") or "")
            if did not in actual: continue
            if audit.get("status") != "reviewed": _add(incomplete, "diagram_not_reviewed", f"diagram {did} status is not reviewed", pid)
            scope, represented, omissions = audit.get("in_scope_relationship_ids"), audit.get("represented_relationship_ids"), audit.get("omissions")
            if not all(isinstance(x, list) for x in (scope, represented, omissions)):
                _add(errors, "diagram_audit_arrays_invalid", f"diagram {did} audit arrays are malformed", pid); continue
            represented_set = set(represented)
            omitted_set = {str(x.get("relationship_id")) for x in omissions if isinstance(x, dict)}
            for rid in set(scope):
                if rid not in rel_by_id: _add(errors, "diagram_unknown_relationship", f"diagram {did} references unknown relationship {rid}", pid); continue
                if (rid in represented_set) == (rid in omitted_set): _add(errors, "diagram_relationship_accounting", f"diagram {did} must represent or omit {rid} exactly once", pid)
                if rid in omitted_set:
                    reason = next((str(x.get("reason") or "") for x in omissions if isinstance(x, dict) and str(x.get("relationship_id")) == rid), "")
                    if not reason: _add(errors, "diagram_omission_reason_missing", f"diagram {did} omission of {rid} has no reason", pid)
                    if rel_by_id[rid].get("importance") == "critical": _add(errors, "critical_diagram_omission", f"diagram {did} omits critical relationship {rid}", pid)
            for rid in (represented_set | omitted_set) - set(scope):
                _add(errors, "diagram_relationship_out_of_scope", f"diagram {did} accounts for out-of-scope relationship {rid}", pid)

    for pid in set(map_by_id) - seen: _add(errors, "architecture_page_without_coverage", f"architecture map page {pid} is absent from coverage report", pid)
    return _report(errors, incomplete, warnings, n_pages, n_diagrams, n_rels)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--wiki-dir", type=Path, default=Path("docs/wiki"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = audit_wiki(args.repo_root, args.wiki_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else args.repo_root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
