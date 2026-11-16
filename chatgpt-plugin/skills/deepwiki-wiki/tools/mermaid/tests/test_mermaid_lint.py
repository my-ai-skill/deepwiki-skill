import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "mermaid_lint.py"
spec = importlib.util.spec_from_file_location("mermaid_lint", MODULE)
ml = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ml
spec.loader.exec_module(ml)

class MermaidLintTests(unittest.TestCase):
    def test_rejects_quoted_yes_pipe_label(self):
        self.assertEqual(len(ml.lint_block('graph TD\n A -->|"Yes"| B\n')), 1)

    def test_rejects_whitespace_quoted_no_pipe_label(self):
        self.assertEqual(len(ml.lint_block('graph TD\n A -->| "No" | B\n')), 1)

    def test_accepts_unquoted_pipe_label(self):
        self.assertEqual(ml.lint_block('graph TD\n A -->|Yes| B\n A -->|No| C\n'), [])

    def test_repairs_only_quote_wrappers_and_is_idempotent(self):
        src = 'graph TD\n A -->|"Yes"| B\n A -->| "No" | C\n'
        fixed, count = ml.repair_block(src)
        self.assertEqual(count, 2)
        self.assertIn('A -->|Yes| B', fixed)
        self.assertIn('A -->|No| C', fixed)
        self.assertEqual(ml.repair_block(fixed), (fixed, 0))

    def test_preserves_middle_label_syntax(self):
        src = 'graph TD\n A -- "label with punctuation" --> B\n'
        self.assertEqual(ml.repair_block(src), (src, 0))

    def test_does_not_touch_node_labels(self):
        src = 'graph TD\n A["Node label"] --> B{"Decision?"}\n'
        self.assertEqual(ml.repair_block(src), (src, 0))

    def test_does_not_touch_non_flowchart_diagrams(self):
        src = 'sequenceDiagram\n A->>B: "Yes"\n'
        self.assertEqual(ml.repair_block(src), (src, 0))

    def test_markdown_repairs_only_mermaid_fences(self):
        fence = chr(96) * 3
        src = ('Text ' + chr(96) + 'A -->|"inline"| B' + chr(96) + '\n\n' +
               fence + 'mermaid\ngraph TD\n A -->|"Yes"| B\n' + fence + '\n' +
               fence + 'mermaid\nsequenceDiagram\n A->>B: "Yes"\n' + fence + '\n')
        fixed, count = ml.repair_markdown(src)
        self.assertEqual(count, 1)
        self.assertIn('A -->|Yes| B', fixed)
        self.assertIn('A->>B: "Yes"', fixed)
        self.assertIn('A -->|"inline"| B', fixed)

    def test_other_flowchart_edge_forms(self):
        src = 'flowchart LR\n A -.->|"async"| B\n A ==>|"main"| C\n'
        fixed, count = ml.repair_block(src)
        self.assertEqual(count, 2)
        self.assertIn('A -.->|async| B', fixed)
        self.assertIn('A ==>|main| C', fixed)

if __name__ == "__main__":
    unittest.main(verbosity=2)
