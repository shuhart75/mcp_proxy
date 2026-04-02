# Review-Only Existing Job

Mode: review-only.
Do not publish anything.
Do not invoke any Confluence skill or wrapper prompt. Follow this instruction set directly.
Do not create subagents unless absolutely necessary.
This job is already bootstrapped from local files. Do not fetch pages again.

Job directory:
`work/review-jobs/req-consistency-001`

Execution rules:
1. Read only:
   - `work/review-jobs/req-consistency-001/job.json`
   - `work/review-jobs/req-consistency-001/overview.md`
   - page `overview.md` files referenced from the job
2. Open only the chunks that are actually needed.
3. Write the controller report to:
   - `work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md`
4. Run:
   - `python3 scripts/advance_review_loop.py --job-dir work/review-jobs/req-consistency-001 --report work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md`
5. Stop and report:
   - main findings
   - pages/chunks inspected
   - `work/review-jobs/req-consistency-001/loop-status.json`

Do not publish.
