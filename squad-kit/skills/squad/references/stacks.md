# Perfis de stack

Use o perfil escolhido na entrevista. Em brownfield, o perfil é o que o projeto já usa. Os comandos abaixo são os que `run_checks` tenta detectar; confirme no projeto antes de depender deles. Para traduzir as exigências dos agentes (escritas com exemplos .NET) para outra stack, use `references/stack-translation.md`.

## Qual perfil recomendar quando o usuário diz "decida você"

| Sinal no pedido ou na conversa | Perfil recomendado |
|---|---|
| Cita Vercel, Supabase, "subir rápido", SaaS/web app sem preferência de linguagem | **G** (Next.js + Supabase no Vercel) |
| Só frontend + dados simples por usuário, sem integração com segredo | **C** (React + Supabase) |
| Prefere .NET / equipe .NET / integração corporativa Windows | **A** ou **B** |
| Prefere Python ou o núcleo é dados/ML | **E** |
| Prefere Node e quer backend separado de longa duração (filas, WebSocket próprio) | **D** |
| Protótipo descartável local | **F** |

Registre em `.squad/stack.md` o sinal que levou à escolha.

## G. Next.js (App Router) + Supabase, deploy no Vercel (recomendado para web app/SaaS sem preferência)

- Estrutura: `app/` (rotas, Server Components, Route Handlers em `app/api/**/route.ts`, Server Actions), `lib/supabase/` (clientes **server** e **browser** separados, via `@supabase/ssr`), `supabase/` (migrations, `seed.sql`, `config.toml`, Edge Functions), `tests/`.
- Dados: Postgres do Supabase; schema versionado com `supabase migration new` e `supabase db push`; tipos com `supabase gen types typescript --local > lib/database.types.ts`. RLS habilitado em **toda** tabela de `public`.
- Auth: Supabase Auth com cookies via `@supabase/ssr`; `middleware.ts` renova a sessão; toda mutação valida usuário no servidor (`getUser()`, não só `getSession()`) **e** é protegida por RLS.
- Segredos: `NEXT_PUBLIC_SUPABASE_URL` e a chave `anon`/publishable podem ir ao cliente; `SUPABASE_SERVICE_ROLE_KEY`/secret key e chaves de terceiros só no servidor (Route Handlers, Server Actions, Edge Functions), nunca com prefixo `NEXT_PUBLIC_`.
- Jobs: Vercel Cron chamando Route Handler protegido por segredo (`CRON_SECRET`) **ou** `pg_cron`/Edge Function agendada no Supabase; confira os limites do plano na doc oficial. Ver `references/integrations.md`.
- Build/test: `npm ci`, `npm run lint`, `npx tsc --noEmit` (ou script `typecheck`), `npm run build`, `npm test` (Vitest). Integração: `supabase start` + testes contra o Supabase local com **dois usuários** (BOLA/RLS); `supabase test db` para policies em pgTAP. E2E: Playwright contra `npm run build && npm start`.
- Deploy: `vercel link`, variáveis por ambiente (`vercel env add`), deploy de preview (`vercel deploy`) e produção (`vercel deploy --prod`) **somente com autorização explícita do usuário** (é ação externa). Migrations em produção: `supabase link` + `supabase db push`, também com autorização. Smoke test com Playwright na URL de preview.
- Observabilidade mínima: logs das funções no Vercel, `error.tsx`/`global-error.tsx`, página de status/última execução dos jobs para o admin.

## A. .NET + React + PostgreSQL (recomendado se o usuário prefere .NET)

- Estrutura: `src/Api` (+ Domain/Application/Infrastructure quando o tamanho justificar), `client/` (React + TS + Vite), `tests/`.
- Dados: EF Core + Npgsql, migrations (`dotnet ef migrations add`, `dotnet ef database update`), PostgreSQL via `docker compose`.
- Auth: ASP.NET Identity ou JWT com hashing do `PasswordHasher`; `[Authorize]` nas rotas de mutação.
- Build/test: `dotnet build`, `dotnet test`; cliente: `npm ci`, `npm run build`, `npm test`.
- Integração: `WebApplicationFactory` + Testcontainers (PostgreSQL real). E2E: Playwright.
- Aplicabilidade: LocalDB/Visual Studio só se aplica se o banco for SQL Server em Windows; com PostgreSQL marque N/A com motivo.

## B. .NET + React + Supabase

- Banco: Postgres do Supabase. A API .NET conecta com Npgsql na connection string do Supabase (use o *pooler* em ambientes serverless/curtos) ou o frontend usa `supabase-js` só para o que for seguro por RLS.
- Auth: Supabase Auth no frontend; a API .NET **valida o JWT do Supabase** (JWKS/segredo do projeto) e autoriza no servidor. Alternativa: auth própria e Supabase só como Postgres.
- Schema: migrations versionadas (Supabase CLI `supabase migration new` / `supabase db push`, **ou** EF Core; não os dois sem combinar). RLS habilitado em toda tabela exposta.
- Segredos: `service_role` só no servidor; `anon key` pode ir ao cliente, protegida por RLS.
- Dev local: `supabase start` (Docker) para ter Postgres/Auth locais.
- Build/test igual ao perfil A; testes de RLS com dois usuários.

## C. React + Supabase (sem backend próprio)

- O frontend fala direto com o Supabase; **a segurança é RLS + policies** testadas. Lógica sensível, segredos e integrações externas vão para **Edge Functions** ou um pequeno backend.
- Auth: Supabase Auth. Tipos gerados pelo CLI (`supabase gen types`).
- Build/test: `npm ci`, `npm run build`, `npm test`; E2E Playwright contra o projeto local (`supabase start`).
- Gate de "autorização no servidor" = policies de RLS verificadas com pelo menos dois usuários (BOLA/IDOR).

## D. Node/TypeScript (Fastify ou NestJS) + React/Next + PostgreSQL ou Supabase

- ORM: Prisma ou Drizzle, com migrations. Validação de entrada (Zod).
- Auth: JWT/sessão com hashing (argon2/bcrypt) ou Supabase Auth.
- Build/test: `npm ci`, `npm run build`, `npm test` (Vitest/Jest); integração com Testcontainers ou banco local em Docker; E2E Playwright.

## E. Python (FastAPI) + React + PostgreSQL ou Supabase

- SQLAlchemy/SQLModel + Alembic; Pydantic para contratos.
- Build/test: `pytest`; cliente como no perfil D.

## F. SQLite (protótipo)

- Só para protótipo local; avise que não é o destino de produção. Use migrations mesmo assim.

## Regras comuns

- `docker-compose.yml` para dependências locais (banco etc.) quando não for Supabase gerenciado.
- `.env.example` completo e `.env` no `.gitignore`.
- README de execução com os comandos exatos, validados.
- CI mínimo (build + testes) quando o usuário escolher nuvem/GitHub.
