"""
Seed de conteúdo completo para consultoria Mercado Livre.
Checklists, treinamentos, agenda, etapas pipeline, templates de jornada.
Uso: python manage.py shell < scripts/seed_content.py
"""
from datetime import time
from apps.accounts.models import User

# ══════════════════════════════════════════════════════════
# AGENDA: ConfiguracaoAgenda + Horários para cada consultor
# ══════════════════════════════════════════════════════════
from apps.agenda.models import ConfiguracaoAgenda, HorarioTrabalho

for consultor in User.objects.filter(role="consultor"):
    slug = consultor.username.replace(" ", "-").lower()
    config, created = ConfiguracaoAgenda.objects.update_or_create(
        consultor=consultor,
        defaults={
            "slug": slug,
            "titulo": f"Agenda - {consultor.get_full_name()}",
            "descricao": f"Agende uma reunião com {consultor.first_name} - 3M Consultoria",
            "duracao_padrao": 60,
            "antecedencia_minima": 24,
            "dias_visiveis": 14,
        },
    )
    if created:
        # Seg a Sex 9h-18h
        for dia in range(5):  # 0=seg, 4=sex
            HorarioTrabalho.objects.get_or_create(
                config=config,
                dia_semana=dia,
                defaults={"hora_inicio": time(9, 0), "hora_fim": time(18, 0), "ativo": True},
            )
    print(f"  ✓ Agenda: {consultor.get_full_name()} → /agenda/c/{slug}/")

print("✓ Configurações de agenda criadas")

# ══════════════════════════════════════════════════════════
# CHECKLISTS: Categorias + Templates + Itens
# ══════════════════════════════════════════════════════════
from apps.checklists.models import ChecklistCategory, ChecklistTemplate, ChecklistTemplateItem

gestor = User.objects.filter(role="gestor").first()

# ── Categorias ──
cats = {}
cats_data = [
    ("Onboarding", "Processos de entrada do novo seller", "rocket-launch", 1),
    ("Conta ML", "Configuração e saúde da conta", "user-circle", 2),
    ("Anúncios", "Qualidade e otimização de anúncios", "photo", 3),
    ("Logística", "Envio, Full e processos logísticos", "truck", 4),
    ("Reputação", "Saúde da reputação e atendimento", "shield-check", 5),
    ("Marketing/Ads", "Campanhas e estratégias de marketing", "megaphone", 6),
    ("Financeiro", "Precificação, custos e margem", "currency-dollar", 7),
    ("Acompanhamento Mensal", "Revisão mensal periódica", "calendar", 8),
    ("Escala", "Processos para crescimento", "arrow-trending-up", 9),
]
for nome, desc, icone, ordem in cats_data:
    cats[nome], _ = ChecklistCategory.objects.update_or_create(
        nome=nome, defaults={"descricao": desc, "icone": icone, "ordem": ordem}
    )
print(f"✓ {len(cats)} categorias de checklist")

# ── Templates de Checklist ──

def criar_checklist(nome, descricao, tipo, target, categoria, itens):
    tpl, _ = ChecklistTemplate.objects.update_or_create(
        nome=nome,
        defaults={"descricao": descricao, "tipo": tipo, "target_audience": target, "criado_por": gestor},
    )
    for i, (desc_item, instrucoes, req_evidence, req_note) in enumerate(itens):
        ChecklistTemplateItem.objects.update_or_create(
            template=tpl, descricao=desc_item,
            defaults={
                "category": cats.get(categoria),
                "instrucoes": instrucoes,
                "ordem": i + 1,
                "requires_evidence": req_evidence,
                "requires_note": req_note,
            },
        )
    return tpl

# 1. ONBOARDING COMPLETO
criar_checklist(
    "Onboarding Completo do Seller",
    "Checklist completo para entrada de novo seller na consultoria",
    "avulso", "consultant", "Onboarding",
    [
        ("Coletar dados de acesso ao Mercado Livre", "Solicitar login e senha ou convite de acesso à conta. Verificar se o acesso funciona.", False, True),
        ("Verificar dados cadastrais da conta ML", "Nome, CPF/CNPJ, endereço, dados bancários. Conferir se está tudo correto.", False, True),
        ("Analisar reputação atual", "Verificar cor da reputação, % de reclamações, tempo de resposta, cancelamentos.", True, True),
        ("Mapear catálogo de produtos", "Listar categorias, quantidade de anúncios, top vendidos, anúncios pausados.", True, True),
        ("Avaliar fotos dos Top 20 anúncios", "Verificar qualidade, fundo branco, múltiplos ângulos, vídeo. Anotar quais precisam melhorar.", True, True),
        ("Avaliar títulos dos Top 20 anúncios", "Verificar se contêm palavras-chave relevantes, marca, modelo. Anotar quais otimizar.", False, True),
        ("Avaliar descrições dos Top 20 anúncios", "Verificar se são completas, têm especificações técnicas, perguntas frequentes.", False, True),
        ("Verificar configuração de frete", "Mercado Envios, Full, Flex, Coleta. Avaliar melhor opção para o seller.", False, True),
        ("Verificar configuração do Mercado Pago", "Saldo, taxas, antecipação, dados bancários para saque.", False, True),
        ("Analisar concorrentes principais", "Identificar 3-5 concorrentes, comparar preços, fotos, reputação.", True, True),
        ("Criar plano de ação inicial (30 dias)", "Definir prioridades e metas para os primeiros 30 dias.", False, True),
        ("Agendar reunião de treinamento inicial", "Marcar na agenda a primeira sessão de treinamento.", False, False),
        ("Enviar kit de boas-vindas por WhatsApp", "Enviar mensagem de boas-vindas com links úteis e cronograma.", False, False),
        ("Preencher diagnóstico inicial", "Aplicar o Diagnóstico 360° completo no sistema.", False, False),
    ],
)

# 2. AUDITORIA DE ANÚNCIOS
criar_checklist(
    "Auditoria de Anúncios",
    "Revisão completa da qualidade dos anúncios do seller",
    "avulso", "consultant", "Anúncios",
    [
        ("Verificar títulos com palavras-chave corretas", "Usar ferramenta de tendências do ML para validar termos. Máximo 60 caracteres.", False, True),
        ("Verificar fichas técnicas preenchidas", "Todos os campos obrigatórios e opcionais relevantes devem estar preenchidos.", True, True),
        ("Avaliar qualidade das fotos (fundo branco)", "Mínimo 6 fotos, fundo branco, sem marca d'água, alta resolução.", True, True),
        ("Verificar se há vídeo nos anúncios principais", "Top 10 anúncios devem ter vídeo demonstrativo.", False, True),
        ("Avaliar descrições dos anúncios", "Descrição completa, especificações, diferenciais, FAQ.", False, True),
        ("Verificar categorização correta", "Anúncios na categoria mais específica possível.", False, True),
        ("Verificar variações configuradas", "Cor, tamanho, modelo — todas as variações disponíveis.", False, True),
        ("Verificar preços vs concorrência", "Comparar preços com os 3 primeiros da busca.", True, True),
        ("Verificar tipo de anúncio (Clássico/Premium)", "Avaliar se o tipo está adequado ao volume de vendas.", False, True),
        ("Verificar garantia configurada", "Garantia de fábrica ou do vendedor configurada quando aplicável.", False, False),
        ("Verificar perguntas não respondidas", "Responder TODAS as perguntas pendentes.", False, True),
        ("Verificar anúncios pausados/inativos", "Reativar ou excluir anúncios pausados sem motivo.", False, True),
    ],
)

# 3. AUDITORIA DE REPUTAÇÃO
criar_checklist(
    "Auditoria de Reputação",
    "Verificação completa da saúde da reputação no ML",
    "avulso", "consultant", "Reputação",
    [
        ("Verificar % de reclamações nos últimos 60 dias", "Meta: abaixo de 2%. Identificar motivos das reclamações.", True, True),
        ("Verificar tempo médio de resposta", "Meta: responder em até 12h. Ideal: menos de 4h.", True, True),
        ("Verificar % de cancelamentos", "Meta: abaixo de 1%. Identificar motivos.", True, True),
        ("Verificar % de entregas atrasadas", "Meta: 0%. Identificar gargalos logísticos.", True, True),
        ("Analisar reclamações abertas", "Ler cada reclamação, classificar motivo, definir ação.", False, True),
        ("Verificar mediações abertas no ML", "Resolver todas as mediações pendentes.", False, True),
        ("Avaliar qualidade das respostas às reclamações", "Respostas educadas, solução rápida, oferta de compensação.", False, True),
        ("Verificar devoluções pendentes", "Processar todas as devoluções aguardando ação.", False, True),
        ("Analisar avaliações negativas recentes", "Identificar padrões de insatisfação.", True, True),
        ("Verificar se mensagens do ML estão sendo respondidas", "Todas as mensagens devem ser respondidas em até 24h.", False, True),
    ],
)

# 4. SETUP LOGÍSTICA / FULL
criar_checklist(
    "Setup Logística e Full",
    "Configuração completa de logística e Mercado Envios Full",
    "avulso", "consultant", "Logística",
    [
        ("Verificar endereço de coleta configurado", "Endereço correto e atualizado para coleta/envio.", False, True),
        ("Avaliar elegibilidade para Full", "Verificar se produtos são elegíveis para Full (peso, dimensão, categoria).", False, True),
        ("Enviar primeiros produtos para Full", "Selecionar top 10-20 produtos e enviar para o centro de distribuição.", True, True),
        ("Configurar Mercado Envios Flex (se aplicável)", "Para sellers com entrega no mesmo dia na região.", False, True),
        ("Verificar embalagens adequadas", "Embalagem protege o produto? Tamanho adequado? Apresentação profissional?", True, True),
        ("Configurar dimensões e peso corretos nos anúncios", "Evitar cobranças incorretas de frete.", False, True),
        ("Verificar prazos de despacho", "Meta: enviar no mesmo dia ou D+1.", False, True),
        ("Configurar frete grátis nos anúncios elegíveis", "Frete grátis para anúncios acima do threshold do ML.", False, True),
        ("Testar fluxo de envio completo", "Simular venda → separação → embalagem → despacho.", False, True),
        ("Configurar SKU/código interno nos produtos Full", "Facilitar controle de estoque.", False, True),
    ],
)

# 5. CONFIGURAÇÃO DE ADS
criar_checklist(
    "Setup de Mercado Ads",
    "Configuração inicial de campanhas de publicidade no ML",
    "avulso", "consultant", "Marketing/Ads",
    [
        ("Verificar saldo disponível para Ads", "Definir orçamento mensal com o seller.", False, True),
        ("Selecionar produtos para campanha", "Escolher produtos com boa margem, estoque e histórico de vendas.", False, True),
        ("Configurar campanha Product Ads", "Criar campanha com segmentação automática.", True, True),
        ("Definir lance (CPC) adequado", "Começar com lance sugerido, ajustar conforme performance.", False, True),
        ("Configurar orçamento diário", "Definir limite diário para controle de gastos.", False, True),
        ("Verificar ACoS target", "Definir meta de ACoS aceitável para o seller (idealmente < 15%).", False, True),
        ("Criar campanha de marca (se aplicável)", "Brand Ads para sellers com marca registrada.", False, True),
        ("Definir palavras-chave negativas", "Excluir termos irrelevantes que gastam budget.", False, True),
        ("Configurar acompanhamento semanal de Ads", "Definir dia da semana para revisar métricas de Ads.", False, False),
        ("Explicar relatórios de Ads ao seller", "Garantir que o seller entende ACoS, CPC, impressões, cliques.", False, True),
    ],
)

# 6. REVISÃO MENSAL
criar_checklist(
    "Revisão Mensal do Seller",
    "Checklist de acompanhamento mensal obrigatório",
    "mensal", "consultant", "Acompanhamento Mensal",
    [
        ("Analisar faturamento do mês vs meta", "Comparar vendas realizadas com a meta definida.", True, True),
        ("Verificar evolução da reputação", "Comparar com mês anterior: reclamações, atrasos, cancelamentos.", True, True),
        ("Revisar diagnóstico mensal", "Aplicar ou atualizar o Diagnóstico 360°.", False, False),
        ("Verificar tarefas pendentes do mês anterior", "Cobrar entregas atrasadas, redefinir prazos se necessário.", False, True),
        ("Analisar performance de Ads", "ROI, ACoS, conversão. Otimizar campanhas.", True, True),
        ("Verificar estoque dos top produtos", "Garantir que não vai faltar estoque dos mais vendidos.", False, True),
        ("Analisar anúncios com queda de vendas", "Identificar motivos: preço, fotos, posição, sazonalidade.", False, True),
        ("Analisar novos concorrentes", "Verificar se surgiram novos concorrentes relevantes.", False, True),
        ("Verificar oportunidades de novos produtos", "Tendências, sazonalidade, nichos não explorados.", False, True),
        ("Definir metas e plano de ação para o próximo mês", "Metas claras, mensuráveis, com responsáveis e prazos.", False, True),
        ("Atualizar jornada do cliente no sistema", "Marcar etapas concluídas, ajustar próximas etapas.", False, False),
        ("Enviar resumo mensal ao seller por WhatsApp", "Resumo com principais números, conquistas e próximos passos.", False, False),
    ],
)

# 7. PRECIFICAÇÃO
criar_checklist(
    "Auditoria de Precificação",
    "Revisão completa de preços e margens do seller",
    "avulso", "consultant", "Financeiro",
    [
        ("Levantar custos fixos mensais do seller", "Aluguel, funcionários, ferramentas, etc.", False, True),
        ("Levantar custo de aquisição de cada produto", "Preço de compra, frete de entrada, impostos.", False, True),
        ("Calcular taxas do ML por produto", "Comissão, frete, Ads. Usar calculadora de custos do ML.", True, True),
        ("Calcular margem líquida por produto", "Receita - custos - taxas = margem real.", True, True),
        ("Identificar produtos com margem negativa", "Produtos que dão prejuízo devem ser ajustados ou removidos.", False, True),
        ("Comparar preços com top 3 concorrentes", "Por produto, verificar se está competitivo.", True, True),
        ("Definir estratégia de preço por categoria", "Penetração, paridade, premium — depende do momento.", False, True),
        ("Verificar se frete grátis impacta margem", "Calcular se o frete absorvido é viável.", False, True),
        ("Criar planilha de custos compartilhada", "Seller deve manter atualizada para controle.", True, False),
        ("Definir preço mínimo por produto (floor price)", "Preço abaixo do qual não se deve vender.", False, True),
    ],
)

# 8. ESCALA
criar_checklist(
    "Checklist de Escala (100→1000 vendas)",
    "Verificações para sellers prontos para escalar operação",
    "avulso", "consultant", "Escala",
    [
        ("Verificar se operação suporta volume 10x", "Processos, equipe, espaço, embalagem — tudo aguenta escalar?", False, True),
        ("Verificar fornecedores alternativos", "Não depender de um único fornecedor. Ter backup.", False, True),
        ("Avaliar necessidade de funcionários", "Quantas pessoas serão necessárias? Quais funções?", False, True),
        ("Configurar Full para top 50 produtos", "Full é essencial para escalar com entrega rápida.", False, True),
        ("Otimizar catálogo completo", "Todas as fichas técnicas, fotos, títulos e descrições.", False, True),
        ("Criar segunda conta ML (se estratégico)", "Para diversificar risco ou atender nichos diferentes.", False, True),
        ("Implementar ERP/sistema de gestão", "Controle de estoque, financeiro e pedidos automatizado.", False, True),
        ("Definir processos documentados", "SOPs para cada etapa: separação, embalagem, envio, atendimento.", False, True),
        ("Configurar campanhas de Ads agressivas", "Aumentar budget de Ads com ROI positivo comprovado.", False, True),
        ("Planejar capital de giro", "Estoque para 60-90 dias + capital operacional.", False, True),
    ],
)

# 9. CHECKLIST DO SELLER (para o próprio seller usar)
criar_checklist(
    "Checklist Diário do Seller",
    "Rotina diária que o seller deve seguir",
    "diario", "seller", "Conta ML",
    [
        ("Verificar novas vendas e processar envios", "Separar, embalar e despachar todos os pedidos do dia.", False, False),
        ("Responder todas as perguntas dos anúncios", "Responder de forma completa e rápida (meta: <1h).", False, False),
        ("Responder mensagens de pós-venda", "Atender dúvidas de compradores sobre entrega, produto.", False, False),
        ("Verificar reclamações abertas", "Resolver reclamações o mais rápido possível.", False, False),
        ("Verificar devoluções pendentes", "Processar devoluções e reembolsos.", False, False),
        ("Verificar estoque dos mais vendidos", "Repor antes de zerar o estoque.", False, False),
        ("Verificar performance de Ads (se ativo)", "Pausar anúncios com ACoS muito alto.", False, False),
    ],
)

# 10. CHECKLIST SEMANAL DO SELLER
criar_checklist(
    "Checklist Semanal do Seller",
    "Rotina semanal para manter a conta saudável",
    "semanal", "seller", "Conta ML",
    [
        ("Analisar vendas da semana vs meta", "Comparar com semana anterior e meta mensal.", False, False),
        ("Verificar anúncios que caíram de posição", "Anúncios que saíram das primeiras posições da busca.", False, False),
        ("Revisar preços vs concorrência", "Ajustar preços para manter competitividade.", False, False),
        ("Verificar avaliações da semana", "Responder avaliações negativas, agradecer positivas.", False, False),
        ("Planejar reposição de estoque", "Fazer pedidos a fornecedores com antecedência.", False, False),
        ("Revisar campanhas de Ads da semana", "Otimizar lances, pausar produtos ruins, ativar novos.", False, False),
        ("Publicar novos anúncios (se aplicável)", "Meta de X novos anúncios por semana.", False, False),
    ],
)

print("✓ 10 templates de checklist criados com todos os itens")

# ══════════════════════════════════════════════════════════
# TREINAMENTOS COMPLETOS
# ══════════════════════════════════════════════════════════
from apps.treinamentos.models import Treinamento

treinamentos = [
    # Operacionais Básicos
    ("Fotografia Profissional para ML", "operacional",
     "Como tirar fotos profissionais com celular: fundo branco, iluminação, ângulos, edição. "
     "Inclui técnicas de foto com fundo infinito DIY e apps de edição gratuitos.", 60),

    ("Títulos Otimizados para ML", "operacional",
     "Como criar títulos que vendem: estrutura ideal, palavras-chave, tendências de busca do ML. "
     "Usar ferramenta de tendências e análise de concorrentes.", 45),

    ("Descrições que Convertem", "operacional",
     "Como escrever descrições persuasivas: estrutura, especificações técnicas, FAQ, gatilhos mentais. "
     "Templates prontos para diferentes categorias.", 45),

    ("Fichas Técnicas Completas", "operacional",
     "Importância do preenchimento completo das fichas técnicas para SEO interno do ML. "
     "Como preencher corretamente cada campo por categoria.", 30),

    ("Gestão de Reputação no ML", "operacional",
     "Como manter reputação verde: gestão de reclamações, mediações, devoluções. "
     "Técnicas de resposta, compensação e prevenção de problemas.", 90),

    ("Atendimento ao Cliente no ML", "operacional",
     "Excelência no atendimento: responder perguntas, pós-venda, mensagens. "
     "Scripts prontos, tempo de resposta, tom de comunicação.", 60),

    ("Mercado Envios Full - Guia Completo", "operacional",
     "Tudo sobre Full: como enviar, custos, vantagens, produtos elegíveis. "
     "Passo a passo de como preparar e enviar a primeira remessa.", 75),

    ("Mercado Envios Flex e Coleta", "operacional",
     "Como usar Flex para entrega no mesmo dia. Configuração de coleta. "
     "Quando usar cada modalidade de envio.", 45),

    ("Embalagem Profissional", "operacional",
     "Tipos de embalagem por produto, proteção adequada, custo-benefício. "
     "Como reduzir devoluções por embalagem inadequada.", 30),

    ("Variações de Anúncios", "operacional",
     "Como configurar variações (cor, tamanho, modelo) corretamente. "
     "Impacto nas vendas e na experiência do comprador.", 30),

    # Estratégicos
    ("Mercado Ads Básico", "estrategica",
     "Introdução ao Mercado Ads: como funciona, tipos de campanha, métricas essenciais. "
     "Criar primeira campanha Product Ads passo a passo.", 75),

    ("Mercado Ads Avançado", "estrategica",
     "Estratégias avançadas: segmentação, lances, otimização de ACoS, testes A/B. "
     "Como escalar campanhas mantendo rentabilidade.", 90),

    ("Precificação Inteligente", "estrategica",
     "Como precificar para maximizar lucro: custo real, taxas do ML, margem alvo. "
     "Estratégias de penetração, paridade e premium. Calculadora de preços.", 60),

    ("Análise de Métricas e KPIs", "estrategica",
     "Interpretar dados do ML: visitas, conversão, ticket médio, ranking. "
     "Dashboard de métricas essenciais e como usar para tomar decisões.", 60),

    ("Gestão Financeira para Sellers", "estrategica",
     "Controle financeiro: fluxo de caixa, DRE simplificado, capital de giro. "
     "Como separar finanças pessoais do negócio. Ferramentas de controle.", 60),

    ("Análise de Concorrência", "estrategica",
     "Como mapear concorrentes: preços, fotos, reputação, posicionamento. "
     "Ferramentas de monitoramento e estratégias de diferenciação.", 45),

    ("SEO no Mercado Livre", "estrategica",
     "Como o algoritmo do ML funciona: fatores de ranking, relevância, conversão. "
     "Otimização completa de anúncios para aparecer nas primeiras posições.", 60),

    ("Escala: De 100 a 1000 Vendas/Mês", "estrategica",
     "Estratégias de escala: processos, equipe, fornecedores, capital de giro. "
     "Quando e como contratar, automatizar e expandir.", 120),

    ("Catálogo e Expansão de Produtos", "estrategica",
     "Como identificar oportunidades de novos produtos: tendências, sazonalidade, nicho. "
     "Pesquisa de mercado dentro do ML, análise de demanda.", 60),

    ("Marca no Mercado Livre", "estrategica",
     "Como registrar marca no INPI, Brand Ads, Official Store. "
     "Vantagens de ter marca registrada no ML e como proteger.", 45),

    ("Promoções e Datas Especiais", "estrategica",
     "Como participar de promoções do ML: Hot Sale, Black Friday, Natal. "
     "Planejamento de estoque, preço e logística para datas especiais.", 60),

    ("Multi-conta e Diversificação", "estrategica",
     "Quando e como abrir segunda conta ML. Estratégias de diversificação por nicho. "
     "Riscos e cuidados legais.", 45),

    ("Pós-venda e Fidelização", "estrategica",
     "Estratégias de pós-venda: follow-up, encarte na embalagem, WhatsApp. "
     "Como transformar compradores em clientes recorrentes (dentro das regras do ML).", 45),

    ("Gestão de Estoque e Reposição", "estrategica",
     "Controle de estoque: estoque mínimo, ponto de reposição, giro de estoque. "
     "Como evitar ruptura e excesso de estoque.", 45),
]

for titulo, cat, desc, duracao in treinamentos:
    Treinamento.objects.update_or_create(
        titulo=titulo,
        defaults={"categoria": cat, "descricao": desc, "duracao_minutos": duracao},
    )

print(f"✓ {len(treinamentos)} treinamentos criados")

# ══════════════════════════════════════════════════════════
# TIPOS DE TAREFA COMPLETOS
# ══════════════════════════════════════════════════════════
from apps.tarefas.models import TipoTarefa

tipos = [
    ("Otimizar Anúncio", "photo", "#6366F1"),
    ("Melhorar Reputação", "shield-check", "#22C55E"),
    ("Configurar Full/Logística", "truck", "#F59E0B"),
    ("Análise de Concorrência", "magnifying-glass", "#EC4899"),
    ("Ajustar Preço", "currency-dollar", "#06B6D4"),
    ("Criar Campanha Ads", "megaphone", "#8B5CF6"),
    ("Treinamento", "academic-cap", "#10B981"),
    ("Responder Reclamação", "chat-bubble-left-right", "#EF4444"),
    ("Criar Novo Anúncio", "plus-circle", "#3B82F6"),
    ("Atualizar Ficha Técnica", "clipboard-document-list", "#F97316"),
    ("Gestão de Estoque", "archive-box", "#84CC16"),
    ("Reunião com Seller", "video-camera", "#A855F7"),
    ("Enviar Relatório", "document-chart-bar", "#0EA5E9"),
    ("Follow-up Pós-venda", "phone", "#14B8A6"),
]
for nome, icone, cor in tipos:
    TipoTarefa.objects.update_or_create(nome=nome, defaults={"icone": icone, "cor": cor})

print(f"✓ {len(tipos)} tipos de tarefa criados")

# ══════════════════════════════════════════════════════════
# SERVIÇOS DE PROPOSTA
# ══════════════════════════════════════════════════════════
from apps.propostas.models import Servico
from decimal import Decimal

servicos = [
    ("Consultoria Operacional", "Acompanhamento mensal com foco em operação: anúncios, logística, reputação e atendimento.", Decimal("997.00"), 1),
    ("Consultoria Estratégica", "Acompanhamento completo: operação + estratégia de crescimento, Ads, precificação e escala.", Decimal("1997.00"), 2),
    ("Consultoria Premium", "Consultoria estratégica + gestão de Ads + reuniões semanais + suporte prioritário.", Decimal("2997.00"), 3),
    ("Setup Inicial de Conta ML", "Configuração completa da conta: anúncios, fotos, Full, frete, precificação.", Decimal("1497.00"), 4),
    ("Gestão de Mercado Ads", "Gestão mensal completa de campanhas: criação, otimização, relatórios.", Decimal("797.00"), 5),
    ("Treinamento Individual (sessão)", "Sessão de treinamento personalizado sobre tema específico.", Decimal("297.00"), 6),
    ("Pacote de Treinamentos (5 sessões)", "5 sessões de treinamento sobre temas essenciais para o seller.", Decimal("1197.00"), 7),
    ("Auditoria Completa da Conta", "Auditoria detalhada: anúncios, reputação, logística, preços, Ads. Relatório com plano de ação.", Decimal("997.00"), 8),
    ("Fotografia Profissional (por produto)", "Sessão de fotos profissionais para até 5 produtos com edição.", Decimal("197.00"), 9),
    ("Criação de Anúncios (pacote 10)", "Criação completa de 10 anúncios: fotos, título, descrição, ficha técnica.", Decimal("497.00"), 10),
]
for nome, desc, preco, ordem in servicos:
    Servico.objects.update_or_create(nome=nome, defaults={"descricao": desc, "preco_sugerido": preco, "ordem": ordem})

print(f"✓ {len(servicos)} serviços de proposta")

# ══════════════════════════════════════════════════════════
# ETAPAS DO PIPELINE
# ══════════════════════════════════════════════════════════
from apps.clientes.models import EtapaPipeline

etapas = [
    ("Onboarding", "#6366F1", 1),
    ("Diagnóstico Inicial", "#8B5CF6", 2),
    ("Plano de Ação", "#EC4899", 3),
    ("Implementação", "#F59E0B", 4),
    ("Acompanhamento", "#22C55E", 5),
    ("Consolidação", "#06B6D4", 6),
    ("Escala", "#10B981", 7),
    ("Maturidade", "#3B82F6", 8),
]
for nome, cor, ordem in etapas:
    EtapaPipeline.objects.update_or_create(nome=nome, defaults={"cor": cor, "ordem": ordem})

print(f"✓ {len(etapas)} etapas de pipeline")

print("\n" + "=" * 50)
print("✅ CONTEÚDO COMPLETO CRIADO!")
print("=" * 50)
