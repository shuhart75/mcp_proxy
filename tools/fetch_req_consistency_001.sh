#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

python3 scripts/fetch_confluence_pages.py \
  --config "${HOME}/.gigacode/confluence-orchestrator/confluence-rest.config.json" \
  --page-id 18028730639 \
  --page-id 18048816272 \
  --output-root "work/fetched-pages/req-consistency-001"
