#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
JOB_DIR="${REPO_DIR}/work/review-jobs/req-consistency-001"

cd "${REPO_DIR}"

python3 - <<'PY' "${JOB_DIR}"
import json
import sys
from pathlib import Path

job_dir = Path(sys.argv[1])
job_path = job_dir / "job.json"
loop_path = job_dir / "loop-status.json"

if not job_path.exists():
    raise SystemExit(f"Job file not found: {job_path}")

job = json.loads(job_path.read_text(encoding="utf-8"))
loop = json.loads(loop_path.read_text(encoding="utf-8")) if loop_path.exists() else {}

print(f"job_id: {job.get('job_id')}")
print(f"job_status: {job.get('status')}")
print(f"loop_status: {loop.get('status')}")
print(f"decision: {loop.get('decision')}")
print(f"current_iteration: {job.get('current_iteration')}")
print()

pages = job.get("pages", [])
published = {str(item.get("page_id")): item for item in job.get("published", [])}

for page in pages:
    page_id = str(page["page_id"])
    workspace_dir = Path(page["workspace_dir"])
    page_path = Path(page["page_path"])
    merged_path = workspace_dir / "merged.md"
    diff_path = workspace_dir / "merged.diff"
    merged_exists = merged_path.exists()
    diff_exists = diff_path.exists()
    changed = False
    if merged_exists and page_path.exists():
        changed = merged_path.read_text(encoding="utf-8") != page_path.read_text(encoding="utf-8")
    published_item = published.get(page_id)
    print(f"page_id: {page_id}")
    print(f"  title: {page.get('title')}")
    print(f"  merged_exists: {merged_exists}")
    print(f"  diff_exists: {diff_exists}")
    print(f"  changed_vs_source: {changed}")
    print(f"  published: {published_item is not None}")
    if published_item is not None:
        print(f"  previous_version: {published_item.get('previous_version')}")
        print(f"  updated_version: {published_item.get('updated_version')}")
    print()
PY
