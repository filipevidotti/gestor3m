"""Geração de PDF da proposta comercial via WeasyPrint."""

import os
import re

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import escape


def _limpar_markdown(texto):
    """Remove formatação markdown e converte em HTML limpo com parágrafos."""
    if not texto:
        return ""
    # Remove **bold** e *italic*
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.+?)\*', r'\1', texto)
    # Remove headers ##
    texto = re.sub(r'^#{1,3}\s*', '', texto, flags=re.MULTILINE)
    # Remove bullet points - e *
    texto = re.sub(r'^\s*[-*]\s+', '• ', texto, flags=re.MULTILINE)
    return texto


def _texto_para_paragrafos(texto):
    """Converte texto limpo em parágrafos HTML."""
    if not texto:
        return ""
    texto = _limpar_markdown(texto)
    paragrafos = [p.strip() for p in texto.split('\n') if p.strip()]
    html_parts = []
    for p in paragrafos:
        p_escaped = escape(p)
        # Detectar se parece um título numerado (ex: "1. Otimização de Anúncios:")
        if re.match(r'^\d+\.?\s', p):
            html_parts.append(f'<p class="item-titulo">{p_escaped}</p>')
        elif p.startswith('•'):
            html_parts.append(f'<p class="item-bullet">{p_escaped}</p>')
        else:
            html_parts.append(f'<p>{p_escaped}</p>')
    return '\n'.join(html_parts)


def gerar_proposta_pdf(proposta):
    """Gera PDF profissional da proposta no formato de apresentação."""
    import weasyprint

    # Caminho absoluto das imagens da apresentação
    img_path = os.path.join(settings.BASE_DIR, "static", "img", "apresentacao")
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo-branca.png")

    # Processar textos: limpar markdown e converter em HTML
    diagnostico_html = _texto_para_paragrafos(proposta.diagnostico_ia)
    proposicao_html = _texto_para_paragrafos(proposta.proposicao_valor)
    comercial_html = _texto_para_paragrafos(proposta.proposta_comercial)

    html_string = render_to_string("propostas/_report_pdf.html", {
        "proposta": proposta,
        "servicos": proposta.servicos_incluidos.select_related("servico").all(),
        "metricas": proposta.metricas or {},
        "img_path": img_path,
        "logo_path": logo_path,
        "diagnostico_html": diagnostico_html,
        "proposicao_html": proposicao_html,
        "comercial_html": comercial_html,
    })

    pdf = weasyprint.HTML(
        string=html_string,
        base_url=str(settings.BASE_DIR),
    ).write_pdf()

    nome = proposta.nome_display or "Proposta"
    filename = f"Proposta_3M_{nome}_{proposta.created_at.strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
