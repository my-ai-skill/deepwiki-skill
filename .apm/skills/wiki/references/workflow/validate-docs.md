# Step: validate-docs (Phase 4)

## Goal

Validate the generated documentation and apply safe fixes:
- Mermaid diagrams pass a real Mermaid.js or Mermaid CLI parse/render check; if neither renderer actually runs, each affected block is explicitly reported as `not_run` (never as valid or invalid)
- Document structure is consistent (PAGE_ID markers, AUTOGEN markers, no overlaps)

## Inputs

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `doc_dir` | No | `{output_dir}` | Directory containing generated `.md` docs |
| `output_dir` | No | `docs/wiki` | Base output dir (for `_reports/`) |
| `toc_file` | No | `{output_dir}/toc.yaml` | TOC file used to validate expected pages/sections |
| `repo_path` | No | `.` | Repository root path |

## Outputs

| Path | Description |
|------|-------------|
| `{output_dir}/_reports/mermaid_invalid.json` | Invalid Mermaid blocks report |
| `{output_dir}/_reports/structure_validation.json` | Document structure validation report |
| `{doc_dir}/*.md` | In-place fixes (Mermaid blocks and/or missing structural markers only) |

## Scripts

### `validate_docs_structure.py`

Validates document structure against TOC specification: PAGE_ID markers, AUTOGEN markers, internal links.

**Usage**:
```bash
python scripts/validate_docs_structure.py \
    --doc-dir "{doc_dir}" \
    --toc-file "{toc_file}"
```

**Parameters**:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--doc-dir` | Yes | - | Directory containing generated .md docs |
| `--toc-file` | Yes | - | Path to toc.yaml file |
| `--output` | No | stdout | Output JSON report to file |
| `--errors-only` | No | false | Only report errors, not warnings |
| `--fix` | No | false | Auto-fix issues where possible (not yet implemented) |

**Output Structure** (JSON):
```json
{
  "summary": {
    "pages_validated": 5,
    "pages_missing": 0,
    "sections_validated": 20,
    "sections_missing": 2,
    "total_errors": 3,
    "total_warnings": 1,
    "is_valid": false
  },
  "errors": [
    {
      "file": "01_overview.md",
      "line": 1,
      "severity": "error",
      "category": "page_id",
      "message": "Missing PAGE_ID marker",
      "fix_hint": "Add <!-- PAGE_ID: project_01_overview --> at the start"
    }
  ],
  "warnings": [...]
}
```

**Issue Categories**:

| Category | Description |
|----------|-------------|
| `page_id` | PAGE_ID marker missing or incorrect |
| `autogen` | AUTOGEN marker issues (missing, mismatched, orphaned) |
| `structure` | Basic structure issues (H1 headings, file size) |
| `link` | Internal link issues (broken or undefined targets) |
| `toc` | TOC alignment issues (missing pages, extra files) |

### `validate_mermaid.py`

Extracts Mermaid diagrams, rejects known authoring-policy violations, and validates syntax using Mermaid CLI (`mmdc`) when available. A missing CLI is an unexecuted check, not a syntax failure.

**Usage**:
```bash
# Validate all diagrams in a directory (invalid only)
python3 scripts/validate_mermaid.py \
    --input "{doc_dir}" \
    --invalid-only

# Validate a single Mermaid file
python3 scripts/validate_mermaid.py --input diagram.mmd

# Validate code string directly
python3 scripts/validate_mermaid.py --code "graph TD\n    A-->B"
```

**Parameters**:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--input` | Yes* | - | Input file (.mmd) or directory (scans .md files) |
| `--code` | Yes* | - | Mermaid code string to validate |
| `--blocks` | Yes* | - | JSON file with extracted blocks |
| `--output` | No | stdout | Output JSON report to file |
| `--patterns` | No | `["*.md"]` | Glob patterns for .md files |
| `--mmdc` | No | `mmdc` | Path to mmdc executable |
| `--invalid-only` | No | false | Only output invalid blocks |
| `--extract-only` | No | false | Only extract blocks, don't validate |

*One of `--input`, `--code`, or `--blocks` is required (mutually exclusive).

**Output Structure** (with `--invalid-only`):
```json
{
  "invalid_blocks": [
    {
      "file_path": "01_overview.md",
      "code": "graph TD\n    A[User] --> B",
      "start_line": 45,
      "end_line": 55,
      "error_message": "Parse error on line 2",
      "error_type": "syntax_error",
      "error_line": 2,
      "fix_hint": "Add quotes around node text: A[\"User\"]"
    }
  ],
  "total_invalid": 2,
  "total_scanned": 10,
  "files_affected": 1
}
```

**Error Types**:

| Type | Description | Common Fix |
|------|-------------|------------|
| `lexical_error` | Unrecognized text/characters | Quote node text with special characters |
| `syntax_error` | General syntax issues | Check diagram type and arrow syntax |
| `node_error` | Node definition problems | Balance brackets, quote labels |
| `edge_error` | Arrow/edge problems | Use valid arrows (-->, ---) |
| `cli_unavailable` | mmdc not installed | Install @mermaid-js/mermaid-cli |
| `timeout` | Validation timeout | Simplify diagram |

## Workflow

### 1. Mermaid Diagram Validation

1) Run `validate_mermaid.py` script:
```bash
python scripts/validate_mermaid.py \
    --input "{doc_dir}" \
    --invalid-only \
    --output "{output_dir}/_reports/mermaid_invalid.json"
```

2) Interpret validation outcomes as three distinct states:
   - `passed`: Mermaid CLI actually parsed and rendered the block successfully.
   - `failed`: a static authoring-policy error or actual Mermaid parser/renderer error was found.
   - `not_run`: Mermaid CLI/browser renderer was unavailable. Do not label this as valid or invalid and do not auto-rewrite the diagram.
   - The JSON report must include `validation_status`, `validation_level`, and counts for `passed`, `failed`, and `unvalidated`.
   - If CLI is unavailable but an actual browser can be opened, use `tools/mermaid/preview.html` and record Mermaid.js parse/render results. Otherwise report `not_run`.

3) If invalid blocks are found (`total_invalid > 0`):
   - Fix each invalid diagram (max 3 attempts per diagram) using `mermaid_policy.md` and the `fix_hint`.
   - Re-run the script until no invalid blocks remain.
   - If still invalid after 3 attempts, comment out the diagram block and add a TODO noting the error.

4) Report is saved to `{output_dir}/_reports/mermaid_invalid.json`. A report with `total_unvalidated > 0` is incomplete, even when `total_invalid == 0`.

### 2. Document Structure Validation

1) Run `validate_docs_structure.py` script:
```bash
python scripts/validate_docs_structure.py \
    --doc-dir "{doc_dir}" \
    --toc-file "{toc_file}" \
    --output "{output_dir}/_reports/structure_validation.json"
```

2) If errors are found (`summary.is_valid == false`), fix each issue based on `fix_hint`:

**PAGE_ID fixes**:
   - If missing: Add `<!-- PAGE_ID: {expected_id} -->` at the start of file
   - If incorrect: Replace with correct PAGE_ID from TOC

**AUTOGEN marker fixes**:
   - Missing BEGIN: Add `<!-- BEGIN:AUTOGEN {section_id} -->` before section content
   - Missing END: Add `<!-- END:AUTOGEN {section_id} -->` after section content
   - Mismatched: Correct section_id to match TOC
   - Orphaned: Remove unpaired markers

3) Re-run the script to confirm all errors are fixed

4) Report is saved to `{output_dir}/_reports/structure_validation.json`

**Safe auto-fixes allowed**:
  - Add missing PAGE_ID/AUTOGEN markers
  - Fix mismatched section_id to match TOC
  - Do NOT rewrite page content

## Mermaid acceptance gate

A page set may be described as Mermaid-validated only when every extracted Mermaid block has `validation_status=passed` from an actual Mermaid.js parse+SVG render or Mermaid CLI run. Static policy checks are useful preflight checks but are not a parser. If any block is `not_run`, the overall Mermaid result is `not_run`/incomplete, not passed. If any block is `failed`, the result is failed until corrected and re-run. Keep the validation engine/version and execution evidence in the report.
