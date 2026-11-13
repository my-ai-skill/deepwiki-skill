# Mermaid Engine: portable design without MCP

## Goal

Keep Mermaid authoring and rendering portable across browser-based LLMs, local coding agents, and CI without requiring a hosted MCP service.

## Components

1. Static authoring validator: universal baseline rules; not a full Mermaid parser.
2. Mermaid.js browser preview: real parse/render through the official Mermaid JavaScript library, yielding SVG.
3. Mermaid CLI: optional local/CI validator and raster/PDF export capability.

## Browser preview behavior

Open `../tools/mermaid/preview.html` in a modern browser. Paste Mermaid code or a Markdown document containing Mermaid fenced blocks. The page extracts blocks, invokes Mermaid.js `parse`/`render`, displays SVG previews, reports parse errors, and allows SVG download. It loads the pinned Mermaid ESM version from jsDelivr. Internet access is therefore required unless that dependency is locally vendored.

The browser preview runs separately from the LLM chat UI. A web LLM that cannot execute arbitrary JavaScript cannot be assumed to render the artifact inside its own conversation. It can still generate the standard HTML preview artifact for the user's browser.

## CLI behavior

When Node.js, Mermaid CLI, and browser dependencies are installed, use the original `scripts/validate_mermaid.py` or `mmdc`. CLI is optional for portable skill usage. It is not replaced by static checks and does not require MCP.

## Report levels

- `static`: policy/structure review only; not proof of Mermaid parsing.
- `mermaid-js`: actual Mermaid.js parser and SVG renderer ran.
- `mermaid-cli`: actual CLI run completed.

Do not overstate one level as another.
