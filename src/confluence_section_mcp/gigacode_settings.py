from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .config import AppConfig


DEFAULT_SETTINGS_CANDIDATES = [
    Path.home() / "Downloads" / "settings.json",
    Path.home() / ".gigacode" / "settings.json",
]


def find_settings_file(explicit: str | None = None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"settings file not found: {path}")
        return path
    for candidate in DEFAULT_SETTINGS_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not find settings.json in default locations")


def load_settings(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"settings file must contain a JSON object: {path}")
    return payload


def build_app_config_from_gigacode_settings(settings_path: str | None = None, *, server_name: str = "Atlassian") -> AppConfig:
    path = find_settings_file(settings_path)
    settings = load_settings(path)
    servers = settings.get("mcpServers")
    if not isinstance(servers, dict):
        raise ValueError(f"mcpServers object not found in settings file: {path}")
    server = servers.get(server_name)
    if not isinstance(server, dict):
        available = ", ".join(sorted(str(key) for key in servers.keys()))
        raise ValueError(f"MCP server '{server_name}' not found in settings file. Available: {available}")

    command = _expand_text(server.get("command"))
    if not command:
        raise ValueError(f"mcpServers.{server_name}.command is required")

    raw_args = server.get("args", [])
    if not isinstance(raw_args, list):
        raise ValueError(f"mcpServers.{server_name}.args must be a list")
    args = [_expand_text(item) for item in raw_args]

    raw_env = server.get("env", {})
    if raw_env is None:
        raw_env = {}
    if not isinstance(raw_env, dict):
        raise ValueError(f"mcpServers.{server_name}.env must be an object")
    env_map = {str(key): _stringify_env_value(value) for key, value in raw_env.items()}

    payload = {
        "mode": "mcp",
        "upstream_mcp": {
            "command": command,
            "args": args,
            "env": env_map,
            "get_page_tool": "confluence_get_page",
            "update_page_tool": "confluence_update_page",
            "page_id_arg": "page_id",
            "body_arg": "content",
            "title_arg": "title",
            "get_page_extra_args": {
                "convert_to_markdown": True,
                "include_metadata": True,
            },
            "update_page_extra_args": {
                "content_format": "markdown",
            },
        },
    }
    return AppConfig.from_mapping(payload)


def _expand_text(value: Any) -> str:
    if value is None:
        return ""
    return os.path.expanduser(os.path.expandvars(str(value)))


def _stringify_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
