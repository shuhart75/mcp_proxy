#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  1. Edit the config block at the top of this file on the target machine.
  2. Run:
     bash tools/run_real_confluence_smoke.sh start
  3. After GigaCode finishes, run:
     bash tools/run_real_confluence_smoke.sh finish

Optional overrides:
  bash tools/run_real_confluence_smoke.sh start --job-id JOB_ID --config /path/to/config.json
  bash tools/run_real_confluence_smoke.sh finish --job-id JOB_ID --config /path/to/config.json

Notes:
  - `start` runs the standard operator bootstrap on the target machine.
  - After `start`, open GigaCode there, paste the generated prompt, and wait for the model to finish.
  - Then run the `finish` subcommand on the same machine.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Edit these values on the target machine once, then use:
#   bash tools/run_real_confluence_smoke.sh start
#   bash tools/run_real_confluence_smoke.sh finish
DEFAULT_JOB_ID="real-smoke-001"
DEFAULT_MODE="mixed"
DEFAULT_CONFIG_PATH="${HOME}/.gigacode/confluence-orchestrator/confluence-rest.config.json"
DEFAULT_SOURCE_REF="REPLACE_WITH_PAGE_ID_OR_URL"
DEFAULT_PARENT_REF="REPLACE_WITH_PARENT_PAGE_ID_OR_URL"
DEFAULT_TASK_TEXT="Update the existing page as needed and create one small child page to verify the mixed flow."
DEFAULT_TASK_FILE=""

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

SUBCOMMAND="$1"
shift

case "${SUBCOMMAND}" in
  start)
    MODE="${DEFAULT_MODE}"
    JOB_ID="${DEFAULT_JOB_ID}"
    CONFIG_PATH="${DEFAULT_CONFIG_PATH}"
    SOURCE_REF="${DEFAULT_SOURCE_REF}"
    DEFAULT_PARENT_REF="${DEFAULT_PARENT_REF}"
    TASK_TEXT="${DEFAULT_TASK_TEXT}"
    TASK_FILE="${DEFAULT_TASK_FILE}"

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --job-id)
          JOB_ID="$2"
          shift 2
          ;;
        --config)
          CONFIG_PATH="$2"
          shift 2
          ;;
        --source)
          SOURCE_REF="$2"
          shift 2
          ;;
        --default-parent)
          DEFAULT_PARENT_REF="$2"
          shift 2
          ;;
        --mode)
          MODE="$2"
          shift 2
          ;;
        --task-text)
          TASK_TEXT="$2"
          shift 2
          ;;
        --task-file)
          TASK_FILE="$2"
          shift 2
          ;;
        --help|-h)
          usage
          exit 0
          ;;
        *)
          echo "Unknown argument: $1" >&2
          usage >&2
          exit 1
          ;;
      esac
    done

    if [[ "${SOURCE_REF}" == "REPLACE_WITH_PAGE_ID_OR_URL" || "${DEFAULT_PARENT_REF}" == "REPLACE_WITH_PARENT_PAGE_ID_OR_URL" ]]; then
      echo "Edit tools/run_real_confluence_smoke.sh and set DEFAULT_SOURCE_REF / DEFAULT_PARENT_REF before running." >&2
      exit 1
    fi
    if [[ -z "${JOB_ID}" || -z "${CONFIG_PATH}" || -z "${SOURCE_REF}" || -z "${DEFAULT_PARENT_REF}" ]]; then
      echo "start requires job/config/source/default-parent values" >&2
      exit 1
    fi
    if [[ -z "${TASK_TEXT}" && -z "${TASK_FILE}" ]]; then
      echo "start requires --task-text or --task-file" >&2
      exit 1
    fi
    if [[ -n "${TASK_TEXT}" && -n "${TASK_FILE}" ]]; then
      echo "Use either --task-text or --task-file, not both" >&2
      exit 1
    fi

    cd "${REPO_DIR}"
    CMD=(
      bash "${REPO_DIR}/tools/start_confluence_job.sh"
      --job-id "${JOB_ID}"
      --mode "${MODE}"
      --config "${CONFIG_PATH}"
      --source "${SOURCE_REF}"
      --default-parent "${DEFAULT_PARENT_REF}"
    )
    if [[ -n "${TASK_FILE}" ]]; then
      CMD+=(--task-file "${TASK_FILE}")
    else
      CMD+=(--task-text "${TASK_TEXT}")
    fi
    "${CMD[@]}"
    echo
    echo "Next on the target machine:"
    echo "  1. Open GigaCode."
    echo "  2. Paste work/review-jobs/${JOB_ID}/gigacode-prompt.md."
    echo "  3. After GigaCode finishes, run:"
    echo "     bash tools/run_real_confluence_smoke.sh finish --job-id ${JOB_ID} --config ${CONFIG_PATH}"
    ;;
  finish)
    JOB_ID="${DEFAULT_JOB_ID}"
    CONFIG_PATH="${DEFAULT_CONFIG_PATH}"
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --job-id)
          JOB_ID="$2"
          shift 2
          ;;
        --config)
          CONFIG_PATH="$2"
          shift 2
          ;;
        --help|-h)
          usage
          exit 0
          ;;
        *)
          echo "Unknown argument: $1" >&2
          usage >&2
          exit 1
          ;;
      esac
    done
    if [[ -z "${JOB_ID}" || -z "${CONFIG_PATH}" ]]; then
      echo "finish requires --job-id and --config" >&2
      exit 1
    fi
    cd "${REPO_DIR}"
    bash "${REPO_DIR}/tools/finish_confluence_job.sh" --job-id "${JOB_ID}" --config "${CONFIG_PATH}"
    ;;
  --help|-h|help)
    usage
    ;;
  *)
    echo "Unknown subcommand: ${SUBCOMMAND}" >&2
    usage >&2
    exit 1
    ;;
esac
