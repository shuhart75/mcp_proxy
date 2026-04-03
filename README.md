# Confluence Section MCP

This repository now contains two tracks:

1. A previous experimental custom MCP proxy.
2. A new stage-1 GigaCode extension workflow that avoids custom MCP transport and builds on an already working Atlassian MCP server.

The recommended path for large-page review and editing is now the direct API design in [`docs/direct-api-v2.md`](./docs/direct-api-v2.md).
For a simple team-facing operator guide, use [`docs/team-confluence-workflow.md`](./docs/team-confluence-workflow.md).
The extension workflow documented in [`docs/stage1-extension.md`](./docs/stage1-extension.md) remains available as a legacy path.
For step-by-step macOS installation commands, use [`docs/stage1-macos-setup.md`](./docs/stage1-macos-setup.md).
The previous extension-oriented stage-2 flow is documented in [`docs/stage2-runbook.md`](./docs/stage2-runbook.md).

`confluence-section-mcp` originally started as a small MCP server and CLI orchestrator that turns one large Confluence page into bounded sections.

The intended flow is:

1. Read the page once.
2. Split it into sections by explicit markers or by Markdown headings.
3. Send each section to a different editor agent or CLI in parallel.
4. Merge the edited sections locally.
5. Push one final update back to Confluence without asking the LLM to hold the whole page in context.

The preferred deployment mode for GigaCode is now a JSON config file passed via `--config`, because some GigaCode builds do not propagate `mcpServers.env` into the spawned process.

## What is included

- `confluence-section-mcp`
  - MCP server with section-level tools.
- `confluence-section-orchestrator`
  - CLI that runs an external editor command over page sections in parallel and merges the outputs.
- `file` mode
  - Local markdown files for testing.
- `rest` mode
  - Direct Confluence REST adapter using the page body format selected via `CONFLUENCE_BODY_FORMAT`.
- `mcp` mode
  - The proxy spawns an upstream MCP server over `stdio`, calls its Confluence tools, and exposes only section-level tools to your model.

## Supported sectioning modes

- `markers`
  - Preferred. The page contains markers like:

```md
<!-- BEGIN:release-notes -->
## Release notes
...
<!-- END:release-notes -->
```

- `headings`
  - Fallback. The page is split by Markdown headings and further chunked if a heading block is still too large.

## Install

```bash
cd /home/reutov/confluence-section-mcp
python3 -m pip install -e .
```

## Configuration

`confluence-section-mcp` can load configuration from:

1. `--config /absolute/path/config.json`
2. `./confluence-section-mcp.config.json`
3. `~/.config/confluence-section-mcp/config.json`
4. environment variables

For GigaCode, prefer option 1.

### File mode

```bash
export CONFLUENCE_SECTION_MODE=file
export CONFLUENCE_FILE_ROOT=/path/to/local-pages
```

Each page is stored as:

- `/path/to/local-pages/12345.md`
- `/path/to/local-pages/12345.meta.json`

Example meta:

```json
{
  "title": "Sample Page",
  "version": 7,
  "body_format": "markdown"
}
```

### REST mode

```bash
export CONFLUENCE_SECTION_MODE=rest
export CONFLUENCE_BASE_URL="https://your-domain.atlassian.net"
export CONFLUENCE_BODY_FORMAT=storage
export CONFLUENCE_EMAIL="user@example.com"
export CONFLUENCE_API_TOKEN="..."
```

Or use bearer auth:

```bash
export CONFLUENCE_BEARER_TOKEN="..."
```

Notes:

- This adapter writes back using the selected Confluence body format.
- If you currently rely on Rovo MCP Markdown conversion, keep that in mind. Direct REST updates are safer when your chosen `CONFLUENCE_BODY_FORMAT` matches what you actually read and write.

### MCP mode for hidden Rovo

Use this when you want GigaCode to talk only to this proxy while the original Atlassian/Rovo server stays completely behind it.

```bash
export CONFLUENCE_SECTION_MODE=mcp
export CONFLUENCE_UPSTREAM_COMMAND=npx
export CONFLUENCE_UPSTREAM_ARGS='-y mcp-remote https://mcp.atlassian.com/v1/mcp'
```

Optional overrides:

```bash
export CONFLUENCE_UPSTREAM_GET_TOOL=getConfluencePage
export CONFLUENCE_UPSTREAM_UPDATE_TOOL=updateConfluencePage
export CONFLUENCE_UPSTREAM_PAGE_ID_ARG=pageId
export CONFLUENCE_UPSTREAM_BODY_ARG=body
export CONFLUENCE_UPSTREAM_TITLE_ARG=title
```

If the upstream process needs selected environment variables, pass them through:

```bash
export CONFLUENCE_UPSTREAM_ENV='ATLASSIAN_API_TOKEN,ATLASSIAN_EMAIL'
```

What this buys you:

- GigaCode sees only `confluence_page_outline`, `confluence_page_section`, `confluence_replace_section`, `confluence_apply_sections`.
- The original Rovo/Atlassian tool catalog does not consume model context.
- Section splitting and final merge happen in this proxy, not in the model.

### GigaCode without `mcpServers.env`

If your GigaCode build does not pass `mcpServers.env` to the MCP process, use a file-based config instead.

1. Copy [`examples/confluence-section-mcp.config.example.json`](./examples/confluence-section-mcp.config.example.json) to `confluence-section-mcp.config.json`.
2. Fill in real paths and Atlassian credentials.
3. Point GigaCode to the proxy using [`examples/gigacode-mcp-config.no-env.json`](./examples/gigacode-mcp-config.no-env.json).

In that mode:

- GigaCode only launches `confluence-section-mcp --config /absolute/path/...`.
- The proxy itself injects the Atlassian env for the hidden upstream `mcp-atlassian`.
- You do not depend on `mcpServers.env` at all.

## MCP tools

- `confluence_page_outline`
  - Returns page metadata and section outline.
- `confluence_page_section`
  - Returns one bounded section.
- `confluence_replace_section`
  - Replaces one section, merges locally, optionally writes back.
- `confluence_apply_sections`
  - Replaces multiple sections in one merged write.

## Example MCP config

```json
{
  "mcpServers": {
    "confluence-sections": {
      "command": "confluence-section-mcp",
      "env": {
        "CONFLUENCE_SECTION_MODE": "rest",
        "CONFLUENCE_BASE_URL": "https://your-domain.atlassian.net",
        "CONFLUENCE_BODY_FORMAT": "storage",
        "CONFLUENCE_EMAIL": "user@example.com",
        "CONFLUENCE_API_TOKEN": "..."
      }
    }
  }
}
```

Example with hidden upstream Rovo behind this proxy:

```json
{
  "mcpServers": {
    "confluence-sections": {
      "command": "confluence-section-mcp",
      "env": {
        "CONFLUENCE_SECTION_MODE": "mcp",
        "CONFLUENCE_UPSTREAM_COMMAND": "npx",
        "CONFLUENCE_UPSTREAM_ARGS": "-y mcp-remote https://mcp.atlassian.com/v1/mcp"
      }
    }
  }
}
```

Example with your local `mcp-atlassian` install is in [`examples/gigacode-mcp-config.json`](./examples/gigacode-mcp-config.json).
The preferred no-env variant is in [`examples/gigacode-mcp-config.no-env.json`](./examples/gigacode-mcp-config.no-env.json).
The MCP handshake smoke-test variant is in [`examples/gigacode-mcp-config.smoke.json`](./examples/gigacode-mcp-config.smoke.json).

Notes for GigaCode config:

- Prefer absolute paths over `$HOME` placeholders unless you have confirmed the client expands them.
- String env values are safer than JSON booleans for `*_SSL_VERIFY` because many MCP launchers pass env vars as strings.
- With this setup, only the proxy is registered as an MCP server in GigaCode. The upstream Atlassian server is spawned internally by the proxy.
- If you are using `mcp-atlassian` rather than Rovo MCP, prefer a file config and set tool names/args explicitly. The sample config already uses `confluence_get_page` / `confluence_update_page`.

## Handshake Debugging

If GigaCode shows `Disconnected` before any real tool calls happen, first test whether it can talk to a minimal MCP server at all.

1. Replace your MCP config with [`examples/gigacode-mcp-config.smoke.json`](./examples/gigacode-mcp-config.smoke.json).
2. Restart GigaCode fully.
3. Inspect `/tmp/gigacode-mcp-smoke.log`.

Expected healthy log:

```text
smoke server started
method=initialize id=...
method=tools/list id=...
```

If the log only shows:

```text
smoke server started
stdin closed
```

then GigaCode launched the process but closed the pipe before any MCP handshake reached the server. In that case the problem is outside the Confluence proxy logic and must be debugged at the GigaCode launcher/config layer.

For proxy-level tracing, add `--log-file /absolute/path/proxy-debug.log` to the proxy server args and inspect that file after restart.

If the handwritten smoke server still fails, try the official Python SDK smoke server on the target machine:

```json
{
  "mcpServers": {
    "ConfluenceSections": {
      "command": "/path/to/python-with-mcp-sdk",
      "args": [
        "/absolute/path/to/mcp_proxy/tools/fastmcp_smoke_server.py"
      ],
      "timeout": 60000,
      "trust": false
    }
  }
}
```

Then inspect:

```bash
cat /tmp/gigacode-fastmcp-smoke.log
```

If the FastMCP version connects while the handwritten smoke server does not, the issue is in the custom stdio/protocol implementation, not in GigaCode's ability to launch a local MCP process.

If you suspect a protocol-library mismatch, run the runtime diagnostic script on the target machine:

```bash
python3 tools/diagnose_mcp_runtime.py \
  "/Users/21356108/.gigacode/extensions/mcp_proxy/confluence-section-mcp" \
  "/Users/21356108/Library/Application Support/iTerm2/iterm2env-3.10.4/versions/3.10.4/bin/mcp-atlassian"
```

It prints JSON with:

- Python executable and version
- `PYTHONPATH` / `VIRTUAL_ENV`
- availability of `mcp`, `mcp.server.fastmcp`, and `fastmcp`
- discovered `python` and `mcp-atlassian` executables
- existence and executability of explicitly passed file paths

For a real GigaCode installation, prefer the config-driven diagnostic script. It reads `settings.json`, finds `mcpServers.ConfluenceSections`, follows `--config`, and probes the actual Python interpreters configured there.

```bash
python3 tools/diagnose_from_gigacode_settings.py
```

If your `settings.json` is not in a default location, pass it explicitly:

```bash
python3 tools/diagnose_from_gigacode_settings.py "/absolute/path/to/settings.json"
```

## Parallel editor orchestration

The orchestrator runs one shell command per section. The command receives escaped file paths via placeholders:

- `{input_file}`
- `{output_file}`
- `{instruction_file}`
- `{section_id}`
- `{label}`

Minimal example:

```bash
confluence-section-orchestrator 12345 \
  --strategy markers \
  --max-workers 4 \
  --instructions "Rewrite the section in a concise release-note style." \
  --editor-command "cp {input_file} {output_file}"
```

Typical real setup with an LLM CLI:

```bash
confluence-section-orchestrator 12345 \
  --strategy markers \
  --max-workers 4 \
  --instructions-file ./rewrite-prompt.txt \
  --editor-command "gigacode edit --instructions {instruction_file} --input {input_file} --output {output_file}" \
  --write-back
```

The orchestrator writes a workspace with:

- `manifest.json`
- one directory per section with `input.md`, `output.md`, `instructions.txt`
- `merged.md`
- `merged.diff`

## Suggested multi-agent pattern

1. Add stable `BEGIN/END` markers to large pages.
2. Use `confluence_page_outline` to list sections.
3. Hand each section to a dedicated agent or CLI invocation.
4. Collect edited section outputs.
5. Call `confluence_apply_sections` once, or use the orchestrator `--write-back`.
6. Re-read the outline or target sections to verify the write.

## Validation

```bash
cd /home/reutov/confluence-section-mcp
python3 -m unittest discover -s tests -v
```
