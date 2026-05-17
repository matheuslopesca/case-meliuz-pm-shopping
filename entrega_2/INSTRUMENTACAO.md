# Plano de instrumentação — Login social InApp

> Documento companion da PRD. Define eventos, propriedades, UTMs, `mz_*` e o
> processo de validação antes do lançamento.

## 1. Princípios

1. **Tudo que decidirmos pelo número, instrumentamos antes.** Se não tem
   evento, não tem decisão.
2. **Evento por estado, não por tela.** `oauth_started` ≠ `oauth_completed` ≠
   `oauth_failed`. Cada estado tem seu evento próprio.
3. **Sample 100% no MVP.** Estamos aprendendo; sampling vem depois.
4. **Reuso da convenção `mz_*`.** Não criamos novas chaves se uma `mz_*`
   existente serve.

## 2. Eventos do app (Amplitude / BigQuery)

| Nome | Tipo | Quando dispara |
|---|---|---|
| `oauth_intercepted` | app | App detecta tentativa de OAuth na WebView principal |
| `oauth_started` | app | Sub-WebView abre com a URL OAuth |
| `oauth_completed` | app | Callback URL recebida com `code`/`id_token` válido |
| `oauth_failed` | app | Sub-WebView fecha sem callback ou retorna erro |
| `oauth_fallback_external` | app | Provedor/parceiro não suportado, abrimos externo |

## 3. Propriedades padrão (todos os eventos)

| Propriedade | Tipo | Exemplo |
|---|---|---|
| `partner_id` | string | "P042" |
| `provider` | enum | "google" \| "apple" \| "facebook" |
| `flag_variant` | enum | "a" (controle, externo) \| "b" (intercept InApp) |
| `app_version` | string | "8.42.1" |
| `device_os` | enum | "ios" \| "android" |
| `os_version` | string | "iOS 18.2" \| "Android 14" |
| `visit_id` | string | hash da visit original |
| `started_at` | timestamp ISO | "2026-06-12T14:21:11Z" |

Eventos específicos adicionam:

- `oauth_completed`: `latency_ms` (int), `outcome="success"`.
- `oauth_failed`: `error_code`, `error_message`, `latency_ms`.
- `oauth_fallback_external`: `reason` (enum: `unsupported_provider`,
  `unsupported_partner`, `webview_compat_error`).

## 4. UTMs e `mz_*` na tracking URL

Inseridos pelo app no redirect final que vai para a Méliuz:

```
utm_content=INAPP_OAUTH
utm_term=<google|apple|facebook>
mz_test_inapp_oauth=<a|b>
mz_oauth_outcome=<success|fail|fallback>
mz_oauth_latency_ms=<int>
mz_redirect=inapp
```

Quando o fluxo legacy é usado (`flag_variant=a`), os parâmetros são:

```
utm_content=EXTERNAL_BROWSER_MODAL
utm_term=login
mz_test_inapp_oauth=a
mz_redirect=browserdefault
```

Isso mantém compatibilidade com o ETL existente e permite cruzar com o
dataset do teste anterior.

## 5. Esquema da tabela `visit_url_metadata` (delta)

Não precisa de mudança de schema — `tracking_url_params` é JSON livre. Apenas
documentamos no catálogo de dados que as chaves `mz_test_inapp_oauth`,
`mz_oauth_outcome` e `mz_oauth_latency_ms` agora podem aparecer.

## 6. Como validar antes do go-live

### 6.1. Smoke test automatizado

Script Detox/XCUITest que:

1. Abre o app em ambiente de staging.
2. Navega para uma loja parceira com OAuth habilitado.
3. Clica em "Entrar com Google".
4. Confere se os eventos `oauth_intercepted` e `oauth_started` foram
   disparados nos primeiros 500ms.
5. Completa o fluxo com credencial de teste.
6. Confere se `oauth_completed` disparou e se a tracking URL final tem os
   parâmetros corretos.
7. Repete para Apple e Facebook.

### 6.2. Matriz manual (QA)

| Parceiro | Provedor | iOS | Android |
|---|---|---|---|
| P001 | Google | ✅/❌ | ✅/❌ |
| P001 | Apple | ✅/❌ | ✅/❌ |
| P001 | Facebook | ✅/❌ | ✅/❌ |
| … | … | … | … |
| P020 | Facebook | ✅/❌ | ✅/❌ |

Critério de pass: todos os 5 eventos disparam, callback retorna autenticada,
nenhum crash.

### 6.3. Shadow mode em produção

Antes de habilitar para usuário, ligar a flag em "shadow":
- O código executa, eventos são disparados, mas o usuário continua vendo o
  fluxo antigo.
- Permite confrontar o que aconteceria com o que aconteceu.
- Validar que `oauth_completed.latency_ms` p95 < 6s em tráfego real.

### 6.4. Dashboard ao vivo (BigQuery + Looker/Metabase)

Métricas com refresh de 5 min:

- Volume de `oauth_intercepted` por hora.
- Taxa de sucesso (`completed / started`).
- Latência p50/p95/p99.
- Top 5 erros por `error_code`.
- CVR e comissão/visita das visitas com `flag_variant=b`.

Alertas (PagerDuty):

- `oauth_failed_rate > 5%` por hora → killswitch automático.
- Crash rate `oauth_*` > 0,1% por hora → killswitch manual + page on-call.

## 7. Catálogo de dados (atualizações)

Adicionar no catálogo da Méliuz:

- Tag "Shopping > InApp OAuth" em todos os eventos `oauth_*`.
- Owner: PM Pleno Shopping.
- SLA do dado: < 30 min de latência entre evento e BI.
- Schema documentado em `/repo/docs/eventos.md`.

## 8. Plano de retirada da instrumentação

Após decisão final (ship/kill):

- **Se ship 100%:** manter `oauth_*` como eventos permanentes; remover a
  flag `mz_test_inapp_oauth` 30 dias depois (passa a ser comportamento
  padrão).
- **Se kill:** desligar flag, manter eventos por 90 dias para post-mortem,
  depois descontinuar.
