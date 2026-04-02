#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/publish_review_job_with_debug.sh --job-id JOB_ID [--config /path/to/confluence-rest.config.json]
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID=""
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-id)
      JOB_ID="$2"
      ARGS+=("$1" "$2")
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "${JOB_ID}" ]]; then
  echo "--job-id is required" >&2
  exit 1
fi

cd "${REPO_DIR}"

if bash "${REPO_DIR}/tools/publish_review_job.sh" "${ARGS[@]}"; then
  exit 0
fi

echo
echo "Publish failed. Collecting debug bundle..."
DEBUG_FILE="$(bash "${REPO_DIR}/tools/collect_review_job_debug.sh" "${JOB_ID}")"
echo "Debug file: ${DEBUG_FILE}"
exit 1
