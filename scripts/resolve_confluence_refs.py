#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from urllib.parse import parse_qs, urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve Confluence page refs or URLs to page ids.")
    parser.add_argument("--ref", action="append", dest="refs", required=True, help="Confluence page id or URL; repeat for multiple refs")
    return parser.parse_args()


def resolve_ref(ref: str) -> dict[str, str]:
    stripped = ref.strip()
    if stripped.isdigit():
        return {"ref": ref, "page_id": stripped}

    parsed = urlparse(stripped)
    query = parse_qs(parsed.query)
    page_id = query.get("pageId", [None])[0]
    if page_id and page_id.isdigit():
        return {"ref": ref, "page_id": page_id}

    match = re.search(r"/pages/(\d+)(?:/|$)", parsed.path)
    if match:
        return {"ref": ref, "page_id": match.group(1)}

    raise SystemExit(f"Could not resolve Confluence page id from ref: {ref}")


def main() -> int:
    args = parse_args()
    payload = {"refs": [resolve_ref(item) for item in args.refs]}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
