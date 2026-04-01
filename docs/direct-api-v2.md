# Direct API V2 Plan

This is the target architecture for large Confluence review and edit workflows.

## Why this replaces the previous approach

- Live MCP tools consume prompt context in GigaCode.
- Large page bodies should not pass through `write_file`.
- Review and transport are different concerns and should be separated.

## Core principles

1. Direct Confluence REST API is the backend.
2. Local scripts move large page bodies.
3. GigaCode reads only job overviews and selected chunks.
4. Subagents are optional and only used for clearly independent edits.
5. Validation is iterative:
   - inspect result
   - decide approved vs needs-edits
   - if needed, re-edit and validate again

## Job layout

```text
work/review-jobs/<job-id>/
├── task.md
├── overview.md
├── job.json
├── loop-status.json
├── reports/
│   ├── iteration-001/
│   │   └── controller-report.md
│   └── iteration-002/
│       └── controller-report.md
└── pages/
    ├── <page-id-1>/
    │   ├── page.source
    │   ├── page.original.source
    │   ├── page.meta.json
    │   ├── task.md
    │   ├── workspace.json
    │   ├── overview.md
    │   ├── merged.md
    │   ├── merged.diff
    │   └── chunks/
    └── <page-id-2>/
```

## Phase plan

### Phase 1

- direct API bootstrap for one or more pages
- page overview generation
- job state and loop state files
- manual edit and manual controller report

### Phase 2

- route GigaCode through overview-first inspection
- read only selected chunks
- enable review-only and review-and-fix modes

### Phase 3

- selective subagent use for bounded chunks only
- automated publish path for approved pages

## Current scripts

Bootstrap a direct API review job:

```bash
python3 scripts/bootstrap_direct_review_job.py \
  --job-id req-consistency-001 \
  --page-id 12345 \
  --page-id 67890 \
  --config examples/confluence-rest.config.example.json \
  --task-text "Check both pages for consistency and propose fixes."
```

Advance the validation loop after a controller report:

```bash
python3 scripts/advance_review_loop.py \
  --job-dir work/review-jobs/req-consistency-001 \
  --report work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md
```
