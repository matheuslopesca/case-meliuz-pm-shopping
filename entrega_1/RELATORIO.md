# Entrega 1 — Análise do Teste A/B/C e Recomendação

> **Teste:** In-App Browser com opção de saída externa (Header vs Config)
> **Período de análise:** janela completa fornecida pelo BI da Méliuz
> **Métrica-norte:** comissão esperada por visita
> **Decisão recomendada:** **manter A (controle)**. Não escalar B nem C.

---

## 1. TL;DR (leia primeiro)

1. **Recomendação: não implementar B (Header) nem C (Config).** Manter o fluxo
   atual do In-App Browser (variante A) para 100% dos usuários.
2. **B (Header) destrói valor de forma estatisticamente robusta:** queda de
   **−2,03% relativa em CVR** (p = 0,0006, IC95% = [−0,41 pp; −0,11 pp]) e
   **−R$ 0,34 por visita em comissão** (IC95% = [−R$ 0,57; −R$ 0,11]). A −R$ 0,34
   por visita, em 385 mil visitas no teste, isso equivale a ~**R$ 132 mil perdidos
   só no período do experimento**.
3. **C (Config) é praticamente neutro:** lift de CVR não é significativo (p = 0,076)
   e comissão por visita varia em torno de zero (IC95% inclui zero). Não há ganho.
4. **A causa-raiz é clara:** sempre que o usuário sai pelo navegador externo
   (`mz_redirect = browserdefault`) a comissão por visita cai pela metade ou mais
   (R$ 2,49–R$ 2,94 vs R$ 5,55 no InApp). O culpado mais provável: **quebra de
   atribuição** quando a sessão sai do app.
5. **A próxima aposta certa não é "esconder ou mostrar mais a saída externa".**
   É **resolver o problema que motiva a saída** (login social, performance,
   confiança no parceiro) dentro do In-App Browser. Detalhamos isso na Entrega 2.

---

## 2. Respostas às perguntas do enunciado

### 2.1. Por que um app de cashback teria um In-App Browser?

Porque o ato de gerar cashback exige que duas coisas aconteçam em sequência
sem perder a costura entre elas:

1. **Atribuição comercial.** A Méliuz só recebe a comissão da loja se o tracking
   (parâmetros UTM + identificadores na URL) chegar intacto até a conclusão da
   compra. Em um navegador externo, cookies de terceiros, ITP, deep links e
   apps concorrentes podem cortar essa cadeia. No In-App Browser, a Méliuz
   controla a janela inteira.
2. **Experiência integrada.** A jornada — descobrir loja, ativar cashback,
   comprar, ver cashback creditado — vive dentro do app. Sair para Safari ou
   Chrome quebra esse ciclo: o usuário pode esquecer de voltar, perder o
   contexto, ou comprar a próxima vez direto na loja, descashbackando a
   transação no agregado.

Em outras palavras, **o In-App Browser não é uma "telinha" técnica: é o
mecanismo que protege a margem unitária de cada saída e a recorrência do
usuário no app.**

### 2.2. Qual problema de produto este teste tenta resolver?

O time hipoteticamente identificou que **uma fatia dos usuários quer/precisa
sair para o navegador externo**. Causas plausíveis (não exclusivas):

- O usuário **já está logado na loja** no Safari/Chrome e perde isso ao usar
  o WebView do app, o que quebra carrinho, endereço salvo, métodos de pagamento.
- Sites de loja **performam pior dentro do WebView** (alguns bloqueiam
  cookies, alguns têm telas que não cabem no WebView, alguns exigem 3DS que
  não funciona no app).
- O usuário **não confia que está num ambiente seguro** (visual InApp pode
  parecer "menos legítimo" para alguns segmentos).

O teste tenta oferecer uma "válvula de escape" controlada (header em B,
config em C) e medir se essa válvula gera mais conversão (porque libera
usuários travados) ou menos (porque a atribuição quebra na saída).

### 2.3. Qual o trade-off entre In-App Browser e saída para navegador externo?

| Aspecto | In-App Browser | Navegador externo |
|---|---|---|
| **Atribuição** | Forte. Cookies próprios, deep linking controlado. | Frágil. ITP, troca de janela, perda de UTM. |
| **Experiência** | Controlada, sem multi-app. Pode bater em login. | Familiar para o usuário (sessões existentes). |
| **Confiabilidade** | Variável site a site. | Padrão de mercado. |
| **Métricas para o produto** | Eventos completos do funil. | Funil "termina" no momento da saída. |
| **Performance** | Depende do WebView do SO. | Otimizado pelo navegador nativo. |
| **Risco competitivo** | Usuário fica no app Méliuz. | Usuário fica exposto a outras notificações. |

A saída externa cobra um **preço alto em atribuição/receita** (perdemos visibilidade
e dinheiro) em troca de um **ganho incerto em conversão** (talvez alguns usuários
travados consigam concluir). Os dados deste teste mostram que esse trade-off
está **claramente desequilibrado contra a saída externa**.

### 2.4. Qual hipótese cada variante parece testar?

| Variante | Hipótese implícita |
|---|---|
| **A — Controle** | "O In-App Browser sozinho é o melhor experimento custo-benefício." |
| **B — Header (alta descoberta)** | "Se eu der uma saída externa muito visível (botão no header) + login social, libero usuários travados e converto mais — apesar do risco de atribuição." |
| **C — Config (baixa descoberta)** | "Se eu der a mesma saída, mas escondida no menu de configurações, mantenho o ganho para quem realmente precisa, sem 'sangrar' atribuição da massa." |

Em ambos B e C, o login social é apresentado em conjunto com a saída externa
(`utm_term=login`) — então o teste mistura duas mudanças, e isso precisa ser
isolado na leitura (ver Insights, seção 5).

### 2.5. Como definir e calcular a métrica de sucesso?

Para um produto de cashback, a métrica que melhor captura "valor por saída"
é **comissão esperada por visita**:

```
commission_per_visit_v = Σ expected_commission_amount[transacoes_da_variante_v]
                        ÷ visitas_da_variante_v
```

CVR e AOV são diagnósticos. A comissão por visita combina os dois e é a única
que dimensiona impacto financeiro direto para a Méliuz.

Estatística aplicada:

- **CVR** (proporção de visitas que viram compra): z-test de duas proporções
  com correção de pool para o erro-padrão.
- **AOV** (ticket médio): bootstrap percentile 95% (distribuição muito
  assimétrica, t-test seria sensível à cauda).
- **Comissão por visita e GMV por visita**: bootstrap também.

Tudo isso está em `/repo/analise/02_metrics.py` com função `z_test_two_proportions`
e `bootstrap_diff_mean` implementadas sem dependências externas para auditoria.

### 2.6. Qual versão deve ser implementada? Por quê?

**Versão A (controle).** A análise mostra que:

- **B perde** CVR e comissão por visita com IC95% inteiramente negativo.
- **C é neutra** — não justifica o custo de manter um novo fluxo, opção no menu,
  estados de UI, eventos extras e suporte técnico.

Mesmo que B ou C tivessem um lift positivo pequeno, o custo de manutenção de
uma feature em produção (testes, design system, regressões, edge cases por
parceiro) só se paga quando o ganho é claro e relevante. Aqui não é.

A pergunta certa **não é** "qual variante implementar"; é "**o que vamos fazer
em relação ao problema que motivou o teste**" — e isso vira a Entrega 2.

---

## 3. Análise estruturada dos dados

### 3.1. Limpeza e tratamento

- Encoding UTF-8 com BOM em vários CSVs → leitura com `encoding="utf-8-sig"`.
- Variante extraída de `visit_url_metadata.tracking_url_params` (JSON) pelo campo
  `mz_test_gotoexternalbrowser`. Quem não tem o campo → `variant = None`
  (4,2% das visitas; tratamos como fora do teste e descartamos para análise A/B/C).
- `utm_content` e `utm_term` vêm de `url_params.csv`; alguns valores estão em
  caixa alta (`EXTERNAL_BROWSER_MODAL`) — já consistente.
- Compras múltiplas por visita: agregamos `transactions` por `visit_id` antes
  do join (somando `sale_amount`, `cashback_amount`, `expected_commission_amount`)
  para evitar dupla contagem.
- Verificamos contaminação cruzada (usuário em mais de uma variante):
  **3.712 clientes em ≥2 variantes (0,97% da base)**. Mantivemos no
  intent-to-treat por visita por ser percentual baixo; sanity check mostrou
  que os resultados não mudam materialmente excluindo-os.

### 3.2. Identificação das variantes

| Variante | Visitas | % do total | Customers únicos |
|---|---:|---:|---:|
| A — Controle | 377.716 | 31,5% | 128.804 |
| B — Header | 385.757 | 32,2% | 128.738 |
| C — Config | 383.870 | 32,1% | 128.478 |
| Sem `mz_test_*` | 50.122 | 4,2% | — (excluído) |

Distribuição balanceada — sem indício de problema na aleatorização.

### 3.3. Tabela master de resultados (grão visita)

| Métrica | A | B | C | Δ B vs A | Δ C vs A |
|---|---:|---:|---:|---|---|
| Visitas | 377.716 | 385.757 | 383.870 | +2,1% | +1,6% |
| Compradores | 48.607 | 48.632 | 48.878 | +0,1% | +0,6% |
| Nº transações | 50.639 | 50.543 | 51.346 | −0,2% | +1,4% |
| **CVR** | **12,87%** | **12,61%** | **12,73%** | **−0,26 pp (p=0,0006)** | **−0,14 pp (p=0,076)** |
| **AOV** | R$ 540,52 | R$ 501,51 | R$ 530,40 | −R$ 39,01 | −R$ 10,12 |
| **GMV/visita** | R$ 72,47 | R$ 65,71 | R$ 70,95 | −R$ 6,76 | −R$ 1,52 |
| **Comissão/visita** | **R$ 5,56** | **R$ 5,22** | **R$ 5,50** | **−R$ 0,34** | **−R$ 0,06** |
| GMV total | R$ 27,4 M | R$ 25,3 M | R$ 27,2 M | — | — |
| Comissão total | R$ 2,10 M | R$ 2,01 M | R$ 2,11 M | — | — |

> **Como ler:** a coluna "Δ" mostra a diferença entre tratamento e controle.
> Verde-conceitual = bom; aqui, todos os deltas relevantes são neutros ou negativos.

### 3.4. Inferência estatística

z-test de duas proporções para CVR:

| Comparação | CVR ctrl | CVR trat | Lift relativo | z | p-valor | IC95% (pp) |
|---|---:|---:|---:|---:|---:|---|
| B vs A | 12,869% | 12,607% | **−2,03%** | −3,43 | **0,0006** | [−0,411 ; −0,112] |
| C vs A | 12,869% | 12,733% | −1,05% | −1,77 | 0,076 | [−0,286 ; +0,014] |
| C vs B | 12,607% | 12,733% | +1,00% | +1,66 | 0,096 | [−0,023 ; +0,275] |

Bootstrap (1.000 reamostras) para comissão por visita:

| Comparação | Comissão ctrl | Comissão trat | Diff | IC95% |
|---|---:|---:|---:|---|
| B vs A | R$ 5,5598 | R$ 5,2178 | **−R$ 0,3420** | **[−R$ 0,57 ; −R$ 0,11]** |
| C vs A | R$ 5,5598 | R$ 5,5043 | −R$ 0,0556 | [−R$ 0,30 ; +R$ 0,19] |
| C vs B | R$ 5,2178 | R$ 5,5043 | +R$ 0,2864 | [+R$ 0,06 ; +R$ 0,51] |

**Interpretação:**
- B vs A: significativo e negativo em **CVR**, **comissão/visita** e **GMV/visita**.
- C vs A: IC abrange zero em todas as três métricas; tratado como **neutro**.
- C vs B: C é melhor que B (consistente com a teoria de "esconder a válvula").

### 3.5. Cortes que iluminam o porquê

#### a) Por canal final (INAPP vs BROWSERDEFAULT)

| Variante | Canal | Visitas | CVR | Comissão/visita |
|---|---|---:|---:|---:|
| A | InApp | 377.716 | 12,87% | R$ 5,56 |
| B | InApp | 376.350 | 12,64% | R$ 5,29 |
| B | Browser externo | 9.407 | **11,46%** | **R$ 2,49** |
| C | InApp | 376.513 | 12,77% | R$ 5,55 |
| C | Browser externo | 7.357 | **11,01%** | **R$ 2,94** |

**O canal externo é tóxico para a comissão por visita.** Ele converte menos
*e* gera menos comissão *quando converte* — provavelmente porque uma parte
das compras concluídas no navegador externo **não está sendo atribuída** à
Méliuz (cookies de terceiros, ITP no iOS, deeplink que abre outro app).

#### b) Por tipo de saída (utm_term)

| Variante | utm_term | Visitas | CVR | Comissão/visita |
|---|---|---:|---:|---:|
| B | HEADER | 5.872 | 11,60% | **R$ 2,98** |
| B | LOGIN | 3.535 | 11,23% | **R$ 1,66** |
| C | CONFIG | 3.896 | 11,81% | **R$ 4,59** |
| C | LOGIN | 3.461 | 10,11% | **R$ 1,09** |

Dois insights importantes aqui:

- **CONFIG converte melhor que HEADER em comissão por visita** (R$ 4,59 vs
  R$ 2,98). Pode ser viés de seleção: quem vai até o menu Config é mais
  intencional — talvez já tenha carrinho na loja, então a compra ocorre logo
  em seguida.
- **LOGIN é o pior caso** nas duas variantes (R$ 1,66 e R$ 1,09). Quando o
  usuário sai para fazer login social no navegador externo, a sessão fica
  fragmentada. Hipótese: ele autentica, é redirecionado para um endereço sem
  os parâmetros de atribuição, e a compra (quando ocorre) não conta para a Méliuz.

---

## 4. Recomendação fundamentada

### 4.1. Decisão

**Não implementar B nem C. Manter A (controle) para 100% dos usuários.**

### 4.2. Impacto esperado

Se a Méliuz tivesse lançado B para 100% (cenário hipotético):

- Comissão/visita: **−R$ 0,34** × volume mensal do Shopping.
- Tomando a magnitude do experimento como referência (~385 mil visitas em B),
  estimo o "evitar perda" da decisão correta em **~R$ 1,5 a 2 M / ano** em
  comissão (proporcionalmente ao volume anual da operação Shopping; a Méliuz
  conhece o número exato e deve recalcular).

Se a Méliuz tivesse lançado C para 100%:

- Comissão/visita: variação dentro do ruído. Impacto financeiro líquido próximo
  de zero — mas com **custo de manutenção** (eng + design + suporte) que não
  se justifica.

### 4.3. Plano de descontinuação

1. Encerrar o experimento na próxima janela de release (manter A como default).
2. Retirar a flag `mz_test_gotoexternalbrowser` do código (remover dívida técnica).
3. Manter os eventos `external_browser_modal` e os UTMs `header`/`config`/`login`
   no schema de tracking por mais 30 dias, para análises retroativas/contestações.
4. Compartilhar os aprendizados em um post-mortem público (cultura de
   transparência).

### 4.4. Riscos, limitações e cuidados

- **Atribuição perdida não medida.** Algumas das compras "que sumiram" na saída
  externa podem ter ocorrido e simplesmente não foram atribuídas. Isso significa
  que a queda real de **conversão** pode ser menor que parece, mas a queda real
  de **receita para a Méliuz** é exatamente a que vimos (a receita só existe se
  for atribuída).
- **Confounder de UX adicional.** Em B e C, a saída externa veio bundled com
  "fluxo de login social". Ainda não conseguimos isolar o efeito puro do botão
  no header vs o efeito do login social. Próximo teste precisa decompor isso.
- **Viés de auto-seleção dentro do tratamento.** Quem clica em "abrir no
  navegador" é, por definição, um usuário com mais fricção. Compará-lo direto
  com usuários do controle InApp é injusto. A análise por *intent-to-treat*
  (todos os usuários da variante, cliquem ou não) é a correta para a decisão e
  é a que usamos para a recomendação.
- **Sazonalidade.** A janela do teste pega o período de dezembro/2025 a
  janeiro/2026, com Black Friday tardia e início de ano. O efeito pode estar
  amplificado em parceiros sazonais — não invalida a decisão, mas vale o
  follow-up em janela "normal".
- **3.712 customers (~0,97%) apareceram em mais de uma variante.** Refizemos
  os cálculos excluindo-os; resultado não muda materialmente, mas o ideal seria
  ajustar a chave de aleatorização para fixar variante por `customer_id`.

---

## 5. Insights adicionais

### 5.1. O que os dados revelam além da pergunta principal

- **A queda de AOV em B é o maior dado a investigar.** R$ 540 → R$ 502 é uma
  queda de 7,2% no ticket médio. Possível explicação: usuários que saem pelo
  header podem estar finalizando compras menores que aprenderam a fazer no
  carrinho que já tinham na loja, enquanto quem fica InApp explora mais e
  acrescenta itens. Vale validar.
- **CONFIG converte mais que HEADER em comissão/visita (R$ 4,59 vs R$ 2,98)
  — mesmo com menor volume.** Sugere que o público "intencional" (vai
  ao menu) compensa o público "exploratório" (vê o botão no header). Para
  Shopping, intencionalidade é mais lucrativa.
- **LOGIN é universalmente ruim**, ignorando a variante. Em vez de "deixar o
  usuário logar fora", devemos focar em **resolver login dentro do InApp** —
  esse é o próximo teste com maior potencial (ver Entrega 2).

### 5.2. Como interpretar as saídas

- **Saída normal pela tela do parceiro** (`utm_content = PARTNER_PAGE`,
  `mz_redirect = inapp`): é a jornada padrão. Esperada e correta. Métrica de
  controle natural.
- **Saída externa via Header (`utm_term = header`)**: usuário viu o botão no
  topo enquanto navegava. Indica "saída exploratória" — pode ser curiosidade
  ou frustração.
- **Saída externa via Config (`utm_term = config`)**: usuário foi ao menu de
  configurações e mudou intencionalmente. Indica "saída deliberada" — usuário
  já decidiu por algum motivo concreto.
- **Saída externa via Login (`utm_term = login`)**: usuário disparou login
  social que abriu navegador externo. Indica "saída forçada por
  arquitetura" — não é uma escolha do usuário, é uma consequência do desenho.
  É a mais perigosa para atribuição.

### 5.3. Novas perguntas que eu faria com mais tempo/dados

1. **Quanto de comissão "perdida" no canal externo é, na verdade, atribuição
   incorreta?** Cruzar com cookies de pós-clique do parceiro para estimar o
   *gap*.
2. **Existem parceiros onde a saída externa converte tão bem quanto InApp?**
   Se sim, podemos manter saída externa só para esses (allowlist por
   `partner_id`).
3. **Qual o impacto de longo prazo (D7, D30) de uma sessão que sai vs uma
   que fica?** Saídas podem afetar recorrência futura, não só a venda do
   momento.
4. **Quão sensível é o resultado ao SO?** iOS tem ITP; Android é menos
   restritivo. Talvez B funcione em Android e seja desastre em iOS.
5. **Quem é o "comprador externo de alto valor"?** Talvez existam usuários
   power-users que precisam da saída — para eles, oferecer uma rota oculta
   gera ganho.

---

## 6. Processo, IA e escalabilidade

### 6.1. Como rodei a análise

Sequência reprodutível:

```
01_explore.py        → grão, integridade, identificação das variantes
02_metrics.py        → agregações, z-test, bootstrap
03_visualizations.py → gráficos para o relatório
```

Saídas em `/repo/outputs/`:
- `resumo_por_variante.csv`
- `resumo_por_variante_canal.csv`
- `resumo_por_feature.csv`
- `ztest_cvr.csv`
- `bootstrap_commission.csv`
- `graficos/*.png`

### 6.2. Como validei o resultado

- Comparação manual: `df.groupby('variant')['converted'].mean()` vs a coluna
  `cvr` da tabela de resumo. Bate.
- Sanity check do número total de transações: `transactions.shape[0] = 160.269`;
  somando `n_tx` por variante na base granularidade-visita: 50.639 + 50.543 +
  51.346 + (50.122 sem variant ≈ ~7.700 tx) ≈ 160k. Bate.
- z-test re-implementado sem scipy; rodei a mesma comparação na calculadora
  de Evan Miller e obtive z e p coincidentes.
- Bootstrap: rodei com `seed=42` para reprodutibilidade e re-rodei com `seed=7`
  para checar estabilidade do IC. Variação < 0,5% na diferença média.

### 6.3. Como o agente é reutilizável

A pasta `/agent` contém:

- `SYSTEM_PROMPT.md`: define identidade, princípios, pipeline padrão e
  critérios de decisão. Reuso direto em outros testes A/B/C.
- `RUNBOOK.md`: passo a passo operacional para o PM aplicar em um novo teste
  (briefing → script → relatório).
- `templates/REPORT_TEMPLATE.md`: estrutura obrigatória do relatório final
  (TL;DR, contexto, resultados, recomendação, riscos, apêndice).
- `templates/PRD_TEMPLATE.md`: estrutura padrão de PRD (usada na Entrega 2).
- `checklists/QA_DADOS.md` e `checklists/QA_RELATORIO.md`: revisão prévia ao
  shipping de qualquer análise.

Para um próximo teste do time de Shopping, basta:

1. Trocar a chave do experimento (`mz_test_<nome>`) no `01_explore.py`.
2. Atualizar o `test_brief.md` com a hipótese e o MDE.
3. Rodar os três scripts.
4. Alimentar o agente com os CSVs de output + briefing.
5. Aplicar a checklist QA antes de enviar para o stakeholder.

Tempo estimado por teste: **30 min a 1h de análise** + meia hora de revisão.

---

## 7. Apêndice: gráficos

Os arquivos PNG estão em `/repo/outputs/graficos/`:

- `g1_cvr_por_variante.png` — CVR por variante.
- `g2_comissao_por_variante.png` — Comissão por visita por variante.
- `g3_canal_externo.png` — Comissão por canal (InApp vs externo).
- `g4_feature_saida.png` — Comissão por tipo de saída externa.
- `g5_lifts_com_ic.png` — Forest plot dos lifts com IC95%.

---

## 8. Apêndice: definição matemática das estatísticas

**z-test de duas proporções (pooled):**

```
p̂_pool = (s1 + s2) / (n1 + n2)
SE = sqrt( p̂_pool · (1 − p̂_pool) · (1/n1 + 1/n2) )
z = (p̂2 − p̂1) / SE
p_value = 2 · (1 − Φ(|z|))
```

**IC95% da diferença de proporções (Wald):**

```
SE_diff = sqrt( p̂1·(1−p̂1)/n1 + p̂2·(1−p̂2)/n2 )
IC95% = (p̂2 − p̂1) ± 1.96 · SE_diff
```

**Bootstrap percentile (média):**

```
para i em 1..B:
  amostra_ctrl_i = bootstrap(controle)
  amostra_trat_i = bootstrap(tratamento)
  diff_i = média(amostra_trat_i) − média(amostra_ctrl_i)
IC95% = (percentil_2.5(diff_i), percentil_97.5(diff_i))
```

Implementação completa em `/repo/analise/02_metrics.py`.
