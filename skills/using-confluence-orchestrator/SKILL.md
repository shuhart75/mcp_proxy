---
name: using-confluence-orchestrator
description: Use when the user needs to modify a large Confluence page through GigaCode while keeping model context bounded and leveraging subagents.
---

# Using Confluence Orchestrator

## Purpose

Route large Confluence editing requests into the chunked workflow instead of editing the whole page in one prompt.

## When to use

- The page is long enough that full-page editing would waste context.
- The user wants a coordinated update across multiple sections.
- The user explicitly mentions Confluence, mcp-atlassian, chunking, or subagents.

## Rules

- Prefer the existing Atlassian MCP server as the Confluence backend.
- Do not build or rely on a custom MCP transport in this workflow.
- Fetch the page once, store it locally, and operate on files from that point forward.
- Use the chunking script if the page is large enough to justify splitting.
- Use chunk subagents for independent sections.
- Use a controller subagent before write-back.
- Keep the final write-back as one controlled operation through the existing Atlassian MCP update tool.
- If the page is short, skip chunking and edit it directly.

## Routing

- If the task targets one Confluence page, invoke `large-confluence-editing`.
- If the task compares or aligns two or more Confluence pages, invoke `multi-page-confluence-consistency`.
