#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_markdown_chunks import merge_from_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge edited Confluence chunk files back into one markdown document.")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json created by chunk_confluence_markdown.py")
    parser.add_argument("--output", required=True, help="Path to merged markdown output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = merge_from_manifest(Path(args.manifest), Path(args.output))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
