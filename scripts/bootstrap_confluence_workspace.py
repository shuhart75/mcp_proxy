#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.adapters import build_adapter
from confluence_section_mcp.gigacode_settings import build_app_config_from_gigacode_settings
from lib_confluence_workflow import prepare_workspace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a Confluence page using the Atlassian MCP config from GigaCode settings and prepare a local workspace."
    )
    parser.add_argument("--page-id", required=True, help="Confluence page id")
    parser.add_argument("--workspace-root", default="work/confluence", help="Root directory where page workspaces are created")
    parser.add_argument("--task-file", help="Path to a text/markdown file containing the global task")
    parser.add_argument("--task-text", help="Inline task text if no task file is used")
    parser.add_argument("--settings", help="Path to GigaCode settings.json. Defaults to standard locations.")
    parser.add_argument("--server-name", default="Atlassian", help="Name of the Atlassian MCP server in settings.json")
    parser.add_argument("--max-chars", type=int, default=12000, help="Target maximum chunk size for heading-based splitting")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.task_file and not args.task_text:
        raise SystemExit("Provide --task-file or --task-text")
    task_text = args.task_text or Path(args.task_file).read_text(encoding="utf-8")

    config = build_app_config_from_gigacode_settings(args.settings, server_name=args.server_name)
    adapter = build_adapter(config)
    try:
        snapshot = adapter.get_page(args.page_id)
    finally:
        adapter.close()

    workspace_root = Path(args.workspace_root)
    incoming_dir = workspace_root / args.page_id
    incoming_dir.mkdir(parents=True, exist_ok=True)
    incoming_page = incoming_dir / "incoming-page.md"
    incoming_task = incoming_dir / "incoming-task.md"
    incoming_page.write_text(snapshot.body, encoding="utf-8")
    incoming_task.write_text(task_text, encoding="utf-8")

    summary = prepare_workspace(
        page_id=args.page_id,
        page_file=incoming_page,
        workspace_root=workspace_root,
        task_text=task_text,
        max_chars=args.max_chars,
    )

    page_meta = {
        "page_id": snapshot.page_id,
        "title": snapshot.title,
        "version": snapshot.version,
        "body_format": snapshot.body_format,
        "space_id": snapshot.space_id,
        "settings_server": args.server_name,
    }
    meta_path = Path(summary.workspace_dir) / "page.meta.json"
    meta_path.write_text(json.dumps(page_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "workspace_dir": summary.workspace_dir,
                "page_id": summary.page_id,
                "title": snapshot.title,
                "version": snapshot.version,
                "body_format": snapshot.body_format,
                "page_path": summary.page_path,
                "task_path": summary.task_path,
                "manifest_path": summary.manifest_path,
                "meta_path": str(meta_path),
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
