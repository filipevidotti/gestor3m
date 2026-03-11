"""
Seed v3: Novos checklists, treinamentos e calendário promocional.
Uso: python manage.py shell < scripts/seed_v3.py
"""
from datetime import date
from apps.accounts.models import User, Modulo
from apps.checklists.models import ChecklistCategory, ChecklistTemplate, ChecklistTemplateItem
from apps.treinamentos.models import Treinamento
from apps.calendario_promocional.models import DataPromocional

gestor = User.objects.filter(role="gestor").first()
cats = {c.nome: c for c in ChecklistCategory.objects.all()}

# Novas categorias se necessárias
for nome, desc, icone, ordem in [
    ("Full / Logística", "Mercado Envios Full e logística", "truck", 4),
    ("Vendas", "Primeiras vendas e conversão", "shopping-cart", 14),
    ("Conteúdo", "Clips, vídeos e conteúdo visual", "video", 15),
    ("Promoções", "Central de promoções e datas especiais", "tag", 16),
]:
    cats[nome], _ = ChecklistCategory.objects.update_or_create(
        nome=nome, defaults={"descricao": desc, "icone": icone, "ordem": ordem}
    )


def cl(nome, descricao, tipo, target, categoria, itens):
    tpl, _ = ChecklistTemplate.objects.update_or_create(
        nome=nome,
        defaults={"descricao": descricao, "tipo": tipo, "target_audience": target, "criado_por": gestor},
    )
    for i, (desc_item, instrucoes, req_ev, req_note) in enumerate(itens):
        ChecklistTemplateItem.objects.update_or_create(
            template=tpl, descricao=desc_item,
            defaults={"category": cats.get(categoria), "instrucoes": instrucoes, "ordem": i + 1, "requires_evidence": req_ev, "requires_note": req_note},
        )
    return tpl


# ══════════════════════════════════════════════════════════
# CHECKLISTS NOVOS
# ══════════════════════════════════════════════════════════

# 1. PRIMEIRO ENVIO FULL
cl("Primeiro Envio Full",
   "Passo a passo do primeiro envio de produtos para o centro de distribuição Full",
   "avulso", "consultant", "Full / Logística",
   [
       ("Verificar elegibilidade dos produtos", "Checar peso máximo (30kg), dimensões, categoria permitida. Produtos frágeis/perigosos não são aceitos.", False, True),
       ("Selecionar 10-20 produtos para primeiro envio", "Começar com top sellers que têm estoque. Não enviar catálogo inteiro de uma vez.", False, True),
       ("Criar unidades de envio no painel Full", "Agrupar produtos por envio. Seguir limite de caixas/unidades por remessa.", True, True),
       ("Imprimir etiquetas FNSKU", "Cada unidade deve ter etiqueta FNSKU individual colada no produto.", True, False),
       ("Preparar embalagem individual", "Cada produto deve estar embalado individualmente com proteção. Sem etiquetas externas de preço.", True, True),
       ("Verificar dimensões e peso declarados", "Pesar e medir cada produto. Diferenças causam cobrança extra e podem bloquear envio.", False, True),
       ("Embalar caixa de envio corretamente", "Caixa firme, sem espaço vazio (usar enchimento). Peso máximo da caixa de envio: 30kg.", True, True),
       ("Colar etiqueta da caixa de envio", "Etiqueta da remessa na parte de fora da caixa, legível e sem dobras.", True, False),
       ("Agendar coleta ou levar ao ponto de entrega", "Verificar prazo de entrega ao CD. Coleta gratuita ou drop-off em agência.", False, True),
       ("Acompanhar recebimento no painel Full", "Verificar se todos os produtos foram recebidos e estão disponíveis. Reportar divergências.", True, True),
       ("Verificar anúncios ativaram tag 'Full'", "Após recebimento, anúncios devem mostrar 'Enviado pelo Full'. Pode levar 24-48h.", True, False),
       ("Documentar custos do Full", "Anotar custo de armazenamento, picking e frete para calcular margem real.", False, True),
   ])

# 2. TRANSFORME PERGUNTAS EM VENDAS
cl("Transforme Perguntas em Vendas",
   "Como responder perguntas de forma que converta em venda",
   "avulso", "consultant", "Vendas",
   [
       ("Configurar notificações de perguntas", "Ativar notificação push no celular. Meta: responder em menos de 15 minutos.", False, False),
       ("Criar banco de respostas prontas", "10-20 respostas para perguntas mais frequentes. Personalizar com nome do produto.", False, True),
       ("Responder TODAS as perguntas pendentes", "Zero perguntas sem resposta. Perguntas antigas afastam compradores.", False, True),
       ("Incluir informação EXTRA na resposta", "Além de responder, mencionar: frete grátis, envio Full, garantia, diferencial.", False, True),
       ("Usar linguagem positiva e acolhedora", "Começar com 'Olá! Obrigado pelo interesse!'. Nunca ser seco ou rude.", False, True),
       ("Fazer cross-selling nas respostas", "Mencionar produtos complementares: 'Temos também o modelo X que combina com...'.", False, True),
       ("Criar senso de urgência", "'Últimas unidades em estoque!' ou 'Promoção válida até amanhã!'. Usar com moderação e honestidade.", False, True),
       ("Nunca informar dados de contato", "Regra do ML: não passar WhatsApp, email, telefone nas respostas. Risco de suspensão.", False, False),
       ("Responder perguntas sobre defeitos com transparência", "Se o produto tem limitações, informar. Evita reclamação depois.", False, True),
       ("Monitorar taxa de conversão pós-pergunta", "Verificar se quem pergunta está comprando. Se não, ajustar as respostas.", False, True),
       ("Revisar perguntas frequentes do anúncio", "Se a mesma pergunta aparece muito, a informação falta no anúncio. Atualizar descrição.", False, True),
   ])

# 3. ERROS COMUNS NO FULL
cl("Erros Comuns no Full — Evite!",
   "Checklist preventivo para evitar os erros mais frequentes no Mercado Envios Full",
   "avulso", "consultant", "Full / Logística",
   [
       ("Peso e dimensões corretos?", "ERRO COMUM: declarar peso/dimensão errado. Causa cobrança extra ou bloqueio. SEMPRE pesar e medir.", False, True),
       ("Produto embalado individualmente?", "ERRO: enviar sem embalar. Cada unidade precisa de embalagem individual com proteção.", True, True),
       ("Etiqueta FNSKU em cada unidade?", "ERRO: esquecer etiqueta ou colar no lugar errado. Sem etiqueta = produto perdido no CD.", True, False),
       ("Produto frágil com proteção extra?", "ERRO: enviar eletrônicos/vidro sem plástico bolha. Produto quebrado = prejuízo.", True, True),
       ("Verificou prazo de validade (se alimento/cosmético)?", "ERRO: enviar produtos vencidos ou com validade curta. ML recusa no recebimento.", False, True),
       ("Caixa de envio não excede 30kg?", "ERRO: caixa pesada demais. Máximo 30kg por caixa e 150cm de soma das 3 dimensões.", False, True),
       ("Não enviou produto proibido?", "ERRO: enviar baterias soltas, líquidos inflamáveis, produtos falsificados. Lista proibida no ML.", False, True),
       ("Conferiu quantidade antes de fechar caixa?", "ERRO: enviar quantidade diferente do declarado. Divergência gera suspensão.", False, True),
       ("Removeu etiquetas antigas da caixa?", "ERRO: caixa com código de barras antigo confunde a leitura no CD.", False, False),
       ("Verificou estoque virtual vs físico?", "ERRO: ter estoque Full zerado mas vender. Cancela pedido e prejudica reputação.", False, True),
   ])

# 4. CLIPS (VÍDEOS CURTOS)
cl("Clips do Mercado Livre",
   "Checklist para criar e otimizar Clips (vídeos curtos) no ML",
   "avulso", "consultant", "Conteúdo",
   [
       ("Verificar elegibilidade para Clips", "Conta precisa ter reputação verde e volume mínimo. Verificar no painel.", False, True),
       ("Selecionar 5-10 produtos para primeiros Clips", "Escolher produtos visuais, com demonstração clara. Evitar produtos genéricos.", False, True),
       ("Gravar vídeo vertical (9:16)", "Formato de Reels/TikTok. Máximo 60 segundos. Ideal: 15-30 segundos.", True, True),
       ("Mostrar produto em uso nos primeiros 3 segundos", "Captar atenção imediata. Nada de intro longa ou logo.", True, True),
       ("Adicionar texto/legendas no vídeo", "Muitas pessoas assistem sem som. Legendas aumentam engajamento.", True, True),
       ("Não incluir preço ou promoção no vídeo", "Regra do ML: vídeo não pode ter preço, link externo ou marca d'água.", False, False),
       ("Publicar Clip vinculado ao anúncio", "No app do ML, vincular o Clip ao anúncio correto.", True, True),
       ("Monitorar visualizações e cliques", "Acompanhar métricas por 7 dias. Clip bom tem taxa de clique > 3%.", False, True),
       ("Criar calendário de publicação", "Meta: 2-3 Clips por semana. Consistência é mais importante que volume.", False, True),
       ("Revisar Clips com baixa performance", "Clip com poucas views após 7 dias: trocar thumbnail ou regravar.", False, True),
   ])

# 5. CENTRAL DE PROMOÇÕES
cl("Central de Promoções do ML",
   "Como usar a Central de Promoções para aumentar vendas",
   "avulso", "consultant", "Promoções",
   [
       ("Acessar Central de Promoções no painel do ML", "Menu > Publicidade > Promoções. Verificar promoções disponíveis.", True, True),
       ("Verificar promoções ativas/disponíveis", "ML oferece promoções sazonais com inscrição. Verificar requisitos.", False, True),
       ("Calcular desconto mantendo margem positiva", "Desconto real mínimo exigido pelo ML (geralmente 10-20%). Calcular se margem ainda é positiva.", False, True),
       ("Selecionar produtos com bom estoque", "ERRO: inscrever produto com pouco estoque. Se vender tudo, perde posição de destaque.", False, True),
       ("Inscrever produtos dentro do prazo", "Cada promoção tem prazo de inscrição. Após fechar, não aceita mais.", False, True),
       ("Configurar preço 'De/Por' corretamente", "Preço 'De' deve ter sido praticado nos últimos 60 dias (regra ML).", False, True),
       ("Ativar frete grátis nos produtos da promoção", "Frete grátis + desconto = muito mais visibilidade.", False, True),
       ("Aumentar budget de Ads durante promoção", "Mais investimento em Ads durante promoções gera ROI melhor.", False, True),
       ("Monitorar vendas durante a promoção", "Acompanhar em tempo real. Ajustar estoque/preço se necessário.", False, True),
       ("Pós-promoção: analisar resultados", "Vendas, faturamento, margem real, novos clientes. Valeu a pena?", True, True),
       ("Documentar aprendizados", "O que funcionou? O que não? Qual produto vendeu mais? Registrar para próxima promoção.", False, True),
   ])

# 6. 10 PRIMEIRAS VENDAS
cl("10 Primeiras Vendas",
   "Guia passo a passo para conquistar as 10 primeiras vendas no ML",
   "avulso", "consultant", "Vendas",
   [
       ("Ter pelo menos 10 anúncios ativos", "Quantidade mínima para começar. Todos com fotos boas e preço competitivo.", False, True),
       ("Verificar se os preços estão na faixa do mercado", "Nas primeiras vendas, preço competitivo é mais importante que margem alta.", True, True),
       ("Ativar frete grátis onde possível", "Frete grátis é o maior acelerador de vendas para contas novas.", False, True),
       ("Configurar envio rápido (D+1 ou D+0)", "Prazo curto melhora posicionamento. Enviar no mesmo dia se possível.", False, True),
       ("Responder perguntas em menos de 1 hora", "Velocidade de resposta afeta o ranking. Ativar notificações no celular.", False, True),
       ("Compartilhar anúncios em redes sociais", "WhatsApp, Instagram, Facebook. Tráfego externo conta para o algoritmo.", False, True),
       ("Criar campanha de Product Ads", "Investir R$ 10-20/dia nos primeiros 15 dias. Ajuda a ganhar visibilidade.", False, True),
       ("Pedir para amigos/conhecidos avaliarem", "Compras legítimas de conhecidos. NUNCA fazer compras falsas (ML detecta).", False, True),
       ("Monitorar diariamente: visitas, perguntas, vendas", "Anotar métricas diárias para entender o que funciona.", False, True),
       ("Enviar RÁPIDO a primeira venda", "Primeira venda define a impressão. Enviar no mesmo dia, embalar com capricho.", False, False),
       ("Solicitar avaliação após entrega", "Pelo chat do ML, pedir feedback educadamente após confirmação de entrega.", False, False),
       ("Celebrar as 10 vendas!", "Marco importante! Conta começa a ganhar relevância após primeiras vendas.", False, False),
   ])

# 7. CHECKLIST BLACK FRIDAY
cl("Black Friday - Checklist Completo",
   "Preparação detalhada para a Black Friday no Mercado Livre",
   "avulso", "consultant", "Promoções",
   [
       ("Definir orçamento total para Black Friday (60 dias antes)", "Investimento em estoque + Ads + possíveis descontos. Definir com o seller.", False, True),
       ("Selecionar catálogo participante (45 dias antes)", "Top 30-50 produtos. Foco em: alta margem, bom estoque, boa conversão.", False, True),
       ("Fazer pedido extra de estoque (45 dias antes)", "Pedir 3-5x o volume normal dos produtos selecionados.", False, True),
       ("Enviar estoque extra para Full (30 dias antes)", "Full é essencial na BF. Envio no dia = desvantagem enorme.", True, True),
       ("Inscrever produtos na promoção oficial (verificar prazo)", "Acompanhar abertura de inscrição. Geralmente 20-30 dias antes.", True, True),
       ("Calcular desconto real mantendo margem", "Desconto real de pelo menos 15-20%. ML verifica histórico de preços.", True, True),
       ("Otimizar fotos e títulos dos produtos participantes", "Fotos profissionais, títulos com 'Black Friday' se permitido.", True, True),
       ("Configurar frete grátis em todos os participantes", "Frete grátis é obrigatório para competir na BF.", False, True),
       ("Aumentar budget de Ads (2-3x)", "Começar a aumentar 7 dias antes. No dia, ter budget 3-5x do normal.", False, True),
       ("Preparar equipe/operação para volume 5-10x", "Quem vai separar? Embalar? Enviar? Responder perguntas?", False, True),
       ("Testar operação com simulação de alto volume", "Simular dia de BF: 50 pedidos em 2h. Cronometrar cada etapa.", False, True),
       ("Preparar respostas rápidas para perguntas BF", "Templates: 'Desconto válido até...', 'Estoque limitado...', 'Frete grátis...'.", False, False),
       ("No dia: monitorar vendas em tempo real", "Acompanhar a cada hora. Ajustar preços/estoque conforme necessário.", False, True),
       ("No dia: monitorar concorrência", "Verificar preços dos concorrentes e ajustar se necessário.", False, True),
       ("Pós-BF (48h): analisar resultados completos", "Vendas totais, faturamento, margem real, novos clientes, estoque restante.", True, True),
       ("Pós-BF: atenção redobrada com reputação", "Volume alto = mais chance de problemas. Monitorar reclamações diariamente.", False, True),
   ])

print("✓ 7 novos checklists criados")

# ══════════════════════════════════════════════════════════
# TREINAMENTOS NOVOS
# ══════════════════════════════════════════════════════════

novos_treinos = [
    ("Reputação no ML - Guia Definitivo", "operacional",
     "Tudo sobre reputação: como funciona o termômetro, fatores que impactam, "
     "como subir de cor, como recuperar reputação vermelha/amarela. "
     "Estratégias práticas de prevenção e recuperação.", 90),

    ("Minha Página no Mercado Livre", "operacional",
     "Como personalizar e otimizar a Página do Vendedor (Minha Página): "
     "banner, descrição da loja, categorias, destaque de produtos, identidade visual. "
     "Impacto na conversão e confiança do comprador.", 45),

    ("Mercado Envios Flex - Guia Completo", "operacional",
     "Tudo sobre Flex: como funciona, requisitos, configuração, áreas de cobertura. "
     "Como entregar no mesmo dia. Quando usar Flex vs Full vs Coleta.", 60),

    ("Erros e Boas Práticas no Full", "operacional",
     "Os 10 erros mais comuns no Full e como evitar: peso errado, embalagem inadequada, "
     "etiquetas, produtos proibidos, controle de estoque virtual vs físico. "
     "Boas práticas para aprovação rápida no CD.", 60),

    ("Black Friday no ML - Estratégia Completa", "estrategica",
     "Preparação completa para Black Friday: timeline de 60 dias, seleção de produtos, "
     "cálculo de desconto, estoque, Full, Ads, equipe, operação. "
     "Cases de sucesso e erros fatais. Análise pós-evento.", 120),

    ("Clips no Mercado Livre", "operacional",
     "Como criar Clips (vídeos curtos) que vendem: formato, duração, conteúdo. "
     "Como gravar com celular, editar e publicar. Métricas de sucesso. "
     "Exemplos de Clips que mais convertem por categoria.", 60),

    ("Central de Promoções - Como Usar", "estrategica",
     "Guia completo da Central de Promoções do ML: tipos de promoção, "
     "como se inscrever, requisitos, cálculo de preço De/Por, "
     "estratégias para maximizar vendas em promoções oficiais.", 60),

    ("Transforme Perguntas em Vendas", "operacional",
     "Técnicas avançadas para converter perguntas em vendas: respostas rápidas, "
     "cross-selling, senso de urgência, linguagem persuasiva. "
     "Banco de respostas prontas por categoria. Métricas de conversão.", 45),

    ("10 Primeiras Vendas no ML", "operacional",
     "Estratégia completa para sellers iniciantes conquistarem as primeiras 10 vendas: "
     "precificação agressiva, frete grátis, Ads iniciais, resposta rápida. "
     "Como construir reputação do zero.", 60),

    ("Calendário Promocional do ML", "estrategica",
     "Todas as datas importantes do e-commerce e ML: quando acontecem, "
     "como se preparar, quando inscrever, quanto investir. "
     "Planejamento anual com antecedência ideal para cada data.", 60),

    ("Preparação para Datas Especiais", "estrategica",
     "Framework completo de preparação: 60 dias antes até pós-evento. "
     "Estoque, preço, Full, Ads, equipe. Aplicável para qualquer data: "
     "Black Friday, Hot Sale, Dia das Mães, Natal, etc.", 75),

    ("Como Usar Cupons e Ofertas Relâmpago", "estrategica",
     "Ferramentas de desconto do ML: cupons do vendedor, ofertas relâmpago, "
     "ofertas do dia. Quando usar cada um, como configurar, impacto nas vendas.", 45),

    ("Onboarding: Primeiros 30 Dias do Seller", "operacional",
     "O que o seller precisa aprender nos primeiros 30 dias: "
     "conta, anúncios, fotos, frete, reputação, perguntas. "
     "Checklist visual e cronograma dia a dia.", 90),
]

for titulo, cat, desc, duracao in novos_treinos:
    Treinamento.objects.update_or_create(
        titulo=titulo,
        defaults={"categoria": cat, "descricao": desc, "duracao_minutos": duracao},
    )

print(f"✓ {len(novos_treinos)} novos treinamentos criados")

# ══════════════════════════════════════════════════════════
# CALENDÁRIO PROMOCIONAL 2026
# ══════════════════════════════════════════════════════════

datas_2026 = [
    # Oficiais ML
    ("Liquidação de Janeiro", "oficial_ml", "media", date(2026, 1, 5), date(2026, 1, 15), "#F59E0B",
     "Primeira liquidação do ano. Foco em queima de estoque de Natal.", 20,
     "Boa oportunidade para vender estoque parado do ano anterior com descontos reais."),

    ("Volta às Aulas", "sazonal", "alta", date(2026, 1, 20), date(2026, 2, 10), "#3B82F6",
     "Material escolar, mochilas, eletrônicos para estudantes.", 30,
     "Foco em: notebooks, tablets, mochilas, material escolar, organização."),

    ("Carnaval", "sazonal", "baixa", date(2026, 2, 14), date(2026, 2, 17), "#EC4899",
     "Fantasias, acessórios, bebidas, coolers.", 15,
     "Nicho específico. Bom para sellers de moda e acessórios."),

    ("Dia da Mulher", "sazonal", "media", date(2026, 3, 1), date(2026, 3, 8), "#EC4899",
     "Presentes, beleza, moda feminina, autocuidado.", 20,
     "Boa data para sellers de beleza, moda e acessórios."),

    ("Dia do Consumidor", "oficial_ml", "critica", date(2026, 3, 10), date(2026, 3, 15), "#FE8103",
     "Uma das maiores datas do ML! Descontos comparáveis à Black Friday.", 45,
     "MUITO IMPORTANTE: é a 'Black Friday do primeiro semestre'. Preparar estoque, Ads e Full com antecedência."),

    ("Páscoa", "sazonal", "media", date(2026, 4, 1), date(2026, 4, 5), "#A855F7",
     "Chocolates, brinquedos, presentes infantis.", 20,
     "Foco em presentes e brinquedos. Chocolates vendem muito online."),

    ("Dia das Mães", "sazonal", "critica", date(2026, 5, 1), date(2026, 5, 10), "#EC4899",
     "Segunda maior data do varejo! Presentes, eletrônicos, beleza, moda.", 45,
     "DATA CRÍTICA: perde só para Natal e BF. Categorias: perfumaria, moda, eletrônicos, eletrodomésticos."),

    ("Dia dos Namorados", "sazonal", "alta", date(2026, 6, 1), date(2026, 6, 12), "#EF4444",
     "Presentes, perfumes, acessórios, experiências.", 30,
     "Foco em presentes personalizados, perfumaria, moda e eletrônicos."),

    ("Hot Sale ML", "oficial_ml", "critica", date(2026, 6, 22), date(2026, 6, 28), "#FE8103",
     "Mega promoção oficial do Mercado Livre! Descontos em todas as categorias.", 45,
     "EVENTO OFICIAL ML: inscrição obrigatória. Muito tráfego no site. Preparar Full e Ads."),

    ("Dia dos Pais", "sazonal", "alta", date(2026, 8, 1), date(2026, 8, 9), "#3B82F6",
     "Ferramentas, eletrônicos, moda masculina, esportes.", 30,
     "Categorias fortes: eletrônicos, ferramentas, automotivo, moda masculina."),

    ("Dia das Crianças", "sazonal", "alta", date(2026, 10, 1), date(2026, 10, 12), "#22C55E",
     "Brinquedos, games, eletrônicos infantis, roupas.", 30,
     "Brinquedos e games dominam. Preparar estoque com antecedência."),

    ("Esquenta Black Friday", "oficial_ml", "alta", date(2026, 11, 1), date(2026, 11, 20), "#F59E0B",
     "Semanas de promoções antes da BF. Aquecimento de vendas.", 30,
     "Já começar a vender com descontos para ganhar impulso antes da BF."),

    ("Black Friday", "oficial_ml", "critica", date(2026, 11, 27), date(2026, 11, 29), "#0F172A",
     "A MAIOR data do e-commerce! Descontos reais, volume 10-20x.", 60,
     "PREPARAÇÃO MÁXIMA: estoque 5x, Full obrigatório, Ads 5x, equipe extra. Esta data DEFINE o ano."),

    ("Cyber Monday", "oficial_ml", "alta", date(2026, 11, 30), date(2026, 12, 1), "#6366F1",
     "Extensão da BF focada em eletrônicos e tecnologia.", 15,
     "Boa para vender o que sobrou da BF com descontos adicionais."),

    ("Natal", "sazonal", "critica", date(2026, 12, 1), date(2026, 12, 23), "#22C55E",
     "Maior período de vendas do ano! Presentes de todas as categorias.", 45,
     "Atenção ao PRAZO: última data de envio para chegar antes do Natal. Full resolve isso."),

    ("Liquidação de Fim de Ano", "oficial_ml", "media", date(2026, 12, 26), date(2026, 12, 31), "#F59E0B",
     "Queima de estoque pós-Natal. Descontos agressivos.", 10,
     "Boa para limpar estoque que sobrou do Natal. Descontos de 30-50%."),
]

for nome, tipo, imp, dt_ini, dt_fim, cor, desc, antec, dicas in datas_2026:
    DataPromocional.objects.update_or_create(
        nome=nome,
        data_inicio=dt_ini,
        defaults={
            "tipo": tipo,
            "importancia": imp,
            "data_fim": dt_fim,
            "cor": cor,
            "descricao": desc,
            "dicas": dicas,
            "antecedencia_preparo_dias": antec,
        },
    )

print(f"✓ {len(datas_2026)} datas promocionais 2026 criadas")

# ── Módulo Calendário ──
Modulo.objects.update_or_create(
    slug="calendario", defaults={"nome": "Calendário Promocional", "icone": "calendar-days", "ordem": 26}
)

# Atribuir módulo aos consultores
mod_cal = Modulo.objects.get(slug="calendario")
for u in User.objects.filter(role__in=["consultor", "gestor"]):
    u.modulos.add(mod_cal)

print("✓ Módulo calendário criado e atribuído")

# ── Resumo final ──
total_cl = ChecklistTemplate.objects.count()
total_it = ChecklistTemplateItem.objects.count()
total_tr = Treinamento.objects.count()
total_dp = DataPromocional.objects.count()

print(f"\n{'=' * 50}")
print(f"📋 Total Checklists: {total_cl} ({total_it} itens)")
print(f"🎓 Total Treinamentos: {total_tr}")
print(f"📅 Total Datas Promocionais: {total_dp}")
print(f"{'=' * 50}")
