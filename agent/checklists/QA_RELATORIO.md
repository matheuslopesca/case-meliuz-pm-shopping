# Checklist — QA do relatório de análise

> Aplicar antes de compartilhar o relatório com stakeholders (líder de produto,
> head, eng manager). Cada item é binário: passa ou não passa.

## Aderência ao formato

- [ ] TL;DR em 3-5 bullets, com a decisão na primeira linha.
- [ ] Todas as 9 seções do template estão presentes.
- [ ] Apêndice metodológico contém fórmulas e queries usadas.

## Aderência aos dados

- [ ] Cada número citado na narrativa bate com `resumo_por_variante.csv`.
- [ ] Cada IC95% citado bate com `ztest_cvr.csv` ou `bootstrap_*.csv`.
- [ ] Gráficos têm labels numéricas legíveis (não só barras coloridas).

## Aderência ao critério de decisão

- [ ] A recomendação respeita a tabela ship/iterate/kill/inconclusive.
- [ ] Se o p<0.05 mas efeito é tiny, isso está explicitado.
- [ ] Se o p>0.05 mas efeito tem direção clara, isso está explicitado.

## Comunicação

- [ ] Nada de jargão técnico sem explicação na primeira ocorrência.
- [ ] A frase "estatisticamente significante" só aparece com IC reportado.
- [ ] Reading time estimado < 12 minutos para a versão completa.
- [ ] TL;DR fica acima da dobra (entendível sem rolar).

## Storytelling

- [ ] A análise tem um "porquê" claro, não só números.
- [ ] Existe uma seção de "próximos testes" com ≥ 3 hipóteses.
- [ ] Os riscos/limitações estão honestos (não é uma seção pro forma).
