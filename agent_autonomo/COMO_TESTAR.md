# Como testar o agente autônomo na sua máquina

> ~10 minutos de setup. Instruções para **macOS** e **Linux**.
> Custo da execução real: **US$ 0,15 a US$ 0,40** por rodada (depende do modelo).

## Premissa

Este guia assume que você **já clonou o repositório do GitHub** para algum
lugar da sua máquina, por exemplo:

```bash
git clone https://github.com/matheuslopesca/case-meliuz-pm-shopping.git
cd case-meliuz-pm-shopping
```

Todos os comandos abaixo são executados **a partir da raiz do repositório
clonado**. Onde aparece `<repo>`, leia "a pasta onde você clonou".

## O que você vai precisar

1. **Python 3.10 ou superior** (`python3 --version`).
2. **pip3** atualizado (`pip3 --version`). Em macOS/Linux, sempre use `pip3` — o `pip` "puro" tende a apontar para Python 2 ou ficar inconsistente.
3. **Os 6 CSVs do case** colocados em `<repo>/dados/`. (Os CSVs não vêm no
   repositório por causa do tamanho; quem está revisando o case já os
   recebeu junto do enunciado.)
4. **Uma API key da Anthropic** (gratuito para criar; cobra por uso).

> Não tem `python3` ou `pip3`? Instale:
> - **macOS:** `brew install python` (precisa do [Homebrew](https://brew.sh)).
> - **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install -y python3 python3-pip`.
> - **Linux (Fedora):** `sudo dnf install -y python3 python3-pip`.

---

## Passo 1 · Conseguir uma API key da Anthropic

> **Atalho para o time de avaliação:** se você quer testar o agente mas
> não tem uma conta da Anthropic com créditos, me mande um e-mail
> (**matheuslopescarvalho@gmail.com**) que eu envio uma chave temporária
> de uma conta que carreguei com créditos especificamente para este case.
> Você roda em ~3 minutos sem custo nenhum.

Se preferir usar uma conta sua:

1. Acesse <https://console.anthropic.com/>.
2. Crie a conta com o email que usa.
3. Vá em **Settings → API Keys → Create Key**.
4. Copie a chave (começa com `sk-ant-...`). **Ela só aparece uma vez** — salve em local seguro.
5. Para créditos: a Anthropic dá US$ 5 de crédito grátis no signup. É mais que suficiente para 15-30 rodadas do agente.

## Passo 2 · Posicionar os dados

A pasta `dados/` precisa existir na raiz do repo, com os 6 CSVs:

```
<repo>/
├── dados/
│   ├── visits.csv
│   ├── transactions.csv
│   ├── url_params.csv
│   ├── visit_url_metadata.csv
│   ├── partners.csv
│   └── channels.csv
├── agent_autonomo/
└── ...
```

Como criar:

```bash
mkdir -p dados
# copie os 6 CSVs para essa pasta
```

Se preferir manter os CSVs em outro lugar (por exemplo, em uma pasta
compartilhada do sistema), você pode apontar pelo env var
`MELIUZ_DATA_DIR` no Passo 4.

## Passo 3 · Instalar as dependências

```bash
cd agent_autonomo
pip3 install -r requirements.txt
```

> Se aparecer `error: externally-managed-environment` (comum em Python 3.12+
> no macOS via Homebrew e no Ubuntu 24.04+), use uma destas alternativas:
>
> **Opção A — `--break-system-packages`** (mais rápido, instala global):
>
> ```bash
> pip3 install -r requirements.txt --break-system-packages
> ```
>
> **Opção B — virtualenv** (recomendado para isolar):
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip3 install -r requirements.txt
> ```
>
> Lembre-se de ativar o venv (`source .venv/bin/activate`) em cada nova
> sessão do Terminal antes de rodar o agente.

Verifique se instalou:

```bash
python3 -c "import anthropic, pandas, numpy; print('OK')"
```

Deve imprimir `OK`.

## Passo 4 · Configurar a API key (e, se necessário, paths customizados)

```bash
export ANTHROPIC_API_KEY="sk-ant-cole-sua-chave-aqui"
```

Se você colocou os CSVs em `<repo>/dados/`, **não precisa de mais nada** —
os scripts encontram automaticamente. Só configure as variáveis abaixo se
quiser apontar para outro lugar:

```bash
# opcional: só se os dados/outputs estiverem fora da pasta do repo
export MELIUZ_DATA_DIR="/caminho/customizado/para/os/csvs"
export MELIUZ_OUT_DIR="/caminho/customizado/para/saidas"
```

> Para persistir a chave entre sessões:
>
> - **macOS** (zsh): adicione no fim de `~/.zshrc` e rode `source ~/.zshrc`.
> - **Linux** (bash): adicione no fim de `~/.bashrc` e rode `source ~/.bashrc`.
>
> Para descobrir qual shell você usa: `echo $SHELL`.

## Passo 5 · Validar a infra com `--dry-run` (sem gastar token)

```bash
python3 run_agent.py --dry-run
```

Saída esperada:

```
======================================================================
ABx Analyst — agente autônomo
Modelo: claude-opus-4-5
Briefing: briefing_exemplo.md
Tools disponíveis: ['list_files', 'load_csv', ...]
======================================================================

[dry-run] mostrando o pacote de contexto que iria para o LLM:
  system_prompt: 3432 chars
  user_msg: 1390 chars
  tools: 7 definidas

[dry-run] simulando chamada do agente: list_files()
   📤 tool_result ← {"ok": true, "result": {"files": [...]}}
```

Se você viu os 6 CSVs listados, **toda a parte local está funcionando**.
Falta só pagar os tokens.

## Passo 6 · Rodar de verdade

```bash
python3 run_agent.py --briefing briefing_exemplo.md
```

O agente vai começar a logar passo a passo:

```
── passo  1 · chamando o LLM ──────────────────────────────────
   🔧 tool_use → list_files({})
   📤 tool_result ← {"ok": true, "result": {"files": [...]}}
── passo  2 · chamando o LLM ──────────────────────────────────
   🔧 tool_use → load_csv({"filename": "visits.csv", "alias": "visits"})
   ...
✅ Agente terminou (end_turn).
```

Tempo total: **~2 a 5 minutos**.

## Passo 7 · Conferir o output

```bash
cat outputs/agent_report.md      # ou o nome que o agente escolheu
ls outputs/
```

O relatório segue a estrutura definida no `system_prompt.md`. Compare com
`../entrega_1/RELATORIO.md` (versão humana) — os números devem bater.

---

## Custo por execução

### Medições reais (este case, dataset completo)

| Modelo | Custo medido | Observação |
|---|---:|---|
| Claude **Opus 4.5** | **US$ 0,34** | Análise completa, ~13 tool calls. |
| Claude **Opus 4.7** | **US$ 0,40** | Idem, com cortes adicionais nos guardrails. |

Esses são os números reais do painel da Anthropic, rodando o
`briefing_exemplo.md` sobre os 1,2 M de visitas do case.

### Estimativas para outros modelos (não medidos)

Baseadas no preço público da Anthropic em mai/2026:

| Modelo | Custo estimado |
|---|---:|
| Claude Sonnet 4.5 | ~US$ 0,07-0,12 |
| Claude Haiku 4.5 | ~US$ 0,01-0,03 |

### Como trocar de modelo

```bash
export ABXAGENT_MODEL="claude-sonnet-4-5"
python3 run_agent.py --briefing briefing_exemplo.md
```

Recomendação prática: **rode primeiro com Haiku ou Sonnet** para validar
que o pipeline está se comportando como esperado (custo ~US$ 0,03-0,12).
Quando estiver pronto para gerar a versão "oficial" do relatório, suba
para Opus 4.5 ou 4.7.

### Comparativo com trabalho humano

O mesmo relatório feito por um analista humano leva ~30-60 min — custo
aproximado de **R$ 150 a R$ 300** em horas de squad. O agente é
**~1.000× mais barato** em escala. Por isso a recomendação do `/agent`
(humano) para casos novos e do `/agent_autonomo` (automático) para
monitoria recorrente.

---

## Troubleshooting

### "anthropic.AuthenticationError: invalid x-api-key"

A variável `ANTHROPIC_API_KEY` está vazia ou errada. Confirme:

```bash
echo $ANTHROPIC_API_KEY | head -c 20
```

Deve imprimir algo como `sk-ant-api03-...`.

### "anthropic.RateLimitError"

Sua conta tem rate limit baixo (provavelmente nova). Espere 1 min e tente
de novo, ou compre US$ 5 de crédito no console — sobe o limite na hora.

### "anthropic.BadRequestError: model_not_found"

O nome do modelo no `ABXAGENT_MODEL` está incorreto. Verifique os modelos
disponíveis em <https://docs.anthropic.com/en/docs/about-claude/models>.
Defaults seguros em mai/2026:

- `claude-opus-4-5` (mais capaz, mais caro)
- `claude-sonnet-4-5` (balanceado)
- `claude-haiku-4-5` (rápido e barato)

### "FileNotFoundError: visits.csv" (ou similar)

A pasta `dados/` está vazia ou em outro lugar. Confirme:

```bash
ls dados/
```

Devem aparecer os 6 CSVs. Se estiver em outro lugar, ajuste:

```bash
export MELIUZ_DATA_DIR="/caminho/correto/dados"
```

### O agente entra em loop / não termina

Por segurança o `MAX_ITERATIONS = 25`. Se ele atingir esse limite sem
chamar `write_report`, o script aborta com a mensagem
"⚠️ Limite atingido sem end_turn". Pode acontecer se o briefing for muito
ambíguo ou se você restringir tools no system prompt.

Solução: simplifique o briefing ou aumente o limite:

```bash
export ABXAGENT_MAX_ITER=40
```

### O agente está caro demais

Trocar de modelo é a solução mais direta (ver tabela acima). Outras opções:

- Reduzir `n_boot` em `bootstrap_diff_mean` (default 500 → use 200).
- Pedir ao agente, no briefing, que rode "só as comparações essenciais (B vs A e C vs A)".

---

## Modificações que vale a pena testar

Para sentir como o agente é flexível, tente:

1. **Mudar o briefing** — edite `briefing_exemplo.md` e diga "preocupe-se especialmente com o impacto em AOV". Veja o agente priorizar AOV nas análises.
2. **Mudar a métrica primária** no system prompt — em vez de comissão por visita, peça "GMV total" — observe a recomendação mudar.
3. **Adicionar uma tool nova** em `tools.py` — por exemplo `breakdown_by_partner(top_n=10)`. Atualize `TOOL_SCHEMAS` e `DISPATCH`. O agente vai descobrir sozinho que ela existe e usar quando fizer sentido.

---

## E se eu não quiser pagar pela API agora?

Tudo bem. O modo `--dry-run` valida que:

- O loop está implementado corretamente.
- As 7 tools funcionam (mostrando a chamada inicial `list_files`).
- O contexto (system prompt + briefing + tools) está bem formado.

A validação manual ponta-a-ponta das 7 tools (já feita) está em
`execucao_exemplo.md` com os resultados que o agente produziria — o
output bate exatamente com o relatório humano da Entrega 1.

Em outras palavras: você consegue **demonstrar** que o agente funciona
sem precisar gastar US$ 0,30. Mas rodar de verdade impressiona muito mais
em entrevista — vale o investimento.
