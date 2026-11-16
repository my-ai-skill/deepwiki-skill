# Mermaid Authoring, Repair, and Regression Rules

## Authority and legacy-policy override

This packaged reference is authoritative for Mermaid authoring in this plugin. The pinned upstream .apm/skills/wiki/references/mermaid_policy.md contains legacy examples that quote pipe-delimited flowchart edge labels (for example A -->|"Yes"| B). Those edge-label examples are superseded by this reference. Keep the upstream source unchanged; apply this adapter rule whenever the upstream policy is loaded.

The distinction is:
- Node labels may and often should be quoted: A["Load Config"], B{"Valid?"}.
- Pipe-delimited flowchart edge labels are plain text and must not have wrapper quotes: A -->|Yes| B.
- Middle-label syntax is different and may use quotes: A -- "label with punctuation" --> B.

Do not copy node-label quoting rules to pipe-delimited edge labels.

## Mandatory normalization before writing or final validation

When creating a Mermaid flowchart, emit unquoted pipe labels from the start. When reviewing existing/generated diagrams, run the packaged tools/mermaid/mermaid_lint.py:

    python tools/mermaid/mermaid_lint.py path/to/page.md --check
    python tools/mermaid/mermaid_lint.py path/to/page.md --repair --output /tmp/page.repaired.md

The repair pass is intentionally narrow and deterministic:
1. It only examines fenced mermaid blocks declared as graph or flowchart.
2. It recognizes a complete pipe-label payload wrapped in one pair of double quotes, optionally surrounded by whitespace, such as A -->|"Yes"| B or A -->| "No" | B.
3. It removes only the wrapper quotes and whitespace immediately surrounding the quoted token, preserving label text, edge operator, indentation, and remaining source.
4. It does not modify node labels, sequence/class/state diagrams, inline Markdown, quoted middle-label syntax (A -- "label" --> B), or payloads containing embedded/escaped quotes where intent is ambiguous.
5. The helper writes to a separate output path and never overwrites input. Review/merge only affected generated/AUTOGEN content; preserve manual content outside generated markers.
6. Re-run --check on repaired output. If a finding remains or cannot be safely normalized, mark authoring lint unresolved and report exact line and manual correction needed. Never silently remove meaningful punctuation.

## Canonical flowchart example

    graph TD
      A["Mock method invoked"] --> B["Lock g_gmock_mutex"]
      B --> C["Reverse-scan expectations"]
      C --> D{"Matching expectation found?"}
      D -->|No| E["Format unexpected-call report"]
      D -->|Yes| F["Check saturation and prerequisites"]
      F --> G["Increment call count"]
      G --> H["Select Action or default"]
      H --> I["Release lock"]
      I --> J["Perform selected Action"]

## Separate authoring and renderer outcomes

Record two independent results for every Mermaid block:
- authoring_lint: passed, repaired, or unresolved.
- renderer: passed, failed, or not_run.

repaired means a deterministic source correction was applied and post-repair lint passed. It is not a Mermaid parser result. renderer=passed requires a real Mermaid parser and SVG render. renderer=failed requires an actual parser/renderer error. renderer=not_run means no parser/renderer executed; it is neither proof of valid syntax nor proof of invalid syntax.

Do not label a fixable pre-repair lint finding as a Mermaid syntax/render failure. If safe repair succeeds but no renderer runs, report authoring_lint=repaired and renderer=not_run.

## Regression fixtures

| Input | Expected normalized output | Expected lint |
|---|---|---|
| A -->|"Yes"| B | A -->|Yes| B | pass after repair |
| A -->| "No" | B | A -->|No| B | pass after repair |
| A -->|"no"| D | A -->|no| D | pass after repair |
| A -->|"yes"| E | A -->|yes| E | pass after repair |
| A -->|Yes| B | unchanged | pass |
| A -- "label" --> B | unchanged | pass; do not misclassify |
| A["Node label"] -->|Yes| B | unchanged | pass; retain node quotes |

After static repair and lint, run Mermaid.js parse() plus SVG render(), or Mermaid CLI, when available. Static fixtures alone never prove runtime rendering.
