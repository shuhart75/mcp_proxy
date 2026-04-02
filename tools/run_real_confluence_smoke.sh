#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/run_real_confluence_smoke.sh start \
    --job-id JOB_ID \
    --config /path/to/confluence-rest.config.json \
    --source PAGE_ID_OR_URL \
    --default-parent PAGE_ID_OR_URL \
    [--mode update|mixed] \
    [--task-text "..."] \
    [--task-file /path/to/task.md]

  bash tools/run_real_confluence_smoke.sh finish \
    --job-id JOB_ID \
    --config /path/to/confluence-rest.config.json

Notes:
  - `start` runs the standard operator bootstrap on the target machine.
  - After `start`, open GigaCode there, paste the generated prompt, and wait for the model to finish.
  - Then run the `finish` subcommand on the same machine.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

SUBCOMMAND="$1"
shift

case "${SUBCOMMAND}" in
  start)
    MODE="mixed"
    JOB_ID=""
    CONFIG_PATH=""
    SOURCE_REF=""
    DEFAULT_PARENT_REF=""
    TASK_TEXT=""
    TASK_FILE=""

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

    if [[ -z "${JOB_ID}" || -z "${CONFIG_PATH}" || -z "${SOURCE_REF}" || -z "${DEFAULT_PARENT_REF}" ]]; then
      echo "start requires --job-id, --config, --source, and --default-parent" >&2
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
    JOB_ID=""
    CONFIG_PATH=""
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
