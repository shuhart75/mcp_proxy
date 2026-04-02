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
from lib_page_store import write_snapshot_to_file_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Confluence pages through direct API and store them as local file-mode inputs."
    )
    parser.add_argument("--config", required=True, help="Path to adapter config JSON. Intended for rest mode.")
    parser.add_argument("--page-id", action="append", dest="page_ids", required=True, help="Confluence page id to fetch; repeat for multiple pages")
    parser.add_argument("--output-root", default="work/fetched-pages", help="Directory where fetched pages are written")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_app_config(args.config)
    if config.mode not in {"rest", "file"}:
        raise SystemExit("fetch_confluence_pages.py supports only rest mode and local file mode")

    output_root = Path(args.output_root)
    adapter = build_adapter(config)
    pages: list[dict[str, object]] = []
    try:
        for page_id in args.page_ids:
            snapshot = adapter.get_page(page_id)
            stored = write_snapshot_to_file_root(snapshot, output_root)
            pages.append(
                {
                    "page_id": snapshot.page_id,
                    "title": snapshot.title,
                    "version": snapshot.version,
                    "body_format": snapshot.body_format,
                    **stored,
                }
            )
    finally:
        adapter.close()

    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "pages": pages,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
