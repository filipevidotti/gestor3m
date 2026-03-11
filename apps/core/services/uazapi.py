"""
UAZAPI WhatsApp API client.
Docs: https://docs.uazapi.com/
Auth: header 'token' com o token da instancia.
Base URL: https://<server> (sem instancia no path).
Endpoints confirmados via teste direto na API:
  - GET /status (público)
  - GET /instance/status (autenticado)
  - GET /contacts
  - GET /group/list
  - POST /send/text {number, text}
  - POST /send/location {number, lat, lng, title}
  - POST /send/contact {number, ...}
  - POST /webhook {url, enabled, events}
"""
import logging
import re

import requests

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)


class UazapiClient:
    """Cliente para a API UAZAPI (WhatsApp)."""

    TIMEOUT = 30

    def __init__(self):
        self.base_url = Configuracao.get("UAZAPI_URL", "").rstrip("/")
        self.token = Configuracao.get("UAZAPI_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update({
            "token": self.token,
            "Content-Type": "application/json",
        })

    def _get(self, endpoint):
        """GET request autenticada."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT)
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                logger.error("UAZAPI GET %s: %s %s", endpoint, resp.status_code, data)
            return data, resp.status_code
        except requests.RequestException:
            logger.exception("UAZAPI connection error GET %s", endpoint)
            raise

    def _post(self, endpoint, json_data=None):
        """POST request autenticada."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.post(url, json=json_data, timeout=self.TIMEOUT)
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                logger.error("UAZAPI POST %s: %s %s", endpoint, resp.status_code, data)
            return data, resp.status_code
        except requests.RequestException:
            logger.exception("UAZAPI connection error POST %s", endpoint)
            raise

    # ── Status / Conexão ─────────────────────────────────────────

    def status_conexao(self):
        """Retorna status da conexão da instância."""
        data, _ = self._get("/instance/status")
        return data

    def qrcode(self):
        """Retorna QR code para conectar instância."""
        data, _ = self._get("/instance/qrcode")
        return data.get("qrcode", "")

    # ── Mensagens ─────────────────────────────────────────────────

    def enviar_mensagem(self, telefone, texto):
        """Envia mensagem de texto simples."""
        telefone = formatar_telefone(telefone)
        try:
            data, status = self._post("/send/text", {
                "number": telefone,
                "text": texto,
            })
            if status < 400:
                logger.info("WhatsApp enviado para %s", telefone)
                return True
            logger.error("Falha ao enviar para %s: %s", telefone, data)
            return False
        except Exception:
            logger.exception("Erro ao enviar WhatsApp para %s", telefone)
            return False

    def enviar_mensagem_grupo(self, group_id, texto):
        """Envia mensagem para um grupo WhatsApp."""
        try:
            data, status = self._post("/send/text", {
                "number": group_id,
                "text": texto,
            })
            if status < 400:
                logger.info("WhatsApp grupo enviado para %s", group_id)
                return True
            logger.error("Falha ao enviar para grupo %s: %s", group_id, data)
            return False
        except Exception:
            logger.exception("Erro ao enviar para grupo %s", group_id)
            return False

    def enviar_imagem(self, telefone, url, caption=""):
        """Envia imagem com caption opcional."""
        telefone = formatar_telefone(telefone)
        data, _ = self._post("/send/image", {
            "number": telefone,
            "image": url,
            "caption": caption,
        })
        return data

    def enviar_documento(self, telefone, url, filename=""):
        """Envia documento."""
        telefone = formatar_telefone(telefone)
        data, _ = self._post("/send/document", {
            "number": telefone,
            "document": url,
            "fileName": filename,
        })
        return data

    # ── Grupos ────────────────────────────────────────────────────

    def listar_grupos(self):
        """Lista todos os grupos do WhatsApp."""
        try:
            data, status = self._get("/group/list")
            if status >= 400:
                logger.error("Erro ao listar grupos: %s", data)
                return []

            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                grupos = data.get("groups", data.get("data", data.get("response", [])))
                if isinstance(grupos, list):
                    return grupos

            return []
        except Exception:
            logger.exception("Erro ao listar grupos")
            return []

    def info_grupo(self, group_id):
        """Busca informações de um grupo específico."""
        try:
            data, _ = self._get(f"/group/info?groupJid={group_id}")
            return data
        except Exception:
            logger.exception("Erro ao buscar grupo %s", group_id)
            return None

    def participantes_grupo(self, group_id):
        """Lista participantes de um grupo."""
        info = self.info_grupo(group_id)
        if info and isinstance(info, dict):
            return info.get("participants", [])
        return []

    # ── Verificação ───────────────────────────────────────────────

    def verificar_numero(self, telefone):
        """Verifica se número está registrado no WhatsApp."""
        try:
            telefone = formatar_telefone(telefone)
            data, _ = self._get(f"/misc/onWhatsApp?phone={telefone}")
            return bool(data.get("exists", False))
        except Exception:
            return False

    # ── Webhook ───────────────────────────────────────────────────

    def configurar_webhook(self, url, events=None):
        """Configura URL do webhook na UAZAPI."""
        if events is None:
            events = ["messages.upsert", "groups.update"]
        data, status = self._post("/webhook", {
            "url": url,
            "enabled": True,
            "events": events,
        })
        return data, status


# ── Utilitários ──────────────────────────────────────────────────


def formatar_telefone(telefone):
    """Normaliza telefone para formato UAZAPI: 5511999999999."""
    numero = re.sub(r"\D", "", str(telefone))
    if "@" in str(telefone):
        numero = re.sub(r"\D", "", str(telefone).split("@")[0])
    if len(numero) <= 11:
        numero = f"55{numero}"
    if numero.startswith("5555") and len(numero) > 13:
        numero = numero[2:]
    return numero


# ── Funções de conveniência ──────────────────────────────────────


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
