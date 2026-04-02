#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

bash "${REPO_DIR}/tools/fetch_req_consistency_001.sh"
bash "${REPO_DIR}/tools/bootstrap_req_consistency_001_from_files.sh"

cat <<EOF
Prepared review job:
  ${REPO_DIR}/work/review-jobs/req-consistency-001

Next:
  1. Copy the prompt with:
     cd ${REPO_DIR}
     bash tools/show_req_consistency_001_prompt.sh
  2. Paste it into GigaCode.
  3. If the result is approved later, publish with:
     cd ${REPO_DIR}
     bash tools/publish_req_consistency_001.sh
EOF
