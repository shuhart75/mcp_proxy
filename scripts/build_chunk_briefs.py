#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_confluence_workflow import build_chunk_briefs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build per-chunk editing briefs for the Confluence workflow.")
    parser.add_argument("--manifest", required=True, help="Path to chunk manifest.json")
    parser.add_argument("--task-file", required=True, help="Path to task.md containing the global task")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_chunk_briefs(manifest_path=Path(args.manifest), task_path=Path(args.task_file))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
