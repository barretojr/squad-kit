# Squad

[English](README.md) | **Português (Brasil)**

Esquadrão de agentes que **entrevista você, planeja e constrói** uma aplicação ponta a ponta, provando o resultado com build e testes reais. Funciona no **Claude Code** e no **Antigravity**.

A skill é agnóstica de domínio e de stack: tipo de negócio, banco, linguagem e integrações vêm da entrevista inicial e ficam registrados em `.squad/stack.md`. Em projetos existentes, a equipe preserva a stack encontrada.

Ela responde **no seu idioma**: escreva o pedido em português, inglês, espanhol... (ou diga "em português") e a entrevista, os relatórios e os textos da interface do app seguem esse idioma. Os arquivos da skill ficam em inglês, que é o idioma oficial do repositório.

## Como usar

```text
/squad crie uma aplicação que <descreva o que ela faz>
```
ou, em linguagem natural: *"use a skill squad e crie ..."*.

1. **Descoberta de mercado:** o PM levanta 3 a 5 produtos que já fazem algo parecido e os blocos prontos (APIs oficiais, bibliotecas, templates) e propõe **construir × integrar × adaptar** para cada capacidade, com políticas, custos e riscos.
2. **Entrevista (uma rodada, até 8 perguntas):** stack (com recomendação **Next.js + Supabase no Vercel** quando não há preferência), **banco** (PostgreSQL, **Supabase**, SQL Server, SQLite), autenticação, integrações e credenciais, rotinas em segundo plano, deploy e nível de testes, mais até duas perguntas vindas da descoberta.
3. **Plano** curto (modo `lite`) ou mesa-redonda completa (modo `full`), já com as ameaças principais.
4. **Construção por fatias verticais** (dados → API → tela → teste), com RLS/autorização desde a primeira tabela e build/testes a cada fatia.
5. **Verificação real:** `run_checks` (lint, typecheck, build, testes), auditorias mecânicas, revisão no browser e **revisão independente** do crítico de código e do AppSec, em subagentes com contexto limpo.
6. **Deploy de preview** no Vercel/Supabase, só se você autorizar.
7. **Entrega:** como rodar, URL de preview, o que passou/falhou e **o que ainda depende de você**, com o passo a passo.

| Modo | Quando | Equipe | Fecha com |
|---|---|---|---|
| `lite` (padrão para "crie...") | App novo / feature grande | Arquiteto, Construtor, Verificador | `run_checks` + auditorias + crítico e AppSec independentes + tabela de aceite |
| `full` | Pedido explícito de mesa-redonda | 11 especialistas + 2 críticos + `@Finalizer` | Gate independente do Finalizer |
| `audit` | Projeto existente, sem construir | Especialistas relevantes | Roadmap priorizado |

## Instalação

Requer Python 3.10+ (instalador e MCP). Node 18+ só para as skills pesadas.

### Claude Code

```powershell
python install_claude.py --project C:\Projetos\MinhaApp     # .claude/ no projeto
python install_claude.py --global                           # ~/.claude/
python install_claude.py --project C:\Projetos\MinhaApp --with-heavy-skills   # + design-taste-frontend e playwright-cli (~60 MB)
```

O MCP é instalado mas **não registrado**. Para ativá-lo só no projeto que precisar, rode dentro dele:

```powershell
claude mcp add squad --scope local -- python <caminho>/.claude/mcp/server.py
```

### Antigravity

```powershell
.\install.ps1 -TargetProject "C:\Projetos\MinhaApp"   # ou -Global, ou sem argumentos para o menu
```
```bash
./install.sh "/caminho/do/projeto"   # ou --global
```

## Detalhes

A documentação completa (ferramentas do MCP, estrutura do repositório, créditos e licenças de terceiros) está no [README em inglês](README.md). Os caminhos e títulos `##` dentro de `.squad/` são um contrato fixo em inglês; o conteúdo dos relatórios fica no idioma do usuário, e os status são aceitos em inglês ou português (`APPROVED`/`APROVADO`, `REJECTED`/`REPROVADO`).

## Contribuindo

Issues e PRs são bem-vindos, em inglês ou português. Veja o [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

MIT. Materiais de terceiros mantêm suas licenças (veja "Credits" no [README](README.md)).
