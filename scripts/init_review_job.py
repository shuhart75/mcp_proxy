#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib_review_job import initialize_review_job


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize an empty review job for create-only or mixed workflows.")
    parser.add_argument("--job-id", required=True, help="Job identifier used under the workspace root")
    parser.add_argument("--workspace-root", default="work/review-jobs", help="Root directory where review jobs are created")
    parser.add_argument("--task-file", help="Path to a text/markdown file containing the global task")
    parser.add_argument("--task-text", help="Inline task text if no task file is used")
    parser.add_argument("--max-chars", type=int, default=12000, help="Target maximum chunk size")
    parser.add_argument("--mode", default="create", help="Requested operator mode: analyze, update, create, mixed")
    parser.add_argument("--source-ref", action="append", default=[], help="Original source page ref or URL; repeat for multiple refs")
    parser.add_argument("--default-parent-id", help="Default Confluence parent page id for newly created pages")
    parser.add_argument("--default-space-id", help="Default Confluence space id for newly created pages")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.task_file and not args.task_text:
        raise SystemExit("Provide --task-file or --task-text")

    task_text = args.task_text or Path(args.task_file).read_text(encoding="utf-8")
    job_dir = Path(args.workspace_root) / args.job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "new-pages").mkdir(parents=True, exist_ok=True)
    (job_dir / "artifacts" / "updated-pages").mkdir(parents=True, exist_ok=True)
    (job_dir / "artifacts" / "new-pages").mkdir(parents=True, exist_ok=True)

    job_state = initialize_review_job(
        job_dir=job_dir,
        task_text=task_text,
        pages=[],
        max_chars=args.max_chars,
        job_metadata={
            "request_mode": args.mode,
            "source_refs": list(args.source_ref or []),
            "default_parent_id": args.default_parent_id,
            "default_space_id": args.default_space_id,
            "allow_new_pages": True,
        },
    )
    print(json.dumps(job_state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
