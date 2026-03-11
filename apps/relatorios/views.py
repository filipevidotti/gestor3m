from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required

from .models import RelatorioMensal
from .utils import coletar_dados_mensal, gerar_pdf


@consultor_required
def listar(request):
    """Lista relatórios mensais."""
    if request.user.is_gestor:
        relatorios = RelatorioMensal.objects.all()
        clientes = Cliente.objects.filter(status="ativo")
    else:
        relatorios = RelatorioMensal.objects.filter(cliente__consultor=request.user)
        clientes = Cliente.objects.filter(consultor=request.user, status="ativo")

    relatorios = relatorios.select_related("cliente").order_by("-ano", "-mes")[:50]

    return render(request, "relatorios/listar.html", {
        "relatorios": relatorios,
        "clientes": clientes,
    })


@consultor_required
def gerar(request, pk):
    """Gera relatório mensal para um cliente."""
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        mes = int(request.POST.get("mes", timezone.localdate().month))
        ano = int(request.POST.get("ano", timezone.localdate().year))

        # Verificar se já existe
        rel, created = RelatorioMensal.objects.get_or_create(
            cliente=cliente, mes=mes, ano=ano,
        )

        # Coletar dados
        dados = coletar_dados_mensal(cliente, mes, ano)
        rel.dados = dados

        # Gerar PDF
        pdf = gerar_pdf(dados)
        if pdf:
            filename = f"relatorio_{cliente.empresa}_{mes:02d}_{ano}.pdf"
            rel.arquivo.save(filename, ContentFile(pdf.read()), save=False)

        rel.save()
        messages.success(request, f"Relatório de {mes:02d}/{ano} gerado.")
        return redirect("relatorios:listar")

    hoje = timezone.localdate()
    return render(request, "relatorios/gerar.html", {
        "cliente": cliente,
        "mes_atual": hoje.month,
        "ano_atual": hoje.year,
    })


@consultor_required
def download(request, pk):
    """Download do PDF."""
    if request.user.is_gestor:
        rel = get_object_or_404(RelatorioMensal, pk=pk)
    else:
        rel = get_object_or_404(RelatorioMensal, pk=pk, cliente__consultor=request.user)

    if not rel.arquivo:
        messages.error(request, "PDF não disponível.")
        return redirect("relatorios:listar")

    return FileResponse(rel.arquivo.open(), as_attachment=True, filename=rel.arquivo.name.split("/")[-1])


@consultor_required
def enviar(request, pk):
    """Envia relatório via WhatsApp e email."""
    if request.user.is_gestor:
        rel = get_object_or_404(RelatorioMensal, pk=pk)
    else:
        rel = get_object_or_404(RelatorioMensal, pk=pk, cliente__consultor=request.user)

    if request.method == "POST":
        from apps.core.services.brevo import enviar_email
        from apps.core.services.evolution import enviar_mensagem

        seller = getattr(rel.cliente, "usuario", None)

        # WhatsApp
        if seller and seller.telefone:
            texto = (
                f"Ola {seller.first_name}! 📊\n\n"
                f"Seu relatório mensal de {rel.mes:02d}/{rel.ano} está pronto!\n\n"
                f"Tarefas concluídas: {rel.dados.get('tarefas_concluidas', 0)}/{rel.dados.get('tarefas_total', 0)}\n"
                f"Reuniões: {rel.dados.get('reunioes', 0)}\n"
                f"Checklists: {rel.dados.get('checklists_total', 0)}\n\n"
                f"_3M Consultoria_"
            )
            enviar_mensagem(seller.telefone, texto)

        # Email
        if seller and seller.email and rel.arquivo:
            enviar_email(
                seller.email,
                seller.get_full_name(),
                f"Relatório Mensal {rel.mes:02d}/{rel.ano} — 3M Consultoria",
                f"<p>Olá {seller.first_name},</p>"
                f"<p>Seu relatório mensal está disponível.</p>"
                f"<p>3M Consultoria</p>",
            )

        rel.enviado = True
        rel.enviado_em = timezone.now()
        rel.save(update_fields=["enviado", "enviado_em"])
        messages.success(request, "Relatório enviado ao cliente.")

    return redirect("relatorios:listar")
