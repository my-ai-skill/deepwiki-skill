import copy, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_wiki import audit_wiki

SHA = "a" * 40

def make_repo(root):
    (root / "src").mkdir()
    (root / "docs/wiki/_context").mkdir(parents=True)
    (root / "docs/wiki/_reports").mkdir(parents=True)
    (root / "src/module.py").write_text("# module\ndef start():\n    return run()\n\ndef run():\n    return True\n", encoding="utf-8")
    (root / "docs/wiki/toc.yaml").write_text(f'ref_commit_hash: "{SHA}"\n', encoding="utf-8")
    md = f"""<!-- PAGE_ID: demo_lifecycle -->
# Execution lifecycle
[Source](https://github.com/acme/demo/blob/{SHA}/src/module.py#L2-L6)
main entrypoint description
RunAllTests phase
<!-- DIAGRAM_ID: lifecycle-flow -->
\x60\x60\x60mermaid
graph TD
    A[main] -->|calls| B[run]
\x60\x60\x60
"""
    (root / "docs/wiki/01_lifecycle.md").write_text(md, encoding="utf-8")
    rels = [
        {"id":"rel-main-run","kind":"call","source":"main","target":"run","condition":"default","importance":"critical","status":"covered",
         "evidence":[{"path":"src/module.py","start_line":2,"end_line":3,"contains":"def start"}],
         "representation":{"kind":"diagram","location":"Lifecycle diagram","diagram_id":"lifecycle-flow","diagram_fragment":"A[main] -->|calls| B[run]"}},
        {"id":"rel-run-result","kind":"returns","source":"run","target":"True","condition":"normal return","importance":"critical","status":"covered",
         "evidence":[{"path":"src/module.py","start_line":5,"end_line":6,"contains":"def run"}],
         "representation":{"kind":"prose","location":"RunAllTests section","anchor":"RunAllTests phase"}}
    ]
    claims=[{"id":"claim-main","statement":"main invokes run","importance":"critical","status":"covered",
             "evidence":[{"path":"src/module.py","start_line":2,"end_line":3,"contains":"def start"}],
             "representation":{"kind":"prose","location":"Overview","anchor":"main entrypoint description"}}]
    inventory=[{"path":"src/module.py","disposition":"covered","symbols_reviewed":["start","run"],"reason":""}]
    amap={"schema_version":"1.0","repository":{"full_name":"acme/demo","source_ref":SHA},
          "pages":[{"page_id":"demo_lifecycle","filename":"01_lifecycle.md","source_inventory":inventory,
                    "relationships":copy.deepcopy(rels),"diagrams":[{"diagram_id":"lifecycle-flow","relationship_ids":["rel-main-run"]}]}]}
    cov={"schema_version":"1.0","repository":{"full_name":"acme/demo","source_ref":SHA},
         "pages":[{"page_id":"demo_lifecycle","filename":"01_lifecycle.md","diagram_count":1,"source_inventory":inventory,
                   "claims":claims,"relationships":rels,"diagram_audits":[{"diagram_id":"lifecycle-flow","scope":"entry flow","status":"reviewed",
                   "in_scope_relationship_ids":["rel-main-run"],"represented_relationship_ids":["rel-main-run"],"omissions":[]}]}]}
    (root / "docs/wiki/_context/architecture_map.json").write_text(json.dumps(amap), encoding="utf-8")
    (root / "docs/wiki/_reports/architecture_coverage.json").write_text(json.dumps(cov), encoding="utf-8")
    return amap, cov

class AuditWikiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.amap,self.cov=make_repo(self.root)
    def tearDown(self): self.temp.cleanup()
    def audit(self): return audit_wiki(self.root)
    def save_cov(self): (self.root/"docs/wiki/_reports/architecture_coverage.json").write_text(json.dumps(self.cov),encoding="utf-8")
    def save_map(self): (self.root/"docs/wiki/_context/architecture_map.json").write_text(json.dumps(self.amap),encoding="utf-8")
    def test_complete_manifest_passes(self):
        r=self.audit(); self.assertEqual(r["status"],"passed",r); self.assertEqual(r["summary"]["relationships_checked"],2)
    def test_line_range_out_of_bounds_fails(self):
        self.cov["pages"][0]["claims"][0]["evidence"][0]["end_line"]=99; self.save_cov()
        self.assertIn("evidence_range_out_of_bounds",{x["code"] for x in self.audit()["errors"]})
    def test_excerpt_mismatch_fails(self):
        self.cov["pages"][0]["claims"][0]["evidence"][0]["contains"]="not present"; self.save_cov()
        self.assertIn("evidence_excerpt_mismatch",{x["code"] for x in self.audit()["errors"]})
    def test_missing_source_citation_fails(self):
        p=self.root/"docs/wiki/01_lifecycle.md"; p.write_text(p.read_text().replace(f"https://github.com/acme/demo/blob/{SHA}/src/module.py#L2-L6","https://example.invalid/source"))
        self.assertIn("source_citation_missing",{x["code"] for x in self.audit()["errors"]})
    def test_wrong_citation_commit_fails(self):
        p=self.root/"docs/wiki/01_lifecycle.md"; p.write_text(p.read_text().replace(SHA,"b"*40))
        self.assertIn("source_citation_missing",{x["code"] for x in self.audit()["errors"]})
    def test_page_marker_mismatch_fails(self):
        p=self.root/"docs/wiki/01_lifecycle.md"; p.write_text(p.read_text().replace("demo_lifecycle","wrong_page"))
        self.assertIn("page_id_marker_mismatch",{x["code"] for x in self.audit()["errors"]})
    def test_missing_page_fails(self):
        (self.root/"docs/wiki/01_lifecycle.md").unlink()
        self.assertIn("markdown_missing",{x["code"] for x in self.audit()["errors"]})
    def test_diagram_marker_missing_fails(self):
        p=self.root/"docs/wiki/01_lifecycle.md"; p.write_text(p.read_text().replace("<!-- DIAGRAM_ID: lifecycle-flow -->\n",""))
        self.assertIn("diagram_marker_missing",{x["code"] for x in self.audit()["errors"]})
    def test_diagram_fragment_missing_fails(self):
        self.cov["pages"][0]["relationships"][0]["representation"]["diagram_fragment"]="A --> B"; self.save_cov()
        self.assertIn("diagram_relationship_fragment_missing",{x["code"] for x in self.audit()["errors"]})
    def test_map_relation_mismatch_fails(self):
        self.amap["pages"][0]["relationships"].append({"id":"rel-extra"}); self.save_map()
        self.assertIn("architecture_coverage_relation_mismatch",{x["code"] for x in self.audit()["errors"]})
    def test_critical_diagram_omission_fails(self):
        a=self.cov["pages"][0]["diagram_audits"][0]; a["represented_relationship_ids"]=[]; a["omissions"]=[{"relationship_id":"rel-main-run","reason":"left out"}]
        self.save_cov()
        self.assertIn("critical_diagram_omission",{x["code"] for x in self.audit()["errors"]})
    def test_missing_claim_anchor_is_incomplete(self):
        self.cov["pages"][0]["claims"][0]["representation"].pop("anchor"); self.save_cov(); r=self.audit()
        self.assertEqual(r["status"],"incomplete"); self.assertIn("claim_anchor_missing",{x["code"] for x in r["incomplete"]})
    def test_toc_ref_mismatch_fails(self):
        (self.root/"docs/wiki/toc.yaml").write_text(f'ref_commit_hash: "{"b"*40}"\n')
        self.assertIn("toc_source_ref_mismatch",{x["code"] for x in self.audit()["errors"]})

if __name__ == "__main__": unittest.main(verbosity=2)
