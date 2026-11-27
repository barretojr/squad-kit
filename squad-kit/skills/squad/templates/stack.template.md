# Stack e decisões do projeto

- **Atualizado em:** [data]
- **Modo:** [lite | full | audit]
- **Tipo de projeto:** [greenfield | brownfield]

## Produto

- **Objetivo:** [uma frase]
- **Usuários e acesso:** [privado/público; um usuário ou vários; papéis]
- **Fora do MVP:** [3 itens]

## Stack

| Camada | Escolha | Motivo / quem decidiu |
|---|---|---|
| Backend | [.NET / Node-TS / Python / sem backend] | [usuário / squad] |
| Frontend | [React+Vite / Next / outro] | |
| Banco | [PostgreSQL / Supabase / SQL Server / SQLite] | |
| Autenticação | [Identity-JWT / Supabase Auth / social / sem login] | |
| Migrations | [EF Core / Prisma / Alembic / Supabase CLI] | |
| Testes | [básico / completo] e ferramentas | |
| Deploy / ambiente | [Vercel + Supabase cloud / local Docker / nuvem X] | |
| Jobs em segundo plano | [nenhum / Vercel Cron / pg_cron / Edge Function agendada / worker] e frequência | |
| Perfil de `stacks.md` | [A–G] e o sinal que levou à escolha | |

## Descoberta (resumo)

- Produtos equivalentes: [nomes, link para `.squad/produto/descoberta.md`]
- Decisões construir × integrar: [capacidade → decisão]
- Riscos aceitos pelo usuário: [ex.: integração não oficial, custo por uso]

## Deploy (se aplicável)

- Vercel: projeto [existe/criar] · deploy de preview autorizado: [sim/não] · produção: [usuário aprova] · domínio: [...]
- Supabase: projetos [dev/preview] e [produção] separados: [sim/não] · `db push` em produção autorizado: [sim/não]
- Variáveis de ambiente por ambiente: [lista de nomes, sem valores]

## Supabase (se aplicável)

- Projeto existente: [sim/não]. URL e `anon key` via `.env`: [sim/não]. `service_role` somente no servidor.
- Acesso aos dados: [direto do frontend com RLS / via API própria]
- Auth: [Supabase Auth / própria] · Storage/Realtime/Edge Functions: [quais]
- Dev local: [`supabase start` / projeto na nuvem]

## Integrações externas

| Serviço | Credencial disponível? | Sandbox? | Observações |
|---|---|---|---|
| [nome] | [sim/não] | [sim/não] | |

## Comandos do projeto (preencher conforme existirem)

- Build: `[...]`
- Testes unitários: `[...]`
- Testes de integração: `[...]`
- E2E: `[...]`
- Rodar local: `[...]`

## O que depende do usuário

- [chaves, contas, aprovações, domínio/DNS...]
