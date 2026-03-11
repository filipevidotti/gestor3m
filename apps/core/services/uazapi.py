"""
UAZAPI WhatsApp API client.
Docs: https://docs.uazapi.com/
"""
import logging

import requests

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)


class UazapiClient:
    """Cliente para a API UAZAPI (WhatsApp)."""

    def __init__(self):
        self.base_url = Configuracao.get("UAZAPI_URL", "").rstrip("/")
        self.token = Configuracao.get("UAZAPI_TOKEN", "")

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method, endpoint, **kwargs):
        """Faz request genérico à API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault("headers", self._headers)
        kwargs.setdefault("timeout", 15)
        try:
            resp = requests.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            logger.exception("UAZAPI request failed: %s %s", method, endpoint)
            raise

    # ── Status ────────────────────────────────────────────────────

    def status(self):
        """Verifica status da instância."""
        return self._request("GET", "/status")

    # ── Mensagens ─────────────────────────────────────────────────

    def enviar_mensagem(self, telefone, texto):
        """Envia mensagem de texto simples."""
        telefone = _normalizar_telefone(telefone)
        try:
            self._request("POST", "/send/text", json={
                "phone": telefone,
                "message": texto,
            })
            logger.info("WhatsApp enviado para %s", telefone)
            return True
        except Exception:
            logger.exception("Erro ao enviar WhatsApp para %s", telefone)
            return False

    def enviar_mensagem_grupo(self, group_id, texto):
        """Envia mensagem para um grupo."""
        try:
            self._request("POST", "/send/text", json={
                "phone": group_id,
                "message": texto,
                "isGroup": True,
            })
            logger.info("WhatsApp grupo enviado para %s", group_id)
            return True
        except Exception:
            logger.exception("Erro ao enviar para grupo %s", group_id)
            return False

    # ── Grupos ────────────────────────────────────────────────────

    def listar_grupos(self):
        """Lista todos os grupos do WhatsApp.

        Returns: lista de dicts com id, subject, size, etc.
        """
        try:
            data = self._request("GET", "/groups")
            # A resposta pode variar: lista direta ou dentro de uma chave
            if isinstance(data, list):
                return data
            return data.get("groups", data.get("data", []))
        except Exception:
            logger.exception("Erro ao listar grupos")
            return []

    def info_grupo(self, group_id):
        """Busca informações de um grupo específico."""
        try:
            return self._request("GET", f"/groups/{group_id}")
        except Exception:
            logger.exception("Erro ao buscar grupo %s", group_id)
            return None

    def participantes_grupo(self, group_id):
        """Lista participantes de um grupo."""
        try:
            data = self._request("GET", f"/groups/{group_id}/participants")
            if isinstance(data, list):
                return data
            return data.get("participants", data.get("data", []))
        except Exception:
            logger.exception("Erro ao listar participantes do grupo %s", group_id)
            return []


def _normalizar_telefone(telefone):
    """Remove formatação e garante formato 55XXXXXXXXXXX."""
    num = "".join(c for c in telefone if c.isdigit())
    if not num.startswith("55"):
        num = "55" + num
    return num


# ── Funções de conveniência (compatibilidade com evolution.py) ────


def enviar_mensagem(telefone, texto):
    """Wrapper compatível com a interface antiga da evolution."""
    client = UazapiClient()
    if not client.base_url or not client.token:
        logger.warning("UAZAPI não configurada.")
        return False
    return client.enviar_mensagem(telefone, texto)


def enviar_mensagem_grupo(group_id, texto):
    """Envia mensagem para grupo via UAZAPI."""
    client = UazapiClient()
    if not client.base_url or not client.token:
        logger.warning("UAZAPI não configurada.")
        return False
    return client.enviar_mensagem_grupo(group_id, texto)
