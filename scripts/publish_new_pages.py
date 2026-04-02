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
from lib_review_job import load_private_job_state, write_job_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish newly created pages from a review job.")
    parser.add_argument("--job-dir", required=True, help="Path to the review job directory")
    parser.add_argument("--config", required=True, help="Path to adapter config JSON. Supports rest mode.")
    parser.add_argument("--version-message", default="Direct review job create page", help="Confluence version message")
    parser.add_argument("--dry-run", action="store_true", help="List new page candidates without creating them")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    job_dir = Path(args.job_dir)
    payload = load_private_job_state(job_dir)
    if payload.get("status") not in {"approved", "published"}:
        raise SystemExit(f"Review job is not approved for create-page publish: {payload.get('status')}")

    config = load_app_config(args.config)
    if config.mode not in {"rest", "file"}:
        raise SystemExit("publish_new_pages.py currently supports rest and file modes")

    candidates = collect_new_page_candidates(job_dir, payload)
    if args.dry_run:
        print(json.dumps({"job_id": payload["job_id"], "new_page_candidates": candidates}, ensure_ascii=False, indent=2))
        return 0
    if not candidates:
        print(json.dumps({"job_id": payload["job_id"], "created_pages": []}, ensure_ascii=False, indent=2))
        return 0

    adapter = build_adapter(config)
    created: list[dict[str, object]] = []
    try:
        for candidate in candidates:
            body = Path(candidate["input_path"]).read_text(encoding="utf-8")
            snapshot = adapter.create_page(
                title=str(candidate["title"]),
                body=body,
                parent_id=(str(candidate["parent_id"]) if candidate.get("parent_id") else None),
                space_id=(str(candidate["space_id"]) if candidate.get("space_id") else None),
                version_message=args.version_message,
            )
            created.append(
                {
                    "slug": candidate["slug"],
                    "page_id": snapshot.page_id,
                    "title": snapshot.title,
                    "parent_id": candidate.get("parent_id"),
                    "space_id": snapshot.space_id,
                    "input_path": candidate["input_path"],
                    "meta_path": candidate["meta_path"],
                }
            )
    finally:
        adapter.close()

    payload["status"] = "published"
    payload["created_pages"] = created
    write_job_state(job_dir, payload)
    print(json.dumps({"job_id": payload["job_id"], "status": payload["status"], "created_pages": created}, ensure_ascii=False, indent=2))
    return 0


def collect_new_page_candidates(job_dir: Path, payload: dict[str, object]) -> list[dict[str, object]]:
    job_metadata = payload.get("job_metadata") or {}
    existing_created = {
        str(item.get("slug"))
        for item in payload.get("created_pages", [])
        if isinstance(item, dict) and item.get("slug")
    }
    default_parent_id = None
    default_space_id = None
    if isinstance(job_metadata, dict):
        default_parent_id = job_metadata.get("default_parent_id")
        default_space_id = job_metadata.get("default_space_id")

    new_pages_root = job_dir / "new-pages"
    candidates: list[dict[str, object]] = []
    if not new_pages_root.exists():
        return candidates

    for page_dir in sorted(new_pages_root.iterdir()):
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        if page_dir.name in existing_created:
            continue
        meta_path = page_dir / "page.meta.json"
        input_path = page_dir / "page.md"
        if not meta_path.exists() or not input_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        title = str(meta.get("title") or "").strip()
        if not title:
            raise SystemExit(f"New page metadata is missing title: {meta_path}")
        parent_id = str(meta.get("parent_id") or default_parent_id or "").strip() or None
        if not parent_id:
            raise SystemExit(f"New page metadata is missing parent_id and no default parent is configured: {meta_path}")
        space_id = str(meta.get("space_id") or default_space_id or "").strip() or None
        candidates.append(
            {
                "slug": page_dir.name,
                "title": title,
                "parent_id": parent_id,
                "space_id": space_id,
                "input_path": str(input_path),
                "meta_path": str(meta_path),
            }
        )
    return candidates


if __name__ == "__main__":
    raise SystemExit(main())
