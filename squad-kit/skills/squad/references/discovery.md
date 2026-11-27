# Descoberta de mercado (antes da entrevista)

Objetivo: antes de perguntar a stack, saber **o que já existe** que resolve o pedido, inteiro ou em partes, para que a entrevista ofereça escolhas informadas (construir, integrar ou adaptar) e o plano não reinvente o que já é produto, biblioteca ou API.

Dono: `@PM` (no `lite`, o Arquiteto). Saída: `.squad/produto/descoberta.md`. Duração-alvo: curta; é um reconhecimento, não um estudo de mercado.

## Quando rodar

- Sempre em greenfield com pedido de "crie/construa…".
- Em brownfield, só para a feature nova pedida (não para o produto inteiro).
- Pule se o usuário disser explicitamente "não pesquise" ou se `.squad/produto/descoberta.md` já existir e cobrir o pedido.
- Sem acesso à web: registre "descoberta pendente: sem acesso à web", não invente produtos nem URLs, e siga para a entrevista.

## O que levantar (fontes primárias, URL direta e data de acesso)

1. **Produtos equivalentes (3 a 5):** quem já faz isso, para quem, modelo de preço, o que fazem bem e o que os usuários reclamam (só se houver fonte pública). Serve para recorte de escopo e diferencial, não para copiar.
2. **Blocos reutilizáveis:** para cada capacidade central do pedido, o que existe pronto:
   - API/serviço oficial (ex.: um canal de mensagens, um provedor de pagamentos, uma fonte de dados);
   - biblioteca/SDK open source mantido (licença, última release, estrelas não são critério sozinhas);
   - template/starter oficial da stack provável.
3. **Restrições que mudam a arquitetura:** termos de uso, políticas da plataforma, aprovações de conta, custos por uso, limites de taxa, exigência de opt-in/consentimento, proibição de automação não oficial. Veja `references/integrations.md`.
4. **Riscos de dependência:** API não oficial, serviço sem SLA, preço que escala com uso, lock-in.

## Decisão construir × integrar × adaptar

Para cada capacidade central, registre uma linha:

| Capacidade | Opções encontradas | Recomendação | Motivo | Custo/risco |
|---|---|---|---|---|
| [ex.: envio de mensagens] | [API oficial X; biblioteca não oficial Y] | integrar X | [política, estabilidade] | [custo por mensagem; aprovação de conta] |

Regras:

- Prefira **API oficial** a automação não oficial; se a única opção viável for não oficial, marque como risco alto e leve à entrevista.
- Prefira **integrar** quando o bloco não é o diferencial do produto; **construa** o que é diferencial.
- Nunca recomende contornar termos de uso, CAPTCHA, paywall ou bloqueio técnico.

## Como alimenta a entrevista

Leve no máximo **duas** perguntas da descoberta para o bloco da entrevista, só quando a resposta mudar a arquitetura. Exemplos de formato:

- "Para [capacidade], o caminho oficial é [X] (exige [aprovação/custo]). Usar X, usar [alternativa] ciente do risco, ou deixar fora do MVP?"
- "Já existe [produto] que faz [parte]. Integrar com ele ou construir próprio?"

Mostre ao usuário um resumo de 3 a 5 linhas da descoberta junto com as perguntas.

## Modelo de `.squad/produto/descoberta.md`

```markdown
# Descoberta — [pedido em uma frase]

- **Data:** [AAAA-MM-DD] · **Acesso à web:** [sim/não]

## Produtos equivalentes
| Produto | Para quem | Preço | Pontos fortes | Lacunas observadas | Fonte (URL, data) |
|---|---|---|---|---|---|

## Blocos reutilizáveis e decisão
| Capacidade | Opções | Recomendação | Motivo | Custo/risco |
|---|---|---|---|---|

## Restrições que afetam a arquitetura
- [política/limite/aprovação — fonte]

## Diferencial proposto
- [o que este produto faz que os equivalentes não fazem, ou "nenhum: é uma versão própria"]

## Perguntas levadas para a entrevista
1. [...]
```

Fatos, inferências e recomendações ficam separados. Nada de números de mercado sem fonte.
