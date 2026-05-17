# Plano de teste — Login social InApp (Teste D)

> Documento companion da PRD. Define como vamos medir o sucesso ou fracasso
> do OAuth interceptado.

## 1. Desenho do teste

| Item | Definição |
|---|---|
| **Tipo** | A/B (não A/B/C, porque o teste anterior já matou as variantes intermediárias). |
| **Unidade de aleatorização** | `customer_id` — para reduzir contaminação cruzada de 0,97% observada no teste anterior. |
| **Alocação** | 50/50, dentro da população elegível. |
| **População elegível** | Usuários que tentaram login social em algum dos top 20 parceiros nos últimos 90 dias (ou que vierem a tentar no período do teste). |
| **Tratamento (B)** | OAuth interceptado dentro do InApp Browser. |
| **Controle (A)** | Fluxo atual (abre navegador externo). |
| **Métrica primária** | Comissão por visita de visitas elegíveis. |
| **Período mínimo** | 4 semanas (2 ciclos semanais) ou até 10.000 conversões por braço — o que vier primeiro. |

## 2. Tamanho de amostra (sanity)

Cenário base: comissão por visita do controle ≈ R$ 1,37. Para detectar um
lift de +50% relativo (passar para R$ 2,06) com 80% de poder e α=0,05
two-sided, considerando a alta variância da métrica (presença de outliers de
GMV alto), estimo via simulação:

- N por braço ≈ **35.000 visitas elegíveis**.
- Volume mensal observado no teste anterior: ~3.500 visitas elegíveis (login)
  por mês.
- **Tempo estimado para o teste rodar:** ~10 semanas. Aceitável dado o
  upside.

Se quisermos encurtar:
- Expandir para top 40 parceiros (dobra elegíveis).
- Considerar análise sequencial (mSPRT) com guardrails de Type-I.

## 3. Cronograma

| Semana | Atividade |
|---|---|
| -2 a -1 | Implementação + QA + shadow mode em 1% |
| 0 | Liga em 5% (sanity check de saúde) |
| 1 | Sobe para 25% (se health OK) |
| 2-5 | 50% A / 50% B (coleta principal) |
| 6 | Decisão preliminar (early peek com correção alpha) |
| 7-8 | Continuação se "iterate", consolidação se "ship/kill" |
| 9 | Análise final e post-mortem |

## 4. Critérios de decisão

### Ship (rollout para 100%)

Todas as condições simultaneamente:

- **Métrica primária** (comissão/visita): lift relativo ≥ +50%, com IC95%
  inteiramente positivo.
- **Guardrail 1** (CVR geral Shopping, todas as visitas): IC inclui zero ou
  é positivo. Não pode cair.
- **Guardrail 2** (latência p95 OAuth): ≤ 6s.
- **Guardrail 3** (taxa de crash app): sem regressão estatística (IC inclui
  zero).
- **Guardrail 4** (NPS Shopping, mensal): IC inclui zero ou é positivo.

### Iterate (manter teste rodando)

Sinal misto: lift positivo mas com IC abrangendo zero, ou métrica primária
positiva mas guardrail técnico marginal. Coletar mais 2 semanas.

### Kill (desligar e arquivar)

- Métrica primária neutra ou negativa após período completo.
- OU regressão clara em qualquer guardrail.

### Inconclusive

Insuficiência de amostra após 12 semanas. Decisão: pivotar para outro teste
(ex: focar em um único parceiro de alto volume).

## 5. Análises secundárias planejadas

Para serem rodadas **junto** com a análise final (não cherry-picking depois):

1. Lift por **provedor** (Google/Apple/Facebook) — algum domina o ganho?
2. Lift por **SO** (iOS x Android) — ITP no iOS pode amplificar diferença.
3. Lift por **top 5 parceiros** — quem ganha mais? Quem rejeita o intercept?
4. Funil pós-login: o usuário que logou InApp realmente completa a compra?

Todas com o mesmo método estatístico do principal (z-test ou bootstrap).

## 6. Anti-fraude e qualidade do dado

- Não contar como conversão visitas com `oauth_failed` seguido de compra em
  janela > 1h (provavelmente compraria de qualquer forma).
- Detectar bots: filtrar visitas com latência OAuth < 200ms (impossível
  humanamente).
- Validar que `customer_id` está consistente entre `oauth_*` e `visits`.

## 7. Plano de comunicação

| Audiência | Quando | Como |
|---|---|---|
| Squad Shopping | Diário | Standup |
| Head de Produto | Semanal | Slack thread `#shopping-test-D` |
| Liderança | Mid-test (semana 4) e final | Deck + dashboard |
| Empresa | Final | Post-mortem aberto na wiki |

## 8. O que faremos com o aprendizado

Independente do resultado:

- **Se ship:** expandir para top 40 parceiros em 60 dias; depois long tail.
- **Se iterate:** experimentar OAuth com SDK nativo de provedor (em vez de
  WebView).
- **Se kill:** investigar por que login externo converte tão pouco — pode
  ser problema de UX (usuário desiste no caminho de volta), não de
  atribuição. Mudaria a hipótese central.
