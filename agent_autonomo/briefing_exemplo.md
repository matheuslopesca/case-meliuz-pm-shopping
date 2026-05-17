# Briefing — Teste A/B/C In-App Browser (Shopping)

## Contexto

Estamos avaliando se oferecer uma saída para o navegador externo dentro do
In-App Browser melhora ou piora a experiência de cashback dos usuários do
app Méliuz.

## Variantes

- A — Controle: fluxo padrão do In-App Browser, sem opção de saída externa.
- B — Header: botão de saída externa no header + login social.
- C — Config: opção de saída externa no menu de configurações + login social.

## Chave do experimento no JSON

`mz_test_gotoexternalbrowser` (valores: `a`, `b`, `c`).

## Métrica primária

Comissão esperada por visita (`expected_commission_amount / visitas`).

## Guardrails

- CVR geral não pode cair mais de 2 pp.
- AOV não pode cair mais de 5%.

## Dados disponíveis

CSVs no diretório padrão (`MELIUZ_DATA_DIR`):

- `visits.csv` — 1 linha por saída/click.
- `transactions.csv` — 1 linha por compra atribuída.
- `visit_url_metadata.csv` — JSON com parâmetros `mz_*` por visita.
- `url_params.csv`, `partners.csv`, `channels.csv` — dimensões.

## Pergunta a responder

Qual variante devemos implementar para 100% dos usuários? Por quê?

Use o pipeline padrão do ABx Analyst e entregue o relatório no formato
obrigatório do system prompt.
