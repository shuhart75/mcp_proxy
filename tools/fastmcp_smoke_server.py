#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP


LOG_PATH = Path("/tmp/gigacode-fastmcp-smoke.log")
mcp = FastMCP("ConfluenceSectionsSmoke")


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


@mcp.tool()
def smoke_ping() -> str:
    """Return a simple confirmation that the FastMCP smoke server is alive."""
    log("smoke_ping called")
    return "ok"


def main() -> None:
    log("fastmcp smoke server started")
    mcp.run()


if __name__ == "__main__":
    main()
