# Architecture completeness and traceability gate

## Why this gate exists

Structural validity, citation validity, Mermaid syntax, and analysis completeness are different properties. A page can have valid markers, real citations, and a renderable diagram while omitting an important target, entry point, dependency, platform branch, or runtime path. Never treat a structural or syntax pass as proof of complete analysis.

This reference adds a semantic-coverage gate to the existing six-phase workflow. It does not replace the upstream phase specifications, source-reading rules, or Mermaid renderer checks.

## Required artifacts

Produce these artifacts in addition to the existing TOC and pages:

1. \`_context/architecture_map.json\` during TOC design.
2. \`_reports/architecture_coverage.json\` during document validation.

The architecture map is a plan derived from source inspection, not a folder-name outline. The coverage report records what was actually verified after writing.

## Phase 2 — build an architecture map before choosing pages

Read the repository tree, manifests/build files, entry points, representative implementation files, and tests. Identify the architecture dimensions that actually exist in this repository. Do not force every category onto every project.

For relevant modules, targets, and features, examine:

- **Build-time composition**: targets, source files compiled into each target, aggregate/translation units, link dependencies, generated code, and build options.
- **Source-level composition**: includes/imports, exported/public interfaces, implementation boundaries, inheritance or registration relationships.
- **Runtime behavior**: entry points, initialization, call/control flow, state transitions, ownership/lifecycle, data flow, error paths.
- **Conditional behavior**: platform/compiler/feature macros, configuration switches, optional dependencies, alternate implementations, and fallback paths.
- **Verification**: test targets, test fixtures, important test-to-feature mappings, and relevant CI/build entry points.

Create an inventory of the relevant source files and a relationship list. Each relationship must identify its kind and direction, for example:

- \`compile_input\`: \`gmock target -> gmock-all.cc\`
- \`includes\`: \`gmock-all.cc -> gmock-spec-builders.cc\`
- \`link_dependency\`: \`gmock target -> gtest target\` (non-MSVC branch)
- \`entrypoint\`: \`gmock_main.cc -> InitGoogleMock -> RUN_ALL_TESTS\`
- \`platform_branch\`: \`MSVC vs non-MSVC target composition\`

The examples above are illustrative; only register relationships proven by the target repository.

Map every high-importance topic to a TOC page and section. A source file can support multiple pages. Cross-cutting relationships must be assigned to a page that explains the relationship, not merely listed in a relevant-source block. If a necessary relationship does not fit the proposed TOC, add or adjust a page/section before writing.

For every diagram planned in the TOC, state its intended scope and the relationship IDs it should depict. Avoid mixing build-time, source-include, link, and runtime-call edges without labeling the edge semantics.

## Phase 3 — write from evidence, not from the outline alone

For each page:

1. Read all mapped source files. Follow important symbols and dependencies into additional files when the mapped files do not establish the complete behavior.
2. Build a page-local evidence/relationship ledger before writing prose or Mermaid.
3. For each important claim or relationship, record exact source evidence (path and real line range), importance (\`critical\` or \`supporting\`), and where it is explained (\`prose\`, \`table\`, or \`diagram\` plus a location).
4. Explain important conditional branches explicitly. Do not describe only the default branch when the code has materially different platform/compiler/configuration branches.
5. Build diagrams from the ledger. Every arrow must have an unambiguous relation meaning and source evidence. The diagram must include all critical relationships inside its declared scope. Supporting relationships may be omitted only with an explicit reason.
6. Check that the page title, its promised scope, prose, tables, and diagrams agree. A section titled “build and test entrypoints” is incomplete if it explains the implementation aggregation but omits the actual test entry targets or entry functions.

Distinguish:
- **Source fact**: directly visible in the inspected source.
- **Derived relationship**: inferred by combining multiple source facts; cite every source needed for the derivation.
- **Unknown / not inspected**: mark explicitly; do not fill the gap using general assumptions.

The worker returns the page plus its page-local coverage ledger. It must not claim a page is complete merely because it has citations or a Mermaid block.

## Phase 4 — independent semantic coverage review

After all page workers finish, the orchestrator performs a distinct review pass. When separate review agents are genuinely available, use one; otherwise the current agent must re-read the relevant sources in a fresh validation pass and state that it was a same-agent second pass. Never claim independent-agent review when it did not happen.

For each page:

1. Compare the TOC scope and architecture map with the actual page. Look for promised topics with no explanation.
2. Re-open key source files and reconstruct the important relationships from source, rather than trusting the page worker's ledger alone.
3. Confirm that all relevant source inventory entries have a disposition: covered, or not applicable with a reason. Unreviewed entries make the result incomplete.
4. Confirm each critical claim and relationship has real source evidence and a location in the page.
5. For every diagram, compare the nodes and edges with the source-derived relationship list. Verify direction, edge semantics, platform conditions, and omitted in-scope relationships. A syntactically valid diagram can still fail this semantic check.
6. Check that related pages do not leave cross-page relationships unexplained or contradict each other.
7. Fix omissions in the generated/AUTOGEN region, then repeat the review. Do not modify manual content outside AUTOGEN boundaries.

Use \`tools/architecture/validate_coverage.py\` to validate the coverage-report structure and completeness fields. This helper checks declared coverage records; it cannot discover a relationship omitted from the architecture map or prove that a cited line semantically supports a claim. The independent source reread is mandatory and must be recorded in the report.

## Coverage report format

The file \`_reports/architecture_coverage.json\` uses schema version \`1.0\`:

\`\`\`json
{
  "schema_version": "1.0",
  "repository": {
    "full_name": "owner/repo",
    "source_ref": "<full commit SHA>"
  },
  "semantic_review": {
    "status": "completed",
    "method": "same-agent second pass with source files re-opened",
    "reviewer": "orchestrator"
  },
  "pages": [
    {
      "page_id": "repo_01_architecture",
      "filename": "01_architecture.md",
      "diagram_count": 1,
      "source_inventory": [
        {
          "path": "src/module.cc",
          "disposition": "covered",
          "symbols_reviewed": ["Module::Init"],
          "reason": ""
        }
      ],
      "claims": [
        {
          "id": "claim-01",
          "statement": "The target initializes the module before dispatch.",
          "importance": "critical",
          "status": "covered",
          "evidence": [
            {"path": "src/module.cc", "start_line": 10, "end_line": 25}
          ],
          "representation": {"kind": "prose", "location": "Initialization section"}
        }
      ],
      "relationships": [
        {
          "id": "rel-01",
          "kind": "link_dependency",
          "source": "module target",
          "target": "runtime target",
          "condition": "non-Windows",
          "importance": "critical",
          "status": "covered",
          "evidence": [
            {"path": "CMakeLists.txt", "start_line": 30, "end_line": 34}
          ],
          "representation": {"kind": "diagram", "location": "Architecture diagram edge module->runtime"}
        }
      ],
      "diagram_audits": [
        {
          "diagram_id": "architecture-flow",
          "scope": "Build-target and runtime-entry relationships",
          "status": "reviewed",
          "in_scope_relationship_ids": ["rel-01"],
          "represented_relationship_ids": ["rel-01"],
          "omissions": []
        }
      ]
    }
  ]
}
\`\`\`

Field rules:

- \`source_inventory.disposition\`: \`covered\` or \`not_applicable\`. Use \`not_applicable\` only with a concrete reason. An unreviewed file must remain explicitly marked \`unreviewed\` and makes the report incomplete.
- \`claims[].importance\` and \`relationships[].importance\`: \`critical\` or \`supporting\`.
- \`status\`: \`covered\`, \`gap\`, or \`unreviewed\`. A covered item needs evidence and a page representation. A gap or unreviewed item cannot pass.
- Every evidence line range must be checked against the exact source commit; the helper checks shape only, not GitHub line existence or semantic relevance.
- Relationship \`kind\` must name the actual relation type. Do not use a generic arrow when the distinction matters.
- Each diagram audit must account for every relationship ID in its declared scope as either represented or omitted with a reason. Omitting a critical in-scope relationship is an error. A supporting relationship omitted from a diagram may be acceptable when the relationship is explained elsewhere and the omission reason is stated.
- Set `diagram_count` to the actual number of fenced Mermaid blocks in the page. The validator requires `diagram_count == len(diagram_audits)`; every Mermaid diagram must have exactly one audit. If the renderer is unavailable, record that separately in the Mermaid report; it does not waive semantic review.

## Quality status and reporting

Keep these dimensions separate:

- \`structure_status\`: page IDs, markers, headings, and links.
- \`citation_status\`: citation path/commit/line verification.
- \`content_coverage_status\`: source inventory, claims, and architecture relationships.
- \`diagram_semantic_status\`: whether each diagram matches the source-derived relationship list.
- \`mermaid_authoring_status\`: static style lint.
- \`mermaid_renderer_status\`: actual Mermaid.js/CLI execution.

The coverage helper returns:
- \`passed\`: all declared relevant inventory, claims, critical/supporting relationships, and diagram scopes are reviewed and accounted for.
- \`incomplete\`: any item is unreviewed or has a coverage gap.
- \`failed\`: malformed records, missing evidence for a covered claim, duplicate IDs, missing diagram audits, or a critical in-scope relationship omitted from a diagram.

A complete Wiki run must not be reported as fully passed when content coverage is incomplete or failed. A Mermaid renderer result of \`not_run\` must also remain \`not_run\`; do not conflate it with diagram-semantic status.
