from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class ReviewPageRecord:
    page_id: str
    title: str
    version: int
    body_format: str
    workspace_dir: str
    page_path: str
    manifest_path: str
    overview_path: str
    chunk_count: int
    strategy: str


def build_page_overview(*, manifest_path: Path, output_path: Path, title: str, page_id: str, body_format: str, max_preview_chars: int = 240) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lines = [
        f"# Page Overview: {title}",
        "",
        f"- Page id: `{page_id}`",
        f"- Body format: `{body_format}`",
        f"- Chunking strategy: `{manifest['strategy']}`",
        f"- Chunk count: `{len(manifest['chunks'])}`",
        "",
        "## Chunks",
        "",
    ]
    for chunk in manifest["chunks"]:
        chunk_path = Path(chunk["path"])
        preview = _preview_text(chunk_path.read_text(encoding="utf-8"), max_chars=max_preview_chars)
        lines.extend(
            [
                f"### {chunk['chunk_id']}",
                "",
                f"- Label: {chunk['label']}",
                f"- File: `{chunk['path']}`",
                f"- Preview: {preview}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def initialize_review_job(*, job_dir: Path, task_text: str, pages: list[ReviewPageRecord], max_chars: int) -> dict[str, Any]:
    job_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = job_dir / "reports" / "iteration-001"
    reports_dir.mkdir(parents=True, exist_ok=True)
    task_path = job_dir / "task.md"
    task_path.write_text(task_text, encoding="utf-8")
    overview_path = job_dir / "overview.md"
    overview_path.write_text(_render_job_overview(task_text=task_text, pages=pages), encoding="utf-8")

    payload = {
        "job_id": job_dir.name,
        "job_dir": str(job_dir),
        "task_path": str(task_path),
        "overview_path": str(overview_path),
        "status": "ready_for_review",
        "current_iteration": 1,
        "max_chars": max_chars,
        "pages": [
            {
                "page_id": page.page_id,
                "title": page.title,
                "version": page.version,
                "body_format": page.body_format,
                "workspace_dir": page.workspace_dir,
                "page_path": page.page_path,
                "manifest_path": page.manifest_path,
                "overview_path": page.overview_path,
                "chunk_count": page.chunk_count,
                "strategy": page.strategy,
            }
            for page in pages
        ],
        "history": [],
        "next_report_path": str(reports_dir / "controller-report.md"),
    }
    write_job_state(job_dir, payload)
    return payload


def write_job_state(job_dir: Path, payload: dict[str, Any]) -> Path:
    state_path = job_dir / "job.json"
    state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return state_path


def load_job_state(job_dir: Path) -> dict[str, Any]:
    return json.loads((job_dir / "job.json").read_text(encoding="utf-8"))


def advance_review_loop(*, job_dir: Path, report_path: Path) -> dict[str, Any]:
    payload = load_job_state(job_dir)
    report_text = report_path.read_text(encoding="utf-8")
    decision = _parse_prefixed_value(report_text, "Decision") or "unknown"
    next_action = _parse_prefixed_value(report_text, "Recommended next action")
    current_iteration = int(payload.get("current_iteration", 1))
    history_entry = {
        "iteration": current_iteration,
        "report_path": str(report_path),
        "decision": decision.lower(),
        "recommended_next_action": next_action,
    }
    payload.setdefault("history", []).append(history_entry)

    normalized = decision.strip().lower()
    if normalized in {"approved", "review-only"}:
        payload["status"] = normalized
        payload["next_report_path"] = None
    else:
        payload["status"] = "needs-edits"
        next_iteration = current_iteration + 1
        payload["current_iteration"] = next_iteration
        next_dir = job_dir / "reports" / f"iteration-{next_iteration:03d}"
        next_dir.mkdir(parents=True, exist_ok=True)
        payload["next_report_path"] = str(next_dir / "controller-report.md")

    write_job_state(job_dir, payload)
    loop_status = {
        "job_id": payload["job_id"],
        "status": payload["status"],
        "current_iteration": payload["current_iteration"],
        "decision": normalized,
        "recommended_next_action": next_action,
        "next_report_path": payload["next_report_path"],
    }
    (job_dir / "loop-status.json").write_text(json.dumps(loop_status, ensure_ascii=False, indent=2), encoding="utf-8")
    return loop_status


def collect_publish_candidates(job_dir: Path) -> dict[str, Any]:
    payload = load_job_state(job_dir)
    candidates: list[dict[str, Any]] = []
    for page in payload.get("pages", []):
        workspace_dir = Path(page["workspace_dir"])
        merged_path = workspace_dir / "merged.md"
        page_path = Path(page["page_path"])
        if not merged_path.exists():
            continue
        if merged_path.read_text(encoding="utf-8") == page_path.read_text(encoding="utf-8"):
            continue
        candidates.append(
            {
                "page_id": page["page_id"],
                "title": page["title"],
                "workspace_dir": str(workspace_dir),
                "input_path": str(merged_path),
                "body_format": page["body_format"],
            }
        )
    return {
        "job_id": payload["job_id"],
        "status": payload["status"],
        "publish_candidates": candidates,
    }


def _render_job_overview(*, task_text: str, pages: list[ReviewPageRecord]) -> str:
    lines = [
        "# Review Job Overview",
        "",
        "## Task",
        "",
        task_text.strip(),
        "",
        "## Pages",
        "",
    ]
    for page in pages:
        lines.extend(
            [
                f"### {page.page_id}",
                "",
                f"- Title: {page.title}",
                f"- Body format: `{page.body_format}`",
                f"- Chunk count: `{page.chunk_count}`",
                f"- Strategy: `{page.strategy}`",
                f"- Page overview: `{page.overview_path}`",
                "",
            ]
        )
    return "\n".join(lines)


def _preview_text(text: str, *, max_chars: int) -> str:
    compact = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    compact = re.sub(r"(?is)<[^>]+>", " ", compact)
    compact = re.sub(r"(?m)^#{1,6}\s+", "", compact)
    compact = re.sub(r"\s+", " ", compact).strip()
    compact = re.sub(r"\s+([,.;:!?])", r"\1", compact)
    if len(compact) <= max_chars:
        return compact or "(empty)"
    return compact[: max_chars - 1].rstrip() + "…"


def _parse_prefixed_value(text: str, prefix: str) -> str | None:
    needle = prefix.lower() + ":"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.lower().startswith(needle):
            return line.split(":", 1)[1].strip()
    return None
