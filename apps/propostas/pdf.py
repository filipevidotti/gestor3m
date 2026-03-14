"""Geração de PDF da proposta comercial via WeasyPrint."""

import os

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string


def gerar_proposta_pdf(proposta):
    """Gera PDF profissional da proposta no formato de apresentação."""
    import weasyprint

    # Caminho absoluto das imagens da apresentação
    img_path = os.path.join(settings.BASE_DIR, "static", "img", "apresentacao")
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo-branca.png")

    html_string = render_to_string("propostas/_report_pdf.html", {
        "proposta": proposta,
        "servicos": proposta.servicos_incluidos.select_related("servico").all(),
        "metricas": proposta.metricas or {},
        "img_path": img_path,
        "logo_path": logo_path,
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
