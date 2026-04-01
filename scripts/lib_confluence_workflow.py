from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any

from lib_markdown_chunks import split_markdown, write_workspace


@dataclass(frozen=True)
class WorkspaceSummary:
    workspace_dir: str
    page_id: str
    page_path: str
    task_path: str
    manifest_path: str
    strategy: str
    chunk_count: int
    should_chunk: bool


def prepare_workspace(
    *,
    page_id: str,
    page_file: Path,
    workspace_root: Path,
    task_text: str,
    max_chars: int = 12000,
) -> WorkspaceSummary:
    source = page_file.read_text(encoding="utf-8")
    workspace_dir = workspace_root / page_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    page_target = workspace_dir / "page.md"
    backup_target = workspace_dir / "page.original.md"
    task_path = workspace_dir / "task.md"
    shutil.copyfile(page_file, page_target)
    shutil.copyfile(page_file, backup_target)
    task_path.write_text(task_text, encoding="utf-8")

    strategy, chunks = split_markdown(source, max_chars=max_chars)
    chunk_root = workspace_dir / "chunks"
    manifest_path = write_workspace(page_target, chunk_root, source, strategy, chunks)

    summary = WorkspaceSummary(
        workspace_dir=str(workspace_dir),
        page_id=page_id,
        page_path=str(page_target),
        task_path=str(task_path),
        manifest_path=str(manifest_path),
        strategy=strategy,
        chunk_count=len(chunks),
        should_chunk=len(chunks) > 1,
    )
    (workspace_dir / "workspace.json").write_text(
        json.dumps(
            {
                "workspace_dir": summary.workspace_dir,
                "page_id": summary.page_id,
                "page_path": summary.page_path,
                "task_path": summary.task_path,
                "manifest_path": summary.manifest_path,
                "strategy": summary.strategy,
                "chunk_count": summary.chunk_count,
                "should_chunk": summary.should_chunk,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def build_chunk_briefs(*, manifest_path: Path, task_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    task_text = task_path.read_text(encoding="utf-8").strip()
    chunks = manifest["chunks"]
    results: list[dict[str, str]] = []
    for index, chunk in enumerate(chunks):
        chunk_dir = Path(chunk["path"]).parent
        previous_label = chunks[index - 1]["label"] if index > 0 else None
        next_label = chunks[index + 1]["label"] if index + 1 < len(chunks) else None
        brief_path = chunk_dir / "brief.md"
        brief_path.write_text(
            _render_chunk_brief(
                task_text=task_text,
                chunk_id=str(chunk["chunk_id"]),
                label=str(chunk["label"]),
                chunk_path=str(chunk["path"]),
                edited_path=str(chunk["edited_path"]),
                previous_label=previous_label,
                next_label=next_label,
            ),
            encoding="utf-8",
        )
        results.append({"chunk_id": str(chunk["chunk_id"]), "brief_path": str(brief_path)})
    return {
        "manifest_path": str(manifest_path),
        "task_path": str(task_path),
        "chunk_count": len(chunks),
        "briefs": results,
    }


def summarize_controller_report(report_path: Path) -> dict[str, Any]:
    text = report_path.read_text(encoding="utf-8")
    decision = "unknown"
    next_action = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if lower.startswith("decision:"):
            decision = line.split(":", 1)[1].strip().lower()
        if lower.startswith("recommended next action:"):
            next_action = line.split(":", 1)[1].strip()
    approved = decision == "approved"
    summary = {
        "report_path": str(report_path),
        "decision": decision,
        "approved": approved,
        "recommended_next_action": next_action,
        "preview": "\n".join(text.splitlines()[:20]),
    }
    status_path = report_path.with_name("controller-status.json")
    status_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["status_path"] = str(status_path)
    return summary


def _render_chunk_brief(
    *,
    task_text: str,
    chunk_id: str,
    label: str,
    chunk_path: str,
    edited_path: str,
    previous_label: str | None,
    next_label: str | None,
) -> str:
    lines = [
        f"# Chunk Brief: {chunk_id}",
        "",
        "## Global Task",
        "",
        task_text,
        "",
        "## Assigned Chunk",
        "",
        f"- Chunk id: `{chunk_id}`",
        f"- Label: {label}",
        f"- Source file: `{chunk_path}`",
        f"- Output file: `{edited_path}`",
        "",
        "## Neighboring Context",
        "",
        f"- Previous section: {previous_label or 'None'}",
        f"- Next section: {next_label or 'None'}",
        "",
        "## Editing Rules",
        "",
        "- Edit only this chunk.",
        "- Preserve heading structure unless the task explicitly requires a rewrite.",
        "- Keep terminology consistent with the global task and neighboring sections.",
        "- Write the final result to `edited.md` in the same chunk directory.",
        "",
    ]
    return "\n".join(lines)
