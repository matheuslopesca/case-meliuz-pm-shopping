# Checklist — Qualidade dos dados antes de tirar conclusão

> Use SEMPRE antes de mandar qualquer análise para stakeholder.

## Grão

- [ ] Toda chave primária declarada como "1 linha por X" tem `nunique == len`.
- [ ] A chave de aleatorização não duplica dentro do grão.

## Volume

- [ ] Variantes têm volume parecido (desvio < 5%).
- [ ] Janela do teste cobre ≥ 2 ciclos semanais (efeito dia-da-semana).
- [ ] Sample size suficiente para detectar o MDE definido no plano de teste.

## Integridade

- [ ] 100% das FKs em `visits` resolvem em `partners`, `channels`,
      `url_params`, `visit_url_metadata`.
- [ ] 100% das FKs em `transactions` resolvem em `visits`.

## Contaminação

- [ ] % de `customer_id` em mais de uma variante < 2%.
- [ ] Se >2%, decidir tratamento (excluir ou análise sensitivity).

## NaN / Vazios

- [ ] Quantos `mz_test_*` vieram null? Por quê?
- [ ] `utm_term` vazio é válido (situação base) ou bug de instrumentação?

## Anomalias temporais

- [ ] Plot de visits por dia: queda atípica? deploy quebrou tracking?
- [ ] Há valores de `sale_amount` negativos ou zero? Investigar.

## Sanity checks de negócio

- [ ] Comissão / cashback ratio fica em faixa esperada (ex: 1.5x-3x).
- [ ] Top-10 parceiros somam a fatia esperada do GMV.
- [ ] AOV está em faixa razoável para o segmento (Shopping ~ R$200-700).
