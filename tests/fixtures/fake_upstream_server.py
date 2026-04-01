from __future__ import annotations

import json
import sys


PAGE = {
    "page_id": "demo-page",
    "title": "Demo Upstream Page",
    "body": "<!-- BEGIN:intro -->\n# Intro\nOriginal upstream text.\n<!-- END:intro -->\n",
}


def read_message() -> dict | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line == b"\r\n":
            break
        name, _, value = line.decode("utf-8").partition(":")
        headers[name.strip().lower()] = value.strip()
    length = int(headers["content-length"])
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def write_message(message: dict) -> None:
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def tool_result(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


while True:
    message = read_message()
    if message is None:
        raise SystemExit(0)
    method = message.get("method")
    message_id = message.get("id")
    if method == "initialize":
        write_message(
            {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "fake-upstream", "version": "0.1.0"},
                },
            }
        )
        continue
    if method == "notifications/initialized":
        continue
    if method == "tools/call":
        params = message.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name in {"getConfluencePage", "confluence_get_page"}:
            write_message({"jsonrpc": "2.0", "id": message_id, "result": tool_result(PAGE["body"])})
            continue
        if name in {"updateConfluencePage", "confluence_update_page"}:
            body = arguments.get("body")
            if body is None:
                body = arguments.get("content")
            PAGE["body"] = body
            if "title" in arguments:
                PAGE["title"] = arguments["title"]
            write_message({"jsonrpc": "2.0", "id": message_id, "result": tool_result("ok")})
            continue
        write_message({"jsonrpc": "2.0", "id": message_id, "error": {"code": -32601, "message": f"Unknown tool: {name}"}})
        continue
    if message_id is not None:
        write_message({"jsonrpc": "2.0", "id": message_id, "error": {"code": -32601, "message": f"Unsupported method: {method}"}})
