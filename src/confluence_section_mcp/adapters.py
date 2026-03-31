from __future__ import annotations

import atexit
from base64 import b64encode
from dataclasses import dataclass
import os
import json
from pathlib import Path
import subprocess
import threading
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import AppConfig, FileConfig, RestConfig, UpstreamMcpConfig


class AdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class PageSnapshot:
    page_id: str
    title: str
    version: int
    body: str
    body_format: str
    space_id: str | None = None


class PageAdapter:
    def get_page(self, page_id: str) -> PageSnapshot:
        raise NotImplementedError

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version: int,
        version_message: str | None = None,
        space_id: str | None = None,
    ) -> PageSnapshot:
        raise NotImplementedError

    def close(self) -> None:
        return None


class FilePageAdapter(PageAdapter):
    def __init__(self, config: FileConfig) -> None:
        self.root = Path(config.root)

    def _path_for(self, page_id: str) -> Path:
        return self.root / f"{page_id}.md"

    def _meta_for(self, page_id: str) -> Path:
        return self.root / f"{page_id}.meta.json"

    def get_page(self, page_id: str) -> PageSnapshot:
        path = self._path_for(page_id)
        if not path.exists():
            raise AdapterError(f"Page file not found: {path}")
        meta_path = self._meta_for(page_id)
        meta: dict[str, Any] = {}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return PageSnapshot(
            page_id=page_id,
            title=str(meta.get("title", page_id)),
            version=int(meta.get("version", 1)),
            body=path.read_text(encoding="utf-8"),
            body_format=str(meta.get("body_format", "markdown")),
            space_id=meta.get("space_id"),
        )

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version: int,
        version_message: str | None = None,
        space_id: str | None = None,
    ) -> PageSnapshot:
        path = self._path_for(page_id)
        path.write_text(body, encoding="utf-8")
        meta = {
            "title": title,
            "version": version + 1,
            "body_format": "markdown",
            "space_id": space_id,
        }
        if version_message:
            meta["version_message"] = version_message
        self._meta_for(page_id).write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")
        return self.get_page(page_id)


class ConfluenceRestAdapter(PageAdapter):
    def __init__(self, config: RestConfig) -> None:
        self.config = config

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"
            return headers
        if self.config.email and self.config.api_token:
            pair = f"{self.config.email}:{self.config.api_token}".encode("utf-8")
            headers["Authorization"] = f"Basic {b64encode(pair).decode('ascii')}"
            return headers
        raise AdapterError("Set either CONFLUENCE_BEARER_TOKEN or CONFLUENCE_EMAIL + CONFLUENCE_API_TOKEN")

    def _request(self, method: str, path: str, *, query: dict[str, str] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.config.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = Request(url=url, data=data, headers=self._headers(), method=method)
        try:
            with urlopen(request) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AdapterError(f"Confluence API {method} {path} failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise AdapterError(f"Confluence API {method} {path} failed: {exc.reason}") from exc

    def get_page(self, page_id: str) -> PageSnapshot:
        data = self._request(
            "GET",
            f"/wiki/api/v2/pages/{page_id}",
            query={"body-format": self.config.body_format},
        )
        body_obj = data.get("body", {}).get(self.config.body_format, {})
        body = body_obj.get("value")
        if body is None:
            raise AdapterError(
                f"Page {page_id} did not include body format '{self.config.body_format}'. "
                "Try another CONFLUENCE_BODY_FORMAT value."
            )
        return PageSnapshot(
            page_id=str(data.get("id", page_id)),
            title=str(data.get("title", page_id)),
            version=int(data.get("version", {}).get("number", 1)),
            body=str(body),
            body_format=self.config.body_format,
            space_id=(str(data["spaceId"]) if data.get("spaceId") is not None else self.config.default_space_id),
        )

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version: int,
        version_message: str | None = None,
        space_id: str | None = None,
    ) -> PageSnapshot:
        payload: dict[str, Any] = {
            "id": page_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": self.config.body_format,
                "value": body,
            },
            "version": {
                "number": version + 1,
            },
        }
        if version_message:
            payload["version"]["message"] = version_message
        target_space_id = space_id or self.config.default_space_id
        if target_space_id:
            payload["spaceId"] = target_space_id
        self._request("PUT", f"/wiki/api/v2/pages/{page_id}", payload=payload)
        return self.get_page(page_id)


class StdioMcpClient:
    def __init__(self, config: UpstreamMcpConfig) -> None:
        env = os.environ.copy()
        env.update(config.env)
        if config.env_passthrough:
            allowed = set(config.env_passthrough) | set(config.env) | {"PATH", "HOME", "USER", "SHELL"}
            env = {key: value for key, value in env.items() if key in allowed}
        self.process = subprocess.Popen(
            [config.command, *config.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            env=env,
        )
        self._lock = threading.Lock()
        self._next_id = 1
        atexit.register(self.close)
        self._initialize()

    def _initialize(self) -> None:
        self.call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "confluence-section-mcp", "version": "0.1.0"}})
        self.notify("notifications/initialized", {})

    def close(self) -> None:
        process = getattr(self, "process", None)
        if not process:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        for stream_name in ("stdin", "stdout", "stderr"):
            stream = getattr(process, stream_name, None)
            if stream:
                stream.close()
        self.process = None

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params})

    def call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self.process is None or self.process.poll() is not None:
                raise AdapterError("Upstream MCP process is not running")
            message_id = self._next_id
            self._next_id += 1
            self._write({"jsonrpc": "2.0", "id": message_id, "method": method, "params": params})
            while True:
                message = self._read()
                if message is None:
                    stderr = b""
                    if self.process and self.process.stderr:
                        stderr = self.process.stderr.read()
                    raise AdapterError(f"Upstream MCP process closed unexpectedly: {stderr.decode('utf-8', errors='replace')}")
                if message.get("id") != message_id:
                    continue
                if "error" in message:
                    raise AdapterError(f"Upstream MCP error for {method}: {message['error']}")
                return message.get("result", {})

    def _write(self, message: dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            raise AdapterError("Upstream MCP stdin is unavailable")
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
        self.process.stdin.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii"))
        self.process.stdin.write(payload)
        self.process.stdin.flush()

    def _read(self) -> dict[str, Any] | None:
        if not self.process or not self.process.stdout:
            return None
        headers: dict[str, str] = {}
        while True:
            line = self.process.stdout.readline()
            if not line:
                return None
            if line == b"\r\n":
                break
            name, _, value = line.decode("utf-8").partition(":")
            headers[name.strip().lower()] = value.strip()
        length = int(headers["content-length"])
        body = self.process.stdout.read(length)
        return json.loads(body.decode("utf-8"))


class UpstreamMcpPageAdapter(PageAdapter):
    def __init__(self, config: UpstreamMcpConfig) -> None:
        self.config = config
        self.client = StdioMcpClient(config)

    def close(self) -> None:
        self.client.close()

    def get_page(self, page_id: str) -> PageSnapshot:
        arguments: dict[str, Any] = {
            self.config.page_id_arg: page_id,
            **self.config.get_page_extra_args,
        }
        payload = self.client.call(
            "tools/call",
            {
                "name": self.config.get_page_tool,
                "arguments": arguments,
            },
        )
        parsed = _parse_upstream_page(payload)
        return PageSnapshot(
            page_id=page_id,
            title=str(parsed.get("title") or page_id),
            version=int(parsed.get("version") or 0),
            body=str(parsed["body"]),
            body_format=str(parsed.get("body_format") or "markdown"),
            space_id=(str(parsed["space_id"]) if parsed.get("space_id") is not None else None),
        )

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version: int,
        version_message: str | None = None,
        space_id: str | None = None,
    ) -> PageSnapshot:
        arguments: dict[str, Any] = {
            **self.config.update_page_extra_args,
            self.config.page_id_arg: page_id,
            self.config.body_arg: body,
        }
        if self.config.title_arg:
            arguments[self.config.title_arg] = title
        if version_message:
            arguments["versionMessage"] = version_message
        if space_id:
            arguments["spaceId"] = space_id
        self.client.call(
            "tools/call",
            {
                "name": self.config.update_page_tool,
                "arguments": arguments,
            },
        )
        updated = self.get_page(page_id)
        if updated.version == 0:
            updated = PageSnapshot(
                page_id=updated.page_id,
                title=updated.title,
                version=version + 1,
                body=updated.body,
                body_format=updated.body_format,
                space_id=updated.space_id,
            )
        return updated


def _parse_upstream_page(result: dict[str, Any]) -> dict[str, Any]:
    texts = [
        entry.get("text", "")
        for entry in result.get("content", [])
        if entry.get("type") == "text"
    ]
    text = "\n".join(part for part in texts if part)
    if not text:
        raise AdapterError("Upstream MCP get-page tool returned no text content")
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        else:
            if isinstance(payload, dict):
                body = payload.get("body") or payload.get("markdown") or payload.get("content") or payload.get("bodyMarkdown")
                if body is None:
                    raise AdapterError("Upstream JSON payload did not contain body/markdown/content/bodyMarkdown")
                return {
                    "title": payload.get("title"),
                    "version": payload.get("version") or payload.get("versionNumber"),
                    "body": body,
                    "body_format": payload.get("body_format") or payload.get("format") or "markdown",
                    "space_id": payload.get("space_id") or payload.get("spaceId"),
                }
    return {
        "title": None,
        "version": 0,
        "body": text,
        "body_format": "markdown",
        "space_id": None,
    }


def build_adapter(config: AppConfig) -> PageAdapter:
    if config.mode == "file" and config.file:
        return FilePageAdapter(config.file)
    if config.mode == "mcp" and config.upstream_mcp:
        return UpstreamMcpPageAdapter(config.upstream_mcp)
    if config.mode == "rest" and config.rest:
        return ConfluenceRestAdapter(config.rest)
    raise AdapterError(f"Unsupported adapter mode: {config.mode}")
