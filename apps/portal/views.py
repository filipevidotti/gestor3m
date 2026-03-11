from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from apps.core.decorators import role_required

from apps.accounts.models import User
from apps.checklists.models import ChecklistExecution, ChecklistExecutionItem
from apps.clientes.models import Cliente, Funcionario
from apps.diagnosticos.models import Diagnostic
from apps.planos.models import PlanoAcao
from apps.reunioes.models import Reuniao
from apps.tarefas.models import Tarefa
from apps.treinamentos.models import TreinamentoRealizado
from apps.anuncios.models import UploadCurvaABC, UploadMetricas, AnuncioAtualizar

from django.db.models import Avg, Q
from django.utils import timezone
from datetime import timedelta


def portal_required(view_func):
    """Permite seller e funcionario no portal."""
    return role_required("seller", "funcionario")(view_func)


def seller_only(view_func):
    """Apenas seller (dono). Funcionario nao acessa."""
    return role_required("seller")(view_func)


def get_cliente(request):
    """Retorna o Cliente vinculado ao usuario logado (seller ou funcionario)."""
    user = request.user
    if user.role == "seller":
        if hasattr(user, "cliente_perfil") and user.cliente_perfil:
            return user.cliente_perfil
        return None
    if user.role == "funcionario":
        if hasattr(user, "funcionario_perfil") and user.funcionario_perfil:
            return user.funcionario_perfil.cliente
        return None
    return None


# ── Dashboard ───────────────────────────────────────────────


@portal_required
def dashboard(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    is_func = request.user.is_funcionario

    if is_func:
        # Funcionario: so suas tarefas e checklists atribuidos
        tarefas_pendentes = Tarefa.objects.filter(
            cliente=cliente,
            responsavel=request.user,
            is_active=True,
            status__in=["pendente", "em_andamento"],
        )[:5]

        checklists_pendentes = ChecklistExecution.objects.filter(
            cliente=cliente,
            executor=request.user,
            template__target_audience="client",
            status__in=["pending", "in_progress"],
        ).select_related("template")[:5]

        checklists_concluidos = ChecklistExecution.objects.filter(
            cliente=cliente, executor=request.user, status="completed"
        ).count()
        checklists_total = ChecklistExecution.objects.filter(
            cliente=cliente, executor=request.user
        ).count()
    else:
        # Seller: tudo do cliente
        tarefas_pendentes = Tarefa.objects.filter(
            cliente=cliente,
            is_active=True,
            status__in=["pendente", "em_andamento"],
        )[:5]

        checklists_pendentes = ChecklistExecution.objects.filter(
            cliente=cliente,
            template__target_audience="client",
            status__in=["pending", "in_progress"],
        ).select_related("template")[:5]

        checklists_concluidos = ChecklistExecution.objects.filter(
            cliente=cliente, status="completed"
        ).count()
        checklists_total = ChecklistExecution.objects.filter(cliente=cliente).count()

    reunioes_proximas = Reuniao.objects.filter(cliente=cliente).order_by("-data")[:3] if not is_func else []

    ultimo_diagnostico = None
    if not is_func:
        ultimo_diagnostico = (
            Diagnostic.objects.filter(cliente=cliente, status="completed")
            .select_related("template")
            .order_by("-completed_at")
            .first()
        )

    return render(request, "portal/dashboard.html", {
        "cliente": cliente,
        "checklists_pendentes": checklists_pendentes,
        "tarefas_pendentes": tarefas_pendentes,
        "reunioes_proximas": reunioes_proximas,
        "ultimo_diagnostico": ultimo_diagnostico,
        "checklists_concluidos": checklists_concluidos,
        "checklists_total": checklists_total,
    })


# ── Checklists ──────────────────────────────────────────────


@portal_required
def checklists(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    execucoes = ChecklistExecution.objects.filter(
        cliente=cliente, template__target_audience="client"
    ).select_related("template", "executor").order_by("-created_at")

    if request.user.is_funcionario:
        execucoes = execucoes.filter(executor=request.user)

    status_filter = request.GET.get("status")
    if status_filter:
        execucoes = execucoes.filter(status=status_filter)

    return render(request, "portal/checklists.html", {
        "cliente": cliente,
        "execucoes": execucoes,
    })


@portal_required
def checklist_detalhe(request, pk):
    cliente = get_cliente(request)
    filters = {"pk": pk, "cliente": cliente}
    if request.user.is_funcionario:
        filters["executor"] = request.user
    execucao = get_object_or_404(ChecklistExecution, **filters)

    itens = execucao.itens.select_related("template_item__category").order_by(
        "template_item__category__ordem", "template_item__ordem"
    )
    categorias = OrderedDict()
    for item in itens:
        cat = item.template_item.category.nome if item.template_item.category else "Geral"
        categorias.setdefault(cat, []).append(item)

    return render(request, "portal/checklist_detalhe.html", {
        "checklist": execucao,
        "categorias": categorias,
    })


@portal_required
def checklist_executar(request, pk):
    cliente = get_cliente(request)
    filters = {"pk": pk, "cliente": cliente}
    if request.user.is_funcionario:
        filters["executor"] = request.user
    execucao = get_object_or_404(ChecklistExecution, **filters)

    if execucao.status == "completed":
        return redirect("portal:checklist_detalhe", pk=pk)

    itens = execucao.itens.select_related("template_item__category").prefetch_related(
        "evidencias"
    ).order_by("template_item__category__ordem", "template_item__ordem")

    categorias = OrderedDict()
    for item in itens:
        cat = item.template_item.category.nome if item.template_item.category else "Geral"
        if cat not in categorias:
            categorias[cat] = {"itens": [], "total": 0, "completos": 0}
        categorias[cat]["itens"].append(item)
        categorias[cat]["total"] += 1
        if item.status != "pending":
            categorias[cat]["completos"] += 1

    cat_names = list(categorias.keys())
    cat_ativa = request.GET.get("cat", cat_names[0] if cat_names else None)

    return render(request, "portal/checklist_executar.html", {
        "checklist": execucao,
        "categorias": categorias,
        "cat_ativa": cat_ativa,
        "cat_names": cat_names,
    })


@portal_required
def checklist_salvar(request, pk):
    cliente = get_cliente(request)
    filters = {"pk": pk, "cliente": cliente}
    if request.user.is_funcionario:
        filters["executor"] = request.user
    execucao = get_object_or_404(ChecklistExecution, **filters)

    if request.method == "POST":
        if execucao.status == "pending":
            execucao.status = "in_progress"
            execucao.save(update_fields=["status"])

        for key, value in request.POST.items():
            if key.startswith("item_"):
                item_id = key.replace("item_", "")
                try:
                    item = execucao.itens.get(pk=item_id)
                    item.status = value
                    item.completed_by = request.user
                    item.save(update_fields=["status", "completed_by"])
                except ChecklistExecutionItem.DoesNotExist:
                    pass

            if key.startswith("note_"):
                item_id = key.replace("note_", "")
                try:
                    item = execucao.itens.get(pk=item_id)
                    item.note = value
                    item.save(update_fields=["note"])
                except ChecklistExecutionItem.DoesNotExist:
                    pass

        next_cat = request.POST.get("next_cat")
        if next_cat:
            return redirect(f"/portal/checklists/{pk}/executar/?cat={next_cat}")

        messages.success(request, "Respostas salvas.")
        return redirect("portal:checklist_executar", pk=pk)

    return redirect("portal:checklist_executar", pk=pk)


@portal_required
def checklist_completar(request, pk):
    cliente = get_cliente(request)
    filters = {"pk": pk, "cliente": cliente}
    if request.user.is_funcionario:
        filters["executor"] = request.user
    execucao = get_object_or_404(ChecklistExecution, **filters)

    if request.method == "POST":
        execucao.calcular_score()
        messages.success(request, f"Checklist finalizado! Score: {execucao.score}%")
        return redirect("portal:checklist_detalhe", pk=pk)

    return redirect("portal:checklist_executar", pk=pk)


# ── Diagnosticos (seller only) ──────────────────────────────


@seller_only
def diagnosticos(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    diags = (
        Diagnostic.objects.filter(cliente=cliente, status="completed")
        .select_related("template")
        .order_by("-completed_at")
    )

    return render(request, "portal/diagnosticos.html", {
        "cliente": cliente,
        "diagnosticos": diags,
    })


@seller_only
def diagnostico_detalhe(request, pk):
    cliente = get_cliente(request)
    diag = get_object_or_404(
        Diagnostic.objects.select_related("template"),
        pk=pk,
        cliente=cliente,
        status="completed",
    )
    respostas = diag.answers.select_related("question").order_by(
        "question__categoria", "question__ordem"
    )

    categorias = OrderedDict()
    for resp in respostas:
        cat = resp.question.categoria
        categorias.setdefault(cat, []).append(resp)

    return render(request, "portal/diagnostico_detalhe.html", {
        "diagnostico": diag,
        "categorias": categorias,
    })


# ── Tarefas ─────────────────────────────────────────────────


@portal_required
def tarefas(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    lista = Tarefa.objects.filter(
        cliente=cliente, is_active=True
    ).select_related("checklist_execution", "tipo", "responsavel").order_by("-created_at")

    if request.user.is_funcionario:
        lista = lista.filter(responsavel=request.user)

    return render(request, "portal/tarefas.html", {
        "cliente": cliente,
        "tarefas": lista,
    })


@portal_required
def tarefa_concluir(request, pk):
    """Seller ou funcionario marca tarefa como concluida."""
    cliente = get_cliente(request)
    if not cliente:
        return HttpResponseForbidden()

    filters = {"pk": pk, "cliente": cliente, "is_active": True}
    if request.user.is_funcionario:
        filters["responsavel"] = request.user
    tarefa = get_object_or_404(Tarefa, **filters)

    if request.method == "POST" and tarefa.status != "concluido":
        tarefa.status = "concluido"
        tarefa.concluido_em = timezone.now()
        tarefa.save(update_fields=["status", "concluido_em"])

    html = render_to_string("portal/_tarefa_linha.html", {"tarefa": tarefa}, request=request)
    return HttpResponse(html)


# ── Reunioes (seller only) ──────────────────────────────────


@seller_only
def reunioes(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    lista = Reuniao.objects.filter(cliente=cliente).order_by("-data")

    return render(request, "portal/reunioes.html", {
        "cliente": cliente,
        "reunioes": lista,
    })


# ── Planos de Acao ──────────────────────────────────────────


@portal_required
def planos(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    lista = PlanoAcao.objects.filter(cliente=cliente).prefetch_related("itens")

    return render(request, "portal/planos.html", {
        "cliente": cliente,
        "planos": lista,
    })


@portal_required
def plano_detalhe(request, pk):
    cliente = get_cliente(request)
    plano = get_object_or_404(
        PlanoAcao.objects.prefetch_related("itens__responsavel"), pk=pk, cliente=cliente
    )

    return render(request, "portal/plano_detalhe.html", {
        "plano": plano,
        "is_funcionario": request.user.is_funcionario,
    })


# ── Treinamentos (seller only) ─────────────────────────────


@seller_only
def treinamentos(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    realizados = (
        TreinamentoRealizado.objects.filter(cliente=cliente)
        .select_related("treinamento")
        .order_by("-data")
    )

    return render(request, "portal/treinamentos.html", {
        "cliente": cliente,
        "treinamentos": realizados,
    })


# ── Anuncios (seller only) ─────────────────────────────────


@seller_only
def anuncios_curva_abc(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    uploads = UploadCurvaABC.objects.filter(cliente=cliente).order_by("-data_referencia")
    upload_atual = uploads.first()
    upload_anterior = uploads[1] if uploads.count() > 1 else None

    sel_id = request.GET.get("upload")
    if sel_id:
        upload_atual = uploads.filter(pk=sel_id).first() or upload_atual

    itens_atual = []
    itens_anterior_map = {}
    if upload_atual:
        itens_atual = list(upload_atual.itens.all())
    if upload_anterior:
        itens_anterior_map = {i.mlb: i for i in upload_anterior.itens.all()}

    comparativo = []
    for item in itens_atual:
        ant = itens_anterior_map.get(item.mlb)
        comparativo.append({
            "item": item,
            "anterior": ant,
            "fat_diff": float(item.faturamento - ant.faturamento) if ant else None,
            "est_diff": item.estoque - ant.estoque if ant else None,
            "qtd_diff": item.quantidade - ant.quantidade if ant else None,
            "classe_mudou": ant.classe != item.classe if ant else False,
        })

    ultimos = list(uploads[:8])
    ultimos.reverse()
    chart_labels = [u.data_referencia.strftime("%d/%m") for u in ultimos]
    chart_faturamento = []
    for u in ultimos:
        total = sum(float(i.faturamento) for i in u.itens.all())
        chart_faturamento.append(round(total, 2))

    return render(request, "portal/curva_abc.html", {
        "cliente": cliente,
        "uploads": uploads,
        "upload_atual": upload_atual,
        "comparativo": comparativo,
        "chart_labels": chart_labels,
        "chart_faturamento": chart_faturamento,
    })


@seller_only
def anuncios_metricas(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    uploads = UploadMetricas.objects.filter(cliente=cliente).order_by("-data_referencia")
    upload_atual = uploads.first()
    upload_anterior = uploads[1] if uploads.count() > 1 else None

    sel_id = request.GET.get("upload")
    if sel_id:
        upload_atual = uploads.filter(pk=sel_id).first() or upload_atual

    itens_atual = []
    itens_anterior_map = {}
    if upload_atual:
        itens_atual = list(upload_atual.itens.all())
    if upload_anterior:
        itens_anterior_map = {i.mlb: i for i in upload_anterior.itens.all()}

    comparativo = []
    for item in itens_atual:
        ant = itens_anterior_map.get(item.mlb)
        comparativo.append({
            "item": item,
            "anterior": ant,
            "visitas_diff": item.visitas - ant.visitas if ant else None,
            "vendas_diff": item.vendas_30d - ant.vendas_30d if ant else None,
            "conv_diff": float(item.conversao - ant.conversao) if ant else None,
        })

    ultimos = list(uploads[:8])
    ultimos.reverse()
    chart_labels = [u.data_referencia.strftime("%d/%m") for u in ultimos]
    chart_visitas = [sum(i.visitas for i in u.itens.all()) for u in ultimos]
    chart_vendas = [sum(i.vendas_30d for i in u.itens.all()) for u in ultimos]

    return render(request, "portal/metricas.html", {
        "cliente": cliente,
        "uploads": uploads,
        "upload_atual": upload_atual,
        "comparativo": comparativo,
        "chart_labels": chart_labels,
        "chart_visitas": chart_visitas,
        "chart_vendas": chart_vendas,
    })


@seller_only
def anuncios_atualizacoes(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    anuncios = AnuncioAtualizar.objects.filter(cliente=cliente)
    total = anuncios.count()
    feitos = anuncios.exclude(
        Q(precisa_foto=True, foto_feito=False) | Q(precisa_video=True, video_feito=False)
    ).count()

    pendentes = anuncios.filter(
        Q(precisa_foto=True, foto_feito=False) | Q(precisa_video=True, video_feito=False)
    )

    return render(request, "portal/atualizacoes.html", {
        "cliente": cliente,
        "anuncios": pendentes,
        "total": total,
        "feitos": feitos,
    })


@seller_only
def anuncio_marcar_feito(request, pk):
    """Seller marca foto ou video como feito."""
    cliente = get_cliente(request)
    if not cliente:
        return HttpResponseForbidden()

    anuncio = get_object_or_404(AnuncioAtualizar, pk=pk, cliente=cliente)

    if request.method == "POST":
        tipo = request.POST.get("tipo")  # "foto" ou "video"
        if tipo == "foto" and anuncio.precisa_foto:
            anuncio.foto_feito = True
        elif tipo == "video" and anuncio.precisa_video:
            anuncio.video_feito = True
        anuncio.save()

        # Se tudo concluido, registrar data e criar tarefa concluida
        if anuncio.concluido and not anuncio.concluido_em:
            anuncio.concluido_em = timezone.now()
            anuncio.save(update_fields=["concluido_em"])

            Tarefa.objects.create(
                cliente=cliente,
                criado_por=request.user,
                responsavel=request.user,
                descricao=f"Atualização concluída: {anuncio.mlb} - {anuncio.titulo[:60]}",
                status="concluido",
                concluido_em=timezone.now(),
            )

    if request.htmx:
        return render(request, "portal/_anuncio_row.html", {"an": anuncio})
    return redirect("portal:anuncios_atualizacoes")


# ── Evolução (seller only) ─────────────────────────────────


@seller_only
def minha_evolucao(request):
    """Dashboard de evolução do seller — antes/depois com gráficos."""
    import json

    from apps.checklists.models import ChecklistExecution
    from apps.diagnosticos.models import Diagnostic

    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    # Diagnósticos completos ordenados
    diagnosticos = (
        Diagnostic.objects.filter(cliente=cliente, status="completed")
        .order_by("ano", "mes")
    )

    scores_mensal = []
    scores_categorias_atual = {}
    scores_categorias_primeiro = {}

    for d in diagnosticos:
        label = f"{d.mes:02d}/{d.ano}"
        scores_mensal.append({"label": label, "score": float(d.score or 0)})
        if d.scores_por_categoria:
            if not scores_categorias_primeiro:
                scores_categorias_primeiro = {
                    k: float(v) for k, v in d.scores_por_categoria.items()
                }
            scores_categorias_atual = {
                k: float(v) for k, v in d.scores_por_categoria.items()
            }

    # Tarefas e reuniões por mês (últimos 6 meses)
    hoje = timezone.localdate()
    tarefas_mensal = []
    reunioes_mensal = []
    for i in range(5, -1, -1):
        mes_ref = (hoje.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        label = f"{mes_ref.month:02d}/{mes_ref.year}"

        t_concluidas = Tarefa.objects.filter(
            cliente=cliente, status="concluido",
            updated_at__year=mes_ref.year, updated_at__month=mes_ref.month,
        ).count()
        t_total = Tarefa.objects.filter(
            cliente=cliente,
            created_at__year=mes_ref.year, created_at__month=mes_ref.month,
        ).count()
        tarefas_mensal.append({"label": label, "concluidas": t_concluidas, "total": t_total})

        r_count = Reuniao.objects.filter(
            cliente=cliente,
            data__year=mes_ref.year, data__month=mes_ref.month,
        ).count()
        reunioes_mensal.append({"label": label, "total": r_count})

    # Checklists score médio
    checklists_score = ChecklistExecution.objects.filter(
        cliente=cliente, status="completed",
    ).aggregate(media=Avg("score"))["media"] or 0

    # Comparativo
    score_primeiro = float(diagnosticos.first().score) if diagnosticos.exists() else 0
    score_atual = float(diagnosticos.last().score) if diagnosticos.exists() else 0
    variacao = score_atual - score_primeiro

    context = {
        "cliente": cliente,
        "scores_mensal_json": json.dumps(scores_mensal),
        "categorias_primeiro_json": json.dumps(scores_categorias_primeiro),
        "categorias_atual_json": json.dumps(scores_categorias_atual),
        "tarefas_mensal_json": json.dumps(tarefas_mensal),
        "reunioes_mensal_json": json.dumps(reunioes_mensal),
        "checklists_score": round(checklists_score, 1),
        "score_primeiro": score_primeiro,
        "score_atual": score_atual,
        "variacao": round(variacao, 1),
        "total_diagnosticos": diagnosticos.count(),
        "total_reunioes": Reuniao.objects.filter(cliente=cliente).count(),
        "total_tarefas_concluidas": Tarefa.objects.filter(
            cliente=cliente, status="concluido"
        ).count(),
    }
    return render(request, "portal/evolucao.html", context)


# ── Equipe (seller only) ────────────────────────────────────


@seller_only
def equipe_listar(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    funcionarios = Funcionario.objects.filter(
        cliente=cliente
    ).select_related("usuario").order_by("usuario__first_name")

    return render(request, "portal/equipe.html", {
        "cliente": cliente,
        "funcionarios": funcionarios,
    })


@seller_only
def equipe_criar(request):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        sobrenome = request.POST.get("sobrenome", "").strip()
        email = request.POST.get("email", "").strip()
        cargo = request.POST.get("cargo", "").strip()
        telefone = request.POST.get("telefone", "").strip()
        senha = request.POST.get("senha", "").strip()

        if not nome or not email or not senha:
            messages.error(request, "Nome, e-mail e senha são obrigatórios.")
            return render(request, "portal/equipe_form.html", {
                "cliente": cliente,
                "form_title": "Novo Funcionário",
                "dados": request.POST,
            })

        if User.objects.filter(email=email).exists():
            messages.error(request, "Já existe um usuário com este e-mail.")
            return render(request, "portal/equipe_form.html", {
                "cliente": cliente,
                "form_title": "Novo Funcionário",
                "dados": request.POST,
            })

        # Gerar username unico a partir do email
        username = email.split("@")[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        usuario = User.objects.create_user(
            username=username,
            email=email,
            password=senha,
            first_name=nome,
            last_name=sobrenome,
            role="funcionario",
            telefone=telefone,
        )

        Funcionario.objects.create(
            usuario=usuario,
            cliente=cliente,
            cargo=cargo,
            cadastrado_por=request.user,
        )

        messages.success(request, f"Funcionário {nome} cadastrado com sucesso!")
        return redirect("portal:equipe_listar")

    return render(request, "portal/equipe_form.html", {
        "cliente": cliente,
        "form_title": "Novo Funcionário",
        "dados": {},
    })


@seller_only
def equipe_editar(request, pk):
    cliente = get_cliente(request)
    if not cliente:
        return render(request, "portal/sem_vinculo.html")

    funcionario = get_object_or_404(Funcionario, pk=pk, cliente=cliente)

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        sobrenome = request.POST.get("sobrenome", "").strip()
        cargo = request.POST.get("cargo", "").strip()
        telefone = request.POST.get("telefone", "").strip()
        nova_senha = request.POST.get("senha", "").strip()

        if not nome:
            messages.error(request, "Nome é obrigatório.")
            return render(request, "portal/equipe_form.html", {
                "cliente": cliente,
                "form_title": "Editar Funcionário",
                "funcionario": funcionario,
                "dados": request.POST,
            })

        usuario = funcionario.usuario
        usuario.first_name = nome
        usuario.last_name = sobrenome
        usuario.telefone = telefone
        usuario.save(update_fields=["first_name", "last_name", "telefone"])

        if nova_senha:
            usuario.set_password(nova_senha)
            usuario.save(update_fields=["password"])

        funcionario.cargo = cargo
        funcionario.save(update_fields=["cargo", "updated_at"])

        messages.success(request, "Funcionário atualizado.")
        return redirect("portal:equipe_listar")

    return render(request, "portal/equipe_form.html", {
        "cliente": cliente,
        "form_title": "Editar Funcionário",
        "funcionario": funcionario,
        "dados": {
            "nome": funcionario.usuario.first_name,
            "sobrenome": funcionario.usuario.last_name,
            "email": funcionario.usuario.email,
            "cargo": funcionario.cargo,
            "telefone": funcionario.usuario.telefone,
        },
    })


@seller_only
def equipe_desativar(request, pk):
    cliente = get_cliente(request)
    if not cliente:
        return HttpResponseForbidden()

    funcionario = get_object_or_404(Funcionario, pk=pk, cliente=cliente)

    if request.method == "POST":
        usuario = funcionario.usuario
        if usuario.is_active:
            usuario.is_active = False
            usuario.save(update_fields=["is_active"])
            funcionario.soft_delete()
            messages.success(request, f"Funcionário {usuario.get_full_name()} desativado.")
        else:
            usuario.is_active = True
            usuario.save(update_fields=["is_active"])
            funcionario.restore()
            messages.success(request, f"Funcionário {usuario.get_full_name()} reativado.")

    return redirect("portal:equipe_listar")
