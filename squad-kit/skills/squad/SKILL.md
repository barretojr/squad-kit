---
name: squad
description: >-
  Agent squad that INTERVIEWS the user (stack, database, Supabase, auth, integrations,
  deploy), plans and builds an application end to end with real build and test evidence.
  Use ONLY when the user explicitly asks for this skill/squad (e.g. "use the squad skill
  and build an app that...", "/squad ...", "use a skill squad e crie..."). Do not use for
  questions, one-off edits or small tasks.
---

# Squad

Turns a request like *"use the squad and build an app that does X"* into a near-ready application: discovery of what already exists → short interview → lean plan → vertical-slice build → verification with real commands and independent reviewers → preview deploy (if authorized) → delivery with the list of what is left to configure.

The skill is **domain- and stack-agnostic**. Nothing here assumes a business type, database or language: everything comes from the interview (`references/intake.md`) and is recorded in `.squad/stack.md`.

## Language

- **Detect the user's language** from the request (or an explicit "in English", "em português", "en français"...). Record it as `Language:` in `.squad/stack.md` and keep it for the whole project unless the user changes it.
- Everything the user reads is in that language: interview questions, summaries, reports' body text, roadmap, UI copy of the built app (unless the user asks for another UI language), README of the built app, final delivery message.
- **Fixed contract, always English:** file and folder names under `.squad/`, the `##` headings required by the reports, and status keywords (`PLANNED`, `IN PROGRESS`, `BLOCKED`, `DONE`, `VALIDATED`, `APPROVED`, `REJECTED`, `N/A`). The MCP validators read these; Portuguese status words (`APROVADO`, `REPROVADO`) are also accepted.
- The skill's own files are in English; that never changes the language you answer in.

## Modes

| Mode | When | Team | Closes with |
|---|---|---|---|
| **lite** (default for "build/create an app") | New app or large feature, fast result | 3 roles: Architect (`pm`+`coord`), Builder (`backend`/`frontend`/`dba`/`designer` as needed), Verifier (`qa`+`appsec`) | `run_checks` + `audit_code_delivery` + `audit_security_controls` + independent review (`code_critic_blind` and `appsec` as subagents) + acceptance table |
| **full** | Explicit "round table" request, large product or deep audit | The 11 specialists in parallel + 2 critics + `@Finalizer` | Independent `@Finalizer` gate |
| **audit** | Existing project: diagnose, do not build | The relevant specialists | Prioritized roadmap; waits for the user to pick items |

If the user does not name a mode, use **lite** for "build/create…" and **audit** for "analyze/audit…". State the chosen mode in one line.

## Host compatibility

- **Antigravity:** subagents through `invoke_subagent`; agents in `.agents/agents/`.
- **Claude Code:** subagents through the `Agent` tool (profiles installed in `.claude/agents/`); questions through `AskUserQuestion`.
- **No subagent tool:** run the roles yourself, in sequence, **saying explicitly that they are not independent subagents**. Never present simulated roles as real agents.
- **The `squad` MCP is optional.** With it, use `inspect_project`, `run_checks`, `audit_*`, `initialize_squad_docs` etc. Without it, do the equivalent through the shell (build/test) and direct reading, and record that the MCP was unavailable.

## Step 0 — Reconnaissance

1. Find the project root. If `.squad/stack.md` exists, read it and **do not repeat questions already answered**.
2. **Resume:** if `.squad/coordination/roadmap.md` has `IN PROGRESS`/`BLOCKED` items, the previous session was interrupted. Summarize in 3 lines where it stopped, run `run_checks` to learn the real state and continue from the first unfinished item (do not restart the plan).
3. Existing project (brownfield): detect stack, database, auth and tests (`inspect_project` or direct reading) and **preserve** what exists. Ask only what cannot be detected.
4. Empty project (greenfield): go to discovery and the interview.

## Step 0.5 — Market discovery

Follow `references/discovery.md`: 3 to 5 equivalent products, reusable building blocks (official APIs, libraries, starters) and a **build × integrate × adapt** decision for each core capability, with policy/cost constraints (`references/integrations.md`). Save to `.squad/product/discovery.md`. The result becomes at most two interview questions. Without web access, mark it pending and move on; never invent products or URLs.

With a subagent tool, run discovery as a `pm` subagent **in parallel** with reconnaissance so the interview is not delayed.

## Step 1 — Interview (mandatory before building)

Follow `references/intake.md`. Rules:

- **One single round** of questions, as a block, each with a recommended option and always an "other / you decide" way out. Use the host's question tool when available; otherwise a short numbered list.
- **Skip** whatever the request or the project already answers. Ask only what materially changes the result.
- Mandatory block: **stack** (backend/frontend), **database** (own PostgreSQL, Supabase, SQL Server, SQLite…), **existing Supabase project/integration**, **authentication**, **external integrations and available credentials**, **deploy/environment**, **test level**.
- If the user says "you decide", pick the recommended profile from `references/stacks.md` and record the decision and why.
- At most **one follow-up round**, only for dependencies created by the answers (e.g. "use Supabase" → "existing project? use Supabase Auth?").
- Save the result to `.squad/stack.md` (template `templates/stack.template.md`) and show the user a 5–8 line summary.

Specific domains (a business niche, a well-known integration) **are not part of this skill**: if the user names a *domain pack*, read `references/domain-packs.md`. Otherwise the PM researches only what the user described.

## Step 2 — Plan

- **lite:** the Architect writes a short roadmap in `.squad/coordination/roadmap.md`: goal, 3 items explicitly out of the MVP, vertical slices with verifiable acceptance criteria (each with an ID, e.g. `S1-AC2`), data model, API contracts, **main threats** (3 to 5 lines from `appsec`: who can see/change what), risks and what depends on the user's credentials. If there is an external integration, the PM records the research in `.squad/product/field-research.md` with official sources, URLs and access date. Show the user the plan in at most 10 lines and keep building (do not wait for approval unless the user asked to review the plan).
- **full / audit:** real parallel fan-out of the specialists (`pm`, `designer`, `design_system`, `coord`, `dba`, `backend`, `frontend`, `frontend_reviewer`, `appsec`, `qa`, `devops`). Each writes only its own report (see `templates/project-docs.md`) without changing code. Confirm the reports, resend only the failed ones, and `@Coord` consolidates the roadmap. In `audit` and `full`, present the roadmap and **wait for the user to pick items**.
- If web research is unavailable, mark it pending; never invent sources.

## Step 3 — Build (lite: continues without pausing; full: after items are picked)

An explicit "build the app" request already authorizes building in `lite`. Stop to ask only when a missing decision materially changes scope, cost or risk.

1. **Verifiable skeleton first:** project structure, database with versioned migrations/schema, authentication, configuration through environment variables, `.env.example`, run `README`. Run the build before moving on.
2. **Vertical slices**, one at a time (data → API → UI → test). Each slice ends with build and tests passing; only then the next. Parallelize only independent work and never edit the same file in parallel.
3. **External integrations:** own interface + one connector per service, behind configuration. Without credentials the app **starts and shows an empty/"configuration pending" state**; never invented data. Record in the roadmap what the user must provide (accounts, approvals, keys).
4. **Design:** `@Designer`/`@design_system` define visual direction and tokens; use `get_design_reference` and `design-taste-frontend` for real references. Loading/empty/error/success states on every data screen.
5. **Security while building, not only at the end:** every table is born with RLS/policies (Supabase) or every mutation route is born with server-side authorization; every secret is born in an environment variable. Use `references/stack-translation.md` for the equivalent in the chosen stack.
6. Update reports, the roadmap (status per item: `PENDING`, `IN PROGRESS`, `DONE`, `BLOCKED`, `VALIDATED`) and `PROJECT_MAP.md` with **changed files and real results**. Planned is not done.

## Quality gates (all modes)

- **Real data:** no fixed KPIs, lists, users or offers presented as real. Fixtures only in tests/isolated stories.
- **Real authentication** in private apps (server-side, or RLS/policies when the backend is Supabase). The frontend alone is never the security boundary. Privileged keys never reach the client.
- **Real persistence** and versioned schema; "in memory" never counts as done.
- **Proven first-party integration:** a real request from the browser/client to the running backend, with the observed status. Mocking your own API does not satisfy the gate.
- **Secrets:** no keys in code, reports or logs; `.env` in `.gitignore`.
- **User language in the UI:** no framework/infra names.

## Step 4 — Verification

- **Always:** `run_checks` (or the equivalent commands of the profile in `references/stacks.md`): lint, typecheck, build, unit tests and, when planned, integration tests. Record command + result. Failed? Fix and run again; do not downplay.
- `audit_code_delivery` and `audit_security_controls` for mechanical scans; treat findings as leads and confirm by reading the code.
- UI: `@frontend_reviewer` (or you, in `lite`) opens the app in a real browser through `run_playwright_cli`, on desktop and mobile, and records screenshots, console and requests. Include accessibility (axe) and performance (Lighthouse) checks when the tools are available; otherwise record them as not run.
- **Independent review (all modes):** whoever built it does not approve it. With a subagent tool, run **in parallel** and with a clean context (only the diff, `.squad/stack.md` and the roadmap; none of the Builder's justifications):
  - `code_critic_blind` — shortcuts, mocks, fake data, swallowed errors;
  - `appsec` — authorization/RLS proved with two users, secrets out of the client, validated inputs, pitfalls in `references/stack-translation.md`.
  Fix critical/high findings and ask for a second pass only over what changed. Without subagents, run both passes yourself, in sequence, and state that they were not independent.
- **Acceptance table (lite):** in the roadmap, one row per criterion (`S1-AC2 | APPROVED/REJECTED | evidence`); a criterion without evidence is REJECTED.
- `full`: the two critics debate, then `@Finalizer` runs `validate_completion_checklist` and `validate_squad_artifacts`; declare done only with `valid: true`. A gap becomes a roadmap task and blocks acceptance.

## Step 4.5 — Deploy (optional, only with authorization)

Deploying is an outward-facing action: run only what the user authorized in the interview (`.squad/stack.md`, Deploy section) or explicitly later.

1. Prerequisites: Step 4 clean; environment variables listed per environment (names, no values) and checked; migrations versioned.
2. Supabase: `supabase link` to the **preview/dev** project and `supabase db push`. Production only with a new authorization.
3. Vercel: `vercel deploy` (preview). Production (`--prod`) only with a new authorization.
4. Smoke test on the preview URL with `run_playwright_cli`: home page, login, one real data flow; record HTTP status and console in `.squad/evidence/deploy.md`.
5. No CLI login or no authorization: do not work around it; hand the user the exact commands and mark the deploy as pending on them.

## Step 5 — Delivery

Answer, in the user's language, with: what was built and **how to run it** (exact commands); preview URL if deployed; what passed and what failed/stayed blocked, with evidence; the independent reviewers' findings and what was fixed; **what the user still needs to configure** (keys, accounts, approvals, DNS), with step-by-step instructions to obtain each; decisions from the interview and discovery; next roadmap items. Never show a quality badge without evidence.

## References in this skill

- `references/discovery.md` — market discovery and the build × integrate × adapt decision.
- `references/intake.md` — questions, options and how to record the answers.
- `references/stacks.md` — stack profiles (including Next.js + Supabase on Vercel), build/test/deploy commands.
- `references/stack-translation.md` — the equivalent, per stack, of the requirements the agents write with .NET examples; Supabase and Vercel pitfalls.
- `references/integrations.md` — patterns for messaging, third-party data collection, scheduled jobs, webhooks, payments and LLMs.
- `references/domain-packs.md` — how to plug in niche knowledge without polluting the skill.
- `references/rules.md` — the squad rules (installed from `rules/squad-context.md`).
- `templates/` — `stack.template.md`, `project-docs.md`, `roadmap.md`, `agent-report.md`, `PROJECT_MAP.template.md`.
