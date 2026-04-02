#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

JOB_DIR="${REPO_DIR}/work/review-jobs/req-consistency-001"
REPORT_PATH="${JOB_DIR}/reports/iteration-001/controller-report.md"
ADVANCE_SCRIPT="${REPO_DIR}/scripts/advance_review_loop.py"

cat <<EOF
Use \`multi-page-confluence-consistency\`.

Mode: review-only.
Do not publish anything.
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
3. Write the controller report to:
   - \`${REPORT_PATH}\`
4. The controller report must contain these exact lines as standalone lines:
   - \`Decision: approved\` or \`Decision: review-only\` or \`Decision: needs-edits\`
   - \`Recommended next action: <text>\`
5. Run:
   - \`python3 ${ADVANCE_SCRIPT} --job-dir ${JOB_DIR} --report ${REPORT_PATH}\`
6. Stop and report:
   - main findings
   - pages/chunks inspected
   - \`${JOB_DIR}/loop-status.json\`

Do not publish.
EOF
