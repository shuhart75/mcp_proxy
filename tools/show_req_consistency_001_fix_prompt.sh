#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"
bash "${REPO_DIR}/tools/show_review_job_prompt.sh" --job-id req-consistency-001 --mode review-and-fix
