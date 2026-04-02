from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib_review_job import ReviewPageRecord, advance_review_loop, build_page_overview, initialize_review_job, load_job_state, load_private_job_state, private_job_dir


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

    def test_advance_review_loop_accepts_markdown_header_decision_format(self) -> None:
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
                "## Decision: review-only\n\n## Recommended next action\n\nnone\n",
                encoding="utf-8",
            )
            result = advance_review_loop(job_dir=job_dir, report_path=report_path)
            self.assertEqual(result["status"], "review-only")
            self.assertEqual(result["decision"], "review-only")
            self.assertEqual(result["recommended_next_action"], "none")

    def test_initialize_review_job_persists_job_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            job_dir = Path(tmpdir) / "job-1"
            payload = initialize_review_job(
                job_dir=job_dir,
                task_text="Create pages.",
                pages=[],
                max_chars=12000,
                job_metadata={"request_mode": "create", "default_parent_id": "123"},
            )
            self.assertEqual(payload["job_metadata"]["request_mode"], "create")
            stored = load_job_state(job_dir)
            self.assertEqual(stored["job_metadata"]["default_parent_id"], "123")

    def test_initialize_review_job_hides_private_page_paths_from_public_state(self) -> None:
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
                        page_path="/tmp/job-1-internal/pages/1/page.source",
                        manifest_path="/tmp/job-1/pages/1/chunks/manifest.json",
                        overview_path="/tmp/job-1/pages/1/overview.md",
                        chunk_count=2,
                        strategy="html-headings",
                    )
                ],
                max_chars=12000,
            )
            public_state = load_job_state(job_dir)
            private_state = load_private_job_state(job_dir)
            self.assertNotIn("page_path", public_state["pages"][0])
            self.assertEqual(private_state["pages"][0]["page_path"], "/tmp/job-1-internal/pages/1/page.source")
            self.assertTrue((private_job_dir(job_dir) / "job.json").exists())


if __name__ == "__main__":
    unittest.main()
