#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

bash "${REPO_DIR}/tools/prepare_review_job.sh" \
  --job-id req-consistency-001 \
  --page-id 18028730639 \
  --page-id 18048816272 \
  --task-text "Проверить страницы на консистентность терминологии, требований и описаний процессов. Ничего не публиковать."
