from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .adapters import AdapterError, PageAdapter, PageSnapshot
from .sectioning import apply_section_replacements, build_layout


@dataclass(frozen=True)
class SectionView:
    page_id: str
    title: str
    version: int
    section_id: str
    label: str
    strategy: str
    content: str


class SectionService:
    def __init__(self, adapter: PageAdapter) -> None:
        self.adapter = adapter

    def get_outline(self, page_id: str, strategy: str = "markers", max_chars: int = 6000) -> dict[str, Any]:
        snapshot = self.adapter.get_page(page_id)
        layout = build_layout(snapshot.body, strategy=strategy, max_chars=max_chars)
        return {
            "page_id": snapshot.page_id,
            "title": snapshot.title,
            "version": snapshot.version,
            "body_format": snapshot.body_format,
            "strategy": layout.strategy,
            "sections": layout.outline(),
        }

    def get_section(self, page_id: str, section_id: str, strategy: str = "markers", max_chars: int = 6000) -> SectionView:
        snapshot = self.adapter.get_page(page_id)
        layout = build_layout(snapshot.body, strategy=strategy, max_chars=max_chars)
        section = layout.require_section(section_id)
        return SectionView(
            page_id=snapshot.page_id,
            title=snapshot.title,
            version=snapshot.version,
            section_id=section.id,
            label=section.label,
            strategy=layout.strategy,
            content=section.content(snapshot.body),
        )

    def apply_sections(
        self,
        page_id: str,
        sections: list[dict[str, str]],
        strategy: str = "markers",
        max_chars: int = 6000,
        dry_run: bool = False,
        version_message: str | None = None,
    ) -> dict[str, Any]:
        snapshot = self.adapter.get_page(page_id)
        layout = build_layout(snapshot.body, strategy=strategy, max_chars=max_chars)
        replacements = {entry["section_id"]: entry["content"] for entry in sections}
        merged = apply_section_replacements(layout, replacements)
        result = {
            "page_id": snapshot.page_id,
            "title": snapshot.title,
            "previous_version": snapshot.version,
            "strategy": layout.strategy,
            "updated_sections": sorted(replacements.keys()),
            "body_preview": merged[:1000],
        }
        if dry_run:
            result["dry_run"] = True
            return result
        updated = self.adapter.update_page(
            page_id=snapshot.page_id,
            title=snapshot.title,
            body=merged,
            version=snapshot.version,
            version_message=version_message,
            space_id=snapshot.space_id,
        )
        result["new_version"] = updated.version
        return result

    def replace_section(
        self,
        page_id: str,
        section_id: str,
        content: str,
        strategy: str = "markers",
        max_chars: int = 6000,
        dry_run: bool = False,
        version_message: str | None = None,
    ) -> dict[str, Any]:
        return self.apply_sections(
            page_id=page_id,
            sections=[{"section_id": section_id, "content": content}],
            strategy=strategy,
            max_chars=max_chars,
            dry_run=dry_run,
            version_message=version_message,
        )


def format_tool_result(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "__dataclass_fields__"):
        serializable = asdict(payload)
    else:
        serializable = payload
    return {
        "content": [
            {
                "type": "text",
                "text": str(serializable) if isinstance(serializable, str) else _json_dump(serializable),
            }
        ]
    }


def _json_dump(payload: Any) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)
