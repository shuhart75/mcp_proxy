from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib_confluence_workflow import build_chunk_briefs, prepare_workspace, summarize_controller_report


class ConfluenceWorkflowTests(unittest.TestCase):
    def test_prepare_workspace_and_build_briefs(self) -> None:
        source = "# One\nalpha\n## Two\nbeta\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            page_file = root / "incoming-page.md"
            page_file.write_text(source, encoding="utf-8")
            summary = prepare_workspace(
                page_id="123",
                page_file=page_file,
                workspace_root=root / "work",
                task_text="Update both sections.",
                max_chars=100,
            )
            self.assertTrue(summary.should_chunk)
            manifest_path = Path(summary.manifest_path)
            task_path = Path(summary.task_path)
            result = build_chunk_briefs(manifest_path=manifest_path, task_path=task_path)
            self.assertEqual(result["chunk_count"], 2)
            first_brief = Path(result["briefs"][0]["brief_path"]).read_text(encoding="utf-8")
            self.assertIn("Global Task", first_brief)
            self.assertIn("Update both sections.", first_brief)

    def test_summarize_controller_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "controller-report.md"
            report_path.write_text(
                "Decision: approved\n"
                "Task coverage: all good\n"
                "Recommended next action: write back the merged page\n",
                encoding="utf-8",
            )
            summary = summarize_controller_report(report_path)
            self.assertTrue(summary["approved"])
            self.assertEqual(summary["decision"], "approved")
            status_path = Path(summary["status_path"])
            self.assertTrue(status_path.exists())
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["approved"])


if __name__ == "__main__":
    unittest.main()
