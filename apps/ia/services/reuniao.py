"""
Serviço de análise de reuniões com IA.

Fluxo: Upload áudio → Whisper transcrição → Agno análise → Tarefas automáticas
"""
import logging

from apps.core.models import Configuracao

from .engine import chamar_ia, extrair_json

logger = logging.getLogger(__name__)

PROMPT_ANALISE_REUNIAO = """Analise a transcrição desta reunião de consultoria do Mercado Livre.

## Dados do Cliente
- Empresa: {empresa}
- Status: {status}
- Tipo consultoria: {tipo_consultoria}
- Score diagnóstico atual: {score_atual}
- Scores por categoria: {scores_categoria}

## Tipo da Reunião
{tipo_reuniao}

## Transcrição
{transcricao}

---

Retorne um JSON com esta estrutura EXATA:
{{
    "resumo": "Resumo de 3-5 pontos principais da reunião",
    "acoes_identificadas": [
        {{
            "descricao": "Descrição da ação",
            "responsavel": "consultor" ou "cliente",
            "prioridade": "baixa", "media", "alta" ou "urgente",
            "prazo_dias": 7
        }}
    ],
    "sentimento_cliente": "positivo", "neutro", "negativo" ou "misto",
    "insights": [
        {{
            "tipo": "risco", "oportunidade" ou "alerta",
            "descricao": "Descrição do insight"
        }}
    ],
    "proximos_passos": "Resumo dos próximos passos acordados",
    "pontos_atencao": ["Lista de pontos que merecem atenção"]
}}
"""


def transcrever_audio(audio_path):
    """Transcreve áudio usando Whisper API (OpenAI)."""
    api_key = Configuracao.get("OPENAI_API_KEY")
    if not api_key:
        return {"success": False, "error": "OPENAI_API_KEY não configurada"}

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
                response_format="text",
            )

        return {
            "success": True,
            "transcricao": response if isinstance(response, str) else response.text,
        }

    except Exception as e:
        logger.error(f"Erro Whisper: {e}")
        return {"success": False, "error": str(e)}


def analisar_reuniao(reuniao):
    """Analisa transcrição de reunião com IA e retorna insights."""
    cliente = reuniao.cliente

    # Buscar último diagnóstico do cliente
    ultimo_diag = (
        cliente.diagnosticos.filter(status="completed")
        .order_by("-ano", "-mes")
        .first()
    )

    context_data = {
        "empresa": cliente.empresa,
        "status": cliente.get_status_display(),
        "tipo_consultoria": cliente.get_tipo_consultoria_display(),
        "score_atual": str(ultimo_diag.score) if ultimo_diag else "N/A",
        "scores_categoria": str(ultimo_diag.scores_por_categoria) if ultimo_diag else "N/A",
        "tipo_reuniao": reuniao.get_tipo_display(),
        "transcricao": reuniao.transcricao or reuniao.transcricao_rascunho or "",
    }

    prompt = PROMPT_ANALISE_REUNIAO.format(**context_data)

    result = chamar_ia(
        prompt=prompt,
        tipo_analise="reuniao",
        cliente=cliente,
        consultor=reuniao.consultor,
    )

    if not result.get("success"):
        return result

    parsed = extrair_json(result["content"])
    if not parsed:
        return {
            "success": False,
            "error": "Não foi possível extrair JSON da resposta da IA",
            "raw_content": result["content"],
        }

    return {
        "success": True,
        "data": parsed,
    }


def criar_tarefas_da_reuniao(reuniao, acoes):
    """Cria tarefas automaticamente a partir das ações identificadas pela IA."""
    from datetime import timedelta
    from django.utils import timezone
    from apps.tarefas.models import Tarefa

    tarefas_criadas = []

    for acao in acoes:
        prazo_dias = acao.get("prazo_dias", 7)
        prioridade_map = {
            "baixa": "baixa",
            "media": "media",
            "alta": "alta",
            "urgente": "urgente",
        }

        # Definir responsável
        if acao.get("responsavel") == "cliente":
            # Se cliente tem acesso seller, atribuir a ele
            responsavel = reuniao.cliente.usuario or reuniao.consultor
        else:
            responsavel = reuniao.consultor

        tarefa = Tarefa.objects.create(
            cliente=reuniao.cliente,
            criado_por=reuniao.consultor,
            responsavel=responsavel,
            descricao=f"[IA] {acao['descricao']}",
            prioridade=prioridade_map.get(acao.get("prioridade", "media"), "media"),
            prazo=timezone.now().date() + timedelta(days=prazo_dias),
        )
        tarefas_criadas.append(tarefa)

    return tarefas_criadas
