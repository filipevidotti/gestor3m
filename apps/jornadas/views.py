from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.core.decorators import gestor_required, consultor_required
from apps.clientes.models import Cliente

from .forms import JornadaTemplateForm, EtapaTemplateForm
from .models import JornadaTemplate, EtapaTemplate, JornadaCliente, EtapaCliente


# ── Config Templates (gestor) ──────────────────────────────────


@gestor_required
def config_templates(request):
    templates = JornadaTemplate.objects.all()
    return render(request, "jornadas/config_templates.html", {"templates": templates})


@gestor_required
def criar_template(request):
    if request.method == "POST":
        form = JornadaTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Template de jornada criado.")
            return redirect("jornadas:config_templates")
    else:
        form = JornadaTemplateForm()
    return render(request, "jornadas/form_template.html", {"form": form})


@gestor_required
def editar_template(request, pk):
    template = get_object_or_404(JornadaTemplate, pk=pk)
    if request.method == "POST":
        form = JornadaTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Template atualizado.")
            return redirect("jornadas:config_templates")
    else:
        form = JornadaTemplateForm(instance=template)
    return render(request, "jornadas/form_template.html", {"form": form, "template": template})


@gestor_required
def excluir_template(request, pk):
    template = get_object_or_404(JornadaTemplate, pk=pk)
    if request.method == "POST":
        template.soft_delete()
        messages.success(request, "Template desativado.")
    return redirect("jornadas:config_templates")


@gestor_required
def gerenciar_etapas(request, pk):
    """Gerenciar etapas de um template de jornada."""
    template = get_object_or_404(JornadaTemplate, pk=pk)
    etapas = template.etapas.filter(is_active=True).order_by("ordem")

    if request.method == "POST":
        form = EtapaTemplateForm(request.POST)
        if form.is_valid():
            etapa = form.save(commit=False)
            etapa.jornada_template = template
            etapa.save()
            messages.success(request, f"Etapa '{etapa.nome}' adicionada.")
            return redirect("jornadas:gerenciar_etapas", pk=pk)
    else:
        form = EtapaTemplateForm()

    return render(request, "jornadas/gerenciar_etapas.html", {
        "template": template,
        "etapas": etapas,
        "form": form,
    })


# ── Jornada do Cliente ──────────────────────────────────────


@consultor_required
def timeline_cliente(request, cliente_pk):
    """Timeline visual da jornada do cliente."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    jornada = JornadaCliente.objects.filter(
        cliente=cliente, status="ativa"
    ).first()

    jornadas_anteriores = JornadaCliente.objects.filter(
        cliente=cliente
    ).exclude(status="ativa").order_by("-created_at")

    templates_disponiveis = JornadaTemplate.objects.filter(is_active=True)

    etapas = []
    if jornada:
        # Verificar atrasos
        for etapa in jornada.etapas.filter(is_active=True):
            etapa.verificar_atraso()
        etapas = jornada.etapas.filter(is_active=True).order_by("ordem")

    return render(request, "jornadas/timeline.html", {
        "cliente": cliente,
        "jornada": jornada,
        "etapas": etapas,
        "jornadas_anteriores": jornadas_anteriores,
        "templates_disponiveis": templates_disponiveis,
    })


@consultor_required
def gerar_jornada(request, cliente_pk):
    """Gera jornada para o cliente — manual ou via IA."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    if request.method == "POST":
        modo = request.POST.get("modo", "manual")

        if modo == "ia":
            # Disparar task assíncrona
            ultimo_diag = (
                cliente.diagnosticos.filter(status="completed")
                .order_by("-ano", "-mes")
                .first()
            )
            if not ultimo_diag:
                messages.error(request, "O cliente precisa ter ao menos um diagnóstico concluído para gerar jornada com IA.")
                return redirect("jornadas:timeline_cliente", cliente_pk=cliente_pk)

            from apps.ia.tasks import gerar_jornada_automatica
            gerar_jornada_automatica.delay(cliente.id, ultimo_diag.id)
            messages.info(request, "Jornada sendo gerada pela IA. Atualize a página em alguns instantes.")

        else:
            # Manual: usar template selecionado
            template_id = request.POST.get("template_id")
            template = get_object_or_404(JornadaTemplate, pk=template_id)
            hoje = timezone.now().date()

            from datetime import timedelta

            jornada = JornadaCliente.objects.create(
                cliente=cliente,
                jornada_template=template,
                nome=f"{template.nome} - {cliente.empresa}",
                data_inicio=hoje,
            )

            for ordem, etapa_tpl in enumerate(template.etapas.filter(is_active=True).order_by("ordem")):
                EtapaCliente.objects.create(
                    jornada=jornada,
                    etapa_template=etapa_tpl,
                    nome=etapa_tpl.nome,
                    descricao=etapa_tpl.descricao,
                    tipo=etapa_tpl.tipo,
                    ordem=ordem,
                    data_prevista=hoje + timedelta(days=etapa_tpl.dias_offset),
                    data_limite=hoje + timedelta(days=etapa_tpl.dias_offset + etapa_tpl.duracao_dias),
                )

            messages.success(request, f"Jornada '{template.nome}' criada com {jornada.total_etapas} etapas.")

        return redirect("jornadas:timeline_cliente", cliente_pk=cliente_pk)

    return redirect("jornadas:timeline_cliente", cliente_pk=cliente_pk)


@consultor_required
def recalibrar(request, pk):
    """Recalibra jornada existente com IA."""
    jornada = get_object_or_404(JornadaCliente, pk=pk)

    if request.method == "POST":
        ultimo_diag = (
            jornada.cliente.diagnosticos.filter(status="completed")
            .order_by("-ano", "-mes")
            .first()
        )
        if not ultimo_diag:
            messages.error(request, "Nenhum diagnóstico concluído encontrado.")
            return redirect("jornadas:timeline_cliente", cliente_pk=jornada.cliente.pk)

        from apps.ia.tasks import recalibrar_jornada_task
        recalibrar_jornada_task.delay(jornada.cliente.id, ultimo_diag.id)
        messages.info(request, "Recalibração em andamento. Atualize a página em instantes.")
        return redirect("jornadas:timeline_cliente", cliente_pk=jornada.cliente.pk)

    return redirect("jornadas:timeline_cliente", cliente_pk=jornada.cliente.pk)


@consultor_required
def concluir_etapa(request, pk):
    """Marca etapa como concluída (HTMX)."""
    etapa = get_object_or_404(EtapaCliente, pk=pk)

    if request.method == "POST":
        etapa.concluir()

        if request.headers.get("HX-Request"):
            return render(request, "jornadas/partials/etapa_card.html", {"etapa": etapa})

        messages.success(request, f"Etapa '{etapa.nome}' concluída!")
        return redirect("jornadas:timeline_cliente", cliente_pk=etapa.jornada.cliente.pk)

    return HttpResponse(status=405)


@consultor_required
def atualizar_status_etapa(request, pk):
    """Atualiza status da etapa (HTMX)."""
    etapa = get_object_or_404(EtapaCliente, pk=pk)

    if request.method == "POST":
        novo_status = request.POST.get("status")
        if novo_status in dict(EtapaCliente.Status.choices):
            if novo_status == "concluida":
                etapa.concluir()
            else:
                etapa.status = novo_status
                etapa.save(update_fields=["status", "updated_at"])

        if request.headers.get("HX-Request"):
            return render(request, "jornadas/partials/etapa_card.html", {"etapa": etapa})

        return redirect("jornadas:timeline_cliente", cliente_pk=etapa.jornada.cliente.pk)

    return HttpResponse(status=405)
