#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from confluence_section_mcp.adapters import build_adapter
from confluence_section_mcp.config import load_app_config
from confluence_section_mcp.gigacode_settings import build_app_config_from_gigacode_settings
from lib_confluence_workflow import prepare_workspace
from lib_review_job import ReviewPageRecord, build_page_overview, initialize_review_job


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Confluence review job with one local workspace per page. Supports direct API config, local file mode, or hidden Atlassian MCP via GigaCode settings."
    )
    parser.add_argument("--job-id", required=True, help="Job identifier used under the workspace root")
    parser.add_argument("--page-id", action="append", dest="page_ids", required=True, help="Confluence page id to include; repeat for multiple pages")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--config", help="Path to adapter config JSON. Supports rest, file, or mcp modes.")
    source_group.add_argument("--settings", help="Path to GigaCode settings.json for hidden Atlassian MCP backend")
    parser.add_argument("--server-name", default="Atlassian", help="MCP server name inside settings.json when --settings is used")
    parser.add_argument("--workspace-root", default="work/review-jobs", help="Root directory where review jobs are created")
    parser.add_argument("--task-file", help="Path to a text/markdown file containing the global task")
    parser.add_argument("--task-text", help="Inline task text if no task file is used")
    parser.add_argument("--max-chars", type=int, default=12000, help="Target maximum chunk size")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.task_file and not args.task_text:
        raise SystemExit("Provide --task-file or --task-text")

    if args.settings:
        config = build_app_config_from_gigacode_settings(args.settings, server_name=args.server_name)
    else:
        config = load_app_config(args.config)
    if config.mode not in {"rest", "file", "mcp"}:
        raise SystemExit("bootstrap_direct_review_job.py supports rest, file, and hidden MCP backends only")

    task_text = args.task_text or Path(args.task_file).read_text(encoding="utf-8")
    job_dir = Path(args.workspace_root) / args.job_id
    pages_root = job_dir / "pages"
    pages_root.mkdir(parents=True, exist_ok=True)

    adapter = build_adapter(config)
    page_records: list[ReviewPageRecord] = []
    try:
        for page_id in args.page_ids:
            snapshot = adapter.get_page(page_id)
            incoming_dir = pages_root / page_id
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
    finally:
        adapter.close()

    job_state = initialize_review_job(job_dir=job_dir, task_text=task_text, pages=page_records, max_chars=args.max_chars)
    print(json.dumps(job_state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
