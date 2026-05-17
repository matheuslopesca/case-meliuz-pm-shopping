"""
tools.py — Conjunto de ferramentas (tools) que o agente autônomo pode chamar.

Cada função aqui é um "tool call" do ponto de vista do LLM:
- O LLM decide qual chamar.
- O LLM passa os argumentos.
- O Python executa e devolve o resultado em texto.

Diferença vs /agent (humano):
- Lá, é um humano que decide qual script rodar e na ordem.
- Aqui, é o LLM que olha o estado, decide o próximo passo e chama a função.

Para um leitor que nunca viu tool use: imagine que o LLM tem acesso a um
"controle remoto" com botões — cada função abaixo é um botão. O LLM aperta
o botão certo, lê o que aparece no visor, e decide o próximo a apertar.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# --------------- estado global mínimo (compartilhado entre tools) ---------------
# Em um sistema de produção, isso viria de uma sessão/contexto persistente.
# Para a prova de conceito, mantemos em memória durante a execução.
# Defaults relativos à raiz do repositório, para que qualquer pessoa que
# clone o repo possa rodar sem editar paths absolutos.
#   - dados/ na raiz: pasta com os CSVs do case (o usuário precisa colocar
#     os 6 arquivos lá; o repositório não distribui os dados originais).
#   - agent_autonomo/outputs/: pasta de saída do agente.
_THIS = Path(__file__).resolve()
_REPO_ROOT = _THIS.parents[1]
STATE: dict[str, Any] = {
    "data_dir": os.environ.get("MELIUZ_DATA_DIR", str(_REPO_ROOT / "dados")),
    "out_dir": os.environ.get("MELIUZ_OUT_DIR", str(_THIS.parent / "outputs")),
    "loaded": {},          # nome_lógico → DataFrame
    "computed": {},        # nome_lógico → resultado computado
    "rng": np.random.default_rng(42),
}
Path(STATE["out_dir"]).mkdir(parents=True, exist_ok=True)


def _ok(payload: Any) -> str:
    """Empacota um retorno de sucesso de forma estável para o LLM ler."""
    return json.dumps({"ok": True, "result": payload}, ensure_ascii=False, default=str)


def _err(msg: str) -> str:
    return json.dumps({"ok": False, "error": msg}, ensure_ascii=False)


# =============================================================================
# TOOLS
# =============================================================================

def list_files(directory: str | None = None) -> str:
    """Lista os CSVs disponíveis no diretório de dados."""
    d = Path(directory) if directory else Path(STATE["data_dir"])
    if not d.exists():
        return _err(f"diretório não existe: {d}")
    files = sorted(p.name for p in d.iterdir() if p.suffix == ".csv")
    return _ok({"dir": str(d), "files": files})


def load_csv(filename: str, alias: str | None = None) -> str:
    """Carrega um CSV em memória; devolve schema e primeiras linhas.

    O LLM usa isso para entender o shape do dado antes de pedir agregação.
    """
    path = Path(STATE["data_dir"]) / filename
    if not path.exists():
        return _err(f"arquivo não encontrado: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    alias = alias or filename.replace(".csv", "")
    STATE["loaded"][alias] = df
    return _ok({
        "alias": alias,
        "rows": len(df),
        "columns": list(df.columns),
        "head": df.head(3).to_dict(orient="records"),
    })


def parse_variant_from_metadata(alias: str = "visit_url_metadata",
                                test_key: str = "mz_test_gotoexternalbrowser") -> str:
    """Lê o JSON em tracking_url_params e extrai a variante de cada visita.

    Retorna contagens por variante (sanity check de aleatorização).
    """
    if alias not in STATE["loaded"]:
        return _err(f"alias '{alias}' não carregado. Use load_csv primeiro.")
    df = STATE["loaded"][alias].copy()

    def _extract(s: str) -> str | None:
        try:
            return json.loads(s).get(test_key)
        except Exception:
            return None

    df["variant"] = df["tracking_url_params"].apply(_extract)
    STATE["loaded"][alias] = df
    counts = df["variant"].value_counts(dropna=False).to_dict()
    return _ok({"test_key": test_key, "variant_counts": counts})


def compute_variant_summary(visits_alias: str = "visits",
                            metadata_alias: str = "visit_url_metadata",
                            transactions_alias: str = "transactions") -> str:
    """Computa o resumo master por variante (grão visita).

    Retorna métricas-chave: visits, buyers, CVR, AOV, comissão/visita, GMV/visita.
    """
    for a in [visits_alias, metadata_alias, transactions_alias]:
        if a not in STATE["loaded"]:
            return _err(f"alias '{a}' não carregado. Use load_csv primeiro.")
    visits = STATE["loaded"][visits_alias]
    meta = STATE["loaded"][metadata_alias]
    tx = STATE["loaded"][transactions_alias]
    if "variant" not in meta.columns:
        return _err("metadata sem coluna 'variant'. Rode parse_variant_from_metadata.")

    base = visits.merge(meta[["visit_id", "variant"]], on="visit_id", how="left")
    tx_g = tx.groupby("visit_id").agg(
        n_tx=("transaction_id", "count"),
        gmv=("sale_amount", "sum"),
        cashback=("cashback_amount", "sum"),
        commission=("expected_commission_amount", "sum"),
    ).reset_index()
    base = base.merge(tx_g, on="visit_id", how="left").fillna({"n_tx": 0, "gmv": 0, "cashback": 0, "commission": 0})
    base["converted"] = (base["n_tx"] > 0).astype(int)

    abc = base[base["variant"].isin(["a", "b", "c"])].copy()
    g = abc.groupby("variant").agg(
        visits=("visit_id", "count"),
        buyers=("converted", "sum"),
        n_tx=("n_tx", "sum"),
        gmv=("gmv", "sum"),
        commission=("commission", "sum"),
    ).reset_index()
    g["cvr"] = g["buyers"] / g["visits"]
    g["aov"] = g["gmv"] / g["n_tx"].where(g["n_tx"] > 0)
    g["commission_per_visit"] = g["commission"] / g["visits"]
    g["gmv_per_visit"] = g["gmv"] / g["visits"]

    STATE["computed"]["abc_visit_level"] = abc
    STATE["computed"]["summary_by_variant"] = g
    return _ok({"summary_by_variant": g.to_dict(orient="records")})


def z_test_proportions(group_a: str, group_b: str,
                       metric: str = "converted") -> str:
    """z-test de duas proporções entre duas variantes.

    Args:
        group_a, group_b: nomes das variantes ('a', 'b', 'c').
        metric: coluna binária para a proporção (default 'converted').
    """
    if "abc_visit_level" not in STATE["computed"]:
        return _err("rode compute_variant_summary antes.")
    df = STATE["computed"]["abc_visit_level"]
    a = df[df["variant"] == group_a]
    b = df[df["variant"] == group_b]
    s1, n1 = int(a[metric].sum()), len(a)
    s2, n2 = int(b[metric].sum()), len(b)
    if min(n1, n2) == 0:
        return _err("um dos grupos está vazio.")
    p1, p2 = s1 / n1, s2 / n2
    p_pool = (s1 + s2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se if se > 0 else 0.0
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    ic_lo = (p2 - p1) - 1.96 * se_diff
    ic_hi = (p2 - p1) + 1.96 * se_diff
    return _ok({
        "comparison": f"{group_b} vs {group_a}",
        "p_control": p1, "p_treatment": p2,
        "lift_abs_pp": (p2 - p1) * 100,
        "lift_rel_pct": (p2 / p1 - 1) * 100 if p1 > 0 else None,
        "z": z, "p_value": p_value,
        "ic95_pp": [ic_lo * 100, ic_hi * 100],
    })


def bootstrap_diff_mean(group_a: str, group_b: str,
                        column: str = "commission", n_boot: int = 500) -> str:
    """Bootstrap percentile para diferença de médias entre dois grupos."""
    if "abc_visit_level" not in STATE["computed"]:
        return _err("rode compute_variant_summary antes.")
    df = STATE["computed"]["abc_visit_level"]
    a = df[df["variant"] == group_a][column].values
    b = df[df["variant"] == group_b][column].values
    diffs = np.empty(n_boot)
    rng = STATE["rng"]
    for i in range(n_boot):
        sa = rng.choice(a, len(a), replace=True)
        sb = rng.choice(b, len(b), replace=True)
        diffs[i] = sb.mean() - sa.mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return _ok({
        "comparison": f"{group_b} vs {group_a}",
        "column": column,
        "mean_control": float(a.mean()),
        "mean_treatment": float(b.mean()),
        "diff": float(b.mean() - a.mean()),
        "ic95": [float(lo), float(hi)],
        "n_boot": n_boot,
    })


def write_report(content: str, filename: str = "agent_report.md") -> str:
    """Salva o relatório final em disco."""
    path = Path(STATE["out_dir"]) / filename
    path.write_text(content, encoding="utf-8")
    return _ok({"path": str(path), "bytes": path.stat().st_size})


# =============================================================================
# JSON SCHEMAS (para o LLM saber quais tools existem e seus argumentos)
# =============================================================================

TOOL_SCHEMAS = [
    {
        "name": "list_files",
        "description": "Lista os CSVs disponíveis no diretório de dados.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Diretório (opcional, default = data_dir)."}
            },
        },
    },
    {
        "name": "load_csv",
        "description": "Carrega um CSV em memória. Retorna shape e primeiras linhas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "alias": {"type": "string", "description": "Nome lógico para referenciar depois."},
            },
            "required": ["filename"],
        },
    },
    {
        "name": "parse_variant_from_metadata",
        "description": "Extrai a variante A/B/C do JSON tracking_url_params em visit_url_metadata.",
        "input_schema": {
            "type": "object",
            "properties": {
                "alias": {"type": "string"},
                "test_key": {"type": "string", "description": "Chave do teste no JSON, ex: mz_test_gotoexternalbrowser"},
            },
        },
    },
    {
        "name": "compute_variant_summary",
        "description": "Calcula o resumo master por variante (CVR, AOV, GMV/visita, comissão/visita).",
        "input_schema": {
            "type": "object",
            "properties": {
                "visits_alias": {"type": "string"},
                "metadata_alias": {"type": "string"},
                "transactions_alias": {"type": "string"},
            },
        },
    },
    {
        "name": "z_test_proportions",
        "description": "z-test de duas proporções entre duas variantes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_a": {"type": "string", "description": "Variante controle, ex: 'a'."},
                "group_b": {"type": "string", "description": "Variante tratamento, ex: 'b'."},
                "metric": {"type": "string", "description": "Coluna binária, default 'converted'."},
            },
            "required": ["group_a", "group_b"],
        },
    },
    {
        "name": "bootstrap_diff_mean",
        "description": "Bootstrap percentile para diferença de médias.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_a": {"type": "string"},
                "group_b": {"type": "string"},
                "column": {"type": "string", "description": "Coluna numérica (commission, gmv, ...)."},
                "n_boot": {"type": "integer", "description": "Número de reamostras."},
            },
            "required": ["group_a", "group_b"],
        },
    },
    {
        "name": "write_report",
        "description": "Salva o relatório final em Markdown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "filename": {"type": "string"},
            },
            "required": ["content"],
        },
    },
]


# Dispatcher: mapeia nome -> função
DISPATCH = {
    "list_files": list_files,
    "load_csv": load_csv,
    "parse_variant_from_metadata": parse_variant_from_metadata,
    "compute_variant_summary": compute_variant_summary,
    "z_test_proportions": z_test_proportions,
    "bootstrap_diff_mean": bootstrap_diff_mean,
    "write_report": write_report,
}


def call_tool(name: str, **kwargs) -> str:
    """Despacha uma chamada de tool pelo nome. Sempre retorna string JSON."""
    fn = DISPATCH.get(name)
    if fn is None:
        return _err(f"tool desconhecida: {name}")
    try:
        return fn(**kwargs)
    except Exception as e:
        return _err(f"{type(e).__name__}: {e}")
