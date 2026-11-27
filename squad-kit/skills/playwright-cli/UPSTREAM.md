# Upstream attribution

This folder vendors [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) (`@playwright/cli`, see `package.json` for the version).

- **License:** Apache License 2.0, Copyright (c) Microsoft Corporation. The full text is in [`LICENSE`](LICENSE) (copied from the official Playwright package) and must stay with any copy of this folder. Source files keep their original license headers.
- **Reviewed:** 2026-11-27.

## What is upstream and what is local

| Path | Origin |
|---|---|
| `playwright-cli.js`, `skillCheck.js`, `playwright.config.ts`, `scripts/`, `references/`, `package.json`, `package-lock.json` | Copied from upstream (not edited in this repository) |
| `UPSTREAM_SKILL.md` | Copy of the upstream skill file (kept for reference) |
| `SKILL.md` | **Local adaptation** for the Squad (MCP `run_playwright_cli`, `.squad/evidence/` paths) |
| `UPSTREAM.md` | Local (this file) |
| `LICENSE` | Apache-2.0 text from the official Playwright package |

`node_modules/` is not versioned; install it with `npm ci` inside this folder. Its packages keep their own licenses.

## Updating from upstream

Replace the upstream files listed above with the new release, keep the local `SKILL.md`, then update the review date.
