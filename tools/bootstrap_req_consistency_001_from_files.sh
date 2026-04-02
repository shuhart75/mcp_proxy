#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

python3 scripts/bootstrap_review_job_from_file_root.py \
  --job-id req-consistency-001 \
  --page-id 18028730639 \
  --page-id 18048816272 \
  --input-root "work/fetched-pages/req-consistency-001" \
  --task-text "Проверить страницы на консистентность терминологии, требований и описаний процессов. Ничего не публиковать."
