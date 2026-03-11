"""
Seed extra: checklists e treinamentos complementares.
Uso: python manage.py shell < scripts/seed_content_extra.py
"""
from decimal import Decimal
from apps.accounts.models import User
from apps.checklists.models import ChecklistCategory, ChecklistTemplate, ChecklistTemplateItem
from apps.treinamentos.models import Treinamento

gestor = User.objects.filter(role="gestor").first()
cats = {c.nome: c for c in ChecklistCategory.objects.all()}


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


# ══════════════════════════════════════════════════════════
# NOVAS CATEGORIAS
# ══════════════════════════════════════════════════════════
new_cats = [
    ("Recuperação", "Processos de recuperação de conta e reputação", "exclamation-triangle", 10),
    ("Datas Especiais", "Preparação para grandes promoções", "gift", 11),
    ("Encerramento", "Processos de offboarding e transição", "arrow-right-on-rectangle", 12),
    ("Qualidade", "Controle de qualidade de produtos e processos", "check-badge", 13),
]
for nome, desc, icone, ordem in new_cats:
    cats[nome], _ = ChecklistCategory.objects.update_or_create(
        nome=nome, defaults={"descricao": desc, "icone": icone, "ordem": ordem}
    )
print(f"✓ {len(new_cats)} novas categorias")

# ══════════════════════════════════════════════════════════
# CHECKLISTS EXTRAS
# ══════════════════════════════════════════════════════════

# 11. RECUPERAÇÃO DE REPUTAÇÃO (emergência)
criar_checklist(
    "Recuperação de Reputação (Emergência)",
    "Protocolo emergencial quando reputação cai para amarela/vermelha",
    "avulso", "consultant", "Recuperação",
    [
        ("Identificar TODAS as reclamações abertas", "Listar cada reclamação com motivo, data e status. Priorizar por antiguidade.", True, True),
        ("Classificar reclamações por tipo", "Separar em: produto defeituoso, atraso, não recebeu, diferente do anúncio, outros.", False, True),
        ("Resolver reclamações de produto defeituoso", "Oferecer troca imediata ou reembolso total. Responder em até 4h.", False, True),
        ("Resolver reclamações de atraso", "Contatar transportadora, informar novo prazo, oferecer compensação se necessário.", False, True),
        ("Resolver reclamações de 'diferente do anúncio'", "Verificar anúncio, corrigir se necessário, oferecer devolução fácil.", False, True),
        ("Responder TODAS as mediações abertas", "Prioridade máxima. Mediação perdida impacta muito a reputação.", False, True),
        ("Pausar anúncios com problemas recorrentes", "Produtos que geram muitas reclamações devem ser pausados e corrigidos.", False, True),
        ("Revisar prazo de despacho", "Garantir que está enviando dentro do prazo. Reduzir prazo se possível.", False, True),
        ("Verificar qualidade das embalagens", "Embalagem inadequada causa devoluções. Melhorar proteção.", True, True),
        ("Criar alerta diário de novas reclamações", "Monitorar diariamente até estabilizar a reputação.", False, False),
        ("Definir meta de dias sem reclamação", "Meta: 7 dias seguidos sem nova reclamação. Depois 14, depois 30.", False, True),
        ("Revisar anúncios que mais geram problemas", "Fotos enganosas? Descrição incompleta? Produto de baixa qualidade?", True, True),
        ("Montar plano de prevenção", "Documentar processos para evitar reincidência de cada tipo de problema.", False, True),
    ],
)

# 12. PREPARAÇÃO BLACK FRIDAY / HOT SALE
criar_checklist(
    "Preparação para Data Especial (Black Friday/Hot Sale)",
    "Checklist completo de preparação para grandes eventos promocionais",
    "avulso", "consultant", "Datas Especiais",
    [
        ("Definir produtos participantes (60 dias antes)", "Selecionar top 20-50 produtos com melhor margem e estoque.", False, True),
        ("Calcular preço promocional mantendo margem", "Desconto real de pelo menos 10%. Calcular se margem ainda é positiva.", True, True),
        ("Garantir estoque suficiente (45 dias antes)", "Fazer pedido extra a fornecedores. Estoque para 3-5x o volume normal.", False, True),
        ("Enviar estoque para Full (30 dias antes)", "Produtos Full vendem mais em datas especiais. Enviar com antecedência.", True, True),
        ("Otimizar fotos e títulos dos produtos participantes", "Fotos de alta qualidade, títulos com palavras-chave sazonais.", True, True),
        ("Configurar frete grátis onde possível", "Frete grátis aumenta conversão significativamente.", False, True),
        ("Inscrever produtos na promoção oficial do ML", "Verificar requisitos e inscrever dentro do prazo.", True, True),
        ("Aumentar budget de Ads (15 dias antes)", "Dobrar ou triplicar investimento em Ads para os produtos participantes.", False, True),
        ("Preparar equipe para volume extra", "Garantir que tem gente suficiente para separar, embalar e enviar.", False, True),
        ("Testar fluxo de envio com volume alto", "Simular operação com 3-5x o volume normal.", False, True),
        ("Preparar respostas rápidas para perguntas frequentes", "Templates de resposta para perguntas comuns sobre promoção.", False, False),
        ("Monitorar concorrentes no dia", "Acompanhar preços da concorrência e ajustar se necessário.", False, True),
        ("Definir plano de contingência", "O que fazer se acabar estoque? Se der problema logístico? Se o preço do concorrente for menor?", False, True),
        ("Pós-evento: analisar resultados em 48h", "Vendas, faturamento, margem, novas reclamações, estoque restante.", True, True),
    ],
)

# 13. OFFBOARDING / ENCERRAMENTO
criar_checklist(
    "Encerramento de Contrato / Offboarding",
    "Processo organizado de encerramento da consultoria com o seller",
    "avulso", "consultant", "Encerramento",
    [
        ("Agendar reunião de encerramento com o seller", "Reunião presencial ou online para formalizar o encerramento.", False, False),
        ("Apresentar relatório final de evolução", "Comparar métricas de quando entrou vs agora: vendas, reputação, faturamento.", True, True),
        ("Documentar processos implementados", "Lista de tudo que foi configurado, otimizado e ensinado.", False, True),
        ("Verificar se há tarefas/pendências em aberto", "Finalizar ou documentar o que ficou pendente.", False, True),
        ("Transferir conhecimento de Ads", "Se o consultor gerencia Ads, ensinar o seller a manter ou transferir para outro.", False, True),
        ("Revogar acessos compartilhados", "Remover acesso do consultor à conta ML, Mercado Pago, etc.", False, False),
        ("Enviar pesquisa NPS final", "Coletar feedback sobre a experiência do seller com a consultoria.", False, False),
        ("Formalizar encerramento do contrato", "Documento ou e-mail confirmando encerramento e data.", False, False),
        ("Oferecer plano de manutenção/acompanhamento", "Propor plano reduzido mensal para manter acompanhamento.", False, True),
        ("Atualizar status do cliente no sistema", "Marcar como 'Encerrado' e documentar motivo.", False, True),
    ],
)

# 14. SETUP NOVA CONTA ML
criar_checklist(
    "Setup de Nova Conta Mercado Livre",
    "Configuração completa de uma nova conta ML do zero",
    "avulso", "consultant", "Conta ML",
    [
        ("Criar conta no Mercado Livre", "CPF ou CNPJ. Preferir CNPJ para limites maiores.", False, True),
        ("Completar verificação de identidade", "Enviar documentos para liberar funcionalidades completas.", True, True),
        ("Configurar dados bancários no Mercado Pago", "Conta bancária para recebimento dos pagamentos.", False, True),
        ("Configurar endereço de envio/coleta", "Endereço atualizado e correto para coletas.", False, True),
        ("Ativar Mercado Envios", "Configurar modalidade de envio (Full, Flex, Coleta, Agência).", False, True),
        ("Configurar informações de faturamento", "Dados fiscais corretos para notas fiscais.", False, True),
        ("Publicar primeiros 5 anúncios teste", "Anúncios básicos para testar fluxo completo.", True, True),
        ("Realizar primeira venda teste", "Vender para alguém de confiança para testar todo o processo.", False, True),
        ("Configurar templates de resposta", "Respostas prontas para perguntas e mensagens frequentes.", False, False),
        ("Ativar notificações no celular", "App do ML com notificações de vendas, perguntas e reclamações.", False, False),
        ("Registrar marca (se aplicável)", "Iniciar processo no INPI e cadastrar no ML.", False, True),
        ("Configurar Mercado Ads", "Ativar conta de publicidade e definir primeiro orçamento.", False, True),
    ],
)

# 15. AUDITORIA DE SEO / POSICIONAMENTO
criar_checklist(
    "Auditoria de SEO e Posicionamento",
    "Verificação completa do posicionamento dos anúncios nas buscas do ML",
    "avulso", "consultant", "Anúncios",
    [
        ("Listar top 20 produtos por faturamento", "Identificar os produtos mais importantes para focar.", True, True),
        ("Verificar posição na busca para cada produto", "Buscar termos principais e anotar posição de cada anúncio.", True, True),
        ("Analisar títulos vs termos de busca", "Título contém as palavras-chave que o comprador busca?", False, True),
        ("Verificar fichas técnicas completas", "Fichas incompletas prejudicam o ranking.", False, True),
        ("Comparar preço com concorrentes da primeira página", "Estar na faixa de preço dos top resultados.", True, True),
        ("Verificar tipo de anúncio (Clássico/Premium/Full)", "Premium e Full têm vantagem no ranking.", False, True),
        ("Analisar taxa de conversão por anúncio", "Produtos com baixa conversão perdem posição.", True, True),
        ("Verificar se tem frete grátis", "Frete grátis melhora posicionamento.", False, True),
        ("Verificar tempo de despacho configurado", "Menor tempo = melhor posicionamento.", False, True),
        ("Analisar qualidade das fotos vs concorrentes", "Fotos melhores = mais cliques = mais conversão = melhor ranking.", True, True),
        ("Verificar se produto tem avaliações", "Produtos sem avaliações têm desvantagem.", False, True),
        ("Testar variações de título (A/B)", "Criar versões de título e monitorar performance por 7 dias.", False, True),
        ("Documentar ações de melhoria por anúncio", "Para cada anúncio fora do top 10, definir ações específicas.", False, True),
    ],
)

# 16. REVISÃO TRIMESTRAL (mais profunda que mensal)
criar_checklist(
    "Revisão Trimestral Estratégica",
    "Análise profunda trimestral de toda a operação do seller",
    "trimestral", "consultant", "Acompanhamento Mensal",
    [
        ("Analisar evolução de faturamento (3 meses)", "Gráfico de vendas mensais. Tendência de crescimento ou queda.", True, True),
        ("Comparar diagnósticos dos 3 meses", "Evolução por categoria. Onde melhorou, onde piorou.", True, True),
        ("Analisar ROI da consultoria", "Faturamento antes vs depois. Justificar investimento na consultoria.", True, True),
        ("Revisar metas do trimestre vs realizado", "Quais metas foram atingidas? Quais não? Por quê?", False, True),
        ("Analisar evolução de reputação", "Gráfico de reclamações, cancelamentos, tempo de resposta.", True, True),
        ("Revisar eficiência de Ads no trimestre", "ACoS médio, ROI, budget total investido, vendas geradas.", True, True),
        ("Analisar mix de produtos", "Quais cresceram? Quais caíram? Oportunidades não exploradas.", False, True),
        ("Avaliar processos operacionais", "Logística, atendimento, envio — estão eficientes?", False, True),
        ("Benchmark com outros sellers do segmento", "Comparar métricas com benchmark do segmento.", False, True),
        ("Redefinir metas para próximo trimestre", "Metas SMART: específicas, mensuráveis, alcançáveis, relevantes, temporais.", False, True),
        ("Atualizar plano de ação estratégico", "Novo plano com base na análise trimestral.", False, True),
        ("Apresentar resultados ao seller", "Reunião formal de apresentação de resultados e plano futuro.", False, False),
        ("Reavaliar plano/tipo de consultoria", "O seller precisa de upgrade? Downgrade? Está no plano certo?", False, True),
    ],
)

# 17. PREPARAÇÃO PARA MERCADOLÍDER
criar_checklist(
    "Preparação para MercadoLíder",
    "Requisitos e preparação para atingir status MercadoLíder",
    "avulso", "consultant", "Escala",
    [
        ("Verificar requisitos atuais do MercadoLíder", "Faturamento mínimo, quantidade de vendas, reputação. Verificar no ML.", True, True),
        ("Calcular gap entre situação atual e requisitos", "Quanto falta em faturamento? Quantas vendas faltam? Reputação está OK?", False, True),
        ("Definir prazo realista para atingir MercadoLíder", "Projetar crescimento mensal e estimar mês de atingimento.", False, True),
        ("Garantir reputação verde estável", "Mínimo 60 dias sem queda de reputação.", False, True),
        ("Aumentar volume de vendas", "Estratégias: Ads, promoções, novos produtos, preço competitivo.", False, True),
        ("Diversificar base de produtos", "Mais produtos = mais chances de venda = mais volume.", False, True),
        ("Otimizar conversão dos top anúncios", "Melhorar fotos, títulos, preços para converter mais.", False, True),
        ("Verificar se todos os envios são no prazo", "Zero atrasos é essencial para manter MercadoLíder.", False, True),
        ("Monitorar progresso semanal", "Acompanhar semanalmente o avanço em direção às metas.", False, True),
        ("Celebrar conquista com o seller!", "Quando atingir, fazer um post/mensagem de celebração.", False, False),
    ],
)

# 18. CONTROLE DE QUALIDADE DE PRODUTO
criar_checklist(
    "Controle de Qualidade de Produtos",
    "Verificação de qualidade antes de enviar ou publicar produtos",
    "avulso", "seller", "Qualidade",
    [
        ("Verificar produto conforme descrição do anúncio", "O produto recebido do fornecedor é exatamente o que está no anúncio?", True, True),
        ("Testar funcionamento do produto", "Se eletrônico/mecânico: ligar, testar funções básicas.", False, True),
        ("Verificar embalagem original intacta", "Caixa sem amassados, lacre intacto, todos os acessórios.", True, True),
        ("Conferir voltagem/tamanho/cor corretos", "Variações devem corresponder ao pedido do comprador.", False, False),
        ("Verificar manual/documentação inclusa", "Manual em português (se obrigatório), certificado, garantia.", False, False),
        ("Tirar foto do produto antes do envio", "Registro visual caso haja reclamação de defeito.", True, False),
        ("Verificar integridade da embalagem de envio", "Proteção adequada com plástico bolha, isopor ou enchimento.", True, False),
        ("Colar etiqueta de envio corretamente", "Etiqueta visível, legível, sem cobrir informações do produto.", False, False),
    ],
)

print("✓ 8 checklists extras criados")

# ══════════════════════════════════════════════════════════
# TREINAMENTOS EXTRAS
# ══════════════════════════════════════════════════════════

treinamentos_extras = [
    # Operacionais extras
    ("Mercado Shops - Loja Virtual no ML", "operacional",
     "Como configurar e gerenciar o Mercado Shops: personalização, banner, categorias internas. "
     "Diferença entre catálogo e loja, como melhorar a experiência do comprador.", 45),

    ("Como Responder Perguntas que Convertem", "operacional",
     "Técnicas para transformar perguntas em vendas: velocidade de resposta, informação completa, "
     "cross-selling, gatilhos de urgência. Templates de respostas que vendem.", 45),

    ("Gestão de Devoluções e Trocas", "operacional",
     "Processo completo de devoluções: como aceitar, quando contestar, logística reversa. "
     "Como reduzir devoluções com anúncios mais precisos e embalagem adequada.", 45),

    ("Vídeo para Anúncios no ML", "operacional",
     "Como gravar vídeos demonstrativos com celular: roteiro, iluminação, edição. "
     "Apps de edição gratuitos. Formatos aceitos pelo ML. Impacto na conversão.", 60),

    ("Ferramentas Gratuitas para Sellers", "operacional",
     "Ferramentas gratuitas essenciais: Nubimetrics (tendências), planilhas de custo, "
     "editores de foto, geradores de ficha técnica, calculadora de frete.", 30),

    ("Mercado Pago - Gestão Financeira", "operacional",
     "Como gerenciar o Mercado Pago: saldo, antecipação, taxas, empréstimos. "
     "Quando antecipar, como economizar em taxas, Point para vendas presenciais.", 45),

    ("Atendimento Pós-venda Excepcional", "operacional",
     "Como surpreender o comprador: encarte na embalagem, mensagem de agradecimento, "
     "follow-up pós-entrega. Impacto nas avaliações e recorrência.", 30),

    ("Gestão de Múltiplos Pedidos", "operacional",
     "Organização para alto volume: como separar, etiquetar e embalar muitos pedidos. "
     "Fluxo de trabalho, checklist de separação, controle de erros.", 45),

    # Estratégicos extras
    ("Tributação e Impostos para E-commerce", "estrategica",
     "Noções essenciais de tributação: MEI, Simples Nacional, nota fiscal. "
     "Quando migrar de CPF para CNPJ. Obrigações fiscais por marketplace. "
     "Custos tributários que devem entrar na precificação.", 90),

    ("Automação de Processos para Sellers", "estrategica",
     "Ferramentas de automação: ERP (Bling, Tiny, Olist), integração multi-marketplace, "
     "emissão automática de NF, gestão de estoque automatizada. Quando investir em automação.", 60),

    ("Como Ser MercadoLíder e MercadoLíder Platinum", "estrategica",
     "Requisitos detalhados, benefícios, estratégias para atingir e manter. "
     "Impacto no posicionamento, badge de confiança, acesso a recursos exclusivos.", 45),

    ("Loja Oficial (Official Store) no ML", "estrategica",
     "Requisitos para se tornar Official Store, processo de aplicação, custos. "
     "Benefícios: destaque na busca, página personalizada, landing pages.", 45),

    ("Expansão para Outros Marketplaces", "estrategica",
     "Quando e como expandir: Shopee, Amazon, Magalu, Americanas. "
     "Diferenças de cada plataforma, priorização, integração via hub.", 75),

    ("Inteligência de Mercado e Tendências", "estrategica",
     "Como usar dados do ML para tomar decisões: tendências de busca, produtos em alta, "
     "sazonalidade por categoria. Ferramentas de inteligência (Nubimetrics, ML Trends).", 60),

    ("Construindo uma Marca no Marketplace", "estrategica",
     "Como criar identidade visual: logo, paleta de cores, padrão de fotos. "
     "Branding no anúncio, na embalagem, no atendimento. Diferenciação por marca.", 60),

    ("Gestão de Equipe para E-commerce", "estrategica",
     "Como montar equipe: funções essenciais (separação, atendimento, fotos, Ads). "
     "Quando contratar, como treinar, indicadores por função. Cultura de excelência.", 75),

    ("Análise de Sazonalidade e Planejamento Anual", "estrategica",
     "Calendário comercial: quando vende mais, quando vende menos por categoria. "
     "Como planejar estoque, preço e Ads para cada período. Black Friday, Natal, Dia das Mães.", 60),

    ("Estratégias de Bundles e Kits", "estrategica",
     "Como criar kits e combos que vendem mais: seleção de produtos complementares, "
     "precificação de kit, como anunciar. Impacto no ticket médio e margem.", 45),

    ("Negociação com Fornecedores", "estrategica",
     "Técnicas de negociação: como conseguir melhores preços, prazo de pagamento, "
     "exclusividade. Quando trocar de fornecedor. Importação básica.", 60),

    ("Métricas Avançadas e Dashboard", "estrategica",
     "KPIs avançados: LTV do comprador, taxa de recompra, CAC por Ads, margem por categoria, "
     "GMROI (retorno sobre investimento em estoque). Como montar dashboard no Google Sheets.", 60),
]

for titulo, cat, desc, duracao in treinamentos_extras:
    Treinamento.objects.update_or_create(
        titulo=titulo,
        defaults={"categoria": cat, "descricao": desc, "duracao_minutos": duracao},
    )

print(f"✓ {len(treinamentos_extras)} treinamentos extras criados")

# ══════════════════════════════════════════════════════════
# RESUMO FINAL
# ══════════════════════════════════════════════════════════
total_checklists = ChecklistTemplate.objects.count()
total_itens = ChecklistTemplateItem.objects.count()
total_treinamentos = Treinamento.objects.count()

print(f"\n{'=' * 50}")
print(f"📋 Total Checklists: {total_checklists} ({total_itens} itens)")
print(f"🎓 Total Treinamentos: {total_treinamentos}")
print(f"{'=' * 50}")
