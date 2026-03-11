import logging

import requests

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3"


def _get_config():
    api_key = Configuracao.get("BREVO_API_KEY")
    sender_email = Configuracao.get("BREVO_SENDER_EMAIL", "noreply@3mconsultoria.com.br")
    sender_name = Configuracao.get("BREVO_SENDER_NAME", "3M Consultoria")
    return api_key, sender_email, sender_name


def enviar_email(destinatario_email, destinatario_nome, assunto, html_content):
    """Envia e-mail transacional via Brevo API."""
    api_key, sender_email, sender_name = _get_config()
    if not api_key:
        logger.warning("Brevo API não configurada.")
        return False

    try:
        resp = requests.post(
            f"{BREVO_API_URL}/smtp/email",
            json={
                "sender": {"name": sender_name, "email": sender_email},
                "to": [{"email": destinatario_email, "name": destinatario_nome}],
                "subject": assunto,
                "htmlContent": html_content,
            },
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("E-mail enviado para %s", destinatario_email)
        return True
    except Exception:
        logger.exception("Erro ao enviar e-mail para %s", destinatario_email)
        return False


def enviar_template_email(destinatario_email, destinatario_nome, template_id, params=None):
    """Envia e-mail usando template Brevo."""
    api_key, sender_email, sender_name = _get_config()
    if not api_key:
        return False

    try:
        resp = requests.post(
            f"{BREVO_API_URL}/smtp/email",
            json={
                "sender": {"name": sender_name, "email": sender_email},
                "to": [{"email": destinatario_email, "name": destinatario_nome}],
                "templateId": template_id,
                "params": params or {},
            },
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Erro ao enviar template e-mail para %s", destinatario_email)
        return False
