#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

python3 "${REPO_DIR}/tools/diagnose_mcp_runtime.py" \
  "/Users/21356108/.gigacode/extensions/mcp_proxy/confluence-section-mcp" \
  "/Users/21356108/Library/Application Support/iTerm2/iterm2env-3.10.4/versions/3.10.4/bin/mcp-atlassian"
