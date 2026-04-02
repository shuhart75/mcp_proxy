# File-First V3

This is the fallback architecture when hidden MCP transport is unreliable and direct review should be driven from local files.

## Flow

1. Fetch pages outside the model loop:

```bash
python3 scripts/fetch_confluence_pages.py \
  --config /absolute/path/to/confluence-rest.config.json \
  --page-id 12345 \
  --page-id 67890 \
  --output-root work/fetched-pages/req-consistency-001
```

2. Bootstrap a review job from those local files:

```bash
python3 scripts/bootstrap_review_job_from_file_root.py \
  --job-id req-consistency-001 \
  --page-id 12345 \
  --page-id 67890 \
  --input-root work/fetched-pages/req-consistency-001 \
  --task-text "Check both pages for consistency and do not publish."
```

3. Run the existing review loop in GigaCode against the local job files only.

4. Publish approved pages:

```bash
python3 scripts/publish_review_job.py \
  --job-dir work/review-jobs/req-consistency-001 \
  --config /absolute/path/to/confluence-rest.config.json
```

## Why use this

- page transport is fully separated from GigaCode
- GigaCode never has to write full page bodies
- fetch and auth can be debugged independently of review logic
