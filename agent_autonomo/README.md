# Agente autônomo — prova de conceito

> Esta pasta é **um upgrade técnico** sobre `/agent` (que é o workflow humano).
> Aqui o LLM toma cada decisão de pipeline sozinho via *tool use*.

## Por que duas pastas?

O case da Méliuz pede tanto **maturidade no uso de IA** quanto
**reaproveitamento e escalabilidade**. Esses dois objetivos são atendidos
melhor por **soluções diferentes**:

| Pasta | O que é | Quando usar |
|---|---|---|
| **`/agent`** | Workflow human-in-the-loop. System prompt + runbook + templates + checklists que um humano usa em conjunto com um LLM para conduzir uma análise. | Casos novos, ambíguos, com dados desconhecidos. O humano valida cada passo. **É o que recomendo como prática do squad no dia a dia.** |
| **`/agent_autonomo`** | Agente real com loop autônomo. O LLM decide cada tool call sem intervenção humana, executa a análise inteira e produz o relatório. | Casos repetitivos, testes recorrentes, monitoria automática. **É o caminho de escala depois que o workflow do squad estabiliza.** |

A diferença essencial: **quem decide o próximo passo**.

| Critério | `/agent` (humano) | `/agent_autonomo` |
|---|---|---|
| Decisão do próximo passo | Humano | LLM em loop |
| Tool calls explícitas? | Não | Sim — 7 tools definidas em `tools.py` |
| Custo por execução | Tempo humano | Tokens (mais barato em escala) |
| Auditabilidade | Checklist humana | Log estruturado de tool calls |
| Velocidade | 30-60 min com humano | ~2-5 min sem humano |
| Risco de erro silencioso | Baixo (humano revisa) | Médio (precisa de guardrails fortes) |

## Como funciona o loop

```
┌──────────────────────────────────────────────────────────┐
│  1. carrega system_prompt.md + briefing.md               │
│  2. envia para Claude com TOOL_SCHEMAS                    │
│  3. Claude responde com tool_use(name, args)              │
│  4. run_agent.py executa tools.call_tool(name, **args)    │
│  5. devolve tool_result para Claude                       │
│  6. repete até Claude responder end_turn                  │
│  7. Claude chamou write_report → relatório está em disco  │
└──────────────────────────────────────────────────────────┘
```

## Arquivos

- `system_prompt.md` — identidade, princípios, formato obrigatório do relatório.
- `briefing_exemplo.md` — briefing do teste em Markdown (input do agente).
- `tools.py` — implementação das 7 tools + JSONSchema + dispatcher.
- `run_agent.py` — loop agêntico (Anthropic SDK).
- `requirements.txt` — `anthropic`, `pandas`, `numpy`.
- `outputs/` — onde o relatório final é salvo.

## Como rodar

> **Premissa:** os comandos abaixo são executados a partir da raiz do
> repositório que você clonou do GitHub. Os 6 CSVs do case devem estar em
> `./dados/` na raiz (os scripts encontram automaticamente).

### Modo dry-run (sem API key — para inspecionar o pacote de contexto)

```bash
cd agent_autonomo
python3 run_agent.py --dry-run
```

Output esperado: mostra o tamanho do system prompt, do briefing, lista das
tools e executa **uma** chamada (`list_files`) para validar que o pipeline
local funciona.

### Modo real (com API key — macOS / Linux)

```bash
cd agent_autonomo
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python3 run_agent.py --briefing briefing_exemplo.md
```

> Guia detalhado (instalação do Python, virtualenv, troubleshooting,
> custos por modelo) em [`COMO_TESTAR.md`](./COMO_TESTAR.md).

Cada passo do agente é logado no stdout:

```
── passo  1 · chamando o LLM ────────────────────────────
   🔧 tool_use → list_files({})
   📤 tool_result ← {"ok": true, "result": {"files": ["channels.csv", ...]}}
── passo  2 · chamando o LLM ────────────────────────────
   🔧 tool_use → load_csv({"filename": "visits.csv", "alias": "visits"})
   📤 tool_result ← {"ok": true, "result": {"rows": 1197465, ...}}
   ...
✅ Agente terminou (end_turn).
```

Ao final, o relatório está em `outputs/agent_report.md`.

## O que esse agente sabe fazer (escopo do MVP)

✅ Identificar variantes A/B/C a partir do JSON `tracking_url_params`.
✅ Calcular métricas master por variante (CVR, AOV, comissão/visita, GMV/visita).
✅ Rodar z-test de proporções e bootstrap para diferenças de média.
✅ Produzir um relatório no formato canônico do squad.
✅ Decidir entre ship / iterate / kill / inconclusive.

## O que ele **não** sabe fazer (escopo da próxima iteração)

❌ Cortes por canal final (`channel_id`) — fácil de adicionar como nova tool.
❌ Cortes por parceiro top-N — idem.
❌ Geração de gráficos (PNG) — exigiria headless matplotlib + tool dedicada.
❌ Memória entre sessões — hoje cada execução é stateless.
❌ Auto-revisão (segundo LLM aplicando os checklists) — próximo passo lógico.

## Por que não substituí o `/agent` (humano)

Por três razões honestas:

1. **Confiabilidade.** Em análises novas e ambíguas, o humano ainda valida
   melhor do que o LLM autônomo. Ship/kill envolve dinheiro real.
2. **Manutenção.** O workflow humano é texto + checklist; qualquer PM
   atualiza. O agente autônomo é código que precisa de eng para evoluir.
3. **Custo de token.** Para o squad inteiro, rodar o workflow humano sai
   mais barato e mais auditável que o agente autônomo no dia a dia.

A combinação **workflow humano para casos novos + agente autônomo para
casos recorrentes** é o desenho que faz sentido na Méliuz.
