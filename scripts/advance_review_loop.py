#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_review_job import advance_review_loop


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Advance a review job after a controller report and prepare the next iteration if needed."
    )
    parser.add_argument("--job-dir", required=True, help="Path to the review job directory")
    parser.add_argument("--report", required=True, help="Path to the controller or cross-page report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = advance_review_loop(job_dir=Path(args.job_dir), report_path=Path(args.report))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
