#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

JOB_DIR="${REPO_DIR}/work/review-jobs/req-consistency-001"
REPORT_PATH="${JOB_DIR}/reports/iteration-001/controller-report.md"
ADVANCE_SCRIPT="${REPO_DIR}/scripts/advance_review_loop.py"
PUBLISH_SCRIPT="${REPO_DIR}/tools/publish_req_consistency_001.sh"

cat <<EOF
Use \`multi-page-confluence-consistency\`.

Mode: review-and-fix.
Do not publish automatically.
Do not create subagents unless absolutely necessary.
This job is already bootstrapped from local files. Do not fetch pages again.
Use the exact absolute paths below. Do not reinterpret them relative to the current working directory.

Job directory:
\`${JOB_DIR}\`

Execution rules:
1. Read only:
   - \`${JOB_DIR}/job.json\`
   - \`${JOB_DIR}/overview.md\`
   - page \`overview.md\` files referenced from the job
2. Open only the chunks that are actually needed.
3. Edit only the chunks that require changes.
4. Merge only changed pages by writing:
   - \`${JOB_DIR}/pages/<page-id>/merged.md\`
   - \`${JOB_DIR}/pages/<page-id>/merged.diff\`
5. Write the controller report to:
   - \`${REPORT_PATH}\`
6. Run:
   - \`python3 ${ADVANCE_SCRIPT} --job-dir ${JOB_DIR} --report ${REPORT_PATH}\`
7. If the loop status is \`needs-edits\`, do one more targeted pass.
8. If the loop status is \`approved\`, stop and tell me the job is ready for publish with \`bash ${PUBLISH_SCRIPT}\`.

Do not publish automatically.
EOF
