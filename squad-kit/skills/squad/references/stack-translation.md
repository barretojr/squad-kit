# Tradução de rigor entre stacks

Os perfis dos agentes foram escritos com exemplos de .NET, React, PostgreSQL, Testcontainers e SignalR. Eles definem **o nível de exigência**, não a tecnologia. Quando a stack em `.squad/stack.md` for outra, aplique o equivalente desta tabela. Se não houver equivalente, registre "N/A — motivo" no relatório; não rebaixe a exigência em silêncio.

| Exigência (exemplo .NET no perfil) | Next.js + Supabase (Vercel) | React/Vite + Supabase (sem backend) | Node (Fastify/Nest) | Python (FastAPI) |
|---|---|---|---|---|
| `[Authorize]` em rotas de mutação | Checar sessão no servidor (`supabase.auth.getUser()` em Route Handler/Server Action/middleware) **e** RLS na tabela | **RLS + policies** com `auth.uid()`; Edge Function valida JWT | hook/guard de auth por rota | `Depends()` de auth por rota |
| Filtrar por `UserId`/`TenantId` das claims (BOLA) | Policy `using (auth.uid() = user_id)`; nunca confiar em id do body | idem | `where user_id = req.user.id` | idem |
| DTO imutável, sem mass assignment | Schema Zod no input da Server Action/Route Handler; `insert` só com campos permitidos | Policy `with check` + colunas com `grant` restrito | Zod/class-validator | Pydantic |
| EF Core migrations | `supabase migration new` + `supabase db push`; tipos com `supabase gen types` | idem | Prisma/Drizzle migrations | Alembic |
| Testcontainers + PostgreSQL real | `supabase start` (Postgres/Auth locais) + testes de integração (Vitest) contra ele; `supabase test db` (pgTAP) para policies | idem | Testcontainers Node ou Postgres em Docker | pytest + Postgres em Docker |
| `WebApplicationFactory` (teste de API) | Chamar Route Handlers via `fetch` contra `next dev`/`next start` local, ou testar a função com request real | Chamar Supabase local com dois usuários reais | `fastify.inject` / supertest | `TestClient` |
| SignalR (tempo real) | Supabase Realtime (canal autorizado por RLS) | idem | WebSocket/SSE com auth | WebSocket com auth |
| `ProblemDetails` sem vazar stack trace | Resposta de erro padronizada; `error.tsx`; sem `error.message` do banco para o cliente | Mensagens de erro mapeadas no cliente | error handler global | exception handler |
| `RateLimiter` nativo | Rate limit no middleware/edge ou serviço de KV; limites do Supabase Auth configurados | Limites do Supabase Auth + Edge Function | `@fastify/rate-limit` | `slowapi` |
| Segredos no `appsettings`/User Secrets | Variáveis de ambiente do Vercel por ambiente (Development/Preview/Production); `NEXT_PUBLIC_*` **só** para valores públicos | `VITE_*` é público: só URL e `anon`/publishable key | `.env` + secret store | idem |
| Dockerfile chiseled non-root | N/A no Vercel (plataforma gerencia o runtime); Docker só para dev local se houver serviço extra | N/A | Dockerfile non-root | idem |
| `docker compose up` local | `supabase start` + `npm run dev` | idem | compose | compose |
| CI com `dotnet test` | GitHub Actions: `npm ci`, `lint`, `typecheck`, `build`, testes; Vercel faz deploy de preview por PR | idem | idem | idem |
| LocalDB/Visual Studio | N/A (motivo: não é .NET/SQL Server) | N/A | N/A | N/A |

## Supabase: armadilhas que contam como falha de segurança

- Tabela em schema exposto (`public`) **sem RLS habilitado** = dados abertos para qualquer portador da `anon key`.
- Policy `using (true)` em tabela com dado de usuário.
- `service_role`/secret key em qualquer arquivo que vá ao browser, ou em variável `NEXT_PUBLIC_*`/`VITE_*`.
- Função `security definer` sem `set search_path = ''` (ou schema fixo).
- Bucket de Storage público com arquivos privados; policies de `storage.objects` ausentes.
- URLs de redirecionamento do Auth abertas (`*`) em produção.
- Confiar em `user_metadata` (editável pelo usuário) para autorização; use `app_metadata` ou tabela própria de papéis.

## Vercel: armadilhas comuns

- Variável sensível marcada para o ambiente errado ou exposta com prefixo `NEXT_PUBLIC_`.
- Rota de cron pública (sem segredo no header).
- Função que excede o tempo máximo do plano em trabalho longo (use lotes/fila).
- Headers de segurança ausentes (`Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`) — configure em `next.config` ou `vercel.json`.
- Preview deployments públicos com dados reais de produção: use projeto/banco separado para preview ou proteja o preview.
