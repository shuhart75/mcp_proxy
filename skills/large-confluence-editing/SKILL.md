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
3. Save the returned markdown body to `work/confluence/<page-id>/incoming-page.md`.
4. Save the user task to `work/confluence/<page-id>/incoming-task.md`.
5. Prepare the workspace:

```bash
python3 scripts/prepare_confluence_workspace.py \
  --page-id <page-id> \
  --page-file work/confluence/<page-id>/incoming-page.md \
  --task-file work/confluence/<page-id>/incoming-task.md \
  --workspace-root work/confluence \
  --max-chars 12000
```

6. Build chunk briefs:

```bash
python3 scripts/build_chunk_briefs.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --task-file work/confluence/<page-id>/task.md
```

7. Create one `confluence-chunk-editor` subagent per chunk. Each subagent receives:
   - the global task
   - the chunk id
   - the path to its `brief.md`
   - the path to its `source.md`
   - the instruction to write output to `edited.md`
8. Wait for all chunk editors to finish.
9. Merge the results:

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --output work/confluence/<page-id>/merged.md \
  --diff-output work/confluence/<page-id>/merged.diff
```

10. Create one `confluence-merge-controller` subagent. Give it:
   - the global task
   - `merged.md`
   - `manifest.json`
   - the instruction to write `controller-report.md`
11. Summarize the controller verdict:

```bash
python3 scripts/collect_controller_summary.py \
  --report work/confluence/<page-id>/controller-report.md
```

12. If the controller status approves the document, write the merged markdown back through the existing Atlassian MCP update tool.
13. Report the controller summary and the write-back result to the user.

## Execution Rules

- Never ask a chunk subagent to edit more than one chunk.
- Keep chunk assignments disjoint.
- Preserve stable heading structure where possible.
- Prefer markdown round-tripping because this workflow assumes the Atlassian MCP is already handling that successfully in the environment.
- Before write-back, use the merged local file as the single source of truth.
- Use the controller status file as the approval gate before write-back.

## Write-back Guidance

- The main session performs the final update.
- Do not let chunk subagents call the update tool directly.
- Include the controller's verdict in the final user report.
