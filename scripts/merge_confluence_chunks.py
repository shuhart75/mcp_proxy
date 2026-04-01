#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_markdown_chunks import merge_from_manifest, write_diff


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge edited Confluence chunk files back into one markdown document.")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json created by chunk_confluence_markdown.py")
    parser.add_argument("--output", required=True, help="Path to merged markdown output")
    parser.add_argument("--diff-output", help="Optional path to unified diff output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    result = merge_from_manifest(manifest_path, Path(args.output))
    if args.diff_output:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_path = Path(manifest["source_path"])
        source_text = source_path.read_text(encoding="utf-8")
        merged_text = Path(args.output).read_text(encoding="utf-8")
        diff_path = write_diff(source_text, merged_text, Path(args.diff_output), from_name=source_path.name, to_name=Path(args.output).name)
        result["diff_output"] = str(diff_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
