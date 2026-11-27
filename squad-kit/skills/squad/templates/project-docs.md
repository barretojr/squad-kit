# Estrutura de documentação do produto

Crie esta pasta na raiz do projeto, ao lado do `.slnx`/`.sln` ou `package.json` quando houver. Ela guarda relatórios de agentes e contexto de trabalho; não é projeto compilável.

```text
.squad/
├── README.md
├── stack.md                       # Decisões da entrevista (stack, deploy, riscos aceitos)
├── produto/
│   ├── descoberta.md              # PM: equivalentes no mercado e construir × integrar
│   └── pesquisa-de-campo.md       # PM: usuários, APIs/integrações e fontes
├── coordenacao/
│   ├── coord.md                   # Coord: escopo, contratos, integrações, decisões
│   └── roadmap.md                 # Único backlog priorizado e rastreável
├── design/
│   ├── direcao-visual-e-marca.md  # Designer: marca/logo, UX e sistema visual
│   ├── design-system.md           # Design system: contrato e tokens
│   └── DESIGN.md                  # Design system agent: contrato visual para o código
├── dados/dba.md                   # Modelo, integridade e migrações planejadas/feitas
├── backend/backend.md             # APIs, autenticação e regras de domínio
├── frontend/frontend.md           # Telas, contratos consumidos e integração real
├── frontend/revisao-visual.md     # UI reviewer: browser, viewports e evidências
├── seguranca/appsec.md            # Ameaças, controles e testes de segurança
├── qualidade/qa.md                # Critérios, matriz e evidência real de testes
├── operacao/devops.md             # Ambiente, pipeline e operação
└── evidencias/                    # run_checks.md, deploy.md, screenshots do frontend
```

Cada arquivo de agente contém: status e data; contexto/evidências; decisões e hipóteses; o que precisa ser feito; plano e dependências; o que foi feito (na fase de planejamento: nenhuma implementação de produto); validação com comandos e resultado real; pendências e links para fontes/IDs do roadmap. O agente dono atualiza o próprio relatório; Coord mantém o roadmap e o índice.

Nunca grave segredos, tokens, credenciais, payloads pessoais ou dados de cliente sem anonimização nesses documentos. Não duplique pesquisa extensa: Coord referencia a pesquisa do PM e registra somente as decisões que dela decorrem.

`.squad/qualidade/finalizer.md` is the independent completion gate. It has one checklist row per required final check and records status plus evidence. It is not a substitute for QA, frontend review, or either code critic.
