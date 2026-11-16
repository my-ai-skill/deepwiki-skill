# Mermaid static lint and safe repair

mermaid_lint.py is a narrow deterministic authoring helper, not a Mermaid parser. It only inspects fenced mermaid blocks whose diagram declaration is graph or flowchart and normalizes wrapper-quoted pipe-delimited edge labels.

    # Static check; input is never modified
    python tools/mermaid/mermaid_lint.py docs/wiki/01_overview.md --check

    # Repair to a separate output file; input is never overwritten
    python tools/mermaid/mermaid_lint.py docs/wiki/page.md --repair --output /tmp/page.repaired.md

    # Regression suite
    python -m unittest discover -s tools/mermaid/tests -v

Supported examples:
- A -->|"Yes"| B becomes A -->|Yes| B
- A -->| "No" | B becomes A -->|No| B

The helper preserves edge-label text and edge operator. It does not alter node labels, sequence/class/state diagrams, inline Markdown, or middle-label syntax such as A -- "label" --> B. Repairs are written to a separate output file for review; callers should only merge changes into generated/AUTOGEN content.

A passing static check is not proof that Mermaid accepts or renders the diagram. Use preview.html for actual Mermaid.js parse plus SVG render, or Mermaid CLI when installed. Report renderer status separately.
