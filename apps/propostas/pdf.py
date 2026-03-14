"""Geração de PDF da proposta comercial via WeasyPrint."""

import os
import re
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import escape


def _limpar_markdown(texto):
    """Remove formatação markdown."""
    if not texto:
        return ""
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.+?)\*', r'\1', texto)
    texto = re.sub(r'^#{1,3}\s*', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'^\s*[-*]\s+', '• ', texto, flags=re.MULTILINE)
    return texto


def _extrair_topicos(texto, max_topicos=5):
    """Extrai tópicos principais do texto para exibição compacta."""
    if not texto:
        return []
    texto = _limpar_markdown(texto)
    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
    topicos = []
    titulo_atual = None

    for linha in linhas:
        # Detectar título numerado: "1. Algo:" ou "1. Algo"
        match = re.match(r'^(\d+)\.\s*(.+?)(?:\s*:(.*))?$', linha)
        if match:
            if titulo_atual and len(topicos) < max_topicos:
                topicos.append(titulo_atual)
            desc = (match.group(3) or "").strip()
            titulo_atual = {"titulo": match.group(2).strip().rstrip(':'), "desc": desc}
        elif titulo_atual and not titulo_atual["desc"]:
            # Primeira linha após título vira descrição
            titulo_atual["desc"] = linha[:120]
        elif linha.startswith('•') and titulo_atual:
            if not titulo_atual["desc"]:
                titulo_atual["desc"] = linha.lstrip('• ')[:120]

    if titulo_atual and len(topicos) < max_topicos:
        topicos.append(titulo_atual)

    # Se não conseguiu extrair tópicos numerados, extrair frases do texto
    if not topicos:
        # Juntar tudo e separar por frases (ponto seguido de espaço e maiúscula)
        texto_inteiro = ' '.join(linhas)
        frases = re.split(r'(?<=\.)\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])', texto_inteiro)
        for frase in frases:
            frase = frase.strip()
            if len(frase) < 15:
                continue
            # Título = primeira frase curta, descrição = continuação
            if len(frase) <= 80:
                topicos.append({"titulo": frase, "desc": ""})
            else:
                # Cortar no primeiro ponto dentro dos primeiros 80 chars
                corte = frase.find('.', 20)
                if 0 < corte <= 80:
                    topicos.append({"titulo": frase[:corte + 1], "desc": frase[corte + 1:].strip()[:120]})
                else:
                    topicos.append({"titulo": frase[:70] + "...", "desc": ""})
            if len(topicos) >= max_topicos:
                break

    return topicos[:max_topicos]


def _formatar_valor(valor):
    """Formata valor monetário: 2500.00 → 2.500,00"""
    if not valor:
        return "0,00"
    try:
        v = Decimal(str(valor))
        inteiro = int(v)
        centavos = int((v - inteiro) * 100)
        # Formatar com ponto como separador de milhares
        inteiro_fmt = f"{inteiro:,}".replace(",", ".")
        return f"{inteiro_fmt},{centavos:02d}"
    except Exception:
        return str(valor)


def gerar_proposta_pdf(proposta):
    """Gera PDF profissional da proposta no formato de apresentação."""
    import weasyprint

    img_path = os.path.join(settings.BASE_DIR, "static", "img", "apresentacao")
    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo-branca.png")

    # Extrair tópicos compactos dos textos
    topicos_diagnostico = _extrair_topicos(proposta.diagnostico_ia, 4)
    topicos_proposicao = _extrair_topicos(proposta.proposicao_valor, 4)
    topicos_comercial = _extrair_topicos(proposta.proposta_comercial, 5)

    # Formatar valores monetários
    valor_mensalidade_fmt = _formatar_valor(proposta.valor_mensalidade)
    valor_setup_fmt = _formatar_valor(proposta.valor_setup)

    html_string = render_to_string("propostas/_report_pdf.html", {
        "proposta": proposta,
        "servicos": proposta.servicos_incluidos.select_related("servico").all(),
        "metricas": proposta.metricas or {},
        "img_path": img_path,
        "logo_path": logo_path,
        "topicos_diagnostico": topicos_diagnostico,
        "topicos_proposicao": topicos_proposicao,
        "topicos_comercial": topicos_comercial,
        "valor_mensalidade_fmt": valor_mensalidade_fmt,
        "valor_setup_fmt": valor_setup_fmt,
    })

    pdf = weasyprint.HTML(
        string=html_string,
        base_url=str(settings.BASE_DIR),
    ).write_pdf()

    nome = proposta.nome_display or "Proposta"
    filename = f"Proposta_3M_{nome}_{proposta.created_at.strftime('%Y%m%d')}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
