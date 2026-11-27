# Padrões de integração por categoria

Referência genérica (não é domain pack): vale para qualquer produto que precise de uma destas capacidades. Detalhes de um serviço específico vêm sempre da **documentação oficial**, pesquisada pelo `@PM` com URL e data de acesso; nada aqui substitui essa pesquisa.

Regra comum a todas: interface própria no código (ex.: `MessageSender`, `PriceSource`, `PaymentProvider`) + um conector por serviço, atrás de configuração. Sem credencial, o app sobe e mostra estado de "configuração pendente"; nunca dado inventado.

## 1. Canais de mensagem (chat, e-mail, SMS, push)

- Use o canal **oficial** de API do provedor. Automação não oficial (cliente web emulado, sessão de app pessoal) costuma violar termos de uso e leva a bloqueio de número/conta: só com aceite explícito do usuário, registrado em `.squad/stack.md` como risco alto.
- Levante: aprovação de conta/empresa, verificação de número ou domínio, **modelos (templates) pré-aprovados** para mensagens iniciadas pela empresa, janela de atendimento, exigência de **opt-in** registrado, limites por destinatário e por dia, custo por mensagem/conversa.
- Implemente: registro de consentimento (quem, quando, como), descadastro (opt-out) que funciona na hora, fila com retentativa e backoff, deduplicação por chave de idempotência, log de status de entrega via webhook.
- Teste: conector com sandbox/número de teste do provedor; sem sandbox, teste a interface com um conector fake **só em teste**.

## 2. Coleta de dados de terceiros (preços, catálogos, cotações, conteúdo)

- Ordem de preferência: **API oficial ou de parceiros/afiliados** → feed oficial (XML/CSV/JSON) → coleta de páginas públicas.
- Coleta de páginas só quando os termos permitirem: respeite `robots.txt`, identifique o cliente (User-Agent genérico do produto), limite de taxa conservador, cache, horário de baixo tráfego. Nunca contorne login, CAPTCHA, paywall ou bloqueio. Registre a base legal/termos consultados na pesquisa do PM.
- Implemente: normalização em um modelo próprio (fonte, id externo, valor, moeda, coletado_em), histórico em vez de sobrescrever quando o produto depende de variação, detecção de quebra (fonte mudou de formato → alerta, não dado errado).
- Teste: fixtures **gravadas** de respostas reais em teste; um teste de contrato opcional contra a fonte real, fora da suíte padrão.

## 3. Tarefas agendadas e em segundo plano

- Escolha conforme o host: cron do provedor de deploy (ex.: Vercel Cron), agendador do banco (ex.: `pg_cron` no Supabase), funções agendadas (ex.: Supabase Edge Functions com agendamento), worker próprio com fila. Verifique na doc oficial os **limites do plano** (frequência mínima, tempo máximo de execução).
- Todo job é **idempotente** (rodar duas vezes não duplica efeito), tem trava contra execução concorrente, registra início/fim/erro e expõe "última execução" na UI administrativa.
- Rota HTTP chamada pelo cron é protegida (segredo compartilhado no header, comparado em tempo constante); nunca pública.
- Trabalho longo é quebrado em lotes ou enviado a uma fila; não dependa de uma função serverless ficar viva além do limite.

## 4. Webhooks recebidos

- Valide **assinatura** (HMAC ou mecanismo do provedor) antes de qualquer efeito; rejeite fora da janela de tempo.
- Responda rápido (2xx) e processe de forma assíncrona; deduplique pelo id do evento.
- Webhook não usa a sessão do usuário: a autorização é a assinatura.

## 5. Pagamentos e cobrança

- Checkout hospedado pelo provedor sempre que possível (reduz escopo de conformidade). Nunca armazene dados de cartão.
- Estado da assinatura/pedido vem do **webhook** do provedor, não do redirecionamento do browser.
- Ambiente de teste do provedor no desenvolvimento; chaves de produção só no servidor.

## 6. IA/LLM dentro do produto

- Chave de API só no servidor; limite de uso por usuário; timeout e mensagem de erro amigável.
- Entrada do usuário nunca vira instrução de sistema; saída do modelo é tratada como dado não confiável (sem executar, sem renderizar HTML cru).
- Registre custo estimado por operação no roadmap.

## O que registrar

Para cada integração, no `pesquisa-de-campo.md` do PM: link da doc oficial, autenticação, limites, aprovações, custos, políticas, sandbox. No roadmap: o que depende do usuário (conta, aprovação, chave) com o passo a passo para obter.
