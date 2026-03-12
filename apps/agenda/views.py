import json
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required

from .google_calendar import (
    HAS_GOOGLE,
    buscar_eventos_ocupados,
    criar_evento,
    deletar_evento,
    get_flow,
    listar_eventos,
)
from .models import Agendamento, ConfiguracaoAgenda, HorarioTrabalho


# ---------------------------------------------------------------------------
# Views do consultor (autenticadas)
# ---------------------------------------------------------------------------


@consultor_required
def agenda_config(request):
    """Configuração da agenda do consultor."""
    config, created = ConfiguracaoAgenda.objects.get_or_create(
        consultor=request.user
    )

    if request.method == "POST":
        config.titulo = request.POST.get("titulo", "")
        config.descricao = request.POST.get("descricao", "")
        config.duracao_padrao = int(request.POST.get("duracao_padrao", 60))
        config.antecedencia_minima = int(request.POST.get("antecedencia_minima", 24))
        config.dias_visiveis = int(request.POST.get("dias_visiveis", 14))
        config.save()

        # Salvar horários de trabalho
        HorarioTrabalho.objects.filter(config=config).delete()
        for dia in range(7):
            ativo = request.POST.get(f"dia_{dia}_ativo")
            inicio = request.POST.get(f"dia_{dia}_inicio")
            fim = request.POST.get(f"dia_{dia}_fim")
            if ativo and inicio and fim:
                HorarioTrabalho.objects.create(
                    config=config,
                    dia_semana=dia,
                    hora_inicio=inicio,
                    hora_fim=fim,
                    ativo=True,
                )

        messages.success(request, "Configuração salva com sucesso!")
        return redirect("agenda:config")

    horarios = {h.dia_semana: h for h in config.horarios.filter(ativo=True)}
    google_conectado = bool(config.google_token)
    link_publico = request.build_absolute_uri(f"/agenda/c/{config.slug}/")

    return render(request, "agenda/config.html", {
        "config": config,
        "horarios": horarios,
        "dias_semana": HorarioTrabalho.DiaSemana.choices,
        "google_conectado": google_conectado,
        "link_publico": link_publico,
        "has_google": HAS_GOOGLE,
    })


@consultor_required
def agenda_visualizar(request):
    """Visualização da agenda do consultor com FullCalendar."""
    config = ConfiguracaoAgenda.objects.filter(consultor=request.user).first()
    return render(request, "agenda/visualizar.html", {
        "config": config,
    })


@consultor_required
def agenda_eventos_json(request):
    """API JSON para FullCalendar — retorna eventos do consultor."""
    start = request.GET.get("start", "")
    end = request.GET.get("end", "")

    qs = Agendamento.objects.filter(consultor=request.user)
    if start:
        qs = qs.filter(data_hora__gte=start)
    if end:
        qs = qs.filter(data_hora__lte=end)

    STATUS_COLORS = {
        "confirmado": "#3B82F6",    # blue
        "realizado": "#22C55E",     # green
        "cancelado": "#EF4444",     # red
        "nao_compareceu": "#F59E0B",  # amber
    }

    events = []
    for ag in qs.select_related("cliente"):
        fim = ag.data_hora + timedelta(minutes=ag.duracao)
        events.append({
            "id": ag.pk,
            "title": ag.nome_cliente,
            "start": ag.data_hora.isoformat(),
            "end": fim.isoformat(),
            "backgroundColor": STATUS_COLORS.get(ag.status, "#6B7280"),
            "borderColor": STATUS_COLORS.get(ag.status, "#6B7280"),
            "extendedProps": {
                "source": "local",
                "email": ag.email_cliente,
                "telefone": ag.telefone_cliente,
                "status": ag.status,
                "status_display": ag.get_status_display(),
                "duracao": ag.duracao,
                "observacao": ag.observacao,
            },
        })

    # Importar eventos do Google Calendar
    config = ConfiguracaoAgenda.objects.filter(consultor=request.user).first()
    if config and config.google_token and start and end:
        google_event_ids = set(
            Agendamento.objects.filter(
                consultor=request.user,
                google_event_id__isnull=False,
            ).exclude(google_event_id="").values_list("google_event_id", flat=True)
        )

        tz = timezone.get_current_timezone()
        try:
            dt_start = timezone.make_aware(datetime.fromisoformat(start[:10]), tz)
            dt_end = timezone.make_aware(datetime.fromisoformat(end[:10]) + timedelta(days=1), tz)
        except (ValueError, TypeError):
            dt_start = dt_end = None

        if dt_start and dt_end:
            google_events = listar_eventos(config, dt_start, dt_end)
            for ge in google_events:
                if ge.get("id") in google_event_ids:
                    continue
                g_start = ge.get("start", {})
                g_end = ge.get("end", {})
                events.append({
                    "id": f"google_{ge.get('id', '')}",
                    "title": ge.get("summary", "(Sem título)"),
                    "start": g_start.get("dateTime", g_start.get("date", "")),
                    "end": g_end.get("dateTime", g_end.get("date", "")),
                    "backgroundColor": "#4285F4",
                    "borderColor": "#4285F4",
                    "extendedProps": {
                        "source": "google",
                        "status": "google",
                        "status_display": "Google Calendar",
                        "observacao": ge.get("description", ""),
                    },
                })

    return JsonResponse(events, safe=False)


@consultor_required
def agenda_criar(request):
    """Cria um novo agendamento manualmente (interno)."""
    if request.user.is_gestor:
        clientes = Cliente.objects.all()
        consultores = User.objects.filter(
            role__in=[User.Role.CONSULTOR, User.Role.GESTOR], is_active=True
        )
    else:
        clientes = Cliente.objects.filter(consultor=request.user)
        consultores = User.objects.filter(pk=request.user.pk)

    if request.method == "POST":
        data_str = request.POST.get("data", "")
        horario_str = request.POST.get("horario", "")
        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        telefone = request.POST.get("telefone", "").strip()
        duracao = int(request.POST.get("duracao", 60) or 60)
        observacao = request.POST.get("observacao", "").strip()
        cliente_id = request.POST.get("cliente", "")
        consultor_id = request.POST.get("consultor", "")

        if not all([data_str, horario_str, nome]):
            messages.error(request, "Preencha data, horário e nome.")
            return redirect("agenda:criar")

        consultor = request.user
        if consultor_id and request.user.is_gestor:
            consultor = User.objects.filter(pk=consultor_id).first() or request.user

        tz = timezone.get_current_timezone()
        data_hora = timezone.make_aware(
            datetime.strptime(f"{data_str} {horario_str}", "%Y-%m-%d %H:%M"), tz
        )

        agendamento = Agendamento.objects.create(
            consultor=consultor,
            data_hora=data_hora,
            duracao=duracao,
            nome_cliente=nome,
            email_cliente=email or "",
            telefone_cliente=telefone,
            observacao=observacao,
            cliente_id=int(cliente_id) if cliente_id else None,
        )

        # Criar evento no Google Calendar
        config = ConfiguracaoAgenda.objects.filter(consultor=consultor).first()
        if config and config.google_token:
            event_id = criar_evento(config, agendamento)
            if event_id:
                agendamento.google_event_id = event_id
                agendamento.save(update_fields=["google_event_id"])

        messages.success(request, "Agendamento criado com sucesso!")
        return redirect("agenda:visualizar")

    config = ConfiguracaoAgenda.objects.filter(consultor=request.user).first()
    return render(request, "agenda/criar.html", {
        "clientes": clientes,
        "consultores": consultores,
        "config": config,
        "duracao_padrao": config.duracao_padrao if config else 60,
    })


@consultor_required
def agenda_editar(request, pk):
    """Edita um agendamento existente."""
    if request.user.is_gestor:
        agendamento = get_object_or_404(Agendamento, pk=pk)
        clientes = Cliente.objects.all()
        consultores = User.objects.filter(
            role__in=[User.Role.CONSULTOR, User.Role.GESTOR], is_active=True
        )
    else:
        agendamento = get_object_or_404(Agendamento, pk=pk, consultor=request.user)
        clientes = Cliente.objects.filter(consultor=request.user)
        consultores = User.objects.filter(pk=request.user.pk)

    if request.method == "POST":
        data_str = request.POST.get("data", "")
        horario_str = request.POST.get("horario", "")
        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        telefone = request.POST.get("telefone", "").strip()
        duracao = int(request.POST.get("duracao", 60) or 60)
        observacao = request.POST.get("observacao", "").strip()
        cliente_id = request.POST.get("cliente", "")
        consultor_id = request.POST.get("consultor", "")

        if not all([data_str, horario_str, nome]):
            messages.error(request, "Preencha data, horário e nome.")
            return redirect("agenda:editar", pk=pk)

        if consultor_id and request.user.is_gestor:
            agendamento.consultor = User.objects.filter(pk=consultor_id).first() or agendamento.consultor

        tz = timezone.get_current_timezone()
        agendamento.data_hora = timezone.make_aware(
            datetime.strptime(f"{data_str} {horario_str}", "%Y-%m-%d %H:%M"), tz
        )
        agendamento.duracao = duracao
        agendamento.nome_cliente = nome
        agendamento.email_cliente = email or ""
        agendamento.telefone_cliente = telefone
        agendamento.observacao = observacao
        agendamento.cliente_id = int(cliente_id) if cliente_id else None
        agendamento.save()

        messages.success(request, "Agendamento atualizado!")
        return redirect("agenda:visualizar")

    return render(request, "agenda/editar.html", {
        "agendamento": agendamento,
        "clientes": clientes,
        "consultores": consultores,
    })


@consultor_required
def agenda_followup(request):
    """Painel de follow-up: acompanhar confirmações de agendamentos futuros."""
    agora = timezone.now()
    agendamentos = Agendamento.objects.filter(
        status=Agendamento.Status.CONFIRMADO,
        data_hora__gte=agora,
    ).select_related("cliente", "consultor").order_by("data_hora")

    if not request.user.is_gestor:
        agendamentos = agendamentos.filter(consultor=request.user)

    total = agendamentos.count()
    confirmados = agendamentos.filter(confirmado_pelo_cliente=True).count()
    pendentes = total - confirmados

    return render(request, "agenda/followup.html", {
        "agendamentos": agendamentos,
        "total": total,
        "confirmados": confirmados,
        "pendentes": pendentes,
    })


@consultor_required
@require_POST
def agenda_toggle_confirmacao(request, pk):
    """Toggle confirmação do cliente."""
    if request.user.is_gestor:
        agendamento = get_object_or_404(Agendamento, pk=pk)
    else:
        agendamento = get_object_or_404(Agendamento, pk=pk, consultor=request.user)
    agendamento.confirmado_pelo_cliente = not agendamento.confirmado_pelo_cliente
    agendamento.save(update_fields=["confirmado_pelo_cliente", "updated_at"])

    status_text = "confirmado" if agendamento.confirmado_pelo_cliente else "pendente"
    messages.success(request, f"Agendamento marcado como {status_text}.")

    next_url = request.POST.get("next", "")
    if next_url:
        return redirect(next_url)
    return redirect("agenda:followup")


@consultor_required
@require_POST
def agenda_enviar_mensagem(request, pk):
    """Envia mensagem de confirmação via WhatsApp para o cliente, consultor e grupo."""
    from .tasks import enviar_confirmacao_agendamento

    if request.user.is_gestor:
        agendamento = get_object_or_404(Agendamento, pk=pk)
    else:
        agendamento = get_object_or_404(Agendamento, pk=pk, consultor=request.user)

    if not agendamento.telefone_cliente:
        messages.error(request, "Este agendamento não possui telefone cadastrado.")
    else:
        enviar_confirmacao_agendamento.delay(agendamento.pk)
        messages.success(request, f"Mensagem de confirmação sendo enviada para {agendamento.nome_cliente}.")

    next_url = request.POST.get("next", "")
    if next_url:
        return redirect(next_url)
    return redirect("agenda:followup")


@consultor_required
def agenda_agendamentos(request):
    """Lista de agendamentos com filtros."""
    agendamentos = Agendamento.objects.filter(
        consultor=request.user,
    ).select_related("cliente").order_by("-data_hora")

    status = request.GET.get("status")
    if status:
        agendamentos = agendamentos.filter(status=status)

    periodo = request.GET.get("periodo")
    hoje = timezone.now().date()
    if periodo == "hoje":
        agendamentos = agendamentos.filter(data_hora__date=hoje)
    elif periodo == "semana":
        agendamentos = agendamentos.filter(
            data_hora__date__gte=hoje,
            data_hora__date__lte=hoje + timedelta(days=7),
        )
    elif periodo == "mes":
        agendamentos = agendamentos.filter(
            data_hora__year=hoje.year,
            data_hora__month=hoje.month,
        )

    return render(request, "agenda/agendamentos.html", {
        "agendamentos": agendamentos,
        "status_choices": Agendamento.Status.choices,
        "filtro_status": status,
        "filtro_periodo": periodo,
    })


@consultor_required
@require_POST
def agenda_cancelar(request, pk):
    """Consultor cancela um agendamento."""
    agendamento = get_object_or_404(
        Agendamento, pk=pk, consultor=request.user
    )
    agendamento.status = Agendamento.Status.CANCELADO
    agendamento.save(update_fields=["status", "updated_at"])

    # Remover do Google Calendar
    config = ConfiguracaoAgenda.objects.filter(consultor=request.user).first()
    if config and agendamento.google_event_id:
        deletar_evento(config, agendamento.google_event_id)

    messages.success(request, "Agendamento cancelado.")
    return redirect("agenda:agendamentos")


@consultor_required
@require_POST
def agenda_marcar_status(request, pk):
    """Consultor marca status de um agendamento (realizado/não compareceu)."""
    agendamento = get_object_or_404(
        Agendamento, pk=pk, consultor=request.user
    )
    novo_status = request.POST.get("status")
    if novo_status in (Agendamento.Status.REALIZADO, Agendamento.Status.NAO_COMPARECEU):
        agendamento.status = novo_status
        agendamento.save(update_fields=["status", "updated_at"])
        messages.success(request, "Status atualizado.")
    return redirect("agenda:agendamentos")


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------


@consultor_required
def google_auth_inicio(request):
    """Inicia o fluxo OAuth2 com Google."""
    if not HAS_GOOGLE:
        messages.error(request, "Bibliotecas do Google não instaladas.")
        return redirect("agenda:config")

    redirect_uri = request.build_absolute_uri("/agenda/google/callback/")
    flow = get_flow(redirect_uri)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["google_oauth_state"] = state
    return redirect(auth_url)


@consultor_required
def google_auth_callback(request):
    """Callback do OAuth2 Google."""
    if not HAS_GOOGLE:
        messages.error(request, "Bibliotecas do Google não instaladas.")
        return redirect("agenda:config")

    redirect_uri = request.build_absolute_uri("/agenda/google/callback/")
    flow = get_flow(redirect_uri)
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    creds = flow.credentials
    config, _ = ConfiguracaoAgenda.objects.get_or_create(consultor=request.user)
    config.google_token = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
    }
    if not config.google_calendar_id:
        config.google_calendar_id = "primary"
    config.save()

    messages.success(request, "Google Calendar conectado com sucesso!")
    return redirect("agenda:config")


@consultor_required
@require_POST
def google_desconectar(request):
    """Remove a conexão com o Google Calendar."""
    config = get_object_or_404(ConfiguracaoAgenda, consultor=request.user)
    config.google_token = None
    config.google_calendar_id = ""
    config.save(update_fields=["google_token", "google_calendar_id", "updated_at"])
    messages.success(request, "Google Calendar desconectado.")
    return redirect("agenda:config")


# ---------------------------------------------------------------------------
# Views públicas (sem login)
# ---------------------------------------------------------------------------


def publico_agenda(request, slug):
    """Página pública estilo Calendly para agendar com o consultor."""
    config = get_object_or_404(ConfiguracaoAgenda, slug=slug, is_active=True)
    horarios = config.horarios.filter(ativo=True).order_by("dia_semana", "hora_inicio")

    hoje = date.today()
    dias = []
    for i in range(config.dias_visiveis):
        dia = hoje + timedelta(days=i)
        # Só mostra dias que têm horário configurado
        horario_dia = horarios.filter(dia_semana=dia.weekday()).first()
        if horario_dia:
            dias.append({
                "data": dia,
                "dia_semana": HorarioTrabalho.DiaSemana(dia.weekday()).label,
            })

    return render(request, "agenda/publico.html", {
        "config": config,
        "consultor": config.consultor,
        "dias": dias,
        "duracao": config.duracao_padrao,
    })


def publico_horarios(request, slug):
    """API JSON: retorna slots disponíveis para uma data específica."""
    config = get_object_or_404(ConfiguracaoAgenda, slug=slug, is_active=True)
    data_str = request.GET.get("data")
    if not data_str:
        return JsonResponse({"slots": []})

    data_selecionada = date.fromisoformat(data_str)
    dia_semana = data_selecionada.weekday()

    horario = config.horarios.filter(dia_semana=dia_semana, ativo=True).first()
    if not horario:
        return JsonResponse({"slots": []})

    # Gerar slots
    duracao = config.duracao_padrao
    slots = []
    current = datetime.combine(data_selecionada, horario.hora_inicio)
    fim = datetime.combine(data_selecionada, horario.hora_fim)
    tz = timezone.get_current_timezone()

    # Horário mínimo de antecedência
    minimo = timezone.now() + timedelta(hours=config.antecedencia_minima)

    # Buscar agendamentos existentes nesse dia
    agendamentos = Agendamento.objects.filter(
        consultor=config.consultor,
        data_hora__date=data_selecionada,
        status=Agendamento.Status.CONFIRMADO,
    ).values_list("data_hora", "duracao")

    ocupados = []
    for ag_inicio, ag_duracao in agendamentos:
        ag_fim = ag_inicio + timedelta(minutes=ag_duracao)
        ocupados.append((ag_inicio, ag_fim))

    # Buscar eventos do Google Calendar
    if config.google_token:
        inicio_dia = timezone.make_aware(
            datetime.combine(data_selecionada, time.min), tz
        )
        fim_dia = timezone.make_aware(
            datetime.combine(data_selecionada, time.max), tz
        )
        google_busy = buscar_eventos_ocupados(config, inicio_dia, fim_dia)
        for g_start, g_end in google_busy:
            ocupados.append((g_start, g_end))

    while current + timedelta(minutes=duracao) <= fim:
        slot_inicio = timezone.make_aware(current, tz)
        slot_fim = slot_inicio + timedelta(minutes=duracao)

        disponivel = True
        if slot_inicio < minimo:
            disponivel = False
        else:
            for oc_inicio, oc_fim in ocupados:
                if slot_inicio < oc_fim and slot_fim > oc_inicio:
                    disponivel = False
                    break

        if disponivel:
            slots.append(current.strftime("%H:%M"))

        current += timedelta(minutes=duracao)

    return JsonResponse({"slots": slots})


@require_POST
def publico_agendar(request, slug):
    """Confirma o agendamento público."""
    config = get_object_or_404(ConfiguracaoAgenda, slug=slug, is_active=True)

    data_str = request.POST.get("data")
    horario_str = request.POST.get("horario")
    nome = request.POST.get("nome", "").strip()
    email = request.POST.get("email", "").strip()
    telefone = request.POST.get("telefone", "").strip()
    observacao = request.POST.get("observacao", "").strip()

    if not all([data_str, horario_str, nome, email]):
        messages.error(request, "Preencha todos os campos obrigatórios.")
        return redirect("agenda:publico_agenda", slug=slug)

    tz = timezone.get_current_timezone()
    data_hora = timezone.make_aware(
        datetime.strptime(f"{data_str} {horario_str}", "%Y-%m-%d %H:%M"), tz
    )

    # Verificar se slot ainda está disponível
    conflito = Agendamento.objects.filter(
        consultor=config.consultor,
        data_hora=data_hora,
        status=Agendamento.Status.CONFIRMADO,
    ).exists()

    if conflito:
        messages.error(request, "Este horário já foi reservado. Escolha outro.")
        return redirect("agenda:publico_agenda", slug=slug)

    agendamento = Agendamento.objects.create(
        consultor=config.consultor,
        data_hora=data_hora,
        duracao=config.duracao_padrao,
        nome_cliente=nome,
        email_cliente=email,
        telefone_cliente=telefone,
        observacao=observacao,
    )

    # Criar evento no Google Calendar
    if config.google_token:
        event_id = criar_evento(config, agendamento)
        if event_id:
            agendamento.google_event_id = event_id
            agendamento.save(update_fields=["google_event_id"])

    return render(request, "agenda/publico_confirmado.html", {
        "agendamento": agendamento,
        "config": config,
        "consultor": config.consultor,
    })


def publico_cancelar(request, token):
    """Cancela agendamento via token UUID (link enviado por e-mail)."""
    agendamento = get_object_or_404(Agendamento, token_cancelamento=token)

    if request.method == "POST":
        if agendamento.status == Agendamento.Status.CONFIRMADO:
            agendamento.status = Agendamento.Status.CANCELADO
            agendamento.save(update_fields=["status", "updated_at"])

            config = ConfiguracaoAgenda.objects.filter(
                consultor=agendamento.consultor
            ).first()
            if config and agendamento.google_event_id:
                deletar_evento(config, agendamento.google_event_id)

        return render(request, "agenda/publico_cancelado.html", {
            "agendamento": agendamento,
        })

    return render(request, "agenda/publico_cancelar_confirma.html", {
        "agendamento": agendamento,
    })
