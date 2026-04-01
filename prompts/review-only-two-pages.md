# Review-Only Two Pages

Use `multi-page-confluence-consistency`.

Mode: review-only.
Do not publish anything.
Do not create subagents unless absolutely necessary.
Use direct API workflow, not live MCP.

Job ID: `req-consistency-001`
Config: `~/.gigacode/confluence-orchestrator/confluence-rest.config.json`

Pages:
- `<PAGE_ID_1>`
- `<PAGE_ID_2>`

Task:
Check both Confluence pages for consistency of terminology, requirements, process descriptions, contradictions, and semantic mismatches. Do not change Confluence content. Produce a review report only.

Execution rules:
1. Bootstrap the job with `bootstrap_direct_review_job.py`.
2. Read only:
   - `work/review-jobs/req-consistency-001/job.json`
   - `work/review-jobs/req-consistency-001/overview.md`
   - page `overview.md` files
3. Open only the chunks that are actually needed.
4. Write the controller report to:
   - `work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md`
5. Run:
   - `python3 scripts/advance_review_loop.py --job-dir work/review-jobs/req-consistency-001 --report work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md`
6. Stop and report:
   - main findings
   - pages/chunks inspected
   - `loop-status.json`

Do not publish.
