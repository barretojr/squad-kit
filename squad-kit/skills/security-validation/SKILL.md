---
name: security-validation
description: Threat-model and verify authentication, authorization, data access and common web/API risks with reproducible evidence.
---
# Security Validation

During planning, write a threat model and prioritized test cases. During selected execution, test only the authorized local application and scope. For private dashboards, verify server-side authentication/authorization, session expiry/logout, password recovery, tenant/user boundaries (BOLA/IDOR), input validation, XSS/CSRF where relevant, rate limiting and secret handling. Use two test identities for access-control checks where possible. Include a minimal safe reproduction and expected 401/403/404 behavior, then help the owner close findings. Never attack external systems, expose customer data/secrets, or claim a penetration test from static review alone. Report exact endpoint, preconditions, result, severity and evidence; state when active verification could not run.

## Stack-specific checklist

Apply the rows that match `.squad/stack.md`; the full table is in `skills/squad/references/stack-translation.md`.

**Supabase**
- RLS enabled on every table in exposed schemas; policies use `auth.uid()`; no `using (true)` on user data; `with check` on insert/update.
- Prove RLS with two users against the local stack (`supabase start`): A cannot select/update/delete B's rows through the `anon`/publishable key. Prefer an automated test (Vitest/pgTAP `supabase test db`).
- `service_role`/secret key only in server code; grep the client bundle and `NEXT_PUBLIC_*`/`VITE_*` variables.
- `security definer` functions set a fixed `search_path`; Storage buckets private unless content is public, with `storage.objects` policies.
- Authorization never reads `user_metadata`; Auth redirect URLs restricted; email confirmation and rate limits configured as agreed.
- Run the Supabase database linter/security advisor when available (`supabase db lint`) and record the output.

**Next.js / Vercel**
- Every Route Handler and Server Action that mutates data checks the user on the server (`getUser()`), not only in middleware or the UI.
- Inputs validated with a schema (e.g. Zod) on the server.
- Cron routes require a secret header compared in constant time; webhooks verify the provider signature.
- Security headers set (`Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`, frame protection).
- Preview deployments do not use production data unless the user approved it.

**Any stack**
- No secrets in source, reports or logs; `.env*` (except `.env.example`) ignored by git.
- Dependency audit (`npm audit --omit=dev`, `pip-audit`, `dotnet list package --vulnerable`) recorded; High/Critical either fixed or justified.
- Third-party credentials stored by users are encrypted at rest (e.g. Supabase Vault, `pgp_sym_encrypt`, platform KMS).
