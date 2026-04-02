from __future__ import annotations

import json
from pathlib import Path

from confluence_section_mcp.adapters import PageSnapshot


def write_snapshot_to_file_root(snapshot: PageSnapshot, output_root: Path) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    page_path = output_root / f"{snapshot.page_id}.md"
    meta_path = output_root / f"{snapshot.page_id}.meta.json"
    page_path.write_text(snapshot.body, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
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
    return {
        "page_path": str(page_path),
        "meta_path": str(meta_path),
    }


def read_snapshot_from_file_root(page_id: str, input_root: Path) -> PageSnapshot:
    page_path = input_root / f"{page_id}.md"
    meta_path = input_root / f"{page_id}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return PageSnapshot(
        page_id=page_id,
        title=str(meta.get("title", page_id)),
        version=int(meta.get("version", 1)),
        body=page_path.read_text(encoding="utf-8"),
        body_format=str(meta.get("body_format", "markdown")),
        space_id=(str(meta["space_id"]) if meta.get("space_id") is not None else None),
    )
