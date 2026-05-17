# Case Méliuz — PM Pleno Shopping

> Resolução do case técnico "Teste A/B/C do In-App Browser" para a vaga de
> Product Manager Pleno — Shopping.
> Autor: **Matheus Carvalho** · matheuslopescarvalho@gmail.com · 2026-05-17

---

## TL;DR da resolução

1. **Recomendação:** não implementar B nem C. Manter A (controle) — a opção
   de saída para navegador externo destrói comissão por visita,
   especialmente nas saídas via login social.
2. **Maior aprendizado:** o login social que sai para navegador externo é o
   **maior vazamento isolado de comissão** identificado no teste (queda de
   ~75% na comissão por visita).
3. **Próxima aposta:** OAuth interceptado dentro do In-App Browser. PRD
   completa, plano de instrumentação, plano de teste A/B e quebra em tasks
   para engenharia estão na pasta `entrega_2/`.

---

## Como navegar este repositório

```
repo/
├── README.md                       ← você está aqui
├── agent/                          ← workflow humano + IA (squad day-to-day)
│   ├── SYSTEM_PROMPT.md            · identidade, princípios, pipeline padrão
│   ├── RUNBOOK.md                  · passo a passo para reusar em novos testes
│   ├── templates/
│   │   ├── REPORT_TEMPLATE.md      · template do relatório de análise
│   │   └── PRD_TEMPLATE.md         · template padrão de PRD
│   └── checklists/
│       ├── QA_DADOS.md             · qualidade dos dados antes da análise
│       └── QA_RELATORIO.md         · revisão antes de compartilhar o relatório
│
├── agent_autonomo/                 ← agente real (orchestrator com tool use)
│   ├── README.md                   · diferença vs /agent humano + como rodar
│   ├── system_prompt.md            · prompt do agente
│   ├── briefing_exemplo.md         · briefing de teste (input do agente)
│   ├── tools.py                    · 7 tools + JSONSchema + dispatcher
│   ├── run_agent.py                · loop agêntico (Anthropic SDK)
│   ├── execucao_exemplo.md         · log validado + auditoria vs análise humana
│   └── requirements.txt
│
├── analise/                        ← código Python executável e reproduzível
│   ├── 01_explore.py               · grão, integridade, identificação de variantes
│   ├── 02_metrics.py               · agregações, z-test, bootstrap
│   └── 03_visualizations.py        · gráficos do relatório
│
├── entrega_1/
│   └── RELATORIO.md                ← Entrega 1: análise e recomendação completas
│
├── entrega_2/
│   ├── PRD_login_social_in_app.md  ← Entrega 2: PRD da próxima melhoria
│   ├── INSTRUMENTACAO.md           ·   plano de eventos, UTMs, mz_* e validação
│   ├── PLANO_DE_TESTE.md           ·   desenho do A/B, MDE, critérios
│   └── HANDOFF_ENG.md              ·   quebra em tasks para engenharia
│
├── docs/
│   └── COMO_RODAR.md               · passo a passo para reproduzir do zero
│
└── outputs/                        ← gerado pelos scripts (CSVs e PNGs)
    ├── visits_enriched.csv
    ├── base_visit_level_abc.csv
    ├── resumo_por_variante.csv
    ├── resumo_por_variante_canal.csv
    ├── resumo_por_feature.csv
    ├── ztest_cvr.csv
    ├── bootstrap_commission.csv
    └── graficos/
        ├── g1_cvr_por_variante.png
        ├── g2_comissao_por_variante.png
        ├── g3_canal_externo.png
        ├── g4_feature_saida.png
        └── g5_lifts_com_ic.png
```

## Como reproduzir do zero

### Pré-requisito · Instalar Python 3.10+ e pip3

Confira primeiro se já tem (no Terminal/PowerShell):

```bash
python3 --version    # deve mostrar 3.10 ou superior
pip3 --version
```

Se algum desses comandos não funcionar, instale pelo método mais simples
do seu sistema:

**macOS** — via [Homebrew](https://brew.sh):

```bash
brew install python
```

**Linux (Ubuntu / Debian / WSL):**

```bash
sudo apt update && sudo apt install -y python3 python3-pip
```

**Linux (Fedora / RHEL):**

```bash
sudo dnf install -y python3 python3-pip
```

**Windows** — caminho mais simples sem terminal:

1. Abra a **Microsoft Store**, busque `Python 3.12` (ou superior) e clique
   em **Get / Obter**.
2. Abra o **PowerShell** e confirme: `python --version` e `pip --version`.

> Alternativa: baixar o instalador oficial em
> <https://www.python.org/downloads/windows/> e, na primeira tela,
> **marcar "Add Python to PATH"** antes de clicar em *Install Now*.

> No Windows, os comandos abaixo trocam `python3` por `python` e `pip3`
> por `pip`. O resto é igual.

### Pipeline

```bash
# 1. Clonar o repositório (se ainda não o fez)
git clone https://github.com/matheuslopesca/case-meliuz-pm-shopping.git
cd case-meliuz-pm-shopping

# 2. Colocar os 6 CSVs do case na pasta `dados/` na raiz do repo
#    (visits.csv, transactions.csv, url_params.csv, visit_url_metadata.csv,
#     partners.csv, channels.csv — eles vêm junto do enunciado)
mkdir -p dados
# copie os CSVs para ./dados/

# 3. Instalar dependências
pip3 install pandas numpy matplotlib

# 4. Rodar a pipeline (a partir da raiz do repo)
python3 analise/01_explore.py
python3 analise/02_metrics.py
python3 analise/03_visualizations.py
```

Tempo total: ~2 minutos em uma máquina padrão.

> Os scripts usam paths relativos à raiz do repo por padrão (`./dados/` e
> `./outputs/`). Se você quiser apontar para outros lugares, sobrescreva
> via env var antes de rodar:
> `export MELIUZ_DATA_DIR=/caminho/customizado` ou `MELIUZ_OUT_DIR`.

## Roteiro de leitura sugerido (30-40 min)

1. **`entrega_1/RELATORIO.md`** — TL;DR + análise completa (10 min).
2. **`outputs/graficos/`** — olhe os 5 gráficos enquanto lê (3 min).
3. **`entrega_2/PRD_login_social_in_app.md`** — a PRD da próxima melhoria
   (10 min).
4. **`entrega_2/HANDOFF_ENG.md`** — como isso vira sprint (5 min).
5. **`agent/SYSTEM_PROMPT.md`** + **`agent/RUNBOOK.md`** — para entender
   como o trabalho é reaproveitável e auditável (10 min).
6. **`analise/01_explore.py`** + **`analise/02_metrics.py`** — para conferir
   números e o método estatístico (5-10 min).

## O que este repo demonstra (mapa para os critérios da vaga)

| Competência avaliada | Onde está |
|---|---|
| Pensamento analítico | `entrega_1/RELATORIO.md` §3-§5 + scripts |
| Tomada de decisão | `entrega_1/RELATORIO.md` §4 |
| Product thinking | `entrega_1/RELATORIO.md` §5 + `entrega_2/PRD_...md` §2-§5 |
| Instrumentação | `entrega_2/INSTRUMENTACAO.md` |
| Execução com engenharia | `entrega_2/HANDOFF_ENG.md` |
| Design de experimento | `entrega_2/PLANO_DE_TESTE.md` + apêndice estatístico do relatório |
| Processo, IA e escalabilidade | `agent/` (workflow humano) + `agent_autonomo/` (agente real com tool use) |
| Comunicação | TL;DRs, tabelas, gráficos e prose direta nos relatórios |

## Stack e princípios

- **Python 3.10+**, pandas, numpy, matplotlib. Sem scipy (não disponível no
  ambiente padrão); implementei z-test e bootstrap manualmente para garantir
  auditabilidade.
- **Reprodutibilidade primeiro.** Mesma seed, mesmos números. Caminhos
  parametrizados por env vars.
- **Tudo em Markdown auditável.** Sem .docx ou PDFs proprietários — facilita
  PR, diff e versionamento no GitHub.
- **Agente como artefato de primeira classe.** Não é "memorinha"; é um
  sistema com prompt, runbook, templates e checklist de QA.

## Agente autônomo — execução real medida

O agente em `agent_autonomo/` **foi rodado de verdade** sobre o dataset do
case, e os custos por execução foram medidos no painel da Anthropic:

| Modelo | Custo medido por execução | Resultado |
|---|---:|---|
| Claude **Opus 4.5** | **US$ 0,34** | Reproduz fielmente os números da Entrega 1 |
| Claude **Opus 4.7** | **US$ 0,40** | Idem; análise um pouco mais aprofundada nos guardrails |

Em ambos os casos, o agente chamou de 8 a 13 tools por execução, identificou
sozinho a violação de guardrail de AOV pela variante B (insight que não
estava explícito no briefing) e produziu o relatório final no formato
canônico do squad.

> Para referência: o mesmo trabalho feito por um humano leva ~30-60 min de
> análise (custo de squad ~ R$ 150-300). O agente é portanto **3 a 4 ordens
> de grandeza mais barato** em casos repetitivos — o que justifica usá-lo
> para monitoria contínua, mantendo o workflow humano em `/agent` para casos
> novos e ambíguos.

### Precisa de uma API key da Anthropic para testar o agente?

Se você for da equipe de avaliação e quiser executar o agente autônomo
mas não tem uma conta da Anthropic com créditos, **me avise por e-mail
(matheuslopescarvalho@gmail.com)**. Forneço uma chave temporária de uma
conta que carreguei com créditos especificamente para este teste — o
custo total previsto está coberto.

---

## Notas pessoais ao recrutador

Foco em três escolhas que fiz neste case (e que reflete como eu trabalho):

1. **Métrica-norte = comissão por visita.** É o que importa para o negócio.
   CVR sozinho engana porque mais compradores não significa mais receita se
   eles compram menos ou se a atribuição quebra.
2. **Não recomendei nada novo neste teste.** É raro um PM dizer "não faça
   nada"; mas o melhor produto é o que protege a receita do tropeço. O
   próximo teste, sim, ataca o problema-raiz (login).
3. **Investi em escalabilidade desde o dia 1.** O agente, os templates e os
   checklists existem para que o próximo teste do squad não dependa de mim
   refazer tudo do zero — alguém em onboarding consegue rodar a mesma análise
   em uma tarde.

Obrigado pela leitura.
