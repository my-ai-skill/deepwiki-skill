# Mermaid Engine: portable design without MCP

## Goal

Keep Mermaid authoring and rendering portable across browser-based LLMs, local coding agents, and CI without requiring a hosted MCP service. The packaged mermaid-authoring.md is authoritative for syntax and repair, including an explicit override of contradictory legacy edge-label examples in the pinned upstream Mermaid policy.

## Components

1. Static authoring validator: checks diagram structure and authoring conventions. It is a preflight, not a full Mermaid parser.
2. Safe repair pass: tools/mermaid/mermaid_lint.py normalizes wrapper-quoted pipe-delimited flowchart edge labels before final lint. It preserves label text and does not touch node labels or middle-label syntax.
3. Mermaid.js browser preview: real parse/render through the official Mermaid JavaScript library, yielding SVG.
4. Mermaid CLI: optional local/CI validator and raster/PDF export capability.

## Required validation sequence

1. Extract every fenced Mermaid block from every generated Markdown page.
2. Run static authoring lint and identify safely repairable quoted pipe-edge labels.
3. Apply deterministic repairs to generated/AUTOGEN content using a separate output file; preserve manual content outside generated markers.
4. Re-run static lint and record whether the block passed unchanged, passed after repair, or remains unresolved.
5. Run Mermaid.js parse() and render() with SVG output, or Mermaid CLI, when available.
6. Fix actual parser/renderer failures and repeat the real renderer check.
7. Report renderer success only when every block has actually passed a renderer. If any renderer was not run, overall runtime validation is incomplete.

## Browser preview behavior

Serve the preview directory over HTTP because browsers may block local ES module imports from file://. From the repository root, run cd chatgpt-plugin/skills/deepwiki-wiki/tools/mermaid && python -m http.server 8000, then open http://127.0.0.1:8000/preview.html. Paste Mermaid code or a Markdown document containing Mermaid fenced blocks. The page extracts blocks, invokes Mermaid.js parse/render, displays SVG previews, reports per-block parse errors, and allows SVG download. It loads Mermaid ESM 11.4.1 from jsDelivr. Internet access is therefore required unless that dependency is locally vendored.

The browser preview runs separately from the LLM chat UI. A web LLM that cannot execute arbitrary JavaScript cannot be assumed to render the artifact inside its own conversation. It can still generate the standard HTML preview artifact for the user's browser.

## CLI behavior

Run the static helper with --check or --repair --output as documented in mermaid-authoring.md. This helper is not Mermaid CLI and does not compile diagrams. When Node.js, Mermaid CLI, and browser dependencies are installed, use mmdc for actual parser/render validation. CLI is optional for portable skill usage and does not require MCP.

## Required result fields

For each Mermaid block, report two independent dimensions:
- authoring_lint: passed, repaired, or unresolved.
- renderer: passed, failed, or not_run.

Definitions:
- authoring_lint=passed: source passed static authoring rules without edits.
- authoring_lint=repaired: a safe normalization was applied, then static lint passed.
- authoring_lint=unresolved: a policy violation remains after repair; state the exact issue. This is an authoring-policy result, not proof that Mermaid.js rejected the source.
- renderer=passed: actual Mermaid.js parse plus SVG render, or Mermaid CLI, completed successfully.
- renderer=failed: an actual parser/renderer returned an error. Include engine/version and error.
- renderer=not_run: no parser/renderer executed; this is neither pass nor proof of invalid syntax.

Never turn a static preflight finding into renderer=failed. A safely repaired block with no renderer run is authoring_lint=repaired, renderer=not_run. Record engine/version, total block count, and per-block outcomes. Overall runtime validation is passed only if every block is renderer=passed; it is failed if an actual renderer failed; otherwise it is not_run/incomplete. Report unresolved authoring lint separately.

See Mermaid authoring, repair, and regression rules for exact transformations and fixtures.
