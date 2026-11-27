# Initial interview (intake)

Goal: decide, with as few questions as possible, everything that materially changes the application. **One round**, as a block. Skip what the request or the project already answers. Each question has a recommended option and an "other / you decide" way out. Ask in the user's language (see "Language" in `SKILL.md`).

In Claude Code use `AskUserQuestion` (up to 4 questions per call; group by theme and make more than one call if needed). In Antigravity, use a short numbered list.

Before the questions, show the discovery summary (`references/discovery.md`, 3 to 5 lines) and include the up to two "build × integrate" questions it produced. They take priority over the generic questions below because they change the architecture.

Question budget: **at most 8** in the main round. Beyond that, cut the lowest-impact ones and decide them yourself (recorded as "decided by the squad").

## Block 1 — Product (only if the request is vague)

- What is the main outcome for the end user, and who uses it? (one sentence)
- Private app (login) or public? One user or many (multi-tenant/team)?
- What must stay **out** of the MVP? (if not said, the Architect proposes 3 cuts)

## Block 2 — Stack

- **Backend:** .NET (C#) · Node/TypeScript · Python (FastAPI) · no own backend (BaaS, e.g. Supabase) · other.
- **Frontend:** React + TypeScript + Vite · Next.js · other · no frontend (API only).
- Recommendation when the user says "you decide": use the "Which profile to recommend" table in `references/stacks.md`. With no signal at all, for a web app/SaaS recommend **profile G (Next.js + Supabase on Vercel)**; if the user is fluent in a language, prefer it.
- A single combined question is usually enough: "Stack: Next.js + Supabase on Vercel (recommended) · .NET + React + PostgreSQL · Python + React · other".

## Block 3 — Database

- **Own PostgreSQL** (local Docker; ORM migrations) · **Supabase** (managed Postgres + Auth/Storage/Realtime) · SQL Server · SQLite (local prototype) · other.
- If **Supabase** (follow-up allowed):
  1. Is there an existing Supabase project? URL and `anon`/publishable key go through `.env` (never the `service_role`/secret key in chat; it stays on the server only).
  2. **Supabase Auth** or own authentication?
  3. Data access **straight from the frontend with RLS** (no own backend) or **through an own API** that uses Supabase's Postgres?
  4. Storage, Realtime or Edge Functions needed?
  5. Local development with `supabase start` (Docker) or directly against the cloud project?
- If **own PostgreSQL/SQL Server**: existing instance or Docker Compose? Which version?

## Block 4 — Authentication and access

- Email + password · social login (which provider) · magic link · Supabase Auth · no login.
- Roles/permissions? (e.g. admin and regular user)
- Password recovery and email verification needed?

## Block 5 — External integrations

- Which external services must the product consume or trigger? (free list; may be none)
- For each: account/credentials/approval already in place? Is there a sandbox?
- Rule: without credentials the app starts with an empty state and a configuration notice. The Architect records in the roadmap what depends on the user.
- Background work (scheduled jobs, queues, webhooks)? Real time?

## Block 6 — Runtime and quality

- **Where it runs:** Vercel (frontend/API) + Supabase cloud · local (Docker) · another cloud (which?) · not sure yet. Windows, Linux or both?
- If **Vercel**: existing account/team and project? May the squad make a **preview** deploy at the end (requires your own `vercel login`)? Production stays for you to approve later. Custom domain?
- If **Supabase cloud**: separate projects for development/preview and production? (recommended: yes)
- **Background routine:** does something need to run by itself (collection, sending, reports)? How often? (decides Vercel Cron × `pg_cron`/Edge Function; see `references/integrations.md`)
- **Test level:** basic (build + unit) · complete (+ integration with a real database + browser E2E). Recommended: complete for the main flow.
- **Design:** desired visual reference (brands in the `get_design_reference` catalog), UI language, existing brand/logo.

## How to record

Fill `.squad/stack.md` from `templates/stack.template.md` with the choice, the reason and what was "decided by the squad". Show the user a 5–8 line summary and continue. Ask again only if an answer creates a new dependency.
