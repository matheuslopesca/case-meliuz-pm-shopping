# [Teste XX] — Relatório de análise

> Template versionado. Não altere as seções; preencha-as.

## 1. TL;DR

- Decisão: **{ship | iterate | kill | inconclusive}** — variante recomendada: **{A | B | C}**
- Impacto esperado em 12 meses: **R$ {valor}** em comissão (+{x}% vs controle)
- Risco-chave: {risco}

## 2. Contexto e perguntas

- Hipótese testada: …
- Variantes: …
- Período: …
- Tamanho da amostra: A={n_a}, B={n_b}, C={n_c}

## 3. Como li os dados

- Grão: visita
- Filtros aplicados: …
- Tratamento de NaN: …
- Contaminação cruzada observada: {pct}% (decisão: …)

## 4. Resultados

| Métrica | A | B | C | B vs A | C vs A |
|---|---|---|---|---|---|
| Visitas | | | | — | — |
| Compradores | | | | — | — |
| CVR | | | | …% [IC95%] p=… | …% [IC95%] p=… |
| AOV | | | | | |
| Comissão/visita | | | | | |
| GMV/visita | | | | | |

Inserir gráficos: g1, g2, g3, g4, g5.

## 5. Diagnóstico

- Por que B {ganhou/perdeu}? …
- Por que C {ganhou/perdeu}? …
- Onde está o efeito? (canal? feature? parceiro?) …

## 6. Recomendação

- {Variante}: justificativa.
- Plano de rollout: …
- Stakeholders a alinhar antes do ship: …

## 7. Riscos e limitações

- Limitação 1 …
- Limitação 2 …

## 8. Próximas perguntas

1. …
2. …
3. …

## 9. Apêndice metodológico

- Definição exata de cada métrica.
- Fórmulas dos testes estatísticos.
- Links para queries / scripts.
