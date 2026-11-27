# Squad

**English** | [Português (Brasil)](README.pt-BR.md)

An agent squad that **interviews you, plans and builds** an application end to end, proving the result with real builds and tests. Works with **Claude Code** and **Antigravity**.

The skill is domain- and stack-agnostic: business type, database, language and integrations come from the initial interview and are recorded in `.squad/stack.md`. In existing projects, the team keeps the stack it finds.

It answers in **your language**: write the request in English, Portuguese, Spanish, French... (or add "in English") and the interview, reports and the built app's UI copy follow it. The skill files themselves are in English.

## How to use

```text
/squad build an app that <describe what it does>
```
or in plain language: *"use the squad skill and build ..."*.

1. **Market discovery:** the PM finds 3 to 5 products that already do something similar plus ready-made building blocks (official APIs, libraries, starters) and proposes **build × integrate × adapt** for each capability, with policies, costs and risks (`references/discovery.md`).
2. **Interview (one round, up to 8 questions):** stack (recommending **Next.js + Supabase on Vercel** when you have no preference), **database** (PostgreSQL, **Supabase**, SQL Server, SQLite), authentication, integrations and credentials, background jobs, deploy and test level, plus up to two questions from discovery. Nothing the request or project already answers is asked again.
3. **Plan:** short (`lite` mode) or a full round table (`full` mode), including the main threats.
4. **Vertical-slice build** (data → API → screen → test), with RLS/authorization from the first table and build/tests after every slice.
5. **Real verification:** `run_checks` (lint, typecheck, build, tests), mechanical audits, browser review (accessibility and Lighthouse when available) and an **independent review** by the code critic and AppSec, as subagents with a clean context.
6. **Preview deploy** on Vercel/Supabase, only if you authorize it, with a smoke test on the URL.
7. **Delivery:** how to run it, the preview URL, what passed/failed and **what still depends on you** (keys, accounts, approvals), step by step.

| Mode | When | Team | Closes with |
|---|---|---|---|
| `lite` (default for "build...") | New app / large feature | Architect, Builder, Verifier | `run_checks` + audits + independent critic and AppSec + acceptance table |
| `full` | Explicit round-table request | 11 specialists + 2 critics + `@Finalizer` | Independent Finalizer gate |
| `audit` | Existing project, no building | Relevant specialists | Prioritized roadmap |

Skill references: `references/discovery.md` (market discovery), `references/intake.md` (questions), `references/stacks.md` (profiles and commands per stack, including Next.js + Supabase on Vercel), `references/stack-translation.md` (each agent requirement in each stack + Supabase/Vercel pitfalls), `references/integrations.md` (messaging, data collection, jobs, webhooks, payments, LLMs), `references/domain-packs.md` (plugging in niche knowledge without polluting the skill).

## Installation

Requires Python 3.10+ (installer and MCP). Node 18+ only for the heavy skills.

### Claude Code (recommended: lightweight)

```bash
python install_claude.py --project /path/to/your-app        # .claude/ in the project
python install_claude.py --global                           # ~/.claude/
python install_claude.py --project /path/to/your-app --with-heavy-skills   # + design-taste-frontend (taste-skill) and playwright-cli (~60 MB)
```

Installs 8 light skills, the 14 converted agents (each description limits it to the skill's flow, so they never fire on their own) and the MCP server **without registering it**. The MCP is optional; enable it only in the project that needs it, from inside it:

```bash
claude mcp add squad --scope local -- python <path>/.claude/mcp/server.py
```
(or pass `--register-mcp` together with `--project`).

### Antigravity

```powershell
.\install.ps1                              # menu
.\install.ps1 -TargetProject "C:\Projects\MyApp"
.\install.ps1 -Global
```
```bash
./install.sh "/path/to/project"   # or --global
```

Installs into `.agents/` (project) or `~/.gemini/config/` (global). The `squad-context.md` rule is `trigger: manual`: it does not apply to ordinary prompts. Reload Antigravity after installing.

## MCP server (optional)

A dependency-free stdio server in Python 3.10+. The skill works without it (using the shell and direct reading). With it:

| Tool | Purpose |
|---|---|
| `run_checks` | **Runs real lint, typecheck, build and tests** (dotnet, npm/pnpm/yarn, pytest, go, cargo; `only=["db"]` for `supabase test db`), returns status/exit code/output and appends to `.squad/evidence/run_checks.md`. Known commands only; `install=true` installs missing Node dependencies. |
| `inspect_project` | Inventory, detected stack (incl. Next.js, Vite, Vercel, Supabase), persistence, authentication, configs, UI jargon and the declared `stack.md`. |
| `audit_code_delivery` | Mechanical scan: simulated latency, fake IDs, metrics typed into JSX, embedded mocks, swallowed errors (JS/TS/C#/Python/Go), `Thread.Sleep`. Skips test files. |
| `audit_security_controls` | Mutations without auth (.NET `[Authorize]`, Next.js Route Handlers and Server Actions), **Supabase tables without RLS**, `using (true)` policies, `security definer` without `search_path`, hardcoded secrets, `service_role` in client code, secret-like `NEXT_PUBLIC_*`/`VITE_*` variables, `.env` not ignored, missing security tests, unencrypted credentials. |
| `audit_frontend_taste` | Generic AI copy, arbitrary colors/spacing, `prefers-reduced-motion`. |
| `get_design_reference` | Local catalog of reference `DESIGN.md` files. |
| `run_playwright_cli` | Playwright CLI (fixed allowed commands, http/https URLs only). |
| `initialize_squad_docs`, `update_agent_report`, `update_roadmap`, `validate_squad_artifacts`, `validate_completion_checklist` | Artifacts and the completion gate in `.squad/`. |

Audits are heuristics: treat them as leads and confirm by reading the code. The MCP never runs agents or simulates subagents. Paths and required `##` headings under `.squad/` are a fixed English contract; report bodies may be in any language, and status keywords are accepted in English or Portuguese.

## Layout

```text
squad-kit/                    # the single versioned source
├── mcp/server.py             # MCP server (optional)
├── agents/                   # 11 specialists + 2 critics + finalizer
├── commands/                 # /teamwork alias (full mode)
├── rules/                    # squad-context.md (trigger: manual)
└── skills/
    ├── squad/                # SKILL.md + references/ + templates/
    ├── design-reference/     # awesome-design-md catalog
    ├── design-taste-frontend/, playwright-cli/   # heavy, optional (third party, see Credits)
    └── product-research, product-brand-design, quality-validation, security-validation, frontend-integration, spatial-design
tests/                        # MCP and installer tests (python -m unittest)
install.ps1 / install.sh      # Antigravity
install_claude.py             # Claude Code
```

Product working docs live in `.squad/` in the target project (reports, `stack.md`, roadmap, evidence; layout in `skills/squad/templates/project-docs.md`); `.agents/` is Antigravity configuration.

## Contributing

Issues and PRs are welcome — new domain packs, stack profiles, MCP heuristics and translations especially. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [CHANGELOG](CHANGELOG.md).

## Credits and third-party licenses

| Project | Use | License |
|---|---|---|
| [VoltAgent/awesome-design-md](https://github.com/voltagent/awesome-design-md) | Catalog of reference `DESIGN.md` files, in `skills/design-reference/design-md/` with `LICENSE` (see `UPSTREAM.md`) | [MIT](https://github.com/voltagent/awesome-design-md/blob/main/LICENSE) |
| [leonxlnx/taste-skill](https://github.com/leonxlnx/taste-skill) | The `design-taste-frontend` skill (art direction, anti-slop scripts and assets), in `skills/design-taste-frontend/` with `LICENSE` and `UPSTREAM.md`. Photos, icons and fonts in the assets keep their own licenses (credits in the `credits.json` files). | [MIT](https://github.com/leonxlnx/taste-skill/blob/main/LICENSE) |
| [Microsoft Playwright CLI](https://github.com/microsoft/playwright-cli) | Browser inspection, in `skills/playwright-cli/` with `LICENSE` and `UPSTREAM.md` | [Apache-2.0](https://github.com/microsoft/playwright-cli/blob/main/LICENSE) |

The [LICENSE](LICENSE) covers this repository's original content; third-party material keeps its own licenses.

## License

MIT.
