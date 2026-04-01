# Stage 1: GigaCode-Compatible Confluence Orchestrator

## Why this exists

Previous attempts failed at the custom MCP transport layer. Stage 1 avoids that problem entirely.

This extension does not register a new MCP server. It integrates with GigaCode using the native extension/skills/agents mechanism and assumes the existing Atlassian MCP is already working.

## Recommended Atlassian MCP scope

Because GigaCode injects tool descriptions into the prompt context, keep only the small Confluence subset needed for this workflow:

- `confluence_get_page`
- `confluence_update_page`
- optionally `confluence_search`

If your GigaCode build supports it, configure `includeTools` on the Atlassian MCP server instead of exposing the full Jira and Confluence catalog.

## Installation

1. Clone this repository into `~/.gigacode/extensions/confluence-orchestrator`.
2. Restart GigaCode.
3. Confirm the extension loads without warnings about missing `gigacode-extension.json`.

## Usage

Ask GigaCode to use the extension skill:

```text
Use confluence-orchestrator:large-confluence-editing.
Task: update page 123456 so that the release notes and rollout sections reflect version 2.4.
```

Or use the manual command:

```text
/large-confluence-edit
```

## Local file workflow

The skill uses local helper scripts:

### Chunk page

```bash
python3 scripts/chunk_confluence_markdown.py \
  --input work/confluence/123456/page.md \
  --output-dir work/confluence/123456/chunks \
  --max-chars 12000
```

### Merge chunks

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/123456/chunks/manifest.json \
  --output work/confluence/123456/merged.md
```

## Stage 1 scope

Stage 1 gives GigaCode a compatible orchestration layer:

- extension metadata
- chunk editor and controller subagents
- chunk/merge helper scripts
- workflow skills and command entrypoint

It deliberately avoids custom MCP transport work.

## Planned Stage 2

Stage 2 can add a dedicated helper plugin or external runner that automates:

- chunk subagent dispatch
- controller approval gates
- final write-back with fewer manual prompts
