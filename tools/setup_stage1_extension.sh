#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_EXT_DIR="${HOME}/.gigacode/extensions/confluence-orchestrator"
TARGET_DOC_DIR="${HOME}/.gigacode/confluence-orchestrator"

mkdir -p "${HOME}/.gigacode/extensions"
mkdir -p "${TARGET_DOC_DIR}"

if [ "${REPO_DIR}" != "${TARGET_EXT_DIR}" ]; then
  rm -rf "${TARGET_EXT_DIR}"
  ln -s "${REPO_DIR}" "${TARGET_EXT_DIR}"
fi

cp "${REPO_DIR}/docs/stage1-macos-setup.md" "${TARGET_DOC_DIR}/stage1-macos-setup.md"
cp "${REPO_DIR}/docs/stage2-runbook.md" "${TARGET_DOC_DIR}/stage2-runbook.md"
cp "${REPO_DIR}/examples/stage1-atlassian-settings.sample.json" "${TARGET_DOC_DIR}/stage1-atlassian-settings.sample.json"

cat <<EOF
Stage 1 extension assets prepared.

Extension path:
  ${TARGET_EXT_DIR}

Copied reference files:
  ${TARGET_DOC_DIR}/stage1-macos-setup.md
  ${TARGET_DOC_DIR}/stage2-runbook.md
  ${TARGET_DOC_DIR}/stage1-atlassian-settings.sample.json

Next:
1. Read ${TARGET_DOC_DIR}/stage1-macos-setup.md
2. Update ~/.gigacode/settings.json using the sample
3. Restart GigaCode
4. Validate stage 1, then continue with ${TARGET_DOC_DIR}/stage2-runbook.md
5. In GigaCode, invoke:
   skill: using-confluence-orchestrator
   or
   /large-confluence-edit
EOF
