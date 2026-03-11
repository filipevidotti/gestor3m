import logging
from datetime import datetime, timedelta

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build

    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _google_creds():
    """Busca Client ID e Secret do model Configuracao."""
    return (
        Configuracao.get("GOOGLE_CLIENT_ID"),
        Configuracao.get("GOOGLE_CLIENT_SECRET"),
    )


def get_flow(redirect_uri):
    """Cria o fluxo OAuth2 para Google Calendar."""
    if not HAS_GOOGLE:
        raise RuntimeError("google-api-python-client não está instalado.")
    client_id, client_secret = _google_creds()
    return Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )


def get_credentials(config):
    """Obtém credenciais do Google a partir do token salvo."""
    if not config.google_token:
        return None
    client_id, client_secret = _google_creds()
    return Credentials(
        token=config.google_token.get("token"),
        refresh_token=config.google_token.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


def get_calendar_service(config):
    """Retorna o serviço do Google Calendar."""
    creds = get_credentials(config)
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds)


def criar_evento(config, agendamento):
    """Cria evento no Google Calendar e retorna o event_id."""
    service = get_calendar_service(config)
    if not service:
        logger.warning("Google Calendar não configurado para %s", config.consultor)
        return None

    calendar_id = config.google_calendar_id or "primary"
    fim = agendamento.data_hora + timedelta(minutes=agendamento.duracao)

    event = {
        "summary": f"Reunião com {agendamento.nome_cliente}",
        "description": (
            f"Cliente: {agendamento.nome_cliente}\n"
            f"E-mail: {agendamento.email_cliente}\n"
            f"Telefone: {agendamento.telefone_cliente}\n"
            f"Obs: {agendamento.observacao}"
        ),
        "start": {
            "dateTime": agendamento.data_hora.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
        "end": {
            "dateTime": fim.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
        "attendees": [{"email": agendamento.email_cliente}],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 15},
            ],
        },
    }

    try:
        result = service.events().insert(
            calendarId=calendar_id, body=event, sendUpdates="all"
        ).execute()
        logger.info("Evento criado no Google Calendar: %s", result.get("id"))
        return result.get("id")
    except Exception:
        logger.exception("Erro ao criar evento no Google Calendar")
        return None


def deletar_evento(config, google_event_id):
    """Remove evento do Google Calendar."""
    service = get_calendar_service(config)
    if not service or not google_event_id:
        return

    calendar_id = config.google_calendar_id or "primary"

    try:
        service.events().delete(
            calendarId=calendar_id, eventId=google_event_id, sendUpdates="all"
        ).execute()
        logger.info("Evento removido do Google Calendar: %s", google_event_id)
    except Exception:
        logger.exception("Erro ao deletar evento do Google Calendar")


def buscar_eventos_ocupados(config, data_inicio, data_fim):
    """Consulta freebusy do Google Calendar para verificar horários ocupados."""
    service = get_calendar_service(config)
    if not service:
        return []

    calendar_id = config.google_calendar_id or "primary"

    body = {
        "timeMin": data_inicio.isoformat(),
        "timeMax": data_fim.isoformat(),
        "timeZone": "America/Sao_Paulo",
        "items": [{"id": calendar_id}],
    }

    try:
        result = service.freebusy().query(body=body).execute()
        busy = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])
        return [
            (
                datetime.fromisoformat(b["start"]),
                datetime.fromisoformat(b["end"]),
            )
            for b in busy
        ]
    except Exception:
        logger.exception("Erro ao consultar freebusy do Google Calendar")
        return []
