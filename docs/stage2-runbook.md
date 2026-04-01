# Stage 2 Runbook

Stage 2 turns the stage-1 extension into a repeatable semi-automatic workflow.

The key idea is:

1. fetch once through the working Atlassian MCP
2. move the page body into a local workspace
3. prepare chunk files and chunk briefs with scripts
4. dispatch chunk subagents
5. merge locally
6. run a controller subagent
7. only then write back through the existing Atlassian MCP

## Workspace layout

```text
work/confluence/<page-id>/
├── page.md
├── page.original.md
├── task.md
├── workspace.json
├── merged.md
├── merged.diff
├── controller-report.md
├── controller-status.json
└── chunks/
    ├── manifest.json
    ├── <chunk-id-1>/
    │   ├── source.md
    │   ├── brief.md
    │   └── edited.md
    └── <chunk-id-2>/
        ├── source.md
        ├── brief.md
        └── edited.md
```

## Step-by-step

### 1. Prefer direct workspace bootstrap

Write the user request to:

```text
work/confluence/<page-id>/incoming-task.md
```

Then bootstrap the workspace directly from `~/.gigacode/settings.json`:

```bash
python3 scripts/bootstrap_confluence_workspace.py \
  --page-id <page-id> \
  --task-file work/confluence/<page-id>/incoming-task.md \
  --workspace-root work/confluence \
  --max-chars 12000
```

This avoids large file writes through the model and is the recommended path when GigaCode emits errors like `API Error: terminated` during page-body writes.

Fallback only if the bootstrap script cannot be used:

1. fetch via Atlassian MCP
2. save `incoming-page.md` manually
3. run `prepare_confluence_workspace.py`

### 2. Build chunk briefs

```bash
python3 scripts/build_chunk_briefs.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --task-file work/confluence/<page-id>/task.md
```

### 3. Dispatch one chunk editor subagent per chunk

Give each subagent:

- the global task from `task.md`
- the path to its `brief.md`
- the path to its `source.md`
- the instruction to write `edited.md`

### 4. Merge local results

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --output work/confluence/<page-id>/merged.md \
  --diff-output work/confluence/<page-id>/merged.diff
```

### 5. Run the controller subagent

Give the controller:

- `task.md`
- `merged.md`
- `chunks/manifest.json`
- the instruction to write `controller-report.md`

### 6. Collect the controller status

```bash
python3 scripts/collect_controller_summary.py \
  --report work/confluence/<page-id>/controller-report.md
```

If `approved` is `false`, stop and review the report.

### 7. Prefer direct write-back

Only after controller approval:

```bash
python3 scripts/write_back_confluence_workspace.py \
  --page-id <page-id> \
  --input work/confluence/<page-id>/merged.md
```

Fallback only if the write-back script cannot be used:

- read `merged.md`
- call `mcp__Atlassian__confluence_update_page`
- report the controller decision and write-back result to the user

## Recommended user-facing report

- page id
- chunk count
- whether chunking was used
- controller decision
- whether write-back happened
- main changes

## Multi-page consistency mode

If the task targets two or more pages, do not route it through the single-page editing skill.

Use the `multi-page-confluence-consistency` skill instead.

Recommended pattern:

1. fetch each page once through the Atlassian MCP
2. create one local workspace per page with `prepare_confluence_workspace.py`
3. build briefs for each page
4. choose one of two modes:
   - review-only: no chunk edits, no merge, no write-back
   - review-and-fix: run chunk editors only for the pages and chunks that need changes
5. run one `confluence-cross-page-controller` over the complete page set
6. stop after the report unless the user explicitly asked for write-back

Suggested output files:

- `work/confluence/<page-id>/workspace.json`
- `work/confluence/<page-id>/chunks/manifest.json`
- `work/confluence/<page-id>/merged.md` for pages that were changed
- `work/confluence/<page-id>/merged.diff` for pages that were changed
- `work/confluence/cross-page-report.md`
