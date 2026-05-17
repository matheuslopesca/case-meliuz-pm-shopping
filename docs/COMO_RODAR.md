# Como rodar a análise do zero

> Para qualquer pessoa que não conhece o repo conseguir reproduzir todos os
> resultados em menos de 10 minutos.

## Premissa

Este guia assume que você **já clonou o repositório do GitHub**:

```bash
git clone https://github.com/matheuslopesca/case-meliuz-pm-shopping.git
cd case-meliuz-pm-shopping
```

Todos os comandos abaixo são executados **a partir da raiz do repositório
clonado**.

## Pré-requisitos

- **Python 3.10 ou superior** instalado (`python3 --version`).
- **pip3** atualizado (`pip3 --version`).
- **Os 6 CSVs do case** colocados na pasta `dados/` na raiz do repo:

  ```
  case-meliuz-pm-shopping/
  ├── dados/
  │   ├── visits.csv
  │   ├── transactions.csv
  │   ├── url_params.csv
  │   ├── visit_url_metadata.csv
  │   ├── partners.csv
  │   └── channels.csv
  └── ...
  ```

  Os CSVs não vêm versionados (~600 MB no total quando processados); quem
  está revisando o case já os recebeu junto do enunciado.

## Passo 1 — Instalar dependências

```bash
pip3 install pandas numpy matplotlib
```

> **Não usamos scipy** — z-test e bootstrap estão implementados manualmente
> em `analise/02_metrics.py` para evitar dependências pesadas e tornar a
> matemática auditável a olho.

> Se aparecer `error: externally-managed-environment` (Python 3.12+ no
> macOS via Homebrew, Ubuntu 24.04+), use:
>
> ```bash
> pip3 install pandas numpy matplotlib --break-system-packages
> ```
>
> Ou crie um virtualenv:
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip3 install pandas numpy matplotlib
> ```

## Passo 2 — Rodar a pipeline

Da raiz do repo:

```bash
python3 analise/01_explore.py        # ~30s — perfila os dados e extrai variantes
python3 analise/02_metrics.py        # ~60s — agregações e testes estatísticos
python3 analise/03_visualizations.py # ~5s  — gera os PNGs
```

Os scripts encontram automaticamente:

- `dados/` na raiz do repo (entrada).
- `outputs/` na raiz do repo (saída, criada se não existir).

Se você quiser apontar para outros lugares, defina antes de rodar:

```bash
export MELIUZ_DATA_DIR="/caminho/customizado/dados"
export MELIUZ_OUT_DIR="/caminho/customizado/outputs"
```

## Passo 3 — Conferir saídas

Em `outputs/` devem aparecer:

- `visits_enriched.csv` — visits com variante, mz_redirect, utm_content e utm_term.
- `base_visit_level_abc.csv` — grão visita com flag de conversão.
- `resumo_por_variante.csv` — métricas master por variante.
- `resumo_por_variante_canal.csv` — quebra por canal (InApp x externo).
- `resumo_por_feature.csv` — quebra por tipo de saída.
- `ztest_cvr.csv` — z-test de proporções.
- `bootstrap_commission.csv` — bootstrap de comissão por visita.
- `graficos/g1...g5.png` — gráficos do relatório.

## Passo 4 — Ler o relatório

Abra `entrega_1/RELATORIO.md` em qualquer leitor de Markdown (GitHub, VS
Code, Typora, etc.). Os números do relatório referenciam os CSVs gerados em
`outputs/`.

## Como cheguei nos números (esquema mental)

```
visits.csv ────┐
               ├──► join url_param_id     ──► url_params.csv (utm_content, utm_term)
               ├──► join visit_id         ──► visit_url_metadata.csv (JSON com mz_*)
               ├──► join partner_id       ──► partners.csv (dim parceiros)
               └──► join channel_id       ──► channels.csv (INAPP / BROWSERDEFAULT)

transactions.csv ─► group by visit_id ─► aggregar (n_tx, gmv, cashback, commission)
                                          │
                                          ▼
                              base_visit_level_abc.csv

Métricas (por variante):
  CVR              = buyers / visits
  AOV              = GMV / n_tx
  Comissão/visita  = Σ commission / visits
  GMV/visita       = Σ GMV / visits
```

## Solução de problemas

| Problema | Causa provável | Como resolver |
|---|---|---|
| `FileNotFoundError: dados/visits.csv` | Pasta `dados/` ausente ou vazia | Coloque os 6 CSVs em `dados/` na raiz, ou aponte `MELIUZ_DATA_DIR` para o lugar correto |
| `ImportError: pandas` | Dependências não instaladas | `pip3 install pandas numpy matplotlib` |
| `UnicodeDecodeError` ao ler CSV | Arquivo veio sem BOM ou com BOM em encoding diferente | Os scripts já usam `utf-8-sig`; se mesmo assim falhar, troque para `utf-8` ou `latin-1` no `read_csv` |
| Bootstrap muito lento | `n_boot` alto ou dataset grande | Reduzir `n_boot` em `02_metrics.py` (default = 1000) |

## Como atualizar o agente para um novo teste

Veja `agent/RUNBOOK.md` — passo a passo para reaproveitar o agente em
qualquer outro teste A/B/C do time.
