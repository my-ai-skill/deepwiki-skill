## Version 2.0.4 authoritative authoring policy

For Mermaid authoring and repairs, read the packaged `mermaid-authoring.md` reference first. It is the current authoritative rule set for the ChatGPT package and supersedes older quoted pipe-edge-label examples in historical upstream references. The corrected source policy, static regression lint, and Phase 4 tri-state changes are in `my-ai-skill/deepwiki-skill` branch `feature/chatgpt-deepwiki-plugin` at commit `7dc70c2983f707590a8f9378337c899776a8cc3f` (or a later commit on that same branch).

# Mermaid Engine: portable design without MCP

## Goal

Keep Mermaid authoring and rendering portable across browser-based LLMs, local coding agents, and CI without requiring a hosted MCP service.

## Components

1. Static authoring validator: universal baseline rules, including a regression check for quoted pipe-delimited flowchart edge labels; not a full Mermaid parser.
2. Mermaid.js browser preview: real parse/render through the official Mermaid JavaScript library, yielding SVG.
3. Mermaid CLI: optional local/CI validator and raster/PDF export capability.

## Browser preview behavior

Serve the preview directory over HTTP because browsers may block local ES module imports from `file://`. From the repository root, run `cd chatgpt-plugin/skills/deepwiki-wiki/tools/mermaid && python -m http.server 8000`, then open `http://127.0.0.1:8000/preview.html`. Paste Mermaid code or a Markdown document containing Mermaid fenced blocks. The page extracts blocks, invokes Mermaid.js `parse`/`render`, displays SVG previews, reports per-block parse errors, and allows SVG download. It loads the pinned Mermaid ESM version from jsDelivr. This is the Level 1 runtime check; static lint alone is not equivalent. Internet access is therefore required unless that dependency is locally vendored.

The browser preview runs separately from the LLM chat UI. A web LLM that cannot execute arbitrary JavaScript cannot be assumed to render the artifact inside its own conversation. It can still generate the standard HTML preview artifact for the user's browser.

## CLI behavior

When Node.js, Mermaid CLI, and browser dependencies are installed, use the original `scripts/validate_mermaid.py` or `mmdc`. CLI is optional for portable skill usage. It is not replaced by static checks and does not require MCP.

## Report levels

- `static`: policy/structure review only; not proof of Mermaid parsing. It must never be reported as compilation success.
- `mermaid-js`: actual Mermaid.js parser and SVG renderer ran.
- `mermaid-cli`: actual CLI run completed.

Do not overstate one level as another.

## Required tri-state reporting

For each extracted block, report exactly one of:

- `passed`: Mermaid.js parse and SVG render completed successfully, or Mermaid CLI completed successfully.
- `failed`: static authoring lint or an actual Mermaid parser/renderer returned an error.
- `not_run`: no Mermaid parser/renderer executed. This is not an invalid-diagram finding and is not a pass.

The overall Mermaid status is `passed` only if all blocks are `passed`; `failed` if any block is `failed`; otherwise `not_run`/incomplete if one or more blocks were not run. Always record the engine and version, total blocks, and per-block outcomes.

See [Mermaid authoring and regression rules](mermaid-authoring.md) for the pipe-edge-label distinction and regression fixtures.
