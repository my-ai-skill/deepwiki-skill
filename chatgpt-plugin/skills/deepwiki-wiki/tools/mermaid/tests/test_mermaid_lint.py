import importlib.util
import unittest
import sys
from pathlib import Path

MODULE = Path(__file__).parents[1] / "mermaid_lint.py"
spec = importlib.util.spec_from_file_location("mermaid_lint", MODULE)
ml = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ml
spec.loader.exec_module(ml)

class MermaidLintTests(unittest.TestCase):
    def test_rejects_quoted_yes_pipe_label(self):
        src = 'graph TD\n A -->|"Yes"| B\n'
        self.assertEqual(len(ml.lint_block(src)), 1)

    def test_rejects_whitespace_quoted_no_pipe_label(self):
        src = 'graph TD\n A -->| "No" | B\n'
        self.assertEqual(len(ml.lint_block(src)), 1)

    def test_accepts_unquoted_pipe_label(self):
        src = 'graph TD\n A -->|Yes| B\n A -->|No| C\n'
        self.assertEqual(ml.lint_block(src), [])

    def test_repairs_only_quote_wrappers_and_is_idempotent(self):
        src = 'graph TD\n A -->|"Yes"| B\n A -->| "No" | C\n'
        fixed, count = ml.repair_block(src)
        self.assertEqual(count, 2)
        self.assertIn('A -->|Yes| B', fixed)
        self.assertIn('A -->|No| C', fixed)
        fixed_again, count_again = ml.repair_block(fixed)
        self.assertEqual((fixed_again, count_again), (fixed, 0))

    def test_preserves_middle_label_syntax(self):
        src = 'graph TD\n A -- "label with punctuation" --> B\n'
        fixed, count = ml.repair_block(src)
        self.assertEqual((fixed, count), (src, 0))

    def test_does_not_touch_node_labels(self):
        src = 'graph TD\n A["Node label"] --> B{"Decision?"}\n'
        fixed, count = ml.repair_block(src)
        self.assertEqual((fixed, count), (src, 0))

    def test_does_not_touch_non_flowchart_diagrams(self):
        src = 'sequenceDiagram\n A->>B: "Yes"\n'
        fixed, count = ml.repair_block(src)
        self.assertEqual((fixed, count), (src, 0))

    def test_markdown_repairs_only_mermaid_fences(self):
        src = ('Text `A -->|"inline"| B`\n\n```mermaid\ngraph TD\n A -->|"Yes"| B\n```\n'
               '\n```mermaid\nsequenceDiagram\n A->>B: "Yes"\n```\n')
        fixed, count = ml.repair_markdown(src)
        self.assertEqual(count, 1)
        self.assertIn('A -->|Yes| B', fixed)
        self.assertIn('A->>B: "Yes"', fixed)
        self.assertIn('`A -->|"inline"| B`', fixed)

    def test_repairs_four_original_report_edges(self):
        src = ('graph TD\n'
               '  C -->|"no"| D["Report unexpected call"]\n'
               '  C -->|"yes"| E["Update call count"]\n'
               '  F -->|"yes"| G["Report excessive call"]\n'
               '  F -->|"no"| H["Choose Action"]\n')
        fixed, count = ml.repair_block(src)
        self.assertEqual(count, 4)
        self.assertEqual(len(ml.lint_block(fixed)), 0)
        self.assertIn('C -->|no| D["Report unexpected call"]', fixed)
        self.assertIn('C -->|yes| E["Update call count"]', fixed)
        self.assertIn('F -->|yes| G["Report excessive call"]', fixed)
        self.assertIn('F -->|no| H["Choose Action"]', fixed)

    def test_other_flowchart_edge_forms(self):
        src = 'flowchart LR\n A -.->|"async"| B\n A ==>|"main"| C\n'
        fixed, count = ml.repair_block(src)
        self.assertEqual(count, 2)
        self.assertIn('A -.->|async| B', fixed)
        self.assertIn('A ==>|main| C', fixed)

if __name__ == "__main__":
    unittest.main(verbosity=2)
