from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gridforge_agents.prompts import classify_issue
from gridforge_agents.tools import ToolError, ToolRunner
from gridforge_agents.workflow import _parse_review, _version_tuple


class ToolRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runner = ToolRunner(self.root, writable=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_write_and_read_repository_file(self) -> None:
        self.runner.write_file("core/example.py", "value = 42\n")
        result = self.runner.read_file("core/example.py")
        self.assertIn("value = 42", result)

    def test_tail_reads_append_only_registers(self) -> None:
        self.runner.write_file("Modification_Register.txt", "first\nsecond\nthird\n")
        result = self.runner.read_file("Modification_Register.txt", tail_lines=2)
        self.assertIn("2: second", result)
        self.assertIn("3: third", result)

    def test_register_is_append_only(self) -> None:
        self.runner.write_file("Modification_Register.txt", "historical entry\\n")
        with self.assertRaises(ToolError):
            self.runner.write_file("Modification_Register.txt", "replacement\\n")
        self.runner.append_modification_register("new entry\\n")
        result = (self.root / "Modification_Register.txt").read_text(encoding="utf-8")
        self.assertTrue(result.startswith("historical entry\\n"))
        self.assertIn("new entry", result)

    def test_replace_requires_one_exact_match(self) -> None:
        self.runner.write_file("sample.txt", "before\n")
        self.runner.replace_text("sample.txt", "before", "after")
        self.assertIn("after", self.runner.read_file("sample.txt"))
        with self.assertRaises(ToolError):
            self.runner.replace_text("sample.txt", "missing", "other")

    def test_rejects_path_traversal_and_secret_files(self) -> None:
        with self.assertRaises(ToolError):
            self.runner.read_file("../outside.txt")
        with self.assertRaises(ToolError):
            self.runner.write_file(".env", "SECRET=not-allowed")

    def test_read_only_runner_rejects_writes(self) -> None:
        readonly = ToolRunner(self.root, writable=False)
        with self.assertRaises(ToolError):
            readonly.execute("write_file", {"path": "x.txt", "content": "no"})


class WorkflowParsingTests(unittest.TestCase):
    def test_version_parser(self) -> None:
        self.assertEqual(_version_tuple("0.21.0"), (0, 21, 0))
        self.assertEqual(_version_tuple("0.3.0"), (0, 3, 0))
        self.assertIsNone(_version_tuple("unknown"))

    def test_issue_ownership_tags_take_precedence(self) -> None:
        self.assertEqual(classify_issue("[Control] Channel freshness", "MeasurementChannel"), "control-simulation")
        self.assertEqual(classify_issue("[UI/Control] Timer inspector", "Apply and discard"), "control-simulation")
        self.assertEqual(classify_issue("[Instrumentation Wiring] Signal identity", "SLD"), "measurement")
        self.assertEqual(classify_issue("[UI/Keyboard] Editor shortcuts", "Tool dispatch"), "sld-ui")

    def test_review_parser_accepts_approved_json(self) -> None:
        review = _parse_review('{"verdict":"APPROVE","summary":"ok","findings":[]}')
        self.assertEqual(review["verdict"], "APPROVE")

    def test_review_parser_rejects_missing_verdict(self) -> None:
        with self.assertRaises(Exception):
            _parse_review('{"summary":"not a verdict"}')


if __name__ == "__main__":
    unittest.main()
