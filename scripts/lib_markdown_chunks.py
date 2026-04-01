from __future__ import annotations

from dataclasses import dataclass
import difflib
import json
from pathlib import Path
import re
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(?P<title>.+?)\s*$", re.MULTILINE)
HTML_HEADING_RE = re.compile(
    r"(?is)<h(?P<level>[1-6])(?:\s[^>]*)?>(?P<title>.*?)</h(?P=level)>"
)
BEGIN_RE = re.compile(r"<!--\s*BEGIN:(?P<id>[-\w./:]+)\s*-->")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    label: str
    start: int
    end: int


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.strip().lower())
    cleaned = re.sub(r"[-\s]+", "-", cleaned)
    return cleaned.strip("-") or "chunk"


def split_markdown(source: str, max_chars: int = 12000) -> tuple[str, list[Chunk]]:
    marker_chunks = _split_markers(source)
    if marker_chunks:
        return "markers", marker_chunks
    heading_chunks = _split_headings(source, max_chars=max_chars)
    if heading_chunks:
        return "headings", heading_chunks
    html_heading_chunks = _split_html_headings(source, max_chars=max_chars)
    if html_heading_chunks:
        return "html-headings", html_heading_chunks
    return "single", [Chunk(chunk_id="001-full-page", label="Full page", start=0, end=len(source))]


def _split_markers(source: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    cursor = 0
    while True:
        begin = BEGIN_RE.search(source, cursor)
        if not begin:
            return chunks
        chunk_id = begin.group("id")
        end_re = re.compile(rf"<!--\s*END:{re.escape(chunk_id)}\s*-->")
        end = end_re.search(source, begin.end())
        if not end:
            raise ValueError(f"Missing END marker for {chunk_id}")
        chunks.append(Chunk(chunk_id=chunk_id, label=chunk_id, start=begin.start(), end=end.end()))
        cursor = end.end()


def _split_headings(source: str, max_chars: int) -> list[Chunk]:
    matches = list(HEADING_RE.finditer(source))
    if not matches:
        return []
    chunks: list[Chunk] = []
    if matches[0].start() > 0:
        chunks.append(Chunk(chunk_id="000-preface", label="Preface", start=0, end=matches[0].start()))
    for index, match in enumerate(matches, start=1):
        start = match.start()
        end = matches[index].start() if index < len(matches) else len(source)
        title = match.group("title").strip()
        if end - start <= max_chars:
            chunks.append(Chunk(chunk_id=f"{index:03d}-{_slugify(title)}", label=title, start=start, end=end))
            continue
        chunks.extend(_split_large_section(source, start, end, title, index, max_chars))
    return chunks


def _split_large_section(source: str, start: int, end: int, title: str, index: int, max_chars: int) -> list[Chunk]:
    text = source[start:end]
    lines = text.splitlines(keepends=True)
    chunks: list[Chunk] = []
    current_start = start
    current_len = 0
    piece_index = 1
    for line in lines:
        if current_len and current_len + len(line) > max_chars:
            chunks.append(
                Chunk(
                    chunk_id=f"{index:03d}-{_slugify(title)}-{piece_index:02d}",
                    label=f"{title} [{piece_index}]",
                    start=current_start,
                    end=current_start + current_len,
                )
            )
            current_start += current_len
            current_len = 0
            piece_index += 1
        current_len += len(line)
    if current_len:
        chunks.append(
            Chunk(
                chunk_id=f"{index:03d}-{_slugify(title)}-{piece_index:02d}",
                label=f"{title} [{piece_index}]",
                start=current_start,
                end=current_start + current_len,
            )
        )
    return chunks


def _split_html_headings(source: str, max_chars: int) -> list[Chunk]:
    matches = list(HTML_HEADING_RE.finditer(source))
    if not matches:
        return []
    chunks: list[Chunk] = []
    if matches[0].start() > 0:
        chunks.append(Chunk(chunk_id="000-preface", label="Preface", start=0, end=matches[0].start()))
    for index, match in enumerate(matches, start=1):
        start = match.start()
        end = matches[index].start() if index < len(matches) else len(source)
        raw_title = re.sub(r"(?is)<[^>]+>", " ", match.group("title"))
        title = re.sub(r"\s+", " ", raw_title).strip() or f"Section {index}"
        if end - start <= max_chars:
            chunks.append(Chunk(chunk_id=f"{index:03d}-{_slugify(title)}", label=title, start=start, end=end))
            continue
        chunks.extend(_split_large_section(source, start, end, title, index, max_chars))
    return chunks


def write_workspace(source_path: Path, output_dir: Path, source: str, strategy: str, chunks: list[Chunk]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_dir = output_dir / chunk.chunk_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        chunk_text = source[chunk.start:chunk.end]
        (chunk_dir / "source.md").write_text(chunk_text, encoding="utf-8")
        manifest_chunks.append(
            {
                "chunk_id": chunk.chunk_id,
                "label": chunk.label,
                "start": chunk.start,
                "end": chunk.end,
                "path": str(chunk_dir / "source.md"),
                "edited_path": str(chunk_dir / "edited.md"),
            }
        )
    manifest = {
        "source_path": str(source_path),
        "strategy": strategy,
        "chunks": manifest_chunks,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def merge_from_manifest(manifest_path: Path, output_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = Path(manifest["source_path"])
    source = source_path.read_text(encoding="utf-8")
    parts: list[str] = []
    cursor = 0
    used_paths: list[str] = []
    for chunk in manifest["chunks"]:
        start = int(chunk["start"])
        end = int(chunk["end"])
        parts.append(source[cursor:start])
        edited_path = Path(chunk["edited_path"])
        source_chunk_path = Path(chunk["path"])
        selected_path = edited_path if edited_path.exists() else source_chunk_path
        used_paths.append(str(selected_path))
        replacement = selected_path.read_text(encoding="utf-8")
        replacement = _match_trailing_newlines(source[start:end], replacement)
        parts.append(replacement)
        cursor = end
    parts.append(source[cursor:])
    merged = "".join(parts)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged, encoding="utf-8")
    return {
        "manifest_path": str(manifest_path),
        "output_path": str(output_path),
        "chunks": len(manifest["chunks"]),
        "used_paths": used_paths,
    }


def _match_trailing_newlines(original: str, replacement: str) -> str:
    original_newlines = len(original) - len(original.rstrip("\n"))
    replacement_newlines = len(replacement) - len(replacement.rstrip("\n"))
    if replacement_newlines > original_newlines:
        return replacement[: len(replacement) - (replacement_newlines - original_newlines)]
    if replacement_newlines < original_newlines:
        return replacement + ("\n" * (original_newlines - replacement_newlines))
    return replacement


def write_diff(source_text: str, merged_text: str, diff_path: Path, from_name: str = "before", to_name: str = "after") -> Path:
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff = "".join(
        difflib.unified_diff(
            source_text.splitlines(keepends=True),
            merged_text.splitlines(keepends=True),
            fromfile=from_name,
            tofile=to_name,
        )
    )
    diff_path.write_text(diff, encoding="utf-8")
    return diff_path
