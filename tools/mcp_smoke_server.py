#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


LOG_PATH = Path("/tmp/gigacode-mcp-smoke.log")


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def read_message() -> dict | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if not line.strip():
            break
        name, _, value = line.decode("utf-8").partition(":")
        headers[name.strip().lower()] = value.strip()
    body = sys.stdin.buffer.read(int(headers["content-length"]))
    return json.loads(body.decode("utf-8"))


def write_message(message: dict) -> None:
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


TOOLS = [
    {
        "name": "smoke_ping",
        "description": "Returns a simple confirmation that the MCP smoke server is alive.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    }
]


def main() -> None:
    log("smoke server started")
    while True:
        message = read_message()
        if message is None:
            log("stdin closed")
            return
        method = message.get("method")
        message_id = message.get("id")
        log(f"method={method} id={message_id}")
        if method == "initialize":
            write_message(
                {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "mcp-smoke-server", "version": "0.1.0"},
                    },
                }
            )
            continue
        if method == "notifications/initialized":
            continue
        if method == "tools/list":
            write_message({"jsonrpc": "2.0", "id": message_id, "result": {"tools": TOOLS}})
            continue
        if method == "tools/call":
            write_message(
                {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {"content": [{"type": "text", "text": "ok"}]},
                }
            )
            continue
        if method == "ping":
            write_message({"jsonrpc": "2.0", "id": message_id, "result": {}})
            continue
        if message_id is not None:
            write_message(
                {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {"code": -32601, "message": f"Unsupported method: {method}"},
                }
            )


if __name__ == "__main__":
    main()
