# DeepWiki Codebase Wiki 2.0.1

Cross-platform plugin packaging for the original `my-ai-skill/deepwiki-skill` Agent Skill.

This is an additive ChatGPT adapter, not a replacement for the original Skill. The repository's original `.apm/` skill, references, scripts, templates, `workflow-runner` agent, prompt, and manifest remain the backup/source of truth. This feature branch adds this package under `chatgpt-plugin/` and does not modify those originals.

Key upgrades:
- Preserve the six-phase workflow and exact one-phase workflow-runner contract.
- Use native independent page workers in `doc-write` where supported; otherwise execute the same contracts sequentially.
- Keep Mermaid MCP-free: provide a standalone browser preview with Mermaid.js; keep CLI optional for local agents and CI.
- Clearly report actual validation level and runtime capability; never overstate static checks as real rendering.
