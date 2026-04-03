#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/show_review_job_prompt.sh --job-id JOB_ID [--mode analyze|update|create|mixed|review-only|review-and-fix]
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID=""
MODE=""

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
cd "${REPO_DIR}"

python3 - <<'PY' "${REPO_DIR}" "${JOB_ID}" "${MODE}"
import json
import sys
from pathlib import Path

repo_dir = Path(sys.argv[1])
job_id = sys.argv[2]
raw_mode = sys.argv[3].strip()
job_dir = repo_dir / "work" / "review-jobs" / job_id
job_path = job_dir / "job.json"
if not job_path.exists():
    raise SystemExit(f"Job file not found: {job_path}")

job = json.loads(job_path.read_text(encoding="utf-8"))
loop_path = job_dir / "loop-status.json"
loop = json.loads(loop_path.read_text(encoding="utf-8")) if loop_path.exists() else {}
job_metadata = job.get("job_metadata") or {}

if not raw_mode:
    raw_mode = str(job_metadata.get("request_mode") or "analyze")
aliases = {
    "review-only": "analyze",
    "review-and-fix": "update",
}
mode = aliases.get(raw_mode, raw_mode)
if mode not in {"analyze", "update", "create", "mixed"}:
    raise SystemExit(f"Unsupported mode: {mode}")

report_path = loop.get("next_report_path") or job.get("next_report_path")
if not report_path:
    iteration = int(job.get("current_iteration", 1))
    report_path = str(job_dir / "reports" / f"iteration-{iteration:03d}" / "controller-report.md")
report_path = str((repo_dir / report_path).resolve()) if not Path(report_path).is_absolute() else str(Path(report_path).resolve())

advance_script = repo_dir / "scripts" / "advance_review_loop.py"
materialize_script = repo_dir / "scripts" / "materialize_review_job_outputs.py"
validate_script = repo_dir / "scripts" / "validate_review_job_outputs.py"
finish_script = repo_dir / "tools" / "finish_confluence_job.sh"
new_pages_dir = job_dir / "new-pages"
default_parent_id = job_metadata.get("default_parent_id")

print(f"Mode: {mode}.")
if mode == "analyze":
    print("Do not publish anything.")
else:
    print("Do not publish automatically.")
print("Do not invoke any Confluence skill or wrapper prompt. Follow this instruction set directly.")
print("Do not create subagents. Delegation is forbidden for this workflow.")
print("This job is already bootstrapped from local files. Do not fetch pages again.")
print("Do not inspect or edit full-source page files such as `page.source`, `page.original.source`, `incoming-page.source`, `workspace.json`, or hidden/internal job files.")
print("Do not create helper scripts, notebooks, or ad-hoc tools inside the review job. Use only the provided commands below.")
print("Only chunk files, page-level merged outputs, controller reports, and `new-pages/*` are valid write targets.")
print("Use the exact absolute paths below. Do not reinterpret them relative to the current working directory.\n")
print("Job directory:")
print(f"`{job_dir}`\n")
print("Execution rules:")
print("1. Read only:")
print(f"   - `{job_dir / 'job.json'}`")
print(f"   - `{job_dir / 'overview.md'}`")
print("   - page `overview.md` files referenced from the job")
print("2. Open only the chunks that are actually needed.")
if mode == "analyze":
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
    print("7. At the end, tell me to run:")
    print(f"   - `bash {finish_script} --job-id {job_id}`")
    print("\nDo not publish.")
else:
    step = 3
    if mode in {"update", "mixed"}:
        print(f"{step}. Edit only the existing-page chunks that require changes.")
        step += 1
        print(f"{step}. After editing chunks, create page-level outputs by running:")
        print(f"   - `python3 {materialize_script} --job-dir {job_dir}`")
        print("   This command creates `merged.md` and `merged.diff` for every changed existing page.")
        step += 1
    if mode in {"create", "mixed"}:
        print(f"{step}. If the task requires new pages, create one directory per new page under:")
        print(f"   - `{new_pages_dir}/<slug>/page.md`")
        print(f"   - `{new_pages_dir}/<slug>/page.meta.json`")
        print("   Required meta fields:")
        print("   - `title`")
        print("   - `parent_id`")
        print("   Optional meta fields:")
        print("   - `space_id`")
        print("   - `body_format`")
        if default_parent_id:
            print(f"   Default parent_id for new pages in this job: `{default_parent_id}`")
        step += 1
    print(f"{step}. Validate outputs before writing the report by running:")
    print(f"   - `python3 {validate_script} --job-dir {job_dir}`")
    step += 1
    print(f"{step}. Write the controller report to this exact path and overwrite its previous contents for the current iteration:")
    print(f"   - `{report_path}`")
    step += 1
    print(f"{step}. The controller report must contain these exact lines as standalone lines:")
    print("   - `Decision: approved` only if actual page edits were made and changed page-level merged outputs exist")
    print("   - `Decision: review-only` if no edits were needed")
    print("   - `Decision: needs-edits` if another pass is needed")
    print("   - `Recommended next action: <text>`")
    print("   Do not copy forward an old `needs-edits` report after making changes.")
    step += 1
    print(f"{step}. Run:")
    print(f"   - `python3 {advance_script} --job-dir {job_dir} --report {report_path}`")
    step += 1
    print(f"{step}. If the loop status is `needs-edits`, do one more targeted pass.")
    step += 1
    print(f"{step}. If the loop status is `approved`, stop and tell me to run:")
    print(f"   - `bash {finish_script} --job-id {job_id}`")
    step += 1
    print(f"{step}. If the loop status is `review-only`, stop and explicitly say that no publish is needed.")
    print("\nDo not publish automatically.")
PY
