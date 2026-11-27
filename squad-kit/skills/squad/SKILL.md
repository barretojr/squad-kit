---
name: squad
description: >-
  Esquadrão de agentes que ENTREVISTA o usuário (stack, banco, Supabase, autenticação,
  integrações, deploy), planeja e constrói uma aplicação ponta a ponta com evidências reais
  de build e testes. Use SOMENTE quando o usuário pedir explicitamente esta skill/squad
  (ex.: "use a skill squad e crie uma aplicação que..."). Não use para perguntas,
  edições pontuais ou tarefas pequenas.
---

# Squad

Transforma um pedido como *"use a skill e crie uma aplicação que faça X"* em uma aplicação quase pronta: descoberta do que já existe → entrevista curta → plano enxuto → construção por fatias verticais → verificação com comandos reais e revisores independentes → deploy de preview (se autorizado) → entrega com a lista do que falta configurar.

A skill é **agnóstica de domínio e de stack**. Nada aqui assume um tipo de negócio, banco ou linguagem: tudo vem da entrevista (`references/intake.md`) e é gravado em `.squad/stack.md`.

## Modos

| Modo | Quando | Equipe | Fecha com |
|---|---|---|---|
| **lite** (padrão para "crie/construa uma aplicação") | App novo ou feature grande, quer resultado rápido | 3 papéis: Arquiteto (`pm`+`coord`), Construtor (`backend`/`frontend`/`dba`/`designer` conforme precisar), Verificador (`qa`+`appsec`) | `run_checks` + `audit_code_delivery` + `audit_security_controls` + revisão independente (`code_critic_blind` e `appsec` como subagentes) + tabela de aceite |
| **full** | Pedido explícito de "mesa-redonda", produto grande ou auditoria profunda | Os 11 especialistas em paralelo + 2 críticos + `@Finalizer` | Gate independente do `@Finalizer` |
| **audit** | Projeto existente: diagnosticar, sem construir | Os especialistas relevantes | Roadmap priorizado; espera o usuário escolher itens |

Se o usuário não disser o modo, use **lite** para "crie…" e **audit** para "analise/audite…". Diga qual modo escolheu em uma linha.

## Compatibilidade de ambiente

- **Antigravity:** subagentes pela ferramenta `invoke_subagent`; agentes em `.agents/agents/`.
- **Claude Code:** subagentes pela ferramenta `Agent` (os perfis instalados em `.claude/agents/` são os mesmos arquivos de `agents/`); perguntas ao usuário pela ferramenta de perguntas (`AskUserQuestion`).
- **Sem ferramenta de subagentes:** execute os papéis você mesmo, em sequência, **dizendo explicitamente que não são subagentes independentes**. Nunca apresente papéis simulados como agentes reais.
- **MCP `squad` é opcional.** Com ele, use `inspect_project`, `run_checks`, `audit_*`, `initialize_squad_docs` etc. Sem ele, faça o equivalente por shell (build/test) e leitura direta, e registre que o MCP não estava disponível.

## Passo 0 — Reconhecimento

1. Identifique a raiz do projeto. Se `.squad/stack.md` já existe, leia-o e **não repita perguntas já respondidas**.
2. **Retomada:** se `.squad/coordenacao/roadmap.md` tem itens `EM ANDAMENTO`/`BLOQUEADO`, a sessão anterior foi interrompida. Resuma em 3 linhas onde parou, rode `run_checks` para saber o estado real e continue do primeiro item não concluído (não recomece o plano).
3. Projeto existente (brownfield): detecte stack, banco, auth e testes (`inspect_project` ou leitura direta) e **preserve** o que existe. Pergunte apenas o que não der para detectar.
4. Projeto vazio (greenfield): siga para a descoberta e a entrevista.

## Passo 0.5 — Descoberta de mercado

Siga `references/discovery.md`: 3 a 5 produtos equivalentes, blocos reutilizáveis (APIs oficiais, bibliotecas, templates) e a decisão **construir × integrar × adaptar** para cada capacidade central, com restrições de política/custo (`references/integrations.md`). Grave em `.squad/produto/descoberta.md`. O resultado vira até duas perguntas da entrevista. Sem acesso à web, marque como pendente e siga; nunca invente produtos ou URLs.

Em ambiente com subagentes, rode a descoberta como subagente `pm` **em paralelo** com o reconhecimento do projeto, para não atrasar a entrevista.

## Passo 1 — Entrevista (obrigatória antes de construir)

Siga `references/intake.md`. Regras:

- **Uma única rodada** de perguntas, em bloco, com uma opção recomendada em cada uma e sempre com a saída "outro/decida você". Use a ferramenta de perguntas do ambiente quando existir; senão, uma lista numerada.
- **Pule** tudo que o prompt já respondeu ou que o projeto já revela. Pergunte só o que muda materialmente o resultado.
- Bloco obrigatório: **stack** (backend/frontend), **banco** (PostgreSQL próprio, Supabase, SQL Server, SQLite…), **se já existe projeto/integração com Supabase**, **autenticação**, **integrações externas e credenciais disponíveis**, **deploy/ambiente**, **nível de testes**.
- Se o usuário disser "decida você", escolha o perfil recomendado em `references/stacks.md`, registre a decisão e o porquê.
- Máximo de **uma rodada de follow-up**, só para dependências criadas pelas respostas (ex.: "usar Supabase" → "já tem projeto? usar Supabase Auth?").
- Grave o resultado em `.squad/stack.md` (modelo em `templates/stack.template.md`) e mostre um resumo de 5 a 8 linhas ao usuário.

Domínios específicos (um nicho de negócio, uma integração conhecida) **não fazem parte desta skill**: se existir um *domain pack* citado pelo usuário, leia `references/domain-packs.md`. Fora isso, o PM pesquisa só o que o usuário descreveu.

## Passo 2 — Plano

- **lite:** o Arquiteto produz, em `.squad/coordenacao/roadmap.md`, um roadmap curto: objetivo, 3 itens explicitamente fora do MVP, fatias verticais com critérios de aceite verificáveis (cada critério com ID, ex.: `F1-AC2`), modelo de dados, contratos de API, **ameaças principais** (3 a 5 linhas do `appsec`: quem pode ver/alterar o quê), riscos e o que depende de credenciais do usuário. Se houver integração externa, o PM registra a pesquisa em `.squad/produto/pesquisa-de-campo.md` com fontes oficiais, URLs e data de acesso. Mostre ao usuário o plano em até 10 linhas e siga construindo (não espere aprovação, salvo se ele pediu para revisar o plano).
- **full / audit:** fan-out real dos especialistas em paralelo (`pm`, `designer`, `design_system`, `coord`, `dba`, `backend`, `frontend`, `frontend_reviewer`, `appsec`, `qa`, `devops`). Cada um grava só o seu relatório (ver `templates/project-docs.md`), sem alterar código. Confirme os relatórios, reenvie só os que falharam, e o `@Coord` consolida o roadmap. No `audit` e no `full`, apresente o roadmap e **espere o usuário escolher os itens**.
- Se a pesquisa web estiver indisponível, marque a pesquisa como pendente; não invente fontes.

## Passo 3 — Construção (lite: continua sem pausar; full: após a escolha de itens)

Um pedido explícito de "crie a aplicação" já autoriza a construção no `lite`. Pare para perguntar apenas se uma decisão ausente mudar materialmente escopo, custo ou risco.

1. **Esqueleto verificável primeiro:** estrutura de projetos, banco com migrations/schema versionado, autenticação, configuração por variáveis de ambiente, `.env.example`, `README` de execução. Rode build antes de seguir.
2. **Fatias verticais**, uma por vez (dado → API → UI → teste). Cada fatia termina com build e testes passando; só então a próxima. Paralelize apenas trabalho independente e nunca edite o mesmo arquivo em paralelo.
3. **Integrações externas:** interface própria + conector por serviço, atrás de configuração. Sem credencial, o app **sobe e mostra estado vazio/aviso de configuração**; nunca dados inventados. Registre no roadmap o que o usuário precisa providenciar (contas, aprovações, chaves).
4. **Design:** `@Designer`/`@design_system` definem direção visual e tokens; use `get_design_reference` e `design-taste-frontend` para referências reais. Estados loading/empty/error/success em toda tela com dados.
5. **Segurança durante a construção, não só no fim:** toda tabela nasce com RLS/policies (Supabase) ou toda rota de mutação nasce com autorização no servidor; segredo nasce em variável de ambiente. Use `references/stack-translation.md` para o equivalente na stack escolhida.
6. Atualize relatórios, roadmap (status por item: `PENDENTE`, `EM ANDAMENTO`, `CONCLUÍDO`, `BLOQUEADO`) e `PROJECT_MAP.md` com **arquivos alterados e resultados reais**. Planejado não é feito.

## Gates de qualidade (valem em todos os modos)

- **Dados reais:** sem KPIs, listas, usuários ou ofertas fixos apresentados como reais. Fixtures só em teste/storybook isolado.
- **Autenticação real** em app privado (servidor, ou RLS/policies quando o backend é Supabase). Frontend sozinho nunca é a barreira de segurança. Chaves privilegiadas jamais no cliente.
- **Persistência real** e schema versionado; "em memória" não conta como concluído.
- **Integração first-party provada:** requisição real do browser/cliente para o backend em execução, com status observado. Mock da própria API não satisfaz o gate.
- **Segredos:** nada de chave em código, relatório ou log; `.env` no `.gitignore`.
- **Linguagem do usuário na UI:** sem nomes de framework/infra.

## Passo 4 — Verificação

- **Sempre:** `run_checks` (ou os comandos equivalentes do perfil em `references/stacks.md`): build, testes unitários e, quando previstos, integração. Anote comando + resultado. Falhou? Corrija e rode de novo; não relativize.
- `audit_code_delivery` e `audit_security_controls` para varreduras mecânicas; trate os achados como pistas, confirme lendo o código.
- UI: `@frontend_reviewer` (ou você, no `lite`) abre o app em browser real via `run_playwright_cli`, em desktop e mobile, e registra screenshots, console e requests. Inclua checagem de acessibilidade (axe) e desempenho (Lighthouse) quando as ferramentas estiverem disponíveis; sem elas, registre como não executado.
- **Revisão independente (todos os modos):** quem construiu não aprova a própria entrega. Com ferramenta de subagentes, rode **em paralelo** e com contexto limpo (só o diff, `.squad/stack.md` e o roadmap; nada das justificativas do Construtor):
  - `code_critic_blind` — atalhos, mocks, dados falsos, erros engolidos;
  - `appsec` — autorização/RLS testada com dois usuários, segredos fora do cliente, entradas validadas, armadilhas de `references/stack-translation.md`.
  Corrija os achados críticos/altos e peça um segundo passe só sobre o que mudou. Sem subagentes, faça os dois passes você mesmo, em sequência, e declare que não foram independentes.
- **Tabela de aceite (lite):** no roadmap, uma linha por critério (`F1-AC2 | APROVADO/REPROVADO | evidência`); critério sem evidência = REPROVADO.
- `full`: os dois críticos debatem, depois o `@Finalizer` roda `validate_completion_checklist` e `validate_squad_artifacts`; só declare concluído com `valid: true`. Lacuna = tarefa no roadmap e aceite bloqueado.

## Passo 4.5 — Deploy (opcional, só com autorização)

Deploy é ação externa: só execute o que o usuário autorizou na entrevista (`.squad/stack.md`, seção Deploy) ou depois, explicitamente.

1. Pré-requisitos: verificação do Passo 4 limpa; variáveis de ambiente listadas por ambiente (nomes, sem valores) e conferidas; migrations versionadas.
2. Supabase: `supabase link` ao projeto de **preview/dev** e `supabase db push`. Produção só com nova autorização.
3. Vercel: `vercel deploy` (preview). Produção (`--prod`) só com nova autorização.
4. Smoke test na URL de preview com `run_playwright_cli`: página principal, login, um fluxo de dados real; registre status HTTP e console em `.squad/evidencias/deploy.md`.
5. Sem login na CLI ou sem autorização: não tente contornar; entregue os comandos exatos para o usuário rodar e marque o deploy como pendente dele.

## Passo 5 — Entrega

Responda com: o que foi construído e **como rodar** (comandos exatos); URL de preview, se houve deploy; o que passou e o que falhou/ficou bloqueado, com evidência; achados dos revisores independentes e o que foi corrigido; **o que o usuário ainda precisa configurar** (chaves, contas, aprovações, DNS), com o passo a passo para obter cada uma; decisões da entrevista e da descoberta; próximos itens do roadmap. Nunca exiba selo de qualidade sem evidência.

## Referências desta skill

- `references/discovery.md` — descoberta de mercado e decisão construir × integrar × adaptar.
- `references/intake.md` — perguntas, opções e como registrar as respostas.
- `references/stacks.md` — perfis de stack (incluindo Next.js + Supabase no Vercel), comandos de build/teste/deploy.
- `references/stack-translation.md` — equivalente, em cada stack, das exigências escritas com exemplos .NET nos agentes; armadilhas de Supabase e Vercel.
- `references/integrations.md` — padrões para mensageria, coleta de dados de terceiros, jobs agendados, webhooks, pagamentos e LLM.
- `references/domain-packs.md` — como acoplar conhecimento de um nicho sem poluir a skill.
- `templates/` — `stack.template.md`, `project-docs.md`, `roadmap.md`, `agent-report.md`, `PROJECT_MAP.template.md`.
