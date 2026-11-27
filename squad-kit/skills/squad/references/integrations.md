# Integration patterns by category

Generic reference (not a domain pack): applies to any product that needs one of these capabilities. Details of a specific service always come from its **official documentation**, researched by `@PM` with URL and access date; nothing here replaces that research.

Rule shared by all: an own interface in the code (e.g. `MessageSender`, `PriceSource`, `PaymentProvider`) + one connector per service, behind configuration. Without credentials the app starts and shows a "configuration pending" state; never invented data.

## 1. Messaging channels (chat, email, SMS, push)

- Use the provider's **official** API channel. Unofficial automation (emulated web client, personal app session) usually violates the terms of use and leads to number/account bans: only with the user's explicit acceptance, recorded in `.squad/stack.md` as high risk.
- Find out: business/account approval, number or domain verification, **pre-approved templates** for business-initiated messages, service window, recorded **opt-in** requirement, per-recipient and per-day limits, cost per message/conversation.
- Implement: consent record (who, when, how), opt-out that works immediately, queue with retry and backoff, deduplication through an idempotency key, delivery status log through webhooks.
- Test: connector against the provider's sandbox/test number; without a sandbox, test the interface with a fake connector **in tests only**.

## 2. Third-party data collection (prices, catalogs, quotes, content)

- Order of preference: **official or partner/affiliate API** → official feed (XML/CSV/JSON) → collecting public pages.
- Collect pages only when the terms allow it: respect `robots.txt`, identify the client (a generic product User-Agent), conservative rate limit, caching, off-peak schedule. Never bypass login, CAPTCHA, paywall or blocks. Record the terms consulted in the PM research.
- Implement: normalization into an own model (source, external id, value, currency, collected_at), history instead of overwriting when the product depends on change over time, breakage detection (source changed format → alert, not wrong data).
- Test: **recorded** fixtures of real responses in tests; an optional contract test against the real source, outside the default suite.

## 3. Scheduled and background jobs

- Choose by host: the deploy provider's cron (e.g. Vercel Cron), the database scheduler (e.g. `pg_cron` on Supabase), scheduled functions (e.g. Supabase Edge Functions with scheduling), an own worker with a queue. Check the **plan limits** in the official docs (minimum frequency, maximum execution time).
- Every job is **idempotent** (running twice does not duplicate effects), has a lock against concurrent runs, logs start/end/error and shows "last run" in the admin UI.
- An HTTP route called by cron is protected (shared secret in a header, compared in constant time); never public.
- Long work is split into batches or sent to a queue; do not rely on a serverless function living beyond its limit.

## 4. Incoming webhooks

- Validate the **signature** (HMAC or the provider's mechanism) before any effect; reject requests outside the time window.
- Answer fast (2xx) and process asynchronously; deduplicate by event id.
- Webhooks do not use the user's session: the signature is the authorization.

## 5. Payments and billing

- Provider-hosted checkout whenever possible (reduces compliance scope). Never store card data.
- Subscription/order state comes from the provider's **webhook**, not from the browser redirect.
- Provider test environment in development; production keys only on the server.

## 6. AI/LLM inside the product

- API key only on the server; per-user usage limits; timeouts and a friendly error message.
- User input never becomes a system instruction; model output is untrusted data (never executed, never rendered as raw HTML).
- Record the estimated cost per operation in the roadmap.

## What to record

For each integration, in the PM's `field-research.md`: link to the official docs, authentication, limits, approvals, costs, policies, sandbox. In the roadmap: what depends on the user (account, approval, key) with step-by-step instructions to obtain it.
