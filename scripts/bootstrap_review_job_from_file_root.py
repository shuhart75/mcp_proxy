#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib_confluence_workflow import prepare_workspace
from lib_page_store import read_snapshot_from_file_root
from lib_review_job import ReviewPageRecord, build_page_overview, initialize_review_job, private_job_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a review job from pages that were already fetched into a local file root."
    )
    parser.add_argument("--job-id", required=True, help="Job identifier used under the workspace root")
    parser.add_argument("--page-id", action="append", dest="page_ids", required=True, help="Page id to include; repeat for multiple pages")
    parser.add_argument("--input-root", required=True, help="Directory containing <page-id>.md and <page-id>.meta.json files")
    parser.add_argument("--workspace-root", default="work/review-jobs", help="Root directory where review jobs are created")
    parser.add_argument("--task-file", help="Path to a text/markdown file containing the global task")
    parser.add_argument("--task-text", help="Inline task text if no task file is used")
    parser.add_argument("--max-chars", type=int, default=12000, help="Target maximum chunk size")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.task_file and not args.task_text:
        raise SystemExit("Provide --task-file or --task-text")

    task_text = args.task_text or Path(args.task_file).read_text(encoding="utf-8")
    job_dir = Path(args.workspace_root) / args.job_id
    pages_root = job_dir / "pages"
    private_pages_root = private_job_dir(job_dir) / "pages"
    pages_root.mkdir(parents=True, exist_ok=True)
    private_pages_root.mkdir(parents=True, exist_ok=True)
    input_root = Path(args.input_root)

    page_records: list[ReviewPageRecord] = []
    for page_id in args.page_ids:
        snapshot = read_snapshot_from_file_root(page_id, input_root)
        incoming_dir = private_pages_root / page_id
        incoming_dir.mkdir(parents=True, exist_ok=True)
        source_path = incoming_dir / "incoming-page.source"
        source_path.write_text(snapshot.body, encoding="utf-8")
        summary = prepare_workspace(
            page_id=page_id,
            page_file=source_path,
            workspace_root=pages_root,
            task_text=task_text,
            max_chars=args.max_chars,
            page_filename="page.source",
            original_filename="page.original.source",
            private_workspace_root=private_pages_root,
        )
        meta_path = Path(summary.workspace_dir) / "page.meta.json"
        meta_path.write_text(
            json.dumps(
                {
                    "page_id": snapshot.page_id,
                    "title": snapshot.title,
                    "version": snapshot.version,
                    "body_format": snapshot.body_format,
                    "space_id": snapshot.space_id,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        overview_path = Path(summary.workspace_dir) / "overview.md"
        build_page_overview(
            manifest_path=Path(summary.manifest_path),
            output_path=overview_path,
            title=snapshot.title,
            page_id=snapshot.page_id,
            body_format=snapshot.body_format,
        )
        page_records.append(
            ReviewPageRecord(
                page_id=snapshot.page_id,
                title=snapshot.title,
                version=snapshot.version,
                body_format=snapshot.body_format,
                workspace_dir=summary.workspace_dir,
                page_path=summary.page_path,
                manifest_path=summary.manifest_path,
                overview_path=str(overview_path),
                chunk_count=summary.chunk_count,
                strategy=summary.strategy,
            )
        )

    job_state = initialize_review_job(job_dir=job_dir, task_text=task_text, pages=page_records, max_chars=args.max_chars)
    print(json.dumps(job_state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
