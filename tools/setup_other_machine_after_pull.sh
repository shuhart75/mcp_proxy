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
cp "${REPO_DIR}/docs/file-first-v3.md" "${TARGET_DOC_DIR}/file-first-v3.md"
cp "${REPO_DIR}/examples/confluence-rest.config.example.json" "${TARGET_CONFIG_SAMPLE_PATH}"
cp "${REPO_DIR}/prompts/review-only-two-pages.md" "${TARGET_PROMPT_DIR}/review-only-two-pages.md"
cp "${REPO_DIR}/prompts/review-only-existing-job.md" "${TARGET_PROMPT_DIR}/review-only-existing-job.md"
cp "${REPO_DIR}/prompts/review-and-fix-existing-job.md" "${TARGET_PROMPT_DIR}/review-and-fix-existing-job.md"
cp "${REPO_DIR}/prompts/review-and-fix-existing-job-file-first.md" "${TARGET_PROMPT_DIR}/review-and-fix-existing-job-file-first.md"

if [ ! -f "${TARGET_CONFIG_PATH}" ]; then
  cp "${REPO_DIR}/examples/confluence-rest.config.example.json" "${TARGET_CONFIG_PATH}"
fi

cat <<EOF
Other-machine setup completed.

Prepared files:
  ${TARGET_DOC_DIR}/direct-api-v2.md
  ${TARGET_DOC_DIR}/file-first-v3.md
  ${TARGET_CONFIG_SAMPLE_PATH}
  ${TARGET_CONFIG_PATH}
  ${TARGET_PROMPT_DIR}/review-only-two-pages.md
  ${TARGET_PROMPT_DIR}/review-only-existing-job.md
  ${TARGET_PROMPT_DIR}/review-and-fix-existing-job.md
  ${TARGET_PROMPT_DIR}/review-and-fix-existing-job-file-first.md
  ${REPO_DIR}/tools/fetch_req_consistency_001.sh
  ${REPO_DIR}/tools/bootstrap_req_consistency_001_from_files.sh
  ${REPO_DIR}/tools/prepare_req_consistency_001.sh
  ${REPO_DIR}/tools/publish_req_consistency_001.sh
  ${REPO_DIR}/tools/show_req_consistency_001_prompt.sh
  ${REPO_DIR}/tools/show_req_consistency_001_fix_prompt.sh

What to do next on this machine:

1. Optional validation:
   cd ${REPO_DIR}
   python3 -m unittest discover -s tests -v

2. Prepare the ready-made review job:
   cd ${REPO_DIR}
   bash tools/prepare_req_consistency_001.sh

3. Print the default review-only prompt and paste it into GigaCode:
   cd ${REPO_DIR}
   bash tools/show_req_consistency_001_prompt.sh

4. If you explicitly want GigaCode to edit and later publish, use instead:
   cd ${REPO_DIR}
   bash tools/show_req_consistency_001_fix_prompt.sh

5. Open the generated job overview manually if needed:
   cd ${REPO_DIR}
   sed -n '1,220p' work/review-jobs/req-consistency-001/job.json
   sed -n '1,220p' work/review-jobs/req-consistency-001/overview.md

6. If the fix-mode job is approved later and actually has merged outputs, publish with:
   cd ${REPO_DIR}
   bash tools/publish_req_consistency_001.sh

7. After each future git pull, run again:
   cd ${REPO_DIR}
   bash tools/setup_other_machine_after_pull.sh

Reference docs:
  ${TARGET_DOC_DIR}/direct-api-v2.md
  ${TARGET_DOC_DIR}/file-first-v3.md
  ${TARGET_DOC_DIR}/stage1-macos-setup.md
  ${TARGET_DOC_DIR}/stage2-runbook.md
  ${TARGET_PROMPT_DIR}/review-only-two-pages.md
  ${TARGET_PROMPT_DIR}/review-only-existing-job.md
  ${TARGET_PROMPT_DIR}/review-and-fix-existing-job.md
  ${TARGET_PROMPT_DIR}/review-and-fix-existing-job-file-first.md
EOF
