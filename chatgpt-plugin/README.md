# DeepWiki Codebase Wiki 2.0.11

Cross-platform plugin packaging for the original `my-ai-skill/deepwiki-skill` Agent Skill.

This is an additive ChatGPT adapter, not a replacement for the original Skill. The repository's original `.apm/` skill, references, scripts, templates, `workflow-runner` agent, prompt, and manifest remain the backup/source of truth. This feature branch adds this package under `chatgpt-plugin/` and does not modify those originals.

Key upgrades:
- Preserve the six-phase workflow and exact one-phase workflow-runner contract.
- Use native independent page workers in `doc-write` where supported; otherwise execute the same contracts sequentially.
- Keep Mermaid MCP-free: provide a standalone browser preview with Mermaid.js; keep CLI optional for local agents and CI.
- Clearly report actual validation level and runtime capability; never overstate static checks as real rendering.


## Mermaid validation correctness

- The plugin's authoring policy standardizes pipe-delimited flowchart edge labels as unquoted (`A -->|Yes| B`). The static lint/repair helper normalizes wrapper-quoted labels; this is an authoring-policy check, not proof that Mermaid.js itself rejects the original text.
- Static checks are not a Mermaid parser. Runtime outcomes are tri-state: `passed`, `failed`, or `not_run`.
- Mermaid CLI unavailability is reported as `not_run`, never as a diagram syntax failure or a successful validation.
- Phase 4 requires actual Mermaid.js parse/render or Mermaid CLI success for every block before reporting an overall pass.


## Deterministic Mermaid authoring check

Run `python tools/mermaid/mermaid_lint.py path/to/page.md --check` for a non-mutating static check. To normalize safe wrapper-quoted pipe labels, write to a separate review file with `--repair --output /tmp/page.repaired.md`. Review the diff, then merge only the intended generated/AUTOGEN changes back into the original page. The temporary repaired file is not a second deliverable Wiki page. Manual content outside AUTOGEN markers must remain unchanged.

The helper does not run Mermaid.js. Use `preview.html` for actual parse and SVG render; report renderer status separately as `passed`, `failed`, or `not_run`.


## Architecture completeness and semantic review

- Phase 2 builds a source-derived architecture map before approving the TOC.
- Phase 3 records page-local claims, source evidence, and relationship-to-page/diagram mappings.
- Phase 4 re-opens key source files and checks that critical build, include, link, runtime, control/data-flow, and platform-branch relationships are explained and represented in the diagrams.
- `_reports/architecture_coverage.json` records coverage separately from structural validation.
- `tools/architecture/validate_coverage.py` validates the coverage manifest and its regression suite covers missing evidence, unreviewed source files, critical diagram omissions, and incomplete review states.

The manifest validator does not understand the codebase by itself. Phase 4 must still perform and record a source-grounded semantic review. A structure pass or Mermaid syntax pass cannot be reported as an architecture-completeness pass.


## Version boundaries

- The ChatGPT runtime adapter version is declared by `chatgpt-plugin/plugin.json` and must match this README and `skills/deepwiki-wiki/README.md`.
- The original Agent Skill version is declared separately by the repository-root `apm.yml` and displayed in the root language READMEs. It is intentionally independent; the current root APM version is not the ChatGPT plugin version.
- Run `python chatgpt-plugin/skills/deepwiki-wiki/tools/architecture/check_versions.py .` to audit these boundaries and stale plugin release-version references.


## Execution lifecycle and cross-file verification

- For end-to-end runtime paths, the plugin now requires a source-derived lifecycle analysis: pre-entry registration, entry point, initialization, dispatch/loop, callbacks/reporting, alternate paths, and teardown.
- The `references/execution-lifecycle-analysis.md` guide defines lifecycle-stage, call-hierarchy, and event/cleanup views without copying conventions from unrelated frameworks.
- `tools/architecture/audit_wiki.py` cross-checks source line ranges and literal excerpts, commit-pinned Markdown citations, PAGE_ID/DIAGRAM_ID markers, architecture-map/coverage relationship identity, and exact diagram fragments.
- The cross-file audit is deterministic consistency checking, not a semantic proof. Phase 4 must still independently re-read the source and reconstruct the runtime path.
- Run the architecture and Mermaid regression suites before release; report browser Mermaid.js rendering separately from static checks.


## Locale-aware Wiki filenames

The resolved Wiki locale controls page filenames as well as page titles, descriptions, body text, and diagram labels. For example, a Chinese Wiki uses `01_项目总览.md` and `02_核心执行流程.md`; an English Wiki uses `01_project_overview.md`. Stable page/section IDs and source-code identifiers remain unchanged. The TOC `filename` is authoritative; all README, TOC, architecture/coverage reports, and relative Markdown links must be updated together on rename. Run `python tools/architecture/validate_toc_filenames.py docs/wiki/toc.yaml` to enforce locale consistency before writing and during validation.
