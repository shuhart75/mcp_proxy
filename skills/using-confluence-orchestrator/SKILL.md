---
name: using-confluence-orchestrator
description: Use when the user needs to modify a large Confluence page through GigaCode while keeping model context bounded and leveraging subagents.
description: Use when the user needs to review or modify large Confluence pages through a direct API workflow with bounded context and minimal file-tool usage.
---

# Using Confluence Orchestrator

## Purpose

Route large Confluence review and edit requests into the direct API job workflow instead of editing whole pages in one prompt.

## When to use

- The page is long enough that full-page editing would waste context.
- The user wants a coordinated update across multiple sections.
- The user explicitly mentions Confluence, chunking, consistency review, or subagents.

## Rules

- Prefer direct Confluence API via local scripts.
- Do not expose live MCP tools to the model in this workflow.
- Bootstrap one local review job and operate on files from that point forward.
- Start with job and page overviews before reading any full chunk.
- Use chunk edits only for sections that actually need changes.
- Use a controller review before publish.
- Repeat the loop if the controller returns `needs-fixes`.
- Use subagents only when chunks are clearly independent and there is a real speed benefit.

## Routing

- If the task targets one Confluence page, invoke `large-confluence-editing`.
- If the task compares or aligns two or more Confluence pages, invoke `multi-page-confluence-consistency`.
