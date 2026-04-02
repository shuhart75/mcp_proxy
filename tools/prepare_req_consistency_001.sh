#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

rm -rf "${REPO_DIR}/work/fetched-pages/req-consistency-001"
rm -rf "${REPO_DIR}/work/review-jobs/req-consistency-001"

bash "${REPO_DIR}/tools/fetch_req_consistency_001.sh"
bash "${REPO_DIR}/tools/bootstrap_req_consistency_001_from_files.sh"

cat <<EOF
Prepared review job:
  ${REPO_DIR}/work/review-jobs/req-consistency-001

Next:
  1. For consistency-check only, copy the review-only prompt with:
     cd ${REPO_DIR}
     bash tools/show_req_consistency_001_prompt.sh
  2. If you explicitly want GigaCode to edit pages, use instead:
     cd ${REPO_DIR}
     bash tools/show_req_consistency_001_fix_prompt.sh
  3. Paste the chosen prompt into GigaCode.
  4. Publish only if the fix-mode run actually produced merged outputs and finished with status approved:
     cd ${REPO_DIR}
     bash tools/publish_req_consistency_001.sh
EOF
