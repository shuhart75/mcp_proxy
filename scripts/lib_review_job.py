from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from lib_markdown_chunks import merge_from_manifest, write_diff


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


FORBIDDEN_VISIBLE_PAGE_FILES = (
    "page.source",
    "page.original.source",
    "incoming-page.source",
)


def private_job_dir(job_dir: Path) -> Path:
    return job_dir.parent.with_name(f"{job_dir.parent.name}-internal") / job_dir.name


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


def initialize_review_job(
    *,
    job_dir: Path,
    task_text: str,
    pages: list[ReviewPageRecord],
    max_chars: int,
    job_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
        "job_metadata": job_metadata or {},
    }
    write_job_state(job_dir, payload)
    return _sanitize_job_state(payload)


def write_job_state(job_dir: Path, payload: dict[str, Any]) -> Path:
    state_path = job_dir / "job.json"
    internal_dir = private_job_dir(job_dir)
    internal_dir.mkdir(parents=True, exist_ok=True)
    internal_state_path = internal_dir / "job.json"
    internal_state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    state_path.write_text(json.dumps(_sanitize_job_state(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return state_path


def load_job_state(job_dir: Path) -> dict[str, Any]:
    return json.loads((job_dir / "job.json").read_text(encoding="utf-8"))


def load_private_job_state(job_dir: Path) -> dict[str, Any]:
    state_path = private_job_dir(job_dir) / "job.json"
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return load_job_state(job_dir)


def advance_review_loop(*, job_dir: Path, report_path: Path) -> dict[str, Any]:
    payload = load_private_job_state(job_dir)
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
    payload = load_private_job_state(job_dir)
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


def materialize_merged_outputs(job_dir: Path, payload: dict[str, object] | None = None) -> dict[str, object]:
    if payload is None or any(isinstance(page, dict) and "page_path" not in page for page in payload.get("pages", [])):
        payload = load_private_job_state(job_dir)
    materialized: list[dict[str, str]] = []
    for page in payload.get("pages", []):
        if not isinstance(page, dict):
            continue
        workspace_dir = Path(str(page["workspace_dir"]))
        manifest_path = Path(str(page["manifest_path"]))
        page_path = Path(str(page["page_path"]))
        if not manifest_path.exists() or not page_path.exists():
            continue
        merged_path = workspace_dir / "merged.md"
        diff_path = workspace_dir / "merged.diff"
        merge_from_manifest(manifest_path, merged_path)
        source_text = page_path.read_text(encoding="utf-8")
        merged_text = merged_path.read_text(encoding="utf-8")
        write_diff(source_text, merged_text, diff_path, from_name=page_path.name, to_name=merged_path.name)
        materialized.append(
            {
                "page_id": str(page["page_id"]),
                "merged_path": str(merged_path),
                "diff_path": str(diff_path),
            }
        )
    if materialized:
        payload["materialized_outputs"] = materialized
        write_job_state(job_dir, payload)
    return payload


def validate_job_outputs(job_dir: Path, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or load_private_job_state(job_dir)
    errors: list[str] = []
    warnings: list[str] = []
    changed_pages: list[str] = []
    incomplete_new_pages: list[str] = []
    complete_new_pages: list[str] = []

    for page in payload.get("pages", []):
        if not isinstance(page, dict):
            continue
        page_id = str(page["page_id"])
        workspace_dir = Path(str(page["workspace_dir"]))
        page_path = Path(str(page["page_path"]))
        backup_path = page_path.with_name("page.original.source")
        manifest_path = Path(str(page["manifest_path"]))
        merged_path = workspace_dir / "merged.md"
        diff_path = workspace_dir / "merged.diff"

        for name in FORBIDDEN_VISIBLE_PAGE_FILES:
            forbidden_path = workspace_dir / name
            if forbidden_path.exists():
                errors.append(f"Visible full-source file is forbidden in strict mode: {forbidden_path}")

        if not page_path.exists():
            errors.append(f"Hidden source page is missing: {page_path}")
            continue
        if backup_path.exists() and page_path.read_text(encoding="utf-8") != backup_path.read_text(encoding="utf-8"):
            errors.append(f"Hidden source page was modified instead of chunk/page outputs: {page_path}")

        changed_chunks = _collect_changed_chunks(manifest_path)
        if changed_chunks and not merged_path.exists():
            warnings.append(f"Changed chunks detected for page {page_id}, but merged.md is missing and will need materialization.")

        if merged_path.exists():
            if merged_path.read_text(encoding="utf-8") != page_path.read_text(encoding="utf-8"):
                changed_pages.append(page_id)
                if not diff_path.exists():
                    warnings.append(f"Changed page {page_id} is missing merged.diff.")

    new_pages_root = job_dir / "new-pages"
    if new_pages_root.exists():
        for page_dir in sorted(new_pages_root.iterdir()):
            if not page_dir.is_dir() or page_dir.name.startswith("_"):
                continue
            meta_path = page_dir / "page.meta.json"
            page_md_path = page_dir / "page.md"
            if meta_path.exists() and page_md_path.exists():
                complete_new_pages.append(page_dir.name)
            else:
                incomplete_new_pages.append(page_dir.name)
                errors.append(f"New page output is incomplete: {page_dir}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "changed_pages": changed_pages,
        "complete_new_pages": complete_new_pages,
        "incomplete_new_pages": incomplete_new_pages,
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


def _sanitize_job_state(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = json.loads(json.dumps(payload, ensure_ascii=False))
    pages = []
    for page in sanitized.get("pages", []):
        if not isinstance(page, dict):
            pages.append(page)
            continue
        item = dict(page)
        item.pop("page_path", None)
        pages.append(item)
    sanitized["pages"] = pages
    return sanitized


def _collect_changed_chunks(manifest_path: Path) -> list[str]:
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    changed: list[str] = []
    for chunk in manifest.get("chunks", []):
        if not isinstance(chunk, dict):
            continue
        source_path = Path(str(chunk["path"]))
        source_text = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        edited_path = Path(str(chunk.get("edited_path", "")))
        if edited_path.exists() and edited_path.read_text(encoding="utf-8") != source_text:
            changed.append(str(chunk.get("chunk_id")))
            continue
        merged_path = source_path.with_name("merged.md")
        if merged_path.exists() and merged_path.read_text(encoding="utf-8") != source_text:
            changed.append(str(chunk.get("chunk_id")))
    return changed


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
    header_with_value = re.search(rf"(?im)^(?:#+\s*)?{re.escape(prefix)}\s*:\s*(.+?)\s*$", text)
    if header_with_value:
        return header_with_value.group(1).strip()
    section_header = re.search(rf"(?im)^(?:#+\s*)?{re.escape(prefix)}\s*$", text)
    if section_header:
        tail = text[section_header.end():]
        for raw_line in tail.splitlines():
            line = raw_line.strip()
            if not line or line == "---":
                continue
            return line
    return None
