#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

python3 scripts/bootstrap_direct_review_job.py \
  --job-id req-consistency-001 \
  --page-id 18028730639 \
  --page-id 18048816272 \
  --settings "${HOME}/.gigacode/settings.json" \
  --task-text "Проверить страницы на консистентность терминологии, требований и описаний процессов. Ничего не публиковать." \
  --log-file "work/review-jobs/req-consistency-001/bootstrap.log"
