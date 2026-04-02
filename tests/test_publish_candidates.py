from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib_review_job import collect_publish_candidates, initialize_review_job, ReviewPageRecord
from publish_review_job import _materialize_merged_outputs


class PublishCandidatesTests(unittest.TestCase):
    def test_materialize_merged_outputs_builds_merged_file_from_edited_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            job_dir = Path(tmpdir) / "job-1"
            page_dir = job_dir / "pages" / "123"
            chunk_dir = page_dir / "chunks" / "001-a"
            chunk_dir.mkdir(parents=True, exist_ok=True)
            source_path = page_dir / "page.source"
            source_path.write_text("Original", encoding="utf-8")
            (chunk_dir / "source.md").write_text("Original", encoding="utf-8")
            (chunk_dir / "edited.md").write_text("Changed", encoding="utf-8")
            manifest_path = page_dir / "chunks" / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_path": str(source_path),
                        "strategy": "single",
                        "chunks": [
                            {
                                "chunk_id": "001-a",
                                "label": "A",
                                "start": 0,
                                "end": 8,
                                "path": str(chunk_dir / "source.md"),
                                "edited_path": str(chunk_dir / "edited.md"),
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            initialize_review_job(
                job_dir=job_dir,
                task_text="Review consistency.",
                pages=[
                    ReviewPageRecord(
                        page_id="123",
                        title="Page One",
                        version=1,
                        body_format="storage",
                        workspace_dir=str(page_dir),
                        page_path=str(source_path),
                        manifest_path=str(manifest_path),
                        overview_path=str(page_dir / "overview.md"),
                        chunk_count=1,
                        strategy="single",
                    )
                ],
                max_chars=12000,
            )
            payload = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
            _materialize_merged_outputs(job_dir, payload)
            self.assertEqual((page_dir / "merged.md").read_text(encoding="utf-8"), "Changed")
            self.assertTrue((page_dir / "merged.diff").exists())

    def test_collect_publish_candidates_only_returns_changed_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            job_dir = Path(tmpdir) / "job-1"
            page_dir = job_dir / "pages" / "123"
            page_dir.mkdir(parents=True, exist_ok=True)
            source_path = page_dir / "page.source"
            source_path.write_text("Original", encoding="utf-8")
            merged_path = page_dir / "merged.md"
            merged_path.write_text("Changed", encoding="utf-8")
            initialize_review_job(
                job_dir=job_dir,
                task_text="Review consistency.",
                pages=[
                    ReviewPageRecord(
                        page_id="123",
                        title="Page One",
                        version=1,
                        body_format="storage",
                        workspace_dir=str(page_dir),
                        page_path=str(source_path),
                        manifest_path=str(page_dir / "chunks" / "manifest.json"),
                        overview_path=str(page_dir / "overview.md"),
                        chunk_count=2,
                        strategy="html-headings",
                    )
                ],
                max_chars=12000,
            )
            payload = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
            payload["status"] = "approved"
            (job_dir / "job.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            result = collect_publish_candidates(job_dir)
            self.assertEqual(len(result["publish_candidates"]), 1)
            self.assertEqual(result["publish_candidates"][0]["page_id"], "123")


if __name__ == "__main__":
    unittest.main()
