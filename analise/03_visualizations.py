"""
03_visualizations.py — Gera os gráficos que sustentam a recomendação.

Cada gráfico responde a uma pergunta específica:
  - g1_cvr_por_variante.png      → "Alguma variante moveu CVR?"
  - g2_comissao_por_variante.png → "E receita por visita (métrica-norte)?"
  - g3_canal_externo.png         → "Quem sai pelo navegador externo converte pior?"
  - g4_feature_saida.png         → "Header, Config e Login: qual o perfil?"
  - g5_lifts_com_ic.png          → "Os lifts são estatisticamente robustos?"
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Default relativo à raiz do repo; override via env var se necessário.
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(os.environ.get("MELIUZ_OUT_DIR", REPO_ROOT / "outputs"))
GRA_DIR = OUT_DIR / "graficos"
GRA_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = {"a": "#4C78A8", "b": "#F58518", "c": "#54A24B"}
LABEL = {"a": "A — Controle", "b": "B — Header", "c": "C — Config"}


def _save(fig, nome: str) -> None:
    caminho = GRA_DIR / nome
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] {caminho}")


def g1_cvr(resumo: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    cores = [PALETTE[v] for v in resumo["variant"]]
    bars = ax.bar([LABEL[v] for v in resumo["variant"]], resumo["cvr"] * 100,
                  color=cores, edgecolor="white")
    for b, v in zip(bars, resumo["cvr"] * 100):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.2f}%",
                ha="center", fontsize=10)
    ax.set_title("CVR por variante (compradores ÷ visitas)")
    ax.set_ylabel("CVR (%)")
    ax.set_ylim(0, max(resumo["cvr"]) * 100 * 1.15)
    ax.grid(axis="y", alpha=0.3)
    _save(fig, "g1_cvr_por_variante.png")


def g2_comissao(resumo: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    cores = [PALETTE[v] for v in resumo["variant"]]
    bars = ax.bar([LABEL[v] for v in resumo["variant"]],
                  resumo["commission_per_visit"], color=cores, edgecolor="white")
    for b, v in zip(bars, resumo["commission_per_visit"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"R$ {v:.2f}",
                ha="center", fontsize=10)
    ax.set_title("Comissão esperada por visita (métrica-norte)")
    ax.set_ylabel("Comissão / visita (R$)")
    ax.grid(axis="y", alpha=0.3)
    _save(fig, "g2_comissao_por_variante.png")


def g3_canal(rcanal: pd.DataFrame) -> None:
    """Mostra a queda brutal de comissão quando a saída vai para BROWSERDEFAULT."""
    pivot = rcanal.pivot(index="variant", columns="channel_id",
                         values="commission_per_visit").fillna(0)
    pivot = pivot.rename(columns={"C001": "BROWSERDEFAULT", "C002": "INAPP"})
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    pivot.plot(kind="bar", ax=ax, color=["#E45756", "#72B7B2"], edgecolor="white")
    ax.set_title("Comissão por visita: InApp vs Navegador externo")
    ax.set_xlabel("Variante")
    ax.set_ylabel("Comissão / visita (R$)")
    ax.set_xticklabels([LABEL[v] for v in pivot.index], rotation=0)
    ax.legend(title="Canal final")
    ax.grid(axis="y", alpha=0.3)
    for c in ax.containers:
        ax.bar_label(c, fmt="R$ %.2f", padding=3, fontsize=9)
    _save(fig, "g3_canal_externo.png")


def g4_feature(rfeat: pd.DataFrame) -> None:
    """Comissão por visita por feature de saída externa (header/config/login)."""
    rfeat = rfeat.copy()
    rfeat["rotulo"] = rfeat["variant"].str.upper() + " · " + rfeat["utm_term"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bars = ax.bar(rfeat["rotulo"], rfeat["commission_per_visit"],
                  color=["#F58518", "#F58518", "#54A24B", "#54A24B"],
                  edgecolor="white")
    for b, v in zip(bars, rfeat["commission_per_visit"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"R$ {v:.2f}",
                ha="center", fontsize=10)
    ax.set_title("Comissão por visita por tipo de saída externa")
    ax.set_ylabel("Comissão / visita (R$)")
    ax.grid(axis="y", alpha=0.3)
    _save(fig, "g4_feature_saida.png")


def g5_lifts(zt: pd.DataFrame) -> None:
    """Forest plot dos lifts absolutos de CVR com IC95%."""
    fig, ax = plt.subplots(figsize=(7.5, 3.5))
    y = np.arange(len(zt))
    centro = zt["lift_abs"] * 100
    lo = zt["ic95_lo"] * 100
    hi = zt["ic95_hi"] * 100
    ax.errorbar(centro, y, xerr=[centro - lo, hi - centro], fmt="o",
                color="#222", capsize=4)
    for i, p in enumerate(zt["p_value"]):
        ax.text(0.02, i + 0.18, f"p = {p:.4f}", transform=ax.get_yaxis_transform(),
                fontsize=9, color="#666")
    ax.axvline(0, color="#999", linewidth=1, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(zt["comparacao"])
    ax.set_xlabel("Lift absoluto em CVR (pontos percentuais)")
    ax.set_title("Lifts de CVR com IC95% (z-test de proporções)")
    ax.grid(axis="x", alpha=0.3)
    _save(fig, "g5_lifts_com_ic.png")


def main() -> None:
    resumo = pd.read_csv(OUT_DIR / "resumo_por_variante.csv")
    resumo = resumo[resumo["variant"].isin(["a", "b", "c"])].sort_values("variant")

    rcanal = pd.read_csv(OUT_DIR / "resumo_por_variante_canal.csv")
    rcanal = rcanal[rcanal["variant"].isin(["a", "b", "c"])]

    rfeat = pd.read_csv(OUT_DIR / "resumo_por_feature.csv")

    zt = pd.read_csv(OUT_DIR / "ztest_cvr.csv")

    g1_cvr(resumo)
    g2_comissao(resumo)
    g3_canal(rcanal)
    g4_feature(rfeat)
    g5_lifts(zt)


if __name__ == "__main__":
    main()
