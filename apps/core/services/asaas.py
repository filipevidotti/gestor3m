import logging

import requests

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)


class AsaasClient:
    """Cliente para a API Asaas v3 (pagamentos, assinaturas, PIX, boleto)."""

    def __init__(self):
        self.api_key = Configuracao.get("ASAAS_API_KEY")
        env = Configuracao.get("ASAAS_ENVIRONMENT", "sandbox")
        if env == "production":
            self.base_url = "https://api.asaas.com/v3"
        else:
            self.base_url = "https://sandbox.asaas.com/api/v3"

    @property
    def _headers(self):
        return {
            "access_token": self.api_key,
            "Content-Type": "application/json",
        }

    def _request(self, method, endpoint, **kwargs):
        if not self.api_key:
            logger.warning("Asaas API não configurada (ASAAS_API_KEY vazia).")
            return None

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = requests.request(
                method, url, headers=self._headers, timeout=30, **kwargs,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error(
                "Asaas HTTP %s %s → %s: %s",
                method, endpoint, e.response.status_code,
                e.response.text[:500],
            )
            return None
        except Exception:
            logger.exception("Asaas request error: %s %s", method, endpoint)
            return None

    # ── Customers ────────────────────────────────────────────────────────

    def criar_customer(self, nome, cpf_cnpj, email=None, telefone=None,
                       external_reference=None):
        """Cria cliente no Asaas. Retorna dict com 'id' ou None."""
        dados = {
            "name": nome,
            "cpfCnpj": cpf_cnpj,
            "notificationDisabled": True,
        }
        if email:
            dados["email"] = email
        if telefone:
            dados["mobilePhone"] = telefone
        if external_reference:
            dados["externalReference"] = external_reference
        return self._request("POST", "customers", json=dados)

    def buscar_customer(self, customer_id):
        return self._request("GET", f"customers/{customer_id}")

    # ── Cobranças (Payments) ─────────────────────────────────────────────

    def criar_cobranca(self, customer_id, valor, vencimento, descricao,
                       billing_type="PIX", external_reference=None):
        """Cria cobrança avulsa (PIX, BOLETO ou CREDIT_CARD)."""
        dados = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": float(valor),
            "dueDate": str(vencimento),
            "description": descricao,
            "notificationDisabled": True,
        }
        if external_reference:
            dados["externalReference"] = external_reference
        return self._request("POST", "payments", json=dados)

    def consultar_pagamento(self, payment_id):
        return self._request("GET", f"payments/{payment_id}")

    def obter_pix_qrcode(self, payment_id):
        """Retorna dict com 'encodedImage', 'payload', 'expirationDate'."""
        return self._request("GET", f"payments/{payment_id}/pixQrCode")

    def obter_boleto(self, payment_id):
        """Retorna dict com 'identificationField' e 'nossoNumero'."""
        return self._request(
            "GET", f"payments/{payment_id}/identificationField",
        )

    def listar_pagamentos(self, subscription_id=None, customer_id=None):
        """Lista pagamentos, opcionalmente filtrados por subscription."""
        params = {}
        if subscription_id:
            params["subscription"] = subscription_id
        if customer_id:
            params["customer"] = customer_id
        return self._request("GET", "payments", params=params)

    # ── Assinaturas (Subscriptions) ──────────────────────────────────────

    def criar_subscription(self, customer_id, valor, dia_vencimento,
                           descricao, billing_type="BOLETO",
                           cycle="MONTHLY", external_reference=None):
        """Cria assinatura recorrente."""
        from datetime import date, timedelta

        # Calcula próxima data de vencimento
        hoje = date.today()
        if hoje.day <= dia_vencimento:
            proximo = hoje.replace(day=dia_vencimento)
        else:
            if hoje.month == 12:
                proximo = hoje.replace(year=hoje.year + 1, month=1, day=dia_vencimento)
            else:
                proximo = hoje.replace(month=hoje.month + 1, day=dia_vencimento)

        dados = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": float(valor),
            "nextDueDate": str(proximo),
            "cycle": cycle,
            "description": descricao,
            "notificationDisabled": True,
        }
        if external_reference:
            dados["externalReference"] = external_reference
        return self._request("POST", "subscriptions", json=dados)

    def buscar_subscription(self, subscription_id):
        return self._request("GET", f"subscriptions/{subscription_id}")

    def cancelar_subscription(self, subscription_id):
        return self._request("DELETE", f"subscriptions/{subscription_id}")
