# [Relatório] Teste `mz_test_gotoexternalbrowser` — Saída para navegador externo no In-App Browser

## 1. TL;DR
- **Decisão: kill** os tratamentos. Manter o **controle A** (fluxo padrão do In-App Browser, sem saída externa) para 100% dos usuários.
- **Métrica primária — comissão esperada por visita:**
  - A (controle): **R$ 5,560**
  - B (header + login social): R$ 5,218 → **lift relativo −6,15%** (IC95% da diferença: [−R$ 0,564; −R$ 0,114], inteiramente negativo)
  - C (config + login social): R$ 5,504 → lift relativo −1,00% (IC95% [−R$ 0,279; +R$ 0,175], cruza zero)
- **Risco-chave:** B viola o guardrail de CVR (−2,03% rel., p=0,0006) e derruba AOV em ~7%, com perda material de receita por visita; C é estatisticamente indistinguível de A, então não há ganho que justifique o custo de manter a feature.

## 2. Reconstrução do teste

### Tamanhos amostrais e sanity check da aleatorização
| Variante | Visitas | Share |
|---|---:|---:|
| A (controle) | 377.716 | 32,9% |
| B (header) | 385.757 | 33,6% |
| C (config) | 383.870 | 33,5% |
| sem variante (NaN) | 50.122 | 4,4% (descartadas) |
| **Total** | **1.197.465** | 100% |

- Split entre A/B/C bastante balanceado (~33,3% cada), com pequeno desvio (~1pp) — dentro do esperado para SRM em ~1,15M visitas.
- O JSON `tracking_url_params` contém a chave `mz_test_gotoexternalbrowser` em ~95,8% das visitas; as 50k visitas sem chave foram excluídas das análises.

### Anomalias encontradas
- ~4,4% das visitas sem variante atribuída. Não está claro se são visitas pré-rollout, visitas de versões antigas do app ou bug de tagging. Tratadas como exclusão.
- Não há colunas de plataforma/SO nem versão do app no `visits.csv`, então não foi possível segmentar por iOS/Android (limitação registrada na seção 6).

## 3. Resultados

### Tabela master por variante
| Variante | Visitas | Compradores | CVR | AOV (R$) | Comissão/visita (R$) | GMV/visita (R$) |
|---|---:|---:|---:|---:|---:|---:|
| A — controle | 377.716 | 48.607 | **12,87%** | **540,52** | **5,560** | **72,47** |
| B — header   | 385.757 | 48.632 | 12,61% | 501,51 | 5,218 | 65,71 |
| C — config   | 383.870 | 48.878 | 12,73% | 530,40 | 5,504 | 70,95 |

### Comparações estatísticas

**B vs A (header vs controle)**
| Métrica | Lift abs. | Lift rel. | IC95% | p-valor | Veredito |
|---|---:|---:|---|---:|---|
| CVR | −0,262 pp | −2,03% | [−0,411; −0,112] pp | 0,0006 | **Pior, significativo** |
| Comissão/visita | −R$ 0,342 | −6,15% | [−R$ 0,564; −R$ 0,114] | <0,01 (bootstrap) | **Pior, significativo** |
| GMV/visita | −R$ 6,76 | −9,32% | [−R$ 9,37; −R$ 4,04] | <0,01 (bootstrap) | **Pior, significativo** |
| AOV | −R$ 39,01 | −7,22% | (derivado) | — | Viola guardrail (−5%) |

**C vs A (config vs controle)**
| Métrica | Lift abs. | Lift rel. | IC95% | p-valor | Veredito |
|---|---:|---:|---|---:|---|
| CVR | −0,136 pp | −1,05% | [−0,286; +0,014] pp | 0,076 | Não significativo |
| Comissão/visita | −R$ 0,056 | −1,00% | [−R$ 0,279; +R$ 0,175] | n.s. | Não significativo |
| GMV/visita | −R$ 1,52 | −2,10% | [−R$ 4,26; +R$ 1,14] | n.s. | Não significativo |
| AOV | −R$ 10,12 | −1,87% | (derivado) | — | Dentro do guardrail |

**C vs B (melhor tratamento vs pior tratamento)**
| Métrica | Lift abs. | Lift rel. | IC95% | p-valor |
|---|---:|---:|---|---:|
| CVR | +0,126 pp | +1,00% | [−0,023; +0,275] pp | 0,096 |

C é direcionalmente melhor que B em CVR, mas a diferença não cruza o limiar de significância.

## 4. Diagnóstico

### Por que B perdeu
B (botão de saída externa no header + login social) **piora simultaneamente CVR (−2,03% rel.), AOV (−7,2%) e GMV/visita (−9,3%)**. Hipóteses prováveis:
1. **Vazamento de atribuição:** o botão visível no header facilita o usuário sair do In-App Browser para o navegador externo, onde a sessão Méliuz/cookies de tracking se quebram. Compras que aconteceriam atribuídas voltam a "sem cashback", reduzindo CVR observada.
2. **Mudança de mix de compradores:** os usuários que ainda convertem em B compram tickets menores (AOV cai 7%) — possivelmente porque os compradores high-AOV (que se sentiam confortáveis no in-app) são justamente os que migram para o navegador externo e se perdem da atribuição.
3. A combinação CVR↓ + AOV↓ amplifica o impacto na métrica-norte (comissão/visita −6,2%), violando os dois guardrails ao mesmo tempo.

### Por que C "empatou"
C (saída no menu de configurações) esconde a porta de saída atrás de cliques adicionais, então o efeito de vazamento de atribuição é muito menor. As métricas ficam **estatisticamente indistinguíveis de A**, com ponto-estimativa levemente abaixo do controle em todas elas. Não há sinal de que login social esteja entregando ganho líquido suficiente para compensar até esse pequeno arrasto.

### Cortes adicionais investigados
- Compradores únicos por variante (~48,6k–48,9k) batem com CVR, descartando explicação por dupla contagem de transações.
- N de transações por variante (50,5k–51,3k) é consistente com o ranking de CVR.
- C tem mais transações que A (51.346 vs 50.639) mas ticket menor — sugere que C atrai marginalmente mais compras pequenas e perde algumas grandes (mesmo padrão que B, em magnitude menor).

## 5. Recomendação

### Decisão final: **KILL ambos os tratamentos. Rollout = 100% A (controle).**

Justificativa resumida:
- **B falha duro:** viola guardrail de CVR (−2pp limite vs −0,26pp observado em CVR e −2% relativo) e guardrail de AOV (−5% limite vs −7,2% observado), e perde R$ 0,34 de comissão por visita com IC95% inteiramente negativo.
- **C não entrega ganho:** ponto-estimativa pior em todas as métricas, IC95% cruza zero. Não há motivo de produto para incorrer no custo de manutenção/UX de uma feature que, na melhor das hipóteses, é neutra.

### Próximos passos imediatos
1. **Desligar o teste** e manter 100% em A.
2. **Investigar o vazamento de atribuição** no fluxo de B: a hipótese de que o botão no header está derrubando rastreamento merece um deep-dive técnico (logs de sessão, taxa de cliques no botão, taxa de compras "órfãs" pós-clique).
3. **Se houver demanda de produto** por uma saída para navegador externo (ex.: pressão de UX/jurídico), reabrir o teste **só** com a variante C, mas com:
   - Tracking robusto que sobreviva à saída para navegador externo (deep link de volta, fingerprint, etc.).
   - Métrica explícita de "perda de atribuição pós-saída" como guardrail.
4. **Reportar à área de growth/produto** que login social isolado (presente em B e C) não mostrou ganho observável de CVR neste experimento — qualquer roadmap baseado nessa premissa precisa de novo teste isolando login social do botão de saída.

## 6. Limitações

- **4,4% das visitas sem variante** atribuída no JSON foram descartadas. Se essa exclusão for não-aleatória (ex.: enviesada por plataforma ou versão de app), os resultados absolutos podem deslocar, embora a comparação entre A/B/C tenda a se manter.
- **Sem segmentação por plataforma (iOS vs Android), por usuário novo vs recorrente, ou por parceiro**, porque o `visits.csv` não traz essas dimensões diretamente e o escopo da análise priorizou as comparações master. É possível que C seja positiva em algum sub-segmento (ex.: usuários que historicamente já usam navegador externo) — recomendado validar antes de descartar 100% a ideia.
- **Login social está confundido com botão de saída externa** em ambos os tratamentos. Não é possível, com este desenho, isolar o efeito do login social do efeito da saída externa.
- **Bootstrap usou 2.000 reamostras** — suficiente para IC95% estável em N~380k, mas IC pode oscilar levemente em casas decimais.
- Janela temporal e efeitos sazonais (o teste cobre dez/2025–jan/2026, possivelmente Black Friday + Natal + pós-festas) não foram decompostos. Um vencedor durante alta sazonalidade pode não se manter no resto do ano — recomendado revisitar pós-rollout em janela "normal".
