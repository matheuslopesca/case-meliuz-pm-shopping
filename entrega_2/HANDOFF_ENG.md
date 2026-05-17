# Handoff para Engenharia — Login social InApp

> Material que o PM entrega para o tech lead conduzir refinamento técnico.
> Quebra a PRD em entregáveis pequenos, com critério de aceite e ordem de
> execução. É o que vai virar issues no Linear/Jira.

## 1. Visão arquitetural rápida

```
┌────────────────────────────────────────────────────────────┐
│                  In-App Browser (WebView principal)         │
│                                                             │
│   loja-parceira.com.br                                      │
│      └─ clica "Entrar com Google"                            │
│            │                                                │
│            ▼ (URL detectada)                                │
│   ┌──────────────────────────────────────────┐              │
│   │  OAuth Interceptor (Sub-WebView)         │              │
│   │  - accounts.google.com                   │              │
│   │  - usuario faz login                     │              │
│   │  - retorna ?code=…                        │              │
│   └──────────────────────────────────────────┘              │
│            │                                                │
│            ▼ (callback URL navegada)                        │
│   loja-parceira.com.br/auth/callback?code=…  ✅              │
│   (sessão estabelecida, WebView principal continua)         │
└────────────────────────────────────────────────────────────┘
```

## 2. Componentes a construir

| Componente | Plataforma | Owner sugerido |
|---|---|---|
| OAuth URL detector (regex + provider registry) | iOS + Android | Mobile Dev A |
| Sub-WebView wrapper com lifecycle | iOS + Android | Mobile Dev B |
| Callback URL listener + bridge para WebView principal | iOS + Android | Mobile Dev B |
| Feature flag `inapp_oauth_v1` | Backend Flags | Plataforma |
| Eventos `oauth_*` no SDK de tracking | iOS + Android | Mobile Dev A |
| Schema novo no BigQuery (atualização do ETL) | Data | Data Eng |
| Dashboard Looker | BI | Data Analyst |

## 3. Quebra em tasks (formato Linear/Jira)

### Epic: `[Shopping] OAuth interceptado no In-App Browser`

#### Story 1 — Discovery técnica (spike, 3 dias)

**Objetivo:** confirmar viabilidade técnica em iOS e Android antes de
comprometer o sprint.

Tasks:
- [ ] T1.1 — Reproduzir o fluxo atual: identificar exatamente como Google,
      Apple e Facebook tentam abrir externo a partir de WebView (iOS e
      Android). Documentar com vídeos e network logs.
- [ ] T1.2 — POC iOS: interceptar URL OAuth no `WKNavigationDelegate` e
      abrir em uma `WKWebView` filha. Validar que a callback retorna no
      caller.
- [ ] T1.3 — POC Android: interceptar em `WebViewClient.shouldOverrideUrlLoading`
      e abrir em uma `WebView` filha. Mesma validação.
- [ ] T1.4 — Documento de decisão: arquitetura final, dependências, riscos
      pendentes, custo estimado.

**Critério de aceite:** docs publicados + POC rodando para Google em ao menos
1 dos 2 SOs.

#### Story 2 — Feature flag e instrumentação base (3 dias)

- [ ] T2.1 — Criar flag `inapp_oauth_v1` no painel (default off).
- [ ] T2.2 — Implementar evento `oauth_intercepted` em iOS e Android (já
      dispara mesmo no fluxo controle, com `flag_variant`).
- [ ] T2.3 — Confirmar que evento chega ao BigQuery em < 30 min.
- [ ] T2.4 — Atualizar catálogo de dados (Looker/Metabase).

**Critério de aceite:** flag visível no painel; evento chegando em prod com
sample de 1% de usuários reais.

#### Story 3 — Interceptor Google OAuth (5 dias)

- [ ] T3.1 — iOS: implementar `WKNavigationDelegate.decidePolicyFor` para
      detectar `accounts.google.com/o/oauth2/`.
- [ ] T3.2 — iOS: abrir sub-WebView com a URL OAuth, esperar callback,
      retornar para WebView principal.
- [ ] T3.3 — Android: análogo a T3.1 e T3.2.
- [ ] T3.4 — Disparar eventos `oauth_started`, `oauth_completed`,
      `oauth_failed` com `latency_ms`.
- [ ] T3.5 — Testes unitários do detector (regex de URL OAuth).
- [ ] T3.6 — Testes de integração com credencial de teste do Google.

**Critério de aceite:** matriz QA Google × 5 parceiros × 2 SOs passa 100%.

#### Story 4 — Interceptor Apple OAuth (3 dias)

- [ ] T4.1 — Detector e sub-WebView (mesma lógica de T3, com URL
      `appleid.apple.com/auth/authorize`).
- [ ] T4.2 — Eventos.
- [ ] T4.3 — QA: 5 parceiros × 2 SOs.

**Critério de aceite:** matriz Apple passa 100%.

#### Story 5 — Interceptor Facebook OAuth (3 dias)

- [ ] T5.1 — Detector e sub-WebView (`facebook.com/dialog/oauth` e variantes).
- [ ] T5.2 — Eventos.
- [ ] T5.3 — QA: 5 parceiros × 2 SOs.

**Critério de aceite:** matriz Facebook passa 100%.

#### Story 6 — Fallback e edge cases (3 dias)

- [ ] T6.1 — Implementar `oauth_fallback_external` quando provedor não está
      na allowlist.
- [ ] T6.2 — Tratamento de timeout (> 30s sem callback): mostra mensagem
      in-line "tentar novamente".
- [ ] T6.3 — Tratamento de cancelamento do usuário no provedor.
- [ ] T6.4 — Killswitch via flag remota (60s para desligar em prod).

**Critério de aceite:** cenários de erro testados manualmente e
documentados.

#### Story 7 — Tracking URL final + ETL (2 dias)

- [ ] T7.1 — Append dos parâmetros `mz_test_inapp_oauth`, `mz_oauth_outcome`,
      `mz_oauth_latency_ms` no redirect final.
- [ ] T7.2 — Validar no ETL que esses campos chegam em
      `visit_url_metadata.tracking_url_params`.
- [ ] T7.3 — Sanity SQL: contagens batem entre eventos do app e visitas.

**Critério de aceite:** SQL de sanity passa com tolerância < 1%.

#### Story 8 — Dashboard de saúde + alertas (2 dias)

- [ ] T8.1 — Looker board: latência, taxa de sucesso por provedor, CVR e
      comissão/visita por flag_variant.
- [ ] T8.2 — Alerta PagerDuty: `oauth_failed_rate > 5%/hr`.
- [ ] T8.3 — Alerta PagerDuty: crash rate sessão com `oauth_*` > 0,1%/hr.

**Critério de aceite:** dashboard publicado e alertas testados com payload
sintético.

#### Story 9 — Rollout (2 semanas em paralelo)

- [ ] T9.1 — Shadow mode 1%: 48h, métricas estáveis.
- [ ] T9.2 — Beta 5%: 1 semana.
- [ ] T9.3 — 25%, 50%, 100% conforme a régua de saúde definida no plano de teste.

**Critério de aceite:** decisão final documentada (ship/iterate/kill).

## 4. Definition of done (DoD) — aplicável a TODAS as stories

- [ ] Código revisado (≥ 1 reviewer).
- [ ] Testes unitários cobrindo o caminho feliz e ≥ 2 cenários de erro.
- [ ] Lint + CI verdes.
- [ ] Documentação no `/docs` do mobile (markdown).
- [ ] Evento(s) instrumentado(s) chegando ao BigQuery.
- [ ] PR vinculado ao ticket do Linear/Jira.

## 5. Acordos de comunicação

- Standup diário com PM presente (15 min).
- Demo semanal toda quinta-feira (PM + Eng + Design + QA).
- Bloqueios passam direto no canal Slack `#shopping-test-D`, sem esperar reunião.
- PR de QA usa template com checklist da seção 2 deste handoff.

## 6. Estimativa total e dependências

- Soma das stories: ~26 dias úteis de eng.
- Em paralelo com QA e instrumentação: **~5-6 sprints** (squad de 2 devs).
- Dependências externas que travariam:
  - Aprovação jurídica do tratamento de credencial OAuth.
  - Liberação do Data Eng para atualizar ETL (1 dia).
  - Conta de teste em cada provedor (Google/Apple/Facebook).
