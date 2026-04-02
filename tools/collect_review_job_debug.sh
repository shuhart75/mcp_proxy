#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID="${1:-req-consistency-001}"
JOB_DIR="${REPO_DIR}/work/review-jobs/${JOB_ID}"
OUTPUT_DIR="${REPO_DIR}/work/debug"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_FILE="${OUTPUT_DIR}/${JOB_ID}-debug-${TIMESTAMP}.txt"

mkdir -p "${OUTPUT_DIR}"

{
  echo "== Environment =="
  echo "timestamp: ${TIMESTAMP}"
  echo "repo_dir: ${REPO_DIR}"
  echo "job_id: ${JOB_ID}"
  echo "job_dir: ${JOB_DIR}"
  echo

  echo "== Git =="
  git -C "${REPO_DIR}" rev-parse HEAD || true
  git -C "${REPO_DIR}" status --short || true
  echo

  echo "== Job Tree =="
  find "${JOB_DIR}" -maxdepth 3 -type f 2>/dev/null | sort || true
  echo

  echo "== Job JSON =="
  cat "${JOB_DIR}/job.json" 2>/dev/null || true
  echo

  echo "== Loop Status =="
  cat "${JOB_DIR}/loop-status.json" 2>/dev/null || true
  echo

  echo "== Reports =="
  find "${JOB_DIR}/reports" -type f 2>/dev/null | sort || true
  echo
  for report in "${JOB_DIR}"/reports/iteration-*/controller-report.md; do
    [ -f "${report}" ] || continue
    echo "--- REPORT: ${report} ---"
    sed -n '1,260p' "${report}" || true
    echo
  done

  echo "== Merge/Edited Files =="
  find "${JOB_DIR}/pages" \( -name 'merged.md' -o -name 'merged.diff' -o -name 'edited.md' \) -type f 2>/dev/null | sort || true
  echo

  echo "== File Sizes =="
  find "${JOB_DIR}/pages" -name 'merged.md' -type f -exec wc -c {} \; 2>/dev/null || true
  find "${JOB_DIR}/pages" -name 'edited.md' -type f -exec wc -c {} \; 2>/dev/null || true
  echo

  echo "== Candidate Comparison =="
  python3 - <<'PY' "${JOB_DIR}"
import json
import sys
from pathlib import Path

job_dir = Path(sys.argv[1])
job_json = job_dir / "job.json"
if not job_json.exists():
    raise SystemExit(0)
payload = json.loads(job_json.read_text(encoding="utf-8"))
for page in payload.get("pages", []):
    workspace_dir = Path(page["workspace_dir"])
    page_path = Path(page["page_path"])
    merged_path = workspace_dir / "merged.md"
    print(f"page_id={page['page_id']}")
    print(f"  page_path={page_path}")
    print(f"  merged_path={merged_path}")
    print(f"  page_exists={page_path.exists()}")
    print(f"  merged_exists={merged_path.exists()}")
    if page_path.exists() and merged_path.exists():
        same = page_path.read_text(encoding='utf-8') == merged_path.read_text(encoding='utf-8')
        print(f"  merged_equals_source={same}")
    print()
PY
  echo

  echo "== GigaCode Shadow Copies =="
  find "${HOME}/.gigacode" -path "*${JOB_ID}*" -type f 2>/dev/null | sort || true
  echo
} > "${OUTPUT_FILE}"

echo "${OUTPUT_FILE}"

