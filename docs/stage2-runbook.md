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

### 1. Save the fetched page locally

After using `mcp__Atlassian__confluence_get_page`, save the markdown body to:

```text
work/confluence/<page-id>/incoming-page.md
```

Write the user request to:

```text
work/confluence/<page-id>/incoming-task.md
```

### 2. Prepare the workspace

```bash
python3 scripts/prepare_confluence_workspace.py \
  --page-id <page-id> \
  --page-file work/confluence/<page-id>/incoming-page.md \
  --task-file work/confluence/<page-id>/incoming-task.md \
  --workspace-root work/confluence \
  --max-chars 12000
```

### 3. Build chunk briefs

```bash
python3 scripts/build_chunk_briefs.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --task-file work/confluence/<page-id>/task.md
```

### 4. Dispatch one chunk editor subagent per chunk

Give each subagent:

- the global task from `task.md`
- the path to its `brief.md`
- the path to its `source.md`
- the instruction to write `edited.md`

### 5. Merge local results

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/confluence/<page-id>/chunks/manifest.json \
  --output work/confluence/<page-id>/merged.md \
  --diff-output work/confluence/<page-id>/merged.diff
```

### 6. Run the controller subagent

Give the controller:

- `task.md`
- `merged.md`
- `chunks/manifest.json`
- the instruction to write `controller-report.md`

### 7. Collect the controller status

```bash
python3 scripts/collect_controller_summary.py \
  --report work/confluence/<page-id>/controller-report.md
```

If `approved` is `false`, stop and review the report.

### 8. Write back through Atlassian MCP

Only after controller approval:

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
