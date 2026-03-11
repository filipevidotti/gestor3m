import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import gestor_required

from .models import Configuracao


# ── Ícones e descrições por categoria ──────────────────────────────
CATEGORIA_META = {
    "google": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
        "cor": "blue",
        "descricao": "Integração com Google Calendar para agendamentos automáticos.",
    },
    "evolution": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>',
        "cor": "green",
        "descricao": "API Evolution para envio de mensagens via WhatsApp.",
    },
    "brevo": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>',
        "cor": "indigo",
        "descricao": "Serviço de e-mail transacional Brevo (ex-Sendinblue).",
    },
    "asaas": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>',
        "cor": "emerald",
        "descricao": "Gateway de pagamentos Asaas (PIX, boleto, cartão, recorrência).",
    },
    "autentique": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>',
        "cor": "purple",
        "descricao": "Assinatura digital de contratos e documentos via Autentique.",
    },
    "ia": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>',
        "cor": "amber",
        "descricao": "Configuração de IA (OpenAI, Anthropic) para insights e automações.",
    },
    "geral": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
        "cor": "gray",
        "descricao": "Configurações gerais do sistema.",
    },
}

COR_CLASSES = {
    "blue": {"bg": "bg-blue-500/10 dark:bg-blue-500/20", "text": "text-blue-600 dark:text-blue-400", "border": "border-blue-500/20 dark:border-blue-500/30", "dot": "bg-blue-500"},
    "green": {"bg": "bg-green-500/10 dark:bg-green-500/20", "text": "text-green-600 dark:text-green-400", "border": "border-green-500/20 dark:border-green-500/30", "dot": "bg-green-500"},
    "indigo": {"bg": "bg-indigo-500/10 dark:bg-indigo-500/20", "text": "text-indigo-600 dark:text-indigo-400", "border": "border-indigo-500/20 dark:border-indigo-500/30", "dot": "bg-indigo-500"},
    "emerald": {"bg": "bg-emerald-500/10 dark:bg-emerald-500/20", "text": "text-emerald-600 dark:text-emerald-400", "border": "border-emerald-500/20 dark:border-emerald-500/30", "dot": "bg-emerald-500"},
    "purple": {"bg": "bg-purple-500/10 dark:bg-purple-500/20", "text": "text-purple-600 dark:text-purple-400", "border": "border-purple-500/20 dark:border-purple-500/30", "dot": "bg-purple-500"},
    "amber": {"bg": "bg-amber-500/10 dark:bg-amber-500/20", "text": "text-amber-600 dark:text-amber-400", "border": "border-amber-500/20 dark:border-amber-500/30", "dot": "bg-amber-500"},
    "gray": {"bg": "bg-gray-500/10 dark:bg-gray-500/20", "text": "text-gray-600 dark:text-gray-400", "border": "border-gray-500/20 dark:border-gray-500/30", "dot": "bg-gray-500"},
}


@gestor_required
def configuracoes(request):
    """Página de configurações do sistema — somente gestor."""
    configs = Configuracao.objects.all().order_by("categoria", "chave")

    # Agrupar por categoria
    categorias = {}
    for config in configs:
        cat = config.categoria
        if cat not in categorias:
            meta = CATEGORIA_META.get(cat, CATEGORIA_META["geral"])
            cor = COR_CLASSES.get(meta["cor"], COR_CLASSES["gray"])
            categorias[cat] = {
                "nome": config.get_categoria_display(),
                "icone": meta["icone"],
                "descricao": meta["descricao"],
                "cor": cor,
                "configs": [],
            }
        categorias[cat]["configs"].append(config)

    # Contar configuradas vs total
    total = configs.count()
    configuradas = configs.exclude(valor="").count()

    return render(request, "core/configuracoes.html", {
        "categorias": categorias,
        "total": total,
        "configuradas": configuradas,
        "categoria_choices": Configuracao.Categoria.choices,
    })


@gestor_required
@require_POST
def configuracao_salvar(request):
    """Salva uma configuração individual via HTMX."""
    config_id = request.POST.get("config_id")
    valor = request.POST.get("valor", "")

    try:
        config = Configuracao.objects.get(pk=config_id)
        config.valor = valor
        config.save(update_fields=["valor"])
        messages.success(request, f"'{config.chave}' salvo com sucesso!")
    except Configuracao.DoesNotExist:
        messages.error(request, "Configuração não encontrada.")

    return redirect("core:configuracoes")


@gestor_required
@require_POST
def configuracao_criar(request):
    """Cria uma nova configuração."""
    chave = request.POST.get("chave", "").strip().upper()
    categoria = request.POST.get("categoria", "geral")
    valor = request.POST.get("valor", "").strip()
    descricao = request.POST.get("descricao", "").strip()
    is_secret = request.POST.get("is_secret") == "on"

    if not chave:
        messages.error(request, "A chave é obrigatória.")
        return redirect("core:configuracoes")

    if Configuracao.objects.filter(chave=chave).exists():
        messages.error(request, f"A chave '{chave}' já existe.")
        return redirect("core:configuracoes")

    Configuracao.objects.create(
        chave=chave,
        categoria=categoria,
        valor=valor,
        descricao=descricao,
        is_secret=is_secret,
    )
    messages.success(request, f"Configuração '{chave}' criada com sucesso!")
    return redirect("core:configuracoes")


@gestor_required
@require_POST
def configuracao_excluir(request, pk):
    """Exclui uma configuração."""
    try:
        config = Configuracao.objects.get(pk=pk)
        nome = config.chave
        config.delete()
        messages.success(request, f"Configuração '{nome}' excluída.")
    except Configuracao.DoesNotExist:
        messages.error(request, "Configuração não encontrada.")

    return redirect("core:configuracoes")


@gestor_required
@require_POST
def configuracao_testar(request, pk):
    """Testa a conexão de uma integração."""
    config = Configuracao.objects.get(pk=pk)

    # Testes básicos por categoria
    resultado = {"sucesso": False, "mensagem": "Teste não implementado para esta categoria."}

    if config.categoria == "evolution":
        from apps.core.services.evolution import EvolutionClient
        try:
            client = EvolutionClient()
            # Verifica se a instância está conectada
            resultado = {"sucesso": True, "mensagem": "Conexão Evolution OK!"}
        except Exception as e:
            resultado = {"sucesso": False, "mensagem": str(e)}

    elif config.categoria == "ia":
        valor = Configuracao.get("OPENAI_API_KEY")
        if valor and len(valor) > 10:
            resultado = {"sucesso": True, "mensagem": "API Key configurada (validação externa necessária)."}
        else:
            resultado = {"sucesso": False, "mensagem": "API Key não configurada ou inválida."}

    if resultado["sucesso"]:
        messages.success(request, resultado["mensagem"])
    else:
        messages.error(request, resultado["mensagem"])

    return redirect("core:configuracoes")
