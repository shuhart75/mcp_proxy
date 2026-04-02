#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/summarize_review_job.sh --job-id JOB_ID
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
JOB_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-id)
      JOB_ID="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${JOB_ID}" ]]; then
  echo "--job-id is required" >&2
  exit 1
fi

cd "${REPO_DIR}"

python3 - <<'PY' "${REPO_DIR}" "${JOB_ID}"
import json
import sys
from pathlib import Path

repo_dir = Path(sys.argv[1])
job_id = sys.argv[2]
sys.path.insert(0, str(repo_dir / "scripts"))

from lib_review_job import load_private_job_state, validate_job_outputs

job_dir = repo_dir / "work" / "review-jobs" / job_id
job_path = job_dir / "job.json"
loop_path = job_dir / "loop-status.json"

if not job_path.exists():
    raise SystemExit(f"Job file not found: {job_path}")

job = load_private_job_state(job_dir)
loop = json.loads(loop_path.read_text(encoding="utf-8")) if loop_path.exists() else {}
job_metadata = job.get("job_metadata") or {}
validation = validate_job_outputs(job_dir, job)

print(f"job_id: {job.get('job_id')}")
print(f"job_status: {job.get('status')}")
print(f"loop_status: {loop.get('status')}")
print(f"decision: {loop.get('decision')}")
print(f"current_iteration: {job.get('current_iteration')}")
print(f"request_mode: {job_metadata.get('request_mode')}")
print(f"default_parent_id: {job_metadata.get('default_parent_id')}")
print(f"strict_validation_ok: {validation.get('ok')}")
if validation.get("errors"):
    print("validation_errors:")
    for item in validation["errors"]:
        print(f"  - {item}")
print()

pages = job.get("pages", [])
published = {str(item.get("page_id")): item for item in job.get("published", [])}
created_pages = {str(item.get("slug")): item for item in job.get("created_pages", [])}

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

print("new_pages:")
new_pages_root = job_dir / "new-pages"
if new_pages_root.exists():
    found = False
    for page_dir in sorted(new_pages_root.iterdir()):
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        found = True
        meta_path = page_dir / "page.meta.json"
        page_md_path = page_dir / "page.md"
        meta = {}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        created_item = created_pages.get(page_dir.name)
        print(f"  slug: {page_dir.name}")
        print(f"    page_md_exists: {page_md_path.exists()}")
        print(f"    meta_exists: {meta_path.exists()}")
        print(f"    title: {meta.get('title')}")
        print(f"    parent_id: {meta.get('parent_id')}")
        print(f"    created: {created_item is not None}")
        if created_item is not None:
            print(f"    created_page_id: {created_item.get('page_id')}")
        print()
    if not found:
        print("  (none)")
else:
    print("  (none)")
PY
