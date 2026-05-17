"""
02_metrics.py — Cálculo das métricas do teste A/B/C In-App Browser.

O que produzimos:
  - Tabela de resumo por variante (visits, compradores, transações, GMV, cashback, comissão).
  - CVR (taxa de conversão por visita), AOV (ticket médio), GMV/visita,
    Comissão/visita (a métrica que mais importa para a Méliuz).
  - Testes estatísticos: z-test de duas proporções para CVR e bootstrap
    para AOV/Comissão (sem scipy: implementamos as fórmulas no braço).
  - Cortes adicionais por canal (INAPP x BROWSERDEFAULT) e por feature
    (header / config / login) para entender de onde vem o ganho ou a perda.

Por que cada métrica importa:
  - CVR: mede se a mudança fez mais pessoas comprarem.
  - AOV: detecta se mudou a composição (talvez quem compra agora gasta menos).
  - Comissão/visita = CVR × Comissão média por compra. É a métrica de receita
    para a Méliuz e o melhor proxy de "valor por visita".
  - GMV: tamanho da torta movimentada na loja parceira (proxy de relevância).
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Defaults relativos à raiz do repo; override via env var se necessário.
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("MELIUZ_DATA_DIR", REPO_ROOT / "dados"))
OUT_DIR = Path(os.environ.get("MELIUZ_OUT_DIR", REPO_ROOT / "outputs"))
OUT_DIR.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(42)


# ---------- carga e preparação ----------

def carregar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lê visits, transactions e a base enriquecida produzida pelo 01_explore.py."""
    visits = pd.read_csv(DATA_DIR / "visits.csv", encoding="utf-8-sig")
    tx = pd.read_csv(DATA_DIR / "transactions.csv", encoding="utf-8-sig")
    enriched = pd.read_csv(OUT_DIR / "visits_enriched.csv")
    return visits, tx, enriched


def preparar_visit_level(enriched: pd.DataFrame, tx: pd.DataFrame) -> pd.DataFrame:
    """Constrói a granularidade-visita: 1 linha por visita, com soma de compras.

    Por que somar antes de juntar:
      - Uma visit_id pode ter mais de uma transação. Se fizéssemos join direto,
        contaríamos a mesma visita várias vezes na hora de medir CVR.
      - Agregamos transações por visit_id para obter (compras, GMV, cashback,
        comissão) por visita, e depois fazemos LEFT JOIN com a base de visitas.
    """
    tx_g = tx.groupby("visit_id").agg(
        n_tx=("transaction_id", "count"),
        gmv=("sale_amount", "sum"),
        cashback=("cashback_amount", "sum"),
        commission=("expected_commission_amount", "sum"),
    ).reset_index()

    base = enriched.merge(tx_g, on="visit_id", how="left")
    for col in ["n_tx", "gmv", "cashback", "commission"]:
        base[col] = base[col].fillna(0.0)
    base["converted"] = (base["n_tx"] > 0).astype(int)
    return base


# ---------- estatística sem scipy ----------

def z_test_two_proportions(s1: int, n1: int, s2: int, n2: int) -> dict:
    """z-test de duas proporções (two-sided) e IC95% pela diferença.

    s1, n1 = sucessos e tamanho do grupo controle
    s2, n2 = sucessos e tamanho do grupo tratamento
    Retorna dict com p1, p2, lift_abs, lift_rel, z, p_value, ic95.
    """
    p1, p2 = s1 / n1, s2 / n2
    p_pool = (s1 + s2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se if se > 0 else 0.0
    # CDF da normal padrão usando erf (puro stdlib, sem scipy):
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    ic95 = ((p2 - p1) - 1.96 * se_diff, (p2 - p1) + 1.96 * se_diff)
    return dict(
        p_controle=p1, p_tratamento=p2,
        lift_abs=p2 - p1, lift_rel=(p2 / p1 - 1) if p1 > 0 else float("nan"),
        z=z, p_value=p_value, ic95=ic95,
    )


def bootstrap_diff_mean(x_control: np.ndarray, x_treat: np.ndarray,
                        n_boot: int = 2000) -> dict:
    """Bootstrap percentile para diferença de médias (IC95%).

    Útil para comparar AOV, comissão/visita etc., onde os dados são fortemente
    assimétricos (caudas longas). Não exige scipy.
    """
    diff = x_treat.mean() - x_control.mean()
    diffs = np.empty(n_boot)
    n1, n2 = len(x_control), len(x_treat)
    for i in range(n_boot):
        a = RNG.choice(x_control, n1, replace=True)
        b = RNG.choice(x_treat, n2, replace=True)
        diffs[i] = b.mean() - a.mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return dict(diff=diff, ic95=(float(lo), float(hi)),
                mean_control=float(x_control.mean()),
                mean_treat=float(x_treat.mean()))


# ---------- agregações ----------

def resumo_por_variante(base: pd.DataFrame) -> pd.DataFrame:
    """Resumo das métricas por variante, no grão visita."""
    g = base.groupby("variant", dropna=False).agg(
        visits=("visit_id", "count"),
        customers=("customer_id", "nunique"),
        buyers=("converted", "sum"),
        n_tx=("n_tx", "sum"),
        gmv=("gmv", "sum"),
        cashback=("cashback", "sum"),
        commission=("commission", "sum"),
    ).reset_index()
    g["cvr"] = g["buyers"] / g["visits"]
    g["aov"] = g["gmv"] / g["n_tx"].where(g["n_tx"] > 0)
    g["commission_per_visit"] = g["commission"] / g["visits"]
    g["gmv_per_visit"] = g["gmv"] / g["visits"]
    g["cashback_per_visit"] = g["cashback"] / g["visits"]
    return g


def resumo_por_variante_e_canal(base: pd.DataFrame) -> pd.DataFrame:
    """Quebra por canal final: INAPP x BROWSERDEFAULT.

    Importante porque é a "lente" do produto: o usuário que sai pelo navegador
    externo converte mais ou menos?
    """
    g = base.groupby(["variant", "channel_id"], dropna=False).agg(
        visits=("visit_id", "count"),
        buyers=("converted", "sum"),
        n_tx=("n_tx", "sum"),
        gmv=("gmv", "sum"),
        commission=("commission", "sum"),
    ).reset_index()
    g["cvr"] = g["buyers"] / g["visits"]
    g["commission_per_visit"] = g["commission"] / g["visits"]
    return g


def resumo_por_feature_de_saida(base: pd.DataFrame) -> pd.DataFrame:
    """Para B e C, separa o tipo de saída externa (header / config / login).

    Responde: o login social converte melhor que o ponto de descoberta?
    O header/config tem o mesmo perfil de venda?
    """
    sub = base[base["utm_content"] == "EXTERNAL_BROWSER_MODAL"].copy()
    g = sub.groupby(["variant", "utm_term"], dropna=False).agg(
        visits=("visit_id", "count"),
        buyers=("converted", "sum"),
        n_tx=("n_tx", "sum"),
        gmv=("gmv", "sum"),
        commission=("commission", "sum"),
    ).reset_index()
    g["cvr"] = g["buyers"] / g["visits"]
    g["commission_per_visit"] = g["commission"] / g["visits"]
    return g


# ---------- pipeline ----------

def main() -> None:
    print("[load] carregando dados…")
    _, tx, enriched = carregar()
    print(f"[load] visits_enriched={len(enriched):,}  transactions={len(tx):,}")

    base = preparar_visit_level(enriched, tx)
    print(f"[prep] base granularidade-visita: {len(base):,} linhas")

    # Mantemos apenas visitas com variante atribuída (intent-to-treat por visita).
    abc = base[base["variant"].isin(["a", "b", "c"])].copy()
    print(f"[filter] visitas com variante a/b/c: {len(abc):,} ({len(abc)/len(base)*100:.1f}%)")

    print("\n=== RESUMO POR VARIANTE ===")
    resumo = resumo_por_variante(abc)
    print(resumo.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    resumo.to_csv(OUT_DIR / "resumo_por_variante.csv", index=False)

    print("\n=== RESUMO POR VARIANTE x CANAL ===")
    rcanal = resumo_por_variante_e_canal(abc)
    print(rcanal.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    rcanal.to_csv(OUT_DIR / "resumo_por_variante_canal.csv", index=False)

    print("\n=== RESUMO POR FEATURE DE SAÍDA EXTERNA ===")
    rfeat = resumo_por_feature_de_saida(abc)
    print(rfeat.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
    rfeat.to_csv(OUT_DIR / "resumo_por_feature.csv", index=False)

    # ---------- TESTES ESTATÍSTICOS ----------
    print("\n=== TESTES ESTATÍSTICOS — CVR (z-test de proporções) ===")
    a = abc[abc["variant"] == "a"]
    b = abc[abc["variant"] == "b"]
    c = abc[abc["variant"] == "c"]
    sa, na = a["converted"].sum(), len(a)
    sb, nb = b["converted"].sum(), len(b)
    sc, nc = c["converted"].sum(), len(c)

    comparisons = [
        ("B vs A", sa, na, sb, nb),
        ("C vs A", sa, na, sc, nc),
        ("C vs B", sb, nb, sc, nc),
    ]
    rows = []
    for nome, s1, n1, s2, n2 in comparisons:
        r = z_test_two_proportions(s1, n1, s2, n2)
        print(f"  {nome}: CVR ctrl={r['p_controle']*100:.3f}% "
              f"trat={r['p_tratamento']*100:.3f}% "
              f"lift_rel={r['lift_rel']*100:+.2f}% "
              f"z={r['z']:.2f} p={r['p_value']:.4g} "
              f"IC95%=[{r['ic95'][0]*100:+.3f}pp, {r['ic95'][1]*100:+.3f}pp]")
        rows.append({"comparacao": nome, **{k: v for k, v in r.items() if k != "ic95"},
                     "ic95_lo": r["ic95"][0], "ic95_hi": r["ic95"][1]})
    pd.DataFrame(rows).to_csv(OUT_DIR / "ztest_cvr.csv", index=False)

    print("\n=== BOOTSTRAP — COMISSÃO POR VISITA ===")
    boot_rows = []
    for nome, ctrl_df, treat_df in [
        ("B vs A", a, b),
        ("C vs A", a, c),
        ("C vs B", b, c),
    ]:
        r = bootstrap_diff_mean(ctrl_df["commission"].values,
                                treat_df["commission"].values, n_boot=1000)
        print(f"  {nome}: ctrl={r['mean_control']:.4f}  trat={r['mean_treat']:.4f}  "
              f"diff={r['diff']:+.4f}  IC95%=[{r['ic95'][0]:+.4f}, {r['ic95'][1]:+.4f}]")
        boot_rows.append({"comparacao": nome, **{k: v for k, v in r.items() if k != "ic95"},
                          "ic95_lo": r["ic95"][0], "ic95_hi": r["ic95"][1]})
    pd.DataFrame(boot_rows).to_csv(OUT_DIR / "bootstrap_commission.csv", index=False)

    print("\n=== BOOTSTRAP — GMV POR VISITA ===")
    for nome, ctrl_df, treat_df in [
        ("B vs A", a, b),
        ("C vs A", a, c),
        ("C vs B", b, c),
    ]:
        r = bootstrap_diff_mean(ctrl_df["gmv"].values,
                                treat_df["gmv"].values, n_boot=1000)
        print(f"  {nome}: ctrl={r['mean_control']:.4f}  trat={r['mean_treat']:.4f}  "
              f"diff={r['diff']:+.4f}  IC95%=[{r['ic95'][0]:+.4f}, {r['ic95'][1]:+.4f}]")

    # Salva base granularidade-visita para o notebook de visualização.
    abc.to_csv(OUT_DIR / "base_visit_level_abc.csv", index=False)
    print(f"\n[ok] base visit-level salva em {OUT_DIR/'base_visit_level_abc.csv'}")


if __name__ == "__main__":
    main()
