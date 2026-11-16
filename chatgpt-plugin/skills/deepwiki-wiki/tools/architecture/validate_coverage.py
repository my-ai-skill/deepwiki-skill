#!/usr/bin/env python3
"""Validate the structure/completeness of a DeepWiki architecture coverage report.

This is a manifest validator, not a source-code semantic analyzer. A separate
source reread is required to discover omitted relationships and verify evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def validate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    incomplete: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def issue(bucket: list[dict[str, str]], code: str, message: str, page: str = "") -> None:
        item = {"code": code, "message": message}
        if page:
            item["page_id"] = page
        bucket.append(item)

    if not isinstance(data, dict):
        return {"status": "failed", "errors": [{"code": "root_type", "message": "root must be a JSON object"}],
                "incomplete": [], "warnings": []}

    if data.get("schema_version") != "1.0":
        issue(errors, "schema_version", "schema_version must be '1.0'")

    repository = data.get("repository")
    if not isinstance(repository, dict) or not repository.get("full_name") or not repository.get("source_ref"):
        issue(errors, "repository", "repository.full_name and repository.source_ref are required")

    review = data.get("semantic_review")
    if not isinstance(review, dict):
        issue(incomplete, "semantic_review_missing", "semantic_review record is required")
    elif review.get("status") != "completed":
        issue(incomplete, "semantic_review_incomplete",
              "semantic_review.status must be 'completed'; a structural lint cannot replace source rereading")
    elif not review.get("method") or not review.get("reviewer"):
        issue(errors, "semantic_review_metadata", "completed semantic review requires method and reviewer")

    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        issue(errors, "pages", "pages must be a non-empty array")
        pages = []

    page_ids: set[str] = set()
    for page in pages:
        if not isinstance(page, dict):
            issue(errors, "page_type", "each page entry must be an object")
            continue
        page_id = str(page.get("page_id") or "")
        if not page_id:
            issue(errors, "page_id", "page_id is required")
        elif page_id in page_ids:
            issue(errors, "duplicate_page_id", f"duplicate page_id: {page_id}", page_id)
        else:
            page_ids.add(page_id)
        filename = page.get("filename")
        if not filename:
            issue(errors, "filename", "filename is required", page_id)
        diagram_count = page.get("diagram_count")
        if not isinstance(diagram_count, int) or diagram_count < 0:
            issue(errors, "diagram_count", "diagram_count must be a non-negative integer", page_id)

        inventory = page.get("source_inventory")
        if not isinstance(inventory, list) or not inventory:
            issue(incomplete, "source_inventory_missing", "source_inventory must list reviewed relevant files", page_id)
            inventory = []
        for entry in inventory:
            if not isinstance(entry, dict) or not entry.get("path"):
                issue(errors, "source_inventory_entry", "source inventory entries require a path", page_id)
                continue
            disposition = entry.get("disposition")
            if disposition == "unreviewed":
                issue(incomplete, "source_unreviewed", f"source file not reviewed: {entry['path']}", page_id)
            elif disposition == "not_applicable":
                if not entry.get("reason"):
                    issue(errors, "source_exclusion_reason", f"not_applicable source requires a reason: {entry['path']}", page_id)
            elif disposition != "covered":
                issue(errors, "source_disposition", f"invalid disposition for {entry['path']}", page_id)

        claims = page.get("claims")
        if not isinstance(claims, list) or not claims:
            issue(incomplete, "claims_missing", "page must contain at least one audited claim", page_id)
            claims = []
        claim_ids: set[str] = set()
        for claim in claims:
            if not isinstance(claim, dict):
                issue(errors, "claim_type", "claim entries must be objects", page_id)
                continue
            cid = str(claim.get("id") or "")
            if not cid or cid in claim_ids:
                issue(errors, "claim_id", f"claim id missing or duplicated: {cid}", page_id)
            claim_ids.add(cid)
            _validate_coverage_item(claim, "claim", page_id, errors, incomplete, issue)

        relationships = page.get("relationships")
        if not isinstance(relationships, list):
            issue(incomplete, "relationships_missing", "relationships must be explicitly inventoried (empty array is allowed)", page_id)
            relationships = []
        rel_by_id: dict[str, dict[str, Any]] = {}
        for rel in relationships:
            if not isinstance(rel, dict):
                issue(errors, "relationship_type", "relationship entries must be objects", page_id)
                continue
            rid = str(rel.get("id") or "")
            if not rid or rid in rel_by_id:
                issue(errors, "relationship_id", f"relationship id missing or duplicated: {rid}", page_id)
                continue
            rel_by_id[rid] = rel
            if not rel.get("kind") or not rel.get("source") or not rel.get("target"):
                issue(errors, "relationship_endpoints", f"relationship {rid} needs kind/source/target", page_id)
            _validate_coverage_item(rel, "relationship", page_id, errors, incomplete, issue)

        diagram_audits = page.get("diagram_audits")
        if not isinstance(diagram_audits, list):
            issue(errors, "diagram_audits", "diagram_audits must be an array, even when empty", page_id)
            diagram_audits = []
        if isinstance(diagram_count, int) and diagram_count >= 0 and len(diagram_audits) != diagram_count:
            issue(errors, "diagram_audit_count",
                  f"expected {diagram_count} diagram audit(s), found {len(diagram_audits)}", page_id)
        diagram_ids: set[str] = set()
        for audit in diagram_audits:
            if not isinstance(audit, dict):
                issue(errors, "diagram_audit_type", "diagram audit entries must be objects", page_id)
                continue
            did = str(audit.get("diagram_id") or "")
            if not did or did in diagram_ids:
                issue(errors, "diagram_id", f"diagram id missing or duplicated: {did}", page_id)
            diagram_ids.add(did)
            if audit.get("status") != "reviewed":
                issue(incomplete, "diagram_unreviewed", f"diagram has not been semantically reviewed: {did}", page_id)
            in_scope = audit.get("in_scope_relationship_ids")
            represented = audit.get("represented_relationship_ids")
            omissions = audit.get("omissions")
            if not isinstance(in_scope, list) or not isinstance(represented, list) or not isinstance(omissions, list):
                issue(errors, "diagram_scope_shape", f"diagram {did} requires in_scope_relationship_ids, represented_relationship_ids, and omissions arrays", page_id)
                continue
            represented_set = set(represented)
            omission_ids: set[str] = set()
            for omitted in omissions:
                if not isinstance(omitted, dict) or not omitted.get("relationship_id") or not omitted.get("reason"):
                    issue(errors, "diagram_omission_reason", f"diagram {did} omissions require relationship_id and reason", page_id)
                    continue
                omission_ids.add(omitted["relationship_id"])
            in_scope_set = set(in_scope)
            for rid in in_scope_set:
                if rid not in rel_by_id:
                    issue(errors, "unknown_diagram_relationship", f"diagram {did} references unknown relationship {rid}", page_id)
                if (rid in represented_set) == (rid in omission_ids):
                    issue(errors, "diagram_relationship_accounting",
                          f"diagram {did} must account for {rid} exactly once as represented or omitted", page_id)
                if rid in omission_ids and rid in rel_by_id and rel_by_id[rid].get("importance") == "critical":
                    issue(errors, "critical_diagram_omission",
                          f"diagram {did} omits critical in-scope relationship {rid}", page_id)
                elif rid in omission_ids and rid in rel_by_id:
                    issue(warnings, "supporting_diagram_omission",
                          f"diagram {did} intentionally omits supporting relationship {rid}; verify it is explained elsewhere", page_id)
            for rid in (represented_set | omission_ids) - in_scope_set:
                issue(errors, "diagram_out_of_scope_relationship",
                      f"diagram {did} accounts for {rid}, but it is not declared in scope", page_id)

    status = "failed" if errors else ("incomplete" if incomplete else "passed")
    return {
        "status": status,
        "summary": {
            "pages": len(pages),
            "errors": len(errors),
            "incomplete_items": len(incomplete),
            "warnings": len(warnings),
        },
        "errors": errors,
        "incomplete": incomplete,
        "warnings": warnings,
        "limitations": [
            "This helper validates the declared coverage manifest only.",
            "It does not discover omitted source relationships or prove that citation lines semantically support claims.",
            "Phase 4 must independently re-read the target source commit and compare it with the architecture map and generated pages."
        ]
    }


def _validate_coverage_item(item: dict[str, Any], label: str, page_id: str,
                            errors: list[dict[str, str]],
                            incomplete: list[dict[str, str]], issue: Any) -> None:
    item_id = str(item.get("id") or "<missing-id>")
    status = item.get("status")
    importance = item.get("importance")
    if importance not in {"critical", "supporting"}:
        issue(errors, f"{label}_importance", f"{label} {item_id} must set importance to critical or supporting", page_id)
    if status == "unreviewed":
        issue(incomplete, f"{label}_unreviewed", f"{label} not reviewed: {item_id}", page_id)
        return
    if status == "gap":
        issue(incomplete, f"{label}_gap", f"{label} has a coverage gap: {item_id}", page_id)
        return
    if status != "covered":
        issue(errors, f"{label}_status", f"{label} {item_id} has invalid status", page_id)
        return
    evidence = item.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        issue(errors, f"{label}_evidence", f"covered {label} {item_id} requires source evidence", page_id)
    else:
        for ev in evidence:
            if (not isinstance(ev, dict) or not ev.get("path")
                    or not isinstance(ev.get("start_line"), int)
                    or not isinstance(ev.get("end_line"), int)
                    or ev["start_line"] < 1 or ev["end_line"] < ev["start_line"]):
                issue(errors, f"{label}_evidence_shape", f"invalid evidence line range for {label} {item_id}", page_id)
                break
    rep = item.get("representation")
    if not isinstance(rep, dict) or rep.get("kind") not in {"prose", "table", "diagram"} or not rep.get("location"):
        issue(errors, f"{label}_representation", f"covered {label} {item_id} requires a valid page representation", page_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="architecture_coverage.json")
    parser.add_argument("--output", type=Path, help="optional JSON report output path")
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read valid JSON input: {exc}", file=sys.stderr)
        return 2
    report = validate_manifest(data)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
