"""
UAZAPI WhatsApp API client.
Docs: https://docs.uazapi.com/
Auth: Bearer token no header Authorization.
Endpoints confirmados via Gestor4ticket.
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
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        })

    def _request(self, method, endpoint, json_data=None):
        """Faz request autenticada para UAZAPI."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.request(
                method, url, json=json_data, timeout=self.TIMEOUT,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                logger.error(
                    "UAZAPI error %s %s: %s %s",
                    method, endpoint, resp.status_code, data,
                )
            return data
        except requests.RequestException:
            logger.exception("UAZAPI connection error: %s %s", method, endpoint)
            raise

    # ── Status / Conexão ─────────────────────────────────────────

    def status_conexao(self):
        """Retorna status da conexão da instância."""
        return self._request("GET", "/instance/status")

    def qrcode(self):
        """Retorna QR code para conectar instância."""
        data = self._request("GET", "/instance/qrcode")
        return data.get("qrcode", "")

    # ── Mensagens ─────────────────────────────────────────────────

    def enviar_mensagem(self, telefone, texto):
        """Envia mensagem de texto simples."""
        telefone = formatar_telefone(telefone)
        try:
            self._request("POST", "/message/sendText", {
                "phone": telefone,
                "message": texto,
            })
            logger.info("WhatsApp enviado para %s", telefone)
            return True
        except Exception:
            logger.exception("Erro ao enviar WhatsApp para %s", telefone)
            return False

    def enviar_mensagem_grupo(self, group_id, texto):
        """Envia mensagem para um grupo WhatsApp."""
        try:
            self._request("POST", "/message/sendText", {
                "phone": group_id,
                "message": texto,
                "isGroup": True,
            })
            logger.info("WhatsApp grupo enviado para %s", group_id)
            return True
        except Exception:
            logger.exception("Erro ao enviar para grupo %s", group_id)
            return False

    def enviar_imagem(self, telefone, url, caption=""):
        """Envia imagem com caption opcional."""
        return self._request("POST", "/message/sendImage", {
            "phone": formatar_telefone(telefone),
            "image": url,
            "caption": caption,
        })

    def enviar_documento(self, telefone, url, filename=""):
        """Envia documento."""
        return self._request("POST", "/message/sendDocument", {
            "phone": formatar_telefone(telefone),
            "document": url,
            "fileName": filename,
        })

    def enviar_botoes(self, telefone, texto, botoes):
        """Envia mensagem com botões interativos."""
        return self._request("POST", "/message/sendButtons", {
            "phone": formatar_telefone(telefone),
            "title": "",
            "message": texto,
            "footer": "",
            "buttons": botoes,
        })

    # ── Grupos ────────────────────────────────────────────────────

    def listar_grupos(self):
        """Lista todos os grupos do WhatsApp.

        Tenta múltiplos endpoints conhecidos da UAZAPI.
        Returns: lista de dicts com id/jid, subject/name, size, etc.
        """
        # Tentar endpoints na ordem mais provável
        endpoints = [
            "/group/getAllGroups",
            "/group/list",
            "/groups",
            "/group/fetchAllGroups",
        ]
        for endpoint in endpoints:
            try:
                data = self._request("GET", endpoint)
                if data is None:
                    continue
                # Normalizar resposta
                if isinstance(data, list):
                    if data:
                        logger.info("Grupos encontrados via %s: %d", endpoint, len(data))
                        return data
                elif isinstance(data, dict):
                    grupos = data.get("groups", data.get("data", data.get("response", [])))
                    if isinstance(grupos, list) and grupos:
                        logger.info("Grupos encontrados via %s: %d", endpoint, len(grupos))
                        return grupos
            except Exception:
                logger.debug("Endpoint %s falhou, tentando próximo...", endpoint)
                continue

        logger.warning("Nenhum endpoint de grupos retornou dados.")
        return []

    def info_grupo(self, group_id):
        """Busca informações de um grupo específico."""
        try:
            return self._request("POST", "/group/groupMetadata", {
                "groupJid": group_id,
            })
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
            data = self._request("POST", "/misc/onWhatsApp", {
                "phone": formatar_telefone(telefone),
            })
            return bool(data.get("exists", False))
        except Exception:
            return False


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
