# Team Confluence Workflow

This document describes the operator workflow for working with Confluence pages through local jobs and GigaCode.

Use this flow when you need any of the following:

- review one or more existing Confluence pages
- update one or more existing Confluence pages
- create one or more new Confluence pages
- do both updates and new-page creation in one task

## Why the operator runs `start` and `finish`

`start` and `finish` are intentionally outside GigaCode.

Reasons:

- `start` fetches page data and prepares the local job workspace. This is transport and setup, not reasoning.
- `finish` is the publish boundary. It decides whether anything should be published and then performs the side effect.
- GigaCode is good at reviewing and editing content. It is less reliable as the owner of external side effects.
- This split keeps a human in control of the only risky step: publishing to Confluence.
- It also keeps the model away from full-page source transport and pushes it toward chunk-only editing.

Short version:

- operator owns setup and publish
- GigaCode owns review and content edits inside the prepared workspace

## Recommended commands

Short aliases:

- `bash tools/cjob.sh`
- `bash tools/cfinish.sh --job-id <job-id>`

Low-level equivalents:

- `bash tools/start_confluence_job.sh`
- `bash tools/finish_confluence_job.sh`

## One-time setup on a working machine

After each `git pull`:

```bash
cd /path/to/confluence-section-mcp
bash tools/setup_other_machine_after_pull.sh
```

Make sure the REST config exists:

- default path: `~/.gigacode/confluence-orchestrator/confluence-rest.config.json`

## Main usage pattern

The simplest operator flow is interactive:

```bash
cd /path/to/confluence-section-mcp
bash tools/cjob.sh
```

When started without arguments, `cjob.sh` asks for:

- job id
- mode
- task text
- source page ids or URLs
- default parent page for new pages when needed

After the job is prepared, the script creates:

- `work/review-jobs/<job-id>/gigacode-prompt.md`

Paste the full contents of that file into GigaCode.

After GigaCode finishes:

```bash
cd /path/to/confluence-section-mcp
bash tools/cfinish.sh --job-id <job-id>
```

## Modes

Choose one of these modes when you create a job.

### `analyze`

Use when you want review only.

- inspect existing pages
- no new pages
- no publish

### `update`

Use when you want to edit existing pages only.

- one or more existing pages
- no new pages expected

### `create`

Use when you want to create new pages only.

- no existing page edits required
- requires a default parent page

### `mixed`

Use when the task may include both:

- edits to existing pages
- creation of new pages

This is the default mode for ambiguous or broad tasks.

## How to write a good task

A task should say:

- what pages or topics are in scope
- what should change
- whether new pages are expected
- any constraints or non-goals

Good examples:

```text
Review the FE and BE pages for consistency of terminology and lifecycle states. Fix any inconsistencies. Do not publish automatically.
```

```text
Update the existing rollout page and create two new child pages: rollout checklist and open questions.
```

```text
Check whether the new requirement about deployment type immutability is already reflected. If no edits are needed, return review-only.
```

## What GigaCode is expected to do

GigaCode should:

- read `job.json`, `overview.md`, and page `overview.md` files
- open only the chunks it actually needs
- edit only chunk files for existing pages
- create new pages only under `new-pages/`
- write a controller report
- run the review loop command that the prompt tells it to run

GigaCode should not:

- fetch pages again
- edit full-page source files
- publish directly

## What `finish` does

`finish` is the operator-side finalizer.

It:

- validates the job outputs
- materializes merged page outputs if needed
- checks whether the job is `approved`, `review-only`, or `needs-edits`
- publishes only when publishable changes actually exist
- skips publish for `review-only`
- prints a short summary

## Interpreting outcomes

### `review-only`

This means:

- the model reviewed the task
- it found no required changes
- publish is skipped

This is a valid success outcome.

### `approved`

This means:

- changes exist
- merged outputs are present
- publish can proceed

When you run `finish`, the system publishes.

### `needs-edits`

This means:

- another pass is needed
- inspect the controller report and rerun the content pass

## Where results live

Job workspace:

- `work/review-jobs/<job-id>/`

Important files:

- `gigacode-prompt.md`
- `job.json`
- `loop-status.json`
- `overview.md`
- `reports/iteration-001/controller-report.md`

Existing-page publish bundle:

- `work/review-jobs/<job-id>/artifacts/updated-pages`

New-page publish bundle:

- `work/review-jobs/<job-id>/artifacts/new-pages`

## Troubleshooting

If something looks wrong:

```bash
cd /path/to/confluence-section-mcp
bash tools/collect_review_job_debug.sh <job-id>
```

Useful files to inspect:

- `work/review-jobs/<job-id>/job.json`
- `work/review-jobs/<job-id>/loop-status.json`
- `work/review-jobs/<job-id>/reports/iteration-001/controller-report.md`

## Two recommended team workflows

### Workflow A: easiest for humans

Use interactive mode:

```bash
cd /path/to/confluence-section-mcp
bash tools/cjob.sh
```

Then:

```bash
cat work/review-jobs/<job-id>/gigacode-prompt.md
```

Paste that into GigaCode.

Afterwards:

```bash
bash tools/cfinish.sh --job-id <job-id>
```

### Workflow B: one-file smoke or repeated scenario

If the machine already has a prefilled wrapper:

```bash
bash tools/run_real_confluence_smoke.sh start
```

After GigaCode finishes:

```bash
bash tools/run_real_confluence_smoke.sh finish
```

Use this when the same operator repeats similar smoke or acceptance checks.
