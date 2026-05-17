"""
run_agent.py — Loop agêntico real para análise de testes A/B/C.

Diferença vs /agent (humano):
  - Lá, é um humano que decide qual script rodar e quando parar.
  - Aqui, é o LLM que decide cada chamada de tool, lê os resultados,
    e segue até produzir o relatório final.

Como funciona o loop:
  1. Carrega system_prompt.md e briefing.md.
  2. Manda para o Claude com a lista de tools disponíveis (TOOL_SCHEMAS).
  3. Claude responde com `tool_use` (uma ou mais chamadas).
  4. Para cada `tool_use`, executamos a função correspondente em tools.py
     e devolvemos o resultado como `tool_result` na conversa.
  5. Repetimos até Claude responder com `stop_reason="end_turn"`.

Para rodar de verdade (macOS / Linux):
  - É preciso ter `ANTHROPIC_API_KEY` no ambiente.
  - `pip3 install anthropic`
  - `python3 run_agent.py --briefing briefing_exemplo.md`

Modo dry-run (sem API):
  - `python3 run_agent.py --dry-run`
  - Mostra exatamente o que seria enviado para o LLM e simula 1 iteração.

Por que vale a pena ler este arquivo:
  Ele tem ~150 linhas e implementa o esqueleto de um agente real.
  Toda complexidade extra (memória persistente, múltiplos agentes,
  paralelismo) é incremental em cima disso.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import tools  # módulo local

THIS = Path(__file__).resolve().parent
MODEL = os.environ.get("ABXAGENT_MODEL", "claude-opus-4-5")
MAX_ITERATIONS = int(os.environ.get("ABXAGENT_MAX_ITER", "25"))


def read_briefing(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = THIS / path
    return p.read_text(encoding="utf-8")


def read_system_prompt() -> str:
    return (THIS / "system_prompt.md").read_text(encoding="utf-8")


def print_step(i: int, title: str) -> None:
    print(f"\n── passo {i:>2} · {title} " + "─" * (50 - len(title)))


def print_tool_use(name: str, args: dict) -> None:
    print(f"   🔧 tool_use → {name}({json.dumps(args, ensure_ascii=False)})")


def print_tool_result(result: str, max_len: int = 300) -> None:
    snippet = result if len(result) <= max_len else result[:max_len] + " …(truncado)"
    print(f"   📤 tool_result ← {snippet}")


def run(briefing_path: str, dry_run: bool = False) -> None:
    """Executa o loop agêntico."""
    system_prompt = read_system_prompt()
    briefing = read_briefing(briefing_path)

    user_msg = (
        "Briefing do teste a analisar:\n\n"
        "```\n" + briefing + "\n```\n\n"
        "Conduza a análise usando as tools e produza o relatório final via "
        "write_report. Comece pelo `list_files` para enxergar os dados."
    )

    print("=" * 70)
    print(f"ABx Analyst — agente autônomo")
    print(f"Modelo: {MODEL}")
    print(f"Briefing: {briefing_path}")
    print(f"Tools disponíveis: {[t['name'] for t in tools.TOOL_SCHEMAS]}")
    print("=" * 70)

    if dry_run:
        _dry_run_demo(system_prompt, user_msg)
        return

    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("Instale o SDK (macOS/Linux): pip3 install anthropic")

    client = Anthropic()  # usa ANTHROPIC_API_KEY do ambiente
    messages = [{"role": "user", "content": user_msg}]

    for iteration in range(MAX_ITERATIONS):
        print_step(iteration + 1, "chamando o LLM")
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=tools.TOOL_SCHEMAS,
            messages=messages,
        )

        # Coleta tool_uses e text blocks
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]
        for tb in text_blocks:
            if tb.text.strip():
                print(f"   💬 {tb.text.strip()[:400]}")

        # Anexa a resposta do assistant
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn" and not tool_uses:
            print("\n✅ Agente terminou (end_turn).")
            return

        # Para cada tool_use, executa e devolve tool_result
        tool_results = []
        for tu in tool_uses:
            print_tool_use(tu.name, tu.input)
            output = tools.call_tool(tu.name, **tu.input)
            print_tool_result(output)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": output,
            })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    print(f"\n⚠️  Limite de {MAX_ITERATIONS} iterações atingido sem end_turn.")


def _dry_run_demo(system_prompt: str, user_msg: str) -> None:
    """Mostra o que seria enviado e executa 1 chamada de tool para validar."""
    print("\n[dry-run] mostrando o pacote de contexto que iria para o LLM:\n")
    print("  system_prompt:", len(system_prompt), "chars")
    print("  user_msg:", len(user_msg), "chars")
    print("  tools:", len(tools.TOOL_SCHEMAS), "definidas")
    print("\n[dry-run] simulando chamada do agente: list_files()")
    out = tools.call_tool("list_files")
    print_tool_result(out, max_len=400)
    print("\n[dry-run] Tudo conectado. Para rodar de verdade (macOS/Linux):")
    print("  export ANTHROPIC_API_KEY=...")
    print("  pip3 install anthropic")
    print("  python3 run_agent.py --briefing briefing_exemplo.md")


def main() -> None:
    ap = argparse.ArgumentParser(description="ABx Analyst — agente autônomo")
    ap.add_argument("--briefing", default="briefing_exemplo.md",
                    help="Caminho do briefing em Markdown.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Não chama a API; valida o pipeline localmente.")
    args = ap.parse_args()
    run(args.briefing, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
