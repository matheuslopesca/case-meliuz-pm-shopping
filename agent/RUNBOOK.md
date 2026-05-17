# RUNBOOK — Como rodar o ABx Analyst em um novo teste

> Este runbook descreve, passo a passo, como reaproveitar este agente para
> analisar qualquer novo teste A/B/C de Shopping na Méliuz, sem reescrever
> código nem retomar contexto do zero.

## Pré-requisitos

- Python 3.10+, pandas, numpy, matplotlib.
- Acesso aos CSVs do BI (mesmo schema do case: `visits`, `transactions`,
  `url_params`, `visit_url_metadata`, `partners`, `channels`).
- Um modelo LLM (Claude Opus 4 ou superior, com ferramenta de execução de código).

## Estrutura de inputs esperada

```
/dados/
  ├── visits.csv               # 1 linha por click/saída
  ├── transactions.csv         # 1 linha por compra atribuída
  ├── url_params.csv           # combos UTM (utm_content, utm_term)
  ├── visit_url_metadata.csv   # JSON com mz_test_* e mz_redirect
  ├── partners.csv             # dim parceiros
  └── channels.csv             # INAPP / BROWSERDEFAULT
```

## Passo a passo (15 a 30 min com agente)

### 1. Briefing do novo teste (humano → agente)

Crie um arquivo `agent/test_brief.md` com:

```
# Teste XX — <nome curto>
- Hipótese: <o que esperamos que melhore>
- Variantes: A (controle), B (...), C (...)
- Métrica primária: comissão por visita
- Guardrails: AOV não cai >5%, CVR não cai >2pp
- Período: <início> a <fim>
- Tag no mz_*: mz_test_<chave_do_teste>=<a|b|c>
```

### 2. Atualizar a chave do teste no `01_explore.py`

```python
TEST_KEY = "mz_test_gotoexternalbrowser"   # ← trocar aqui
```

Tudo o resto (extração de variante, parsing do JSON) continua igual porque o
schema do BI é estável.

### 3. Rodar a pipeline

```bash
export MELIUZ_DATA_DIR=/caminho/para/dados
export MELIUZ_OUT_DIR=/caminho/para/outputs
python3 analise/01_explore.py
python3 analise/02_metrics.py
python3 analise/03_visualizations.py
```

Os scripts geram:
- `outputs/visits_enriched.csv`
- `outputs/base_visit_level_abc.csv`
- `outputs/resumo_por_variante.csv`
- `outputs/resumo_por_variante_canal.csv`
- `outputs/resumo_por_feature.csv`
- `outputs/ztest_cvr.csv`
- `outputs/bootstrap_commission.csv`
- `outputs/graficos/*.png`

### 4. Carregar o agente com o pacote de contexto

Inputs para o LLM (sempre nessa ordem):
1. `agent/SYSTEM_PROMPT.md`
2. `agent/test_brief.md`
3. `outputs/resumo_por_variante.csv`
4. `outputs/ztest_cvr.csv`
5. `outputs/bootstrap_commission.csv`
6. `outputs/resumo_por_variante_canal.csv`
7. `outputs/resumo_por_feature.csv`

Pergunta do PM (template):
> "Analise o teste descrito em test_brief.md usando as tabelas anexadas.
> Aplique o pipeline padrão. Entregue o relatório no formato obrigatório do
> SYSTEM_PROMPT. Use o template `templates/REPORT_TEMPLATE.md`."

### 5. Validar a saída do agente (checklist humano)

- [ ] O agente reconstruiu corretamente a alocação de variantes?
- [ ] Os números do relatório batem com `resumo_por_variante.csv`?
- [ ] Toda afirmação tem IC e p-valor associados?
- [ ] A recomendação está alinhada com a tabela de critérios?
- [ ] As "próximas perguntas" são acionáveis (não genéricas)?
- [ ] Os gráficos sustentam a narrativa?

### 6. Loop de revisão

Se algum item da checklist falhar, faça **uma única pergunta cirúrgica** ao
agente apontando o erro específico (com linha do relatório). Não rode a
pipeline de novo — o agente apenas reescreve a seção afetada.

## Escalando para outros testes

Este agente foi desenhado para o "shape" típico de testes de funil de saída
no Shopping. Para reusar em outros contextos:

| Tipo de teste | Mudança necessária |
|---|---|
| Teste de homepage / merchandising | Trocar grão de "visita" para "sessão de app" |
| Teste de notificação push | Trocar tabela `visits` por `push_events` |
| Teste de cashback variável | Adicionar dimensão `cashback_pct` na agregação |
| Teste de checkout | Mudar conversão para `n_tx>0 AND status='approved'` |

A regra é: **mude o nome das colunas no `02_metrics.py`**, mantenha as fórmulas.

## Como auditar uma análise feita por outra pessoa

1. Confira `resumo_por_variante.csv` contra os números do relatório.
2. Rode `ztest_cvr.csv` em uma calculadora independente (ex: Statsig, Evan
   Miller's calculator, ou outra implementação do z-test).
3. Verifique se a recomendação respeita a tabela de critérios.
4. Aponte divergências como issues no PR do GitHub.
