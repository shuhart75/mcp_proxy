from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import sys
from typing import Any

from .adapters import AdapterError, build_adapter
from .config import AppConfig, load_app_config
from .service import SectionService, format_tool_result


LOGGER = logging.getLogger("confluence_section_mcp.server")


TOOLS = [
    {
        "name": "confluence_page_outline",
        "description": "Return Confluence page sections using markers first, then heading-based chunking.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "strategy": {"type": "string", "default": "markers"},
                "max_chars": {"type": "integer", "default": 6000},
            },
            "required": ["page_id"],
        },
    },
    {
        "name": "confluence_page_section",
        "description": "Return a single Confluence page section by section id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "section_id": {"type": "string"},
                "strategy": {"type": "string", "default": "markers"},
                "max_chars": {"type": "integer", "default": 6000},
            },
            "required": ["page_id", "section_id"],
        },
    },
    {
        "name": "confluence_replace_section",
        "description": "Replace one section and push the merged page back to Confluence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "section_id": {"type": "string"},
                "content": {"type": "string"},
                "strategy": {"type": "string", "default": "markers"},
                "max_chars": {"type": "integer", "default": 6000},
                "dry_run": {"type": "boolean", "default": False},
                "version_message": {"type": "string"},
            },
            "required": ["page_id", "section_id", "content"],
        },
    },
    {
        "name": "confluence_apply_sections",
        "description": "Replace multiple sections in one merged write.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section_id": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["section_id", "content"],
                    },
                },
                "strategy": {"type": "string", "default": "markers"},
                "max_chars": {"type": "integer", "default": 6000},
                "dry_run": {"type": "boolean", "default": False},
                "version_message": {"type": "string"},
            },
            "required": ["page_id", "sections"],
        },
    },
]


def _read_message(stream: Any) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if not line.strip():
            break
        name, _, value = line.decode("utf-8").partition(":")
        headers[name.strip().lower()] = value.strip()
    length = int(headers["content-length"])
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(stream: Any, message: dict[str, Any]) -> None:
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    stream.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
    stream.write(payload)
    stream.flush()


@dataclass
class ServerState:
    config: AppConfig
    service: SectionService | None = None

    def get_service(self) -> SectionService:
        if self.service is None:
            LOGGER.info("Initializing section service for mode=%s", self.config.mode)
            self.service = SectionService(build_adapter(self.config))
        return self.service


def _error_response(message_id: Any, code: int, text: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {
            "code": code,
            "message": text,
        },
    }


def _handle_initialize(message_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "confluence-section-mcp",
                "version": "0.1.0",
            },
        },
    }


def _handle_tool_call(state: ServerState, message_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})
    try:
        LOGGER.info("Handling tool call: %s", name)
        service = state.get_service()
        if name == "confluence_page_outline":
            return {"jsonrpc": "2.0", "id": message_id, "result": format_tool_result(service.get_outline(**arguments))}
        if name == "confluence_page_section":
            return {"jsonrpc": "2.0", "id": message_id, "result": format_tool_result(service.get_section(**arguments))}
        if name == "confluence_replace_section":
            return {"jsonrpc": "2.0", "id": message_id, "result": format_tool_result(service.replace_section(**arguments))}
        if name == "confluence_apply_sections":
            return {"jsonrpc": "2.0", "id": message_id, "result": format_tool_result(service.apply_sections(**arguments))}
    except (AdapterError, KeyError, ValueError) as exc:
        LOGGER.exception("Tool call failed: %s", name)
        return {"jsonrpc": "2.0", "id": message_id, "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True}}
    return _error_response(message_id, -32601, f"Unknown tool: {name}")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Section-aware Confluence MCP proxy.")
    parser.add_argument("--config", help="Path to JSON config file. If omitted, built-in search paths and env are used.")
    parser.add_argument("--log-file", help="Path to a debug log file for MCP handshake tracing.")
    return parser.parse_args(argv)


def _configure_logging(log_file: str | None) -> None:
    LOGGER.handlers.clear()
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False
    if not log_file:
        LOGGER.addHandler(logging.NullHandler())
        return
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOGGER.addHandler(handler)


def run(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    _configure_logging(args.log_file)
    LOGGER.info("Server process started")
    config = load_app_config(args.config)
    LOGGER.info("Configuration loaded")
    state = ServerState(config=config)
    while True:
        message = _read_message(sys.stdin.buffer)
        if message is None:
            LOGGER.info("stdin closed, exiting")
            return 0
        method = message.get("method")
        message_id = message.get("id")
        LOGGER.info("Received method=%s id=%s", method, message_id)
        if method == "initialize":
            _write_message(sys.stdout.buffer, _handle_initialize(message_id))
            LOGGER.info("initialize handled")
            continue
        if method == "notifications/initialized":
            LOGGER.info("notifications/initialized received")
            continue
        if method == "tools/list":
            _write_message(
                sys.stdout.buffer,
                {"jsonrpc": "2.0", "id": message_id, "result": {"tools": TOOLS}},
            )
            LOGGER.info("tools/list handled")
            continue
        if method == "tools/call":
            _write_message(sys.stdout.buffer, _handle_tool_call(state, message_id, message.get("params", {})))
            LOGGER.info("tools/call handled")
            continue
        if method == "ping":
            _write_message(sys.stdout.buffer, {"jsonrpc": "2.0", "id": message_id, "result": {}})
            LOGGER.info("ping handled")
            continue
        if message_id is not None:
            _write_message(sys.stdout.buffer, _error_response(message_id, -32601, f"Unsupported method: {method}"))
            LOGGER.warning("Unsupported method=%s", method)


def main() -> None:
    try:
        raise SystemExit(run())
    except ValueError as exc:
        LOGGER.exception("Fatal configuration error")
        raise


if __name__ == "__main__":
    main()
