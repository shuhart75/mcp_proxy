#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib_confluence_workflow import summarize_controller_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize controller-review output and create a machine-readable status file.")
    parser.add_argument("--report", required=True, help="Path to controller-report.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = summarize_controller_report(Path(args.report))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
