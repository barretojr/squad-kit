# Project stack and decisions

- **Updated:** [date]
- **Language:** [language the user writes in, e.g. English / Português (Brasil)] — used for every answer, report body and UI copy
- **Mode:** [lite | full | audit]
- **Project type:** [greenfield | brownfield]

## Product

- **Goal:** [one sentence]
- **Users and access:** [private/public; one user or many; roles]
- **Out of the MVP:** [3 items]

## Stack

| Layer | Choice | Reason / who decided |
|---|---|---|
| Backend | [.NET / Node-TS / Python / no backend] | [user / squad] |
| Frontend | [React+Vite / Next / other] | |
| Database | [PostgreSQL / Supabase / SQL Server / SQLite] | |
| Authentication | [Identity-JWT / Supabase Auth / social / no login] | |
| Migrations | [EF Core / Prisma / Alembic / Supabase CLI] | |
| Tests | [basic / complete] and tools | |
| Deploy / environment | [Vercel + Supabase cloud / local Docker / cloud X] | |
| Background jobs | [none / Vercel Cron / pg_cron / scheduled Edge Function / worker] and frequency | |
| `stacks.md` profile | [A–G] and the signal that led to it | |

## Discovery (summary)

- Equivalent products: [names, link to `.squad/product/discovery.md`]
- Build × integrate decisions: [capability → decision]
- Risks accepted by the user: [e.g. unofficial integration, usage-based cost]

## Deploy (if applicable)

- Vercel: project [exists/create] · preview deploy authorized: [yes/no] · production: [user approves] · domain: [...]
- Supabase: separate [dev/preview] and [production] projects: [yes/no] · production `db push` authorized: [yes/no]
- Environment variables per environment: [list of names, no values]

## Supabase (if applicable)

- Existing project: [yes/no]. URL and `anon` key through `.env`: [yes/no]. `service_role` only on the server.
- Data access: [straight from the frontend with RLS / through an own API]
- Auth: [Supabase Auth / own] · Storage/Realtime/Edge Functions: [which]
- Local dev: [`supabase start` / cloud project]

## External integrations

| Service | Credential available? | Sandbox? | Notes |
|---|---|---|---|
| [name] | [yes/no] | [yes/no] | |

## Project commands (fill in as they exist)

- Build: `[...]`
- Unit tests: `[...]`
- Integration tests: `[...]`
- E2E: `[...]`
- Run locally: `[...]`

## What depends on the user

- [keys, accounts, approvals, domain/DNS...]
