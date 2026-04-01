---
name: multi-page-confluence-consistency
description: Review or align two or more large Confluence pages through direct API job scripts with overview-first inspection and an iterative validation loop.
---

# Multi-Page Confluence Consistency

## Goal

Compare, review, and optionally align multiple Confluence pages without forcing one model context to hold all full documents at once.

## When to use

- The user mentions two or more page ids.
- The task is cross-page consistency, terminology alignment, duplication review, or policy comparison.
- One or more pages are large enough that full-page review would waste context.

## Preconditions

- A direct Confluence REST config is available locally.
- Local scripts from this extension are available in the repository checkout.

## Workflow

1. Identify all target page ids and the global consistency goal.
2. Bootstrap a direct review job:

```bash
python3 scripts/bootstrap_direct_review_job.py \
  --job-id <job-id> \
  --page-id <page-id-1> \
  --page-id <page-id-2> \
  --config <direct-api-config.json> \
  --task-file <task-file>
```

3. Read only:
   - `work/review-jobs/<job-id>/job.json`
   - `work/review-jobs/<job-id>/overview.md`
   - each page `overview.md`
4. Decide the operating mode:
   - review-only
   - review-and-fix
5. For review-only:
   - inspect only the relevant chunks
   - write a cross-page controller report
   - stop after the report
6. For review-and-fix:
   - inspect only the relevant chunks
   - edit only changed chunks
   - merge only pages that changed
7. Write the controller report to:

```text
work/review-jobs/<job-id>/reports/iteration-001/controller-report.md
```

8. Advance the validation loop:

```bash
python3 scripts/advance_review_loop.py \
  --job-dir work/review-jobs/<job-id> \
  --report work/review-jobs/<job-id>/reports/iteration-001/controller-report.md
```

9. If the loop status is `needs-edits`, apply another targeted edit pass and validate again.
10. If the loop status is `approved` and the task includes fixes, publish the changed pages:

```bash
python3 scripts/publish_review_job.py \
  --job-dir work/review-jobs/<job-id> \
  --config <direct-api-config.json>
```

11. Report the cross-page findings, changed pages, and publish status to the user.

## Execution Rules

- Do not reject the task just because it spans multiple pages.
- Keep one local workspace per page id.
- Start from job/page overviews and only then open selected chunks.
- For review-only tasks, do not create unnecessary edited files.
- For review-and-fix tasks, do not publish any page before the controller has approved the full set.
- If the user did not explicitly ask for write-back, stop after producing the report.
- Use subagents only if the changed chunks are clearly independent.

## Output Expectations

The final response should include:

- the page ids reviewed
- whether the task was review-only or review-and-fix
- the main consistency findings
- which pages and chunks would need changes
- whether write-back happened
