from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import difflib
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

from .adapters import build_adapter
from .config import load_app_config
from .sectioning import apply_section_replacements, build_layout


@dataclass(frozen=True)
class WorkItem:
    section_id: str
    label: str
    input_file: str
    output_file: str
    instruction_file: str
    command: str


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run parallel section editors and merge the result.")
    parser.add_argument("page_id", help="Confluence page id or local page id in file mode")
    parser.add_argument("--config", help="Path to JSON config file. If omitted, built-in search paths and env are used.")
    parser.add_argument("--editor-command", required=True, help="Shell command template. Supports {input_file}, {output_file}, {instruction_file}, {section_id}, {label}.")
    parser.add_argument("--instructions", help="Inline instructions for each section editor")
    parser.add_argument("--instructions-file", help="Read editor instructions from this file")
    parser.add_argument("--strategy", default="markers", help="markers or headings")
    parser.add_argument("--max-chars", type=int, default=6000)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--workspace", default=".confluence-section-jobs")
    parser.add_argument("--section-id", action="append", dest="section_ids", default=[])
    parser.add_argument("--write-back", action="store_true", help="Push merged content back to Confluence")
    parser.add_argument("--dry-run", action="store_true", help="Do not push even if --write-back is set")
    parser.add_argument("--version-message", default="Section-level automated update")
    return parser.parse_args(argv)


def _load_instructions(args: argparse.Namespace) -> str:
    if args.instructions_file:
        return Path(args.instructions_file).read_text(encoding="utf-8")
    if args.instructions:
        return args.instructions
    raise ValueError("Provide --instructions or --instructions-file")


def _render_command(template: str, item: WorkItem) -> str:
    safe = {
        "input_file": shlex.quote(item.input_file),
        "output_file": shlex.quote(item.output_file),
        "instruction_file": shlex.quote(item.instruction_file),
        "section_id": shlex.quote(item.section_id),
        "label": shlex.quote(item.label),
    }
    rendered = template
    for key, value in safe.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered


def _run_item(item: WorkItem) -> dict[str, Any]:
    completed = subprocess.run(
        item.command,
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    output_path = Path(item.output_file)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed for {item.section_id} with code {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    if not output_path.exists():
        raise RuntimeError(f"Editor command did not create output file for {item.section_id}: {output_path}")
    return {
        "section_id": item.section_id,
        "content": output_path.read_text(encoding="utf-8"),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    instructions = _load_instructions(args)
    config = load_app_config(args.config)
    adapter = build_adapter(config)
    snapshot = adapter.get_page(args.page_id)
    layout = build_layout(snapshot.body, strategy=args.strategy, max_chars=args.max_chars)
    sections = layout.sections
    if args.section_ids:
        allow = set(args.section_ids)
        sections = [section for section in sections if section.id in allow]
    if not sections:
        raise ValueError("No sections selected for editing")

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    workspace = Path(args.workspace) / f"{args.page_id}-{timestamp}"
    workspace.mkdir(parents=True, exist_ok=True)
    replacements: dict[str, str] = {}
    manifest: list[dict[str, Any]] = []

    items: list[WorkItem] = []
    for section in sections:
        section_dir = workspace / section.id
        section_dir.mkdir(parents=True, exist_ok=True)
        input_file = section_dir / "input.md"
        output_file = section_dir / "output.md"
        instruction_file = section_dir / "instructions.txt"
        input_file.write_text(section.content(snapshot.body), encoding="utf-8")
        instruction_file.write_text(instructions, encoding="utf-8")
        item = WorkItem(
            section_id=section.id,
            label=section.label,
            input_file=str(input_file),
            output_file=str(output_file),
            instruction_file=str(instruction_file),
            command="",
        )
        item = WorkItem(**{**asdict(item), "command": _render_command(args.editor_command, item)})
        items.append(item)
        manifest.append(asdict(item))

    (workspace / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = {executor.submit(_run_item, item): item for item in items}
        for future in as_completed(futures):
            results.append(future.result())

    for result in results:
        replacements[result["section_id"]] = result["content"]

    merged = apply_section_replacements(layout, replacements)
    merged_path = workspace / "merged.md"
    merged_path.write_text(merged, encoding="utf-8")

    diff = "".join(
        difflib.unified_diff(
            snapshot.body.splitlines(keepends=True),
            merged.splitlines(keepends=True),
            fromfile=f"{args.page_id}-before",
            tofile=f"{args.page_id}-after",
        )
    )
    (workspace / "merged.diff").write_text(diff, encoding="utf-8")

    updated_version = None
    if args.write_back and not args.dry_run:
        updated = adapter.update_page(
            page_id=snapshot.page_id,
            title=snapshot.title,
            body=merged,
            version=snapshot.version,
            version_message=args.version_message,
            space_id=snapshot.space_id,
        )
        updated_version = updated.version

    summary = {
        "workspace": str(workspace),
        "page_id": snapshot.page_id,
        "title": snapshot.title,
        "strategy": layout.strategy,
        "selected_sections": [section.id for section in sections],
        "updated_version": updated_version,
        "write_back": bool(args.write_back and not args.dry_run),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
