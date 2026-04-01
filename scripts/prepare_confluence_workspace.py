#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_confluence_workflow import prepare_workspace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a standard workspace for a large Confluence editing task.")
    parser.add_argument("--page-id", required=True, help="Confluence page id used for workspace naming")
    parser.add_argument("--page-file", required=True, help="Path to fetched page markdown")
    parser.add_argument("--workspace-root", default="work/confluence", help="Root directory where page workspaces are created")
    parser.add_argument("--task-file", help="Path to a text/markdown file containing the global task")
    parser.add_argument("--task-text", help="Inline task text if no task file is used")
    parser.add_argument("--max-chars", type=int, default=12000, help="Target maximum chunk size for heading-based splitting")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.task_file and not args.task_text:
        raise SystemExit("Provide --task-file or --task-text")
    task_text = args.task_text or Path(args.task_file).read_text(encoding="utf-8")
    summary = prepare_workspace(
        page_id=args.page_id,
        page_file=Path(args.page_file),
        workspace_root=Path(args.workspace_root),
        task_text=task_text,
        max_chars=args.max_chars,
    )
    print(
        json.dumps(
            {
                "workspace_dir": summary.workspace_dir,
                "page_id": summary.page_id,
                "page_path": summary.page_path,
                "task_path": summary.task_path,
                "manifest_path": summary.manifest_path,
                "strategy": summary.strategy,
                "chunk_count": summary.chunk_count,
                "should_chunk": summary.should_chunk,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
