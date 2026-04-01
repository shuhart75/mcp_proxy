#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_markdown_chunks import split_markdown, write_workspace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split large Confluence markdown into bounded chunks.")
    parser.add_argument("--input", required=True, help="Path to source markdown file")
    parser.add_argument("--output-dir", required=True, help="Workspace directory for chunk files")
    parser.add_argument("--max-chars", type=int, default=12000, help="Target maximum chunk size for heading-based splitting")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = Path(args.input)
    output_dir = Path(args.output_dir)
    source = source_path.read_text(encoding="utf-8")
    strategy, chunks = split_markdown(source, max_chars=args.max_chars)
    manifest_path = write_workspace(source_path, output_dir, source, strategy, chunks)
    print(
        json.dumps(
            {
                "input": str(source_path),
                "output_dir": str(output_dir),
                "strategy": strategy,
                "chunk_count": len(chunks),
                "manifest": str(manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
