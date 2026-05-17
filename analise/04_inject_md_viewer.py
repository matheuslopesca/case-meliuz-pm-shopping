"""
04_inject_md_viewer.py
----------------------
Pega o index.html existente e injeta um visualizador de Markdown:

  1. Lê todos os .md relevantes do repo.
  2. Embarca cada um como <script type="text/markdown" id="md-XXX">.
  3. Adiciona marked.js + DOMPurify via CDN.
  4. Adiciona CSS para um modal estilizado tipo "GitHub-flavored".
  5. Adiciona JS para abrir/fechar o modal e renderizar Markdown.
  6. Substitui os links existentes para .md por chamadas openMd(id, title)
     (mantendo um botão "Abrir arquivo .md original" como fallback).

Resultado: HTML continua single-file (sem fetch, sem CORS, sem build),
renderiza .md inline com tipografia bonita e suporte a tabelas/código.
"""

from __future__ import annotations

import html as html_lib
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HTML_PATH = REPO / "index.html"

# (id_no_script, caminho_relativo_no_repo, título_para_o_modal)
MDS = [
    ("md-relatorio",        "entrega_1/RELATORIO.md",                     "Entrega 1 — Análise e Recomendação"),
    ("md-prd",              "entrega_2/PRD_login_social_in_app.md",       "PRD — Login social InApp"),
    ("md-instrumentacao",   "entrega_2/INSTRUMENTACAO.md",                "Plano de Instrumentação"),
    ("md-plano-teste",      "entrega_2/PLANO_DE_TESTE.md",                "Plano de Teste A/B (Teste D)"),
    ("md-handoff",          "entrega_2/HANDOFF_ENG.md",                   "Handoff para Engenharia"),
    ("md-system-prompt",    "agent/SYSTEM_PROMPT.md",                     "Agente — System Prompt"),
    ("md-runbook",          "agent/RUNBOOK.md",                           "Agente — Runbook"),
    ("md-template-report",  "agent/templates/REPORT_TEMPLATE.md",         "Template de Relatório"),
    ("md-template-prd",     "agent/templates/PRD_TEMPLATE.md",            "Template de PRD"),
    ("md-qa-dados",         "agent/checklists/QA_DADOS.md",               "Checklist — QA dos Dados"),
    ("md-qa-relatorio",     "agent/checklists/QA_RELATORIO.md",           "Checklist — QA do Relatório"),
    ("md-como-rodar",       "docs/COMO_RODAR.md",                         "Como Rodar do Zero"),
    ("md-readme",           "README.md",                                  "README do Repositório"),
    ("md-github-setup",     "GITHUB_SETUP.md",                            "Setup do GitHub"),
    # Agente autônomo
    ("md-agente-readme",    "agent_autonomo/README.md",                   "Agente Autônomo — README"),
    ("md-agente-prompt",    "agent_autonomo/system_prompt.md",            "Agente Autônomo — System Prompt"),
    ("md-agente-briefing",  "agent_autonomo/briefing_exemplo.md",         "Agente Autônomo — Briefing Exemplo"),
    ("md-agente-execucao",  "agent_autonomo/execucao_exemplo.md",         "Agente Autônomo — Log de Execução"),
]


def escape_for_script_tag(md: str) -> str:
    """Markdown vai dentro de <script type="text/markdown">. O único caractere
    que quebra esse contexto é a sequência literal </script>. Quebramos com
    uma concatenação inofensiva.
    """
    return md.replace("</script>", "</scr" + "ipt>").replace("</SCRIPT>", "</SCR" + "IPT>")


def load_md_payloads() -> list[tuple[str, str, str, str]]:
    """Retorna (script_id, rel_path, title, conteudo_escaped)."""
    out = []
    for script_id, rel_path, title in MDS:
        p = REPO / rel_path
        if not p.exists():
            print(f"  [skip] não encontrado: {rel_path}")
            continue
        text = p.read_text(encoding="utf-8")
        out.append((script_id, rel_path, title, escape_for_script_tag(text)))
        print(f"  [ok] embarcado: {rel_path} ({len(text):,} chars)")
    return out


CSS_ADDITION = """
/* MD-VIEWER-CSS-START */
/* ==================== MARKDOWN VIEWER ==================== */
.md-modal {
  position: fixed; inset: 0; z-index: 1000;
  display: flex; justify-content: flex-end;
}
.md-modal.hidden { display: none !important; }
.md-modal-overlay {
  position: absolute; inset: 0;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(2px);
}
.md-modal-content {
  position: relative;
  width: min(880px, 100%);
  height: 100vh;            /* altura explícita p/ ancorar o overflow do filho */
  max-height: 100vh;
  background: var(--surface);
  display: flex; flex-direction: column;
  overflow: hidden;         /* impede content extra de empurrar o layout */
  box-shadow: -8px 0 30px rgba(15, 23, 42, 0.2);
  animation: slideIn 0.22s ease;
}
@keyframes slideIn { from { transform: translateX(40px); opacity: 0.4; } to { transform: translateX(0); opacity: 1; } }
.md-modal-header {
  flex: 0 0 auto;           /* header não cresce, não encolhe */
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px; border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
  gap: 16px;
}
.md-modal-header h3 { margin: 0; font-size: 17px; font-weight: 600; color: var(--ink); }
.md-modal-header .md-modal-actions { display: flex; gap: 8px; align-items: center; }
.md-modal-header a.md-raw-link {
  font-size: 13px; color: var(--brand); text-decoration: none; padding: 6px 10px;
  border: 1px solid var(--brand); border-radius: 6px;
}
.md-modal-header a.md-raw-link:hover { background: var(--brand-soft); }
.md-modal-header button.md-close {
  background: none; border: 1px solid var(--line); border-radius: 6px;
  width: 32px; height: 32px; cursor: pointer; font-size: 18px; color: var(--ink-soft);
  display: flex; align-items: center; justify-content: center;
}
.md-modal-header button.md-close:hover { background: #f1f5f9; }
/* IMPORTANTE: o elemento tem id="md-modal-body" (não classe).
   Usamos seletor de ID para que estas regras realmente apliquem. */
#md-modal-body {
  flex: 1 1 auto;
  min-height: 0;            /* KEY: permite o flex item encolher e ativar o overflow */
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding: 32px 40px 64px;
}

/* Estilo do markdown renderizado (inspirado em github-markdown-css) */
.markdown-body { color: var(--ink); font-size: 15px; line-height: 1.65; }
.markdown-body h1, .markdown-body h2, .markdown-body h3,
.markdown-body h4, .markdown-body h5, .markdown-body h6 {
  color: var(--ink); font-weight: 700; line-height: 1.25;
  margin-top: 28px; margin-bottom: 14px;
}
.markdown-body h1 { font-size: 26px; padding-bottom: 8px; border-bottom: 1px solid var(--line); }
.markdown-body h2 { font-size: 22px; padding-bottom: 6px; border-bottom: 1px solid var(--line); }
.markdown-body h3 { font-size: 18px; }
.markdown-body h4 { font-size: 16px; color: var(--ink-soft); }
.markdown-body h5, .markdown-body h6 { font-size: 14px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; }
.markdown-body p { margin: 10px 0; color: var(--ink-soft); }
.markdown-body strong { color: var(--ink); }
.markdown-body a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }
.markdown-body a:hover { color: var(--brand); }
.markdown-body ul, .markdown-body ol { padding-left: 26px; margin: 10px 0; color: var(--ink-soft); }
.markdown-body li { margin: 4px 0; }
.markdown-body li > p { margin: 4px 0; }
.markdown-body blockquote {
  border-left: 4px solid var(--brand);
  background: #f0fdfa;
  margin: 14px 0; padding: 10px 16px;
  color: var(--ink-soft); border-radius: 0 6px 6px 0;
}
.markdown-body blockquote p { margin: 4px 0; }
.markdown-body code {
  background: #f1f5f9; padding: 1px 6px; border-radius: 4px;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  font-size: 13.5px; color: var(--ink);
}
.markdown-body pre {
  background: #0f172a; color: #e2e8f0; padding: 16px;
  border-radius: 8px; overflow-x: auto; margin: 14px 0;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 13px; line-height: 1.55;
}
.markdown-body pre code { background: transparent; color: inherit; padding: 0; }
.markdown-body table { border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 14px; }
.markdown-body table th, .markdown-body table td {
  border: 1px solid var(--line); padding: 8px 12px; text-align: left;
}
.markdown-body table th { background: #f8fafc; font-weight: 600; }
.markdown-body table tr:nth-child(2n) td { background: #fafbfc; }
.markdown-body hr { border: none; border-top: 1px solid var(--line); margin: 24px 0; }
.markdown-body img { max-width: 100%; border-radius: 6px; }
.markdown-body input[type="checkbox"] { margin-right: 6px; }

/* Em telas pequenas, o painel toma a tela toda */
@media (max-width: 720px) {
  .md-modal-content { width: 100%; }
  #md-modal-body { padding: 20px; }
}
/* MD-VIEWER-CSS-END */
"""

JS_ADDITION = """
<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js"></script>
<script>
(function(){
  const modal = document.getElementById('md-modal');
  const title = document.getElementById('md-modal-title');
  const body  = document.getElementById('md-modal-body');
  const raw   = document.getElementById('md-raw-link');

  window.openMd = function(id, displayTitle, rawHref) {
    const src = document.getElementById(id);
    if (!src) {
      console.warn('Markdown source not found:', id);
      window.open(rawHref, '_blank');
      return false;
    }
    const md = src.textContent;
    // marked: ativa GFM (tabelas, task lists, etc.)
    if (typeof marked !== 'undefined') {
      marked.use({ gfm: true, breaks: false });
      const rendered = marked.parse(md);
      const safe = (typeof DOMPurify !== 'undefined') ? DOMPurify.sanitize(rendered) : rendered;
      body.innerHTML = safe;
    } else {
      // fallback se a CDN cair: mostra como pre-formatado
      body.innerHTML = '<pre style="white-space:pre-wrap;font-family:inherit;color:#334155">' +
                       md.replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c])) +
                       '</pre>';
    }
    title.textContent = displayTitle;
    raw.href = rawHref;
    body.scrollTop = 0;
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    return false;
  };

  window.closeMdModal = function() {
    modal.classList.add('hidden');
    document.body.style.overflow = '';
  };

  // ESC fecha o modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      window.closeMdModal();
    }
  });
})();
</script>
"""

MODAL_HTML = """
<div id="md-modal" class="md-modal hidden" role="dialog" aria-modal="true">
  <div class="md-modal-overlay" onclick="closeMdModal()"></div>
  <div class="md-modal-content">
    <header class="md-modal-header">
      <h3 id="md-modal-title">Documento</h3>
      <div class="md-modal-actions">
        <a id="md-raw-link" class="md-raw-link" href="#" target="_blank" rel="noopener">Abrir .md original</a>
        <button class="md-close" onclick="closeMdModal()" aria-label="Fechar">×</button>
      </div>
    </header>
    <article id="md-modal-body" class="markdown-body"></article>
  </div>
</div>
"""


def replace_md_links(html: str, payloads: list[tuple[str, str, str, str]]) -> str:
    """Substitui href="./algum.md" por onclick="openMd(...)" — idempotente.

    Primeiro remove TODOS os onclick="return openMd(...)" existentes (limpeza),
    depois reinjeta uma única ocorrência por link.
    """
    by_path = {rel: (sid, title) for sid, rel, title, _ in payloads}

    # 1. Limpa onclick antigos que possam estar duplicados em execuções anteriores.
    cleanup = re.compile(r'\s*onclick="return openMd\([^)]*\);"')
    html, n_removed = cleanup.subn("", html)
    if n_removed:
        print(f"  [clean] removidos {n_removed} onclick antigos (idempotência)")

    # 2. Reinjeta exatamente um onclick por href .md
    pattern = re.compile(r'href="\./([^"]+\.md)"')

    def repl(m: re.Match) -> str:
        rel = m.group(1)
        if rel not in by_path:
            return m.group(0)
        sid, title = by_path[rel]
        safe_title = title.replace("'", "\\'")
        return f'href="./{rel}" onclick="return openMd(\'{sid}\', \'{safe_title}\', \'./{rel}\');"'

    new_html, n = pattern.subn(repl, html)
    print(f"  [ok] {n} links de .md convertidos para abrir o modal")
    return new_html


def main() -> None:
    print("[load] lendo index.html…")
    html = HTML_PATH.read_text(encoding="utf-8")

    if "id=\"md-modal\"" in html or "MD-VIEWER-CSS-START" in html:
        print("  [warn] visualizador já está no HTML — vou re-aplicar (idempotente)")
        # Remove o bloco HTML (modal + scripts + markdowns embarcados)
        html = re.sub(
            r"\n?<!-- MD-VIEWER-START -->.*?<!-- MD-VIEWER-END -->\n?",
            "\n",
            html,
            flags=re.DOTALL,
        )
        # Remove o bloco CSS para evitar duplicação
        html = re.sub(
            r"\n?/\* MD-VIEWER-CSS-START \*/.*?/\* MD-VIEWER-CSS-END \*/\n?",
            "\n",
            html,
            flags=re.DOTALL,
        )

    print("[load] embarcando .md…")
    payloads = load_md_payloads()

    print("[build] injetando CSS…")
    html = html.replace("</style>", CSS_ADDITION + "\n</style>", 1)

    print("[build] convertendo links .md…")
    html = replace_md_links(html, payloads)

    print("[build] injetando modal, scripts e markdown embarcado antes de </body>…")
    blocks = [MODAL_HTML]
    for sid, rel, title, content in payloads:
        blocks.append(
            f'<script type="text/markdown" id="{sid}" data-rel="{rel}" data-title="{html_lib.escape(title, quote=True)}">'
            + content
            + "</script>"
        )
    blocks.append(JS_ADDITION)
    inject = (
        "\n<!-- MD-VIEWER-START -->\n"
        + "\n".join(blocks)
        + "\n<!-- MD-VIEWER-END -->\n"
    )
    html = html.replace("</body>", inject + "\n</body>", 1)

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"\n[ok] HTML atualizado: {HTML_PATH}")
    print(f"     Tamanho final: {HTML_PATH.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
