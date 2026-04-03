#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_review_job import validate_job_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate strict-mode outputs for a review job.")
    parser.add_argument("--job-dir", required=True, help="Absolute path to the review job directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_job_outputs(Path(args.job_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
