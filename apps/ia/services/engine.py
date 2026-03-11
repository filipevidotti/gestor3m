"""
Agno AI Engine — Motor de IA da 3M Consultoria.

Usa Agno framework com providers configuráveis (Claude/OpenAI).
Knowledge base alimentada por diagnósticos, reuniões e artigos.
"""
import json
import logging
import time

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)

# Instruções-base do consultor IA
SYSTEM_INSTRUCTIONS = """Você é o Consultor IA da 3M Consultoria, especializado em consultoria para vendedores do Mercado Livre.

Seu papel é analisar dados de clientes (vendedores ML) e fornecer recomendações práticas.

## Áreas de Conhecimento
- **Vendas**: Estratégias de venda, precificação, competitividade
- **Logística**: FULL, envios, prazos, custos
- **Reputação**: Gestão de reclamações, métricas, recuperação
- **ADS**: Mercado Ads, Product Ads, campanhas
- **SEO**: Títulos, fichas técnicas, palavras-chave
- **Catálogo**: Qualidade de anúncios, fotos, descrições

## Regras
- Sempre responda em português brasileiro
- Seja direto e prático — o consultor precisa de ações, não teoria
- Use dados concretos quando disponíveis (scores, percentuais, tendências)
- Priorize ações por impacto (alto impacto primeiro)
- Formate respostas em JSON quando solicitado
"""


def get_provider_config():
    """Retorna configuração do provider de IA."""
    provider = Configuracao.get("IA_PROVIDER", "claude")
    if provider == "openai":
        return {
            "provider": "openai",
            "api_key": Configuracao.get("OPENAI_API_KEY"),
            "model": Configuracao.get("OPENAI_MODEL", "gpt-4o"),
        }
    return {
        "provider": "claude",
        "api_key": Configuracao.get("ANTHROPIC_API_KEY"),
        "model": Configuracao.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
    }


def _call_with_agno(prompt, context="", response_format="json"):
    """Chama IA usando Agno framework."""
    config = get_provider_config()
    start = time.time()

    try:
        from agno.agent import Agent
        from agno.models.anthropic import Claude as AgnoClaude
        from agno.models.openai import OpenAIChat

        if config["provider"] == "openai":
            model = OpenAIChat(id=config["model"], api_key=config["api_key"])
        else:
            model = AgnoClaude(id=config["model"], api_key=config["api_key"])

        agent = Agent(
            model=model,
            instructions=[SYSTEM_INSTRUCTIONS],
            markdown=True,
        )

        full_prompt = f"{context}\n\n---\n\n{prompt}" if context else prompt
        response = agent.run(full_prompt)
        content = response.content if hasattr(response, "content") else str(response)

        duration_ms = int((time.time() - start) * 1000)

        return {
            "success": True,
            "content": content,
            "provider": config["provider"],
            "model": config["model"],
            "duration_ms": duration_ms,
        }

    except ImportError:
        logger.warning("Agno não instalado, usando fallback direto via API")
        return _call_direct_api(prompt, context, config)
    except Exception as e:
        logger.error(f"Erro Agno: {e}")
        return _call_direct_api(prompt, context, config)


def _call_direct_api(prompt, context, config):
    """Fallback: chama API diretamente sem Agno."""
    start = time.time()

    try:
        full_prompt = f"{context}\n\n---\n\n{prompt}" if context else prompt

        if config["provider"] == "openai":
            import openai
            client = openai.OpenAI(api_key=config["api_key"])
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": full_prompt},
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0
        else:
            import anthropic
            client = anthropic.Anthropic(api_key=config["api_key"])
            response = client.messages.create(
                model=config["model"],
                max_tokens=4096,
                system=SYSTEM_INSTRUCTIONS,
                messages=[{"role": "user", "content": full_prompt}],
            )
            content = response.content[0].text
            tokens_in = response.usage.input_tokens if response.usage else 0
            tokens_out = response.usage.output_tokens if response.usage else 0

        duration_ms = int((time.time() - start) * 1000)

        return {
            "success": True,
            "content": content,
            "provider": config["provider"],
            "model": config["model"],
            "duration_ms": duration_ms,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
        }

    except Exception as e:
        logger.error(f"Erro API direta ({config['provider']}): {e}")
        return {
            "success": False,
            "error": str(e),
            "provider": config["provider"],
            "model": config["model"],
            "duration_ms": int((time.time() - start) * 1000),
        }


def chamar_ia(prompt, context="", tipo_analise="", cliente=None, consultor=None):
    """
    Função principal para chamar a IA.
    Registra no histórico e retorna resultado.
    """
    from apps.ia.models import HistoricoAnalise

    result = _call_with_agno(prompt, context)

    # Registrar no histórico
    try:
        HistoricoAnalise.objects.create(
            tipo=tipo_analise or "insight",
            cliente=cliente,
            consultor=consultor,
            provider=result.get("provider", ""),
            modelo=result.get("model", ""),
            prompt_resumo=prompt[:500],
            resposta_resumo=result.get("content", result.get("error", ""))[:500],
            resposta_json=result if result.get("success") else {},
            tokens_input=result.get("tokens_input", 0),
            tokens_output=result.get("tokens_output", 0),
            duracao_ms=result.get("duration_ms", 0),
            sucesso=result.get("success", False),
            erro=result.get("error", ""),
        )
    except Exception as e:
        logger.error(f"Erro ao salvar histórico IA: {e}")

    return result


def extrair_json(content):
    """Extrai JSON de uma resposta que pode conter markdown."""
    if not content:
        return None

    # Tenta parse direto
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        pass

    # Tenta extrair de bloco ```json
    import re
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Tenta encontrar { ... } ou [ ... ]
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = content.find(start_char)
        end = content.rfind(end_char)
        if start != -1 and end > start:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass

    return None
