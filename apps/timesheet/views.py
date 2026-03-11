from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required

from .models import RegistroHoras


@consultor_required
def listar(request):
    """Lista registros de horas do consultor logado."""
    if request.user.is_gestor:
        qs = RegistroHoras.objects.all()
    else:
        qs = RegistroHoras.objects.filter(consultor=request.user)

    # Filtros
    cliente_id = request.GET.get("cliente")
    categoria = request.GET.get("categoria")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    if categoria:
        qs = qs.filter(categoria=categoria)
    if data_inicio:
        qs = qs.filter(data__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data__lte=data_fim)

    qs = qs.select_related("cliente", "consultor")

    # Totais
    total_minutos = sum(r.duracao_minutos for r in qs)
    total_horas = total_minutos // 60
    total_min = total_minutos % 60

    # Clientes para filtro
    if request.user.is_gestor:
        clientes = Cliente.objects.filter(status="ativo")
    else:
        clientes = Cliente.objects.filter(consultor=request.user, status="ativo")

    context = {
        "registros": qs[:100],
        "total_horas": total_horas,
        "total_min": total_min,
        "total_minutos": total_minutos,
        "clientes": clientes,
        "categorias": RegistroHoras.Categoria.choices,
        "filtros": {
            "cliente": cliente_id or "",
            "categoria": categoria or "",
            "data_inicio": data_inicio or "",
            "data_fim": data_fim or "",
        },
    }
    return render(request, "timesheet/listar.html", context)


@consultor_required
def criar(request):
    """Cria novo registro de horas."""
    if request.user.is_gestor:
        clientes = Cliente.objects.filter(status="ativo")
    else:
        clientes = Cliente.objects.filter(consultor=request.user, status="ativo")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        data = request.POST.get("data")
        hora_inicio = request.POST.get("hora_inicio")
        hora_fim = request.POST.get("hora_fim")
        categoria = request.POST.get("categoria")
        descricao = request.POST.get("descricao", "").strip()

        if not all([cliente_id, data, hora_inicio, hora_fim, categoria]):
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return render(request, "timesheet/form.html", {
                "clientes": clientes,
                "categorias": RegistroHoras.Categoria.choices,
                "dados": request.POST,
                "form_title": "Novo Registro",
            })

        cliente = get_object_or_404(Cliente, pk=cliente_id)

        RegistroHoras.objects.create(
            consultor=request.user,
            cliente=cliente,
            data=data,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            categoria=categoria,
            descricao=descricao,
        )
        messages.success(request, "Registro de horas salvo.")
        return redirect("timesheet:listar")

    return render(request, "timesheet/form.html", {
        "clientes": clientes,
        "categorias": RegistroHoras.Categoria.choices,
        "dados": {"data": timezone.localdate().isoformat()},
        "form_title": "Novo Registro",
    })


@consultor_required
def editar(request, pk):
    """Edita registro existente."""
    if request.user.is_gestor:
        registro = get_object_or_404(RegistroHoras, pk=pk)
        clientes = Cliente.objects.filter(status="ativo")
    else:
        registro = get_object_or_404(RegistroHoras, pk=pk, consultor=request.user)
        clientes = Cliente.objects.filter(consultor=request.user, status="ativo")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        registro.cliente = get_object_or_404(Cliente, pk=cliente_id)
        registro.data = request.POST.get("data")
        registro.hora_inicio = request.POST.get("hora_inicio")
        registro.hora_fim = request.POST.get("hora_fim")
        registro.categoria = request.POST.get("categoria")
        registro.descricao = request.POST.get("descricao", "").strip()
        registro.save()

        messages.success(request, "Registro atualizado.")
        return redirect("timesheet:listar")

    return render(request, "timesheet/form.html", {
        "clientes": clientes,
        "categorias": RegistroHoras.Categoria.choices,
        "dados": {
            "cliente": str(registro.cliente_id),
            "data": registro.data.isoformat(),
            "hora_inicio": registro.hora_inicio.strftime("%H:%M"),
            "hora_fim": registro.hora_fim.strftime("%H:%M"),
            "categoria": registro.categoria,
            "descricao": registro.descricao,
        },
        "registro": registro,
        "form_title": "Editar Registro",
    })


@consultor_required
def excluir(request, pk):
    """Exclui registro de horas."""
    if request.user.is_gestor:
        registro = get_object_or_404(RegistroHoras, pk=pk)
    else:
        registro = get_object_or_404(RegistroHoras, pk=pk, consultor=request.user)

    if request.method == "POST":
        registro.delete()
        messages.success(request, "Registro excluído.")

    return redirect("timesheet:listar")


@consultor_required
def resumo(request):
    """Resumo de horas por cliente e categoria."""
    if request.user.is_gestor:
        qs = RegistroHoras.objects.all()
    else:
        qs = RegistroHoras.objects.filter(consultor=request.user)

    # Período padrão: mês atual
    hoje = timezone.localdate()
    inicio_mes = hoje.replace(day=1)
    data_inicio = request.GET.get("data_inicio", inicio_mes.isoformat())
    data_fim = request.GET.get("data_fim", hoje.isoformat())

    qs = qs.filter(data__gte=data_inicio, data__lte=data_fim).select_related("cliente")

    # Agrupar por cliente
    por_cliente = {}
    por_categoria = {}
    for r in qs:
        nome = r.cliente.empresa
        mins = r.duracao_minutos
        por_cliente[nome] = por_cliente.get(nome, 0) + mins
        cat_label = r.get_categoria_display()
        por_categoria[cat_label] = por_categoria.get(cat_label, 0) + mins

    total_minutos = sum(por_cliente.values())

    # Formatar para Chart.js
    import json
    clientes_labels = list(por_cliente.keys())
    clientes_valores = [round(v / 60, 1) for v in por_cliente.values()]
    categorias_labels = list(por_categoria.keys())
    categorias_valores = [round(v / 60, 1) for v in por_categoria.values()]

    context = {
        "por_cliente": por_cliente,
        "por_categoria": por_categoria,
        "total_minutos": total_minutos,
        "total_horas": total_minutos // 60,
        "total_min": total_minutos % 60,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "clientes_labels_json": json.dumps(clientes_labels),
        "clientes_valores_json": json.dumps(clientes_valores),
        "categorias_labels_json": json.dumps(categorias_labels),
        "categorias_valores_json": json.dumps(categorias_valores),
    }
    return render(request, "timesheet/resumo.html", context)
