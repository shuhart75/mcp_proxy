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
  ${REPO_DIR}/tools/prepare_review_job.sh
  ${REPO_DIR}/tools/show_review_job_prompt.sh
  ${REPO_DIR}/tools/publish_review_job.sh
  ${REPO_DIR}/tools/publish_review_job_with_debug.sh
  ${REPO_DIR}/tools/summarize_review_job.sh
  ${REPO_DIR}/tools/fetch_req_consistency_001.sh
  ${REPO_DIR}/tools/bootstrap_req_consistency_001_from_files.sh
  ${REPO_DIR}/tools/prepare_req_consistency_001.sh
  ${REPO_DIR}/tools/publish_req_consistency_001.sh
  ${REPO_DIR}/tools/publish_req_consistency_001_with_debug.sh
  ${REPO_DIR}/tools/summarize_req_consistency_001.sh
  ${REPO_DIR}/tools/show_req_consistency_001_prompt.sh
  ${REPO_DIR}/tools/show_req_consistency_001_fix_prompt.sh
  ${REPO_DIR}/tools/collect_review_job_debug.sh

What to do next on this machine:

1. Optional validation:
   cd ${REPO_DIR}
   python3 -m unittest discover -s tests -v

2. Generic flow for any new review job:
   cd ${REPO_DIR}
   bash tools/prepare_review_job.sh \
     --job-id my-review-001 \
     --page-id 12345 \
     --page-id 67890 \
     --task-text "Проверить страницы на консистентность терминологии и требований. Ничего не публиковать."

3. Print a generic prompt:
   cd ${REPO_DIR}
   bash tools/show_review_job_prompt.sh --job-id my-review-001 --mode review-only

4. If you want GigaCode to edit and later publish:
   cd ${REPO_DIR}
   bash tools/show_review_job_prompt.sh --job-id my-review-001 --mode review-and-fix

5. Publish an approved generic job:
   cd ${REPO_DIR}
   bash tools/publish_review_job.sh --job-id my-review-001

6. Or publish with automatic debug collection:
   cd ${REPO_DIR}
   bash tools/publish_review_job_with_debug.sh --job-id my-review-001

7. Print a short summary for any generic job:
   cd ${REPO_DIR}
   bash tools/summarize_review_job.sh --job-id my-review-001

8. Ready-made demo flow for req-consistency-001:
   cd ${REPO_DIR}
   bash tools/prepare_req_consistency_001.sh

9. Print the default review-only demo prompt and paste it into GigaCode:
   cd ${REPO_DIR}
   bash tools/show_req_consistency_001_prompt.sh

10. If you explicitly want GigaCode to edit and later publish in the demo flow, use instead:
   cd ${REPO_DIR}
   bash tools/show_req_consistency_001_fix_prompt.sh

11. Open the generated demo job overview manually if needed:
   cd ${REPO_DIR}
   sed -n '1,220p' work/review-jobs/req-consistency-001/job.json
   sed -n '1,220p' work/review-jobs/req-consistency-001/overview.md

12. If the demo fix-mode job is approved later and actually has merged outputs, publish with:
   cd ${REPO_DIR}
   bash tools/publish_req_consistency_001.sh

13. Or publish the demo flow with automatic debug collection on failure:
   cd ${REPO_DIR}
   bash tools/publish_req_consistency_001_with_debug.sh

14. Print a short demo job summary any time:
   cd ${REPO_DIR}
   bash tools/summarize_req_consistency_001.sh

15. If something looks wrong, collect diagnostics into one file with:
   cd ${REPO_DIR}
   bash tools/collect_review_job_debug.sh req-consistency-001

16. After each future git pull, run again:
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
