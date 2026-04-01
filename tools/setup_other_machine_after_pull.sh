#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DOC_DIR="${HOME}/.gigacode/confluence-orchestrator"
TARGET_CONFIG_DIR="${HOME}/.gigacode/confluence-orchestrator"
TARGET_CONFIG_PATH="${TARGET_CONFIG_DIR}/confluence-rest.config.json"
TARGET_CONFIG_SAMPLE_PATH="${TARGET_CONFIG_DIR}/confluence-rest.config.example.json"

cd "${REPO_DIR}"

mkdir -p "${TARGET_DOC_DIR}"
mkdir -p "${TARGET_CONFIG_DIR}"

bash "${REPO_DIR}/tools/setup_stage1_extension.sh"

cp "${REPO_DIR}/docs/direct-api-v2.md" "${TARGET_DOC_DIR}/direct-api-v2.md"
cp "${REPO_DIR}/examples/confluence-rest.config.example.json" "${TARGET_CONFIG_SAMPLE_PATH}"

if [ ! -f "${TARGET_CONFIG_PATH}" ]; then
  cp "${REPO_DIR}/examples/confluence-rest.config.example.json" "${TARGET_CONFIG_PATH}"
fi

cat <<EOF
Other-machine setup completed.

Prepared files:
  ${TARGET_DOC_DIR}/direct-api-v2.md
  ${TARGET_CONFIG_SAMPLE_PATH}
  ${TARGET_CONFIG_PATH}

What to do next on this machine:

1. Edit direct API config and fill real values:
   ${TARGET_CONFIG_PATH}

2. Optional validation:
   cd ${REPO_DIR}
   python3 -m unittest discover -s tests -v

3. First real bootstrap command:
   cd ${REPO_DIR}
   python3 scripts/bootstrap_direct_review_job.py \\
     --job-id req-consistency-001 \\
     --page-id PAGE_ID_1 \\
     --page-id PAGE_ID_2 \\
     --config ${TARGET_CONFIG_PATH} \\
     --task-text "Проверить страницы на консистентность терминологии, требований и описаний процессов."

4. Open the generated job overview first:
   cd ${REPO_DIR}
   sed -n '1,220p' work/review-jobs/req-consistency-001/job.json
   sed -n '1,220p' work/review-jobs/req-consistency-001/overview.md

5. If the job is approved later, publish with:
   cd ${REPO_DIR}
   python3 scripts/publish_review_job.py \\
     --job-dir work/review-jobs/req-consistency-001 \\
     --config ${TARGET_CONFIG_PATH}

Reference docs:
  ${TARGET_DOC_DIR}/direct-api-v2.md
  ${TARGET_DOC_DIR}/stage1-macos-setup.md
  ${TARGET_DOC_DIR}/stage2-runbook.md
EOF
