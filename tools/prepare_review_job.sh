#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/prepare_review_job.sh \
    --job-id JOB_ID \
    --page-id PAGE_ID \
    --page-id PAGE_ID \
    (--task-text "..." | --task-file /path/to/task.md) \
    [--config /path/to/confluence-rest.config.json] \
    [--workspace-root work/review-jobs] \
    [--fetched-root work/fetched-pages] \
    [--max-chars 12000] \
    [--no-clean]
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID=""
TASK_TEXT=""
TASK_FILE=""
CONFIG_PATH="${HOME}/.gigacode/confluence-orchestrator/confluence-rest.config.json"
WORKSPACE_ROOT="work/review-jobs"
FETCHED_ROOT="work/fetched-pages"
MAX_CHARS="12000"
CLEAN="1"
PAGE_IDS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-id)
      JOB_ID="$2"
      shift 2
      ;;
    --page-id)
      PAGE_IDS+=("$2")
      shift 2
      ;;
    --task-text)
      TASK_TEXT="$2"
      shift 2
      ;;
    --task-file)
      TASK_FILE="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --workspace-root)
      WORKSPACE_ROOT="$2"
      shift 2
      ;;
    --fetched-root)
      FETCHED_ROOT="$2"
      shift 2
      ;;
    --max-chars)
      MAX_CHARS="$2"
      shift 2
      ;;
    --no-clean)
      CLEAN="0"
      shift
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
if [[ ${#PAGE_IDS[@]} -eq 0 ]]; then
  echo "At least one --page-id is required" >&2
  exit 1
fi
if [[ -z "${TASK_TEXT}" && -z "${TASK_FILE}" ]]; then
  echo "Provide --task-text or --task-file" >&2
  exit 1
fi
if [[ -n "${TASK_TEXT}" && -n "${TASK_FILE}" ]]; then
  echo "Use either --task-text or --task-file, not both" >&2
  exit 1
fi

cd "${REPO_DIR}"
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

FETCH_ROOT_PATH="${FETCHED_ROOT}/${JOB_ID}"
JOB_DIR_PATH="${WORKSPACE_ROOT}/${JOB_ID}"

if [[ "${CLEAN}" == "1" ]]; then
  rm -rf "${REPO_DIR}/${FETCH_ROOT_PATH}"
  rm -rf "${REPO_DIR}/${JOB_DIR_PATH}"
fi

FETCH_CMD=(python3 scripts/fetch_confluence_pages.py --config "${CONFIG_PATH}" --output-root "${FETCH_ROOT_PATH}")
for page_id in "${PAGE_IDS[@]}"; do
  FETCH_CMD+=(--page-id "${page_id}")
done
"${FETCH_CMD[@]}"

BOOTSTRAP_CMD=(
  python3 scripts/bootstrap_review_job_from_file_root.py
  --job-id "${JOB_ID}"
  --input-root "${FETCH_ROOT_PATH}"
  --workspace-root "${WORKSPACE_ROOT}"
  --max-chars "${MAX_CHARS}"
)
for page_id in "${PAGE_IDS[@]}"; do
  BOOTSTRAP_CMD+=(--page-id "${page_id}")
done
if [[ -n "${TASK_FILE}" ]]; then
  BOOTSTRAP_CMD+=(--task-file "${TASK_FILE}")
else
  BOOTSTRAP_CMD+=(--task-text "${TASK_TEXT}")
fi
"${BOOTSTRAP_CMD[@]}"

cat <<EOF
Prepared review job:
  ${REPO_DIR}/${JOB_DIR_PATH}

Next:
  1. Review only:
     cd ${REPO_DIR}
     bash tools/show_review_job_prompt.sh --job-id ${JOB_ID} --mode review-only
  2. Review and fix:
     cd ${REPO_DIR}
     bash tools/show_review_job_prompt.sh --job-id ${JOB_ID} --mode review-and-fix
  3. Publish if approved:
     cd ${REPO_DIR}
     bash tools/publish_review_job.sh --job-id ${JOB_ID}
  4. Print a short summary any time:
     cd ${REPO_DIR}
     bash tools/summarize_review_job.sh --job-id ${JOB_ID}
EOF
