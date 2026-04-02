#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/show_review_job_prompt.sh --job-id JOB_ID [--mode review-only|review-and-fix]
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID=""
MODE="review-only"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-id)
      JOB_ID="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
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
if [[ "${MODE}" != "review-only" && "${MODE}" != "review-and-fix" ]]; then
  echo "--mode must be review-only or review-and-fix" >&2
  exit 1
fi

cd "${REPO_DIR}"

python3 - <<'PY' "${REPO_DIR}" "${JOB_ID}" "${MODE}"
import json
import sys
from pathlib import Path

repo_dir = Path(sys.argv[1])
job_id = sys.argv[2]
mode = sys.argv[3]
job_dir = repo_dir / "work" / "review-jobs" / job_id
job_path = job_dir / "job.json"
if not job_path.exists():
    raise SystemExit(f"Job file not found: {job_path}")

job = json.loads(job_path.read_text(encoding="utf-8"))
loop_path = job_dir / "loop-status.json"
loop = json.loads(loop_path.read_text(encoding="utf-8")) if loop_path.exists() else {}

report_path = loop.get("next_report_path") or job.get("next_report_path")
if not report_path:
    iteration = int(job.get("current_iteration", 1))
    report_path = str(job_dir / "reports" / f"iteration-{iteration:03d}" / "controller-report.md")

advance_script = repo_dir / "scripts" / "advance_review_loop.py"
publish_script = repo_dir / "tools" / "publish_review_job.sh"

print("Use `multi-page-confluence-consistency`.\n")
print(f"Mode: {mode}.")
if mode == "review-only":
    print("Do not publish anything.")
else:
    print("Do not publish automatically.")
print("Do not create subagents unless absolutely necessary.")
print("This job is already bootstrapped from local files. Do not fetch pages again.")
print("Use the exact absolute paths below. Do not reinterpret them relative to the current working directory.\n")
print("Job directory:")
print(f"`{job_dir}`\n")
print("Execution rules:")
print("1. Read only:")
print(f"   - `{job_dir / 'job.json'}`")
print(f"   - `{job_dir / 'overview.md'}`")
print("   - page `overview.md` files referenced from the job")
print("2. Open only the chunks that are actually needed.")
if mode == "review-only":
    print("3. Write the controller report to:")
    print(f"   - `{report_path}`")
    print("4. The controller report must contain these exact lines as standalone lines:")
    print("   - `Decision: approved` or `Decision: review-only` or `Decision: needs-edits`")
    print("   - `Recommended next action: <text>`")
    print("5. Run:")
    print(f"   - `python3 {advance_script} --job-dir {job_dir} --report {report_path}`")
    print("6. Stop and report:")
    print("   - main findings")
    print("   - pages/chunks inspected")
    print(f"   - `{job_dir / 'loop-status.json'}`")
    print("\nDo not publish.")
else:
    print("3. Edit only the chunks that require changes.")
    print("4. Do not claim readiness for publish unless you actually created page-level outputs for changed pages:")
    print(f"   - `{job_dir}/pages/<page-id>/merged.md`")
    print(f"   - `{job_dir}/pages/<page-id>/merged.diff`")
    print("5. Write the controller report to:")
    print(f"   - `{report_path}`")
    print("6. The controller report must contain these exact lines as standalone lines:")
    print("   - `Decision: approved` only if actual page edits were made and changed page-level merged outputs exist")
    print("   - `Decision: review-only` if no edits were needed")
    print("   - `Decision: needs-edits` if another pass is needed")
    print("   - `Recommended next action: <text>`")
    print("7. Run:")
    print(f"   - `python3 {advance_script} --job-dir {job_dir} --report {report_path}`")
    print("8. If the loop status is `needs-edits`, do one more targeted pass.")
    print("9. If the loop status is `approved`, stop and tell me the job is ready for publish with:")
    print(f"   - `bash {publish_script} --job-id {job_id}`")
    print("10. If the loop status is `review-only`, stop and explicitly say that no publish is needed.")
    print("\nDo not publish automatically.")
PY
