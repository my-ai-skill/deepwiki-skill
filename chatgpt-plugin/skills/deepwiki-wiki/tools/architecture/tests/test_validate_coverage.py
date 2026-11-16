import copy
import unittest

from validate_coverage import validate_manifest


def valid_manifest():
    return {
        "schema_version": "1.0",
        "repository": {"full_name": "owner/repo", "source_ref": "a" * 40},
        "semantic_review": {
            "status": "completed",
            "method": "same-agent second pass with source files re-opened",
            "reviewer": "orchestrator",
        },
        "pages": [{
            "page_id": "repo_01_build",
            "filename": "01_build.md",
            "source_inventory": [
                {"path": "CMakeLists.txt", "disposition": "covered", "symbols_reviewed": ["gmock"], "reason": ""}
            ],
            "claims": [{
                "id": "claim-01",
                "statement": "The gmock target is built from gmock-all.cc.",
                "importance": "critical",
                "status": "covered",
                "evidence": [{"path": "googlemock/CMakeLists.txt", "start_line": 97, "end_line": 98}],
                "representation": {"kind": "prose", "location": "Build targets section"},
            }],
            "relationships": [
                {
                    "id": "rel-compile",
                    "kind": "compile_input",
                    "source": "gmock target",
                    "target": "gmock-all.cc",
                    "condition": "",
                    "importance": "critical",
                    "status": "covered",
                    "evidence": [{"path": "googlemock/CMakeLists.txt", "start_line": 97, "end_line": 97}],
                    "representation": {"kind": "diagram", "location": "Build graph edge gmock->gmock-all.cc"},
                },
                {
                    "id": "rel-link",
                    "kind": "link_dependency",
                    "source": "gmock target",
                    "target": "gtest target",
                    "condition": "non-MSVC",
                    "importance": "critical",
                    "status": "covered",
                    "evidence": [{"path": "googlemock/CMakeLists.txt", "start_line": 98, "end_line": 98}],
                    "representation": {"kind": "prose", "location": "Platform branches section"},
                },
            ],
            "diagram_audits": [{
                "diagram_id": "build-graph",
                "scope": "Compile input relationship only",
                "status": "reviewed",
                "in_scope_relationship_ids": ["rel-compile"],
                "represented_relationship_ids": ["rel-compile"],
                "omissions": [],
            }],
        }],
    }


class CoverageValidatorTests(unittest.TestCase):
    def test_complete_manifest_passes(self):
        self.assertEqual(validate_manifest(valid_manifest())["status"], "passed")

    def test_critical_relationship_gap_is_incomplete(self):
        data = valid_manifest()
        data["pages"][0]["relationships"][1]["status"] = "gap"
        report = validate_manifest(data)
        self.assertEqual(report["status"], "incomplete")
        self.assertIn("relationship_gap", {x["code"] for x in report["incomplete"]})

    def test_missing_evidence_fails(self):
        data = valid_manifest()
        data["pages"][0]["claims"][0]["evidence"] = []
        report = validate_manifest(data)
        self.assertEqual(report["status"], "failed")
        self.assertIn("claim_evidence", {x["code"] for x in report["errors"]})

    def test_unreviewed_source_makes_report_incomplete(self):
        data = valid_manifest()
        data["pages"][0]["source_inventory"][0]["disposition"] = "unreviewed"
        self.assertEqual(validate_manifest(data)["status"], "incomplete")

    def test_missing_reason_for_not_applicable_source_fails(self):
        data = valid_manifest()
        data["pages"][0]["source_inventory"][0]["disposition"] = "not_applicable"
        data["pages"][0]["source_inventory"][0]["reason"] = ""
        self.assertEqual(validate_manifest(data)["status"], "failed")

    def test_critical_relationship_omitted_from_diagram_fails(self):
        data = valid_manifest()
        audit = data["pages"][0]["diagram_audits"][0]
        audit["in_scope_relationship_ids"].append("rel-link")
        audit["omissions"].append({"relationship_id": "rel-link", "reason": "left out"})
        report = validate_manifest(data)
        self.assertEqual(report["status"], "failed")
        self.assertIn("critical_diagram_omission", {x["code"] for x in report["errors"]})

    def test_supporting_relationship_can_be_omitted_with_reason(self):
        data = valid_manifest()
        rel = data["pages"][0]["relationships"][1]
        rel["importance"] = "supporting"
        audit = data["pages"][0]["diagram_audits"][0]
        audit["in_scope_relationship_ids"].append("rel-link")
        audit["omissions"].append({"relationship_id": "rel-link", "reason": "detailed in adjacent prose"})
        report = validate_manifest(data)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(len(report["warnings"]), 1)

    def test_diagram_relationship_must_be_accounted_for(self):
        data = valid_manifest()
        data["pages"][0]["diagram_audits"][0]["in_scope_relationship_ids"].append("rel-link")
        report = validate_manifest(data)
        self.assertEqual(report["status"], "failed")
        self.assertIn("diagram_relationship_accounting", {x["code"] for x in report["errors"]})

    def test_missing_semantic_review_is_incomplete(self):
        data = valid_manifest()
        data["semantic_review"]["status"] = "not_run"
        self.assertEqual(validate_manifest(data)["status"], "incomplete")

    def test_unknown_relationship_reference_fails(self):
        data = valid_manifest()
        data["pages"][0]["diagram_audits"][0]["represented_relationship_ids"].append("missing")
        report = validate_manifest(data)
        self.assertEqual(report["status"], "failed")
        self.assertIn("diagram_out_of_scope_relationship", {x["code"] for x in report["errors"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
