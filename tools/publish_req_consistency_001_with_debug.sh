#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

if bash "${REPO_DIR}/tools/publish_req_consistency_001.sh"; then
  exit 0
fi

echo
echo "Publish failed. Collecting debug bundle..."
DEBUG_FILE="$(bash "${REPO_DIR}/tools/collect_review_job_debug.sh" req-consistency-001)"
echo "Debug file: ${DEBUG_FILE}"
exit 1
