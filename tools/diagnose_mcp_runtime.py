#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any


MODULES = [
    "mcp",
    "mcp.server",
    "mcp.server.fastmcp",
    "fastmcp",
]

EXECUTABLES = [
    "python3",
    "python",
    "mcp-atlassian",
    "confluence-section-mcp",
]


def module_info(name: str) -> dict[str, Any]:
    info: dict[str, Any] = {"module": name}
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        info["ok"] = False
        info["error"] = f"{type(exc).__name__}: {exc}"
        return info

    info["ok"] = True
    info["file"] = getattr(module, "__file__", None)
    package_root = name.split(".")[0]
    try:
        info["version"] = importlib.metadata.version(package_root)
    except importlib.metadata.PackageNotFoundError:
        info["version"] = None
    return info


def executable_info(name: str) -> dict[str, Any]:
    return {
        "executable": name,
        "path": shutil.which(name),
    }


def env_info() -> dict[str, Any]:
    keys = [
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PATH",
    ]
    data = {key: os.getenv(key) for key in keys}
    data["cwd"] = os.getcwd()
    data["python_executable"] = sys.executable
    data["python_version"] = sys.version
    return data


def file_info(path_text: str) -> dict[str, Any]:
    path = Path(path_text).expanduser()
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_executable": os.access(path, os.X_OK) if path.exists() else False,
    }


def main(argv: list[str]) -> int:
    payload: dict[str, Any] = {
        "env": env_info(),
        "modules": [module_info(name) for name in MODULES],
        "executables": [executable_info(name) for name in EXECUTABLES],
    }
    if argv:
        payload["paths"] = [file_info(item) for item in argv]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
