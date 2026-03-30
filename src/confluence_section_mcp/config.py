from __future__ import annotations

from dataclasses import dataclass
import os
import shlex


@dataclass(frozen=True)
class RestConfig:
    base_url: str
    body_format: str
    email: str | None
    api_token: str | None
    bearer_token: str | None
    default_space_id: str | None


@dataclass(frozen=True)
class FileConfig:
    root: str


@dataclass(frozen=True)
class UpstreamMcpConfig:
    command: str
    args: list[str]
    env_passthrough: list[str]
    get_page_tool: str
    update_page_tool: str
    page_id_arg: str
    body_arg: str
    title_arg: str | None


@dataclass(frozen=True)
class AppConfig:
    mode: str
    rest: RestConfig | None
    file: FileConfig | None
    upstream_mcp: UpstreamMcpConfig | None

    @classmethod
    def from_env(cls) -> "AppConfig":
        mode = os.getenv("CONFLUENCE_SECTION_MODE", "rest").strip().lower()
        if mode == "file":
            root = os.getenv("CONFLUENCE_FILE_ROOT", "").strip()
            if not root:
                raise ValueError("CONFLUENCE_FILE_ROOT is required when CONFLUENCE_SECTION_MODE=file")
            return cls(mode=mode, rest=None, file=FileConfig(root=root), upstream_mcp=None)
        if mode == "mcp":
            command = os.getenv("CONFLUENCE_UPSTREAM_COMMAND", "").strip()
            if not command:
                raise ValueError("CONFLUENCE_UPSTREAM_COMMAND is required when CONFLUENCE_SECTION_MODE=mcp")
            args = shlex.split(os.getenv("CONFLUENCE_UPSTREAM_ARGS", "").strip())
            passthrough_raw = os.getenv("CONFLUENCE_UPSTREAM_ENV", "").strip()
            env_passthrough = [item.strip() for item in passthrough_raw.split(",") if item.strip()]
            return cls(
                mode=mode,
                rest=None,
                file=None,
                upstream_mcp=UpstreamMcpConfig(
                    command=command,
                    args=args,
                    env_passthrough=env_passthrough,
                    get_page_tool=os.getenv("CONFLUENCE_UPSTREAM_GET_TOOL", "getConfluencePage").strip() or "getConfluencePage",
                    update_page_tool=os.getenv("CONFLUENCE_UPSTREAM_UPDATE_TOOL", "updateConfluencePage").strip() or "updateConfluencePage",
                    page_id_arg=os.getenv("CONFLUENCE_UPSTREAM_PAGE_ID_ARG", "pageId").strip() or "pageId",
                    body_arg=os.getenv("CONFLUENCE_UPSTREAM_BODY_ARG", "body").strip() or "body",
                    title_arg=os.getenv("CONFLUENCE_UPSTREAM_TITLE_ARG", "title").strip() or None,
                ),
            )

        base_url = os.getenv("CONFLUENCE_BASE_URL", "").strip().rstrip("/")
        if not base_url:
            raise ValueError("CONFLUENCE_BASE_URL is required when CONFLUENCE_SECTION_MODE=rest")
        return cls(
            mode="rest",
            rest=RestConfig(
                base_url=base_url,
                body_format=os.getenv("CONFLUENCE_BODY_FORMAT", "storage").strip() or "storage",
                email=os.getenv("CONFLUENCE_EMAIL", "").strip() or None,
                api_token=os.getenv("CONFLUENCE_API_TOKEN", "").strip() or None,
                bearer_token=os.getenv("CONFLUENCE_BEARER_TOKEN", "").strip() or None,
                default_space_id=os.getenv("CONFLUENCE_SPACE_ID", "").strip() or None,
            ),
            file=None,
            upstream_mcp=None,
        )
