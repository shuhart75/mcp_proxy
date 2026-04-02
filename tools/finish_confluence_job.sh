#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash tools/finish_confluence_job.sh --job-id JOB_ID [--config /path/to/confluence-rest.config.json] [--no-publish]
EOF
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JOB_ID=""
CONFIG_PATH="${HOME}/.gigacode/confluence-orchestrator/confluence-rest.config.json"
DO_PUBLISH="1"

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
    --no-publish)
      DO_PUBLISH="0"
      shift
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

if [[ -z "${JOB_ID}" ]]; then
  echo "--job-id is required" >&2
  exit 1
fi

cd "${REPO_DIR}"
export PYTHONPATH="${REPO_DIR}/src:${REPO_DIR}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

JOB_DIR="${REPO_DIR}/work/review-jobs/${JOB_ID}"

python3 - <<'PY' "${JOB_DIR}"
import json
import shutil
import sys
from pathlib import Path

repo_dir = Path.cwd()
sys.path.insert(0, str(repo_dir / "scripts"))

from lib_review_job import load_private_job_state, validate_job_outputs
from publish_review_job import _materialize_merged_outputs

job_dir = Path(sys.argv[1])
payload = load_private_job_state(job_dir)
validation = validate_job_outputs(job_dir, payload)
if not validation["ok"]:
    raise SystemExit("Strict review job validation failed:\n- " + "\n- ".join(validation["errors"]))
payload = _materialize_merged_outputs(job_dir, payload)

updated_root = job_dir / "artifacts" / "updated-pages"
new_root = job_dir / "artifacts" / "new-pages"
updated_root.mkdir(parents=True, exist_ok=True)
new_root.mkdir(parents=True, exist_ok=True)

for page in payload.get("pages", []):
    workspace_dir = Path(page["workspace_dir"])
    page_path = Path(page["page_path"])
    merged_path = workspace_dir / "merged.md"
    diff_path = workspace_dir / "merged.diff"
    if not merged_path.exists() or not page_path.exists():
        continue
    if merged_path.read_text(encoding="utf-8") == page_path.read_text(encoding="utf-8"):
        continue
    target_dir = updated_root / str(page["page_id"])
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(merged_path, target_dir / "merged.md")
    if diff_path.exists():
        shutil.copy2(diff_path, target_dir / "merged.diff")
    meta_path = workspace_dir / "page.meta.json"
    if meta_path.exists():
        shutil.copy2(meta_path, target_dir / "page.meta.json")

new_pages_root = job_dir / "new-pages"
if new_pages_root.exists():
    for page_dir in sorted(new_pages_root.iterdir()):
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        target_dir = new_root / page_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in ("page.md", "page.meta.json"):
            src = page_dir / name
            if src.exists():
                shutil.copy2(src, target_dir / name)
PY

python3 - <<'PY' "${JOB_DIR}"
import json
import sys
from pathlib import Path

repo_dir = Path.cwd()
sys.path.insert(0, str(repo_dir / "scripts"))

from lib_review_job import load_private_job_state

job_dir = Path(sys.argv[1])
payload = load_private_job_state(job_dir)
print(json.dumps({"status": payload.get("status"), "job_metadata": payload.get("job_metadata", {})}, ensure_ascii=False))
PY

if [[ "${DO_PUBLISH}" == "1" ]]; then
  JOB_STATUS="$(python3 - <<'PY' "${JOB_DIR}"
import sys
from pathlib import Path

repo_dir = Path.cwd()
sys.path.insert(0, str(repo_dir / "scripts"))

from lib_review_job import load_private_job_state

payload = load_private_job_state(Path(sys.argv[1]))
print(payload.get("status", ""))
PY
)"
  if [[ "${JOB_STATUS}" == "approved" || "${JOB_STATUS}" == "published" ]]; then
    bash "${REPO_DIR}/tools/publish_review_job_with_debug.sh" --job-id "${JOB_ID}" --config "${CONFIG_PATH}" || true
    python3 scripts/publish_new_pages.py --job-dir "work/review-jobs/${JOB_ID}" --config "${CONFIG_PATH}" || true
  else
    echo "Job status is ${JOB_STATUS}; skipping publish."
  fi
fi

bash "${REPO_DIR}/tools/summarize_review_job.sh" --job-id "${JOB_ID}"
echo
echo "Publish bundle:"
echo "  ${JOB_DIR}/artifacts/updated-pages"
echo "  ${JOB_DIR}/artifacts/new-pages"
echo
echo "If something looks wrong, collect diagnostics with:"
echo "  cd ${REPO_DIR}"
echo "  bash tools/collect_review_job_debug.sh ${JOB_ID}"
