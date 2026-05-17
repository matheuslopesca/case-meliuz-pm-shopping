"""
01_explore.py — Exploração inicial dos CSVs do case Méliuz.

Objetivos desta etapa (Validação do dado antes de tirar qualquer conclusão):
  1. Confirmar o grão de cada tabela.
  2. Medir completude (nulos, vazios) das chaves de join.
  3. Detectar duplicidades inesperadas.
  4. Validar a integridade referencial entre tabelas.
  5. Reconstruir as variantes A/B/C a partir do JSON em visit_url_metadata.
  6. Identificar valores únicos de utm_content e utm_term presentes.

Por que isso importa:
  Um teste A/B/C só vale alguma coisa se a aleatorização foi feita corretamente
  e se cada visita é atribuída a UMA e apenas UMA variante. Antes de calcular
  qualquer métrica, é preciso "abrir o capô" dos dados.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

# Caminhos parametrizáveis. Defaults relativos à raiz do repositório, de modo
# que qualquer pessoa clone e rode sem precisar editar paths absolutos.
#   - MELIUZ_DATA_DIR: pasta com os CSVs originais do case (default: ./dados/)
#   - MELIUZ_OUT_DIR:  pasta de saída dos scripts (default: ./outputs/)
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("MELIUZ_DATA_DIR", REPO_ROOT / "dados"))
OUT_DIR = Path(os.environ.get("MELIUZ_OUT_DIR", REPO_ROOT / "outputs"))
OUT_DIR.mkdir(parents=True, exist_ok=True)


def carregar_tabelas() -> dict[str, pd.DataFrame]:
    """Lê todos os CSVs e devolve um dicionário nome -> DataFrame.

    Observação: o BI exportou com BOM em algumas tabelas (\\ufeff no primeiro
    cabeçalho). Usamos encoding='utf-8-sig' para limpar.
    """
    arquivos = {
        "visits": "visits.csv",
        "transactions": "transactions.csv",
        "url_params": "url_params.csv",
        "visit_url_metadata": "visit_url_metadata.csv",
        "partners": "partners.csv",
        "channels": "channels.csv",
    }
    tabelas: dict[str, pd.DataFrame] = {}
    for nome, arq in arquivos.items():
        caminho = DATA_DIR / arq
        df = pd.read_csv(caminho, encoding="utf-8-sig", low_memory=False)
        tabelas[nome] = df
        print(f"[ok] {nome:20s} linhas={len(df):>9,} colunas={list(df.columns)}")
    return tabelas


def checar_grao(tabelas: dict[str, pd.DataFrame]) -> None:
    """Confirma que IDs declarados como chave realmente são únicos.

    O enunciado diz 'uma linha por X' para cada tabela. Vamos verificar.
    """
    print("\n=== CHECAGEM DE GRÃO ===")
    pares = [
        ("visits", "visit_id"),
        ("transactions", "transaction_id"),
        ("url_params", "url_param_id"),
        ("visit_url_metadata", "visit_id"),
        ("partners", "partner_id"),
        ("channels", "channel_id"),
    ]
    for tabela, chave in pares:
        df = tabelas[tabela]
        n = len(df)
        n_uniq = df[chave].nunique(dropna=False)
        flag = "OK" if n == n_uniq else "ATENÇÃO"
        print(f"  [{flag}] {tabela}.{chave}: {n:,} linhas, {n_uniq:,} únicos")


def checar_referencias(tabelas: dict[str, pd.DataFrame]) -> None:
    """Verifica integridade referencial das FKs em visits e transactions."""
    print("\n=== INTEGRIDADE REFERENCIAL ===")
    visits = tabelas["visits"]
    transactions = tabelas["transactions"]
    url_params = tabelas["url_params"]
    visit_url_metadata = tabelas["visit_url_metadata"]
    partners = tabelas["partners"]
    channels = tabelas["channels"]

    checagens = [
        ("visits.partner_id  ⊂ partners.partner_id",
         visits["partner_id"].isin(partners["partner_id"]).mean()),
        ("visits.channel_id  ⊂ channels.channel_id",
         visits["channel_id"].isin(channels["channel_id"]).mean()),
        ("visits.url_param_id ⊂ url_params.url_param_id",
         visits["url_param_id"].isin(url_params["url_param_id"]).mean()),
        ("visits.visit_id     ⊂ visit_url_metadata.visit_id",
         visits["visit_id"].isin(visit_url_metadata["visit_id"]).mean()),
        ("transactions.visit_id ⊂ visits.visit_id",
         transactions["visit_id"].isin(visits["visit_id"]).mean()),
    ]
    for desc, pct in checagens:
        print(f"  {pct*100:6.2f}% válidos — {desc}")


def parse_variante(json_str: str) -> str | None:
    """Extrai a variante (a/b/c) do JSON tracking_url_params.

    Retorna None se não houver mz_test_gotoexternalbrowser.
    """
    try:
        d = json.loads(json_str)
    except (TypeError, ValueError):
        return None
    return d.get("mz_test_gotoexternalbrowser")


def parse_redirect(json_str: str) -> str | None:
    """Extrai mz_redirect do JSON (inapp / browserdefault)."""
    try:
        d = json.loads(json_str)
    except (TypeError, ValueError):
        return None
    return d.get("mz_redirect")


def explorar_variantes(tabelas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Junta visits com visit_url_metadata e identifica a variante de cada visit."""
    print("\n=== IDENTIFICAÇÃO DAS VARIANTES A/B/C ===")
    vum = tabelas["visit_url_metadata"].copy()
    vum["variant"] = vum["tracking_url_params"].apply(parse_variante)
    vum["mz_redirect"] = vum["tracking_url_params"].apply(parse_redirect)
    print(vum["variant"].value_counts(dropna=False).to_string())
    print("\nDistribuição mz_redirect:")
    print(vum["mz_redirect"].value_counts(dropna=False).to_string())

    # Cruza com utm_content para entender qual feature gerou a saída
    visits = tabelas["visits"]
    url_params = tabelas["url_params"]
    base = visits.merge(vum[["visit_id", "variant", "mz_redirect"]], on="visit_id", how="left")
    base = base.merge(url_params, on="url_param_id", how="left")

    print("\nCross variant x mz_redirect:")
    print(pd.crosstab(base["variant"], base["mz_redirect"], dropna=False).to_string())

    print("\nValores de utm_content presentes:")
    print(base["utm_content"].value_counts(dropna=False).head(15).to_string())

    print("\nValores de utm_term presentes:")
    print(base["utm_term"].value_counts(dropna=False).head(15).to_string())

    print("\nCross variant x utm_term (somente external_browser_modal):")
    sub = base[base["utm_content"] == "EXTERNAL_BROWSER_MODAL"]
    print(pd.crosstab(sub["variant"], sub["utm_term"], dropna=False).to_string())

    return base


def checar_unicidade_variante_por_user(base: pd.DataFrame) -> None:
    """Em um A/B/C clean, cada customer_id ideialmente vê só uma variante.
    Vamos contar quantos clientes apareceram em mais de uma variante.
    """
    print("\n=== USUÁRIOS EM MAIS DE UMA VARIANTE (risco de contaminação) ===")
    g = base.dropna(subset=["variant"]).groupby("customer_id")["variant"].nunique()
    print(g.value_counts().sort_index().to_string())
    if (g > 1).any():
        print(f"  ⚠️  {(g > 1).sum():,} clientes em >1 variante "
              f"({(g > 1).mean()*100:.2f}% dos clientes)")


def main() -> None:
    tabelas = carregar_tabelas()
    checar_grao(tabelas)
    checar_referencias(tabelas)
    base = explorar_variantes(tabelas)
    checar_unicidade_variante_por_user(base)

    # Persistimos a base enriquecida para uso nas próximas etapas.
    # (CSV é portável; em produção usaríamos parquet com pyarrow.)
    out = OUT_DIR / "visits_enriched.csv"
    base.to_csv(out, index=False)
    print(f"\n[ok] base enriquecida salva em {out}")


if __name__ == "__main__":
    main()
