# [Relatório] Teste mz_test_gotoexternalbrowser — In-App Browser Exit Option

## 1. TL;DR

- **Decisão: KILL variante B | ITERATE variante C** — recomendação: **manter variante A (controle)**
- **Métrica primária (comissão/visita):**
  - A (controle): R$ 5,56/visita
  - B (header): R$ 5,22/visita → **−6,2% vs controle** (IC95%: [−10,2%; −2,0%])
  - C (config): R$ 5,50/visita → **−1,0% vs controle** (IC95%: [−5,1%; +3,1%])
- **Risco-chave:** A exposição proeminente do botão de saída (variante B) canibaliza conversões significativamente; a opção escondida em configurações (C) é neutra mas sem upside claro.

---

## 2. Reconstrução do teste

### Tamanhos amostrais por variante

| Variante | Descrição | Visitas | Compradores | Transações |
|----------|-----------|---------|-------------|------------|
| A | Controle (sem saída externa) | 377.716 | 48.607 | 50.639 |
| B | Header (botão + login social) | 385.757 | 48.632 | 50.543 |
| C | Config (menu + login social) | 383.870 | 48.878 | 51.346 |
| NaN | Sem variante atribuída | 50.122 | — | — |

**Total analisado:** 1.147.343 visitas (excluídos 50.122 sem variante = 4,2% do tráfego)

### Sanity check da aleatorização

- **Balanceamento:** Desvio máximo de ~2,1% entre grupos (A vs B), aceitável para alocação aleatória.
- **Proporção de visitas:** A = 32,9%, B = 33,6%, C = 33,5% — distribuição uniforme ✓
- **Nenhuma anomalia estrutural identificada** nos dados de atribuição.

### Observações

- Os 50.122 registros sem variante (NaN) provavelmente são visitas de canais não-app ou usuários em versões antigas do app. Foram corretamente excluídos.
- Período implícito: dez/2025 a jan/2026 (baseado em timestamps).

---

## 3. Resultados

### Tabela master de métricas por variante

| Métrica | A (Controle) | B (Header) | C (Config) |
|---------|--------------|------------|------------|
| **CVR** | 12,87% | 12,61% | 12,73% |
| **AOV** | R$ 540,52 | R$ 501,51 | R$ 530,40 |
| **GMV/visita** | R$ 72,47 | R$ 65,71 | R$ 70,95 |
| **Comissão/visita** | R$ 5,560 | R$ 5,218 | R$ 5,504 |
| **GMV total** | R$ 27,37M | R$ 25,35M | R$ 27,23M |
| **Comissão total** | R$ 2,10M | R$ 2,01M | R$ 2,11M |

### Comparações estatísticas

#### B vs A (Header vs Controle)

| Métrica | Lift Absoluto | Lift Relativo | IC95% | p-valor | Status |
|---------|---------------|---------------|-------|---------|--------|
| **CVR** | −0,26 pp | **−2,03%** | [−0,41pp; −0,11pp] | 0,0006 | ❌ Significativo negativo |
| **Comissão/visita** | −R$ 0,342 | **−6,15%** | [−R$0,56; −R$0,11] | <0,01* | ❌ Significativo negativo |
| **GMV/visita** | −R$ 6,76 | **−9,32%** | [−R$9,41; −R$4,11] | <0,01* | ❌ Significativo negativo |

*p-valor derivado do bootstrap (IC não cruza zero)

#### C vs A (Config vs Controle)

| Métrica | Lift Absoluto | Lift Relativo | IC95% | p-valor | Status |
|---------|---------------|---------------|-------|---------|--------|
| **CVR** | −0,14 pp | **−1,05%** | [−0,29pp; +0,01pp] | 0,076 | ⚠️ Marginalmente negativo |
| **Comissão/visita** | −R$ 0,056 | **−1,00%** | [−R$0,29; +R$0,17] | >0,05 | ⚪ Não significativo |
| **GMV/visita** | −R$ 1,52 | **−2,10%** | [−R$4,29; +R$1,31] | >0,05 | ⚪ Não significativo |

#### C vs B (Config vs Header)

| Métrica | Lift Absoluto | Lift Relativo | IC95% | p-valor | Status |
|---------|---------------|---------------|-------|---------|--------|
| **CVR** | +0,13 pp | **+1,00%** | [−0,02pp; +0,27pp] | 0,096 | ⚠️ Marginalmente positivo |
| **Comissão/visita** | +R$ 0,286 | **+5,49%** | [+R$0,05; +R$0,52] | <0,05* | ✅ Significativo positivo |

**Conclusão das comparações:** C > B com significância estatística, mas nem B nem C superam o controle A.

---

## 4. Diagnóstico

### Por que B perdeu (significativamente)?

1. **Visibilidade excessiva da saída:** O botão no header é muito proeminente, incentivando usuários a abandonar o In-App Browser antes de completar a compra.

2. **Quebra do funil de atribuição:** Ao sair para o navegador externo, a sessão de rastreamento é interrompida, e compras subsequentes não são atribuídas ao Méliuz.

3. **Queda generalizada:** Todas as métricas (CVR, AOV, GMV) caíram conjuntamente, indicando um problema sistêmico no fluxo e não apenas em um segmento.

4. **AOV −7,2%:** Usuários que saíram provavelmente completaram compras de maior valor fora do tracking, deixando apenas transações menores atribuídas.

### Por que C foi neutro?

1. **Baixa descoberta:** A opção escondida no menu de configurações teve adoção presumivelmente baixa, minimizando impacto negativo.

2. **Resultado esperado para feature "escondida":** Funciona como um "escape hatch" para power users sem afetar a massa de usuários.

3. **Inconclusivo para upside:** Não há evidência de que o login social compensou as perdas de saída externa.

### Verificação dos guardrails

| Guardrail | Threshold | B vs A | C vs A | Status |
|-----------|-----------|--------|--------|--------|
| CVR não cai >2pp | Max −2pp | −0,26pp | −0,14pp | ✅ Dentro |
| AOV não cai >5% | Max −5% | **−7,2%** | −1,9% | ❌ B viola |

**Variante B viola o guardrail de AOV.**

---

## 5. Recomendação

### Decisão final

| Variante | Decisão | Justificativa |
|----------|---------|---------------|
| **A** | **MANTER** | Performance superior em todas as métricas |
| **B** | **KILL** | Queda significativa de 6,2% em comissão/visita, viola guardrail de AOV |
| **C** | **KILL/ITERATE** | Neutro vs controle, sem benefício que justifique complexidade adicional |

### Próximos passos imediatos

1. **Remover variantes B e C** do experimento e retornar 100% do tráfego para o fluxo A (controle).

2. **Investigar alternativas menos invasivas:** Se o objetivo é oferecer escape para navegador externo, considerar:
   - Mostrar opção apenas após N segundos de inatividade
   - Oferecer apenas quando detectado problema de carregamento
   - A/B testar apenas o login social SEM a opção de saída externa

3. **Analisar comportamento pós-saída:** Se possível, rastrear usuários que usaram a saída externa para entender se houve compras não-atribuídas (perda de tracking vs. perda real de conversão).

4. **Monitorar métricas de satisfação:** NPS ou reclamações relacionadas ao In-App Browser para entender se há demanda real pela feature de saída externa.

---

## 6. Limitações

1. **Sem dados de uso da feature:** Não sabemos quantos usuários efetivamente clicaram no botão de saída externa em B ou C. Isso impediria análise de CACE (efeito sobre os que usaram).

2. **Sem segmentação por parceiro/loja:** Algumas lojas podem funcionar mal no In-App Browser; a feature pode ter valor seletivo.

3. **Atribuição pós-saída desconhecida:** Não é possível medir se usuários que saíram para o browser externo completaram compras depois (fora do tracking).

4. **Período único:** Análise cobre ~1 mês; efeitos sazonais (dez-jan) podem influenciar comportamento.

5. **50K visitas sem variante (4,2%):** Excluídas da análise; se não são aleatórias, pode haver viés marginal.

6. **Sem dados de retenção/LTV:** Impacto de longo prazo na experiência do usuário não foi avaliado.

---

*Relatório gerado pelo ABx Analyst em análise automatizada.*
