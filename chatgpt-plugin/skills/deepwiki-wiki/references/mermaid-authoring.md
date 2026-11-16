# Mermaid Authoring, Repair, and Regression Rules

## Authority and legacy-policy override

This packaged reference is authoritative for Mermaid authoring in this plugin. The pinned upstream `.apm/skills/wiki/references/mermaid_policy.md` contains legacy examples that quote pipe-delimited flowchart edge labels (for example `A -->|"Yes"| B`). Those edge-label examples are superseded by this reference. Keep the upstream source unchanged; apply this adapter rule whenever the upstream policy is loaded.

The distinction is:

- **Node labels** may and often should be quoted: `A["Load Config"]`, `B{"Valid?"}`.
- **Pipe-delimited flowchart edge labels** are plain text and must not have wrapper quotes: `A -->|Yes| B`.
- **Middle-label syntax** is different and may use quotes: `A -- "label with punctuation" --> B`.

Do not copy node-label quoting rules to pipe-delimited edge labels.

## Mandatory normalization before writing or final validation

When creating a Mermaid flowchart, emit unquoted pipe labels from the start. When reviewing existing/generated diagrams, run the packaged helper `tools/mermaid/mermaid_lint.py`:

```sh
python tools/mermaid/mermaid_lint.py path/to/page.md --check
python tools/mermaid/mermaid_lint.py path/to/page.md --repair --output /tmp/page.repaired.md
```

The repair pass is intentionally narrow and deterministic:

1. It only examines fenced `mermaid` blocks declared as `graph` or `flowchart`.
2. It recognizes a complete pipe-label payload wrapped in one pair of double quotes, optionally surrounded by whitespace, such as `A -->|"Yes"| B` or `A -->| "No" | B`.
3. It removes only the wrapper quotes and whitespace immediately surrounding the quoted token, preserving the label text, edge operator, indentation, and remaining source.
4. It does not modify node labels, sequence/class/state diagrams, inline Markdown, quoted middle-label syntax (`A -- "label" --> B`), or payloads containing embedded/escaped quotes where intent is ambiguous.
5. The helper writes to a separate output path and never overwrites the input. Review/merge only the affected generated/AUTOGEN content; preserve manual content outside generated markers.
6. Re-run `--check` on the repaired output. If a finding remains or cannot be safely normalized, mark authoring lint `unresolved` and report the exact line and manual correction needed. Never silently remove meaningful punctuation.

## Canonical flowchart example

```mermaid
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
```

## Separate authoring and renderer outcomes

Record two independent results for every Mermaid block:

- `authoring_lint`: `passed`, `repaired`, or `unresolved` .
- `renderer`: `passed`, `failed`, or `not_run`.

`repaired` means a deterministic source correction was applied and the post-repair lint passed. It is not a Mermaid parser result. `renderer=passed`É•ÅÕ¥É•Ì„É•…°5•Éµ…¥Á…ÉÍ•È…¹MYÉ•¹‘•È¸É•¹‘•É•Èõ™…¥±•‘€É•ÅÕ¥É•Ì…¸…ÑÕ…°Á…ÉÍ•È½É•¹‘•É•È•ÉÉ½È¸É•¹‘•É•Èõ¹½Ñ}ÉÕ¹€µ•…¹Ì¹¼Á…ÉÍ•È½É•¹‘•É•È•á•ÕÑ•ì¥Ð¥Ì¹•¥Ñ¡•ÈÁÉ½½˜½˜Ù…±¥Íå¹Ñ…à¹½ÈÁÉ½½˜½˜¥¹Ù…±¥Íå¹Ñ…à¸()¼¹½Ð±…‰•°„™¥á…‰±”ÁÉ”µÉ•Á…¥È±¥¹Ð™¥¹‘¥¹œ…Ì„5•Éµ…¥Íå¹Ñ…à½É•¹‘•È™…¥±ÕÉ”¸%˜„Í…™”É•Á…¥ÈÍÕ••‘Ì‰ÕÐ¹¼É•¹‘•É•ÈÉÕ¹Ì°É•Á½ÉÐ…ÕÑ¡½É¥¹}±¥¹ÐõÉ•Á…¥É•‘€…¹É•¹‘•É•Èõ¹½Ñ}ÉÕ¹€¸((ŒŒI•É•ÍÍ¥½¸™¥áÑÕÉ•Ì((´€´´ùð‰e•Ì‰ð	€‰•½µ•Ì€´´ùñe•Íð	€…¹Á…ÍÍ•Ì±¥¹Ð…™Ñ•ÈÉ•Á…¥È¸(´€´´ùð€‰9¼ˆð	€‰•½µ•Ì€´´ùñ9½ð	€…¹Á…ÍÍ•Ì±¥¹Ð…™Ñ•ÈÉ•Á…¥È¸(´€´´ùð‰¹¼‰ð€‰•½µ•Ì€´´ùñ¹½ð€…¹Á…ÍÍ•Ì±¥¹Ð…™Ñ•ÈÉ•Á…¥È¸(´€´´ùð‰å•Ì‰ð€‰•½µ•Ì€´´ùñå•Íð€…¹Á…ÍÍ•Ì±¥¹Ð…™Ñ•ÈÉ•Á…¥È¸(´€´´ùñe•Íð	€É•µ…¥¹ÌÕ¹¡…¹•…¹Á…ÍÍ•Ì±¥¹Ð¸(´€´´€‰±…‰•°ˆ€´´ø	€É•µ…¥¹ÌÕ¹¡…¹•…¹¥Ì¹½Ðµ¥Í±…ÍÍ¥™¥•¸(´l‰9½‘”±…‰•°‰t€´´ùñe•Íð	€É•µ…¥¹ÌÕ¹¡…¹•ì¹½‘”ÅÕ½Ñ•Ì…É”É•Ñ…¥¹•¸()™Ñ•ÈÍÑ…Ñ¥ŒÉ•Á…¥È…¹±¥¹Ð°ÉÕ¸5•Éµ…¥¹©ÌÁ…ÉÍ” ¥€Á±ÕÌMYÉ•¹‘•È ¥€°½È5•Éµ…¥1$°Ý¡•¸…Ù…¥±…‰±”¸MÑ…Ñ¥Œ™¥áÑÕÉ•Ì…±½¹”¹•Ù•ÈÁÉ½Ù”ÉÕ¹Ñ¥µ”É•¹‘•É¥¹œ¸(