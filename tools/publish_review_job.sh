#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/publish_review_job.sh --job-id JOB_ID [--config /path/to/confluence-rest.config.json]
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID=""
CONFIG_PATH="${HOME}/.gigacode/confluence-orchestrator/confluence-rest.config.json"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-id)
      JOB_ID="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "${JOB_ID}" ]]; then
  echo "--job-id is required" >&2
  exit 1
fi

cd "${REPO_DIR}"
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

python3 scripts/publish_review_job.py \
  --job-dir "work/review-jobs/${JOB_ID}" \
  --config "${CONFIG_PATH}" \
  "${EXTRA_ARGS[@]}"
