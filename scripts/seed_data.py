"""
Seed script para popular o banco com dados de teste.
Uso: python manage.py shell < scripts/seed_data.py
"""
import random
from datetime import date, timedelta, datetime
from decimal import Decimal

from django.utils import timezone

# ── Configurações (API Keys) ──────────────────────────
from apps.core.models import Configuracao

configs = [
    # Google
    ("google", "GOOGLE_CLIENT_ID", "", "Client ID OAuth 2.0", True),
    ("google", "GOOGLE_CLIENT_SECRET", "", "Client Secret OAuth 2.0", True),
    ("google", "GOOGLE_REDIRECT_URI", "", "URI de redirecionamento OAuth", False),
    # Evolution (WhatsApp)
    ("evolution", "EVOLUTION_API_URL", "", "URL da API Evolution", False),
    ("evolution", "EVOLUTION_API_KEY", "", "API Key Evolution", True),
    ("evolution", "EVOLUTION_INSTANCE", "", "Nome da instância WhatsApp", False),
    # Brevo (Email)
    ("brevo", "BREVO_API_KEY", "", "API Key do Brevo (Sendinblue)", True),
    ("brevo", "BREVO_SENDER_EMAIL", "contato@3mconsultoria.com.br", "Email remetente", False),
    ("brevo", "BREVO_SENDER_NAME", "3M Consultoria", "Nome remetente", False),
    # Asaas (Pagamentos)
    ("asaas", "ASAAS_API_KEY", "", "API Key do Asaas", True),
    ("asaas", "ASAAS_ENVIRONMENT", "sandbox", "Ambiente: sandbox ou production", False),
    # Autentique
    ("autentique", "AUTENTIQUE_API_TOKEN", "", "Token API Autentique", True),
    # IA
    ("ia", "IA_PROVIDER", "anthropic", "Provider de IA: anthropic ou openai", False),
    ("ia", "ANTHROPIC_API_KEY", "", "API Key Anthropic (Claude)", True),
    ("ia", "OPENAI_API_KEY", "", "API Key OpenAI (GPT/Whisper)", True),
    ("ia", "ANTHROPIC_MODEL", "claude-sonnet-4-20250514", "Modelo Anthropic", False),
    ("ia", "OPENAI_MODEL", "gpt-4o", "Modelo OpenAI", False),
    # Geral
    ("geral", "EMPRESA_NOME", "3M Consultoria", "Nome da empresa", False),
    ("geral", "EMPRESA_WHATSAPP", "", "WhatsApp da empresa", False),
    ("geral", "EMPRESA_EMAIL", "contato@3mconsultoria.com.br", "Email da empresa", False),
]

for cat, chave, valor, desc, secret in configs:
    Configuracao.objects.update_or_create(
        chave=chave,
        defaults={"categoria": cat, "valor": valor, "descricao": desc, "is_secret": secret},
    )
print(f"✓ {len(configs)} configurações criadas/atualizadas")

# ── Módulos ────────────────────────────────────────────
from apps.accounts.models import Modulo, User

modulos_data = [
    ("dashboard", "Dashboard", "chart-pie", 1),
    ("clientes", "Clientes", "users", 2),
    ("pipeline", "Pipeline", "funnel", 3),
    ("diagnosticos", "Diagnósticos", "clipboard-check", 5),
    ("tarefas", "Tarefas", "check-circle", 6),
    ("checklists", "Checklists", "list-checks", 7),
    ("reunioes", "Reuniões", "video", 8),
    ("treinamentos", "Treinamentos", "academic-cap", 9),
    ("planos", "Planos de Ação", "light-bulb", 10),
    ("financeiro", "Financeiro", "currency-dollar", 12),
    ("propostas", "Propostas", "document-text", 14),
    ("agenda", "Agenda", "calendar", 15),
    ("nps", "NPS", "star", 16),
    ("relatorios", "Relatórios", "chart-bar", 18),
    ("gamificacao", "Gamificação", "trophy", 20),
    ("swot", "SWOT", "puzzle", 22),
    ("conhecimento", "Base Conhecimento", "book-open", 23),
    ("jornadas", "Jornadas", "map", 25),
    ("ia", "IA", "sparkles", 30),
    ("crm", "CRM", "briefcase", 35),
    ("timesheet", "Timesheet", "clock", 40),
    ("portal", "Portal", "globe", 45),
]

for slug, nome, icone, ordem in modulos_data:
    Modulo.objects.update_or_create(slug=slug, defaults={"nome": nome, "icone": icone, "ordem": ordem})
print(f"✓ {len(modulos_data)} módulos criados")

# ── Usuários ───────────────────────────────────────────
gestor = User.objects.filter(username="gestor").first()
if not gestor:
    gestor = User.objects.create_user("gestor", "gestor@3mconsultoria.com.br", "gestor2024", role="gestor")
    gestor.first_name = "João"
    gestor.last_name = "Silva"
    gestor.save()

consultores_data = [
    ("consultor", "Maria", "Consultora", "consultor@3mconsultoria.com.br", "consultor2024"),
    ("consultor2", "Ana", "Santos", "ana@3mconsultoria.com.br", "consultor2024"),
    ("consultor3", "Pedro", "Oliveira", "pedro@3mconsultoria.com.br", "consultor2024"),
]
consultores = []
for uname, fn, ln, email, pwd in consultores_data:
    u, _ = User.objects.update_or_create(
        username=uname,
        defaults={"first_name": fn, "last_name": ln, "email": email, "role": "consultor"},
    )
    u.set_password(pwd)
    u.save()
    consultores.append(u)
    # Atribuir módulos
    mods = Modulo.objects.filter(slug__in=[
        "dashboard", "clientes", "pipeline", "diagnosticos", "tarefas",
        "checklists", "reunioes", "treinamentos", "planos", "agenda",
        "propostas", "jornadas", "ia", "nps",
    ])
    u.modulos.set(mods)

sellers_data = [
    ("seller", "Carlos", "Vendedor", "carlos@email.com", "seller2024"),
    ("seller2", "Fernanda", "Lima", "fernanda@email.com", "seller2024"),
    ("seller3", "Roberto", "Costa", "roberto@email.com", "seller2024"),
    ("seller4", "Juliana", "Mendes", "juliana@email.com", "seller2024"),
    ("seller5", "Lucas", "Ferreira", "lucas@email.com", "seller2024"),
    ("seller6", "Patrícia", "Almeida", "patricia@email.com", "seller2024"),
]
sellers = []
for uname, fn, ln, email, pwd in sellers_data:
    u, _ = User.objects.update_or_create(
        username=uname,
        defaults={"first_name": fn, "last_name": ln, "email": email, "role": "seller"},
    )
    u.set_password(pwd)
    u.save()
    sellers.append(u)
    mods = Modulo.objects.filter(slug__in=["dashboard", "tarefas", "reunioes", "treinamentos", "portal"])
    u.modulos.set(mods)

print(f"✓ Usuários: 1 gestor, {len(consultores)} consultores, {len(sellers)} sellers")

# ── Etapas Pipeline ────────────────────────────────────
from apps.clientes.models import EtapaPipeline, Cliente, Atividade

etapas_pipeline = [
    ("Onboarding", "#6366F1", 1),
    ("Diagnóstico Inicial", "#8B5CF6", 2),
    ("Plano de Ação", "#EC4899", 3),
    ("Implementação", "#F59E0B", 4),
    ("Acompanhamento", "#22C55E", 5),
    ("Consolidação", "#06B6D4", 6),
]
etapas_obj = []
for nome, cor, ordem in etapas_pipeline:
    e, _ = EtapaPipeline.objects.update_or_create(
        nome=nome, defaults={"cor": cor, "ordem": ordem}
    )
    etapas_obj.append(e)
print(f"✓ {len(etapas_obj)} etapas de pipeline")

# ── Clientes ───────────────────────────────────────────
nichos = ["Eletrônicos", "Moda", "Casa e Decoração", "Brinquedos", "Automotivo", "Esportes"]
clientes_data = [
    ("TechStore Brasil", "12.345.678/0001-01", "techstore_ml", sellers[0]),
    ("Moda Fashion Store", "23.456.789/0001-02", "modafashion", sellers[1]),
    ("Casa & Lar Decorações", "34.567.890/0001-03", "casaelar_ml", sellers[2]),
    ("BrinquedosMania", "45.678.901/0001-04", "brinquedos_mania", sellers[3]),
    ("AutoParts Express", "56.789.012/0001-05", "autoparts_exp", sellers[4]),
    ("SportMax Equipamentos", "67.890.123/0001-06", "sportmax_ml", sellers[5]),
]

clientes = []
for i, (empresa, cnpj, ml_nick, seller_user) in enumerate(clientes_data):
    consultor = consultores[i % len(consultores)]
    etapa = etapas_obj[min(i, len(etapas_obj) - 1)]
    status = random.choice(["ativo", "ativo", "ativo", "onboarding"])
    tipo = random.choice(["estrategica", "operacional"])
    # Check if already exists (ActiveManager filters is_active)
    c = Cliente.all_objects.filter(empresa=empresa).first()
    if not c:
        c = Cliente.all_objects.create(
            empresa=empresa,
            cnpj=cnpj,
            nicho=nichos[i % len(nichos)],
            telefone=f"(11) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            email=f"contato@{empresa.lower().replace(' ', '').replace('&', '')}.com.br",
            ml_nickname=ml_nick,
            ml_seller_id=str(random.randint(100000000, 999999999)),
            ml_reputacao=random.choice(["verde", "amarela", "verde"]),
            consultor=consultor,
            tipo_consultoria=tipo,
            data_inicio=date.today() - timedelta(days=random.randint(30, 180)),
            status=status,
            etapa=etapa,
            usuario=seller_user,
        )
    clientes.append(c)

print(f"✓ {len(clientes)} clientes criados")

# ── Atividades dos Clientes ────────────────────────────
for cliente in clientes:
    for j in range(random.randint(2, 5)):
        Atividade.objects.get_or_create(
            cliente=cliente,
            descricao=random.choice([
                "Reunião de alinhamento realizada",
                "Diagnóstico inicial aplicado",
                "Plano de ação definido com o seller",
                "Treinamento de anúncios aplicado",
                "Acompanhamento mensal - resultados positivos",
                "Ajuste na estratégia de precificação",
                "Revisão de reputação e métricas",
                "Seller implementou melhorias nos anúncios",
            ]),
            defaults={"autor": cliente.consultor},
        )
print("✓ Atividades criadas")

# ── Diagnósticos ───────────────────────────────────────
from apps.diagnosticos.models import DiagnosticTemplate, DiagnosticQuestion, Diagnostic, DiagnosticAnswer

template, _ = DiagnosticTemplate.objects.update_or_create(
    nome="Diagnóstico 360° - Mercado Livre",
    defaults={"descricao": "Avaliação completa do vendedor no Mercado Livre", "criado_por": gestor},
)

categorias_perguntas = {
    "Anúncios": [
        ("Qualidade das fotos dos anúncios", "scale"),
        ("Títulos otimizados com palavras-chave", "scale"),
        ("Descrições completas e persuasivas", "scale"),
        ("Preços competitivos no mercado", "scale"),
        ("Uso de variações nos anúncios", "scale"),
    ],
    "Reputação": [
        ("Taxa de reclamações", "scale"),
        ("Tempo médio de resposta", "scale"),
        ("Taxa de cancelamento", "scale"),
        ("Nível de reputação geral", "scale"),
    ],
    "Logística": [
        ("Prazo de envio", "scale"),
        ("Uso do Mercado Envios Full", "scale"),
        ("Taxa de atraso nas entregas", "scale"),
        ("Embalagem adequada", "scale"),
    ],
    "Financeiro": [
        ("Margem de lucro saudável", "scale"),
        ("Controle de custos operacionais", "scale"),
        ("Fluxo de caixa organizado", "scale"),
    ],
    "Marketing": [
        ("Uso de Mercado Ads", "scale"),
        ("Participação em promoções", "scale"),
        ("Estratégia de precificação", "scale"),
    ],
}

ordem = 0
for cat, perguntas in categorias_perguntas.items():
    for texto, tipo in perguntas:
        ordem += 1
        DiagnosticQuestion.objects.update_or_create(
            template=template,
            texto=texto,
            defaults={"categoria": cat, "tipo": tipo, "ordem": ordem, "weight": Decimal("1.00")},
        )

questions = list(DiagnosticQuestion.objects.filter(template=template))
print(f"✓ Template diagnóstico com {len(questions)} perguntas")

# Criar diagnósticos para cada cliente
for cliente in clientes:
    for m_offset in [2, 1, 0]:
        mes_ref = date.today() - timedelta(days=30 * m_offset)
        diag, created = Diagnostic.objects.update_or_create(
            template=template,
            cliente=cliente,
            mes=mes_ref.month,
            ano=mes_ref.year,
            defaults={
                "executor": cliente.consultor,
                "status": "completed",
                "completed_at": timezone.now() - timedelta(days=30 * m_offset),
            },
        )
        if created:
            total_score = Decimal("0")
            cat_scores = {}
            cat_counts = {}
            for q in questions:
                score = Decimal(str(round(random.uniform(4.0, 9.5), 1)))
                DiagnosticAnswer.objects.update_or_create(
                    diagnostic=diag,
                    question=q,
                    defaults={"value_numeric": score, "score": score},
                )
                total_score += score
                cat_scores[q.categoria] = cat_scores.get(q.categoria, Decimal("0")) + score
                cat_counts[q.categoria] = cat_counts.get(q.categoria, 0) + 1

            diag.score = total_score / len(questions)
            diag.scores_por_categoria = {
                cat: float(cat_scores[cat] / cat_counts[cat]) for cat in cat_scores
            }
            diag.save()

print("✓ Diagnósticos criados (3 meses por cliente)")

# ── Tipos de Tarefa ────────────────────────────────────
from apps.tarefas.models import TipoTarefa, Tarefa

tipos_tarefa = [
    ("Otimizar Anúncio", "photo", "#6366F1"),
    ("Melhorar Reputação", "shield-check", "#22C55E"),
    ("Configurar Full", "truck", "#F59E0B"),
    ("Análise de Concorrência", "magnifying-glass", "#EC4899"),
    ("Ajustar Preço", "currency-dollar", "#06B6D4"),
    ("Criar Campanha Ads", "megaphone", "#8B5CF6"),
]
tipos_obj = []
for nome, icone, cor in tipos_tarefa:
    t, _ = TipoTarefa.objects.update_or_create(nome=nome, defaults={"icone": icone, "cor": cor})
    tipos_obj.append(t)
print(f"✓ {len(tipos_obj)} tipos de tarefa")

# ── Tarefas ────────────────────────────────────────────
tarefas_desc = [
    "Otimizar fotos dos 10 anúncios principais",
    "Reescrever títulos com palavras-chave relevantes",
    "Configurar Mercado Envios Full para top produtos",
    "Analisar concorrentes e ajustar preços",
    "Criar campanha de Mercado Ads para categoria principal",
    "Responder todas reclamações pendentes",
    "Revisar descrições dos anúncios mais vendidos",
    "Configurar variações nos anúncios sem variação",
    "Melhorar embalagem para reduzir devoluções",
    "Ativar promoções para produtos com estoque alto",
]

for cliente in clientes:
    for _ in range(random.randint(3, 6)):
        prazo = date.today() + timedelta(days=random.randint(-10, 30))
        status = random.choice(["pendente", "pendente", "em_andamento", "concluida", "concluida"])
        Tarefa.objects.get_or_create(
            cliente=cliente,
            descricao=random.choice(tarefas_desc),
            defaults={
                "criado_por": cliente.consultor,
                "responsavel": random.choice([cliente.consultor, cliente.consultor]),
                "tipo": random.choice(tipos_obj),
                "prioridade": random.choice(["baixa", "media", "media", "alta", "urgente"]),
                "prazo": prazo,
                "status": status,
                "concluido_em": timezone.now() - timedelta(days=random.randint(0, 5)) if status == "concluida" else None,
            },
        )
print("✓ Tarefas criadas")

# ── Treinamentos ───────────────────────────────────────
from apps.treinamentos.models import Treinamento, TreinamentoRealizado

treinamentos_data = [
    ("Fotografia para Mercado Livre", "operacional", "Como tirar fotos profissionais com celular", 60),
    ("SEO para Títulos e Descrições", "operacional", "Otimização de títulos e descrições para ML", 45),
    ("Gestão de Reputação", "operacional", "Como manter e recuperar reputação no ML", 90),
    ("Mercado Envios Full", "operacional", "Configuração e vantagens do Full", 60),
    ("Mercado Ads Básico", "operacional", "Como criar campanhas de anúncios eficientes", 75),
    ("Mercado Ads Avançado", "estrategica", "Estratégias avançadas de Ads e ROI", 90),
    ("Precificação Inteligente", "estrategica", "Como precificar para maximizar lucro", 60),
    ("Análise de Métricas", "estrategica", "Interpretando os dados do ML para decisões", 45),
    ("Gestão Financeira para Sellers", "estrategica", "Controle financeiro e fluxo de caixa", 60),
    ("Escala: De 100 a 1000 vendas/mês", "estrategica", "Estratégias de escala no marketplace", 120),
]

treinamentos = []
for titulo, cat, desc, duracao in treinamentos_data:
    t, _ = Treinamento.objects.update_or_create(
        titulo=titulo,
        defaults={"categoria": cat, "descricao": desc, "duracao_minutos": duracao},
    )
    treinamentos.append(t)

for cliente in clientes:
    for t in random.sample(treinamentos, k=random.randint(2, 5)):
        TreinamentoRealizado.objects.get_or_create(
            treinamento=t,
            cliente=cliente,
            defaults={
                "data": date.today() - timedelta(days=random.randint(5, 90)),
                "observacoes": "Seller demonstrou bom aproveitamento do conteúdo.",
            },
        )
print(f"✓ {len(treinamentos)} treinamentos + realizações")

# ── Reuniões ───────────────────────────────────────────
from apps.reunioes.models import Reuniao

tipos_reuniao = ["diagnostico", "treinamento_full", "revisao_mensal", "comercial"]
for cliente in clientes:
    for r in range(random.randint(2, 4)):
        data_reuniao = timezone.now() - timedelta(days=random.randint(1, 60))
        Reuniao.objects.get_or_create(
            cliente=cliente,
            data=data_reuniao,
            defaults={
                "tipo": random.choice(tipos_reuniao),
                "duracao_minutos": random.choice([30, 45, 60, 90]),
                "consultor": cliente.consultor,
                "resumo": random.choice([
                    "Discutimos melhorias nos anúncios e estratégia de preços.",
                    "Alinhamento sobre metas do mês e plano de ação.",
                    "Treinamento sobre fotos e descrições otimizadas.",
                    "Revisão mensal dos resultados e ajustes na estratégia.",
                    "Reunião comercial para upgrade de plano.",
                ]),
                "proximos_passos": "Implementar ações definidas na reunião até a próxima semana.",
            },
        )
print("✓ Reuniões criadas")

# ── Checklists ─────────────────────────────────────────
from apps.checklists.models import (
    ChecklistCategory, ChecklistTemplate, ChecklistTemplateItem,
    ChecklistExecution, ChecklistExecutionItem,
)

cat_onb, _ = ChecklistCategory.objects.update_or_create(
    nome="Onboarding", defaults={"icone": "rocket", "ordem": 1}
)
cat_mensal, _ = ChecklistCategory.objects.update_or_create(
    nome="Acompanhamento Mensal", defaults={"icone": "calendar", "ordem": 2}
)

# Template Onboarding
tpl_onb, _ = ChecklistTemplate.objects.update_or_create(
    nome="Checklist de Onboarding",
    defaults={"descricao": "Passos iniciais para novo seller", "tipo": "avulso", "criado_por": gestor},
)
onb_items = [
    "Coletar dados de acesso ao Mercado Livre",
    "Analisar conta e reputação atual",
    "Mapear catálogo de produtos",
    "Verificar configuração de envio",
    "Avaliar fotos e descrições dos top 10 anúncios",
    "Configurar Mercado Envios (Full ou Flex)",
    "Criar plano de ação inicial",
    "Agendar primeira reunião de treinamento",
]
for i, desc in enumerate(onb_items):
    ChecklistTemplateItem.objects.update_or_create(
        template=tpl_onb, descricao=desc,
        defaults={"category": cat_onb, "ordem": i + 1},
    )

# Template Mensal
tpl_mensal, _ = ChecklistTemplate.objects.update_or_create(
    nome="Revisão Mensal",
    defaults={"descricao": "Checklist de acompanhamento mensal", "tipo": "mensal", "criado_por": gestor},
)
mensal_items = [
    "Revisar métricas de vendas do mês",
    "Analisar evolução da reputação",
    "Verificar status das tarefas pendentes",
    "Atualizar diagnóstico mensal",
    "Revisar e ajustar campanhas de Ads",
    "Analisar concorrência e preços",
]
for i, desc in enumerate(mensal_items):
    ChecklistTemplateItem.objects.update_or_create(
        template=tpl_mensal, descricao=desc,
        defaults={"category": cat_mensal, "ordem": i + 1},
    )

# Execuções
for cliente in clientes[:4]:
    exec_obj, created = ChecklistExecution.objects.get_or_create(
        template=tpl_onb,
        cliente=cliente,
        defaults={"executor": cliente.consultor, "status": "completed", "score": 100},
    )
    if created:
        exec_obj.completed_at = timezone.now() - timedelta(days=random.randint(10, 30))
        exec_obj.save()
        for item in ChecklistTemplateItem.objects.filter(template=tpl_onb):
            ChecklistExecutionItem.objects.create(
                execution=exec_obj, template_item=item,
                status="done", completed_at=timezone.now(), completed_by=cliente.consultor,
            )

print("✓ Checklists criados com execuções")

# ── Planos de Ação ─────────────────────────────────────
from apps.planos.models import PlanoAcao, ItemPlano

for cliente in clientes:
    plano, _ = PlanoAcao.objects.get_or_create(
        cliente=cliente,
        titulo=f"Plano de Crescimento - {cliente.empresa}",
        defaults={"tipo": random.choice(["mensal", "trimestral"]), "descricao": "Plano focado em aumento de vendas e melhoria de reputação"},
    )
    itens_plano = [
        "Otimizar os 20 anúncios com mais visitas",
        "Migrar produtos para Full",
        "Criar campanha de Ads com ROI mínimo de 5x",
        "Reduzir tempo de envio para < 24h",
        "Implementar variações em todos os anúncios",
    ]
    for i, desc in enumerate(random.sample(itens_plano, k=random.randint(3, 5))):
        ItemPlano.objects.get_or_create(
            plano=plano,
            descricao=desc,
            defaults={
                "responsavel": cliente.consultor,
                "prioridade": random.choice(["baixa", "media", "alta"]),
                "prazo": date.today() + timedelta(days=random.randint(7, 45)),
                "status": random.choice(["pendente", "em_andamento", "concluido"]),
            },
        )
print("✓ Planos de ação criados")

# ── Contratos e Pagamentos ─────────────────────────────
from apps.financeiro.models import ContratoTemplate, Contrato, Pagamento

tpl_contrato, _ = ContratoTemplate.objects.update_or_create(
    nome="Contrato Padrão Consultoria ML",
    defaults={"conteudo": "Modelo padrão de contrato de consultoria para vendedores do Mercado Livre."},
)

for cliente in clientes:
    valor = random.choice([Decimal("997.00"), Decimal("1497.00"), Decimal("1997.00"), Decimal("2497.00")])
    contrato, _ = Contrato.objects.get_or_create(
        cliente=cliente,
        defaults={
            "plano": f"Consultoria {'Estratégica' if valor > 1500 else 'Operacional'}",
            "valor": valor,
            "dia_vencimento": random.choice([5, 10, 15, 20]),
            "data_inicio": cliente.data_inicio,
            "template": tpl_contrato,
            "status_assinatura": "assinado",
        },
    )
    # Gerar pagamentos dos últimos 3 meses
    for m in range(3):
        mes_ref = date.today().replace(day=1) - timedelta(days=30 * m)
        status_pag = "pago" if m > 0 else random.choice(["pago", "pendente"])
        Pagamento.objects.get_or_create(
            contrato=contrato,
            mes_referencia=mes_ref,
            defaults={
                "valor": valor,
                "status": status_pag,
                "data_pagamento": mes_ref + timedelta(days=contrato.dia_vencimento) if status_pag == "pago" else None,
                "metodo_pagamento": random.choice(["manual", "pix", "boleto"]),
            },
        )
print("✓ Contratos e pagamentos criados")

# ── Propostas e Serviços ──────────────────────────────
from apps.propostas.models import Servico, Proposta

servicos_data = [
    ("Consultoria Operacional", "Acompanhamento operacional mensal", Decimal("997.00"), 1),
    ("Consultoria Estratégica", "Acompanhamento estratégico completo", Decimal("1997.00"), 2),
    ("Treinamento Individual", "Sessão de treinamento personalizado", Decimal("497.00"), 3),
    ("Setup de Conta ML", "Configuração inicial completa da conta", Decimal("1497.00"), 4),
    ("Gestão de Ads", "Gestão mensal de campanhas Mercado Ads", Decimal("797.00"), 5),
]
for nome, desc, preco, ordem in servicos_data:
    Servico.objects.update_or_create(
        nome=nome, defaults={"descricao": desc, "preco_sugerido": preco, "ordem": ordem}
    )
print("✓ Serviços de proposta criados")

# ── NPS ────────────────────────────────────────────────
from apps.nps.models import PesquisaNPS, RespostaNPS

pesquisa, _ = PesquisaNPS.objects.get_or_create(
    titulo="Satisfação Mensal - Março 2026",
    defaults={"descricao": "Pesquisa de satisfação mensal dos sellers", "criado_por": gestor},
)
for cliente in clientes[:4]:
    RespostaNPS.objects.get_or_create(
        pesquisa=pesquisa,
        cliente=cliente,
        defaults={
            "nota": random.randint(7, 10),
            "comentario": random.choice([
                "Excelente atendimento! Minhas vendas cresceram 40%.",
                "Muito satisfeito com o acompanhamento do consultor.",
                "Bom serviço, mas poderia ter mais treinamentos.",
                "Ótimo! Recomendo para todos os sellers.",
            ]),
            "respondido_em": timezone.now() - timedelta(days=random.randint(1, 10)),
        },
    )
print("✓ Pesquisa NPS com respostas")

# ── Notificações ───────────────────────────────────────
from apps.notificacoes.models import Notificacao

for consultor in consultores:
    for _ in range(3):
        Notificacao.objects.get_or_create(
            destinatario=consultor,
            titulo=random.choice([
                "Tarefa atrasada: Otimizar anúncios",
                "Novo diagnóstico disponível",
                "Reunião amanhã às 10h",
                "Seller completou treinamento",
                "Pagamento pendente de cliente",
            ]),
            defaults={
                "tipo": random.choice(["tarefa", "reuniao", "diagnostico", "geral"]),
                "mensagem": "Verifique os detalhes no sistema.",
                "lida": random.choice([True, False]),
            },
        )
print("✓ Notificações criadas")

# ── Jornadas de Cliente ────────────────────────────────
from apps.jornadas.models import JornadaTemplate, EtapaTemplate, JornadaCliente, EtapaCliente

jt = JornadaTemplate.objects.first()
if jt:
    for cliente in clientes[:3]:
        jc, created = JornadaCliente.objects.get_or_create(
            cliente=cliente,
            status="ativa",
            defaults={
                "jornada_template": jt,
                "nome": f"{jt.nome} - {cliente.empresa}",
                "data_inicio": cliente.data_inicio,
                "progresso": Decimal(str(random.randint(20, 70))),
                "areas_foco": ["anúncios", "reputação", "logística"],
            },
        )
        if created:
            etapas_tpl = EtapaTemplate.objects.filter(jornada_template=jt).order_by("ordem")
            for et in etapas_tpl:
                data_prev = cliente.data_inicio + timedelta(days=et.dias_offset)
                status_et = "concluida" if random.random() < 0.4 else random.choice(["pendente", "em_andamento"])
                EtapaCliente.objects.create(
                    jornada=jc,
                    etapa_template=et,
                    nome=et.nome,
                    descricao=et.descricao,
                    tipo=et.tipo,
                    ordem=et.ordem,
                    data_prevista=data_prev,
                    data_limite=data_prev + timedelta(days=et.duracao_dias),
                    status=status_et,
                    data_conclusao=date.today() - timedelta(days=random.randint(1, 20)) if status_et == "concluida" else None,
                )
            jc.calcular_progresso()
    print("✓ Jornadas de cliente criadas")
else:
    print("⚠ Nenhum JornadaTemplate encontrado para criar jornadas")

# ── Insights IA ────────────────────────────────────────
from apps.ia.models import InsightIA

for consultor in consultores:
    for cliente in Cliente.objects.filter(consultor=consultor)[:2]:
        InsightIA.objects.get_or_create(
            consultor=consultor,
            cliente=cliente,
            titulo=f"Alerta: Queda de reputação - {cliente.empresa}",
            defaults={
                "tipo": "alerta",
                "prioridade": "alta",
                "descricao": f"A reputação de {cliente.empresa} caiu nos últimos 7 dias. Recomendamos ação imediata.",
                "acao_sugerida": "Verificar reclamações abertas e responder dentro de 24h.",
                "url_acao": f"/clientes/{cliente.pk}/",
            },
        )
        InsightIA.objects.get_or_create(
            consultor=consultor,
            cliente=cliente,
            titulo=f"Sugestão: Campanha de Ads - {cliente.empresa}",
            defaults={
                "tipo": "sugestao",
                "prioridade": "media",
                "descricao": f"{cliente.empresa} tem produtos com alta conversão. Uma campanha de Ads pode aumentar vendas em 30%.",
                "acao_sugerida": "Criar campanha focada nos top 5 produtos.",
            },
        )
print("✓ Insights IA criados")

# ── Agenda ─────────────────────────────────────────────
from apps.agenda.models import Agendamento

for consultor in consultores:
    for d in range(5):
        data_hora = timezone.now() + timedelta(days=d, hours=random.randint(9, 16))
        cliente = random.choice(clientes)
        Agendamento.objects.get_or_create(
            consultor=consultor,
            data_hora=data_hora,
            defaults={
                "duracao": random.choice([30, 60]),
                "nome_cliente": cliente.empresa,
                "email_cliente": cliente.email,
                "telefone_cliente": cliente.telefone,
                "observacao": "Reunião de acompanhamento",
                "cliente": cliente,
            },
        )
print("✓ Agendamentos criados")

print("\n" + "=" * 50)
print("🎉 SEED COMPLETO! Banco populado com dados de teste.")
print("=" * 50)
