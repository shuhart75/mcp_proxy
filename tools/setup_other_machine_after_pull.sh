#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DOC_DIR="${HOME}/.gigacode/confluence-orchestrator"
TARGET_CONFIG_DIR="${HOME}/.gigacode/confluence-orchestrator"
TARGET_CONFIG_PATH="${TARGET_CONFIG_DIR}/confluence-rest.config.json"
TARGET_CONFIG_SAMPLE_PATH="${TARGET_CONFIG_DIR}/confluence-rest.config.example.json"
TARGET_PROMPT_DIR="${TARGET_DOC_DIR}/prompts"

cd "${REPO_DIR}"

mkdir -p "${TARGET_DOC_DIR}"
mkdir -p "${TARGET_CONFIG_DIR}"
mkdir -p "${TARGET_PROMPT_DIR}"

bash "${REPO_DIR}/tools/setup_stage1_extension.sh"

cp "${REPO_DIR}/docs/direct-api-v2.md" "${TARGET_DOC_DIR}/direct-api-v2.md"
cp "${REPO_DIR}/examples/confluence-rest.config.example.json" "${TARGET_CONFIG_SAMPLE_PATH}"
cp "${REPO_DIR}/prompts/review-only-two-pages.md" "${TARGET_PROMPT_DIR}/review-only-two-pages.md"
cp "${REPO_DIR}/prompts/review-only-existing-job.md" "${TARGET_PROMPT_DIR}/review-only-existing-job.md"

if [ ! -f "${TARGET_CONFIG_PATH}" ]; then
  cp "${REPO_DIR}/examples/confluence-rest.config.example.json" "${TARGET_CONFIG_PATH}"
fi

cat <<EOF
Other-machine setup completed.

Prepared files:
  ${TARGET_DOC_DIR}/direct-api-v2.md
  ${TARGET_CONFIG_SAMPLE_PATH}
  ${TARGET_CONFIG_PATH}
  ${TARGET_PROMPT_DIR}/review-only-two-pages.md
  ${TARGET_PROMPT_DIR}/review-only-existing-job.md
  ${REPO_DIR}/tools/bootstrap_req_consistency_001.sh

What to do next on this machine:

1. Optional validation:
   cd ${REPO_DIR}
   python3 -m unittest discover -s tests -v

2. Bootstrap the prepared review job for pages 18028730639 and 18048816272:
   cd ${REPO_DIR}
   bash tools/bootstrap_req_consistency_001.sh

   Log file:
   ${REPO_DIR}/work/review-jobs/req-consistency-001/bootstrap.log

3. Then use this short prompt in GigaCode:
   ${TARGET_PROMPT_DIR}/review-only-existing-job.md

4. Open the generated job overview manually if needed:
   cd ${REPO_DIR}
   sed -n '1,220p' work/review-jobs/req-consistency-001/job.json
   sed -n '1,220p' work/review-jobs/req-consistency-001/overview.md

5. If the job is approved later, publish with:
   cd ${REPO_DIR}
   python3 scripts/publish_review_job.py \\
     --job-dir work/review-jobs/req-consistency-001 \\
     --settings ~/.gigacode/settings.json

6. After each future git pull, run again:
   cd ${REPO_DIR}
   bash tools/setup_other_machine_after_pull.sh

Reference docs:
  ${TARGET_DOC_DIR}/direct-api-v2.md
  ${TARGET_DOC_DIR}/stage1-macos-setup.md
  ${TARGET_DOC_DIR}/stage2-runbook.md
  ${TARGET_PROMPT_DIR}/review-only-two-pages.md
  ${TARGET_PROMPT_DIR}/review-only-existing-job.md
EOF
