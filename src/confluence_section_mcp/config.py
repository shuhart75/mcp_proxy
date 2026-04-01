from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
from typing import Any


@dataclass(frozen=True)
class RestConfig:
    base_url: str
    body_format: str
    email: str | None
    api_token: str | None
    bearer_token: str | None
    default_space_id: str | None
    ssl_verify: bool
    ca_bundle: str | None


@dataclass(frozen=True)
class FileConfig:
    root: str


@dataclass(frozen=True)
class UpstreamMcpConfig:
    command: str
    args: list[str]
    env: dict[str, str]
    env_passthrough: list[str]
    call_timeout_ms: int
    get_page_tool: str
    update_page_tool: str
    page_id_arg: str
    body_arg: str
    title_arg: str | None
    get_page_extra_args: dict[str, Any]
    update_page_extra_args: dict[str, Any]


@dataclass(frozen=True)
class AppConfig:
    mode: str
    rest: RestConfig | None
    file: FileConfig | None
    upstream_mcp: UpstreamMcpConfig | None

    @classmethod
    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls.from_mapping({})

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Config file must contain a JSON object: {path}")
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "AppConfig":
        mode = _pick(payload, "mode", env="CONFLUENCE_SECTION_MODE", default="rest").strip().lower()
        if mode == "file":
            root = _pick(payload, "file.root", env="CONFLUENCE_FILE_ROOT", default="").strip()
            if not root:
                raise ValueError("CONFLUENCE_FILE_ROOT is required when CONFLUENCE_SECTION_MODE=file")
            return cls(mode=mode, rest=None, file=FileConfig(root=root), upstream_mcp=None)
        if mode == "mcp":
            command = _pick(payload, "upstream_mcp.command", env="CONFLUENCE_UPSTREAM_COMMAND", default="").strip()
            if not command:
                raise ValueError("CONFLUENCE_UPSTREAM_COMMAND is required when CONFLUENCE_SECTION_MODE=mcp")
            args_value = _pick(payload, "upstream_mcp.args", env="CONFLUENCE_UPSTREAM_ARGS", default=[])
            args = _coerce_args(args_value)
            env_value = _pick(payload, "upstream_mcp.env", default={})
            env_map = _coerce_string_map(env_value)
            passthrough_raw = _pick(payload, "upstream_mcp.env_passthrough", env="CONFLUENCE_UPSTREAM_ENV", default="")
            env_passthrough = [item.strip() for item in passthrough_raw.split(",") if item.strip()]
            return cls(
                mode=mode,
                rest=None,
                file=None,
                upstream_mcp=UpstreamMcpConfig(
                    command=command,
                    args=args,
                    env=env_map,
                    env_passthrough=env_passthrough,
                    call_timeout_ms=int(_pick(payload, "upstream_mcp.call_timeout_ms", default=60000)),
                    get_page_tool=_pick(payload, "upstream_mcp.get_page_tool", env="CONFLUENCE_UPSTREAM_GET_TOOL", default="getConfluencePage").strip() or "getConfluencePage",
                    update_page_tool=_pick(payload, "upstream_mcp.update_page_tool", env="CONFLUENCE_UPSTREAM_UPDATE_TOOL", default="updateConfluencePage").strip() or "updateConfluencePage",
                    page_id_arg=_pick(payload, "upstream_mcp.page_id_arg", env="CONFLUENCE_UPSTREAM_PAGE_ID_ARG", default="pageId").strip() or "pageId",
                    body_arg=_pick(payload, "upstream_mcp.body_arg", env="CONFLUENCE_UPSTREAM_BODY_ARG", default="body").strip() or "body",
                    title_arg=_pick(payload, "upstream_mcp.title_arg", env="CONFLUENCE_UPSTREAM_TITLE_ARG", default="title").strip() or None,
                    get_page_extra_args=_coerce_json_map(_pick(payload, "upstream_mcp.get_page_extra_args", default={})),
                    update_page_extra_args=_coerce_json_map(_pick(payload, "upstream_mcp.update_page_extra_args", default={})),
                ),
            )

        base_url = _pick(payload, "rest.base_url", env="CONFLUENCE_BASE_URL", default="").strip().rstrip("/")
        if not base_url:
            raise ValueError("CONFLUENCE_BASE_URL is required when CONFLUENCE_SECTION_MODE=rest")
        return cls(
            mode="rest",
            rest=RestConfig(
                base_url=base_url,
                body_format=_pick(payload, "rest.body_format", env="CONFLUENCE_BODY_FORMAT", default="storage").strip() or "storage",
                email=_pick(payload, "rest.email", env="CONFLUENCE_EMAIL", default="").strip() or None,
                api_token=_pick(payload, "rest.api_token", env="CONFLUENCE_API_TOKEN", default="").strip() or None,
                bearer_token=_pick(payload, "rest.bearer_token", env="CONFLUENCE_BEARER_TOKEN", default="").strip() or None,
                default_space_id=_pick(payload, "rest.default_space_id", env="CONFLUENCE_SPACE_ID", default="").strip() or None,
                ssl_verify=_coerce_bool(_pick(payload, "rest.ssl_verify", env="CONFLUENCE_SSL_VERIFY", default=True)),
                ca_bundle=_pick(payload, "rest.ca_bundle", env="CONFLUENCE_CA_BUNDLE", default="").strip() or None,
            ),
            file=None,
            upstream_mcp=None,
        )


def load_app_config(config_path: str | None = None) -> AppConfig:
    if config_path:
        return AppConfig.from_file(config_path)

    default_paths = [
        Path.cwd() / "confluence-section-mcp.config.json",
        Path.home() / ".config" / "confluence-section-mcp" / "config.json",
    ]
    for candidate in default_paths:
        if candidate.exists():
            return AppConfig.from_file(str(candidate))
    return AppConfig.from_env()


def _pick(payload: dict[str, Any], dotted_key: str, *, env: str | None = None, default: Any = None) -> Any:
    cursor: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            cursor = None
            break
        cursor = cursor[part]
    if cursor is not None:
        return cursor
    if env:
        value = os.getenv(env)
        if value is not None:
            return value
    return default


def _coerce_args(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return shlex.split(value)
    if value in (None, ""):
        return []
    raise ValueError(f"Unsupported upstream_mcp.args value: {value!r}")


def _coerce_string_map(value: Any) -> dict[str, str]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise ValueError("upstream_mcp.env must be an object")
    return {str(key): str(item) for key, item in value.items()}


def _coerce_json_map(value: Any) -> dict[str, Any]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise ValueError("Expected an object")
    return dict(value)


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, int):
        return bool(value)
    raise ValueError(f"Expected a boolean-compatible value, got: {value!r}")
