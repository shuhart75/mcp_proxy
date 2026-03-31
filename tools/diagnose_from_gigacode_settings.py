#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any


DEFAULT_SETTINGS_CANDIDATES = [
    Path.home() / "Downloads" / "settings.json",
    Path.home() / ".gigacode" / "settings.json",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_settings_file(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"settings file not found: {path}")
        return path
    for candidate in DEFAULT_SETTINGS_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not find settings.json in default locations")


def path_info(path_text: str | None) -> dict[str, Any]:
    if not path_text:
        return {"path": None, "exists": False}
    path = Path(path_text).expanduser()
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file() if path.exists() else False,
        "is_executable": os.access(path, os.X_OK) if path.exists() else False,
    }


def which_info(name: str) -> dict[str, Any]:
    return {"name": name, "path": shutil.which(name)}


def run_python_probe(python_path: str) -> dict[str, Any]:
    code = r"""
import importlib
import json
import platform
import sys

mods = ["mcp", "mcp.server", "mcp.server.fastmcp", "fastmcp"]
result = {
    "python_executable": sys.executable,
    "python_version": sys.version,
    "platform": platform.platform(),
    "modules": [],
}
for name in mods:
    item = {"module": name}
    try:
        module = importlib.import_module(name)
        item["ok"] = True
        item["file"] = getattr(module, "__file__", None)
    except Exception as exc:
        item["ok"] = False
        item["error"] = f"{type(exc).__name__}: {exc}"
    result["modules"].append(item)
print(json.dumps(result, ensure_ascii=False))
"""
    try:
        completed = subprocess.run(
            [python_path, "-c", code],
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def parse_proxy_config_from_args(args: list[str]) -> Path | None:
    for index, arg in enumerate(args):
        if arg == "--config" and index + 1 < len(args):
            return Path(args[index + 1]).expanduser()
    return None


def main(argv: list[str]) -> int:
    explicit_settings = argv[0] if argv else None
    settings_path = find_settings_file(explicit_settings)
    settings = load_json(settings_path)

    servers = settings.get("mcpServers", {})
    server = servers.get("ConfluenceSections")
    if not isinstance(server, dict):
        available = sorted(str(key) for key in servers.keys())
        raise SystemExit(f"ConfluenceSections server not found in settings.json. Available mcpServers: {available}")

    command = server.get("command")
    args = server.get("args", [])
    if not isinstance(args, list):
        raise SystemExit("ConfluenceSections.args must be a list")

    proxy_config_path = parse_proxy_config_from_args([str(item) for item in args])
    proxy_config: dict[str, Any] | None = None
    if proxy_config_path and proxy_config_path.exists():
        proxy_config = load_json(proxy_config_path)

    payload: dict[str, Any] = {
        "platform": platform.platform(),
        "settings_path": str(settings_path),
        "confluence_sections": {
            "command": path_info(command),
            "args": [str(item) for item in args],
            "arg_paths": [path_info(str(item)) for item in args if str(item).startswith("/")],
            "timeout": server.get("timeout"),
            "trust": server.get("trust"),
        },
        "which": [
            which_info("python3"),
            which_info("python"),
            which_info("zsh"),
            which_info("bash"),
        ],
        "env": {
            "SHELL": os.getenv("SHELL"),
            "PATH": os.getenv("PATH"),
            "VIRTUAL_ENV": os.getenv("VIRTUAL_ENV"),
            "PYTHONPATH": os.getenv("PYTHONPATH"),
        },
    }

    if isinstance(command, str):
        payload["command_python_probe"] = run_python_probe(command)

    if proxy_config_path:
        payload["proxy_config_path"] = str(proxy_config_path)
        payload["proxy_config_exists"] = proxy_config_path.exists()

    if proxy_config is not None:
        upstream = proxy_config.get("upstream_mcp", {})
        payload["proxy_config"] = {
            "mode": proxy_config.get("mode"),
            "upstream_command": path_info(upstream.get("command")),
            "upstream_args": upstream.get("args"),
            "upstream_arg_paths": [path_info(str(item)) for item in upstream.get("args", []) if str(item).startswith("/")],
            "get_page_tool": upstream.get("get_page_tool"),
            "update_page_tool": upstream.get("update_page_tool"),
            "page_id_arg": upstream.get("page_id_arg"),
            "body_arg": upstream.get("body_arg"),
            "title_arg": upstream.get("title_arg"),
            "env_keys": sorted(list((upstream.get("env") or {}).keys())),
        }
        upstream_command = upstream.get("command")
        if isinstance(upstream_command, str):
            payload["upstream_python_probe"] = run_python_probe(upstream_command)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
