#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_review_job import materialize_merged_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create merged.md and merged.diff files for all edited pages in a review job.")
    parser.add_argument("--job-dir", required=True, help="Absolute path to the review job directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = materialize_merged_outputs(Path(args.job_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
