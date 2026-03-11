import logging

import requests

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)


def _get_config():
    url = Configuracao.get("EVOLUTION_API_URL")
    key = Configuracao.get("EVOLUTION_API_KEY")
    instance = Configuracao.get("EVOLUTION_INSTANCE")
    return url, key, instance


def _normalizar_telefone(telefone):
    """Remove formatação e garante formato 55XXXXXXXXXXX."""
    num = "".join(c for c in telefone if c.isdigit())
    if not num.startswith("55"):
        num = "55" + num
    return num


def enviar_mensagem(telefone, texto):
    """Envia mensagem de texto simples via Evolution API."""
    url, key, instance = _get_config()
    if not all([url, key, instance]):
        logger.warning("Evolution API não configurada.")
        return False

    telefone = _normalizar_telefone(telefone)
    endpoint = f"{url.rstrip('/')}/message/sendText/{instance}"

    try:
        resp = requests.post(
            endpoint,
            json={
                "number": telefone,
                "text": texto,
            },
            headers={"apikey": key, "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("WhatsApp enviado para %s", telefone)
        return True
    except Exception:
        logger.exception("Erro ao enviar WhatsApp para %s", telefone)
        return False


def enviar_mensagem_com_botoes(telefone, texto, botoes):
    """Envia mensagem com botões (máx 3).

    botoes = [{"displayText": "Ver mais", "id": "1"}]
    """
    url, key, instance = _get_config()
    if not all([url, key, instance]):
        return False

    telefone = _normalizar_telefone(telefone)
    endpoint = f"{url.rstrip('/')}/message/sendButtons/{instance}"

    try:
        resp = requests.post(
            endpoint,
            json={
                "number": telefone,
                "title": "",
                "description": texto,
                "buttons": botoes[:3],
            },
            headers={"apikey": key, "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Erro ao enviar botões WhatsApp para %s", telefone)
        return False
