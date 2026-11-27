# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/) for the MCP contract (`SERVER_VERSION` in `squad-kit/mcp/server.py`).

## [Unreleased]

## [2.0.0] — 2026-11-27

### Changed (breaking)
- English is now the repository language: skills, agents, rules, templates, MCP messages and installers. `README.pt-BR.md` keeps a Portuguese overview.
- `.squad/` layout uses English paths: `product/`, `coordination/`, `data/`, `security/`, `quality/`, `operations/`, `evidence/`, with `field-research.md`, `discovery.md`, `visual-direction.md`, `visual-review.md`, `blind-code-critique.md`, `spec-critique.md`. The legacy `.agentes/` folder is no longer supported.
- Required report headings and finalizer checks are in English (e.g. `## Context and evidence`, `**Final verdict:** APPROVED`). Status keywords are accepted in English or Portuguese (`APPROVED`/`APROVADO`, `REJECTED`/`REPROVADO`, `N/A`).
- Agent profiles are stack-neutral, with .NET as one example among others instead of the default.
- Rules are installed as `skills/squad/references/rules.md` for both hosts.

### Added
- Language rule: the squad detects the user's language, records it in `.squad/stack.md` and answers, reports and writes UI copy in it.
- Test suite (`tests/`), GitHub Actions CI, `CONTRIBUTING.md`, issue and pull request templates.
- Roadmap template with an acceptance table; outward-facing actions (deploys, production migrations, pushes) require explicit authorization.
- Upstream `LICENSE` files and `UPSTREAM.md` attribution for the vendored `playwright-cli` (Apache-2.0) and `awesome-design-md` catalog (MIT), checked by the tests.

## [1.5.0] — 2026-11-27

### Added
- Market discovery step (equivalent products, build × integrate × adapt).
- Next.js + Supabase on Vercel stack profile, context-aware stack recommendation and an authorized preview-deploy step.
- `stack-translation.md` and `integrations.md` references.
- Independent code critic and AppSec review in `lite` mode, acceptance table and session resume.
- MCP: Supabase RLS checks, client-side secret exposure, Next.js routes without auth, swallowed errors in JS/TS/Python/Go, lint/typecheck in `run_checks`, finalizer check for authorization tested with two users.

### Changed
- `taste-skill` and `design-taste-frontend` merged into `design-taste-frontend`, now shipping the upstream MIT `LICENSE` and the `library/` folder its scripts need.
- The Claude Code installer keeps each agent's skills as an instruction instead of dropping them.
