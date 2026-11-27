---
trigger: manual
description: Squad rules (evidence, real data, authentication, persistence, integrations, language). Apply only while the squad skill is in use.
---

# Squad rules

> These rules are **not** `always_on`: they apply only inside the `squad` skill flow (the skill references them). Ordinary prompts are not affected.

1. **Interview before building:** stack, database, authentication, integrations and deploy are decided with the user (`references/intake.md`) and recorded in `.squad/stack.md`. Never assume a stack, database or business domain the user did not choose or the existing project does not have.
2. **Language:** answer, report and write UI copy in the language recorded in `.squad/stack.md` (detected from the request). File names, required `##` headings and status keywords stay in English — they are a machine contract.
3. **Two phases in `full`, one in `lite`:** in `full` the agents plan in parallel and `@Coord` consolidates the roadmap before any code. In `lite`, the plan is short and building starts right after. In both, implement only what the user asked for/approved and record real evidence.
4. **Brownfield:** keep the stack found in the project; never migrate technology incidentally.
5. **Mandatory authentication in private apps:** authentication and authorization on the server (or through RLS/policies when the backend is a BaaS such as Supabase), secure password hashing when there are own passwords, protected sessions/tokens. No visual-only login and no frontend-only guards.
6. **Integrations and credentials:** every external service the product consumes has its official API mapped by `@PM`, credentials outside the code (environment variables/secrets or an encrypted settings screen) and defined behavior without credentials (empty state, never invented data). Privileged keys (e.g. `service_role`) never reach the frontend.
7. **Real persistence (DBA):** persistence is never DONE while data lives only in memory. `@DBA` documents where and how data lives (PostgreSQL, Supabase, SQL Server, SQLite...) and how the schema is versioned (migrations).
8. **No tech jargon and no fake metrics in the UI:** the interface speaks the business language. No stack/framework/infra names and no fixed numbers, lists or KPIs presented as real. Without data, show an empty state.
9. **Rigor:** never report a test, research, debate or implementation that did not happen. Every test cited has the exact command and the observed result. AppSec separates theoretical analysis from active testing.
10. **One documentation folder:** `.squad/` holds reports, stack, roadmap and evidence (layout in `templates/project-docs.md`). `.agents/` is Antigravity configuration.
11. **Adversarial and independent review:** whoever built it does not approve it. `code_critic_blind` and `appsec` review with a clean context in every mode; in `full`, `code_critic_spec` debates with the blind critic.
12. **Completion gate:** in `full`, an independent `@Finalizer` + the MCP validators. In `lite`, `run_checks` with real build/tests, clean audits and the acceptance table. Gaps become tasks and block acceptance.
13. **Outward-facing actions** (deploys, production migrations, sending real messages, pushing to remote repositories) only with explicit user authorization.
14. **Stack applicability:** report embedded UI and the real project inventory. LocalDB/Visual Studio only applies to .NET on Windows; on other stacks mark N/A with the reason. Unit tests do not prove integration.
