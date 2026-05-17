# PRD — Login social do parceiro dentro do In-App Browser

> **Iniciativa:** Habilitar login social do parceiro (Google/Apple/Facebook)
> **dentro** do In-App Browser, eliminando a necessidade de saída para
> navegador externo.
> **Squad:** Shopping
> **Status:** Discovery → pronto para refinamento técnico
> **PM:** Matheus Carvalho
> **Última atualização:** 2026-05-17
> **Decisão buscada:** aprovação para entrar em sprint nas próximas 2 semanas.

---

## 1. Sumário executivo

- **O que vamos fazer:** entregar uma camada de **OAuth interceptado**
  no In-App Browser que detecta tentativas de login social do site parceiro,
  conduz o fluxo OAuth diretamente dentro do WebView (sem abrir o navegador
  externo) e devolve o token para a página da loja, mantendo a sessão e a
  atribuição de cashback.
- **Para quem:** usuários do app Méliuz que iniciam compra em lojas parceiras
  que oferecem login social como caminho preferencial (Magalu, Amazon, Shein,
  etc.).
- **Por que agora:** o teste A/B/C do In-App Browser mostrou que **toda saída
  para navegador externo via login social destrói receita** (comissão por
  visita cai para R$ 1,09–R$ 1,66 vs R$ 5,56 do controle). Esse é o **maior
  vazamento de comissão atribuído a um único trigger** identificado no
  experimento.
- **Resultado esperado:** recuperar **+R$ 3,90 a +R$ 4,50 de comissão por
  visita** nas saídas hoje rotuladas como `utm_term=login` (3.535 + 3.461 =
  ~7.000 visitas no período de ~6 semanas do teste). Anualizando o mesmo
  volume e os mesmos 6 parceiros do teste, a recuperação é de **~R$ 250 k /
  ano**; estendendo para o top 20 parceiros do catálogo (cobertura ~80% do
  GMV Shopping), a estimativa cresce para **~R$ 1 a 2 M / ano** em comissão
  recuperada (a confirmar com sizing detalhado pelo time de Data).

---

## 2. Contexto de negócio

A jornada Shopping começa no app Méliuz e termina, na maioria das vezes, no
ambiente da loja parceira. A Méliuz só recebe comissão se a atribuição se
mantiver íntegra até a venda. Em testes de funil de saída, **a entrega do
In-App Browser default (variante A do teste anterior) é o melhor desempenho
econômico** (R$ 5,56 de comissão por visita).

O ponto fraco do In-App Browser hoje é o login social: muitos parceiros
disparam "abrir no Safari/Chrome" quando o usuário clica em "Entrar com
Google". Isso quebra a sessão dentro do app, força o usuário a re-navegar
até a página da compra, e — quando o usuário compra — a atribuição
Méliuz já se perdeu no caminho.

Os números do teste anterior (Entrega 1) tornam isso quantitativo:

| Tipo de saída | Visitas | CVR | Comissão/visita |
|---|---:|---:|---:|
| InApp default (A) | 377.716 | 12,87% | R$ 5,56 |
| InApp B (com header) | 376.350 | 12,64% | R$ 5,29 |
| InApp C (com config) | 376.513 | 12,77% | R$ 5,55 |
| Externo via Header | 5.872 | 11,60% | R$ 2,98 |
| Externo via Config | 3.896 | 11,81% | R$ 4,59 |
| **Externo via Login (B+C)** | **6.996** | **10,7%** | **R$ 1,37 médio** |

A perda de comissão por visita no login externo (R$ 1,37 vs R$ 5,56) é
**−75%**. Se eliminarmos essa saída e mantivermos esses usuários dentro do
In-App Browser, recuperamos quase toda essa diferença.

---

## 3. Problema e oportunidade

### Problema

Quando o usuário clica em "Entrar com Google/Apple/Facebook" no site do
parceiro dentro do In-App Browser, dois cenários ocorrem:

1. **Parceiro abre uma janela de OAuth no navegador externo** (Safari/Chrome)
   automaticamente — o usuário "perde" o app Méliuz.
2. **Parceiro tenta abrir um popup que o WebView bloqueia** — o usuário acha
   que o site quebrou.

Em ambos os casos, a Méliuz é prejudicada: ou o usuário vai para outro
ambiente e a atribuição se perde, ou o usuário desiste.

### Oportunidade

Implementar um **OAuth interceptor** no WebView que:

- Intercepta as chamadas `accounts.google.com`, `appleid.apple.com`,
  `facebook.com/dialog/oauth` antes que elas tentem abrir externo.
- Conduz o fluxo OAuth dentro de uma sub-WebView do próprio In-App Browser.
- Captura o `code` ou `id_token` retornado.
- Devolve para a página da loja com a callback URL esperada.

Resultado: o usuário faz login social sem nunca sair do app Méliuz.

### Por que priorizar agora

- **Maior fonte isolada de perda de comissão** documentada no último teste.
- Solução é técnica, escopo bem definido, não depende de roadmap dos parceiros.
- Já temos a infra de WebView; estamos apenas instrumentando-a melhor.
- Compete com pouca coisa no roadmap (a discussão de "saída para externo"
  está exaurida).

---

## 4. Hipótese

> **Se** interceptarmos o fluxo de login social dentro do In-App Browser
> **então** a comissão por visita das jornadas que envolvem login subirá de
> R$ 1,37 para o nível das jornadas sem login externo (R$ 5,50+)
> **porque** o usuário deixa de sair do app, mantendo a sessão e a atribuição
> Méliuz íntegras.

---

## 5. Solução proposta

### Visão

Quando a página do parceiro disparar OAuth, o In-App Browser:

1. Detecta a URL OAuth no `onShouldStart`/`webRequest`.
2. Em vez de delegar para o sistema operacional, abre o fluxo OAuth em uma
   sub-WebView dentro do app Méliuz.
3. Aguarda o redirect final (`https://lojaparceiro.com.br/auth/callback?code=…`).
4. Devolve o controle para a WebView principal, navegando para a callback URL.
5. Não muda nada para o usuário visualmente (mesmo header, mesmo flow).

### Mockups

> A definir no Figma. Estilo: idêntico ao In-App Browser atual; única adição
> é uma faixa fina de "Login seguro via Méliuz" no topo da sub-WebView,
> reforçando confiança.

### Comportamento por estado

| Estado | Comportamento |
|---|---|
| Login bem-sucedido | Volta para a página da loja com sessão autenticada. Sem mudança visual no app. |
| Usuário cancela OAuth | Volta para a página de checkout do parceiro (estado pré-login). |
| OAuth falha (timeout, erro do provedor) | Mostra mensagem in-line e oferece "tentar de novo" ou "usar e-mail". Não sai do app. |
| Provedor exige 2FA via SMS | Continua no In-App Browser (input SMS no próprio fluxo OAuth). |
| Parceiro usa um provedor não suportado | Fallback graceful: abrir externo *só nesse caso*, com tracking dedicado para mensurar volume. |

---

## 6. Escopo do MVP

### Dentro do escopo

- Interceptar OAuth de **3 provedores**: Google, Apple, Facebook.
- Interceptar para os **top 20 parceiros por GMV** (cobertura > 80% do volume).
- Plataformas: **iOS e Android** (a mesma feature flag liga os dois).
- Tracking completo: eventos novos `oauth_intercepted`, `oauth_completed`,
  `oauth_failed`, com propriedade `provider`, `partner_id`, `latency_ms`.
- Feature flag de rollout gradual (0% → 5% → 25% → 50% → 100%).

### Fora do escopo (próximas iterações)

- Provedores adicionais (Twitter, LinkedIn, Microsoft).
- Long tail de parceiros (do 21° em diante; iteração 2).
- "Lembrar-me" cross-partner (single sign-on dentro do Méliuz) — feature
  separada, alto risco regulatório.
- Login direto via e-mail/senha (não é OAuth, escopo diferente).

---

## 7. Critérios de aceite

- [ ] **CA-1.** Quando o usuário clica em "Entrar com Google" em um dos top 20
      parceiros, a sub-WebView OAuth abre dentro do app Méliuz (sem chamar
      `openURL:` no iOS ou `Intent.ACTION_VIEW` no Android).
- [ ] **CA-2.** Após login bem-sucedido, a página do parceiro carrega autenticada
      e a `visit_id` Méliuz é preservada na sessão.
- [ ] **CA-3.** O evento `oauth_intercepted` dispara em até 200ms após a
      detecção da URL OAuth, com 100% de cobertura dos casos rastreados em QA.
- [ ] **CA-4.** Para qualquer um dos 3 provedores, o tempo p95 entre clique e
      retorno autenticado é ≤ 6s (igual ou melhor que o fluxo externo atual).
- [ ] **CA-5.** Se o fluxo OAuth falhar, o usuário vê uma mensagem in-line
      (sem crash, sem app fechar) com opção "Tentar de novo" ou "Usar e-mail".
- [ ] **CA-6.** A feature flag `inapp_oauth_v1` controla 100% do comportamento
      e permite desligar em 60s via dashboard de flags.
- [ ] **CA-7.** A flag ligada não impacta a CVR de visitas que **não envolvem
      login social** (guardrail).

---

## 8. Instrumentação

### Novos eventos

| Evento | Propriedades | Quando dispara |
|---|---|---|
| `oauth_intercepted` | `partner_id`, `provider`, `flag_variant`, `app_version`, `device_os` | Detecção da URL OAuth na WebView principal |
| `oauth_started` | (idem) + `started_at` | Sub-WebView OAuth abre |
| `oauth_completed` | (idem) + `latency_ms`, `outcome="success"` | Callback URL recebida com `code` válido |
| `oauth_failed` | (idem) + `error_code`, `error_message` | Sub-WebView fecha sem callback ou com erro |
| `oauth_fallback_external` | (idem) + `reason` | Provedor não suportado → abertura externa controlada |

### UTMs e `mz_*`

Saídas que envolvam login (sucesso ou falha) carregam novos parâmetros na
tracking URL final que vai para o parceiro:

```
utm_content=INAPP_OAUTH
utm_term=<google|apple|facebook>
mz_test_inapp_oauth=<a|b>           // a=controle (saída externa atual), b=interceptado
mz_oauth_outcome=<success|fail|fallback>
mz_oauth_latency_ms=<ms>
```

### Exemplo de tracking URL

```
https://www.meliuz.com.br/redirecionar
  ?utm_source=app
  &utm_medium=ios
  &utm_content=INAPP_OAUTH
  &utm_term=google
  &user_id=USER_123
  &mz_test_inapp_oauth=b
  &mz_oauth_outcome=success
  &mz_oauth_latency_ms=2480
  &mz_redirect=inapp
```

### Validação antes do go-live

Antes de habilitar para usuário real:

1. **QA manual cobrindo matriz parceiro × provedor × SO.** 20 parceiros × 3
   provedores × 2 SOs = 120 cenários. Checklist binário pass/fail.
2. **Smoke test em pré-produção** com tráfego sintético (script automatizado
   navega, clica em "Entrar com Google", confere os 5 eventos esperados).
3. **Dry-run em 1% de usuários** por 24h, com a flag em "shadow mode" (o
   código roda, mas o resultado não é aplicado). Permite medir latência e
   taxa de erro real sem afetar a base.
4. **Dashboard em tempo real** durante o rollout, com:
   - Latência p50/p95/p99 do `oauth_completed`.
   - Taxa de `oauth_failed` por provedor.
   - CVR e comissão/visita das visitas marcadas com flag `b`.
   - Alerta automático: se `oauth_failed` > 5% por hora, killswitch via flag.

---

## 9. Métricas de sucesso e guardrails

### Métrica primária

**Comissão por visita** das visitas que envolvem login social
(`utm_term IN ('google','apple','facebook')`).

- **Critério de sucesso (ship 100%):** lift ≥ +50% relativo (cenário base:
  R$ 1,37 → R$ 2,06+) com IC95% inteiramente positivo.
- **Critério de iteração:** lift entre +10% e +50% — manter teste rodando
  por mais 2 semanas para estabilizar.
- **Critério de kill:** lift ≤ 0 ou IC abrange zero após 30 dias com volume
  alvo atingido.

### Métricas secundárias

- CVR das visitas que envolvem login social.
- Latência p95 do OAuth completo.
- Taxa de fallback externo (deveria ser < 10% no MVP).
- Taxa de erro OAuth por provedor.

### Guardrails (devem se manter neutros ou melhorar)

- CVR geral do Shopping (todas as visitas, não só login).
- Tempo médio de carregamento da página do parceiro.
- Taxa de crash do app em sessões com `oauth_intercepted`.
- NPS / CSAT do Shopping (mensal).

---

## 10. Riscos, dependências e fora de escopo

### Riscos técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Provedor OAuth atualiza o fluxo e quebra o intercept | Média | Alto | Monitorar `oauth_failed` por provedor; alerta + killswitch automático |
| Parceiro detecta WebView e bloqueia OAuth | Baixa | Alto | Usar user-agent realista; ter fallback externo bem instrumentado |
| Latência sub-WebView > fluxo externo | Baixa | Médio | Lazy load do iframe OAuth; warm-up de cookies |
| Vazamento de token entre parceiros | Muito baixa | Crítico | Sub-WebView isolada por parceiro, sem cookie sharing |

### Riscos regulatórios / jurídicos

- **LGPD / política do provedor:** confirmar com jurídico que interceptar
  OAuth e processar o `code` dentro do app está coberto pelo ToS do
  Google/Apple/Facebook. Apple já restringe em alguns SDKs.
- **Confiança do usuário:** mostrar de forma clara que ele está fazendo
  login com o provedor X (faixa visual no topo).

### Dependências

- Time de **Plataforma Mobile**: dono do WebView e do gerenciador de
  feature flags.
- Time de **Data**: novos eventos no schema, validação no BI.
- Time de **Suporte/CX**: script para casos de "não consigo logar".
- Time **Jurídico**: review da política de tratamento de credenciais.

### Fora de escopo

Já listado na seção 6.

---

## 11. Roadmap & milestones

| Fase | Entregável | Dono | Duração estimada |
|---|---|---|---|
| Discovery técnica | Spike em iOS + Android para validar viabilidade | Mobile Lead | 1 semana |
| Design | Mockups Figma + faixa de "login seguro" | Designer | 1 semana |
| Build | Implementação dos 3 provedores + instrumentação + flag | Mobile (2 devs) | 3 semanas |
| QA | Matriz 20 × 3 × 2 + smoke test automatizado | QA + PM | 1 semana |
| Shadow mode (1%) | 24-48h em produção, métricas de saúde | PM + Data | 2 dias |
| Beta (5%) | 1 semana com monitoramento | PM | 1 semana |
| Rollout gradual | 5% → 25% → 50% → 100%, com check a cada degrau | PM | 2 semanas |
| Pós-lançamento | Análise final + post-mortem + decisão sobre próximos parceiros | PM | 1 semana |

**Total: ~9 semanas do kickoff ao 100%.**

---

## 12. Apêndice

- Análise que originou esta PRD: `/repo/entrega_1/RELATORIO.md` (seção 5.1
  "LOGIN é universalmente ruim").
- Plano de instrumentação detalhado: `/repo/entrega_2/INSTRUMENTACAO.md`.
- Plano de teste A/B: `/repo/entrega_2/PLANO_DE_TESTE.md`.
- Quebra em tasks para engenharia: `/repo/entrega_2/HANDOFF_ENG.md`.
