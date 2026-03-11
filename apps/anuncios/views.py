from django.contrib import messages
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required

from .models import (
    UploadCurvaABC, ItemCurvaABC,
    UploadMetricas, ItemMetrica,
    AnuncioAtualizar,
)
from .utils import parse_curva_abc, parse_metricas, parse_atualizacoes


# ─── Curva ABC ──────────────────────────────────────────

@consultor_required
def curva_abc(request, cliente_pk):
    """Lista uploads de Curva ABC + comparativo."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
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

    # Dados para gráfico (últimos 8 uploads)
    ultimos = list(uploads[:8])
    ultimos.reverse()
    chart_labels = [u.data_referencia.strftime("%d/%m") for u in ultimos]
    chart_faturamento = []
    for u in ultimos:
        total = sum(float(i.faturamento) for i in u.itens.all())
        chart_faturamento.append(round(total, 2))

    return render(request, "anuncios/curva_abc.html", {
        "cliente": cliente,
        "uploads": uploads,
        "upload_atual": upload_atual,
        "upload_anterior": upload_anterior,
        "comparativo": comparativo,
        "chart_labels": chart_labels,
        "chart_faturamento": chart_faturamento,
    })


@consultor_required
def curva_abc_upload(request, cliente_pk):
    """Upload de planilha de Curva ABC."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        periodo = request.POST.get("periodo")
        data_ref = request.POST.get("data_referencia")

        if not arquivo or not periodo or not data_ref:
            messages.error(request, "Preencha todos os campos.")
            return redirect("anuncios:curva_abc_upload", cliente_pk=cliente_pk)

        upload = UploadCurvaABC.objects.create(
            cliente=cliente,
            uploaded_by=request.user,
            periodo=periodo,
            data_referencia=data_ref,
            arquivo=arquivo,
        )

        try:
            arquivo.seek(0)
            itens = parse_curva_abc(arquivo)
            objs = [ItemCurvaABC(upload=upload, **item_data) for item_data in itens]
            ItemCurvaABC.objects.bulk_create(objs)
            messages.success(request, f"Curva ABC importada: {len(objs)} anúncios.")
        except Exception as e:
            upload.delete()
            messages.error(request, f"Erro ao processar planilha: {e}")
            return redirect("anuncios:curva_abc_upload", cliente_pk=cliente_pk)

        return redirect("anuncios:curva_abc", cliente_pk=cliente_pk)

    return render(request, "anuncios/upload.html", {
        "cliente": cliente,
        "tipo": "Curva ABC",
        "periodo_choices": UploadCurvaABC.Periodo.choices,
        "action_url": "anuncios:curva_abc_upload",
        "back_url": "anuncios:curva_abc",
    })


# ─── Métricas ───────────────────────────────────────────

@consultor_required
def metricas(request, cliente_pk):
    """Lista uploads de Métricas + comparativo."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
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
    chart_visitas = []
    chart_vendas = []
    for u in ultimos:
        chart_visitas.append(sum(i.visitas for i in u.itens.all()))
        chart_vendas.append(sum(i.vendas_30d for i in u.itens.all()))

    return render(request, "anuncios/metricas.html", {
        "cliente": cliente,
        "uploads": uploads,
        "upload_atual": upload_atual,
        "upload_anterior": upload_anterior,
        "comparativo": comparativo,
        "chart_labels": chart_labels,
        "chart_visitas": chart_visitas,
        "chart_vendas": chart_vendas,
    })


@consultor_required
def metricas_upload(request, cliente_pk):
    """Upload de planilha de Métricas."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        periodo = request.POST.get("periodo")
        data_ref = request.POST.get("data_referencia")

        if not arquivo or not periodo or not data_ref:
            messages.error(request, "Preencha todos os campos.")
            return redirect("anuncios:metricas_upload", cliente_pk=cliente_pk)

        upload = UploadMetricas.objects.create(
            cliente=cliente,
            uploaded_by=request.user,
            periodo=periodo,
            data_referencia=data_ref,
            arquivo=arquivo,
        )

        try:
            arquivo.seek(0)
            itens = parse_metricas(arquivo)
            objs = [ItemMetrica(upload=upload, **item_data) for item_data in itens]
            ItemMetrica.objects.bulk_create(objs)
            messages.success(request, f"Métricas importadas: {len(objs)} anúncios.")
        except Exception as e:
            upload.delete()
            messages.error(request, f"Erro ao processar planilha: {e}")
            return redirect("anuncios:metricas_upload", cliente_pk=cliente_pk)

        return redirect("anuncios:metricas", cliente_pk=cliente_pk)

    return render(request, "anuncios/upload.html", {
        "cliente": cliente,
        "tipo": "Métricas",
        "periodo_choices": UploadMetricas.Periodo.choices,
        "action_url": "anuncios:metricas_upload",
        "back_url": "anuncios:metricas",
    })


# ─── Atualizações ───────────────────────────────────────

@consultor_required
def atualizacoes(request, cliente_pk):
    """Lista anúncios que precisam de atualização."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    filtro = request.GET.get("filtro", "pendentes")
    anuncios = AnuncioAtualizar.objects.filter(cliente=cliente)

    if filtro == "pendentes":
        anuncios = anuncios.filter(
            models.Q(precisa_foto=True, foto_feito=False) |
            models.Q(precisa_video=True, video_feito=False)
        )
    elif filtro == "concluidos":
        anuncios = anuncios.exclude(
            models.Q(precisa_foto=True, foto_feito=False) |
            models.Q(precisa_video=True, video_feito=False)
        )

    total = AnuncioAtualizar.objects.filter(cliente=cliente).count()
    feitos = AnuncioAtualizar.objects.filter(cliente=cliente).exclude(
        models.Q(precisa_foto=True, foto_feito=False) |
        models.Q(precisa_video=True, video_feito=False)
    ).count()

    return render(request, "anuncios/atualizacoes.html", {
        "cliente": cliente,
        "anuncios": anuncios,
        "filtro": filtro,
        "total": total,
        "feitos": feitos,
        "pendentes_count": total - feitos,
    })


@consultor_required
def atualizacoes_upload(request, cliente_pk):
    """Upload de planilha de anúncios para atualizar."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            messages.error(request, "Selecione um arquivo.")
            return redirect("anuncios:atualizacoes_upload", cliente_pk=cliente_pk)

        try:
            itens = parse_atualizacoes(arquivo)
            count = 0
            for item_data in itens:
                AnuncioAtualizar.objects.update_or_create(
                    cliente=cliente,
                    mlb=item_data["mlb"],
                    defaults={
                        "criado_por": request.user,
                        "titulo": item_data["titulo"],
                        "precisa_foto": item_data["precisa_foto"],
                        "precisa_video": item_data["precisa_video"],
                    },
                )
                count += 1
            messages.success(request, f"{count} anúncios importados para atualização.")
        except Exception as e:
            messages.error(request, f"Erro ao processar planilha: {e}")
            return redirect("anuncios:atualizacoes_upload", cliente_pk=cliente_pk)

        return redirect("anuncios:atualizacoes", cliente_pk=cliente_pk)

    return render(request, "anuncios/upload_atualizacoes.html", {
        "cliente": cliente,
    })
