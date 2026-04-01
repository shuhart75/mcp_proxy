from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib_review_job import ReviewPageRecord, advance_review_loop, build_page_overview, initialize_review_job


class ReviewJobTests(unittest.TestCase):
    def test_build_page_overview_strips_markup_for_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            chunk_dir = root / "chunks" / "001-scope"
            chunk_dir.mkdir(parents=True, exist_ok=True)
            source_path = chunk_dir / "source.md"
            source_path.write_text("<h1>Scope</h1><p>Alpha <strong>beta</strong>.</p>", encoding="utf-8")
            manifest_path = root / "chunks" / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "strategy": "html-headings",
                        "chunks": [
                            {
                                "chunk_id": "001-scope",
                                "label": "Scope",
                                "path": str(source_path),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            overview_path = root / "overview.md"
            build_page_overview(
                manifest_path=manifest_path,
                output_path=overview_path,
                title="Scope Page",
                page_id="123",
                body_format="storage",
            )
            overview = overview_path.read_text(encoding="utf-8")
            self.assertIn("Alpha beta.", overview)

    def test_advance_review_loop_creates_next_iteration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            job_dir = Path(tmpdir) / "job-1"
            initialize_review_job(
                job_dir=job_dir,
                task_text="Check consistency.",
                pages=[
                    ReviewPageRecord(
                        page_id="1",
                        title="Page One",
                        version=1,
                        body_format="storage",
                        workspace_dir="/tmp/job-1/pages/1",
                        page_path="/tmp/job-1/pages/1/page.source",
                        manifest_path="/tmp/job-1/pages/1/chunks/manifest.json",
                        overview_path="/tmp/job-1/pages/1/overview.md",
                        chunk_count=2,
                        strategy="html-headings",
                    )
                ],
                max_chars=12000,
            )
            report_path = job_dir / "reports" / "iteration-001" / "controller-report.md"
            report_path.write_text(
                "Decision: needs-fixes\nRecommended next action: revise terminology and re-check\n",
                encoding="utf-8",
            )
            result = advance_review_loop(job_dir=job_dir, report_path=report_path)
            self.assertEqual(result["status"], "needs-edits")
            self.assertEqual(result["current_iteration"], 2)
            self.assertTrue((job_dir / "reports" / "iteration-002").exists())


if __name__ == "__main__":
    unittest.main()
