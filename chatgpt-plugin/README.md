# DeepWiki Codebase Wiki 2.0.6

Cross-platform plugin packaging for the original `my-ai-skill/deepwiki-skill` Agent Skill.

This is an additive ChatGPT adapter, not a replacement for the original Skill. The repository's original `.apm/` skill, references, scripts, templates, `workflow-runner` agent, prompt, and manifest remain the backup/source of truth. This feature branch adds this package under `chatgpt-plugin/` and does not modify those originals.

Key upgrades:
- Preserve the six-phase workflow and exact one-phase workflow-runner contract.
- Use native independent page workers in `doc-write` where supported; otherwise execute the same contracts sequentially.
- Keep Mermaid MCP-free: provide a standalone browser preview with Mermaid.js; keep CLI optional for local agents and CI.
- Clearly report actual validation level and runtime capability; never overstate static checks as real rendering.


## Mermaid validation correctness (2.0.6)

- The plugin's authoring policy standardizes pipe-delimited flowchart edge labels as unquoted (`A -->|Yes| B`). The static lint/repair helper normalizes wrapper-quoted labels; this is an authoring-policy check, not proof that Mermaid.js itself rejects the original text.
- Static checks are not a Mermaid parser. Runtime outcomes are tri-state: `passed`, `failed`, or `not_run`.
- Mermaid CLI unavailability is reported as `not_run`, never as a diagram syntax failure or a successful validation.
- Phase 4 requires actual Mermaid.js parse/render or Mermaid CLI success for every block before reporting an overall pass.


## Deterministic Mermaid authoring check (2.0.6)

Run `python tools/mermaid/mermaid_lint.py path/to/page.md --check` for a non-mutating static check. To normalize safe wrapper-quoted pipe labels, write to a separate review file with `--repair --output /tmp/page.repaired.md`. Review the diff, then merge only the intended generated/AUTOGEN changes back into the original page. The temporary repaired file is not a second deliverable Wiki page. Manual content outside AUTOGEN markers must remain unchanged.

The helper does not run Mermaid.js. Use `preview.html` for actual parse and SVG render; report renderer status separately as `passed`, `failed`, or `not_run`.
