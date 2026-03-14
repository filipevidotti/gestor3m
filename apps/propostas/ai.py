"""Integração OpenAI para geração de textos da proposta comercial."""

import logging

from openai import OpenAI

from apps.core.models import Configuracao

logger = logging.getLogger(__name__)


def _get_client():
    """Retorna cliente OpenAI com chave do banco de dados."""
    api_key = Configuracao.get("OPENAI_API_KEY", "")
    return OpenAI(api_key=api_key)


MODEL = "gpt-4o"


def gerar_diagnostico(proposta) -> str:
    """Gera diagnóstico da operação do seller com base no questionário."""
    respostas = proposta.respostas or {}
    metricas = proposta.metricas or {}

    prompt = f"""Você é um consultor especialista em e-commerce e marketplaces (Mercado Livre, Shopee, Amazon).

Analise os dados abaixo de um seller e gere um DIAGNÓSTICO PROFISSIONAL da operação.

## Dados do Seller
- Tipo: {proposta.get_tipo_seller_display()}
- Marketplace: {proposta.get_marketplace_display()}
- Nome: {proposta.nome_display}

## Respostas do Questionário
{_formatar_respostas(respostas)}

## Métricas Calculadas
- Score de Maturidade: {metricas.get('score_total', 0)}/100
- Potencial de ganho mensal: R$ {metricas.get('potencial_total', 0):,.2f}
- Ganho conversão: R$ {metricas.get('ganho_conversao', 0):,.2f}
- Economia Ads: R$ {metricas.get('economia_ads', 0):,.2f}
- Economia logística: R$ {metricas.get('economia_logistica', 0):,.2f}
- Ganho precificação: R$ {metricas.get('ganho_precificacao', 0):,.2f}

## Instruções
1. Escreva em tom profissional mas acessível
2. Aponte os PONTOS FORTES da operação
3. Identifique as VULNERABILIDADES e GAPS
4. Dê NÚMEROS concretos quando possível
5. Máximo 400 palavras
6. NÃO use markdown, escreva em texto corrido com parágrafos
7. Escreva em português do Brasil"""

    return _chamar_openai(prompt)


def gerar_proposicao_valor(proposta) -> str:
    """Gera a proposição de valor da 3M Consultoria para este seller."""
    respostas = proposta.respostas or {}
    metricas = proposta.metricas or {}

    prompt = f"""Você é o redator da 3M Consultoria, especializada em consultoria para sellers de marketplace.

Com base no diagnóstico do seller, gere uma PROPOSIÇÃO DE VALOR personalizada.

## Contexto
- Seller: {proposta.nome_display}
- Tipo: {proposta.get_tipo_seller_display()}
- Marketplace: {proposta.get_marketplace_display()}
- Score atual: {metricas.get('score_total', 0)}/100
- Potencial mensal: R$ {metricas.get('potencial_total', 0):,.2f}

## Dados
{_formatar_respostas(respostas)}

## Instruções
1. Explique POR QUE a 3M Consultoria é a melhor escolha
2. Conecte cada serviço ao GAP identificado no diagnóstico
3. Mostre o ROI potencial da consultoria
4. Tom persuasivo mas honesto, sem promessas irreais
5. Máximo 300 palavras
6. NÃO use markdown, escreva em texto corrido com parágrafos
7. Escreva em português do Brasil"""

    return _chamar_openai(prompt)


def gerar_proposta_comercial(proposta) -> str:
    """Gera o texto da proposta comercial com escopo de trabalho."""
    respostas = proposta.respostas or {}
    metricas = proposta.metricas or {}

    objetivo = respostas.get("bloco_9", {}).get("objetivo_principal", "escalar")

    prompt = f"""Você é o diretor comercial da 3M Consultoria.

Gere o texto da PROPOSTA COMERCIAL detalhada para este seller.

## Contexto
- Seller: {proposta.nome_display}
- Tipo: {proposta.get_tipo_seller_display()}
- Marketplace: {proposta.get_marketplace_display()}
- Objetivo principal: {objetivo}
- Faturamento atual: R$ {metricas.get('faturamento_atual', 0):,.2f}
- Meta: R$ {metricas.get('meta_faturamento', 0):,.2f}

## Dados
{_formatar_respostas(respostas)}

## Instruções
1. Descreva o ESCOPO DE TRABALHO em 4-6 frentes de atuação
2. Para cada frente, liste 2-3 atividades concretas
3. Inclua CRONOGRAMA sugerido (primeiros 3 meses)
4. Mencione reuniões semanais de acompanhamento
5. Inclua expectativa de RESULTADOS por frente
6. Tom executivo e direto
7. Máximo 500 palavras
8. NÃO use markdown, escreva em texto corrido com parágrafos numerados
9. Escreva em português do Brasil"""

    return _chamar_openai(prompt)


def _chamar_openai(prompt: str) -> str:
    """Chama a API OpenAI e retorna o texto gerado."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Você é um consultor especialista em e-commerce e marketplaces. Responda sempre em português do Brasil."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Erro ao chamar OpenAI: {e}")
        return f"[Erro ao gerar texto: {e}]"


def _formatar_respostas(respostas: dict) -> str:
    """Formata respostas do questionário para o prompt."""
    linhas = []
    labels = {
        "bloco_1": "Estrutura da Operação",
        "bloco_2": "Qualidade dos Anúncios",
        "bloco_3": "Publicidade (Ads)",
        "bloco_4": "Logística",
        "bloco_5": "Atendimento",
        "bloco_6": "Precificação",
        "bloco_7": "Gestão e Processos",
        "bloco_8": "Análise Competitiva",
        "bloco_9": "Objetivos",
        "bloco_10": "Dores e Observações",
    }
    for bloco_key in sorted(respostas.keys()):
        dados = respostas[bloco_key]
        if not isinstance(dados, dict):
            continue
        titulo = labels.get(bloco_key, bloco_key)
        linhas.append(f"\n### {titulo}")
        for campo, valor in dados.items():
            if valor:
                linhas.append(f"- {campo.replace('_', ' ').title()}: {valor}")
    return "\n".join(linhas)
