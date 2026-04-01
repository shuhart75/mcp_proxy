---
name: large-confluence-editing
description: Execute a chunked Confluence page editing workflow using an existing Atlassian MCP server, local chunk/merge scripts, chunk-editor subagents, and a merge-controller subagent.
---

# Large Confluence Editing

## Goal

Modify a large Confluence page without forcing one model context to hold the entire document at once.

## Preconditions

- A working Atlassian MCP server is already connected to GigaCode.
- The following Confluence tools are available, or close equivalents:
  - `mcp__Atlassian__confluence_get_page`
  - `mcp__Atlassian__confluence_update_page`
- Local scripts from this extension are available in the repository checkout.

## Workflow

1. Identify the page id and the global task.
2. Fetch the page through the Atlassian MCP tool.
3. Save the returned markdown body to a local workspace file, for example `work/confluence/<page-id>/page.md`.
4. If the document is small, edit it directly and skip chunking.
5. If the document is large, run:

```bash
python3 scripts/chunk_confluence_markdown.py \
  --input work/confluence/<page-id>/page.md \
  --output-dir work/confluence/<page-id>/chunks \
  --max-chars 12000
```

6. Create one `confluence-chunk-editor` subagent per chunk. Each subagent receives:
   - the global task
   - the chunk id
   - the path to its chunk directory
   - the instruction to write output to `edited.md`
7. Wait for all chunk editors to finish.
8. Merge the results:

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --output work/confluence/<page-id>/merged.md
```

9. Create one `confluence-merge-controller` subagent. Give it:
   - the global task
   - `merged.md`
   - `manifest.json`
   - the instruction to write `controller-report.md`
10. If the controller report approves the document, write the merged markdown back through the existing Atlassian MCP update tool.
11. Report the controller summary and the write-back result to the user.

## Execution Rules

- Never ask a chunk subagent to edit more than one chunk.
- Keep chunk assignments disjoint.
- Preserve stable heading structure where possible.
- Prefer markdown round-tripping because this workflow assumes the Atlassian MCP is already handling that successfully in the environment.
- Before write-back, use the merged local file as the single source of truth.

## Write-back Guidance

- The main session performs the final update.
- Do not let chunk subagents call the update tool directly.
- Include the controller's verdict in the final user report.
