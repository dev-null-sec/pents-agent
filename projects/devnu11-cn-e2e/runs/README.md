# Sanitized Test Project Runs

This directory records retest rounds for a private authorized test project.

The public repository keeps this README intentionally generic. Real domains, accounts, raw outputs, screenshots, and target-specific notes must stay in private run files or be replaced with sanitized examples before publication.

Top-level project documents keep accumulated facts:

- `scope.md`: authorization scope and stop conditions.
- `inventory.md`: accumulated assets, APIs, parameters, accounts, and test surfaces.
- `evidence.md`: evidence index.
- `report.md`: current overall report.
- `review.md`: project-level review and workflow feedback.

Each test or retest round should live in its own numbered directory:

```text
runs/R001-<date>-<purpose>/
  brief.md
  progress.md
  evidence.md
  outputs/
  raw/
  R001-report-delta.md
  review.md
```

## Public Sharing Rules

- Do not commit raw captures, screenshots, HAR files, tokens, cookies, or private reports.
- Replace real domains, IPs, usernames, emails, and account roles with demo values.
- Keep `outputs/` and `raw/` ignored unless a file is explicitly sanitized and useful as documentation.
- Report deltas should describe workflow shape and evidence references without exposing private target details.

## Next Round Template

For a new round, create the next sequential run:

```text
runs/R00N-<date>-<purpose>/
```

Before execution, confirm:

- authorized targets and excluded targets;
- allowed request rate, concurrency, and test window;
- whether HTTP probing, browser interaction, API checks, source-origin validation, or authenticated testing is allowed;
- which actions must stop immediately and return to the human owner.

End each round with `R00N-report-delta.md` and `review.md`; only merge facts into the top-level report after review.
