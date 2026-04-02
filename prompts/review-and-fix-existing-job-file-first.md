# Review-And-Fix Existing Job From Local Files

Use `multi-page-confluence-consistency`.

Mode: review-and-fix.
Do not publish automatically.
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
3. Edit only the chunks that require changes.
4. Merge only changed pages by writing:
   - `work/review-jobs/req-consistency-001/pages/<page-id>/merged.md`
   - `work/review-jobs/req-consistency-001/pages/<page-id>/merged.diff`
5. Write the controller report to:
   - `work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md`
6. Run:
   - `python3 scripts/advance_review_loop.py --job-dir work/review-jobs/req-consistency-001 --report work/review-jobs/req-consistency-001/reports/iteration-001/controller-report.md`
7. If the loop status is `needs-edits`, do one more targeted pass.
8. If the loop status is `approved`, stop and tell me the job is ready for publish with `bash tools/publish_req_consistency_001.sh`.

Do not publish automatically.
