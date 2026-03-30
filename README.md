# Confluence Section MCP

`confluence-section-mcp` is a small MCP server and CLI orchestrator that turns one large Confluence page into bounded sections.

The intended flow is:

1. Read the page once.
2. Split it into sections by explicit markers or by Markdown headings.
3. Send each section to a different editor agent or CLI in parallel.
4. Merge the edited sections locally.
5. Push one final update back to Confluence without asking the LLM to hold the whole page in context.

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

Notes for GigaCode config:

- Prefer absolute paths over `$HOME` placeholders unless you have confirmed the client expands them.
- String env values are safer than JSON booleans for `*_SSL_VERIFY` because many MCP launchers pass env vars as strings.
- With this setup, only the proxy is registered as an MCP server in GigaCode. The upstream Atlassian server is spawned internally by the proxy.

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
