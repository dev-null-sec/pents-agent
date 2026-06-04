# Security Policy

## Intended Use

`pents-agent` is designed for authorized Web/API security testing workflows. Scope files, task cards, and review documents are part of the safety model: they exist so an AI agent can stop, ask for confirmation, and avoid crossing boundaries.

## Reporting Project Security Issues

If you find a vulnerability in this repository itself, please use GitHub Security Advisories when available, or open a minimal issue that does not include exploit details, secrets, target data, or working payloads.

Please do not submit:

- API keys, tokens, credentials, cookies, or session files;
- real target screenshots, raw captures, HAR files, or private reports;
- exploit chains against third-party systems;
- unredacted personal data or production data.

## Handling Sensitive Data

Before publishing or opening a pull request:

- keep `.env` and `.env.local` local;
- do not commit real engagement data unless it is intentionally public and sanitized;
- keep bulky raw outputs under ignored `raw/` or `outputs/` paths;
- replace real domains, IPs, accounts, and screenshots with demo values when sharing examples.

## Safety Boundaries

The project defaults to conservative behavior:

- source-origin validation needs explicit confirmation;
- high-risk payload dictionaries are not enabled by default;
- destructive, high-volume, or out-of-scope testing is forbidden by project policy.
