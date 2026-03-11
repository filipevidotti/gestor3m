from collections import OrderedDict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required, gestor_required
from .forms import DiagnosticTemplateForm, DiagnosticQuestionFormSet, DiagnosticForm
from .models import DiagnosticTemplate, DiagnosticQuestion, Diagnostic, DiagnosticAnswer


# ─── Template CRUD (Gestor) ───────────────────────────────

@gestor_required
def template_listar(request):
    templates = DiagnosticTemplate.objects.prefetch_related("perguntas").all()
    return render(request, "diagnosticos/template_listar.html", {
        "templates": templates,
    })


@gestor_required
def template_criar(request):
    if request.method == "POST":
        form = DiagnosticTemplateForm(request.POST)
        formset = DiagnosticQuestionFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            template = form.save(commit=False)
            template.criado_por = request.user
            template.save()
            formset.instance = template
            formset.save()
            messages.success(request, f"Template '{template.nome}' criado.")
            return redirect("diagnosticos:template_listar")
    else:
        form = DiagnosticTemplateForm()
        formset = DiagnosticQuestionFormSet()
    return render(request, "diagnosticos/template_form.html", {
        "form": form,
        "formset": formset,
        "form_title": "Novo Template de Diagnóstico",
    })


@gestor_required
def template_editar(request, pk):
    template = get_object_or_404(DiagnosticTemplate, pk=pk)
    if request.method == "POST":
        form = DiagnosticTemplateForm(request.POST, instance=template)
        formset = DiagnosticQuestionFormSet(request.POST, instance=template)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Template '{template.nome}' atualizado.")
            return redirect("diagnosticos:template_listar")
    else:
        form = DiagnosticTemplateForm(instance=template)
        formset = DiagnosticQuestionFormSet(instance=template)
    return render(request, "diagnosticos/template_form.html", {
        "form": form,
        "formset": formset,
        "form_title": f"Editar: {template.nome}",
    })


# ─── Diagnósticos ─────────────────────────────────────────

@login_required
def listar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    if request.user.is_seller:
        if not hasattr(request.user, "cliente_perfil") or request.user.cliente_perfil.pk != cliente_pk:
            return HttpResponseForbidden("Acesso negado.")
    elif request.user.is_consultor and cliente.consultor != request.user:
        return HttpResponseForbidden("Acesso negado.")

    diagnosticos = Diagnostic.objects.filter(
        cliente=cliente
    ).select_related("template")
    return render(request, "diagnosticos/listar.html", {
        "cliente": cliente,
        "diagnosticos": diagnosticos,
    })


@consultor_required
def criar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    if request.method == "POST":
        form = DiagnosticForm(request.POST)
        if form.is_valid():
            diag = form.save(commit=False)
            diag.cliente = cliente
            diag.executor = request.user
            diag.save()
            messages.success(request, "Diagnóstico criado.")
            return redirect("diagnosticos:executar", pk=diag.pk)
    else:
        now = timezone.now()
        form = DiagnosticForm(initial={
            "cliente": cliente,
            "mes": now.month,
            "ano": now.year,
        })
    return render(request, "diagnosticos/form.html", {
        "form": form,
        "form_title": f"Novo Diagnóstico: {cliente.empresa}",
        "cancel_url": f"/diagnosticos/cliente/{cliente.pk}/",
        "cliente": cliente,
    })


@login_required
def detalhe(request, pk):
    diag = get_object_or_404(
        Diagnostic.objects.select_related("template", "cliente", "executor"), pk=pk
    )
    respostas = diag.respostas.select_related("question").all()

    # Agrupar respostas por categoria
    categorias = OrderedDict()
    for resp in respostas:
        cat = resp.question.categoria
        if cat not in categorias:
            categorias[cat] = {"respostas": [], "score": 0}
        categorias[cat]["respostas"].append(resp)

    # Scores por categoria
    if diag.scores_por_categoria:
        for cat, score in diag.scores_por_categoria.items():
            if cat in categorias:
                categorias[cat]["score"] = score

    # Benchmark do segmento
    benchmark = None
    if diag.cliente.nicho:
        from apps.diagnosticos.models import BenchmarkSegmento
        benchmark = BenchmarkSegmento.objects.filter(
            segmento__iexact=diag.cliente.nicho
        ).first()

    return render(request, "diagnosticos/detalhe.html", {
        "diag": diag,
        "categorias": categorias,
        "benchmark": benchmark,
    })


@consultor_required
def executar(request, pk):
    """Execução do diagnóstico por categoria."""
    diag = get_object_or_404(
        Diagnostic.objects.select_related("template", "cliente"), pk=pk
    )
    if diag.status == Diagnostic.Status.PENDING:
        diag.status = Diagnostic.Status.IN_PROGRESS
        diag.save(update_fields=["status", "updated_at"])

    perguntas = diag.template.perguntas.all()
    respostas_existentes = {r.question_id: r for r in diag.respostas.all()}

    # Agrupar por categoria
    categorias = OrderedDict()
    for p in perguntas:
        if p.categoria not in categorias:
            categorias[p.categoria] = []
        categorias[p.categoria].append({
            "pergunta": p,
            "resposta": respostas_existentes.get(p.pk),
        })

    # Categoria ativa + navegação prev/next
    cat_param = request.GET.get("cat")
    cat_names = list(categorias.keys())
    cat_ativa = cat_param if cat_param in categorias else (cat_names[0] if cat_names else None)

    prev_cat = next_cat = None
    if cat_ativa and cat_ativa in cat_names:
        idx = cat_names.index(cat_ativa)
        if idx > 0:
            prev_cat = cat_names[idx - 1]
        if idx < len(cat_names) - 1:
            next_cat = cat_names[idx + 1]

    return render(request, "diagnosticos/executar.html", {
        "diag": diag,
        "categorias": categorias,
        "cat_names": cat_names,
        "cat_ativa": cat_ativa,
        "prev_cat": prev_cat,
        "next_cat": next_cat,
    })


@consultor_required
def salvar_respostas(request, pk):
    """Salvar respostas de uma categoria via POST."""
    diag = get_object_or_404(Diagnostic, pk=pk)
    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("q_"):
                question_id = key.replace("q_", "")
                try:
                    question = DiagnosticQuestion.objects.get(pk=question_id)
                    answer, created = DiagnosticAnswer.objects.get_or_create(
                        diagnostic=diag,
                        question=question,
                    )
                    if question.tipo == DiagnosticQuestion.TipoPergunta.SELECTION:
                        answer.value_text = value
                    else:
                        try:
                            answer.value_numeric = Decimal(value)
                        except (ValueError, TypeError):
                            answer.value_numeric = 0
                    answer.calcular_score()
                    answer.save()
                except DiagnosticQuestion.DoesNotExist:
                    pass

        next_cat = request.POST.get("next_cat")
        if next_cat:
            return redirect(f"/diagnosticos/{pk}/executar/?cat={next_cat}")
        messages.success(request, "Respostas salvas.")
    return redirect("diagnosticos:executar", pk=pk)


@consultor_required
def completar(request, pk):
    """Finalizar diagnóstico e calcular score."""
    diag = get_object_or_404(Diagnostic, pk=pk)
    if request.method == "POST":
        diag.calcular_score()
        diag.status = Diagnostic.Status.COMPLETED
        diag.completed_at = timezone.now()
        diag.save()

        # Trigger IA: gerar ou recalibrar jornada
        from apps.jornadas.models import JornadaCliente
        jornada_ativa = JornadaCliente.objects.filter(
            cliente=diag.cliente, status="ativa"
        ).first()
        if jornada_ativa:
            from apps.ia.tasks import recalibrar_jornada_task
            recalibrar_jornada_task.delay(diag.cliente.id, diag.id)
        else:
            from apps.ia.tasks import gerar_jornada_automatica
            gerar_jornada_automatica.delay(diag.cliente.id, diag.id)

        messages.success(request, f"Diagnóstico finalizado! Score: {diag.score}/10")
        return redirect("diagnosticos:detalhe", pk=pk)
    return redirect("diagnosticos:executar", pk=pk)


@consultor_required
def repetir(request, pk):
    """Copiar diagnóstico para próximo mês."""
    diag = get_object_or_404(Diagnostic, pk=pk)
    if request.method == "POST":
        novo = diag.copy_to_next_month()
        messages.success(request, f"Diagnóstico criado para {novo.mes:02d}/{novo.ano}.")
        return redirect("diagnosticos:executar", pk=novo.pk)
    return redirect("diagnosticos:detalhe", pk=pk)


@consultor_required
def editar(request, pk):
    diag = get_object_or_404(Diagnostic, pk=pk)
    if request.method == "POST":
        form = DiagnosticForm(request.POST, instance=diag)
        if form.is_valid():
            diag = form.save()
            messages.success(request, "Diagnóstico atualizado.")
            return redirect("diagnosticos:listar", cliente_pk=diag.cliente.pk)
    else:
        form = DiagnosticForm(instance=diag)
    return render(request, "diagnosticos/form.html", {
        "form": form,
        "form_title": f"Editar Diagnóstico: {diag.mes:02d}/{diag.ano}",
        "cancel_url": f"/diagnosticos/cliente/{diag.cliente.pk}/",
        "cliente": diag.cliente,
    })
