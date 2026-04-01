---
name: multi-page-confluence-consistency
description: Review or align two or more large Confluence pages for cross-page consistency using the existing Atlassian MCP server, local workspaces, chunk editors, and a cross-page controller subagent.
---

# Multi-Page Confluence Consistency

## Goal

Compare, review, and optionally align multiple Confluence pages without forcing one model context to hold all full documents at once.

## When to use

- The user mentions two or more page ids.
- The task is cross-page consistency, terminology alignment, duplication review, or policy comparison.
- One or more pages are large enough that full-page review would waste context.

## Preconditions

- A working Atlassian MCP server is already connected to GigaCode.
- The following Confluence tools are available, or close equivalents:
  - `mcp__Atlassian__confluence_get_page`
  - `mcp__Atlassian__confluence_update_page`
- Local scripts from this extension are available in the repository checkout.

## Workflow

1. Identify all target page ids and the global consistency goal.
2. For each page, prefer the direct bootstrap script so the model does not have to write a large page body through a file tool:

```bash
python3 scripts/bootstrap_confluence_workspace.py \
  --page-id <page-id> \
  --task-file work/confluence/<page-id>/incoming-task.md \
  --workspace-root work/confluence \
  --max-chars 12000
```

3. If needed, write the shared task to `work/confluence/<page-id>/incoming-task.md` before running the bootstrap script.
4. Use manual fetch plus file save only as a fallback when the bootstrap script cannot be used.

5. For each page, build chunk briefs:

```bash
python3 scripts/build_chunk_briefs.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --task-file work/confluence/<page-id>/task.md
```

6. Decide the operating mode:
   - Review-only mode: do not edit chunks, use the prepared local workspaces as read-only inputs for analysis.
   - Review-and-fix mode: create one `confluence-chunk-editor` subagent per chunk that must be changed.
7. In review-and-fix mode, wait for all chunk editors to finish and merge each page locally:

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --output work/confluence/<page-id>/merged.md \
  --diff-output work/confluence/<page-id>/merged.diff
```

8. Create one `confluence-cross-page-controller` subagent. Give it:
   - the global task
   - the list of page ids
   - each page's `workspace.json`
   - each page's `manifest.json`
   - each page's review target:
     - `page.md` in review-only mode
     - `merged.md` in review-and-fix mode
   - the instruction to write `work/confluence/cross-page-report.md`
9. If the task is review-only, stop after the cross-page report and return the findings to the user.
10. If the task is review-and-fix, use the cross-page report as the approval gate before any write-back.
11. Only after approval, prefer direct write-back for each changed page:

```bash
python3 scripts/write_back_confluence_workspace.py \
  --page-id <page-id> \
  --input work/confluence/<page-id>/merged.md
```

12. Use the MCP update tool directly only as a fallback when the write-back script cannot be used.
13. Report the cross-page findings, changed pages, and write-back status to the user.

## Execution Rules

- Do not reject the task just because it spans multiple pages.
- Keep one local workspace per page id.
- Never ask a chunk subagent to edit more than one chunk.
- Keep chunk assignments disjoint across all pages.
- For review-only tasks, do not create unnecessary edited files.
- For review-and-fix tasks, do not write back any page before the cross-page controller has reviewed the full set.
- If the user did not explicitly ask for write-back, stop after producing the cross-page report.

## Output Expectations

The final response should include:

- the page ids reviewed
- whether the task was review-only or review-and-fix
- the main consistency findings
- which pages and chunks would need changes
- whether write-back happened
