# Contributing

Thanks for taking a look at `pents-agent`.

This project is still early, and useful feedback is very welcome: better task-card wording, sharper skill boundaries, safer recon defaults, cleaner templates, and field notes about where AI agents get confused.

## What Helps Most

- Small, focused pull requests.
- Reproducible issues with sanitized examples.
- Improvements to `skills/`, `templates/`, `docs/项目路线/`, and `pents` CLI behavior.
- Real workflow feedback written without real target data.

## What Not To Submit

- Secrets, API keys, cookies, tokens, or `.env` files.
- Real engagement reports, raw scan output, screenshots, HAR files, or private target data.
- Payload packs for destructive testing or unauthorized exploitation.
- Large binary tool builds. Third-party tool source, patches, and install notes are preferred.

## Development Notes

- Use `uv` for Python work in this repository.
- Keep changes scoped to the task.
- Do not rewrite project or module README files unless the task explicitly asks for it.
- When adding security workflows, preserve the project rule: humans define scope, AI executes inside that scope.

## Before Opening a PR

- Run the relevant tests or document why they were not run.
- Check that generated/raw artifacts are not included.
- Search for secrets and real target identifiers.
- Keep public examples sanitized.
