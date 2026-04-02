# Direct API V2 Plan

This is the target architecture for large Confluence review and edit workflows.

Direct API remains the target backend, but the same job workflow can temporarily use a hidden Atlassian MCP backend from `~/.gigacode/settings.json` when direct API authentication is blocked.

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
- add direct publish path for approved jobs

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

If your Confluence endpoint uses a corporate certificate chain that is not trusted by the local Python runtime, set one of these in the config:

- `"ssl_verify": false` for a pragmatic internal-network setup
- `"ssl_verify": true` plus `"ca_bundle": "/absolute/path/to/corporate-ca.pem"` for a stricter setup

Authentication and endpoint mode:

- Atlassian Cloud:
  - `base_url`: `https://<site>.atlassian.net`
  - `api_flavor`: `cloud` or `auto`
  - auth: `email` + `api_token`
- Confluence Server/Data Center:
  - `base_url`: `https://<host>` or `https://<host>/<context-path>`
  - `api_flavor`: `server` or `auto`
  - auth: `bearer_token` with a personal access token

If you see `401 Basic Authentication Failure` from an internal Tomcat-based Confluence, that usually means the instance is Server/Data Center and should use `bearer_token`, not Cloud-style `email` + `api_token`.

Advance the validation loop after a controller report:

```bash
python3 scripts/advance_review_loop.py \
  --job-dir work/review-jobs/req-consistency-001 \
  --report work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md
```

Publish all changed pages from an approved job:

```bash
python3 scripts/publish_review_job.py \
  --job-dir work/review-jobs/req-consistency-001 \
  --config examples/confluence-rest.config.example.json
```

## Minimal GigaCode prompts

### Review-only

```text
Use `multi-page-confluence-consistency`.

Mode: review-only.
Do not publish anything.

Task:
<describe the consistency rules>

Job:
1. Bootstrap a direct review job with the provided direct API config.
2. Read only `job.json`, job `overview.md`, and page `overview.md` files first.
3. Open only the chunks that are actually needed.
4. Write a controller report.
5. Advance the loop once and stop.
```

### Review-and-fix

```text
Use `multi-page-confluence-consistency`.

Mode: review-and-fix.
Publish only after approval.

Task:
<describe the required fixes>

Job:
1. Bootstrap a direct review job with the provided direct API config.
2. Read only `job.json`, job `overview.md`, and page `overview.md` files first.
3. Edit only the chunks that need changes.
4. Merge only changed pages.
5. Write a controller report.
6. Advance the loop.
7. If status is `needs-edits`, repeat targeted edits and one more controller pass.
8. If status is `approved`, run `publish_review_job.py`.
```
