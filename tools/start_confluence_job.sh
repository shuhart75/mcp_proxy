#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/start_confluence_job.sh \
    --job-id JOB_ID \
    --mode analyze|update|create|mixed \
    (--task-text "..." | --task-file /path/to/task.md) \
    [--source REF_OR_URL]... \
    [--default-parent REF_OR_URL] \
    [--config /path/to/confluence-rest.config.json] \
    [--max-chars 12000]

Notes:
  --source accepts either a Confluence page id or a page URL.
  --default-parent is required for create or mixed scenarios when new pages may be created.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID=""
MODE=""
TASK_TEXT=""
TASK_FILE=""
CONFIG_PATH="${HOME}/.gigacode/confluence-orchestrator/confluence-rest.config.json"
MAX_CHARS="12000"
SOURCE_REFS=()
DEFAULT_PARENT_REF=""
INTERACTIVE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-id)
      JOB_ID="$2"
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
    --source)
      SOURCE_REFS+=("$2")
      shift 2
      ;;
    --default-parent)
      DEFAULT_PARENT_REF="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --max-chars)
      MAX_CHARS="$2"
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

if [[ $# -eq 0 && -z "${JOB_ID}" && -z "${MODE}" && -z "${TASK_TEXT}" && -z "${TASK_FILE}" && ${#SOURCE_REFS[@]} -eq 0 ]]; then
  INTERACTIVE="1"
fi

if [[ "${INTERACTIVE}" == "1" ]]; then
  DEFAULT_JOB_ID="job-$(date +%Y%m%d-%H%M%S)"
  printf "Job id [%s]: " "${DEFAULT_JOB_ID}"
  read -r JOB_ID_INPUT
  JOB_ID="${JOB_ID_INPUT:-${DEFAULT_JOB_ID}}"

  echo "Mode options: analyze, update, create, mixed"
  printf "Mode [mixed]: "
  read -r MODE_INPUT
  MODE="${MODE_INPUT:-mixed}"

  echo "Paste task text. Finish with an empty line:"
  TASK_LINES=()
  while IFS= read -r line; do
    [[ -z "${line}" ]] && break
    TASK_LINES+=("${line}")
  done
  TASK_TEXT="$(printf '%s\n' "${TASK_LINES[@]}")"

  if [[ "${MODE}" == "analyze" || "${MODE}" == "update" || "${MODE}" == "mixed" ]]; then
    echo "Paste source page links or page ids, one per line. Finish with an empty line:"
    while IFS= read -r line; do
      [[ -z "${line}" ]] && break
      SOURCE_REFS+=("${line}")
    done
  fi

  if [[ "${MODE}" == "create" || "${MODE}" == "mixed" ]]; then
    printf "Default parent page link or id: "
    read -r DEFAULT_PARENT_REF
  fi
fi

if [[ -z "${JOB_ID}" || -z "${MODE}" ]]; then
  echo "--job-id and --mode are required" >&2
  exit 1
fi
case "${MODE}" in
  analyze|update|create|mixed) ;;
  *)
    echo "--mode must be one of: analyze, update, create, mixed" >&2
    exit 1
    ;;
esac
if [[ -z "${TASK_TEXT}" && -z "${TASK_FILE}" ]]; then
  echo "Provide --task-text or --task-file" >&2
  exit 1
fi
if [[ -n "${TASK_TEXT}" && -n "${TASK_FILE}" ]]; then
  echo "Use either --task-text or --task-file, not both" >&2
  exit 1
fi
if [[ ("${MODE}" == "create" || "${MODE}" == "mixed") && -z "${DEFAULT_PARENT_REF}" ]]; then
  echo "--default-parent is required for create and mixed modes" >&2
  exit 1
fi

cd "${REPO_DIR}"
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

JOB_DIR="${REPO_DIR}/work/review-jobs/${JOB_ID}"
INTERNAL_JOB_DIR="${REPO_DIR}/work/review-jobs-internal/${JOB_ID}"
FETCH_ROOT="${REPO_DIR}/work/fetched-pages/${JOB_ID}"
TASK_PATH="${JOB_DIR}/task.md"
PROMPT_PATH="${JOB_DIR}/gigacode-prompt.md"

rm -rf "${FETCH_ROOT}" "${JOB_DIR}" "${INTERNAL_JOB_DIR}"
mkdir -p "${JOB_DIR}"

if [[ -n "${TASK_FILE}" ]]; then
  cp "${TASK_FILE}" "${TASK_PATH}"
else
  printf '%s\n' "${TASK_TEXT}" > "${TASK_PATH}"
fi

SOURCE_IDS=()
if [[ ${#SOURCE_REFS[@]} -gt 0 ]]; then
  RESOLVE_CMD=(python3 scripts/resolve_confluence_refs.py)
  for ref in "${SOURCE_REFS[@]}"; do
    RESOLVE_CMD+=(--ref "${ref}")
  done
  RESOLVED_SOURCES="$("${RESOLVE_CMD[@]}")"
  while IFS= read -r item; do
    SOURCE_IDS+=("${item}")
  done < <(printf '%s\n' "${RESOLVED_SOURCES}" | python3 -c 'import json,sys; payload=json.load(sys.stdin); [print(item["page_id"]) for item in payload["refs"]]')
fi

DEFAULT_PARENT_ID=""
if [[ -n "${DEFAULT_PARENT_REF}" ]]; then
  DEFAULT_PARENT_ID="$(python3 scripts/resolve_confluence_refs.py --ref "${DEFAULT_PARENT_REF}" | python3 -c 'import json,sys; payload=json.load(sys.stdin); print(payload["refs"][0]["page_id"])')"
fi

if [[ ${#SOURCE_IDS[@]} -gt 0 ]]; then
  FETCH_CMD=(python3 scripts/fetch_confluence_pages.py --config "${CONFIG_PATH}" --output-root "${FETCH_ROOT}")
  for page_id in "${SOURCE_IDS[@]}"; do
    FETCH_CMD+=(--page-id "${page_id}")
  done
  "${FETCH_CMD[@]}"

  BOOTSTRAP_CMD=(
    python3 scripts/bootstrap_review_job_from_file_root.py
    --job-id "${JOB_ID}"
    --input-root "${FETCH_ROOT}"
    --workspace-root "work/review-jobs"
    --task-file "${TASK_PATH}"
    --max-chars "${MAX_CHARS}"
  )
  for page_id in "${SOURCE_IDS[@]}"; do
    BOOTSTRAP_CMD+=(--page-id "${page_id}")
  done
  "${BOOTSTRAP_CMD[@]}"
else
  python3 scripts/init_review_job.py \
    --job-id "${JOB_ID}" \
    --workspace-root "work/review-jobs" \
    --task-file "${TASK_PATH}" \
    --max-chars "${MAX_CHARS}" \
    --mode "${MODE}"
fi

METADATA_ARGS=("${JOB_DIR}" "${MODE}" "${DEFAULT_PARENT_ID}" "${DEFAULT_PARENT_REF}" "${TASK_PATH}")
for ref in "${SOURCE_REFS[@]}"; do
  METADATA_ARGS+=("${ref}")
done
python3 - <<'PY' "${REPO_DIR}" "${METADATA_ARGS[@]}"
import json
import sys
from pathlib import Path

repo_dir = Path(sys.argv[1])
sys.path.insert(0, str(repo_dir / "scripts"))

from lib_review_job import load_private_job_state, write_job_state

job_dir = Path(sys.argv[2])
mode = sys.argv[3]
default_parent_id = sys.argv[4] or None
default_parent_ref = sys.argv[5] or None
task_path = sys.argv[6]
source_refs = [item for item in sys.argv[7:] if item]

payload = load_private_job_state(job_dir)
metadata = dict(payload.get("job_metadata") or {})
metadata.update(
    {
        "request_mode": mode,
        "source_refs": source_refs,
        "default_parent_id": default_parent_id,
        "default_parent_ref": default_parent_ref,
        "task_path": task_path,
        "allow_existing_page_updates": mode in {"update", "mixed"},
        "allow_new_pages": mode in {"create", "mixed"},
    }
)
payload["job_metadata"] = metadata
(job_dir / "new-pages").mkdir(parents=True, exist_ok=True)
(job_dir / "artifacts" / "updated-pages").mkdir(parents=True, exist_ok=True)
(job_dir / "artifacts" / "new-pages").mkdir(parents=True, exist_ok=True)
(job_dir / "new-pages" / "_template").mkdir(parents=True, exist_ok=True)
(job_dir / "new-pages" / "_template" / "page.md").write_text("<h1>New page title</h1>\n<p>Write content here.</p>\n", encoding="utf-8")
(job_dir / "new-pages" / "_template" / "page.meta.json").write_text(
    json.dumps(
        {
            "title": "New page title",
            "parent_id": default_parent_id or "REQUIRED_PARENT_ID",
            "space_id": "",
            "body_format": "storage",
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
(job_dir / "new-pages" / "README.md").write_text(
    "\n".join(
        [
            "# New Pages",
            "",
            "Create one directory per new page.",
            "Each new page directory must contain:",
            "- `page.md`",
            "- `page.meta.json`",
            "",
            "Required meta fields:",
            "- `title`",
            "- `parent_id`",
            "",
            "Optional meta fields:",
            "- `space_id`",
            "- `body_format`",
            "",
            "Template:",
            "- `_template/page.md`",
            "- `_template/page.meta.json`",
        ]
    ),
    encoding="utf-8",
)
write_job_state(job_dir, payload)
PY

bash "${REPO_DIR}/tools/show_review_job_prompt.sh" --job-id "${JOB_ID}" --mode "${MODE}" > "${PROMPT_PATH}"
if command -v pbcopy >/dev/null 2>&1; then
  pbcopy < "${PROMPT_PATH}" || true
fi

cat <<EOF
Confluence job prepared.

Job id:
  ${JOB_ID}

Job directory:
  ${JOB_DIR}

Prompt file:
  ${PROMPT_PATH}

Next:
  1. Open GigaCode.
  2. Paste the prompt from:
     ${PROMPT_PATH}
  3. If pbcopy is available, the prompt is already in the clipboard.
  4. After GigaCode finishes, run:
     cd ${REPO_DIR}
     bash tools/finish_confluence_job.sh --job-id ${JOB_ID}
EOF
