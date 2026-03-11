"""Geração de dados e PDF do relatório mensal."""
import io
import logging
from datetime import date

from django.db.models import Avg, Count
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def coletar_dados_mensal(cliente, mes, ano):
    """Coleta todos os dados para o relatório mensal de um cliente."""
    from apps.checklists.models import ChecklistExecution
    from apps.diagnosticos.models import Diagnostic
    from apps.reunioes.models import Reuniao
    from apps.tarefas.models import Tarefa

    # Tarefas do mês
    tarefas_total = Tarefa.objects.filter(
        cliente=cliente,
        created_at__year=ano, created_at__month=mes,
    ).count()
    tarefas_concluidas = Tarefa.objects.filter(
        cliente=cliente, status="concluido",
        updated_at__year=ano, updated_at__month=mes,
    ).count()

    # Reuniões
    reunioes = Reuniao.objects.filter(
        cliente=cliente,
        data__year=ano, data__month=mes,
    ).count()

    # Checklists
    checklists = ChecklistExecution.objects.filter(
        cliente=cliente,
        updated_at__year=ano, updated_at__month=mes,
        status="completed",
    )
    checklists_total = checklists.count()
    checklists_score = checklists.aggregate(media=Avg("score"))["media"] or 0

    # Diagnóstico do mês
    diagnostico = Diagnostic.objects.filter(
        cliente=cliente, mes=mes, ano=ano, status="completed"
    ).first()

    return {
        "cliente_nome": cliente.empresa,
        "consultor_nome": cliente.consultor.get_full_name() if cliente.consultor else "",
        "mes": mes,
        "ano": ano,
        "periodo": f"{mes:02d}/{ano}",
        "tarefas_total": tarefas_total,
        "tarefas_concluidas": tarefas_concluidas,
        "tarefas_taxa": round((tarefas_concluidas / tarefas_total * 100) if tarefas_total > 0 else 0),
        "reunioes": reunioes,
        "checklists_total": checklists_total,
        "checklists_score": round(float(checklists_score), 1),
        "diagnostico_score": float(diagnostico.score) if diagnostico else None,
        "diagnostico_categorias": diagnostico.scores_por_categoria if diagnostico else {},
    }


def gerar_pdf(dados):
    """Gera PDF do relatório usando WeasyPrint."""
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning("WeasyPrint não instalado. PDF não gerado.")
        return None

    html_string = render_to_string("relatorios/_report_pdf.html", {"dados": dados})
    pdf_file = io.BytesIO()
    HTML(string=html_string).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file
