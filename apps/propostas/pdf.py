"""Geração de PDF da proposta comercial via WeasyPrint."""

from django.http import HttpResponse
from django.template.loader import render_to_string


def gerar_proposta_pdf(proposta):
    """Gera PDF profissional da proposta comercial."""
    import weasyprint

    html_string = render_to_string("propostas/_report_pdf.html", {
        "proposta": proposta,
        "servicos": proposta.servicos_incluidos.select_related("servico").all(),
        "metricas": proposta.metricas or {},
    })
    pdf = weasyprint.HTML(string=html_string).write_pdf()

    nome = proposta.nome_display or "Proposta"
    filename = f"Proposta_3M_{nome}_{proposta.created_at.strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
