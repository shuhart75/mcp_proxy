---
name: large-confluence-editing
description: Execute a direct API Confluence page review-and-fix workflow using local job scripts, chunk files, and an iterative validation loop.
---

# Large Confluence Editing

## Goal

Modify one large Confluence page without forcing one model context to hold the entire document at once.

## Preconditions

- A direct Confluence REST config is available locally.
- Local scripts from this extension are available in the repository checkout.

## Workflow

1. Identify the page id and the global task.
2. Bootstrap a direct review job:

```bash
python3 scripts/bootstrap_direct_review_job.py \
  --job-id <job-id> \
  --page-id <page-id> \
  --config <direct-api-config.json> \
  --task-file <task-file>
```

3. Read only:
   - `work/review-jobs/<job-id>/job.json`
   - `work/review-jobs/<job-id>/overview.md`
   - `work/review-jobs/<job-id>/pages/<page-id>/overview.md`
4. Decide whether this is:
   - review-only
   - review-and-fix
5. If fixes are needed, read only the relevant chunk files and edit only those chunks.
6. Merge local results for the page that changed:

```bash
python3 scripts/merge_confluence_chunks.py \
  --manifest work/review-jobs/<job-id>/pages/<page-id>/chunks/manifest.json \
  --output work/review-jobs/<job-id>/pages/<page-id>/merged.md \
  --diff-output work/review-jobs/<job-id>/pages/<page-id>/merged.diff
```

7. Write a controller report to:

```text
work/review-jobs/<job-id>/reports/iteration-001/controller-report.md
```

The report must contain:

- `Decision: approved` or `Decision: needs-fixes`
- `Recommended next action: ...`

8. Advance the validation loop:

```bash
python3 scripts/advance_review_loop.py \
  --job-dir work/review-jobs/<job-id> \
  --report work/review-jobs/<job-id>/reports/iteration-001/controller-report.md
```

9. If the loop status is `needs-edits`, apply the next round of targeted chunk edits and run another controller pass.
10. If the loop status is `approved`, publish the job:

```bash
python3 scripts/publish_review_job.py \
  --job-dir work/review-jobs/<job-id> \
  --config <direct-api-config.json>
```

11. Report the loop status and publish result to the user.

## Execution Rules

- Do not read the full page before inspecting `overview.md`.
- Edit only chunks that are relevant to the task.
- Preserve stable heading structure where possible.
- Use subagents only if the page has multiple independent chunks that really need parallel editing.
- Before publish, use `merged.md` as the single source of truth.
- Use the loop status as the approval gate before publish.

## Write-back Guidance

- The main session performs the final publish.
- Do not let chunk subagents publish directly.
- Include the controller verdict and loop result in the final user report.
