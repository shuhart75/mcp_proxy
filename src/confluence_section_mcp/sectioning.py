from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


BEGIN_RE = re.compile(r"<!--\s*BEGIN:(?P<id>[-\w./:]+)\s*-->")
HEADING_RE = re.compile(r"^(#{1,6})\s+(?P<title>.+?)\s*$", re.MULTILINE)


def _slugify(text: str) -> str:
    lowered = text.strip().lower()
    lowered = re.sub(r"[^\w\s-]", "", lowered)
    lowered = re.sub(r"[-\s]+", "-", lowered)
    return lowered.strip("-") or "section"


@dataclass(frozen=True)
class Section:
    id: str
    label: str
    start: int
    end: int
    content_start: int
    content_end: int

    def content(self, source: str) -> str:
        return source[self.content_start:self.content_end]

    def full_text(self, source: str) -> str:
        return source[self.start:self.end]


@dataclass(frozen=True)
class DocumentLayout:
    source: str
    sections: list[Section]
    strategy: str

    def outline(self) -> list[dict[str, int | str]]:
        return [
            {
                "id": section.id,
                "label": section.label,
                "chars": section.content_end - section.content_start,
                "offset": section.start,
            }
            for section in self.sections
        ]

    def require_section(self, section_id: str) -> Section:
        for section in self.sections:
            if section.id == section_id:
                return section
        raise KeyError(f"Unknown section id: {section_id}")


def build_layout(source: str, strategy: str = "markers", max_chars: int = 6000) -> DocumentLayout:
    normalized = strategy.strip().lower()
    if normalized == "markers":
        sections = split_marked_sections(source)
        if sections:
            return DocumentLayout(source=source, sections=sections, strategy="markers")
        normalized = "headings"
    if normalized == "headings":
        return DocumentLayout(source=source, sections=split_heading_sections(source, max_chars=max_chars), strategy="headings")
    raise ValueError(f"Unsupported strategy: {strategy}")


def split_marked_sections(source: str) -> list[Section]:
    sections: list[Section] = []
    cursor = 0
    while True:
        begin = BEGIN_RE.search(source, cursor)
        if not begin:
            return sections
        section_id = begin.group("id")
        end_marker = re.compile(rf"<!--\s*END:{re.escape(section_id)}\s*-->")
        end = end_marker.search(source, begin.end())
        if not end:
            raise ValueError(f"Missing END marker for section '{section_id}'")
        sections.append(
            Section(
                id=section_id,
                label=section_id,
                start=begin.start(),
                end=end.end(),
                content_start=begin.end(),
                content_end=end.start(),
            )
        )
        cursor = end.end()


def split_heading_sections(source: str, max_chars: int = 6000) -> list[Section]:
    matches = list(HEADING_RE.finditer(source))
    if not matches:
        return _chunk_arbitrary(source, max_chars=max_chars)

    sections: list[Section] = []
    for index, match in enumerate(matches):
        title = match.group("title").strip()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        body = source[start:end]
        if len(body) <= max_chars:
            section_id = f"{index + 1:03d}-{_slugify(title)}"
            sections.append(
                Section(
                    id=section_id,
                    label=title,
                    start=start,
                    end=end,
                    content_start=start,
                    content_end=end,
                )
            )
            continue
        sections.extend(_chunk_large_heading(index=index, title=title, start=start, body=body, max_chars=max_chars))

    if matches[0].start() > 0:
        prefix = source[: matches[0].start()]
        prefix_section = Section(
            id="000-preface",
            label="Preface",
            start=0,
            end=matches[0].start(),
            content_start=0,
            content_end=matches[0].start(),
        )
        sections.insert(0, prefix_section)
    return sections


def _chunk_large_heading(index: int, title: str, start: int, body: str, max_chars: int) -> list[Section]:
    chunks: list[Section] = []
    parts = _split_paragraphs(body, max_chars=max_chars)
    offset = start
    slug = _slugify(title)
    for chunk_index, chunk in enumerate(parts, start=1):
        end = offset + len(chunk)
        chunks.append(
            Section(
                id=f"{index + 1:03d}-{slug}-{chunk_index:02d}",
                label=f"{title} [{chunk_index}]",
                start=offset,
                end=end,
                content_start=offset,
                content_end=end,
            )
        )
        offset = end
    return chunks


def _chunk_arbitrary(source: str, max_chars: int) -> list[Section]:
    parts = _split_paragraphs(source, max_chars=max_chars)
    sections: list[Section] = []
    offset = 0
    for index, part in enumerate(parts, start=1):
        end = offset + len(part)
        sections.append(
            Section(
                id=f"{index:03d}-chunk",
                label=f"Chunk {index}",
                start=offset,
                end=end,
                content_start=offset,
                content_end=end,
            )
        )
        offset = end
    return sections


def _split_paragraphs(source: str, max_chars: int) -> list[str]:
    lines = source.splitlines(keepends=True)
    parts: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        line_len = len(line)
        if current and current_len + line_len > max_chars:
            parts.append("".join(current))
            current = []
            current_len = 0
        if line_len > max_chars:
            if current:
                parts.append("".join(current))
                current = []
                current_len = 0
            for piece in _hard_wrap(line, max_chars=max_chars):
                parts.append(piece)
            continue
        current.append(line)
        current_len += line_len
    if current:
        parts.append("".join(current))
    return parts or [source]


def _hard_wrap(line: str, max_chars: int) -> Iterable[str]:
    start = 0
    while start < len(line):
        yield line[start : start + max_chars]
        start += max_chars


def apply_section_replacements(layout: DocumentLayout, replacements: dict[str, str]) -> str:
    pieces: list[str] = []
    cursor = 0
    for section in layout.sections:
        pieces.append(layout.source[cursor:section.content_start])
        pieces.append(replacements.get(section.id, section.content(layout.source)))
        cursor = section.content_end
    pieces.append(layout.source[cursor:])
    return "".join(pieces)
