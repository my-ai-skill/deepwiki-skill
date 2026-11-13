# DeepWiki Codebase Wiki 2.0.4

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


## Mermaid validation correctness (2.0.4)

- Pipe-delimited flowchart edge labels are unquoted (`A -->|Yes| B`); quoted pipe labels are rejected by static regression lint.
- Static checks are not a Mermaid parser. Runtime outcomes are tri-state: `passed`, `failed`, or `not_run`.
- Mermaid CLI unavailability is reported as `not_run`, never as a diagram syntax failure or a successful validation.
- Phase 4 requires actual Mermaid.js parse/render or Mermaid CLI success for every block before reporting an overall pass.
