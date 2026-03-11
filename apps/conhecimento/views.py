from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from apps.core.decorators import consultor_required

from .models import Artigo, CategoriaConhecimento


@consultor_required
def listar(request):
    """Lista artigos da base de conhecimento."""
    qs = Artigo.objects.select_related("categoria", "autor")

    # Filtrar por visibilidade
    if request.user.is_consultor and not request.user.is_gestor:
        qs = qs.filter(visibilidade__in=["todos", "consultores"])

    # Busca
    busca = request.GET.get("q", "").strip()
    if busca:
        qs = qs.filter(Q(titulo__icontains=busca) | Q(conteudo__icontains=busca))

    # Filtro categoria
    cat_id = request.GET.get("categoria")
    if cat_id:
        qs = qs.filter(categoria_id=cat_id)

    categorias = CategoriaConhecimento.objects.all()
    destaques = qs.filter(destaque=True)[:3]

    return render(request, "conhecimento/listar.html", {
        "artigos": qs[:50],
        "categorias": categorias,
        "destaques": destaques,
        "busca": busca,
        "cat_filtro": cat_id,
    })


@consultor_required
def detalhe(request, slug):
    """Detalhe de um artigo."""
    artigo = get_object_or_404(
        Artigo.objects.select_related("categoria", "autor"), slug=slug
    )
    artigo.visualizacoes += 1
    artigo.save(update_fields=["visualizacoes"])

    return render(request, "conhecimento/detalhe.html", {"artigo": artigo})


@consultor_required
def criar(request):
    """Criar novo artigo (gestor only)."""
    if not request.user.is_gestor:
        messages.error(request, "Apenas gestores podem criar artigos.")
        return redirect("conhecimento:listar")

    categorias = CategoriaConhecimento.objects.all()

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        conteudo = request.POST.get("conteudo", "").strip()
        resumo = request.POST.get("resumo", "").strip()
        categoria_id = request.POST.get("categoria")
        visibilidade = request.POST.get("visibilidade", "todos")
        destaque = request.POST.get("destaque") == "on"

        if not titulo or not conteudo:
            messages.error(request, "Título e conteúdo são obrigatórios.")
            return render(request, "conhecimento/form.html", {
                "categorias": categorias,
                "dados": request.POST,
                "form_title": "Novo Artigo",
            })

        slug = slugify(titulo)
        base_slug = slug
        counter = 1
        while Artigo.all_objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        Artigo.objects.create(
            titulo=titulo,
            slug=slug,
            conteudo=conteudo,
            resumo=resumo,
            categoria_id=categoria_id or None,
            visibilidade=visibilidade,
            destaque=destaque,
            autor=request.user,
        )
        messages.success(request, "Artigo publicado.")
        return redirect("conhecimento:listar")

    return render(request, "conhecimento/form.html", {
        "categorias": categorias,
        "dados": {},
        "form_title": "Novo Artigo",
    })


@consultor_required
def editar(request, slug):
    """Editar artigo (gestor only)."""
    if not request.user.is_gestor:
        messages.error(request, "Apenas gestores podem editar artigos.")
        return redirect("conhecimento:listar")

    artigo = get_object_or_404(Artigo, slug=slug)
    categorias = CategoriaConhecimento.objects.all()

    if request.method == "POST":
        artigo.titulo = request.POST.get("titulo", "").strip()
        artigo.conteudo = request.POST.get("conteudo", "").strip()
        artigo.resumo = request.POST.get("resumo", "").strip()
        artigo.categoria_id = request.POST.get("categoria") or None
        artigo.visibilidade = request.POST.get("visibilidade", "todos")
        artigo.destaque = request.POST.get("destaque") == "on"
        artigo.save()

        messages.success(request, "Artigo atualizado.")
        return redirect("conhecimento:detalhe", slug=artigo.slug)

    return render(request, "conhecimento/form.html", {
        "categorias": categorias,
        "artigo": artigo,
        "dados": {
            "titulo": artigo.titulo,
            "conteudo": artigo.conteudo,
            "resumo": artigo.resumo,
            "categoria": str(artigo.categoria_id or ""),
            "visibilidade": artigo.visibilidade,
            "destaque": artigo.destaque,
        },
        "form_title": "Editar Artigo",
    })
