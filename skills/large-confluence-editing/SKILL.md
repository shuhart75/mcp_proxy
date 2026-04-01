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
2. Prefer the direct bootstrap script so the model does not have to write a large page body through a file tool:

```bash
python3 scripts/bootstrap_confluence_workspace.py \
  --page-id <page-id> \
  --task-file work/confluence/<page-id>/incoming-task.md \
  --workspace-root work/confluence \
  --max-chars 12000
```

3. If needed, write the user task to `work/confluence/<page-id>/incoming-task.md` before running the bootstrap script.
4. Use manual fetch plus file save only as a fallback when the bootstrap script cannot be used.
5. After bootstrap, build chunk briefs:

```bash
python3 scripts/build_chunk_briefs.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --task-file work/confluence/<page-id>/task.md
```

6. Create one `confluence-chunk-editor` subagent per chunk. Each subagent receives:
   - the global task
   - the chunk id
   - the path to its `brief.md`
   - the path to its `source.md`
   - the instruction to write output to `edited.md`
7. Wait for all chunk editors to finish.
8. Merge the results:

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --output work/confluence/<page-id>/merged.md \
  --diff-output work/confluence/<page-id>/merged.diff
```

9. Create one `confluence-merge-controller` subagent. Give it:
   - the global task
   - `merged.md`
   - `manifest.json`
   - the instruction to write `controller-report.md`
10. Summarize the controller verdict:

```bash
python3 scripts/collect_controller_summary.py \
  --report work/confluence/<page-id>/controller-report.md
```

11. If the controller status approves the document, prefer direct write-back through the workspace script:

```bash
python3 scripts/write_back_confluence_workspace.py \
  --page-id <page-id> \
  --input work/confluence/<page-id>/merged.md
```

12. Use the MCP update tool directly only as a fallback when the write-back script cannot be used.
13. Report the controller summary and the write-back result to the user.

## Execution Rules

- Never ask a chunk subagent to edit more than one chunk.
- Keep chunk assignments disjoint.
- Preserve stable heading structure where possible.
- Prefer the bootstrap and write-back scripts because they avoid large `write_file` and large MCP tool payloads passing through the model context.
- Before write-back, use the merged local file as the single source of truth.
- Use the controller status file as the approval gate before write-back.

## Write-back Guidance

- The main session performs the final update.
- Do not let chunk subagents call the update tool directly.
- Include the controller's verdict in the final user report.
