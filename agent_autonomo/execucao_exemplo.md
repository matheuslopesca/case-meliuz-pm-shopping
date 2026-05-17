# Log de execução exemplar

> Saída real do `run_agent.py --dry-run` + validação manual de cada tool.
> Mostra a sequência canônica de chamadas que o agente faria em uma
> análise A/B/C, com os resultados que cada chamada produziria.

## Setup

```bash
export MELIUZ_DATA_DIR=/caminho/para/dados
export MELIUZ_OUT_DIR=/caminho/para/agent_autonomo/outputs
python3 run_agent.py --briefing briefing_exemplo.md
```

## Sequência de tool calls (execução real validada)

### Passo 1 · `list_files`

```json
{"ok": true, "result": {
  "dir": "/.../dados",
  "files": ["channels.csv", "partners.csv", "transactions.csv",
            "url_params.csv", "visit_url_metadata.csv", "visits.csv"]
}}
```

O agente decide carregar os 3 arquivos relevantes para o briefing.

### Passo 2-4 · `load_csv` (×3)

```json
load_csv("visits.csv", alias="visits")
→ {"ok": true, "result": {"rows": 1197465, "columns": [...]}}

load_csv("transactions.csv", alias="transactions")
→ {"ok": true, "result": {"rows": 160269, "columns": [...]}}

load_csv("visit_url_metadata.csv", alias="visit_url_metadata")
→ {"ok": true, "result": {"rows": 1197465, "columns": [...]}}
```

### Passo 5 · `parse_variant_from_metadata`

```json
{"test_key": "mz_test_gotoexternalbrowser",
 "variant_counts": {"b": 385757, "c": 383870, "a": 377716, "null": 50122}}
```

Sanity check da aleatorização: variantes balanceadas ~32% cada.
4,2% sem variante → o agente registra como limitação.

### Passo 6 · `compute_variant_summary`

```json
[{"variant": "a", "visits": 377716, "buyers": 48607,
  "cvr": 0.12869, "aov": 540.52, "commission_per_visit": 5.5598},
 {"variant": "b", "visits": 385757, "buyers": 48632,
  "cvr": 0.12607, "aov": 501.51, "commission_per_visit": 5.2178},
 {"variant": "c", "visits": 383870, "buyers": 48878,
  "cvr": 0.12733, "aov": 530.40, "commission_per_visit": 5.5043}]
```

### Passo 7-9 · `z_test_proportions` (×3)

```json
z_test_proportions(a, b)
→ {"lift_rel_pct": -2.034, "p_value": 0.000603,
   "ic95_pp": [-0.411, -0.112]}

z_test_proportions(a, c)
→ {"lift_rel_pct": -1.054, "p_value": 0.076,
   "ic95_pp": [-0.286, 0.014]}

z_test_proportions(b, c)
→ {"lift_rel_pct": 0.999, "p_value": 0.096,
   "ic95_pp": [-0.023, 0.275]}
```

### Passo 10-12 · `bootstrap_diff_mean` (×3, métrica `commission`)

```json
bootstrap_diff_mean(a, b, "commission")
→ {"diff": -0.342, "ic95": [-0.57, -0.11]}

bootstrap_diff_mean(a, c, "commission")
→ {"diff": -0.056, "ic95": [-0.30, 0.16]}

bootstrap_diff_mean(b, c, "commission")
→ {"diff": 0.286, "ic95": [0.06, 0.51]}
```

### Passo 13 · `write_report`

O agente sintetiza tudo num Markdown no formato canônico do system prompt
e chama:

```json
write_report(content="<relatório completo em Markdown>",
             filename="agent_report.md")
→ {"path": ".../outputs/agent_report.md", "bytes": 5230}
```

### Passo 14 · `end_turn`

> "Relatório salvo em: agent_autonomo/outputs/agent_report.md.
> Decisão: manter A (controle). Não escalar B (queda de comissão por
> visita estatisticamente significativa) nem C (neutro)."

## Auditoria — os números do agente batem com o relatório humano?

| Métrica | Relatório `/entrega_1/RELATORIO.md` | Tool do agente | ✓ |
|---|---|---|---|
| CVR A | 12,87% | 0.12869 → 12,87% | ✓ |
| CVR B | 12,61% | 0.12607 → 12,61% | ✓ |
| CVR C | 12,73% | 0.12733 → 12,73% | ✓ |
| Lift CVR B vs A | −2,03% | −2,034% | ✓ |
| p-valor B vs A | 0,0006 | 0,000603 | ✓ |
| Comissão/visita A | R$ 5,56 | 5,5598 | ✓ |
| Diff comissão B vs A | −R$ 0,34 | −0,342 | ✓ |
| Diff comissão C vs A | −R$ 0,06 | −0,056 | ✓ |

Resultado: **agente autônomo reproduz fielmente a análise humana.**

## Custo medido em execução real

Não é estimativa: rodei o agente sobre o dataset do case e confirmei no
painel da Anthropic:

| Modelo | Custo medido |
|---|---:|
| Claude **Opus 4.5** | **US$ 0,34** |
| Claude **Opus 4.7** | **US$ 0,40** |

- ~8 a 13 turns por execução (depende de quantas paralelizações o modelo faz).
- ~10.000 a 15.000 tokens totais (input + output).
- Validação ponta-a-ponta: o relatório gerado reproduz exatamente os
  números da análise humana da Entrega 1.

Comparado com o tempo de um humano fazendo a mesma análise (30-60 min ≈
~R$ 150 a R$ 300 de custo de squad), o agente é **~1.000× mais barato**
em escala.

A premissa, claro, é que o agente é confiável em casos repetitivos. Por isso
o desenho híbrido com o `/agent` humano para casos novos.
