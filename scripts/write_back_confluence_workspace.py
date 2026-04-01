#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluence_section_mcp.adapters import build_adapter
from confluence_section_mcp.gigacode_settings import build_app_config_from_gigacode_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a merged Confluence page back using the Atlassian MCP config from GigaCode settings."
    )
    parser.add_argument("--page-id", required=True, help="Confluence page id")
    parser.add_argument("--input", help="Path to the merged markdown file. Defaults to work/confluence/<page-id>/merged.md")
    parser.add_argument("--settings", help="Path to GigaCode settings.json. Defaults to standard locations.")
    parser.add_argument("--server-name", default="Atlassian", help="Name of the Atlassian MCP server in settings.json")
    parser.add_argument("--version-message", default="Large-page workspace update", help="Confluence version message")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input) if args.input else Path("work/confluence") / args.page_id / "merged.md"
    body = input_path.read_text(encoding="utf-8")

    config = build_app_config_from_gigacode_settings(args.settings, server_name=args.server_name)
    adapter = build_adapter(config)
    try:
        current = adapter.get_page(args.page_id)
        updated = adapter.update_page(
            page_id=current.page_id,
            title=current.title,
            body=body,
            version=current.version,
            version_message=args.version_message,
            space_id=current.space_id,
        )
    finally:
        adapter.close()

    print(
        json.dumps(
            {
                "page_id": updated.page_id,
                "title": updated.title,
                "input_path": str(input_path),
                "previous_version": current.version,
                "updated_version": updated.version,
                "body_format": updated.body_format,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
