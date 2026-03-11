import logging

import requests

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)


class AutentiqueClient:
    """Cliente para a API Autentique v2 (assinatura digital de documentos)."""

    API_URL = "https://api.autentique.com.br/v2/graphql"

    def __init__(self):
        self.token = Configuracao.get("AUTENTIQUE_API_TOKEN")

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _request(self, query, variables=None, files=None):
        if not self.token:
            logger.warning("Autentique API não configurada (AUTENTIQUE_API_TOKEN vazia).")
            return None

        try:
            operations = {"query": query}
            if variables:
                operations["variables"] = variables

            if files:
                import json

                data = {
                    "operations": json.dumps(operations),
                    "map": json.dumps({"file": ["variables.file"]}),
                }
                resp = requests.post(
                    self.API_URL,
                    headers=self._headers,
                    data=data,
                    files={"file": files},
                    timeout=60,
                )
            else:
                import json

                resp = requests.post(
                    self.API_URL,
                    headers=self._headers,
                    json=operations,
                    timeout=30,
                )

            resp.raise_for_status()
            result = resp.json()

            if "errors" in result:
                logger.error("Autentique GraphQL errors: %s", result["errors"])
                return None

            return result.get("data")

        except requests.exceptions.HTTPError as e:
            logger.error(
                "Autentique HTTP %s: %s",
                e.response.status_code,
                e.response.text[:500],
            )
            return None
        except Exception:
            logger.exception("Autentique request error")
            return None

    def criar_documento(self, nome, pdf_bytes, signatarios):
        """
        Cria documento para assinatura.

        Args:
            nome: Nome do documento
            pdf_bytes: Tupla (filename, file_content, content_type)
            signatarios: Lista de dicts com 'email', 'name', e opcionalmente 'action' (SIGN/APPROVE)

        Returns:
            dict com dados do documento ou None
        """
        signers_input = []
        for s in signatarios:
            signers_input.append({
                "email": s["email"],
                "name": s.get("name", ""),
                "action": s.get("action", "SIGN"),
            })

        query = """
        mutation CreateDocumentMutation(
            $document: DocumentInput!,
            $signers: [SignerInput!]!,
            $file: Upload!
        ) {
            createDocument(
                document: $document,
                signers: $signers,
                file: $file
            ) {
                id
                name
                signatures {
                    public_id
                    name
                    email
                    action { name }
                    link { short_link }
                }
            }
        }
        """

        variables = {
            "document": {"name": nome},
            "signers": signers_input,
            "file": None,
        }

        data = self._request(query, variables=variables, files=pdf_bytes)
        if data:
            return data.get("createDocument")
        return None

    def consultar_documento(self, doc_id):
        """Consulta status de um documento pelo ID."""
        query = """
        query DocumentQuery($id: UUID!) {
            document(id: $id) {
                id
                name
                created_at
                signatures {
                    public_id
                    name
                    email
                    signed { created_at }
                    rejected { created_at }
                    action { name }
                    link { short_link }
                }
            }
        }
        """
        data = self._request(query, variables={"id": doc_id})
        if data:
            return data.get("document")
        return None

    def documento_assinado(self, doc_id):
        """Verifica se todas as assinaturas foram realizadas."""
        doc = self.consultar_documento(doc_id)
        if not doc:
            return False
        for sig in doc.get("signatures", []):
            if not sig.get("signed"):
                return False
        return True
