# DeepWiki Codebase Wiki 2.0.13

This package is the ChatGPT/portable runtime distribution for the original DeepWiki Skill. It is intentionally additive: do not modify the original `.apm/` skill, its scripts, references, templates, worker definition, or prompt on the upstream default branch.

## What is preserved and upgraded

- Original six phases and their order/dependencies.
- Original `workflow-runner` contract: one invocation executes exactly one phase, reads the phase spec first, loads only required references, produces declared outputs, validates, and stops/report failures.
- Native page-level subagents for `doc-write` whenever the host supports real concurrent agents.
- Exact sequential fallback using the same worker contract on hosts without subagents; no false claim of parallel execution.
- Original Python helpers and Mermaid CLI remain usable by local coding-agent/CI runtimes where installed.
- Portable browser Mermaid.js preview for browser-only and cross-provider workflows, without MCP.

## Mermaid preview

Serve the preview directory over HTTP because browsers may block local ES module imports from `file://`. From the repository root, run `cd chatgpt-plugin/skills/deepwiki-wiki/tools/mermaid && python -m http.server 8000`, then open `http://127.0.0.1:8000/preview.html`. Paste raw Mermaid or Markdown containing Mermaid code fences. The page uses Mermaid.js 11.4.1 from jsDelivr to parse and render SVG, and allows each SVG to be downloaded. Internet access to jsDelivr is required unless the JS module is vendored locally.

## Use

Ask the host agent to use this skill for a repository, TOC-based generation, structure-only generation, or incremental update. The host adapter must report which capabilities were actually available: subagents, shell/Python/Node, Mermaid.js, Mermaid CLI, repository access, and write access.


## Mermaid validation correctness

- The plugin's authoring policy standardizes pipe-delimited flowchart edge labels as unquoted (`A -->|Yes| B`). The static lint/repair helper normalizes wrapper-quoted labels; this is an authoring-policy check, not proof that Mermaid.js itself rejects the original text.
- Static checks are not a Mermaid parser. Runtime outcomes are tri-state: `passed`, `failed`, or `not_run`.
- Mermaid CLI unavailability is reported as `not_run`, never as a diagram syntax failure or a successful validation.
- Phase 4 requires actual Mermaid.js parse/render or Mermaid CLI success for every block before reporting an overall pass.


## Deterministic Mermaid authoring check

Run `python tools/mermaid/mermaid_lint.py path/to/page.md --check` for a non-mutating static check. To normalize safe wrapper-quoted pipe labels, write to a separate review file with `--repair --output /tmp/page.repaired.md`. Review the diff, then merge only the intended generated/AUTOGEN changes back into the original page. The temporary repaired file is not a second deliverable Wiki page. Manual content outside AUTOGEN markers must remain unchanged.

The helper does not run Mermaid.js. Use `preview.html` for actual parse and SVG render; report renderer status separately as `passed`, `failed`, or `not_run`.


## Architecture completeness gate

A structurally valid Wiki can still omit important source relationships. The current adapter adds a source-derived architecture map before TOC design, page-local claim/relationship ledgers during writing, and a separate Phase 4 semantic review. The reviewer re-opens key source files and checks diagram nodes/edges, direction, relation type, conditional branches, and omissions against source evidence.

- Policy: `references/architecture-completeness.md`
- Coverage manifest validator: `tools/architecture/validate_coverage.py`
- Regression tests (run from `chatgpt-plugin/skills/deepwiki-wiki/`): `python -m unittest discover -s tools/architecture/tests -v` and `python -m unittest discover -s tools/mermaid/tests -v`
- Required report: `docs/wiki/_reports/architecture_coverage.json`

The helper checks whether the declared coverage ledger is complete and internally consistent. It is not a source-code analyzer and cannot find a relationship omitted from the ledger; independent source rereading in Phase 4 remains mandatory. Structural validation, content coverage, diagram-semantic review, Mermaid authoring lint, and actual Mermaid rendering are separate statuses.


## Version boundaries

The ChatGPT plugin version comes from the parent `chatgpt-plugin/plugin.json`. The original Agent Skill version remains in the repository-root `apm.yml`; these are separate deliverables and must not be forced to the same number.


## Execution lifecycle analysis

When a page covers an end-to-end runtime path, use `references/execution-lifecycle-analysis.md` to document source-derived lifecycle stages, the concrete call hierarchy, event/reporting callbacks, alternate paths, and cleanup ordering. It explicitly distinguishes pre-main registration from runtime discovery and avoids importing another framework's lifecycle conventions.

## Cross-file quality gate

- `tools/architecture/audit_wiki.py` checks evidence line bounds and literal excerpts against local source files, source citations against the pinned commit, PAGE_ID/DIAGRAM_ID markers, diagram counts, relationship IDs across the architecture map and coverage ledger, representation anchors, and exact Mermaid fragments.
- Run it after `validate_coverage.py` and include `_reports/cross_file_audit.json` in the Wiki reports.
- This gate checks traceability and declared relationships; it cannot prove complex semantic correctness or discover relationships missing from both maps. Independent source rereading remains required.


## Locale-aware Wiki filenames

The resolved Wiki locale controls page filenames as well as page titles, descriptions, body text, and diagram labels. For example, a Chinese Wiki uses `01_项目总览.md` and `02_核心执行流程.md`; an English Wiki uses `01_project_overview.md`. Stable page/section IDs and source-code identifiers remain unchanged. The TOC `filename` is authoritative; all README, TOC, architecture/coverage reports, and relative Markdown links must be updated together on rename. Run `python tools/architecture/validate_toc_filenames.py docs/wiki/toc.yaml` to enforce locale consistency before writing and during validation.
