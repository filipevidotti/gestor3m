import json as json_mod
import logging

import requests
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required, gestor_required

from .models import Configuracao, GrupoWhatsApp, MensagemGrupo

logger = logging.getLogger(__name__)


# ── Ícones e descrições por categoria ──────────────────────────────
CATEGORIA_META = {
    "uazapi": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>',
        "cor": "green",
        "descricao": "UAZAPI — WhatsApp API para mensagens e gestão de grupos.",
    },
    "google": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
        "cor": "blue",
        "descricao": "Integração com Google Calendar para agendamentos automáticos.",
    },
    "evolution": {
        "icone": '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>',
        "cor": "green",
        "descricao": "Evolution API (WhatsApp) — Descontinuado, migrar para UAZAPI.",
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
    """Salva uma configuração individual."""
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
def configuracao_testar_categoria(request, categoria):
    """Testa a conexão de uma integração por categoria."""

    testers = {
        "uazapi": _testar_uazapi,
        "google": _testar_google,
        "brevo": _testar_brevo,
        "asaas": _testar_asaas,
        "autentique": _testar_autentique,
        "ia": _testar_ia,
        "evolution": _testar_uazapi,  # fallback
    }

    tester = testers.get(categoria)
    if not tester:
        messages.warning(request, f"Teste não disponível para '{categoria}'.")
        return redirect("core:configuracoes")

    try:
        sucesso, mensagem = tester()
        if sucesso:
            messages.success(request, mensagem)
        else:
            messages.error(request, mensagem)
    except Exception as e:
        logger.exception("Erro ao testar %s", categoria)
        messages.error(request, f"Erro ao testar: {e}")

    return redirect("core:configuracoes")


# ── Funções de teste por categoria ─────────────────────────────────


def _testar_uazapi():
    url = Configuracao.get("UAZAPI_URL")
    token = Configuracao.get("UAZAPI_TOKEN")
    if not url or not token:
        return False, "UAZAPI_URL e UAZAPI_TOKEN não configurados."
    try:
        # /status é público (health check) — testa conectividade
        resp = requests.get(
            f"{url.rstrip('/')}/status",
            headers={"token": token, "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json() if resp.content else {}
            status_info = data.get("status", {})
            instance = status_info.get("checked_instance", {})
            conn = instance.get("connection_status", "unknown")
            name = instance.get("name", "?")
            server = status_info.get("server_status", "?")
            return True, f"UAZAPI OK! Instância: {name}, Conexão: {conn}, Servidor: {server}"
        # Testa endpoint autenticado para validar token
        resp2 = requests.get(
            f"{url.rstrip('/')}/contacts",
            headers={"token": token},
            timeout=10,
        )
        if resp2.status_code == 401:
            return False, f"Servidor acessível mas token inválido. Verifique UAZAPI_TOKEN no painel admin da UAZAPI."
        return False, f"UAZAPI retornou status {resp.status_code}: {resp.text[:200]}"
    except requests.ConnectionError:
        return False, "Não foi possível conectar à UAZAPI. Verifique a URL."
    except Exception as e:
        return False, f"Erro: {e}"


def _testar_google():
    client_id = Configuracao.get("GOOGLE_CLIENT_ID")
    client_secret = Configuracao.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return False, "GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET não configurados."
    if len(client_id) > 10 and len(client_secret) > 10:
        return True, "Google Calendar configurado (credenciais presentes). Conecte via Agenda > Config."
    return False, "Credenciais parecem inválidas (muito curtas)."


def _testar_brevo():
    api_key = Configuracao.get("BREVO_API_KEY")
    if not api_key:
        return False, "BREVO_API_KEY não configurado."
    try:
        resp = requests.get(
            "https://api.brevo.com/v3/account",
            headers={"api-key": api_key, "Accept": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, f"Brevo conectado! Conta: {data.get('email', 'OK')}"
        return False, f"Brevo retornou status {resp.status_code}"
    except Exception as e:
        return False, f"Erro ao testar Brevo: {e}"


def _testar_asaas():
    api_key = Configuracao.get("ASAAS_API_KEY")
    env = Configuracao.get("ASAAS_ENVIRONMENT", "sandbox")
    if not api_key:
        return False, "ASAAS_API_KEY não configurado."
    base = "https://api.asaas.com/v3" if env == "production" else "https://sandbox.asaas.com/api/v3"
    try:
        resp = requests.get(
            f"{base}/finance/balance",
            headers={"access_token": api_key, "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, f"Asaas conectado! Saldo: R$ {data.get('balance', '?')}"
        return False, f"Asaas retornou status {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, f"Erro ao testar Asaas: {e}"


def _testar_autentique():
    token = Configuracao.get("AUTENTIQUE_API_TOKEN")
    if not token:
        return False, "AUTENTIQUE_API_TOKEN não configurado."
    try:
        resp = requests.post(
            "https://api.autentique.com.br/v2/graphql",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"query": "{ me { id email } }"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            me = data.get("data", {}).get("me", {})
            return True, f"Autentique conectado! E-mail: {me.get('email', 'OK')}"
        return False, f"Autentique retornou status {resp.status_code}"
    except Exception as e:
        return False, f"Erro ao testar Autentique: {e}"


def _testar_ia():
    provider = Configuracao.get("IA_PROVIDER", "openai")
    api_key = Configuracao.get("OPENAI_API_KEY")
    if not api_key:
        return False, "OPENAI_API_KEY não configurado."
    try:
        if provider == "openai":
            resp = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                return True, "OpenAI conectado! API Key válida."
            return False, f"OpenAI retornou status {resp.status_code}"
        else:
            # Anthropic
            resp = requests.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                return True, "Anthropic conectado! API Key válida."
            return False, f"Anthropic retornou status {resp.status_code}"
    except Exception as e:
        return False, f"Erro ao testar IA: {e}"


# ── WhatsApp Groups ──────────────────────────────────────────────


@consultor_required
def grupos_whatsapp(request):
    """Lista de grupos WhatsApp com filtros."""
    from datetime import timedelta

    from django.db.models import OuterRef, Subquery

    # Subquery: última mensagem de cada grupo
    ultima_msg = MensagemGrupo.objects.filter(
        grupo=OuterRef("pk"),
    ).order_by("-enviado_em")

    grupos = (
        GrupoWhatsApp.objects.select_related("cliente")
        .annotate(
            ultima_msg_remetente=Subquery(ultima_msg.values("remetente_nome")[:1]),
            ultima_msg_enviado_por_nome=Subquery(
                ultima_msg.values("enviado_por__first_name")[:1]
            ),
            ultima_msg_origem=Subquery(ultima_msg.values("origem")[:1]),
        )
        .all()
    )

    busca = request.GET.get("busca", "").strip()
    if busca:
        grupos = grupos.filter(nome__icontains=busca)

    vinculado = request.GET.get("vinculado")
    if vinculado == "sim":
        grupos = grupos.filter(cliente__isnull=False)
    elif vinculado == "nao":
        grupos = grupos.filter(cliente__isnull=True)

    status = request.GET.get("status")
    if status == "ativo":
        grupos = grupos.filter(is_active=True)
    elif status == "inativo":
        grupos = grupos.filter(is_active=False)

    interacao = request.GET.get("interacao")
    if interacao == "sem_interacao":
        grupos = grupos.filter(ultima_interacao__isnull=True)
    elif interacao == "7dias":
        limite = timezone.now() - timedelta(days=7)
        grupos = grupos.filter(
            models.Q(ultima_interacao__isnull=True) | models.Q(ultima_interacao__lt=limite)
        )
    elif interacao == "30dias":
        limite = timezone.now() - timedelta(days=30)
        grupos = grupos.filter(
            models.Q(ultima_interacao__isnull=True) | models.Q(ultima_interacao__lt=limite)
        )

    clientes = Cliente.objects.filter(is_active=True).order_by("empresa")

    return render(request, "core/grupos_whatsapp.html", {
        "grupos": grupos,
        "clientes": clientes,
        "busca": busca,
        "filtro_vinculado": vinculado,
        "filtro_status": status,
        "filtro_interacao": interacao,
    })


@gestor_required
@require_POST
def grupos_sincronizar(request):
    """Sincroniza grupos do WhatsApp via UAZAPI."""
    from apps.core.services.uazapi import UazapiClient

    client = UazapiClient()
    if not client.base_url or not client.token:
        messages.error(request, "UAZAPI não configurada. Vá em Configurações e preencha UAZAPI_URL e UAZAPI_TOKEN.")
        return redirect("core:grupos_whatsapp")

    try:
        grupos_api = client.listar_grupos()
    except Exception as e:
        messages.error(request, f"Erro ao conectar com UAZAPI: {e}")
        return redirect("core:grupos_whatsapp")

    if not grupos_api:
        messages.warning(request, "Nenhum grupo encontrado na UAZAPI.")
        return redirect("core:grupos_whatsapp")

    criados = 0
    atualizados = 0
    agora = timezone.now()

    for g in grupos_api:
        # Campos UAZAPI: JID, Name, Topic, ParticipantCount, Participants
        gid = g.get("JID") or g.get("jid") or g.get("id") or g.get("groupId", "")
        nome = g.get("Name") or g.get("subject") or g.get("name", "Sem nome")
        desc = g.get("Topic") or g.get("desc") or g.get("description", "")
        foto = g.get("profilePicUrl") or g.get("imgUrl", "")
        size = g.get("ParticipantCount") or g.get("size", 0)
        participants = g.get("Participants") or g.get("participants")
        if isinstance(participants, list) and not size:
            size = len(participants)
        if isinstance(size, list):
            size = len(size)

        if not gid:
            continue

        grupo, created = GrupoWhatsApp.all_objects.update_or_create(
            group_id=gid,
            defaults={
                "nome": nome[:300],
                "descricao": desc,
                "foto_url": foto[:200] if foto else "",
                "participantes_count": size,
                "sincronizado_em": agora,
            },
        )
        if created:
            criados += 1
        else:
            atualizados += 1

    messages.success(request, f"Sincronização concluída! {criados} novos, {atualizados} atualizados.")
    return redirect("core:grupos_whatsapp")


@consultor_required
@require_POST
def grupo_vincular(request, pk):
    """Vincula um grupo a um cliente."""
    grupo = get_object_or_404(GrupoWhatsApp, pk=pk)
    cliente_id = request.POST.get("cliente_id")

    if cliente_id:
        grupo.cliente_id = int(cliente_id)
    else:
        grupo.cliente = None
    grupo.save(update_fields=["cliente", "updated_at"])

    nome_cliente = grupo.cliente.empresa if grupo.cliente else "nenhum"
    messages.success(request, f"Grupo '{grupo.nome}' vinculado a: {nome_cliente}")
    return redirect("core:grupos_whatsapp")


@consultor_required
@require_POST
def grupo_toggle_ativo(request, pk):
    """Ativa/desativa um grupo."""
    grupo = get_object_or_404(GrupoWhatsApp.all_objects, pk=pk)
    if grupo.is_active:
        grupo.soft_delete()
        messages.success(request, f"Grupo '{grupo.nome}' desativado.")
    else:
        grupo.restore()
        messages.success(request, f"Grupo '{grupo.nome}' ativado.")
    return redirect("core:grupos_whatsapp")


@consultor_required
def grupo_detalhe(request, pk):
    """Detalhe do grupo com histórico de mensagens e envio."""
    grupo = get_object_or_404(GrupoWhatsApp.objects.select_related("cliente"), pk=pk)
    mensagens_list = grupo.mensagens.select_related("enviado_por").order_by("-enviado_em")[:50]

    return render(request, "core/grupo_detalhe.html", {
        "grupo": grupo,
        "mensagens": mensagens_list,
    })


@consultor_required
@require_POST
def grupo_enviar_mensagem(request, pk):
    """Envia mensagem para um grupo."""
    from apps.core.services.uazapi import UazapiClient

    grupo = get_object_or_404(GrupoWhatsApp, pk=pk)
    texto = request.POST.get("texto", "").strip()

    if not texto:
        messages.error(request, "Mensagem não pode ser vazia.")
        return redirect("core:grupo_detalhe", pk=pk)

    client = UazapiClient()
    if not client.base_url or not client.token:
        messages.error(request, "UAZAPI não configurada.")
        return redirect("core:grupo_detalhe", pk=pk)

    sucesso = client.enviar_mensagem_grupo(grupo.group_id, texto)
    agora = timezone.now()

    MensagemGrupo.objects.create(
        grupo=grupo,
        texto=texto,
        enviado_por=request.user,
        sucesso=sucesso,
        erro="" if sucesso else "Falha no envio via UAZAPI",
    )

    if sucesso:
        grupo.ultima_mensagem_enviada = agora
        grupo.ultima_interacao = agora
        grupo.save(update_fields=["ultima_mensagem_enviada", "ultima_interacao", "updated_at"])
        messages.success(request, "Mensagem enviada com sucesso!")
    else:
        messages.error(request, "Erro ao enviar mensagem. Verifique a conexão com UAZAPI.")

    return redirect("core:grupo_detalhe", pk=pk)


@consultor_required
@require_POST
def grupos_enviar_bulk(request):
    """Envia mensagem para múltiplos grupos selecionados."""
    from apps.core.services.uazapi import UazapiClient

    grupo_ids = request.POST.getlist("grupo_ids")
    texto = request.POST.get("texto", "").strip()

    if not texto:
        messages.error(request, "Mensagem não pode ser vazia.")
        return redirect("core:grupos_whatsapp")

    if not grupo_ids:
        messages.error(request, "Selecione pelo menos um grupo.")
        return redirect("core:grupos_whatsapp")

    client = UazapiClient()
    if not client.base_url or not client.token:
        messages.error(request, "UAZAPI não configurada.")
        return redirect("core:grupos_whatsapp")

    enviados = 0
    erros = 0
    agora = timezone.now()

    grupos = GrupoWhatsApp.objects.filter(pk__in=grupo_ids, is_active=True)
    for grupo in grupos:
        sucesso = client.enviar_mensagem_grupo(grupo.group_id, texto)

        MensagemGrupo.objects.create(
            grupo=grupo,
            texto=texto,
            enviado_por=request.user,
            sucesso=sucesso,
            erro="" if sucesso else "Falha no envio via UAZAPI",
        )

        if sucesso:
            grupo.ultima_mensagem_enviada = agora
            grupo.ultima_interacao = agora
            grupo.save(update_fields=["ultima_mensagem_enviada", "ultima_interacao", "updated_at"])
            enviados += 1
        else:
            erros += 1

    if enviados:
        messages.success(request, f"Mensagem enviada para {enviados} grupo(s)!")
    if erros:
        messages.warning(request, f"Falha ao enviar para {erros} grupo(s).")

    return redirect("core:grupos_whatsapp")


# ── Webhook UAZAPI ──────────────────────────────────────────────


@csrf_exempt
@require_POST
def uazapi_webhook(request):
    """Recebe eventos da UAZAPI (mensagens recebidas, status, etc).

    Configura no painel UAZAPI:
    URL: https://gestor.3mconsultoria.com.br/webhook/uazapi/
    """
    try:
        body = request.body.decode("utf-8", errors="replace")
        data = json_mod.loads(body)
    except (json_mod.JSONDecodeError, ValueError):
        logger.warning("UAZAPI webhook: JSON inválido: %s", request.body[:500])
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    # Log completo do payload para debug
    logger.info("UAZAPI webhook RAW: %s", body[:2000])

    event = data.get("event", "")

    # UAZAPI pode enviar o evento em diferentes formatos
    if event:
        logger.info("UAZAPI webhook evento: %s", event)
        if "message" in event.lower():
            _processar_mensagem_webhook(data)
        elif "group" in event.lower():
            _processar_grupo_update_webhook(data)
    else:
        # Sem campo 'event' — tentar detectar pelo conteúdo do payload
        logger.info("UAZAPI webhook sem campo 'event', tentando detectar tipo")
        if _parece_mensagem(data):
            _processar_mensagem_webhook(data)
        elif _parece_grupo(data):
            _processar_grupo_update_webhook(data)
        else:
            logger.info("UAZAPI webhook payload não reconhecido (keys: %s)", list(data.keys())[:10])

    return JsonResponse({"status": "ok"})


def _parece_mensagem(data):
    """Detecta se o payload parece ser uma mensagem."""
    # Verifica estruturas comuns de mensagem da UAZAPI
    if "key" in data and "remoteJid" in data.get("key", {}):
        return True
    if "message" in data or "messages" in data:
        return True
    if "data" in data:
        inner = data["data"]
        if isinstance(inner, dict) and "key" in inner:
            return True
        if isinstance(inner, list) and inner and "key" in inner[0]:
            return True
    # Checa campos comuns: from, chatId, remoteJid
    if any(k in data for k in ("remoteJid", "from", "chatId", "pushName")):
        return True
    return False


def _parece_grupo(data):
    """Detecta se o payload parece ser atualização de grupo."""
    if any(k in data for k in ("JID", "jid", "groupJid")):
        return True
    if "data" in data:
        inner = data["data"]
        if isinstance(inner, dict) and any(k in inner for k in ("JID", "jid", "groupJid")):
            return True
    return False


def _extrair_jid_mensagem(data):
    """Extrai o JID do grupo/chat de qualquer formato de payload UAZAPI."""
    # Formato: {data: {key: {remoteJid: ...}}}
    msg_data = data.get("data", data)
    if isinstance(msg_data, list):
        msg_data = msg_data[0] if msg_data else {}

    # Tenta vários caminhos conhecidos
    jid = (
        msg_data.get("key", {}).get("remoteJid", "")
        or msg_data.get("remoteJid", "")
        or msg_data.get("from", "")
        or msg_data.get("chatId", "")
        or data.get("key", {}).get("remoteJid", "")
        or data.get("remoteJid", "")
        or data.get("from", "")
        or data.get("chatId", "")
    )
    return jid


def _extrair_texto_mensagem(data):
    """Extrai o texto da mensagem do payload UAZAPI."""
    msg_data = data.get("data", data)
    if isinstance(msg_data, list):
        msg_data = msg_data[0] if msg_data else {}

    # Tenta vários caminhos
    msg_obj = msg_data.get("message", data.get("message", {}))
    if isinstance(msg_obj, dict):
        texto = (
            msg_obj.get("conversation", "")
            or msg_obj.get("extendedTextMessage", {}).get("text", "")
            or msg_obj.get("text", "")
            or msg_obj.get("caption", "")
            or msg_obj.get("imageMessage", {}).get("caption", "")
            or msg_obj.get("videoMessage", {}).get("caption", "")
        )
        if texto:
            return texto

    # Texto direto no payload
    texto = msg_data.get("text", "") or msg_data.get("body", "") or data.get("text", "")
    return texto


def _extrair_remetente(data):
    """Extrai nome/telefone do remetente."""
    msg_data = data.get("data", data)
    if isinstance(msg_data, list):
        msg_data = msg_data[0] if msg_data else {}

    push_name = (
        msg_data.get("pushName", "")
        or data.get("pushName", "")
        or msg_data.get("senderName", "")
    )

    participant = (
        msg_data.get("key", {}).get("participant", "")
        or data.get("key", {}).get("participant", "")
        or msg_data.get("participant", "")
    )

    return push_name, participant


def _processar_mensagem_webhook(data):
    """Processa mensagem recebida — atualiza ultima_interacao e salva mensagem."""
    try:
        remote_jid = _extrair_jid_mensagem(data)
        texto = _extrair_texto_mensagem(data)
        push_name, participant = _extrair_remetente(data)

        logger.info(
            "UAZAPI msg: jid=%s, push=%s, participant=%s, texto=%s",
            remote_jid, push_name, participant, texto[:100] if texto else "(sem texto)",
        )

        # Só processa mensagens de grupo (@g.us)
        if "@g.us" not in remote_jid:
            return

        agora = timezone.now()

        # Atualiza ultima_interacao do grupo
        updated = GrupoWhatsApp.all_objects.filter(group_id=remote_jid).update(
            ultima_interacao=agora,
        )

        if updated:
            logger.info("Interação atualizada para grupo %s", remote_jid)

            # Salva mensagem recebida no histórico
            grupo = GrupoWhatsApp.all_objects.filter(group_id=remote_jid).first()
            if grupo:
                remetente_info = push_name or participant or "Desconhecido"
                MensagemGrupo.objects.create(
                    grupo=grupo,
                    texto=texto[:5000] if texto else f"[Mensagem de {remetente_info}]",
                    enviado_por=None,  # Mensagem externa, não do sistema
                    sucesso=True,
                    erro="",
                    remetente_nome=remetente_info[:200],
                    remetente_telefone=participant.split("@")[0] if participant else "",
                    origem="webhook",
                )
        else:
            logger.info("Grupo %s não encontrado no banco", remote_jid)

    except Exception:
        logger.exception("Erro ao processar webhook de mensagem")


def _processar_grupo_update_webhook(data):
    """Processa atualização de grupo — atualiza nome/participantes."""
    try:
        group_data = data.get("data", data)
        if isinstance(group_data, list):
            group_data = group_data[0] if group_data else {}

        gid = (
            group_data.get("JID") or group_data.get("jid")
            or group_data.get("groupJid") or group_data.get("id", "")
            or data.get("JID") or data.get("jid") or ""
        )
        if not gid:
            return

        updates = {}
        nome = group_data.get("Name") or group_data.get("subject") or group_data.get("name")
        if nome:
            updates["nome"] = nome[:300]

        size = group_data.get("ParticipantCount") or group_data.get("size") or group_data.get("participantCount")
        if size and isinstance(size, int):
            updates["participantes_count"] = size

        if updates:
            GrupoWhatsApp.all_objects.filter(group_id=gid).update(**updates)
            logger.info("Grupo %s atualizado via webhook", gid)

    except Exception:
        logger.exception("Erro ao processar webhook de grupo")
