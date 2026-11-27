---
description: Atalho para iniciar o squad em modo full (mesa-redonda) antes de executar itens do roadmap.
---

# Alias `/teamwork`

Demanda do usuário: `$ARGUMENTS`

Encaminhe a demanda para `skills/squad/SKILL.md` no **modo `full`** e siga integralmente o fluxo da skill: descoberta, entrevista, fan-out dos especialistas, relatórios em `.squad/`, roadmap e escolha de itens pelo usuário antes de qualquer implementação. Não mantenha um workflow paralelo aqui.

No fim da execução, a revisão independente (críticos + `appsec`) e o `@Finalizer` são obrigatórios; o Finalizer grava `qualidade/finalizer.md` e só aprova com `validate_completion_checklist` retornando `valid: true`. Sem evidência linha a linha não há aprovação final; lacunas viram tarefas no roadmap.
