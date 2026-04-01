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
from lib_review_job import collect_publish_candidates, load_job_state, write_job_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish all changed pages from an approved direct-review job through direct Confluence API."
    )
    parser.add_argument("--job-dir", required=True, help="Path to the review job directory")
    parser.add_argument("--config", required=True, help="Path to direct API config JSON in rest mode")
    parser.add_argument("--version-message", default="Direct review job update", help="Confluence version message")
    parser.add_argument("--dry-run", action="store_true", help="List publish candidates without updating Confluence")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    job_dir = Path(args.job_dir)
    payload = load_job_state(job_dir)
    if payload.get("status") not in {"approved"}:
        raise SystemExit(f"Review job is not approved for publish: {payload.get('status')}")

    config = load_app_config(args.config)
    if config.mode != "rest":
        raise SystemExit("publish_review_job.py requires a direct API config in rest mode")

    candidates = collect_publish_candidates(job_dir)
    if args.dry_run:
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
        return 0

    adapter = build_adapter(config)
    published: list[dict[str, object]] = []
    try:
        for candidate in candidates["publish_candidates"]:
            page_id = str(candidate["page_id"])
            current = adapter.get_page(page_id)
            body = Path(candidate["input_path"]).read_text(encoding="utf-8")
            updated = adapter.update_page(
                page_id=current.page_id,
                title=current.title,
                body=body,
                version=current.version,
                version_message=args.version_message,
                space_id=current.space_id,
            )
            published.append(
                {
                    "page_id": updated.page_id,
                    "title": updated.title,
                    "previous_version": current.version,
                    "updated_version": updated.version,
                    "input_path": candidate["input_path"],
                }
            )
    finally:
        adapter.close()

    payload["status"] = "published"
    payload["published"] = published
    write_job_state(job_dir, payload)
    result = {
        "job_id": payload["job_id"],
        "status": payload["status"],
        "published": published,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
