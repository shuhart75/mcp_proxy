#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

python3 scripts/publish_review_job.py \
  --job-dir "work/review-jobs/req-consistency-001" \
  --config "${HOME}/.gigacode/confluence-orchestrator/confluence-rest.config.json"
