"""Motor de cálculo de métricas para propostas comerciais."""

from decimal import Decimal


def calcular_metricas(proposta):
    """
    Calcula métricas de potencial com base nas respostas do questionário.

    Retorna dict com:
    - ganho_conversao: potencial de aumento de conversão (R$/mês)
    - economia_ads: economia potencial em Ads (R$/mês)
    - economia_logistica: economia em logística (R$/mês)
    - ganho_precificacao: ganho com precificação correta (R$/mês)
    - economia_tempo: horas economizadas / semana
    - score_total: score de 0-100 (maturidade da operação)
    - potencial_total: soma dos ganhos potenciais (R$/mês)
    """
    r = proposta.respostas or {}

    b1 = r.get("bloco_1", {})
    b2 = r.get("bloco_2", {})
    b3 = r.get("bloco_3", {})
    b4 = r.get("bloco_4", {})
    b5 = r.get("bloco_5", {})
    b6 = r.get("bloco_6", {})
    b7 = r.get("bloco_7", {})
    b9 = r.get("bloco_9", {})

    faturamento = _to_decimal(b1.get("faturamento_mensal", 0))

    # ─── 1. Ganho de Conversão ────────────────────────────
    taxa_conversao = _to_decimal(b2.get("taxa_conversao", 0))
    titulo_otimizado = b2.get("titulo_otimizado", "nao")
    fotos_profissionais = b2.get("fotos_profissionais", "nao")
    descricao_html = b2.get("descricao_html", "nao")

    # Estimativa: títulos + fotos + descrição podem aumentar conversão em 2-5%
    pontos_conversao = 0
    if titulo_otimizado != "sim":
        pontos_conversao += 1.5  # +1.5% conversão
    if fotos_profissionais != "sim":
        pontos_conversao += 2.0  # +2% conversão
    if descricao_html != "sim":
        pontos_conversao += 0.5  # +0.5% conversão

    # Ganho = faturamento * (aumento % / taxa atual %)
    if taxa_conversao > 0:
        ganho_conversao = faturamento * (Decimal(str(pontos_conversao)) / taxa_conversao)
    else:
        ganho_conversao = faturamento * Decimal("0.15")  # estimativa 15% do faturamento

    # ─── 2. Economia em Ads ───────────────────────────────
    investimento_ads = _to_decimal(b3.get("investimento_ads", 0))
    acos_atual = _to_decimal(b3.get("acos_atual", 0))
    sabe_otimizar = b3.get("sabe_otimizar_ads", "nao")

    # ACOS ideal ~8%. Se acima, economia = investimento * (acos_atual - 8) / acos_atual
    acos_ideal = Decimal("8.0")
    if acos_atual > acos_ideal and investimento_ads > 0:
        economia_ads = investimento_ads * ((acos_atual - acos_ideal) / acos_atual)
    elif sabe_otimizar != "sim" and investimento_ads > 0:
        economia_ads = investimento_ads * Decimal("0.20")  # 20% de economia estimada
    else:
        economia_ads = Decimal("0")

    # ─── 3. Economia em Logística ─────────────────────────
    custo_frete = _to_decimal(b4.get("custo_frete", 0))
    taxa_atraso = _to_decimal(b4.get("taxa_atraso", 0))
    tipo_envio = b4.get("tipo_envio", "")

    # Se não usa Full e tem atraso, migrar para Full pode economizar
    pedidos_estimados = faturamento / Decimal("80") if faturamento > 0 else Decimal("0")  # ticket médio ~R$80
    economia_logistica = Decimal("0")
    if tipo_envio != "full" and taxa_atraso > 2:
        economia_logistica = pedidos_estimados * Decimal("3.0")  # ~R$3 por pedido
    if custo_frete > 15 and tipo_envio != "full":
        economia_logistica += pedidos_estimados * (custo_frete - Decimal("12"))  # delta vs Full

    # ─── 4. Ganho com Precificação ────────────────────────
    margem_liquida = _to_decimal(b6.get("margem_liquida", 0))
    planilha_preco = b6.get("planilha_preco", "nao")
    custos_completos = b6.get("custos_completos", "nao")

    ganho_precificacao = Decimal("0")
    if planilha_preco != "sim" or custos_completos != "sim":
        # Estimativa: precificação correta pode agregar 3-8% de margem
        incremento = Decimal("5.0") if planilha_preco == "nao" else Decimal("2.0")
        ganho_precificacao = faturamento * (incremento / Decimal("100"))

    # ─── 5. Economia de Tempo ─────────────────────────────
    horas_semanais = _to_decimal(b7.get("horas_semanais", 0))
    usa_erp = b7.get("usa_erp", "nao")

    economia_tempo = Decimal("0")
    if usa_erp != "sim":
        economia_tempo += Decimal("8")  # 8h/semana com ERP
    if horas_semanais > 40:
        economia_tempo += (horas_semanais - Decimal("40")) * Decimal("0.5")

    # ─── Score de Maturidade (0-100) ──────────────────────
    score = 0
    # Anúncios (max 25)
    if titulo_otimizado == "sim":
        score += 8
    elif titulo_otimizado == "parcial":
        score += 4
    if fotos_profissionais == "sim":
        score += 9
    elif fotos_profissionais == "parcial":
        score += 4
    if descricao_html == "sim":
        score += 8

    # Ads (max 15)
    if b3.get("usa_ads") == "sim":
        score += 5
    if sabe_otimizar == "sim":
        score += 5
    elif sabe_otimizar == "parcial":
        score += 3
    if acos_atual > 0 and acos_atual <= 10:
        score += 5

    # Logística (max 15)
    if tipo_envio == "full":
        score += 10
    elif tipo_envio == "flex":
        score += 5
    if taxa_atraso < 2:
        score += 5

    # Atendimento (max 15)
    reputacao = b5.get("reputacao", "")
    if reputacao == "verde":
        score += 10
    elif reputacao == "amarelo":
        score += 5
    taxa_reclamacoes = _to_decimal(b5.get("taxa_reclamacoes", 0))
    if taxa_reclamacoes < 2:
        score += 5

    # Precificação (max 15)
    if planilha_preco == "sim":
        score += 8
    elif planilha_preco == "basica":
        score += 4
    if custos_completos == "sim":
        score += 7
    elif custos_completos == "parcial":
        score += 3

    # Gestão (max 15)
    if usa_erp == "sim":
        score += 10
    elif usa_erp == "basico":
        score += 5
    if horas_semanais > 0 and horas_semanais <= 40:
        score += 5

    score = min(score, 100)

    # ─── Potencial Total ──────────────────────────────────
    potencial_total = ganho_conversao + economia_ads + economia_logistica + ganho_precificacao

    metricas = {
        "ganho_conversao": float(round(ganho_conversao, 2)),
        "economia_ads": float(round(economia_ads, 2)),
        "economia_logistica": float(round(economia_logistica, 2)),
        "ganho_precificacao": float(round(ganho_precificacao, 2)),
        "economia_tempo": float(round(economia_tempo, 1)),
        "score_total": score,
        "potencial_total": float(round(potencial_total, 2)),
        "faturamento_atual": float(faturamento),
        "meta_faturamento": float(_to_decimal(b9.get("meta_faturamento", 0))),
    }

    return metricas


def _to_decimal(value):
    """Converte valor para Decimal, retornando 0 se inválido."""
    try:
        return Decimal(str(value)) if value else Decimal("0")
    except Exception:
        return Decimal("0")
