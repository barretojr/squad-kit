# Translating rigor between stacks

Several agent profiles use .NET, React, PostgreSQL, Testcontainers and SignalR as examples. They define **the level of rigor**, not the technology. When the stack in `.squad/stack.md` is different, apply the equivalent from this table. If there is no equivalent, record "N/A — reason" in the report; never lower the bar silently.

| Requirement (.NET example) | Next.js + Supabase (Vercel) | React/Vite + Supabase (no backend) | Node (Fastify/Nest) | Python (FastAPI) |
|---|---|---|---|---|
| `[Authorize]` on mutation routes | Check the session on the server (`supabase.auth.getUser()` in Route Handler/Server Action/middleware) **and** RLS on the table | **RLS + policies** with `auth.uid()`; Edge Functions validate the JWT | auth hook/guard per route | auth `Depends()` per route |
| Filter by `UserId`/`TenantId` from claims (BOLA) | Policy `using (auth.uid() = user_id)`; never trust an id from the body | same | `where user_id = req.user.id` | same |
| Immutable DTO, no mass assignment | Zod schema on the Server Action/Route Handler input; `insert` only allowed fields | Policy `with check` + columns with restricted `grant` | Zod/class-validator | Pydantic |
| EF Core migrations | `supabase migration new` + `supabase db push`; types with `supabase gen types` | same | Prisma/Drizzle migrations | Alembic |
| Testcontainers + real PostgreSQL | `supabase start` (local Postgres/Auth) + integration tests (Vitest) against it; `supabase test db` (pgTAP) for policies | same | Testcontainers for Node or Postgres in Docker | pytest + Postgres in Docker |
| `WebApplicationFactory` (API test) | Call Route Handlers with `fetch` against local `next dev`/`next start`, or test the function with a real request | Call local Supabase with two real users | `fastify.inject` / supertest | `TestClient` |
| SignalR (real time) | Supabase Realtime (channel authorized by RLS) | same | WebSocket/SSE with auth | WebSocket with auth |
| `ProblemDetails` without leaking stack traces | Standard error response; `error.tsx`; never send the database `error.message` to the client | Error messages mapped in the client | global error handler | exception handler |
| Native `RateLimiter` | Rate limit in middleware/edge or a KV service; Supabase Auth limits configured | Supabase Auth limits + Edge Function | `@fastify/rate-limit` | `slowapi` |
| Secrets in `appsettings`/User Secrets | Vercel environment variables per environment (Development/Preview/Production); `NEXT_PUBLIC_*` **only** for public values | `VITE_*` is public: only the URL and the `anon`/publishable key | `.env` + secret store | same |
| Chiseled non-root Dockerfile | N/A on Vercel (the platform manages the runtime); Docker only for local dev if there is an extra service | N/A | non-root Dockerfile | same |
| Local `docker compose up` | `supabase start` + `npm run dev` | same | compose | compose |
| CI with `dotnet test` | GitHub Actions: `npm ci`, `lint`, `typecheck`, `build`, tests; Vercel deploys a preview per PR | same | same | same |
| LocalDB/Visual Studio | N/A (reason: not .NET/SQL Server) | N/A | N/A | N/A |

## Supabase: pitfalls that count as security failures

- A table in an exposed schema (`public`) **without RLS enabled** = data open to anyone holding the `anon` key.
- Policy `using (true)` on a table with user data.
- `service_role`/secret key in any file that reaches the browser, or in a `NEXT_PUBLIC_*`/`VITE_*` variable.
- `security definer` function without `set search_path = ''` (or a fixed schema).
- Public Storage bucket with private files; missing `storage.objects` policies.
- Open Auth redirect URLs (`*`) in production.
- Trusting `user_metadata` (user-editable) for authorization; use `app_metadata` or an own roles table.

## Vercel: common pitfalls

- Sensitive variable set for the wrong environment or exposed with a `NEXT_PUBLIC_` prefix.
- Public cron route (no secret in the header).
- Function exceeding the plan's maximum duration on long work (use batches/queues).
- Missing security headers (`Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`) — configure them in `next.config` or `vercel.json`.
- Public preview deployments with real production data: use a separate project/database for previews or protect them.
